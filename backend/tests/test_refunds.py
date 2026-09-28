"""Truthful charges, money returns, custody and recovery across the refund API."""
import asyncio
import csv
import io
import os
import unittest
from datetime import timedelta, datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import text

import main
import models
import schemas
import test_payment_corrections as payments
import test_save_rejection_http as http_tests
import test_transaction_safety as safety


class RefundTests(unittest.TestCase):
    setUp = payments.PaymentCorrectionTests.setUp
    tearDown = payments.PaymentCorrectionTests.tearDown

    def refund(self, amount=100, purpose="service_refund", key=None, **changes):
        body = dict(payment_id=self.payment.id, refund_purpose=purpose, refund_method="cash",
                    amount=amount, reason="Agreed service refund", confirmed=True,
                    effective_date=main.get_nairobi_today())
        body.update(changes)
        return main.refund_order_payment(self.order.id, schemas.RefundCreate(**body),
                                        self.db, self.owner, idempotency_key=key or uuid4())

    def test_collected_service_refund_agrees_with_finance_csv_and_retry(self):
        self.order.total_price = self.payment.amount = 1000
        self.order.status = "collected"
        self.order.collected_at = datetime(2026, 9, 1, tzinfo=timezone.utc)
        self.db.commit()
        collected_at = self.order.collected_at
        key = uuid4()
        self.refund(200, key=key)
        order = self.refund(200, key=key)  # The first reply may never reach the browser.
        self.assertEqual((order.net_charge, order.amount_paid, order.balance_due, order.refund_due),
                         (800, 800, 0, 0))
        self.assertEqual(order.status, "collected")
        self.assertEqual(order.collected_at, collected_at)
        self.assertEqual(order.total_price, 1000)
        self.assertEqual(order.payments[0].amount, 1000)
        self.assertEqual(len(order.payment_adjustments), 1)
        report = main.financial_summary(self.payment_date, main.get_nairobi_today(), self.db, self.owner)
        self.assertEqual((report.order_value, report.net_charge, report.service_refunds), (1000, 800, 200))
        self.assertEqual((report.total_received, report.refunds_sent, report.net_cash_movement), (1000, 200, 800))
        self.assertEqual(report.outstanding_balance, 0)
        self.assertEqual(report.refund_due, 0)
        async def read_csv():
            response = main.export_orders_csv(self.db, self.owner)
            return "".join([part async for part in response.body_iterator])
        row = next(csv.DictReader(io.StringIO(asyncio.run(read_csv()))))
        self.assertEqual((row["Net Charge"], row["Amount Paid"], row["Balance Due"], row["Refund Due"]),
                         ("800.00", "800.00", "0.00", "0.00"))
        self.assertEqual(row["Status"], "collected")
        self.assertIn("purpose=service_refund", row["Payment Adjustment History"])

    def test_excess_return_does_not_reduce_the_corrected_charge_twice(self):
        main.correct_order_quantity(self.order.id, schemas.OrderQuantityCorrectionCreate(
            expected_quantity=2, new_quantity=1, reason="Correct scale reading", confirmed=True),
            self.db, self.owner, idempotency_key=uuid4())
        self.assertEqual((self.order.net_charge, self.order.refund_due, self.order.balance_due), (150, 150, 0))
        self.assertEqual(self.order.payment_status, "refund_due")
        self.refund(100, purpose="excess_payment")
        self.assertEqual((self.order.net_charge, self.order.refund_due), (150, 50))
        self.refund(50, purpose="excess_payment")
        self.assertEqual((self.order.net_charge, self.order.amount_paid, self.order.refund_due), (150, 150, 0))

    def test_full_refund_is_settled_and_cannot_return_again(self):
        order = self.refund(300)
        self.assertEqual((order.net_charge, order.amount_paid, order.payment_status), (0, 0, "settled"))
        with self.assertRaises(HTTPException):
            self.refund(1)
        self.db.rollback()
        self.assertEqual(self.db.query(models.PaymentAdjustment).count(), 1)

    def test_bounds_dates_confirmation_and_wrong_payment_write_nothing(self):
        for changes in [dict(amount=301), dict(purpose="excess_payment"), dict(confirmed=False),
                        dict(payment_id=999), dict(effective_date=self.payment_date - timedelta(days=1)),
                        dict(effective_date=main.get_nairobi_today() + timedelta(days=1))]:
            with self.subTest(changes=changes), self.assertRaises(HTTPException):
                self.refund(**changes)
            self.db.rollback()
        self.assertEqual(self.db.query(models.PaymentAdjustment).count(), 0)

    def test_entry_correction_after_collection_can_be_settled_by_owner(self):
        self.order.status = "collected"
        self.db.commit()
        main.adjust_order_payment(self.order.id, self.payment.id, schemas.PaymentAdjustmentCreate(
            kind="entry_error", amount=50, confirmed=True, reason="Cash receipt checked"),
            self.db, self.owner, idempotency_key=uuid4())
        body = schemas.PaymentCreate(payment_method="cash", amount=50, confirmed=True)
        with self.assertRaises(HTTPException):
            main.record_order_payment(self.order.id, body, self.db, self.employee, idempotency_key=uuid4())
        self.db.rollback()
        main.record_order_payment(self.order.id, body, self.db, self.owner, idempotency_key=uuid4())
        self.assertEqual((self.order.status, self.order.balance_due), ("collected", 0))

    def test_old_refund_replays_but_new_ambiguous_refunds_are_rejected(self):
        body = schemas.PaymentAdjustmentCreate(kind="refund", amount=100, refund_method="cash",
                                               reason="Older return", confirmed=True)
        key = uuid4()
        self.db.add(models.PaymentAdjustment(order_id=self.order.id, payment_id=self.payment.id,
            kind="refund", refund_method="cash", amount=100, reason=body.reason,
            effective_date=self.payment_date, request_key=str(key),
            request_hash=main.request_fingerprint(f"payment-adjustment:{self.order.id}:{self.payment.id}", body),
            confirmed_by_id=self.owner.id, confirmed_by_username=self.owner.username))
        self.db.commit()
        main.adjust_order_payment(self.order.id, self.payment.id, body, self.db, self.owner, idempotency_key=key)
        self.assertEqual(self.order.net_charge, 300)  # No guessed charge reduction.
        self.assertIsNone(self.order.payment_adjustments[0].refund_purpose)
        with self.assertRaises(HTTPException):
            main.adjust_order_payment(self.order.id, self.payment.id, body, self.db, self.owner, idempotency_key=uuid4())
        self.assertEqual(self.db.query(models.PaymentAdjustment).count(), 1)


