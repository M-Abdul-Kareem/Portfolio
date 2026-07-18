"""
Database connection setup.

Production: uses PostgreSQL hosted on Neon (https://neon.tech) — connection
string read from the DATABASE_URL environment variable. Neon's free tier
scales to zero after 5 minutes idle and auto-resumes in ~hundreds of ms
on the next query, which is why it was chosen over a container-hosted
database for this project.

Local development fallback: if DATABASE_URL isn't set, falls back to a
local SQLite file so you can still run/test everything without needing
a Neon account or internet connection.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./portfolio.db")

# Neon (and most managed Postgres providers) give you a URL starting with
# "postgres://", but SQLAlchemy's modern driver expects "postgresql://".
# This rewrites it automatically so you can paste Neon's connection
# string directly without editing it by hand.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# check_same_thread=False is only needed for SQLite (FastAPI's threaded
# request handling); Postgres doesn't use or need this argument.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that provides a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
