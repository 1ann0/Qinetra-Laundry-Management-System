"""Owner-run first account setup; never run this against private files through AI tools."""
import importlib
import os
from pathlib import Path
import sys

from dotenv import dotenv_values
from sqlalchemy.engine import make_url

from ops.pilot_private_setup import COUNTS_SQL, HOST, PROJECT

PRIVATE_DIRECTORY = Path(__file__).resolve().parent / "private"
RUNTIME_KEYS = ("DATABASE_URL", "QLMS_ENV", "QLMS_DB_SCHEMA", "QLMS_DB_USER", "SECRET_KEY")


def validate_runtime(settings):
    if (settings.get("QLMS_ENV"), settings.get("QLMS_DB_SCHEMA"), settings.get("QLMS_DB_USER")) != (
            "production", "qlms", "qlms_runtime"):
        raise ValueError("Use the restricted pilot configuration")
    if len((settings.get("SECRET_KEY") or "").encode("utf-8")) < 32:
        raise ValueError("The pilot signing secret is missing or too short")
    url = make_url(settings.get("DATABASE_URL") or "")
    if (url.drivername not in {"postgresql", "postgresql+psycopg2"}
            or (url.username, url.host, url.port, url.database) != (
                "qlms_runtime." + PROJECT, HOST, 5432, "postgres")
            or dict(url.query) != {"sslmode": "require"}
            or len((url.password or "").encode("utf-8")) < 16):
        raise ValueError("The connection is not the verified encrypted pilot runtime")


def load_settings(directory=PRIVATE_DIRECTORY):
    settings = dotenv_values(directory / ".env.pilot-runtime", interpolate=False)
    settings = {key: settings.get(key) for key in RUNTIME_KEYS}
    validate_runtime(settings)
    return settings


def check_database(engine):
    with engine.connect() as connection:
        connection.exec_driver_sql("SET TRANSACTION READ ONLY")
        if tuple(connection.exec_driver_sql("SELECT current_user,current_schema()").fetchone()) != (
                "qlms_runtime", "qlms"):
            raise ValueError("Unexpected actual role or schema")
        rights = connection.exec_driver_sql(
            "SELECT rolsuper,rolcreaterole,rolcreatedb,rolbypassrls,rolreplication "
            "FROM pg_roles WHERE rolname=current_user").fetchone()
        if tuple(rights or ()) != (False,) * 5:
            raise ValueError("Runtime privileges need review")
        if tuple(connection.exec_driver_sql(COUNTS_SQL).fetchone()) != (22, 30, 0, 0, 0, 0):
            raise ValueError("First setup requires the catalogue-only pilot")


def prepare_database():
    # Import only after the validated settings replace any old terminal configuration.
    database = importlib.import_module("database")
    check_database(database.engine)


def run_bootstrap():
    return importlib.import_module("create_owner").main()


def main():
    if not sys.stdin.isatty():
        print("FAIL: run in your own private interactive terminal outside Codex.")
        return 1
    try:
        settings = load_settings()
        validate_runtime(settings)
        os.environ.update(settings)
        os.environ["PYTHON_DOTENV_DISABLED"] = "1"
        prepare_database()
        result = run_bootstrap()
        if result == 0:
            print("PASS: first pilot Owner created in the verified restricted pilot.")
        return result
    except Exception:
        # Driver and validation messages can contain connection strings or entered values.
        print("FAIL: private Owner setup stopped. Review settings or connectivity privately; no raw logs in chat.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
