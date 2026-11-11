"""
Purpose:
This file performs an integration test of the news article repository.

It verifies that an article can be inserted into PostgreSQL,
retrieved by URL, and counted successfully. It also removes the
temporary test record so repeated test runs do not pollute the database.
"""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import delete

from app.database.connection import SessionLocal
from app.database.models import NewsArticleModel
from app.database.repository import (
    count_articles,
    create_article,
    get_article_by_url,
)


def test_database_repository():
    unique_id = uuid4().hex
    article_url = f"https://example.com/test-news-{unique_id}"

    article_data = {
        "title": "Testing AI News Database Integration",
        "url": article_url,
        "source": "Test Source",
        "description": "A sample article for database testing.",
        "content": "This article verifies PostgreSQL repository operations.",
        "author": "Test Author",
        "category": "Artificial Intelligence",
        "language": "en",
        "published_at": datetime.now(timezone.utc),
        "fetched_at": datetime.now(timezone.utc),
        "content_hash": None,
    }

    with SessionLocal() as db:
        try:
            initial_count = count_articles(db)

            inserted_article = create_article(db, article_data)

            assert inserted_article is not None
            assert inserted_article.title == article_data["title"]

            retrieved_article = get_article_by_url(db, article_url)

            assert retrieved_article is not None
            assert retrieved_article.url == article_url

            final_count = count_articles(db)
            assert final_count == initial_count + 1

            print("Database repository test passed!")
            print("Inserted article ID:", inserted_article.id)
            print("Total articles:", final_count)

        finally:
            db.execute(
                delete(NewsArticleModel).where(NewsArticleModel.url == article_url)
            )
            db.commit()
