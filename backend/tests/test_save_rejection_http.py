"""Exercise routing, signed-in permissions and save outcomes through ASGI HTTP."""
import asyncio
import json
import unittest
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import auth
import main
import models


class SaveRejectionHttpTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        models.Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        with self.Session() as db:
            owner = models.User(username="test_owner", password_hash="unused", role="owner")
            employee = models.User(username="test_employee", password_hash="unused", role="employee")
            customer = models.Customer(name="Test customer", phone="0700000000", phone_normalized="254700000000")
            other = models.Customer(name="Other customer", phone="0711111111", phone_normalized="254711111111")
            db.add_all([owner, employee, customer, other])
            db.flush()
            order = models.Order(ticket_number="QL-HTTP-001", customer_id=customer.id,
                                 service_type="wash_fold", quantity=2, unit_price=150, total_price=300,
                                 order_date=main.get_nairobi_today())
            db.add(order)
            db.commit()
            self.order_id, self.customer_id, self.other_id = order.id, customer.id, other.id
            self.tokens = {user.role: auth.create_access_token(user.id, user.role, user.token_version)
                           for user in (owner, employee)}

        def get_test_db():
            with self.Session() as db:
                yield db

        self.previous_overrides = main.app.dependency_overrides.copy()
        main.app.dependency_overrides[main.get_db] = get_test_db
        self.quantity_path = f"/orders/{self.order_id}/quantity-corrections"
        self.quantity_body = {"expected_quantity": 2, "new_quantity": 3, "reason": "Checked the scale", "confirmed": True}

    def tearDown(self):
        main.app.dependency_overrides.clear()
        main.app.dependency_overrides.update(self.previous_overrides)
        self.engine.dispose()

    def post(self, path, body, key=None, role="owner", method="POST"):
        # Send a complete HTTP request through FastAPI without a network server.
        async def request():
            data = json.dumps(body).encode()
            headers = [(b"content-type", b"application/json"),
                       (b"idempotency-key", str(key or uuid4()).encode())]
            if role:
                headers.append((b"authorization", f"Bearer {self.tokens[role]}".encode()))
            scope = {"type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
                     "method": method, "scheme": "http", "path": path,
                     "raw_path": path.encode(), "query_string": b"", "root_path": "",
                     "headers": headers, "client": ("127.0.0.1", 1), "server": ("testserver", 80)}
            messages = []

            async def receive():
                return {"type": "http.request", "body": data, "more_body": False}

            async def send(message):
                messages.append(message)

            await main.app(scope, receive, send)
            status = next(message["status"] for message in messages if message["type"] == "http.response.start")
            payload = b"".join(message.get("body", b"") for message in messages if message["type"] == "http.response.body")
            return status, json.loads(payload)

        return asyncio.run(request())

    def test_stale_quantity_rejects_without_writing_then_revised_save_and_retry_work(self):
        status, payload = self.post(self.quantity_path, {**self.quantity_body, "expected_quantity": 1})
        self.assertEqual(status, 409)
        self.assertEqual(payload["detail"]["code"], "QLMS-STALE-RECORD")
        self.assertEqual(payload["detail"]["save_state"], "not_saved")
        with self.Session() as db:
            self.assertEqual(db.get(models.Order, self.order_id).quantity, 2)
            self.assertEqual(db.query(models.OrderCorrection).count(), 0)
        key = uuid4()
        for _ in range(2):
            status, payload = self.post(self.quantity_path, self.quantity_body, key)
            self.assertEqual(status, 200)
            self.assertEqual(payload["quantity"], 3)
        with self.Session() as db:
            self.assertEqual(db.query(models.OrderCorrection).count(), 1)

    def test_changed_key_payload_remains_a_conflict_with_existing_history(self):
        key = uuid4()
        self.assertEqual(self.post(self.quantity_path, self.quantity_body, key)[0], 200)
        status, payload = self.post(self.quantity_path, {**self.quantity_body, "new_quantity": 4}, key)
        self.assertEqual(status, 409)
        self.assertEqual(payload["detail"]["code"], "QLMS-SAVE-CONFLICT")
        self.assertEqual(payload["detail"]["save_state"], "unknown")
        with self.Session() as db:
            self.assertEqual(db.get(models.Order, self.order_id).quantity, 3)
            self.assertEqual(db.query(models.OrderCorrection).count(), 1)

    def test_stale_stage_and_customer_link_are_explicitly_unsaved(self):
        cases = [
            (f"/orders/{self.order_id}/corrections", {"action": "stage_back", "expected_status": "ready"}),
            (f"/orders/{self.order_id}/customer-corrections", {"expected_customer_id": self.other_id, "new_customer_id": self.customer_id}),
        ]
        for path, fields in cases:
            with self.subTest(path=path):
                status, payload = self.post(path, {**fields, "reason": "Owner checked the ticket", "confirmed": True})
                self.assertEqual(status, 409)
                self.assertEqual(payload["detail"]["save_state"], "not_saved")
        with self.Session() as db:
            self.assertEqual(db.query(models.OrderCorrection).count(), 0)

    def test_shared_phone_correction_can_be_confirmed_after_a_rejection(self):
        path = f"/customers/{self.customer_id}/corrections"
        body = {"expected_name": "Test customer", "expected_phone": "0700000000",
                "new_name": "Test customer", "new_phone": "0711111111",
                "reason": "Confirmed the family phone", "confirmed": True}
        status, payload = self.post(path, body)
        self.assertEqual(status, 409)
        self.assertEqual(payload["detail"]["code"], "QLMS-PHONE-SHARED")
        self.assertEqual(payload["detail"]["save_state"], "not_saved")
        with self.Session() as db:
            self.assertEqual(db.get(models.Customer, self.customer_id).phone, "0700000000")
            self.assertEqual(db.query(models.CustomerCorrection).count(), 0)
        status, payload = self.post(path, {**body, "allow_shared_phone": True})
        self.assertEqual(status, 200)
        self.assertEqual(payload["phone"], "0711111111")

    def contact_body(self, **changes):
        body = {"expected_name": "Test customer", "expected_phone": "0700000000",
                "new_name": "Correct customer", "new_phone": "0700000000",
                "reason": "Checked spelling with customer", "confirmed": True}
        body.update(changes)
        return body

    def test_contact_retry_history_and_orders_keep_their_identity(self):
        path = f"/customers/{self.customer_id}/corrections"
        key, body = uuid4(), self.contact_body(new_phone="+254 722 222 222")
        for _ in range(2):
            status, result = self.post(path, body, key)
            self.assertEqual(status, 200)
            self.assertEqual((result["id"], result["phone"]), (self.customer_id, "0722222222"))
        status, history = self.post(path, {}, method="GET")
        self.assertEqual(status, 200)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["before_state"], {"name": "Test customer", "phone": "0700000000"})
        self.assertEqual(history[0]["after_state"], {"name": "Correct customer", "phone": "0722222222"})
        self.assertEqual(history[0]["confirmed_by_username"], "test_owner")
        self.assertNotIn("request_hash", history[0])
        with self.Session() as db:
            order = db.get(models.Order, self.order_id)
            self.assertEqual(order.customer_id, self.customer_id)
            self.assertEqual(order.total_price, 300)
            self.assertEqual(db.query(models.Customer).count(), 2)
            self.assertEqual(db.get(models.Customer, self.customer_id).phone_normalized, "254722222222")
        self.assertEqual(self.post(path, self.contact_body(), key)[0], 409)

    def test_name_only_change_on_shared_number_needs_no_new_phone_approval(self):
        with self.Session() as db:
            other = db.get(models.Customer, self.other_id)
            other.phone, other.phone_normalized = "0700000000", "254700000000"
            db.commit()
        path = f"/customers/{self.customer_id}/corrections"
        status, _ = self.post(path, self.contact_body(new_phone="+254700000000"))
        self.assertEqual(status, 200)
        history = self.post(path, {}, method="GET")[1]
        self.assertFalse(history[0]["shared_phone_confirmed"])

    def test_stale_contact_edit_rejects_then_original_retry_still_works(self):
        path = f"/customers/{self.customer_id}/corrections"
        key, body = uuid4(), self.contact_body()
        self.assertEqual(self.post(path, body, key)[0], 200)
        status, payload = self.post(path, self.contact_body(new_name="Outdated edit"))
        self.assertEqual(status, 409)
        self.assertEqual(payload["detail"]["save_state"], "not_saved")
        second = self.contact_body(expected_name="Correct customer", new_name="Latest customer")
        self.assertEqual(self.post(path, second)[0], 200)
        status, replay = self.post(path, body, key)
        self.assertEqual((status, replay["name"]), (200, "Latest customer"))
        self.assertEqual(len(self.post(path, {}, method="GET")[1]), 2)

    def test_contact_rejects_invalid_or_tampered_input_without_history(self):
        path = f"/customers/{self.customer_id}/corrections"
        for changes, expected in [({"new_name": "  "}, 422), ({"new_phone": "wrong"}, 422),
                                  ({"reason": " "}, 422), ({"confirmed": False}, 400),
                                  ({"new_name": "Test customer"}, 400),
                                  ({"confirmed_by_username": "someone_else"}, 422)]:
            with self.subTest(changes=changes):
                self.assertEqual(self.post(path, self.contact_body(**changes))[0], expected)
        self.assertEqual(self.post(path, {}, method="GET")[1], [])

    def test_contact_read_permissions_missing_record_and_disabled_owner(self):
        for path in [f"/customers/{self.customer_id}", f"/customers/{self.customer_id}/corrections"]:
            self.assertEqual(self.post(path, {}, method="GET")[0], 200)
            for role, expected in [("employee", 403), (None, 401)]:
                self.assertEqual(self.post(path, {}, role=role, method="GET")[0], expected)
        self.assertEqual(self.post("/customers/99999", {}, method="GET")[0], 404)
        self.assertEqual(self.post("/customers/99999/corrections", self.contact_body())[0], 404)
        with self.Session() as db:
            db.query(models.User).filter_by(role="owner").first().is_active = False
            db.commit()
        self.assertEqual(self.post(f"/customers/{self.customer_id}/corrections", self.contact_body())[0], 401)

    def test_invalid_legacy_phone_can_be_corrected(self):
        with self.Session() as db:
            db.get(models.Customer, self.customer_id).phone = "unknown"
            db.commit()
        self.assertEqual(self.post(f"/customers/{self.customer_id}/corrections",
                                  self.contact_body(expected_phone="unknown"))[0], 200)

    def test_employee_and_signed_out_requests_cannot_correct_orders(self):
        paths = [self.quantity_path, f"/orders/{self.order_id}/corrections",
                 f"/orders/{self.order_id}/customer-corrections", f"/customers/{self.customer_id}/corrections"]
        for path in paths:
            for role, expected in [("employee", 403), (None, 401)]:
                with self.subTest(path=path, role=role):
                    self.assertEqual(self.post(path, self.quantity_body, role=role)[0], expected)
        with self.Session() as db:
            self.assertEqual(db.query(models.OrderCorrection).count(), 0)
            self.assertEqual(db.query(models.CustomerCorrection).count(), 0)


if __name__ == "__main__":
    unittest.main()
