"""Database configuration file."""

import os
import sys

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

if os.getenv("ENV") != "production":
    from dotenv import load_dotenv

    load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("DATABASE_URL not set", file=sys.stderr)
    sys.exit(1)

engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20)
session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Get a database session."""
    db = session_local()
    try:
        yield db
    finally:
        db.close()