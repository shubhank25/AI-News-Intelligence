"""
Purpose:
This file manages the PostgreSQL database connection.

It loads database credentials from the project environment,
creates the SQLAlchemy engine, configures database sessions,
and provides a reusable database connection test.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Load environment variables from project root
BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_FILE)


# Read PostgreSQL configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "ai_news_intelligence")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Read optional SSL configuration for cloud PostgreSQL.
DB_SSLMODE = os.getenv("DB_SSLMODE")

# Add SSL configuration only when explicitly provided.
DATABASE_QUERY = {"sslmode": DB_SSLMODE} if DB_SSLMODE else {}

# Create database URL safely.
DATABASE_URL = URL.create(
    drivername="postgresql+psycopg",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME,
    query=DATABASE_QUERY,
)

if not DB_PASSWORD:
    raise RuntimeError("DB_PASSWORD is missing. Please configure it in the .env file.")

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=False,
)


# Configure database sessions
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


# Base class for database models
class Base(DeclarativeBase):
    pass


def get_db():
    """
    Provide a database session and close it after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_database_connection():
    """
    Verify connectivity by executing a simple SQL query.
    """
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            return result.scalar_one() == 1

    except Exception as error:
        print(f"Database connection failed: {error}")
        return False
