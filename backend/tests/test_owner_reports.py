"""Hand-calculated report values and spreadsheet trust boundaries, using fictional records."""
import asyncio
import csv
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal
import io
import json
import os
import unittest
from unittest.mock import patch
from urllib.parse import urlencode
from uuid import uuid4
import zipfile
import xml.etree.ElementTree as ET

from fastapi import HTTPException
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import auth
import main
import models
from owner_reports import build_report, csv_report, xlsx_report, attention_flags
from report_routes import read_snapshot


class OwnerReportTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        models.Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()
        self.owner = models.User(username="report_owner", password_hash="unused", role="owner")
        self.employee = models.User(username="report_employee", password_hash="unused", role="employee")
        self.customer = models.Customer(name="=SUM(1,2)", phone="0700000000")
        self.other = models.Customer(name="Other fictional customer", phone="0711111111")
        self.wash = models.Service(code="wash_fold", name="Wash & Fold", unit="kg", unit_price=150)
        self.duvet = models.Service(code="duvet", name="Duvet", unit="piece", unit_price=600)
        self.db.add_all([self.owner, self.employee, self.customer, self.other, self.wash, self.duvet])
        self.db.flush()
        self.mixed = self.order("QL-20261013-001", self.customer, 900, date(2026, 10, 13))
        self.old = self.order("QL-20260930-001", self.customer, 200, date(2026, 9, 30))
        self.order("QL-20261012-001", self.other, 400, date(2026, 10, 12))
        for service, quantity, subtotal in [(self.wash, 2, 300), (self.duvet, 1, 600)]:
            self.mixed.service_lines.append(models.OrderServiceLine(service_id=service.id, service_name=service.name,
                service_unit=service.unit, quantity=quantity, unit_price=service.unit_price, subtotal=subtotal,
                discount_amount=0, item_recording_mode="none"))
        self.cash = self.payment(self.mixed, "cash", 500)
        self.payment(self.old, "mpesa", 100)
        for kind, amount, purpose in [("entry_error", 100, None), ("refund", 50, "service_refund")]:
            self.db.add(models.PaymentAdjustment(order_id=self.mixed.id, payment_id=self.cash.id, kind=kind,
                amount=amount, refund_method="cash" if kind == "refund" else None, refund_purpose=purpose,
                reason="Fictional check", effective_date=date(2026, 10, 13), confirmed_by_username=self.owner.username))
        self.db.commit()
        self.previous_overrides = main.app.dependency_overrides.copy()
        def test_db():
            with self.Session() as db:
                yield db
        main.app.dependency_overrides[main.get_db] = test_db
        self.tokens = {user.role: auth.create_access_token(user.id, user.role, user.token_version)
                       for user in (self.owner, self.employee)}

    def tearDown(self):
        main.app.dependency_overrides.clear()
        main.app.dependency_overrides.update(self.previous_overrides)
        self.db.close()
        self.engine.dispose()

    def order(self, ticket, customer, charge, booked):
        order = models.Order(ticket_number=ticket, customer_id=customer.id, service_type="wash_fold",
            quantity=1, unit_price=charge, total_price=charge, order_date=booked, status="received")
        self.db.add(order)
        self.db.flush()
        return order

    def payment(self, order, method, amount):
        payment = models.Payment(order_id=order.id, payment_method=method, amount=amount,
            received_date=date(2026, 10, 13), confirmed_by_username=self.owner.username)
        self.db.add(payment)
        self.db.flush()
        return payment

    def report(self, name, **filters):
        return build_report(self.db, name, **filters)

    def section(self, report, key):
        return next(section for section in report["sections"] if section["key"] == key)["rows"]

    def request(self, path, filters=None, role="owner"):
        async def call():
            headers = [(b"authorization", f"Bearer {self.tokens[role]}".encode())] if role else []
            scope = {"type": "http", "asgi": {"version": "3.0", "spec_version": "2.4"}, "http_version": "1.1",
                "method": "GET", "scheme": "https", "path": path, "raw_path": path.encode(),
                "query_string": urlencode(filters or {}).encode(), "root_path": "", "headers": headers,
                "client": ("127.0.0.1", 1), "server": ("testserver", 443)}
            messages = []
            async def receive():
                return {"type": "http.request", "body": b"", "more_body": False}
            async def send(message):
                messages.append(message)
            await main.app(scope, receive, send)
            response = next(message for message in messages if message["type"] == "http.response.start")
            return response["status"], dict(response["headers"]), b"".join(m.get("body", b"") for m in messages)
        return asyncio.run(call())

    def test_customer_period_activity_keeps_all_current_debts(self):
        report = self.report("customer", customer_id=self.customer.id, start_date=date(2026, 10, 13), end_date=date(2026, 10, 13))
        self.assertEqual(len(self.section(report, "orders")), 1)
        self.assertEqual(len(self.section(report, "receipts")), 2)
        self.assertEqual(sum(row["balance_due"] for row in self.section(report, "balances")), Decimal("600"))
        self.assertEqual(report["summary"]["total_received"], Decimal("500"))
        self.assertEqual(report["summary"]["refunds_sent"], Decimal("50"))

    def test_money_matches_hand_calculated_finance_and_method_filters(self):
        report = self.report("money", start_date=date(2026, 10, 13), end_date=date(2026, 10, 13))
        self.assertEqual(report["summary"]["cash_received"], Decimal("400"))
        self.assertEqual(report["summary"]["mpesa_received"], Decimal("100"))
        self.assertEqual(report["summary"]["net_cash_movement"], Decimal("450"))
        finance = main.financial_summary(date(2026, 10, 13), date(2026, 10, 13), self.db, self.owner)
        self.assertEqual(float(report["summary"]["total_received"]), finance.total_received)
        cash = self.report("money", payment_method="cash")
        self.assertEqual(len(self.section(cash, "receipts")), 1)
        self.assertEqual(cash["summary"]["net_cash_movement"], Decimal("350"))

    def test_service_quantities_do_not_allocate_mixed_order_cash(self):
        report = self.report("service", service_id=self.wash.id, start_date=date(2026, 10, 13), end_date=date(2026, 10, 13))
        rows = self.section(report, "service_lines")
        self.assertEqual([(r["quantity"], r["unit"], r["booked_value"]) for r in rows], [(2, "kg", 300)])
        linked = self.section(report, "related_orders")[0]
        self.assertEqual(linked["order_value"], 900)
        self.assertEqual(linked["balance_due"], 500)
        self.assertNotIn("cash_received", rows[0])

    def test_attention_observes_nairobi_midnight_and_ready_threshold(self):
        now = datetime(2026, 10, 12, 21, tzinfo=timezone.utc)
        self.mixed.promised_ready_at = now + timedelta(hours=4)
        self.mixed.holds.append(models.OrderHold(reason="Waiting for customer reply", created_by_username="fixture"))
        self.old.status, self.old.ready_at = "ready", now - timedelta(days=7)
        self.db.commit()
        flags = attention_flags(self.mixed, now)
        self.assertIn("due_today", flags)
        self.assertIn("holds", flags)
        self.assertNotIn("production_late", flags)
        self.assertIn("overdue", attention_flags(self.old, now))
        self.mixed.status = "cancelled"
        self.assertNotIn("holds", attention_flags(self.mixed, now))

    def test_attention_ignores_settled_archives_but_keeps_closed_order_money(self):
        for index in range(12):
            archived = self.order(f"QL-ARCHIVE-{index}", self.other, 0, date(2025, 1, 1))
            archived.status = "collected"
        self.mixed.status = "collected"
        self.old.status = "cancelled"
        self.db.commit()
        with patch("owner_reports.MAX_RECORDS", 3):
            report = self.report("attention")
        tickets = {row["ticket"] for row in self.section(report, "attention")}
        self.assertIn(self.mixed.ticket_number, tickets)
        self.assertIn(self.old.ticket_number, tickets)
        self.assertEqual(report["summary"]["refund_due"], 1)

    def test_csv_neutralizes_text_and_xlsx_preserves_text_without_formulas_or_links(self):
        report = self.report("customer", customer_id=self.customer.id)
        self.assertIn("'=SUM(1,2)", csv_report(report).decode("utf-8-sig"))
        report["sections"][0]["rows"][0]["customer_name"] = "https://example.invalid"
        with zipfile.ZipFile(io.BytesIO(xlsx_report(report))) as book:
            sheets = [book.read(name).decode() for name in book.namelist() if name.startswith("xl/worksheets/sheet") and name.endswith(".xml")]
            self.assertTrue(all("<f>" not in sheet and "<hyperlink" not in sheet for sheet in sheets))
            self.assertTrue(all("state=\"frozen\"" in sheet for sheet in sheets))
            strings = book.read("xl/sharedStrings.xml").decode()
            self.assertIn("0700000000", strings)
            self.assertIn("https://example.invalid", strings)
            self.assertTrue(any("<v>900</v>" in sheet for sheet in sheets))

    def test_permissions_private_headers_and_download_names(self):
        for role, expected in [(None, 401), ("employee", 403), ("owner", 200)]:
            for path in ["/dashboard/reports/orders", "/dashboard/reports/orders/download"]:
                code, headers, body = self.request(path, {"format": "xlsx"} if path.endswith("download") else None, role)
                self.assertEqual(code, expected)
                self.assertIn(b"no-store", headers[b"cache-control"])
                if code == 200 and path.endswith("download"):
                    self.assertTrue(body.startswith(b"PK"))
                    self.assertIn(b"qlms_orders_", headers[b"content-disposition"])

    def test_customer_returns_use_real_visit_days_and_current_last_visit(self):
        now = datetime(2026, 10, 16, 21, tzinfo=timezone.utc)  # Nairobi is already 17 October.
        today = date(2026, 10, 17)
        for days in (7, 29, 30, 89, 90):
            customer = models.Customer(name=f"Return fixture {days}", phone=f"07000000{days:02}")
            self.db.add(customer)
            self.db.flush()
            self.order(f"RETURN-{days}", customer, 150, today - timedelta(days=days))
        never = models.Customer(name="Registered only", phone="0700000099")
        self.db.add(never)
        cancelled = self.order("CANCELLED-VISIT", self.customer, 100, today)
        cancelled.status = "cancelled"
        self.order("FUTURE-VISIT", self.customer, 100, today + timedelta(days=1))
        self.order("SAME-DAY", self.customer, 100, date(2026, 10, 13))
        self.db.commit()
        report = self.report("returns", start_date=date(2026, 10, 1), end_date=today, now=now)
        rows = self.section(report, "customer_returns")
        by_name = {row["customer_name"]: row for row in rows}
        self.assertEqual(by_name[self.customer.name]["last_visit"], "2026-10-13")
        self.assertEqual(by_name[self.customer.name]["visits"], 2)
        self.assertEqual(by_name[self.customer.name]["days_away"], 4)
        self.assertEqual(by_name[never.name]["return_group"], "never")
        for days, group in ((7,"7_29"),(29,"7_29"),(30,"30_89"),(89,"30_89"),(90,"90_plus")):
            self.assertEqual(by_name[f"Return fixture {days}"]["return_group"], group)
        self.assertEqual(report["summary"]["new_this_week"], 1)
        self.assertEqual(report["summary"]["new_this_month"], 2)
        self.assertEqual(report["summary"]["new_in_period"], 2)
        self.assertEqual(report["summary"]["repeat_in_period"], 1)
        filtered = self.report("returns", return_group="30_89", search="fixture 30", now=now)
        self.assertEqual([row["customer_name"] for row in self.section(filtered,"customer_returns")], ["Return fixture 30"])
        self.assertEqual(filtered["summary"]["matching_customers"], 1)

    def test_customer_return_downloads_filters_and_owner_boundary(self):
        self.db.add(models.Customer(name="No visits yet", phone="0700000099"))
        self.db.commit()
        for role, expected in ((None,401),("employee",403),("owner",200)):
            self.assertEqual(self.request("/dashboard/reports/returns", role=role)[0], expected)
            for kind in ("csv","xlsx"):
                code, headers, body = self.request("/dashboard/reports/returns/download", {"format":kind,"search":"Other"}, role)
                self.assertEqual(code, expected)
                self.assertIn(b"no-store", headers[b"cache-control"])
                if expected == 200:
                    self.assertTrue(body.startswith(b"PK") if kind == "xlsx" else b"Other fictional customer" in body)
        for filters in ({"return_group":"lost"},{"search":"x" * 101},{"status":"collected"}):
            self.assertEqual(self.request("/dashboard/reports/returns",filters)[0],422)
        self.assertEqual(self.request("/dashboard/reports/orders",{"return_group":"never"})[0],422)
        self.assertEqual(self.request("/dashboard/reports/returns",{"search":"%"})[0],200)
        self.assertEqual(self.section(self.report("returns",search="%"),"customer_returns"),[])
        self.assertTrue(xlsx_report(self.report("returns",return_group="never")).startswith(b"PK"))
        with patch("owner_reports.MAX_RECORDS",1), self.assertRaises(HTTPException) as oversized:
            self.report("returns")
        self.assertEqual(oversized.exception.status_code,413)

    def test_return_hints_distinguish_open_laundry_first_visits_and_long_absence(self):
        now=datetime(2026,10,16,12,tzinfo=timezone.utc)
        report=self.report("returns",now=now)
        rows={row["customer_name"]:row for row in self.section(report,"customer_returns")}
        self.assertEqual(rows[self.other.name]["next_step"],"Check their open laundry first.")
        self.db.query(models.Order).filter(models.Order.customer_id==self.other.id).update({"status":"collected"})
        self.db.commit()
        row=self.section(self.report("returns",search="Other",now=now),"customer_returns")[0]
        self.assertEqual(row["next_step"],"Ask if their first order was okay.")
        later=now+timedelta(days=90)
        row=self.section(self.report("returns",search="Other",now=later),"customer_returns")[0]
        self.assertEqual(row["next_step"],"Invite them back if they welcome a reminder.")
        self.assertNotIn("usual",row["next_step"])
        _, headers, _=self.request("/dashboard/reports/returns/download",{"format":"csv"})
        self.assertIn(b'qlms_customer_returns_',headers[b'content-disposition'])

    def test_unsupported_filters_and_large_reports_fail_explicitly(self):
        for name, filters in [("unknown", {}), ("customer", {}), ("catalogue", {"start_date": date(2026, 10, 1)}),
                              ("orders", {"payment_method": "cash"}), ("orders", {"start_date": date(2026, 10, 14), "end_date": date(2026, 10, 13)})]:
            with self.subTest(name=name, filters=filters), self.assertRaises(HTTPException):
                self.report(name, **filters)
        with patch("owner_reports.MAX_RECORDS", 1), self.assertRaises(HTTPException) as error:
            self.report("orders")
        self.assertEqual(error.exception.status_code, 413)
        self.assertEqual(self.request("/dashboard/reports/orders/download", {"format": "html"})[0], 422)

    def test_unknown_filters_are_rejected_instead_of_silently_ignored(self):
        for path in ("/dashboard/reports/orders", "/dashboard/reports/orders/download"):
            self.assertEqual(self.request(path, {"startdate": "2026-10-13"})[0], 422)

    def test_oversized_payloads_and_excel_cells_fail_without_truncation(self):
        report = self.report("customer", customer_id=self.customer.id)
        report["sections"][0]["rows"][0]["customer_name"] = "F" * 32768
        with self.assertRaises(HTTPException) as error:
            xlsx_report(report)
        self.assertEqual(error.exception.status_code, 413)
        with patch("owner_reports.MAX_REPORT_BYTES", 100):
            for path in ("/dashboard/reports/orders", "/dashboard/reports/orders/download"):
                self.assertEqual(self.request(path)[0], 413)

    def test_csv_phone_and_padded_links_remain_text_without_double_prefixes(self):
        report = self.report("customer", customer_id=self.customer.id)
        report["sections"][0]["rows"][0].update(customer_phone="+254700000000", customer_name="  https://example.invalid")
        rows = list(csv.reader(io.StringIO(csv_report(report).decode("utf-8-sig"))))
        target = next(row for row in rows if row and row[0] == self.mixed.ticket_number)
        self.assertEqual(target[1], "'  https://example.invalid")
        self.assertEqual(target[2], "'+254700000000")

    def test_queries_are_batched_not_per_order(self):
        for index in range(25):
            self.order(f"QL-BATCH-{index}", self.customer, 50, date(2026, 10, 13))
        self.db.commit()
        self.db.expire_all()
        statements = []
        def capture(conn, cursor, statement, *args):
            statements.append(statement)
        event.listen(self.engine, "before_cursor_execute", capture)
        try:
            report = self.report("orders")
        finally:
            event.remove(self.engine, "before_cursor_execute", capture)
        self.assertEqual(len(self.section(report, "orders")), 28)
        self.assertLess(len(statements), 12)

    def test_customer_summary_separates_current_debt_from_money_owed_back(self):
        self.old.status = "cancelled"
        self.db.commit()
        report = self.report("customer", customer_id=self.customer.id, start_date=date(2026, 10, 13))
        self.assertEqual(report["summary"]["current_balance_due"], Decimal("500"))
        self.assertEqual(report["summary"]["current_refund_due"], Decimal("100"))

    def test_catalogue_includes_the_service_default_clothing_name(self):
        clothing = models.ClothingItemType(name="Fictional duvet", item_group="laundry")
        self.db.add(clothing)
        self.db.flush()
        self.duvet.default_item_type_id = clothing.id
        self.db.commit()
        report = self.report("catalogue")
        duvet = next(row for row in self.section(report, "services") if row["code"] == "duvet")
        self.assertEqual(duvet["default_clothing"], "Fictional duvet")


