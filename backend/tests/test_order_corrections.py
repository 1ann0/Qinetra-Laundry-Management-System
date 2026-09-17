"""Cancellation and stage repair must leave a visible owner history."""
import asyncio
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import auth
import main
import models
import schemas


class OrderCorrectionTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        models.Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        self.owner = models.User(username="owner", password_hash="unused", role="owner")
        self.employee = models.User(username="employee", password_hash="unused", role="employee")
        customer = models.Customer(name="Pilot customer", phone="0700000000")
        self.db.add_all([self.owner, self.employee, customer])
        self.db.flush()
        self.order = models.Order(
            ticket_number="QL-TEST-001", customer_id=customer.id,
            service_type="wash_fold", quantity=2, unit_price=150, total_price=300,
            order_date=main.get_nairobi_today(),
        )
        self.db.add(self.order)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def correct(self, action, **changes):
        body = dict(
            action=action, expected_status=self.order.status,
            reason="Stage was selected by mistake", confirmed=True,
            goods_returned=True, still_in_shop=True,
        )
        body.update(changes)
        return main.correct_order_stage(
            self.order.id, schemas.OrderCorrectionCreate(**body),
            self.db, self.owner, idempotency_key=uuid4(),
        )

    def test_cancel_unpaid_received_order_keeps_ticket_but_excludes_work_and_value(self):
        order = self.correct("cancel", reason="Customer withdrew before work started")
        self.assertEqual(order.status, "cancelled")
        self.assertEqual(order.payment_status, "cancelled")
        self.assertEqual(order.balance_due, Decimal("0"))
        self.assertEqual(order.corrections[0].before_state["status"], "received")
        self.assertEqual(order.corrections[0].after_state["status"], "cancelled")
        self.assertTrue(order.corrections[0].goods_returned_confirmed)
        self.assertEqual(len(main.list_orders(db=self.db, current_user=self.employee)), 0)
        self.assertEqual(len(main.list_orders(search="QL-TEST-001", db=self.db, current_user=self.employee)), 1)
        summary = main.financial_summary(order.order_date, order.order_date, self.db, self.owner)
        self.assertEqual(summary.orders_booked, 0)
        self.assertEqual(summary.cancelled_orders, 1)
        self.assertEqual(summary.order_value, 0)
        self.assertEqual(summary.top_services, [])
        self.assertEqual(main.dashboard_summary(self.db, self.owner).unpaid, 0)

        async def csv_text():
            response = main.export_orders_csv(self.db, self.owner)
            parts = []
            async for part in response.body_iterator:
                parts.append(part if isinstance(part, bytes) else part.encode())
            return b"".join(parts).decode()

        report = asyncio.run(csv_text())
        self.assertIn("Effective Order Value", report)
        self.assertIn("300.00,0.00,0.00", report)
        self.assertIn("cancelled", report)

    def test_cancel_requires_no_payment_returned_goods_and_received_stage(self):
        payment = models.Payment(
            order_id=self.order.id, payment_method="cash", amount=100,
            received_date=self.order.order_date,
            confirmed_by_username=self.employee.username,
        )
        self.db.add(payment)
        self.db.commit()
        with self.assertRaises(HTTPException) as paid:
            self.correct("cancel")
        self.assertEqual(paid.exception.status_code, 400)
        self.db.rollback()
        self.db.delete(payment)
        self.db.commit()
        with self.assertRaises(HTTPException) as goods:
            self.correct("cancel", goods_returned=False)
        self.assertEqual(goods.exception.status_code, 400)
        self.db.rollback()
        self.order.status = "in_progress"
        self.db.commit()
        with self.assertRaises(HTTPException) as started:
            self.correct("cancel")
        self.assertEqual(started.exception.status_code, 400)

    def test_stage_back_is_one_step_and_keeps_prior_timestamps(self):
        ready_time = datetime.now(timezone.utc)
        self.order.status = "collected"
        self.order.ready_at = ready_time
        self.order.collected_at = ready_time
        self.db.commit()
        with self.assertRaises(HTTPException) as no_goods:
            self.correct("stage_back", still_in_shop=False)
        self.assertEqual(no_goods.exception.status_code, 400)
        self.db.rollback()
        order = self.correct("stage_back")
        self.assertEqual(order.status, "ready")
        self.assertIsNone(order.collected_at)
        self.assertIsNotNone(order.ready_at)
        self.assertIsNotNone(order.corrections[0].before_state["collected_at"])
        self.assertTrue(order.corrections[0].still_in_shop_confirmed)
        self.correct("stage_back")
        self.assertEqual(order.status, "in_progress")
        self.assertIsNone(order.ready_at)
        self.correct("stage_back")
        self.assertEqual(order.status, "received")
        with self.assertRaises(HTTPException):
            self.correct("stage_back")
        self.assertEqual(self.db.query(models.OrderCorrection).count(), 3)

    def test_retry_does_not_repeat_stage_change(self):
        self.order.status = "in_progress"
        self.db.commit()
        body = schemas.OrderCorrectionCreate(
            action="stage_back", expected_status="in_progress",
            reason="Wrong tap", confirmed=True,
        )
        key = uuid4()
        main.correct_order_stage(self.order.id, body, self.db, self.owner, idempotency_key=key)
        main.correct_order_stage(self.order.id, body, self.db, self.owner, idempotency_key=key)
        self.assertEqual(self.order.status, "received")
        self.assertEqual(self.db.query(models.OrderCorrection).count(), 1)

    def test_owner_is_required_by_api(self):
        with self.assertRaises(HTTPException) as denied:
            auth.require_owner(self.employee)
        self.assertEqual(denied.exception.status_code, 403)
        route = next(route for route in main.app.routes
                     if getattr(route, "path", "") == "/orders/{order_id}/corrections")
        self.assertIn(auth.require_owner, [dependency.call for dependency in route.dependant.dependencies])


if __name__ == "__main__":
    unittest.main()