class RefundHttpTests(unittest.TestCase):
    setUp = http_tests.SaveRejectionHttpTests.setUp
    tearDown = http_tests.SaveRejectionHttpTests.tearDown
    post = http_tests.SaveRejectionHttpTests.post

    def test_owner_only_strict_fields_and_lost_reply_replay(self):
        with self.Session() as db:
            payment = models.Payment(order_id=self.order_id, amount=300, payment_method="cash",
                                     confirmed_by_username="test_employee", received_date=main.get_nairobi_today())
            db.add(payment)
            db.commit()
            payment_id = payment.id
        path = f"/orders/{self.order_id}/refunds"
        body = dict(payment_id=payment_id, refund_purpose="service_refund", refund_method="cash",
                    amount=100, reason="Refund agreed", confirmed=True, effective_date=str(main.get_nairobi_today()))
        self.assertEqual(self.post(path, body, role="employee")[0], 403)
        self.assertEqual(self.post(path, body, role=None)[0], 401)
        for changes in [dict(net_charge=0), dict(amount=1.001), dict(amount=-1), dict(amount="NaN"),
                        dict(refund_purpose="anything"), dict(confirmed="yes"), dict(reason=" ")]:
            with self.subTest(changes=changes):
                self.assertEqual(self.post(path, {**body, **changes})[0], 422)
        key = uuid4()
        for _ in range(2):
            status, result = self.post(path, body, key=key)
            self.assertEqual(status, 200)
            self.assertEqual((result["net_charge"], result["amount_paid"], result["balance_due"]), (200, 200, 0))
        self.assertEqual(self.post(path, {**body, "amount": 90}, key=key)[0], 409)
        with self.Session() as db:
            self.assertEqual(db.query(models.PaymentAdjustment).count(), 1)


