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
        self.service = models.Service(
            code="wash_fold", name="Wash & Fold", unit="kg", unit_price=150,
            item_recording_mode="tally", turnaround_minutes=180,
        )
        self.db.add_all([self.owner, self.employee, customer, self.service])
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

    def correct_quantity(self, **changes):
        body = dict(
            expected_quantity=self.order.quantity, new_quantity=3,
            reason="Scale reading was corrected", confirmed=True,
        )
        body.update(changes)
        return main.correct_order_quantity(
            self.order.id, schemas.OrderQuantityCorrectionCreate(**body),
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
        quantity_route = next(route for route in main.app.routes
                              if getattr(route, "path", "") == "/orders/{order_id}/quantity-corrections")
        self.assertIn(auth.require_owner, [dependency.call for dependency in quantity_route.dependant.dependencies])

    def test_legacy_wash_quantity_uses_saved_rate_and_keeps_before_after(self):
        self.service.unit_price = 200
        self.db.commit()
        order = self.correct_quantity()
        self.assertEqual(order.quantity, 3)
        self.assertEqual(order.total_price, Decimal("450"))
        self.assertEqual(order.balance_due, Decimal("450"))
        event = order.corrections[0]
        self.assertEqual(event.action, "quantity")
        self.assertEqual(Decimal(event.before_state["quantity"]), 2)
        self.assertEqual(Decimal(event.after_state["quantity"]), 3)
        self.assertEqual(Decimal(event.before_state["order_total"]), 300)
        self.assertEqual(Decimal(event.after_state["order_total"]), 450)

        async def csv_text():
            parts = []
            async for part in main.export_orders_csv(self.db, self.owner).body_iterator:
                parts.append(part if isinstance(part, bytes) else part.encode())
            return b"".join(parts).decode()

        report = asyncio.run(csv_text())
        self.assertIn("Order Correction History", report)
        self.assertIn("quantity: 2", report)
        self.assertIn("Scale reading was corrected", report)

    def test_mixed_order_quantity_and_discount_keep_other_service_unchanged(self):
        duvet = models.Service(
            code="duvet", name="Duvet", unit="item", unit_price=800,
            item_recording_mode="none", turnaround_minutes=180,
        )
        self.db.add(duvet)
        self.db.flush()
        wash_line = models.OrderServiceLine(
            service_id=self.service.id, service_name="Wash & Fold", service_unit="kg",
            quantity=2, unit_price=150, subtotal=300, discount_amount=50,
            item_recording_mode="tally", item_check_status="pending",
        )
        duvet_line = models.OrderServiceLine(
            service_id=duvet.id, service_name="Duvet", service_unit="item",
            quantity=1, unit_price=800, subtotal=800, discount_amount=0,
            item_recording_mode="none", item_check_status="not_required",
        )
        self.order.service_type = "mixed"
        self.order.quantity = 2
        self.order.total_price = 1050
        self.order.service_lines.extend([wash_line, duvet_line])
        self.service.unit_price = 200
        self.db.commit()

        order = self.correct_quantity(
            service_line_id=wash_line.id, expected_quantity=2,
            new_quantity=3, new_discount_amount=75,
        )
        self.assertEqual(order.total_price, Decimal("1175"))
        self.assertEqual(order.quantity, 2)  # Mixed-order summary is its service count.
        self.assertEqual(wash_line.subtotal, Decimal("450"))
        self.assertEqual(wash_line.discount_amount, Decimal("75"))
        self.assertEqual(duvet_line.line_total, Decimal("800"))
        self.assertEqual(Decimal(order.corrections[0].before_state["discount_amount"]), 50)
        self.assertEqual(Decimal(order.corrections[0].after_state["discount_amount"]), 75)

    def test_quantity_cannot_create_an_overpayment_or_change_a_collected_order(self):
        self.db.add(models.Payment(
            order_id=self.order.id, payment_method="cash", amount=280,
            received_date=self.order.order_date, confirmed_by_username="employee",
        ))
        self.db.commit()
        with self.assertRaises(HTTPException) as overpaid:
            self.correct_quantity(new_quantity=1)
        self.assertEqual(overpaid.exception.status_code, 400)
        self.db.rollback()
        self.assertEqual(self.order.total_price, 300)
        self.order.status = "collected"
        self.db.commit()
        with self.assertRaises(HTTPException) as collected:
            self.correct_quantity()
        self.assertEqual(collected.exception.status_code, 400)

    def test_quantity_retry_and_stale_value_do_not_write_twice(self):
        body = schemas.OrderQuantityCorrectionCreate(
            expected_quantity=2, new_quantity=3,
            reason="Scale correction", confirmed=True,
        )
        key = uuid4()
        main.correct_order_quantity(self.order.id, body, self.db, self.owner, idempotency_key=key)
        main.correct_order_quantity(self.order.id, body, self.db, self.owner, idempotency_key=key)
        self.assertEqual(self.db.query(models.OrderCorrection).count(), 1)
        with self.assertRaises(HTTPException) as stale:
            self.correct_quantity(expected_quantity=2, new_quantity=4)
        self.assertEqual(stale.exception.status_code, 409)

    def test_quantity_action_cannot_be_used_for_a_discount_only_change(self):
        with self.assertRaises(HTTPException) as unchanged:
            self.correct_quantity(new_quantity=2)
        self.assertEqual(unchanged.exception.status_code, 400)
        self.assertEqual(self.db.query(models.OrderCorrection).count(), 0)


if __name__ == "__main__":
    unittest.main()
