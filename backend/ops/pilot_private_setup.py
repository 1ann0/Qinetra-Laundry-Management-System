"""Owner-run setup for the fresh pilot; never execute this through an AI tool."""
import re
import sys
from pathlib import Path

from dotenv import dotenv_values
import psycopg2
from psycopg2.extensions import encrypt_password
from sqlalchemy.engine import URL

PROJECT = "istweeaqtykwfuhntgik"
HOST = "aws-1-eu-central-1.pooler.supabase.com"
PRIVATE_DIRECTORY = Path(__file__).resolve().parent / "private"
ROLE_KEYS = {"qlms_runtime": "QLMS_RUNTIME_PASSWORD", "qlms_backup": "QLMS_BACKUP_PASSWORD"}
IMMUTABLE_TABLES = {"customer_corrections", "discount_policy_changes", "order_corrections",
                    "payment_adjustments", "order_item_check_history", "alert_settings_changes"}
DELETABLE_TABLES = {"login_attempt_buckets", "order_items", "order_item_exceptions"}
COUNTS_SQL = """SELECT (SELECT count(*) FROM qlms.services),
    (SELECT count(*) FROM qlms.clothing_item_types), (SELECT count(*) FROM qlms.users),
    (SELECT count(*) FROM qlms.customers), (SELECT count(*) FROM qlms.orders),
    (SELECT count(*) FROM qlms.payments)"""


def load_settings(directory):
    names = ("admin-setup", "db-credentials", "runtime", "hosted-backup")
    settings = {name: dotenv_values(directory / (".env.pilot-" + name), interpolate=False) for name in names}
    admin, roles, runtime, backup = (settings[name] for name in names)
    expected = {"QLMS_PILOT_PROJECT_REF": PROJECT, "QLMS_PILOT_DB_HOST": HOST,
                "QLMS_PILOT_DB_PORT": "5432", "QLMS_PILOT_DB_NAME": "postgres",
                "QLMS_PILOT_ADMIN_USER": "postgres." + PROJECT}
    if any(admin.get(key) != value for key, value in expected.items()):
        raise ValueError("The administrator configuration targets a different project")
    if (runtime.get("QLMS_ENV"), runtime.get("QLMS_DB_SCHEMA"), runtime.get("QLMS_DB_USER")) != ("production", "qlms", "qlms_runtime"):
        raise ValueError("The runtime configuration is not the restricted pilot")
    if (backup.get("QLMS_BACKUP_PROJECT_REF"), backup.get("QLMS_DB_SCHEMA")) != (PROJECT, "qlms"):
        raise ValueError("The backup configuration targets a different project")
    secrets = [admin.get("QLMS_PILOT_ADMIN_PASSWORD"), runtime.get("SECRET_KEY")]
    secrets += [roles.get(key) for key in ROLE_KEYS.values()]
    if any(not value or len(value.encode("utf-8")) < 16 or any(c in value for c in "\r\n\0") for value in secrets) or len(set(secrets)) != 4:
        raise ValueError("Use separate strong credentials")
    if len(runtime["SECRET_KEY"].encode("utf-8")) < 32:
        raise ValueError("The production signing secret is too short")
    # Validate both replacements before changing either roles or local files.
    for name, key, role in [("runtime", "DATABASE_URL", "qlms_runtime"),
                            ("hosted-backup", "QLMS_BACKUP_DATABASE_URL", "qlms_backup")]:
        path = directory / (".env.pilot-" + name)
        if len(re.findall(r"^" + key + r"=[^\r\n]*(?=\r?$)", path.read_text(encoding="utf-8"), re.MULTILINE)) != 1:
            raise ValueError("A private connection setting is missing or duplicated")
        if settings[name].get(key) not in ("", connection_url(role, roles[ROLE_KEYS[role]])):
            raise ValueError("An existing connection setting needs private review")
    return settings


def connection_url(role, password):
    return URL.create("postgresql", username=role + "." + PROJECT, password=password,
                      host=HOST, port=5432, database="postgres", query={"sslmode": "require"}).render_as_string(hide_password=False)