@unittest.skipUnless(os.getenv("QLMS_TEST_DATABASE_URL"), "Requires disposable local PostgreSQL")
class PostgresRefundTests(safety.SaveFixtures, unittest.TestCase):
    setUp = safety.PostgresSaveTests.setUp
    tearDown = safety.PostgresSaveTests.tearDown
    race = safety.PostgresSaveTests.race

    def paid_order(self):
        self.user.role = "owner"
        self.db.commit()
        order = self.create(self.body(initial_payment={"payment_method": "cash", "confirmed": True}))
        body = schemas.RefundCreate(payment_id=order.payments[0].id, refund_purpose="service_refund",
                                    refund_method="cash", amount=200, reason="Agreed refund", confirmed=True,
                                    effective_date=main.get_nairobi_today())
        return order.id, body

    def test_two_refunds_cannot_exceed_payment(self):
        order_id, body = self.paid_order()
        operation = lambda db, user: main.refund_order_payment(order_id, body, db, user, idempotency_key=uuid4())
        self.assertEqual(sorted(status for status, _ in self.race([operation, operation])), [200, 400])
        self.db.expire_all()
        order = self.db.get(models.Order, order_id)
        self.assertEqual((order.net_charge, order.amount_paid, order.balance_due), (100, 100, 0))
        self.assertEqual(len(order.payment_adjustments), 1)

    def test_concurrent_retry_returns_one_event(self):
        order_id, body = self.paid_order()
        key = uuid4()
        operation = lambda db, user: main.refund_order_payment(order_id, body, db, user, idempotency_key=key)
        self.assertEqual([status for status, _ in self.race([operation, operation])], [200, 200])
        self.assertEqual(self.db.query(models.PaymentAdjustment).count(), 1)

    def test_quantity_correction_and_service_refund_serialize_charge_checks(self):
        order_id, refund = self.paid_order()
        line_id = self.db.get(models.Order, order_id).service_lines[0].id
        correction = schemas.OrderQuantityCorrectionCreate(service_line_id=line_id,
            expected_quantity=2, new_quantity=1, reason="Scale verified", confirmed=True)
        outcomes = self.race([
            lambda db, user: main.refund_order_payment(order_id, refund, db, user, idempotency_key=uuid4()),
            lambda db, user: main.correct_order_quantity(order_id, correction, db, user, idempotency_key=uuid4()),
        ])
        self.assertEqual(sorted(status for status, _ in outcomes), [200, 400])
        self.db.expire_all()
        order = self.db.get(models.Order, order_id)
        self.assertGreaterEqual(order.net_charge, 0)
        self.assertEqual(order.balance_due, 0)

    def test_migration_leaves_existing_refund_unclassified_and_repeats(self):
        order_id, body = self.paid_order()
        self.db.add(models.PaymentAdjustment(order_id=order_id, payment_id=body.payment_id,
            kind="refund", amount=50, refund_method="cash", reason="Old return",
            effective_date=main.get_nairobi_today(), confirmed_by_username="save_test"))
        self.db.commit()
        self.db.close()
        with self.engine.begin() as connection:
            connection.exec_driver_sql("ALTER TABLE payment_adjustments DROP COLUMN refund_purpose CASCADE")
        migration = (Path(__file__).parents[1] / "migrations/021_add_refund_purpose.sql").read_text()
        with self.engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
            connection.exec_driver_sql(migration)
            connection.exec_driver_sql(migration)
            self.assertEqual(connection.execute(text("SELECT amount, refund_purpose FROM payment_adjustments")).one(), (Decimal("50"), None))
