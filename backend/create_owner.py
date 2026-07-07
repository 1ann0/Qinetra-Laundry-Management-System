# create_owner.py
# One-off script to create the very first owner account.
# Run this manually once: python create_owner.py
# Do NOT expose this logic as an API route.

from database import SessionLocal
import models
import auth

db = SessionLocal()

username = input("Owner username: ")
password = input("Owner password: ")

existing = db.query(models.User).filter(models.User.username == username).first()
if existing:
    print("That username already exists.")
else:
    new_owner = models.User(
        username=username,
        password_hash=auth.hash_password(password),
        role="owner",
    )
    db.add(new_owner)
    db.commit()
    print(f"Owner account '{username}' created successfully.")

db.close()
