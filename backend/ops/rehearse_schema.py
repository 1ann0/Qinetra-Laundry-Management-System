"""Only a disposable local qlms_test database may generate this snapshot."""
import argparse
import os
import subprocess

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from ops.schema_setup import BACKEND_ROOT, private_schema_sql, rehearse_migrations, write_snapshot


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--container", required=True)
    arguments = parser.parse_args()
    url = make_url(os.environ["QLMS_TEST_DATABASE_URL"])
    if url.get_backend_name() != "postgresql" or url.host not in {"127.0.0.1", "localhost"} or url.database != "qlms_test":
        raise ValueError("Schema rehearsal requires disposable local qlms_test")
    if not arguments.container.startswith("qlms-save-test-"):
        raise ValueError("Use the container created by run-postgres-tests.ps1")
    engine = create_engine(url)
    with engine.begin() as connection:
        connection.exec_driver_sql("CREATE SCHEMA qlms")
        connection.exec_driver_sql("SET LOCAL search_path=qlms,pg_catalog")
        connection.exec_driver_sql((BACKEND_ROOT / "ops/base-schema.sql").read_text())
    rehearse_migrations(engine, "qlms")
    # Reapply to prove repeatability; the snapshot contains schema, never seed data.
    rehearse_migrations(engine, "qlms")
    dump = subprocess.run(["docker", "exec", arguments.container, "pg_dump", "--schema-only", "--schema=qlms",
                           "--no-owner", "--no-privileges", "--no-comments", "-U", "postgres", "-d", "qlms_test"],
                          check=True, capture_output=True, text=True).stdout
    # pg_dump 17's psql-only restrict directives cannot be sent through SQL APIs.
    sql = "\n".join(line for line in dump.splitlines() if not line.startswith(("\\", "--")))
    sql = sql.replace("CREATE SCHEMA qlms;", "CREATE SCHEMA qlms;\n" + private_schema_sql("qlms")) + "\n"
    # Restore the generated schema in the same disposable DB, then verify again.
    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA qlms CASCADE"))
        connection.exec_driver_sql(sql, execution_options={"no_parameters": True})
    from ops.schema_setup import verify_schema
    with engine.connect() as connection:
        verify_schema(connection, "qlms")
        if connection.execute(text("SELECT count(*) FROM qlms.users")).scalar() or connection.execute(text("SELECT count(*) FROM qlms.customers")).scalar():
            raise ValueError("Schema snapshot contains application records")
    write_snapshot(sql)
    engine.dispose()
    print("Full migration chain, repeat application and empty schema restore verified; snapshot written.")


if __name__ == "__main__":
    main()
