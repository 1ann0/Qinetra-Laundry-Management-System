"""Save recovery contracts; PostgreSQL cases use a disposable, local schema only."""
import os
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from threading import Barrier
from unittest.mock import patch
from uuid import uuid4

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

import logic
import main
import models
import schemas


class SaveFixtures:
    def seed(self):
        self.db = self.Session()
        self.user = models.User(username="save_test", password_hash="unused", role="employee")
        self.customer = models.Customer(name="Save test", phone="0700000000")
        self.service = models.Service(code="wash_fold", name="Wash & Fold", unit="kg", unit_price=150, item_recording_mode="tally")
        self.item = models.ClothingItemType(name="Shirt")
        self.db.add_all([self.user, self.customer, self.service, self.item])
        self.db.commit()
        self.user_id, self.customer_id, self.service_id = self.user.id, self.customer.id, self.service.id

    def body(self, **changes):
        fields = {"customer_id": self.customer_id, "services": [{"service_id": self.service_id, "quantity": 2}]}
        fields.update(changes)
        return schemas.DetailedOrderCreate(**fields)

    def create(self, body=None, key=None):
        return main.create_detailed_order(body or self.body(), self.db, self.user, idempotency_key=key or uuid4())


class SaveContractTests(SaveFixtures, unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        models.Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.seed()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_retry_returns_original_order_and_initial_payment_after_price_change(self):
        key = uuid4()
        body = self.body(initial_payment={"payment_method": "cash", "confirmed": True})
        first = self.create(body, key)
        self.assertEqual(first.amount_paid, Decimal("300"))
        self.service.unit_price = 200
        self.db.commit()
        again = self.create(body, key)
        self.assertEqual(first.id, again.id)
        self.assertEqual(again.total_price, Decimal("300"))
        self.assertEqual(len(again.payments), 1)
        self.assertEqual(again.service_lines[0].unit_price, Decimal("150"))

    def test_reused_key_rejects_different_details_and_another_actor(self):
        key = uuid4()
        self.create(key=key)
        with self.assertRaises(HTTPException) as changed:
            self.create(self.body(services=[{"service_id": self.service_id, "quantity": 3}]), key)
        self.assertEqual(changed.exception.status_code, 409)
        other = models.User(username="other", password_hash="unused", role="employee")
        self.db.add(other)
        self.db.commit()
        with self.assertRaises(HTTPException) as actor:
            main.create_detailed_order(self.body(), self.db, other, idempotency_key=key)
        self.assertEqual(actor.exception.status_code, 409)

    def test_invalid_initial_payment_rolls_back_order_and_counter(self):
        with self.assertRaises(HTTPException):
            self.create(self.body(initial_payment={"payment_method": "cash", "amount": 301, "confirmed": True}))
        self.db.rollback()
        self.assertEqual(self.db.query(models.Order).count(), 0)
        self.assertEqual(self.db.query(models.Payment).count(), 0)
        self.assertEqual(self.db.query(models.TicketCounter).count(), 0)
        self.assertTrue(self.create().ticket_number.endswith("-001"))

    def test_payment_retry_after_collection_does_not_add_money(self):
        order = self.create()
        key = uuid4()
        body = schemas.PaymentCreate(payment_method="cash", amount=300, confirmed=True)
        main.record_order_payment(order.id, body, self.db, self.user, idempotency_key=key)
        order.status = "collected"
        self.db.commit()
        again = main.record_order_payment(order.id, body, self.db, self.user, idempotency_key=key)
        self.assertEqual(again.amount_paid, Decimal("300"))
        self.assertEqual(self.db.query(models.Payment).count(), 1)

    def test_clothing_revision_rejects_an_old_editor(self):
        order = self.create()
        line = order.service_lines[0]
        body = schemas.OrderItemsUpdate(items=[{"item_type_id": self.item.id, "quantity": 1}], expected_revision=0)
        saved = main.replace_order_service_items(order.id, line.id, body, self.db, self.user)
        self.assertEqual(saved.item_revision, 1)
        with self.assertRaises(HTTPException) as stale:
            main.replace_order_service_items(order.id, line.id, body, self.db, self.user)
        self.assertEqual(stale.exception.status_code, 409)
        self.assertEqual(len(saved.items), 1)

    def test_duplicate_status_update_cannot_skip_forward(self):
        order = self.create(self.body(services=[{
            "service_id": self.service_id,
            "quantity": 2,
            "items": [{"item_type_id": self.item.id, "quantity": 2}],
        }]))
        body = schemas.OrderStatusUpdate(status="in_progress")
        main.update_order_status(order.id, body, self.db, self.user)
        with self.assertRaises(HTTPException):
            main.update_order_status(order.id, body, self.db, self.user)
        self.assertEqual(order.status, "in_progress")

    def test_ticket_high_suffix_and_deleted_ticket_do_not_reuse_numbers(self):
        order = self.create()
        prefix = order.ticket_number.rsplit("-", 1)[0]
        order.ticket_number = prefix + "-1000"
        self.db.commit()
        next_order = self.create()
        self.assertEqual(next_order.ticket_number, prefix + "-1001")
        self.db.delete(next_order)
        self.db.commit()
        self.assertEqual(self.create().ticket_number, prefix + "-1002")

    def test_daily_counters_and_nairobi_midnight(self):
        yesterday = main.get_nairobi_today() - timedelta(days=1)
        first = self.create(self.body(order_date=yesterday))
        second = self.create()
        self.assertTrue(first.ticket_number.endswith("-001"))
        self.assertTrue(second.ticket_number.endswith("-001"))
        instant = datetime(2026, 9, 8, 21, 1, tzinfo=timezone.utc)
        with patch("logic.datetime") as clock:
            clock.now.side_effect = lambda tz: instant.astimezone(tz)
            self.assertTrue(logic.generate_ticket_number(self.db).startswith("QL-20260909-"))

    def test_decimal_rounding_and_quantity_precision(self):
        self.assertEqual(logic.money("1.005"), Decimal("1.01"))
        self.service.unit_price = Decimal("1.01")
        self.db.commit()
        order = self.create(self.body(services=[{"service_id": self.service_id, "quantity": 0.5}]))
        self.assertEqual(order.total_price, Decimal("0.51"))
        for quantity in [float("inf"), float("nan"), 1.001, 0, -1]:
            with self.subTest(quantity=quantity), self.assertRaises(ValidationError):
                schemas.DetailedOrderServiceCreate(service_id=1, quantity=quantity)


@unittest.skipUnless(os.getenv("QLMS_TEST_DATABASE_URL"), "Set a local QLMS_TEST_DATABASE_URL for real locking tests")
class PostgresSaveTests(SaveFixtures, unittest.TestCase):
    def setUp(self):
        url = make_url(os.environ["QLMS_TEST_DATABASE_URL"])
        if url.get_backend_name() != "postgresql" or url.host not in {"localhost", "127.0.0.1"} or url.database != "qlms_test":
            raise RuntimeError("Concurrency tests require a local PostgreSQL database named qlms_test")
        self.schema = "save_test_" + uuid4().hex
        self.admin = create_engine(url)
        with self.admin.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA "{self.schema}"'))
        self.engine = create_engine(url, connect_args={"options": f"-csearch_path={self.schema} -clock_timeout=10000 -cstatement_timeout=20000"})
        models.Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.seed()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()
        # Only this test's randomly named schema is removed; public is never touched.
        with self.admin.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{self.schema}" CASCADE'))
        self.admin.dispose()

    def race(self, operations):
        barrier = Barrier(len(operations))
        def run(operation):
            with self.Session() as db:
                user = db.get(models.User, self.user_id)
                barrier.wait(timeout=10)
                try:
                    result = operation(db, user)
                    return (200, result.id)
                except HTTPException as error:
                    db.rollback()
                    return (error.status_code, error.detail)
        with ThreadPoolExecutor(max_workers=len(operations)) as pool:
            return list(pool.map(run, operations))

    def test_simultaneous_orders_have_unique_tickets(self):
        body = self.body()
        outcomes = self.race([lambda db, user: main.create_detailed_order(body, db, user, idempotency_key=uuid4()) for _ in range(6)])
        self.assertTrue(all(status == 200 for status, _ in outcomes), outcomes)
        tickets = [row.ticket_number for row in self.db.query(models.Order).all()]
        self.assertEqual(len(set(tickets)), 6)

    def test_simultaneous_same_key_saves_one_order_and_initial_payment(self):
        key = uuid4()
        body = self.body(initial_payment={"payment_method": "cash", "amount": 100, "confirmed": True})
        operation = lambda db, user: main.create_detailed_order(body, db, user, idempotency_key=key)
        outcomes = self.race([operation, operation])
        self.assertEqual(outcomes[0], outcomes[1])
        self.assertEqual(outcomes[0][0], 200)
        self.assertEqual(self.db.query(models.Order).count(), 1)
        self.assertEqual(self.db.query(models.Payment).count(), 1)

    def test_concurrent_partial_payments_cannot_exceed_balance(self):
        order_id = self.create().id
        body = schemas.PaymentCreate(payment_method="cash", amount=200, confirmed=True)
        operation = lambda db, user: main.record_order_payment(order_id, body, db, user, idempotency_key=uuid4())
        outcomes = self.race([operation, operation])
        self.assertEqual(sorted(status for status, _ in outcomes), [200, 400])
        self.db.expire_all()
        self.assertEqual(self.db.get(models.Order, order_id).amount_paid, Decimal("200"))

    def test_concurrent_payment_retry_records_once(self):
        order_id = self.create().id
        key = uuid4()
        body = schemas.PaymentCreate(payment_method="cash", amount=100, confirmed=True)
        operation = lambda db, user: main.record_order_payment(order_id, body, db, user, idempotency_key=key)
        outcomes = self.race([operation, operation])
        self.assertEqual(outcomes[0], outcomes[1])
        self.assertEqual(outcomes[0][0], 200)
        self.assertEqual(self.db.query(models.Payment).count(), 1)

    def test_concurrent_editors_cannot_overwrite_the_first_clothing_check(self):
        order = self.create()
        order_id, line_id, item_id = order.id, order.service_lines[0].id, self.item.id
        body = schemas.OrderItemsUpdate(items=[{"item_type_id": item_id, "quantity": 1}], expected_revision=0)
        operation = lambda db, user: main.replace_order_service_items(order_id, line_id, body, db, user)
        outcomes = self.race([operation, operation])
        self.assertEqual(sorted(status for status, _ in outcomes), [200, 409])

    def test_migrations_upgrade_existing_records_and_can_be_repeated(self):
        order_id = self.create().id
        self.db.close()
        with self.engine.begin() as connection:
            connection.execute(text("DROP TABLE order_holds"))
            connection.execute(text("DROP TABLE order_item_check_history"))
            connection.execute(text("DROP TABLE order_item_exceptions"))
            connection.execute(text("ALTER TABLE order_service_lines DROP COLUMN item_checked_by_id, DROP COLUMN item_checked_by_username, DROP COLUMN item_checked_at"))
            connection.execute(text("ALTER TABLE orders DROP COLUMN request_key, DROP COLUMN request_hash, DROP COLUMN created_by_id"))
            connection.execute(text("ALTER TABLE payments DROP COLUMN request_key, DROP COLUMN request_hash"))
            connection.execute(text("ALTER TABLE order_service_lines DROP COLUMN item_revision"))
            connection.execute(text("DROP TABLE ticket_counters"))
        migration_directory = Path(__file__).parents[1] / "migrations"
        transaction_sql = (migration_directory / "010_transaction_safety.sql").read_text()
        item_history_sql = (migration_directory / "011_add_item_condition_history.sql").read_text()
        hold_sql = (migration_directory / "012_add_customer_reply_holds.sql").read_text()
        with self.engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
            connection.exec_driver_sql(transaction_sql)
            connection.exec_driver_sql(transaction_sql)
            connection.exec_driver_sql(item_history_sql)
            connection.exec_driver_sql(item_history_sql)
            connection.exec_driver_sql(hold_sql)
            connection.exec_driver_sql(hold_sql)
            rls_tables = connection.execute(text("""
                SELECT relname
                FROM pg_class
                WHERE relnamespace = current_schema()::regnamespace
                  AND relrowsecurity
                  AND relname IN ('order_item_exceptions', 'order_item_check_history', 'order_holds')
            """)).scalars().all()
        self.db = self.Session()
        # Reload the fixture user after replacing its closed database session.
        self.user = self.db.get(models.User, self.user_id)
        self.assertEqual(self.db.get(models.Order, order_id).total_price, Decimal("300"))
        self.assertEqual(self.db.get(models.Order, order_id).service_lines[0].item_revision, 0)
        self.assertEqual(
            set(rls_tables),
            {"order_item_exceptions", "order_item_check_history", "order_holds"},
        )
        self.assertTrue(self.create().ticket_number.endswith("-002"))
