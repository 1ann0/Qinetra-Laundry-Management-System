"""Private owner preferences must not expose contacts or grant automation access."""
import os
import unittest
from pathlib import Path
from uuid import uuid4

from sqlalchemy import text

import models
import schemas
import test_discount_policy as policy_fixtures
import test_transaction_safety as transaction_fixtures


class AlertSettingsHttpTests(unittest.TestCase):
    setUp = policy_fixtures.DiscountPolicyHttpTests.setUp
    tearDown = policy_fixtures.DiscountPolicyHttpTests.tearDown
    post = policy_fixtures.DiscountPolicyHttpTests.post

    def save(self, email="owner@example.test", time="22:00", revision=0, **options):
        return self.post("/settings/alerts", {"owner_email": email, "backup_time": time,
                         "expected_revision": revision}, **options)

    def test_owner_default_is_private_and_does_not_claim_active_automation(self):
        status, settings = self.post("/settings/alerts", {}, method="GET")
        self.assertEqual(status, 200)
        self.assertIsNone(settings["owner_email"])
        self.assertEqual(settings["backup_time"], "22:00")
        self.assertEqual(settings["timezone"], "Africa/Nairobi")
        self.assertEqual(settings["automation_status"], "not_configured")
        for path in ("/settings/alerts", "/settings/alerts/history"):
            self.assertEqual(self.post(path, {}, role="employee", method="GET")[0], 403)
            self.assertEqual(self.post(path, {}, role=None, method="GET")[0], 401)
        self.assertEqual(self.save(role="employee")[0], 403)

    def test_invalid_emails_times_and_privilege_fields_never_save(self):
        for email in ("", "two addresses@example.test,other@example.test", "person@example.test\r\nBcc: other@example.test",
                      "wrong", ".name@example.test", "name..name@example.test", "a" * 65 + "@example.test"):
            self.assertEqual(self.save(email=email)[0], 422, email)
        for time in ("24:00", "22:60", "9:00", "2026-10-08T22:00", "NaN"):
            self.assertEqual(self.save(time=time)[0], 422, time)
        for field in ("role", "automation_status", "email_verified", "stakeholder_email", "timezone"):
            self.assertEqual(self.post("/settings/alerts", {"owner_email": "owner@example.test", "backup_time": "22:00",
                             "expected_revision": 0, field: "owner"})[0], 422)
        self.assertEqual(self.save(revision=True)[0], 422)
        with self.Session() as db:
            self.assertEqual(db.query(models.AlertSettingsChange).count(), 0)

    def test_history_retry_and_later_edit_preserve_current_preferences(self):
        key = uuid4()
        self.assertEqual(self.save(email=" owner+alerts@EXAMPLE.test ", key=key)[0], 200)
        self.assertEqual(self.save(email="second@example.test", time="04:30", revision=1)[0], 200)
        status, replay = self.save(email=" owner+alerts@EXAMPLE.test ", key=key)
        self.assertEqual(status, 200)
        self.assertEqual(replay["owner_email"], "second@example.test")
        self.assertEqual(replay["backup_time"], "04:30")
        status, conflict = self.save(email="tampered@example.test", key=key)
        self.assertEqual(status, 409)
        self.assertEqual(conflict["detail"]["save_state"], "unknown")
        status, history = self.post("/settings/alerts/history", {}, method="GET")
        self.assertEqual(status, 200)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["confirmed_by_username"], "discount_owner")
        self.assertEqual(history[1]["after_email"], "owner+alerts@example.test")

    def test_stale_edit_and_disabled_owner_cannot_change_contacts(self):
        self.assertEqual(self.save()[0], 200)
        status, stale = self.save(time="05:00")
        self.assertEqual(status, 409)
        self.assertEqual(stale["detail"]["save_state"], "not_saved")
        with self.Session() as db:
            db.get(models.User, self.user_ids["owner"]).is_active = False
            db.commit()
        self.assertEqual(self.save(revision=1)[0], 401)
        self.assertEqual(self.post("/settings/alerts", {}, method="GET")[0], 401)


@unittest.skipUnless(os.getenv("QLMS_TEST_DATABASE_URL"), "Requires disposable PostgreSQL")
class AlertSettingsPostgresTests(unittest.TestCase):
    seed = transaction_fixtures.SaveFixtures.seed
    tearDown = transaction_fixtures.PostgresSaveTests.tearDown
    race = transaction_fixtures.PostgresSaveTests.race

    def setUp(self):
        transaction_fixtures.PostgresSaveTests.setUp(self)
        self.user.role = "owner"
        self.db.commit()

    def update(self, db, user, key):
        from alert_settings import update_alert_settings
        return update_alert_settings(schemas.AlertSettingsUpdate(owner_email="owner@example.test", backup_time="22:00",
                                     expected_revision=0), db, user, idempotency_key=key)

    def test_concurrent_new_settings_reject_stale_and_same_key_replays_once(self):
        outcomes = self.race([lambda db, user: self.update(db, user, uuid4()),
                              lambda db, user: self.update(db, user, uuid4())])
        self.assertEqual(sorted(status for status, _ in outcomes), [200, 409])
        self.assertEqual(self.db.query(models.AlertSettingsChange).count(), 1)
        with self.engine.begin() as connection:
            connection.execute(text("DELETE FROM alert_settings_changes; DELETE FROM alert_settings"))
        key = uuid4()
        operation = lambda db, user: self.update(db, user, key)
        self.assertEqual([status for status, _ in self.race([operation, operation])], [200, 200])
        self.assertEqual(self.db.query(models.AlertSettingsChange).count(), 1)

    def test_repeat_migration_preserves_settings_and_denies_browser_access(self):
        migration = (Path(__file__).parents[1] / "migrations/024_add_alert_settings.sql").read_text()
        self.db.close()
        with self.engine.begin() as connection:
            connection.execute(text("DROP TABLE alert_settings_changes; DROP TABLE alert_settings"))
        with self.engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
            connection.exec_driver_sql(migration)
            connection.execute(text("UPDATE alert_settings SET backup_minute=270"))
            connection.exec_driver_sql(migration)
            self.assertEqual(connection.execute(text("SELECT backup_minute FROM alert_settings")).scalar(), 270)
            for table in ("alert_settings", "alert_settings_changes"):
                self.assertTrue(connection.execute(text("SELECT relrowsecurity FROM pg_class WHERE oid=to_regclass(:table)"), {"table": table}).scalar())
                for role in ("anon", "authenticated"):
                    if connection.execute(text("SELECT EXISTS(SELECT 1 FROM pg_roles WHERE rolname=:role)"), {"role": role}).scalar():
                        self.assertFalse(connection.execute(text("SELECT has_table_privilege(:role,:table,'SELECT')"), {"role": role, "table": table}).scalar())
