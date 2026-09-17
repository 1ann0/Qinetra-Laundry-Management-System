"""Owner payment corrections preserve receipts and keep cash dates honest."""
import unittest
from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import auth
import main
import models
import schemas


class PaymentCorrectionTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        models.Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        self.owner = models.User(username="owner", password_hash="unused", role="owner")
        self.employee = models.User(username="staff", password_hash="unused", role="employee")
        customer = models.Customer(name="Pilot customer", phone="0700000000")
        self.db.add_all([self.owner, self.employee, customer])
        self.db.flush()
        self.payment_date = main.get_nairobi_today() - timedelta(days=1)
        self.order = models.Order(
            ticket_number="QL-TEST-001", customer_id=customer.id,
            service_type="wash_fold", quantity=2, unit_price=150, total_price=300,
            order_date=self.payment_date,
        )
        self.db.add(self.order)
        self.db.flush()
        self.payment = models.Payment(
            order_id=self.order.id, payment_method="cash", amount=300,
            received_date=self.payment_date,
            confirmed_by_id=self.employee.id,
            confirmed_by_username=self.employee.username,
        )
        self.db.add(self.payment)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def correct(self, kind="entry_error", amount=100, **changes):
        body = dict(kind=kind, amount=amount, reason="Verified with shop receipt", confirmed=True)
        if kind == "refund":
            body["refund_method"] = "mpesa"
        body.update(changes)
        return main.adjust_order_payment(
            self.order.id, self.payment.id, schemas.PaymentAdjustmentCreate(**body),
            self.db, self.owner, idempotency_key=uuid4(),
        )

    def test_entry_mistake_preserves_payment_and_restates_original_date(self):
        order = self.correct()
        self.assertEqual(order.amount_paid, Decimal("200"))
        self.assertEqual(order.balance_due, Decimal("100"))
        self.assertEqual(order.payments[0].amount, 300)
        self.assertEqual(order.payment_adjustments[0].effective_date, self.payment_date)
        summary = main.financial_summary(self.payment_date, self.payment_date, self.db, self.owner)
        self.assertEqual(summary.cash_received, 200)
        self.assertEqual(summary.refunds_sent, 0)
        self.assertEqual(summary.net_cash_movement, 200)

    def test_refund_is_a_separate_cash_out_on_return_date(self):
        self.correct()
        order = self.correct(kind="refund", amount=50)
        self.assertEqual(order.amount_paid, Decimal("150"))
        self.assertEqual(order.payment_adjustments[1].refund_method, "mpesa")
        old_day = main.financial_summary(self.payment_date, self.payment_date, self.db, self.owner)
        today = main.get_nairobi_today()
        new_day = main.financial_summary(today, today, self.db, self.owner)
        self.assertEqual(old_day.total_received, 200)
        self.assertEqual(old_day.refunds_sent, 0)
        self.assertEqual(new_day.total_received, 0)
        self.assertEqual(new_day.refunds_sent, 50)
        self.assertEqual(new_day.net_cash_movement, -50)

    def test_cannot_adjust_more_than_payment_or_adjust_after_collection(self):
        self.correct(amount=250)
        with self.assertRaises(HTTPException) as excessive:
            self.correct(amount=51)
        self.assertEqual(excessive.exception.status_code, 400)
        self.db.rollback()
        self.order.status = "collected"
        self.db.commit()
        with self.assertRaises(HTTPException) as collected:
            self.correct(amount=25)
        self.assertEqual(collected.exception.status_code, 400)
        self.assertEqual(self.db.query(models.PaymentAdjustment).count(), 1)

    def test_retry_keeps_one_event_and_rejects_changed_details(self):
        body = schemas.PaymentAdjustmentCreate(
            kind="entry_error", amount=100, reason="Wrong cash figure", confirmed=True,
        )
        key = uuid4()
        first = main.adjust_order_payment(self.order.id, self.payment.id, body, self.db, self.owner, idempotency_key=key)
        again = main.adjust_order_payment(self.order.id, self.payment.id, body, self.db, self.owner, idempotency_key=key)
        self.assertEqual(first.id, again.id)
        self.assertEqual(self.db.query(models.PaymentAdjustment).count(), 1)
        with self.assertRaises(HTTPException) as changed:
            main.adjust_order_payment(
                self.order.id, self.payment.id,
                schemas.PaymentAdjustmentCreate(kind="entry_error", amount=90, reason="Wrong cash figure", confirmed=True),
                self.db, self.owner, idempotency_key=key,
            )
        self.assertEqual(changed.exception.status_code, 409)

    def test_requires_confirmation_and_owner_api_dependency(self):
        with self.assertRaises(HTTPException) as unconfirmed:
            self.correct(confirmed=False)
        self.assertEqual(unconfirmed.exception.status_code, 400)
        with self.assertRaises(HTTPException) as forbidden:
            auth.require_owner(self.employee)
        self.assertEqual(forbidden.exception.status_code, 403)
        route = next(route for route in main.app.routes
                     if getattr(route, "path", "") == "/orders/{order_id}/payments/{payment_id}/adjustments")
        self.assertIn(auth.require_owner, [dependency.call for dependency in route.dependant.dependencies])


if __name__ == "__main__":
    unittest.main()
