"""Verify discount authority through HTTP and disposable PostgreSQL races."""
import os
import unittest
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from pathlib import Path
from threading import Event
from unittest.mock import patch
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import auth
import main
import models
import schemas
import test_save_rejection_http as http_fixtures
import test_transaction_safety as transaction_fixtures


class DiscountPolicyHttpTests(unittest.TestCase):
    post = http_fixtures.SaveRejectionHttpTests.post

    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        models.Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        with self.Session() as db:
            owner = models.User(username="discount_owner", password_hash="unused", role="owner")
            employee = models.User(username="discount_employee", password_hash="unused", role="employee")
            customer = models.Customer(name="Discount fixture", phone="0700000000")
            services = [models.Service(code=f"discount_{n}", name=f"Fixture service {n}",
                                       unit="item", unit_price=500, item_recording_mode="none") for n in (1, 2)]
            db.add_all([owner, employee, customer, *services])
            db.commit()
            self.customer_id = customer.id
            self.service_ids = [service.id for service in services]
            self.user_ids = {user.role: user.id for user in (owner, employee)}
            self.tokens = {user.role: auth.create_access_token(user.id, user.role, user.token_version)
                           for user in (owner, employee)}
        def get_test_db():
            with self.Session() as db:
                yield db
        self.previous_overrides = main.app.dependency_overrides.copy()
        main.app.dependency_overrides[main.get_db] = get_test_db

    def tearDown(self):
        main.app.dependency_overrides.clear()
        main.app.dependency_overrides.update(self.previous_overrides)
        self.engine.dispose()

    def policy(self, percent, revision=0, **kwargs):
        return self.post("/settings/discount-policy", {
            "employee_max_discount_percent": percent, "expected_revision": revision,
        }, **kwargs)

    def order(self, discounts=(60, 40), **changes):
        return {"customer_id": self.customer_id, "discount_reason": "Owner-approved fixture offer",
                "services": [{"service_id": sid, "quantity": 1, "discount_amount": amount}
                             for sid, amount in zip(self.service_ids, discounts)], **changes}

    def test_default_policy_read_requires_login_and_writes_require_owner(self):
        for role in ("owner", "employee"):
            status, result = self.post("/settings/discount-policy", {}, role=role, method="GET")
            self.assertEqual(status, 200)
            self.assertEqual(Decimal(result["employee_max_discount_percent"]), 0)
            self.assertEqual(result["revision"], 0)
        self.assertEqual(self.post("/settings/discount-policy", {}, role=None, method="GET")[0], 401)
        self.assertEqual(self.policy(10, role="employee")[0], 403)
        self.assertEqual(self.post("/settings/discount-policy/history", {}, role="employee", method="GET")[0], 403)
        with self.Session() as db:
            self.assertEqual(db.query(models.DiscountPolicyChange).count(), 0)
            self.assertEqual(db.query(models.DiscountPolicy).count(), 0)

    def test_invalid_and_tampered_policy_fields_do_not_write(self):
        for value in (-1, 101, "NaN", "Infinity", "0.001", "not a percentage"):
            with self.subTest(value=value):
                self.assertEqual(self.policy(value)[0], 422)
        for extra in ({"role": "owner"}, {"revision": 999}, {"updated_at": "2026-01-01"}):
            self.assertEqual(self.post("/settings/discount-policy", {
                "employee_max_discount_percent": 10, "expected_revision": 0, **extra,
            })[0], 422)
        self.assertEqual(self.policy(10, True)[0], 422)
        with self.Session() as db:
            self.assertEqual(db.query(models.DiscountPolicyChange).count(), 0)

    def test_zero_default_blocks_discount_but_allows_full_price_order(self):
        status, result = self.post("/orders/detailed", self.order(), role="employee")
        self.assertEqual(status, 409)
        self.assertEqual(result["detail"]["code"], "QLMS-DISCOUNT-LIMIT")
        self.assertEqual(result["detail"]["save_state"], "not_saved")
        with self.Session() as db:
            self.assertEqual(db.query(models.Order).count(), 0)
            self.assertEqual(db.query(models.TicketCounter).count(), 0)
        status, result = self.post("/orders/detailed", self.order((0, 0)), role="employee")
        self.assertEqual(status, 200)
        self.assertEqual(result["total_price"], 1000)

    def test_whole_order_boundary_split_lines_and_authority_tampering(self):
        self.assertEqual(self.policy(10)[0], 200)
        status, accepted = self.post("/orders/detailed", self.order(), role="employee")
        self.assertEqual(status, 200)
        self.assertEqual(accepted["total_price"], 900)
        for discounts in ((60, 40.01), (100, 100)):
            status, result = self.post("/orders/detailed", self.order(discounts,
                role="owner", employee_max_discount_percent=100), role="employee")
            self.assertEqual(status, 409)
            self.assertEqual(result["detail"]["code"], "QLMS-DISCOUNT-LIMIT")
        with self.Session() as db:
            self.assertEqual(db.query(models.Order).count(), 1)

    def test_fractional_cent_allowance_rounds_down(self):
        self.policy(50)
        with self.Session() as db:
            db.get(models.Service, self.service_ids[0]).unit_price = Decimal("1.99")
            db.commit()
        def body(discount):
            return self.order() | {"services": [{"service_id": self.service_ids[0], "quantity": 1, "discount_amount": discount}]}
        self.assertEqual(self.post("/orders/detailed", body(0.99), role="employee")[0], 200)
        self.assertEqual(self.post("/orders/detailed", body(1), role="employee")[0], 409)
        with self.Session() as db:
            for service_id in self.service_ids:
                service = db.get(models.Service, service_id)
                service.unit = "kg"
                service.unit_price = Decimal("1.33")
            db.commit()
        rounded_lines = self.order((1, 1))
        for line in rounded_lines["services"]:
            line["quantity"] = 1.5
        status, accepted = self.post("/orders/detailed", rounded_lines, role="employee")
        self.assertEqual(status, 200)
        self.assertEqual(accepted["total_price"], 2)

    def test_owner_can_exceed_employee_ceiling_but_not_service_subtotal(self):
        self.assertEqual(self.post("/orders/detailed", self.order((200, 200)))[0], 200)
        self.assertEqual(self.post("/orders/detailed", self.order((500, 0)))[0], 400)

    def test_accepted_order_and_payment_replay_after_limit_reduction(self):
        self.policy(10)
        key = uuid4()
        body = self.order(initial_payment={"payment_method": "cash", "amount": 900, "confirmed": True})
        status, first = self.post("/orders/detailed", body, key, role="employee")
        self.assertEqual(status, 200)
        self.assertEqual(self.policy(0, 1)[0], 200)
        status, again = self.post("/orders/detailed", body, key, role="employee")
        self.assertEqual(status, 200)
        self.assertEqual(again["id"], first["id"])
        self.assertEqual(again["total_price"], 900)
        with self.Session() as db:
            self.assertEqual(db.query(models.Order).count(), 1)
            self.assertEqual(db.query(models.Payment).count(), 1)

    def test_policy_retry_returns_current_limit_without_reverting_or_duplicate_history(self):
        key = uuid4()
        self.assertEqual(self.policy(10, key=key)[0], 200)
        self.assertEqual(self.policy(5, 1)[0], 200)
        status, replay = self.policy(10, key=key)
        self.assertEqual(status, 200)
        self.assertEqual(Decimal(replay["employee_max_discount_percent"]), 5)
        status, conflict = self.policy(15, key=key)
        self.assertEqual(status, 409)
        self.assertEqual(conflict["detail"]["save_state"], "unknown")
        status, history = self.post("/settings/discount-policy/history", {}, method="GET")
        self.assertEqual(status, 200)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[1]["confirmed_by_username"], "discount_owner")
        self.assertNotIn("request_key", history[0])
        self.assertNotIn("request_hash", history[0])

    def test_stale_policy_change_is_rejected_without_another_history_event(self):
        self.policy(10)
        status, result = self.policy(20)
        self.assertEqual(status, 409)
        self.assertEqual(result["detail"]["save_state"], "not_saved")
        with self.Session() as db:
            self.assertEqual(db.query(models.DiscountPolicyChange).count(), 1)

    def test_disabled_and_revoked_accounts_cannot_read_or_change_policy(self):
        with self.Session() as db:
            db.get(models.User, self.user_ids["employee"]).is_active = False
            db.get(models.User, self.user_ids["owner"]).token_version += 1
            db.commit()
        self.assertEqual(self.post("/settings/discount-policy", {}, role="employee", method="GET")[0], 401)
        self.assertEqual(self.policy(10)[0], 401)


