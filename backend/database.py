# database.py
# Sets up the connection to our Supabase (PostgreSQL) database.

import os
import re
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker, declarative_base

# Load DATABASE_URL from .env
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
DATABASE_SCHEMA = os.getenv("QLMS_DB_SCHEMA", "public")
EXPECTED_DATABASE_USER = os.getenv("QLMS_DB_USER")
if not re.fullmatch(r"[a-z][a-z0-9_]{0,62}", DATABASE_SCHEMA):
    raise ValueError("QLMS_DB_SCHEMA must be a simple lowercase schema name")
if os.getenv("QLMS_ENV") == "production" and (not DATABASE_URL or not DATABASE_URL.startswith(("postgresql://", "postgresql+psycopg2://"))):
    raise ValueError("Production requires PostgreSQL")
if os.getenv("QLMS_ENV") == "production":
    if DATABASE_SCHEMA == "public" or not EXPECTED_DATABASE_USER:
        raise ValueError("Production requires an explicit private schema and restricted database user")
    if make_url(DATABASE_URL).query.get("sslmode") not in {"require", "verify-ca", "verify-full"}:
        raise ValueError("Production requires an encrypted database connection")
    if (make_url(DATABASE_URL).username or "").split(".", 1)[0] != EXPECTED_DATABASE_USER:
        raise ValueError("Production connection must use the configured restricted database user")

# Connection to the database.
# pool_pre_ping checks a connection is still alive before using it,
# and reconnects automatically if Supabase's pooler dropped it from being idle.
connect_args = ({"options": f"-csearch_path={DATABASE_SCHEMA},pg_catalog", "connect_timeout": 10}
                if DATABASE_URL and DATABASE_URL.startswith(("postgresql://", "postgresql+psycopg2://")) else {})
engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)

# Creates a new session per request
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Parent class all table models inherit from
Base = declarative_base()

# Provides a db session to endpoints, closes it after use
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def start_consistent_transaction(db, *, read_only=False):
    # Use only at an HTTP boundary after its authentication read, before ledger work.
    db.rollback()
    if db.get_bind().dialect.name == "postgresql":
        db.connection(execution_options={"isolation_level": "REPEATABLE READ"})
        if read_only:
            db.execute(text("SET TRANSACTION READ ONLY"))
