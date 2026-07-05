# database.py
# Sets up the connection to our Supabase (PostgreSQL) database.

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Load DATABASE_URL from .env
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Connection to the database
engine = create_engine(DATABASE_URL)

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