@unittest.skipUnless(os.getenv("QLMS_TEST_DATABASE_URL"), "Requires disposable local PostgreSQL")
class DiscountPolicyPostgresTests(unittest.TestCase):
    seed = transaction_fixtures.SaveFixtures.seed
    tearDown = transaction_fixtures.PostgresSaveTests.tearDown
    race = transaction_fixtures.PostgresSaveTests.race

    def setUp(self):
        transaction_fixtures.PostgresSaveTests.setUp(self)
        self.service.unit_price = 1000
        owner = models.User(username="policy_owner", role="owner", password_hash="unused")
        self.db.add_all([owner, models.DiscountPolicy(id=1, employee_max_discount_percent=10, revision=0)])
        self.db.commit()
        self.owner_id = owner.id

    def update(self, db, value, key=None, revision=0):
        return main.update_discount_policy(schemas.DiscountPolicyUpdate(
            employee_max_discount_percent=value, expected_revision=revision,
        ), db, db.get(models.User, self.owner_id), idempotency_key=key or uuid4())

    def create(self, db, user, key=None):
        return main.create_detailed_order(schemas.DetailedOrderCreate(
            customer_id=self.customer_id, discount_reason="Approved fixture discount",
            services=[{"service_id": self.service_id, "quantity": 1, "discount_amount": 100}],
            initial_payment={"payment_method": "cash", "amount": 900, "confirmed": True},
        ), db, user, idempotency_key=key or uuid4())

    def test_concurrent_owner_changes_reject_stale_revision(self):
        outcomes = self.race([lambda db, user: self.update(db, 5), lambda db, user: self.update(db, 20)])
        self.assertEqual(sorted(status for status, _ in outcomes), [200, 409])
        self.assertEqual(self.db.query(models.DiscountPolicyChange).count(), 1)

    def test_concurrent_same_policy_save_creates_one_history_event(self):
        key = uuid4()
        operation = lambda db, user: self.update(db, 5, key)
        self.assertEqual([status for status, _ in self.race([operation, operation])], [200, 200])
        self.assertEqual(self.db.query(models.DiscountPolicyChange).count(), 1)

    def test_order_waits_for_lowered_policy_before_acceptance(self):
        holding, release, checking = Event(), Event(), Event()
        original_commit = main.commit_once
        original_enforce = main.enforce_employee_discount
        def delayed_commit(db, record_type, *args):
            if record_type is models.DiscountPolicyChange:
                holding.set()
                if not release.wait(8):
                    raise RuntimeError("Test release timed out")
            return original_commit(db, record_type, *args)
        def observed_enforce(*args):
            checking.set()
            return original_enforce(*args)
        def lower():
            with self.Session() as db:
                self.update(db, 0)
        def create():
            with self.Session() as db:
                try:
                    self.create(db, db.get(models.User, self.user_id))
                    return 200
                except HTTPException as error:
                    db.rollback()
                    return error.status_code
        with patch("main.commit_once", delayed_commit), patch("main.enforce_employee_discount", observed_enforce), ThreadPoolExecutor(2) as pool:
            owner = pool.submit(lower)
            try:
                self.assertTrue(holding.wait(5))
                employee = pool.submit(create)
                self.assertTrue(checking.wait(5))
                self.assertFalse(employee.done())
            finally:
                release.set()
            owner.result(timeout=5)
            self.assertEqual(employee.result(timeout=5), 409)
        self.assertEqual(self.db.query(models.Order).count(), 0)
        self.assertEqual(self.db.query(models.Payment).count(), 0)

    def test_accepted_order_holds_policy_until_commit_and_replays_after_reduction(self):
        holding, release, updating = Event(), Event(), Event()
        original_commit = main.commit_once
        key = uuid4()
        def delayed_commit(db, record_type, *args):
            if record_type is models.Order:
                holding.set()
                if not release.wait(8):
                    raise RuntimeError("Test release timed out")
            return original_commit(db, record_type, *args)
        def create():
            with self.Session() as db:
                return self.create(db, db.get(models.User, self.user_id), key).id
        def lower():
            with self.Session() as db:
                updating.set()
                return self.update(db, 0).revision
        with patch("main.commit_once", delayed_commit), ThreadPoolExecutor(2) as pool:
            employee = pool.submit(create)
            try:
                self.assertTrue(holding.wait(5))
                owner = pool.submit(lower)
                self.assertTrue(updating.wait(5))
                self.assertFalse(owner.done())
            finally:
                release.set()
            order_id = employee.result(timeout=5)
            self.assertEqual(owner.result(timeout=5), 1)
        with self.Session() as db:
            self.assertEqual(self.create(db, db.get(models.User, self.user_id), key).id, order_id)
            self.assertEqual(db.query(models.Order).count(), 1)
            self.assertEqual(db.query(models.Payment).count(), 1)

    def test_migration_repeat_preserves_policy_and_denies_browser_roles(self):
        self.db.close()
        migration = (Path(__file__).parents[1] / "migrations" / "022_add_employee_discount_policy.sql").read_text()
        with self.engine.begin() as connection:
            connection.execute(text("DROP TABLE discount_policy_changes; DROP TABLE discount_policies"))
            connection.execute(text("""DO $$ BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN CREATE ROLE anon NOLOGIN; END IF;
                IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN CREATE ROLE authenticated NOLOGIN; END IF;
                END $$"""))
            connection.execute(text(f'ALTER DEFAULT PRIVILEGES IN SCHEMA "{self.schema}" GRANT ALL ON TABLES TO anon, authenticated'))
            connection.execute(text(f'ALTER DEFAULT PRIVILEGES IN SCHEMA "{self.schema}" GRANT ALL ON SEQUENCES TO anon, authenticated'))
        with self.engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
            connection.exec_driver_sql(migration)
            connection.execute(text("UPDATE discount_policies SET employee_max_discount_percent = 12.5"))
            connection.exec_driver_sql(migration)
            self.assertEqual(connection.execute(text("SELECT employee_max_discount_percent FROM discount_policies")).scalar(), Decimal("12.5"))
            for role in ("anon", "authenticated"):
                for table in ("discount_policies", "discount_policy_changes"):
                    self.assertFalse(connection.execute(text("SELECT has_table_privilege(:role, :table, 'SELECT')"), {"role": role, "table": table}).scalar())
                self.assertFalse(connection.execute(text("SELECT has_sequence_privilege(:role, 'discount_policy_changes_id_seq', 'USAGE')"), {"role": role}).scalar())
            self.assertEqual(connection.execute(text("SELECT count(*) FROM pg_class WHERE relnamespace = current_schema()::regnamespace AND relrowsecurity AND relname IN ('discount_policies', 'discount_policy_changes')")).scalar(), 2)
            self.assertEqual(connection.execute(text("SELECT count(*) FROM customers")).scalar(), 1)
        self.db = self.Session()
