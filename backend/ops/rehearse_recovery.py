"""Prove restricted access and encrypted restore using fictional local records only."""
import argparse
import os
import subprocess
import tempfile
import time
from decimal import Decimal
from pathlib import Path
from uuid import uuid4
from unittest.mock import patch

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

import main
import auth
import models
import schemas
from alert_settings import update_alert_settings
from expense_routes import create_expense, correct_expense, ExpenseInput, ExpenseCorrectionInput
from customer_phone import normalize_kenyan_phone
from ops.backup import export_database, restore_database
from ops.schema_setup import backup_access_sql, runtime_access_sql, verify_schema
from ops.verify_pilot_restore import restore_and_compare


def must_be_denied(engine, query):
    from sqlalchemy.exc import DBAPIError
    try:
        with engine.begin() as connection:
            connection.execute(text(query))
    except DBAPIError as error:
        if getattr(error.orig, "pgcode", None) != "42501":
            raise
        return
    raise AssertionError("Restricted action was unexpectedly allowed")


def main_rehearsal(container, client_image=None):
    started = time.monotonic()
    url = make_url(os.environ["QLMS_TEST_DATABASE_URL"])
    if url.host not in {"localhost", "127.0.0.1"} or url.database != "qlms_test" or not container.startswith("qlms-save-test-"):
        raise ValueError("Use the disposable test runner only")
    admin = create_engine(url)
    runtime_name, backup_name = "qlms_rehearsal_runtime", "qlms_rehearsal_backup"
    runtime_password, backup_password = uuid4().hex, uuid4().hex
    with admin.begin() as connection:
        for role, password in [(runtime_name, runtime_password), (backup_name, backup_password)]:
            connection.exec_driver_sql(f"CREATE ROLE {role} LOGIN PASSWORD '{password}' NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS")
        connection.exec_driver_sql(runtime_access_sql("qlms", runtime_name), execution_options={"no_parameters": True})
        connection.exec_driver_sql(backup_access_sql("qlms", backup_name), execution_options={"no_parameters": True})
        connection.exec_driver_sql("CREATE ROLE anon NOLOGIN", execution_options={"no_parameters": True}) if not connection.execute(text("SELECT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='anon')")).scalar() else None
        connection.exec_driver_sql("CREATE ROLE authenticated NOLOGIN", execution_options={"no_parameters": True}) if not connection.execute(text("SELECT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='authenticated')")).scalar() else None
    runtime_url = url.set(username=runtime_name, password=runtime_password)
    runtime = create_engine(runtime_url, connect_args={"options": "-csearch_path=qlms,pg_catalog"})
    with runtime.connect() as connection:
        verify_schema(connection, "qlms")
    with sessionmaker(bind=runtime)() as db:
        with patch.object(main, "DATABASE_SCHEMA", "qlms"), patch.object(main, "EXPECTED_DATABASE_USER", runtime_name):
            assert main.database_ready(db) == {"status": "ready"}
            with patch.object(main, "EXPECTED_DATABASE_USER", "wrong_runtime"):
                assert main.database_ready(db).status_code == 503
        owner = models.User(username="restore_owner", role="owner", password_hash=auth.hash_password("RestoreFixture123!"))
        customer = models.Customer(name="Fictional restore customer", phone="0700000000", phone_normalized=normalize_kenyan_phone("0700000000"))
        service = models.Service(code="fixture", name="Fictional service", unit="item", unit_price=1000, item_recording_mode="tally")
        shirt = models.ClothingItemType(name="Fictional shirt")
        trouser = models.ClothingItemType(name="Fictional trouser")
        db.add_all([owner, customer, service, shirt, trouser])
        db.commit()
        update_alert_settings(schemas.AlertSettingsUpdate(owner_email="restore-owner@example.test", backup_time="22:00", expected_revision=0),
                              db, owner, idempotency_key=uuid4())
        expense_body = ExpenseInput(paid_date=main.get_nairobi_today(),category="supplies",amount=100,payment_method="cash",note="Fictional restore supplies")
        expense = create_expense(expense_body,db,owner,idempotency_key=uuid4())
        expense_change = ExpenseCorrectionInput(**(expense_body.model_dump() | {"amount":Decimal("75")}),
            funding_source="owner",expected_revision=0,reason="Fictional price and payer correction",is_voided=False)
        correct_expense(expense.id,expense_change,db,owner,idempotency_key=uuid4())
        main.correct_customer_details(customer.id, schemas.CustomerCorrectionCreate(expected_name=customer.name, expected_phone=customer.phone,
                 new_name="Corrected fictional customer", new_phone="0711111111", reason="Fictional contact correction", confirmed=True),
                 db, owner, idempotency_key=uuid4())
        order = main.create_detailed_order(schemas.DetailedOrderCreate(customer_id=customer.id, services=[{"service_id": service.id, "quantity": 1,
                       "items": [{"item_type_id": shirt.id, "quantity": 1, "exceptions": [{"description": "Fictional intake mark"}]}]}],
                       initial_payment={"payment_method": "cash", "confirmed": True}), db, owner, idempotency_key=uuid4())
        line = order.service_lines[0]
        main.replace_order_service_items(order.id, line.id, schemas.OrderItemsUpdate(expected_revision=line.item_revision,
                    items=[{"item_type_id": trouser.id, "quantity": 1}], change_reason="Fictional count correction"), db, owner)
        assert line.item_revision == 1 and len(line.item_history) == 2
        for stage in ["in_progress", "ready", "collected"]:
            main.update_order_status(order.id, schemas.OrderStatusUpdate(status=stage), db, owner)
        payment_id = order.payments[0].id
        key = uuid4()
        refund = schemas.RefundCreate(payment_id=payment_id, refund_purpose="service_refund", refund_method="cash", amount=200,
                    reason="Fictional recovery fixture", effective_date=main.get_nairobi_today(), confirmed=True)
        main.refund_order_payment(order.id, refund, db, owner, idempotency_key=key)
        order = main.refund_order_payment(order.id, refund, db, owner, idempotency_key=key)
        assert (order.net_charge, order.amount_paid, order.balance_due) == (800, 800, 0)
        assert len(order.payment_adjustments) == 1
        order_id, owner_id = order.id, owner.id
        report = main.financial_summary(main.get_nairobi_today(), main.get_nairobi_today(), db, owner)
        assert (report.total_received, report.refunds_sent, report.net_cash_movement) == (1000, 200, 800)
    must_be_denied(runtime, "DELETE FROM qlms.customers")
    must_be_denied(runtime, "UPDATE qlms.payment_adjustments SET reason='tampered'")
    must_be_denied(runtime, "UPDATE qlms.alert_settings_changes SET after_email='tampered@example.test'")
    must_be_denied(runtime, "UPDATE qlms.expense_changes SET reason='tampered'")
    must_be_denied(runtime, "DELETE FROM qlms.expenses")
    must_be_denied(runtime, "CREATE TABLE qlms.forbidden(id integer)")
    backup_url = url.set(username=backup_name, password=backup_password)
    backup = create_engine(backup_url)
    must_be_denied(backup, "UPDATE qlms.customers SET name='tampered'")
    with admin.begin() as connection:
        for browser_role in ("anon", "authenticated"):
            assert not connection.execute(text("SELECT has_schema_privilege(:role,'qlms','USAGE')"), {"role": browser_role}).scalar()
    restore_name = "qlms_restore_" + uuid4().hex
    with admin.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
        connection.exec_driver_sql(f"CREATE DATABASE {restore_name}")
    restore_url = url.set(database=restore_name)
    restored = create_engine(restore_url, connect_args={"options": "-csearch_path=qlms,pg_catalog"})
    try:
        with tempfile.TemporaryDirectory() as folder:
            key = os.urandom(32)
            encrypted, copied = export_database(backup_url, "qlms", key, Path(folder) / "local", Path(folder) / "independent", container)
            archive_bytes = encrypted.stat().st_size
            assert copied.read_bytes() == encrypted.read_bytes()
            restore_file = copied
            if client_image:
                # A second client container reaches only this disposable database's bridge address.
                address = subprocess.run(["docker", "inspect", "--format", "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}", container],
                                         check=True, capture_output=True, text=True, timeout=10).stdout.strip()
                import ipaddress
                if not ipaddress.ip_address(address).is_private:
                    raise ValueError("Use the private disposable database network only")
                client_url = backup_url.set(host=address, port=5432).update_query_dict({"sslmode": "disable"})
                restore_file, _ = export_database(client_url, "qlms", key, Path(folder) / "cloud-client", client_image=client_image)
                print("Pinned cloud PostgreSQL client exported the restricted fictional schema.")
            restore_database(backup_url, restore_url, restore_file, key, container=container)
            tables = restore_and_compare(backup_url, restore_file, key, required_roles=(runtime_name, backup_name))
            print(f"Fresh disposable recovery helper verified {tables} fictional tables and sequence values; temporary container removed.")
        with sessionmaker(bind=restored)() as db:
            verify_schema(db, "qlms")
            order = main.get_order(order_id, db, db.get(models.User, owner_id))
            assert (order.net_charge, order.amount_paid, order.balance_due) == (Decimal("800"), Decimal("800"), 0)
            assert db.query(models.Customer).count() == db.query(models.Order).count() == db.query(models.Payment).count() == db.query(models.PaymentAdjustment).count() == 1
            assert db.query(models.CustomerCorrection).count() == 1
            assert db.query(models.AlertSettingsChange).count() == 1
            assert db.query(models.AlertSettings).one().owner_email == "restore-owner@example.test"
            assert db.query(models.AlertSettings).one().backup_time == "22:00"
            assert db.query(models.Expense).one().amount == Decimal("75")
            assert db.query(models.Expense).one().funding_source == "owner"
            assert "funding_source" not in db.query(models.Expense).one().original_details
            assert Decimal(db.query(models.Expense).one().original_details["amount"]) == Decimal("100")
            assert db.query(models.ExpenseChange).count() == 2
            assert db.query(models.Customer).one().name == "Corrected fictional customer"
            assert order.status == "collected"
            assert order.service_lines[0].item_revision == 1
            assert len(order.service_lines[0].item_history) == 2
            assert auth.verify_password("RestoreFixture123!", db.get(models.User, owner_id).password_hash)
            report = main.financial_summary(main.get_nairobi_today(), main.get_nairobi_today(), db, db.get(models.User, owner_id))
            assert (report.total_received, report.refunds_sent, report.net_cash_movement) == (1000, 200, 800)
        print(f"Restricted runtime/backup permissions, browser denial and encrypted separate-database restore passed ({time.monotonic() - started:.1f}s).")
        print(f"Fictional full-schema encrypted archive: {archive_bytes} bytes; 90 equal-size daily copies: {archive_bytes * 90} bytes. This is a fixture measurement, not a real-data growth forecast.")
    finally:
        restored.dispose()
        with admin.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
            connection.exec_driver_sql(f"DROP DATABASE {restore_name}")
        runtime.dispose()
        backup.dispose()
        admin.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--container", required=True)
    parser.add_argument("--client-image")
    arguments = parser.parse_args()
    main_rehearsal(arguments.container, arguments.client_image)
