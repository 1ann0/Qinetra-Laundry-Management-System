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

    def post(self, path, body, key=None, role="owner"):
        # Send a complete HTTP request through FastAPI without a network server.
        async def request():
            data = json.dumps(body).encode()
            headers = [(b"content-type", b"application/json"),
                       (b"idempotency-key", str(key or uuid4()).encode())]
            if role:
                headers.append((b"authorization", f"Bearer {self.tokens[role]}".encode()))
            scope = {"type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
                     "method": "POST", "scheme": "http", "path": path,
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

    def test_employee_and_signed_out_requests_cannot_correct_orders(self):
        paths = [self.quantity_path, f"/orders/{self.order_id}/corrections",
                 f"/orders/{self.order_id}/customer-corrections"]
        for path in paths:
            for role, expected in [("employee", 403), (None, 401)]:
                with self.subTest(path=path, role=role):
                    self.assertEqual(self.post(path, self.quantity_body, role=role)[0], expected)
        with self.Session() as db:
            self.assertEqual(db.query(models.OrderCorrection).count(), 0)


if __name__ == "__main__":
    unittest.main()
