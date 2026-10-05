"""Create the first owner privately in the terminal, never through an API."""
import getpass
import sys

from pydantic import ValidationError
from sqlalchemy import text

from database import SessionLocal
import models
import auth
import schemas


def main():
    if not sys.stdin.isatty():
        print("Run this in a private interactive terminal; password input must not echo.")
        return 1
    username = input("Owner username: ").strip()
    password = getpass.getpass("Owner password: ")
    if password != getpass.getpass("Confirm password: "):
        print("Passwords do not match. Nothing saved.")
        return 1
    try:
        account = schemas.UserCreate(username=username, password=password, role="owner")
    except ValidationError:
        print("Use a 3–50 character username and a nonblank password of at least 8 characters, at most 72 UTF-8 bytes.")
        return 1
    with SessionLocal() as db:
        # Two simultaneous bootstrap terminals must not create two first owners.
        if db.get_bind().dialect.name == "postgresql":
            db.execute(text("SELECT pg_advisory_xact_lock(7012026)"))
        if db.query(models.User).filter(models.User.role == "owner").first():
            print("An owner already exists. Manage additional accounts from QLMS.")
            return 1
        if db.query(models.User).filter(models.User.username == account.username).first():
            print("That username already exists. Nothing saved.")
            return 1
        db.add(models.User(username=account.username, password_hash=auth.hash_password(account.password), role="owner"))
        db.commit()
    print("Owner account created. Passwords were not printed or stored as plaintext.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