@unittest.skipUnless(os.getenv("QLMS_TEST_DATABASE_URL"), "Use the disposable PostgreSQL runner for snapshot checks")
class PostgresReportSnapshotTests(unittest.TestCase):
    def setUp(self):
        url = make_url(os.environ["QLMS_TEST_DATABASE_URL"])
        if url.get_backend_name() != "postgresql" or url.host not in {"127.0.0.1", "localhost"} or url.database != "qlms_test":
            raise RuntimeError("Reports tests require the disposable local qlms_test database")
        self.schema = "report_test_" + uuid4().hex
        self.admin = create_engine(url)
        with self.admin.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA "{self.schema}"'))
        self.engine = create_engine(url, connect_args={"options": f"-csearch_path={self.schema} -cstatement_timeout=20000"})
        models.Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        with self.Session() as db:
            customer = models.Customer(name="Fictional snapshot", phone="0700000000")
            service = models.Service(code="snapshot", name="Snapshot wash", unit="kg", unit_price=900)
            db.add_all([customer, service])
            db.flush()
            order = models.Order(ticket_number="QL-SNAPSHOT-001", customer_id=customer.id, service_type=service.code,
                quantity=1, unit_price=900, total_price=900, order_date=date(2026, 10, 13), status="received")
            db.add(order)
            db.flush()
            self.order_id = order.id
            db.commit()

    def tearDown(self):
        self.engine.dispose()
        with self.admin.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{self.schema}" CASCADE'))
        self.admin.dispose()

    def test_payment_committed_during_export_appears_only_in_the_next_snapshot(self):
        inserted = []
        def concurrent_payment(connection, cursor, statement, *args):
            if inserted or not statement.lstrip().startswith("SELECT") or "FROM order_service_lines" not in statement:
                return
            inserted.append(True)
            with self.Session() as writer:
                writer.add(models.Payment(order_id=self.order_id, payment_method="cash", amount=300,
                    received_date=date(2026, 10, 13), confirmed_by_username="fictional_writer"))
                writer.commit()
        event.listen(self.engine, "before_cursor_execute", concurrent_payment)
        try:
            with self.Session() as db, read_snapshot(db):
                report = build_report(db, "orders")
            self.assertTrue(inserted)
            self.assertEqual(report["summary"]["current_balance_due"], 900)
        finally:
            event.remove(self.engine, "before_cursor_execute", concurrent_payment)
        with self.Session() as db, read_snapshot(db):
            current = build_report(db, "orders")
        self.assertEqual(current["summary"]["current_balance_due"], 600)

    def test_snapshot_connection_refuses_writes(self):
        with self.Session() as db:
            with self.assertRaises(DBAPIError), read_snapshot(db):
                db.execute(text("UPDATE orders SET total_price = 1"))
        with self.Session() as db:
            self.assertEqual(db.get(models.Order, self.order_id).total_price, 900)

    def test_return_aggregation_and_exports_run_in_the_postgres_read_snapshot(self):
        with self.Session() as db, read_snapshot(db):
            report = build_report(db,"returns",now=datetime(2026,10,16,21,tzinfo=timezone.utc),search="snapshot")
            row = report["sections"][0]["rows"][0]
            self.assertEqual((row["last_visit"],row["days_away"],row["visits"],row["open_orders"]),("2026-10-13",4,1,1))
            self.assertEqual(report["summary"]["new_this_week"],1)
            self.assertTrue(xlsx_report(report).startswith(b"PK"))