def check_database(connection):
    with connection.cursor() as cursor:
        cursor.execute("SELECT current_user, current_database()")
        if cursor.fetchone() != ("postgres", "postgres"):
            raise ValueError("Unexpected administrator connection")
        cursor.execute("""SELECT rolname,rolsuper,rolcreaterole,rolcreatedb,rolbypassrls,rolreplication
            FROM pg_roles WHERE rolname IN ('qlms_runtime','qlms_backup') ORDER BY rolname""")
        if cursor.fetchall() != [("qlms_backup", False, False, False, False, False),
                                  ("qlms_runtime", False, False, False, False, False)]:
            raise ValueError("Restricted roles are missing or have extra authority")
        cursor.execute("""SELECT count(*) FROM pg_auth_members m JOIN pg_roles r ON r.oid=m.member
            WHERE r.rolname IN ('qlms_runtime','qlms_backup')""")
        if cursor.fetchone()[0]:
            raise ValueError("Restricted roles inherit other roles")
        cursor.execute("""SELECT has_schema_privilege('qlms_runtime','qlms','USAGE'),
            has_schema_privilege('qlms_runtime','qlms','CREATE'),has_schema_privilege('qlms_backup','qlms','USAGE'),
            has_schema_privilege('qlms_backup','qlms','CREATE'),has_schema_privilege('anon','qlms','USAGE'),
            has_schema_privilege('authenticated','qlms','USAGE')""")
        if cursor.fetchone() != (True, False, True, False, False, False):
            raise ValueError("Pilot schema access needs review")
        cursor.execute(COUNTS_SQL)
        if cursor.fetchone() != (22, 30, 0, 0, 0, 0):
            raise ValueError("This setup requires the fresh catalogue-only pilot")
        cursor.execute("""SELECT c.relname,c.relrowsecurity,
            has_table_privilege('qlms_runtime',c.oid,'SELECT'),has_table_privilege('qlms_runtime',c.oid,'INSERT'),
            has_table_privilege('qlms_runtime',c.oid,'UPDATE'),has_table_privilege('qlms_runtime',c.oid,'DELETE'),
            has_table_privilege('qlms_backup',c.oid,'SELECT'),has_table_privilege('qlms_backup',c.oid,'INSERT'),
            has_table_privilege('qlms_backup',c.oid,'UPDATE'),has_table_privilege('qlms_backup',c.oid,'DELETE'),
            has_table_privilege('anon',c.oid,'SELECT'),has_table_privilege('authenticated',c.oid,'SELECT'),
            has_table_privilege('qlms_runtime',c.oid,'TRUNCATE'),has_table_privilege('qlms_runtime',c.oid,'TRIGGER'),
            has_table_privilege('qlms_runtime',c.oid,'REFERENCES'),has_table_privilege('qlms_backup',c.oid,'TRUNCATE'),
            has_table_privilege('qlms_backup',c.oid,'TRIGGER'),has_table_privilege('qlms_backup',c.oid,'REFERENCES')
            FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
            WHERE n.nspname='qlms' AND c.relkind='r' ORDER BY c.relname""")
        tables = cursor.fetchall()
        if len(tables) != 22:
            raise ValueError("Unexpected pilot table inventory")
        for table, *rights in tables:
            expected = [True, True, True, table not in IMMUTABLE_TABLES, table in DELETABLE_TABLES,
                        True, False, False, False, False, False, False, False, False, False, False, False]
            if rights != expected:
                raise ValueError("Pilot grants or browser denial need review")
        return tables


def assign_passwords(connection, credentials):
    with connection:
        before = check_database(connection)
        with connection.cursor() as cursor:
            for role, key in ROLE_KEYS.items():
                # Send a SCRAM verifier, keeping cleartext out of SQL activity/logs.
                verifier = encrypt_password(credentials[key], role, connection, "scram-sha-256")
                cursor.execute(f'ALTER ROLE "{role}" LOGIN PASSWORD %s', (verifier,))
        if check_database(connection) != before:
            raise ValueError("Setup unexpectedly changed table access")


def check_role_connection(role, password):
    connection = psycopg2.connect(host=HOST, port=5432, dbname="postgres", user=role + "." + PROJECT,
                                 password=password, sslmode="require", connect_timeout=10,
                                 options="-csearch_path=qlms,pg_catalog", application_name="qlms-private-setup")
    try:
        if not connection.info.ssl_in_use:
            raise ValueError("The restricted connection is not encrypted")
        connection.set_session(readonly=True)
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_user,current_schema()")
            if cursor.fetchone() != (role, "qlms"):
                raise ValueError("The restricted connection has the wrong role/schema")
            cursor.execute(COUNTS_SQL)
            if cursor.fetchone() != (22, 30, 0, 0, 0, 0):
                raise ValueError("The restricted role cannot see the fresh pilot")
    finally:
        connection.close()


def save_connection(path, key, value):
    # Update the existing file in place to retain its owner-only Windows ACL.
    with path.open("r+", encoding="utf-8", newline="") as output:
        content, count = re.subn(r"^" + key + r"=[^\r\n]*(?=\r?$)", lambda _: key + "=" + value,
                                output.read(), flags=re.MULTILINE)
        if count != 1:
            raise ValueError("Connection setting must occur exactly once")
        output.seek(0)
        output.write(content)
        output.truncate()


def run_setup(directory=PRIVATE_DIRECTORY):
    settings = load_settings(directory)
    admin, credentials = settings["admin-setup"], settings["db-credentials"]
    connection = psycopg2.connect(host=HOST, port=5432, dbname="postgres", user="postgres." + PROJECT,
                                 password=admin["QLMS_PILOT_ADMIN_PASSWORD"], sslmode="require",
                                 connect_timeout=10, application_name="qlms-private-setup")
    try:
        if not connection.info.ssl_in_use:
            raise ValueError("The administrator connection is not encrypted")
        assign_passwords(connection, credentials)
    finally:
        connection.close()
    print("STEP: restricted role credentials committed; existing grants and catalogue preserved.")
    for role, key in ROLE_KEYS.items():
        check_role_connection(role, credentials[key])
    for name, key, role in [("runtime", "DATABASE_URL", "qlms_runtime"),
                            ("hosted-backup", "QLMS_BACKUP_DATABASE_URL", "qlms_backup")]:
        save_connection(directory / (".env.pilot-" + name), key, connection_url(role, credentials[ROLE_KEYS[role]]))


def main():
    try:
        run_setup()
    except Exception as error:
        # Driver errors can contain credentials/SQL. Never print their messages or tracebacks.
        print(f"FAIL: private pilot setup ({type(error).__name__}). Share only this line and any STEP line; keep private files closed.", file=sys.stderr)
        return 1
    print("PASS: private pilot database setup; runtime and backup TLS connections verified; private settings saved.")
    print("Deployment, staff accounts and scheduled recovery still require qualification.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
