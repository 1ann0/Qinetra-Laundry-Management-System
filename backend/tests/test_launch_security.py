"""Pilot launch boundaries through real FastAPI requests and database sessions."""
import asyncio
import json
import unittest
import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlencode
from unittest.mock import patch

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import auth
import main
import models
from fastapi import HTTPException
from tests import test_transaction_safety as transaction_fixtures


class LaunchSecurityTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        models.Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.secret = auth.SECRET_KEY
        auth.SECRET_KEY = "launch-security-fictional-secret-at-least-32-bytes"
        with self.Session() as db:
            user = models.User(username="launch_owner", password_hash=auth.hash_password("OwnerPass123"), role="owner")
            disabled = models.User(username="launch_disabled", password_hash=user.password_hash, role="employee", is_active=False)
            customer = models.Customer(name="Fictional launch customer", phone="0700000000", phone_normalized="254700000000")
            db.add_all([user, disabled, customer])
            db.flush()
            order = models.Order(ticket_number="QL-LAUNCH-001", customer_id=customer.id, service_type="=HYPERLINK(\"bad\")",
                                 quantity=1, unit_price=1000, total_price=1000, discount_reason="\t=1+1",
                                 discounted_by_username="+fake", order_date=main.get_nairobi_today())
            db.add(order)
            db.commit()
            self.token = auth.create_access_token(user.id, user.role, user.token_version)
        self.overrides = main.app.dependency_overrides.copy()
        from login_throttle import consume_login_attempt
        # Keep repeated HTTP attempts inside one window, even at a clock boundary.
        self.clock = patch("main.consume_login_attempt", side_effect=lambda db, peer, username: consume_login_attempt(db, peer, username, now=1000))
        self.clock.start()

        def test_db():
            with self.Session() as db:
                yield db

        main.app.dependency_overrides[main.get_db] = test_db

    def tearDown(self):
        self.clock.stop()
        main.app.dependency_overrides.clear()
        main.app.dependency_overrides.update(self.overrides)
        auth.SECRET_KEY = self.secret
        self.engine.dispose()

    def request(self, path, form=None, token=None, headers=None, ip="192.0.2.1", chunks=None, scheme="https"):
        async def run():
            body = urlencode(form).encode() if form is not None else b""
            request_headers = [(b"content-type", b"application/x-www-form-urlencoded")]
            request_headers.extend(headers or [])
            if token:
                request_headers.append((b"authorization", f"Bearer {token}".encode()))
            scope = {"type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
                     "method": "POST" if form is not None else "GET", "scheme": scheme,
                     "path": path, "raw_path": path.encode(), "query_string": b"", "root_path": "",
                     "headers": request_headers, "client": (ip, 1234), "server": ("testserver", 443)}
            messages, pending = [], list(chunks or [body])

            async def receive():
                if pending:
                    return {"type": "http.request", "body": pending.pop(0), "more_body": bool(pending)}
                await asyncio.Event().wait()

            async def send(message):
                messages.append(message)

            await main.app(scope, receive, send)
            start = next(item for item in messages if item["type"] == "http.response.start")
            response_body = b"".join(item.get("body", b"") for item in messages if item["type"] == "http.response.body")
            return start["status"], {k.decode(): v.decode() for k, v in start["headers"]}, response_body

        return asyncio.run(run())

    def login(self, username="launch_owner", password="OwnerPass123", **options):
        return self.request("/auth/login", {"username": username, "password": password}, **options)

    def test_invalid_disabled_and_oversized_passwords_have_generic_failure(self):
        for username, password in [("missing", "OwnerPass123"), ("launch_owner", "wrong"),
                                   ("launch_disabled", "OwnerPass123"), ("launch_owner", "a" * 73),
                                   ("launch_owner", "é" * 37), ("u" * 51, "OwnerPass123")]:
            status, headers, body = self.login(username, password)
            self.assertEqual(status, 401, body)
            self.assertEqual(json.loads(body), {"detail": "Incorrect username or password"})
            self.assertIn("no-store", headers["cache-control"])

    def test_unicode_72_byte_password_is_not_trimmed_or_truncated(self):
        password = "é" * 35 + "x "
        with self.Session() as db:
            user = db.query(models.User).filter_by(username="launch_owner").one()
            user.password_hash = auth.hash_password(password)
            db.commit()
        self.assertEqual(self.login(password=password)[0], 200)
        self.assertEqual(self.login(password=password.strip())[0], 401)

    def test_database_limit_is_shared_and_forwarded_headers_cannot_bypass_it(self):
        for attempt in range(10):
            self.assertEqual(self.login(password="wrong", headers=[(b"x-forwarded-for", f"203.0.113.{attempt}".encode())])[0], 401)
        status, headers, body = self.login()
        self.assertEqual(status, 429, body)
        self.assertGreater(int(headers["retry-after"]), 0)
        self.assertEqual(self.login(ip="192.0.2.2")[0], 200)
        with self.Session() as db:
            buckets = db.query(models.LoginAttemptBucket).all()
            self.assertTrue(all(len(row.bucket_key) == 64 for row in buckets))
            self.assertTrue(all(row.attempts <= 50 for row in buckets))

    def test_login_body_limit_catches_declared_and_chunked_oversize(self):
        for options in [{"headers": [(b"content-length", b"9000")]}, {"chunks": [b"a" * 5000, b"b" * 4000]}]:
            status, headers, body = self.login(**options)
            self.assertEqual(status, 413, body)
            self.assertIn("no-store", headers["cache-control"])
            self.assertNotIn(b"OwnerPass", body)

    def test_csv_neutralizes_text_without_changing_numeric_money(self):
        import csv
        import io
        status, headers, body = self.request("/dashboard/export", token=self.token)
        self.assertEqual(status, 200)
        rows = list(csv.reader(io.StringIO(body.decode())))
        row = dict(zip(rows[0], rows[1]))
        self.assertTrue(row["Services"].startswith("'="))
        self.assertEqual(row["Discount Reason"], "'\t=1+1")
        self.assertEqual(row["Discounted By"], "'+fake")
        self.assertEqual(row["Total Price"], "1000.00")
        self.assertEqual(row["Balance Due"], "1000.00")
        self.assertIn("no-store", headers["cache-control"])

    def test_readiness_detects_missing_columns_and_remains_generic(self):
        self.assertEqual(self.request("/health/ready")[0], 200)
        with self.engine.begin() as connection:
            connection.execute(text("ALTER TABLE users DROP COLUMN token_version"))
        status, headers, body = self.request("/health/ready")
        self.assertEqual(status, 503)
        self.assertEqual(json.loads(body), {"status": "not_ready"})
        self.assertNotIn(b"token_version", body)
        self.assertEqual(self.request("/")[0], 200)

    def test_security_headers_on_auth_success_failure_and_export(self):
        for status, headers, body in [self.login(), self.request("/users"), self.request("/dashboard/export", token=self.token)]:
            self.assertEqual(headers["x-content-type-options"], "nosniff")
            self.assertEqual(headers["x-frame-options"], "DENY")
            self.assertEqual(headers["referrer-policy"], "no-referrer")
            self.assertEqual(headers["strict-transport-security"], "max-age=31536000")
            self.assertIn("no-store", headers["cache-control"])
        self.assertNotIn("strict-transport-security", self.request("/", scheme="http")[1])

    def test_limit_resets_at_the_window_boundary(self):
        from login_throttle import consume_login_attempt
        with self.Session() as db:
            for _ in range(10):
                consume_login_attempt(db, "192.0.2.8", "launch_owner", now=1000)
            with self.assertRaises(Exception) as error:
                consume_login_attempt(db, "192.0.2.8", "launch_owner", now=1001)
            self.assertEqual(error.exception.status_code, 429)
            consume_login_attempt(db, "192.0.2.8", "launch_owner", now=1200)

    def test_password_verification_safely_rejects_bad_hashes_and_long_values(self):
        self.assertFalse(auth.verify_password("x" * 73, auth.hash_password("OwnerPass123")))
        self.assertFalse(auth.verify_password("OwnerPass123", "corrupt"))

    def test_account_limit_blocks_distributed_attempts(self):
        with patch("auth.verify_password", return_value=False):
            for number in range(30):
                self.assertEqual(self.login(password="wrong", ip=f"192.0.2.{number}")[0], 401)
            self.assertEqual(self.login(ip="203.0.113.1")[0], 429)

    def test_exhausted_peer_cannot_create_unbounded_username_buckets(self):
        with patch("auth.verify_password", return_value=False):
            for number in range(50):
                self.assertEqual(self.login(username=f"missing_{number}")[0], 401)
            with self.Session() as db:
                before = db.query(models.LoginAttemptBucket).count()
            for number in range(5):
                self.assertEqual(self.login(username=f"new_missing_{number}")[0], 429)
            with self.Session() as db:
                self.assertEqual(db.query(models.LoginAttemptBucket).count(), before)

    def test_spreadsheet_text_guards_controls_and_fullwidth_prefixes(self):
        from response_security import safe_csv_text
        for value in ["=1+1", "+SUM(A1)", "-1", "@name", "\ttext", "\ntext", " =1", "＝1", "＋1", "－1", "＠name"]:
            self.assertEqual(safe_csv_text(value), "'" + value)
        self.assertEqual(safe_csv_text("Wash & Fold"), "Wash & Fold")

    def test_unhandled_failure_does_not_escape_or_log_sensitive_content(self):
        def fail_privately():
            raise RuntimeError("fictional-private-customer-and-SQL-parameters")
        main.app.add_api_route("/launch-failure-fixture", fail_privately)
        route = main.app.routes[-1]
        try:
            with self.assertLogs("qlms", level="ERROR") as logs:
                status, headers, body = self.request("/launch-failure-fixture")
            self.assertEqual(status, 500)
            self.assertEqual(json.loads(body), {"detail": "QLMS could not complete this request"})
            self.assertIn("no-store", headers["cache-control"])
            self.assertNotIn("fictional-private", "".join(logs.output) + body.decode())
        finally:
            main.app.routes.remove(route)

    def test_failed_stream_raises_only_a_sanitized_exception(self):
        import traceback
        from fastapi.responses import StreamingResponse
        def fail_after_start():
            async def body():
                yield b"safe prefix"
                raise RuntimeError("fictional-private-stream-content")
            return StreamingResponse(body())
        main.app.add_api_route("/launch-stream-fixture", fail_after_start)
        route = main.app.routes[-1]
        try:
            with self.assertLogs("qlms", level="ERROR") as logs, self.assertRaises(RuntimeError) as raised:
                self.request("/launch-stream-fixture")
            self.assertEqual(str(raised.exception), "QLMS response interrupted")
            self.assertNotIn("fictional-private", "".join(logs.output) + "".join(traceback.format_exception(raised.exception)))
        finally:
            main.app.routes.remove(route)


