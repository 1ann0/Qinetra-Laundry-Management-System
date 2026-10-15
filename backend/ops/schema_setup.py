"""Rehearse the full migration chain and produce a schema-only pilot snapshot."""
import hashlib
import json
import re
from pathlib import Path

from sqlalchemy import text
import models

BACKEND_ROOT = Path(__file__).resolve().parents[1]


def identifier(value):
    if not re.fullmatch(r"[a-z][a-z0-9_]{0,62}", value):
        raise ValueError("Use a simple lowercase database identifier")
    return '"' + value + '"'


def migration_files():
    return sorted((BACKEND_ROOT / "migrations").glob("[0-9][0-9][0-9]_*.sql"))


def verify_schema(connection, schema):
    rows = connection.execute(text("SELECT table_name, column_name FROM information_schema.columns WHERE table_schema=:schema"), {"schema": schema})
    actual = {}
    for table, column in rows:
        actual.setdefault(table, set()).add(column)
    missing = [table.name for table in models.Base.metadata.sorted_tables if not set(table.columns.keys()).issubset(actual.get(table.name, set()))]
    if missing:
        raise ValueError("Migration chain does not provide the required application schema: " + ", ".join(missing))


def rehearse_migrations(engine, schema):
    quoted = identifier(schema)
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
        connection.exec_driver_sql(f"SET search_path={quoted},pg_catalog")
        for path in migration_files():
            try:
                connection.exec_driver_sql(path.read_text(encoding="utf-8"), execution_options={"no_parameters": True})
            except Exception:
                connection.exec_driver_sql("ROLLBACK")
                raise
        verify_schema(connection, schema)


def private_schema_sql(schema):
    quoted = identifier(schema)
    # Remove schema usage first; a partially applied setup must not expose tables.
    return f"""
REVOKE ALL ON SCHEMA {quoted} FROM PUBLIC;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='anon') THEN
        REVOKE ALL ON SCHEMA {quoted} FROM anon;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='authenticated') THEN
        REVOKE ALL ON SCHEMA {quoted} FROM authenticated;
    END IF;
END $$;
ALTER DEFAULT PRIVILEGES IN SCHEMA {quoted} REVOKE ALL ON TABLES FROM PUBLIC;
ALTER DEFAULT PRIVILEGES IN SCHEMA {quoted} REVOKE ALL ON SEQUENCES FROM PUBLIC;
"""


def runtime_access_sql(schema, runtime_role):
    quoted, role = identifier(schema), identifier(runtime_role)
    return private_schema_sql(schema) + f"""
GRANT USAGE ON SCHEMA {quoted} TO {role};
REVOKE ALL ON ALL TABLES IN SCHEMA {quoted} FROM {role};
REVOKE ALL ON ALL SEQUENCES IN SCHEMA {quoted} FROM {role};
REVOKE ALL ON ALL TABLES IN SCHEMA {quoted} FROM PUBLIC;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA {quoted} FROM PUBLIC;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA {quoted} TO {role};
GRANT USAGE ON ALL SEQUENCES IN SCHEMA {quoted} TO {role};
GRANT DELETE ON {quoted}.login_attempt_buckets TO {role};
-- Clothing replacement removes mutable rows after recording their earlier snapshot.
GRANT DELETE ON {quoted}.order_items, {quoted}.order_item_exceptions TO {role};
DO $$
DECLARE record RECORD;
BEGIN
    FOR record IN SELECT tablename FROM pg_tables WHERE schemaname='{schema}' LOOP
        EXECUTE format('ALTER TABLE %I.%I ENABLE ROW LEVEL SECURITY', '{schema}', record.tablename);
        IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='anon') THEN
            EXECUTE format('REVOKE ALL ON TABLE %I.%I FROM anon', '{schema}', record.tablename);
        END IF;
        IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='authenticated') THEN
            EXECUTE format('REVOKE ALL ON TABLE %I.%I FROM authenticated', '{schema}', record.tablename);
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='{schema}' AND tablename=record.tablename AND policyname='qlms_server_access') THEN
            EXECUTE format('CREATE POLICY qlms_server_access ON %I.%I TO %I USING (true) WITH CHECK (true)', '{schema}', record.tablename, '{runtime_role}');
        END IF;
    END LOOP;
END $$;
REVOKE UPDATE ON {quoted}.customer_corrections, {quoted}.discount_policy_changes,
    {quoted}.order_corrections, {quoted}.payment_adjustments, {quoted}.order_item_check_history,
    {quoted}.alert_settings_changes, {quoted}.expense_changes FROM {role};
ALTER ROLE {role} SET search_path={quoted},pg_catalog;
"""


def backup_access_sql(schema, backup_role):
    quoted, role = identifier(schema), identifier(backup_role)
    return private_schema_sql(schema) + f"""
GRANT USAGE ON SCHEMA {quoted} TO {role};
REVOKE ALL ON ALL TABLES IN SCHEMA {quoted} FROM {role};
REVOKE ALL ON ALL SEQUENCES IN SCHEMA {quoted} FROM {role};
GRANT SELECT ON ALL TABLES IN SCHEMA {quoted} TO {role};
GRANT SELECT ON ALL SEQUENCES IN SCHEMA {quoted} TO {role};
DO $$
DECLARE record RECORD;
BEGIN
    FOR record IN SELECT tablename FROM pg_tables WHERE schemaname='{schema}' LOOP
        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='{schema}' AND tablename=record.tablename AND policyname='qlms_backup_read') THEN
            EXECUTE format('CREATE POLICY qlms_backup_read ON %I.%I FOR SELECT TO %I USING (true)', '{schema}', record.tablename, '{backup_role}');
        END IF;
    END LOOP;
END $$;
ALTER ROLE {role} SET search_path={quoted},pg_catalog;
"""


def snapshot_manifest(snapshot):
    return {"schema": "qlms", "schema_sha256": hashlib.sha256(snapshot.encode()).hexdigest(),
            "migrations": [{"file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()} for path in migration_files()]}


def write_snapshot(sql):
    sql = sql.rstrip() + "\n"
    destination = BACKEND_ROOT / "schema"
    destination.mkdir(exist_ok=True)
    (destination / "pilot.sql").write_text(sql, encoding="utf-8", newline="\n")
    (destination / "manifest.json").write_text(json.dumps(snapshot_manifest(sql), indent=2) + "\n", encoding="utf-8", newline="\n")
