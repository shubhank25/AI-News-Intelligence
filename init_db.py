"""
Run this script once to create all database tables.

Usage:
    python init_db.py
"""

from app.database.connection import Base, engine, test_database_connection
from app.database.models import ArticleAIAnalysis, NewsArticleModel  # noqa: F401


def init_db():
    print("Testing database connection...")

    if not test_database_connection():
        print("ERROR: Could not connect to PostgreSQL. Check your .env settings.")
        return

    print("Connection successful.")
    print("Creating tables...")

    Base.metadata.create_all(bind=engine)

    print("Done. Tables created:")
    for table in Base.metadata.sorted_tables:
        print(f"  + {table.name}")


if __name__ == "__main__":
    init_db()