@unittest.skipUnless(os.getenv("QLMS_TEST_DATABASE_URL"), "Use disposable local PostgreSQL for shared locking")
class LaunchSecurityPostgresTests(unittest.TestCase):
    seed = transaction_fixtures.SaveFixtures.seed
    setUp = transaction_fixtures.PostgresSaveTests.setUp
    tearDown = transaction_fixtures.PostgresSaveTests.tearDown

    def test_simultaneous_workers_accept_only_ten_attempts_for_one_peer_account(self):
        from login_throttle import consume_login_attempt
        barrier = Barrier(12)

        def attempt(number):
            with self.Session() as db:
                barrier.wait(timeout=10)
                try:
                    consume_login_attempt(db, "192.0.2.99", "fictional", now=1000)
                    return 200
                except HTTPException as error:
                    return error.status_code

        with ThreadPoolExecutor(max_workers=12) as pool:
            results = list(pool.map(attempt, range(12)))
        self.assertEqual(results.count(200), 10)
        self.assertEqual(results.count(429), 2)
        self.db.expire_all()
        self.assertEqual(sorted(row.attempts for row in self.db.query(models.LoginAttemptBucket)), [10, 12, 12])

    def test_login_migration_is_repeatable_and_denies_public_access(self):
        migration = (Path(__file__).parents[1] / "migrations/023_add_login_throttle.sql").read_text()
        self.db.close()
        with self.engine.begin() as connection:
            connection.execute(text("DROP TABLE login_attempt_buckets"))
        with self.engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
            connection.exec_driver_sql(migration)
            connection.execute(text("INSERT INTO login_attempt_buckets VALUES (:key, 900, 2)"), {"key": "a" * 64})
            connection.exec_driver_sql(migration)
            self.assertEqual(connection.execute(text("SELECT attempts FROM login_attempt_buckets")).scalar(), 2)
            self.assertTrue(connection.execute(text("SELECT relrowsecurity FROM pg_class WHERE oid='login_attempt_buckets'::regclass")).scalar())
            self.assertFalse(connection.execute(text("SELECT EXISTS (SELECT 1 FROM information_schema.table_privileges WHERE table_schema=current_schema() AND table_name='login_attempt_buckets' AND grantee='PUBLIC')")).scalar())
        self.db = self.Session()


class OwnerBootstrapTests(unittest.TestCase):
    def test_noninteractive_bootstrap_never_reads_a_password(self):
        import create_owner
        with patch("create_owner.sys.stdin.isatty", return_value=False), patch("create_owner.getpass.getpass") as password:
            self.assertEqual(create_owner.main(), 1)
            password.assert_not_called()

    def test_mismatched_and_overlong_passwords_never_open_the_database(self):
        import create_owner
        for values in [["OwnerPass123", "different"], ["x" * 73, "x" * 73]]:
            with patch("create_owner.sys.stdin.isatty", return_value=True), patch("builtins.input", return_value="owner"), \
                 patch("create_owner.getpass.getpass", side_effect=values), patch("create_owner.SessionLocal") as session:
                self.assertEqual(create_owner.main(), 1)
                session.assert_not_called()
