"""
Purpose:
This file provides database operations for news articles.

It handles single and bulk article insertion, prevents duplicate
records using PostgreSQL conflict handling, and provides methods
to retrieve and count stored articles.
"""

"""
Purpose:
These functions provide additional database read operations
for retrieving individual news articles, available categories,
and aggregated news statistics.
"""

from sqlalchemy import func, or_, select


def get_article_by_id(
    db: Session,
    article_id: int,
) -> NewsArticleModel | None:
    """Retrieve a news article using its database ID."""

    return db.get(NewsArticleModel, article_id)


def get_categories(db: Session) -> list[str]:
    """Return all distinct non-empty news categories."""

    statement = (
        select(NewsArticleModel.category)
        .where(
            NewsArticleModel.category.is_not(None),
            NewsArticleModel.category != "",
        )
        .distinct()
        .order_by(NewsArticleModel.category)
    )

    return list(db.execute(statement).scalars().all())


"""
Purpose:
This function provides aggregated news intelligence statistics.

It reports total articles, sources, AI analysis coverage,
sentiment distribution, and article counts by source.
"""


"""
Purpose:
Returns overall news collection statistics and AI analysis metrics
for the dashboard, including source and sentiment distributions.
"""


def get_news_statistics(db: Session) -> dict:
    total_articles = count_articles(db)

    analyzed_statement = select(func.count(NewsArticleModel.id)).where(
        NewsArticleModel.ai_summary.is_not(None)
    )

    analyzed_articles = db.execute(analyzed_statement).scalar_one()
    pending_articles = total_articles - analyzed_articles

    sentiment_statement = (
        select(
            NewsArticleModel.ai_sentiment,
            func.count(NewsArticleModel.id),
        )
        .where(NewsArticleModel.ai_sentiment.is_not(None))
        .group_by(NewsArticleModel.ai_sentiment)
    )

    sentiment_rows = db.execute(sentiment_statement).all()

    sentiment_distribution = {
        "positive": 0,
        "negative": 0,
        "neutral": 0,
    }

    for sentiment, count in sentiment_rows:
        if sentiment in sentiment_distribution:
            sentiment_distribution[sentiment] = count

    source_statement = (
        select(
            NewsArticleModel.source,
            func.count(NewsArticleModel.id).label("article_count"),
        )
        .group_by(NewsArticleModel.source)
        .order_by(func.count(NewsArticleModel.id).desc())
    )

    source_rows = db.execute(source_statement).all()

    total_sources = len(source_rows)

    coverage_percentage = (
        (analyzed_articles / total_articles) * 100 if total_articles > 0 else 0
    )

    return {
        "total_articles": total_articles,
        "total_sources": total_sources,
        "articles_by_source": [
            {
                "source": source,
                "article_count": article_count,
            }
            for source, article_count in source_rows
        ],
        "ai_analysis": {
            "analyzed_articles": analyzed_articles,
            "pending_articles": pending_articles,
            "coverage_percentage": round(coverage_percentage, 2),
            "sentiment_distribution": sentiment_distribution,
        },
    }


from datetime import date, datetime

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database.models import NewsArticleModel


def prepare_article_data(article_data: dict) -> dict:
    """Convert ISO-formatted datetime strings into datetime objects."""

    prepared_data = article_data.copy()

    for field in ("published_at", "fetched_at"):
        value = prepared_data.get(field)

        if isinstance(value, str):
            prepared_data[field] = datetime.fromisoformat(value.replace("Z", "+00:00"))

    return prepared_data


def create_article(
    db: Session,
    article_data: dict,
) -> NewsArticleModel | None:
    """Insert one article and return it, or None if it is a duplicate."""

    prepared_data = prepare_article_data(article_data)

    try:
        statement = (
            insert(NewsArticleModel)
            .values(**prepared_data)
            .on_conflict_do_nothing()
            .returning(NewsArticleModel.id)
        )

        inserted_id = db.execute(statement).scalar_one_or_none()
        db.commit()

        if inserted_id is None:
            return None

        return db.get(NewsArticleModel, inserted_id)

    except SQLAlchemyError:
        db.rollback()
        raise


def create_articles_bulk(
    db: Session,
    articles: list[dict],
) -> int:
    """
    Insert multiple articles into PostgreSQL.

    Returns the exact number of newly inserted records.
    Duplicate URLs or content hashes are ignored.
    """

    if not articles:
        return 0

    prepared_articles = [prepare_article_data(article) for article in articles]

    try:
        statement = (
            insert(NewsArticleModel)
            .values(prepared_articles)
            .on_conflict_do_nothing()
            .returning(NewsArticleModel.id)
        )

        result = db.execute(statement)
        inserted_ids = result.scalars().all()

        db.commit()

        return len(inserted_ids)

    except SQLAlchemyError:
        db.rollback()
        raise


def get_article_by_url(
    db: Session,
    article_url: str,
) -> NewsArticleModel | None:
    """Retrieve an article using its URL."""

    statement = select(NewsArticleModel).where(NewsArticleModel.url == article_url)

    return db.execute(statement).scalar_one_or_none()


def get_articles(
    db: Session,
    limit: int = 50,
    offset: int = 0,
    category: str | None = None,
) -> list[NewsArticleModel]:
    """Retrieve articles with pagination and optional category filtering."""

    statement = select(NewsArticleModel)

    if category:
        statement = statement.where(NewsArticleModel.category.ilike(category))

    statement = (
        statement.order_by(
            NewsArticleModel.published_at.desc().nulls_last(),
            NewsArticleModel.fetched_at.desc(),
        )
        .limit(limit)
        .offset(offset)
    )

    return list(db.execute(statement).scalars().all())


def count_articles(
    db: Session,
    category: str | None = None,
) -> int:
    """Count all stored articles, optionally filtered by category."""

    statement = select(func.count()).select_from(NewsArticleModel)

    if category:
        statement = statement.where(NewsArticleModel.category.ilike(category))

    return db.execute(statement).scalar_one()


"""
Purpose:
These functions provide additional database read operations
for retrieving individual news articles, available categories,
and aggregated news statistics.
"""


def get_article_by_id(
    db: Session,
    article_id: int,
) -> NewsArticleModel | None:
    """Retrieve a news article using its database ID."""

    return db.get(NewsArticleModel, article_id)


def get_categories(db: Session) -> list[str]:
    """Return all distinct non-empty news categories."""

    statement = (
        select(NewsArticleModel.category)
        .where(
            NewsArticleModel.category.is_not(None),
            NewsArticleModel.category != "",
        )
        .distinct()
        .order_by(NewsArticleModel.category)
    )

    return list(db.execute(statement).scalars().all())


"""
Purpose:
This function searches stored news articles using a keyword.

It searches across article titles, descriptions, and full content
using PostgreSQL case-insensitive matching.
"""


def search_articles(
    db: Session,
    keyword: str,
    limit: int = 20,
) -> list[NewsArticleModel]:
    """Search articles by keyword across title, description, and content."""

    search_pattern = f"%{keyword.strip()}%"

    statement = (
        select(NewsArticleModel)
        .where(
            or_(
                NewsArticleModel.title.ilike(search_pattern),
                NewsArticleModel.description.ilike(search_pattern),
                NewsArticleModel.content.ilike(search_pattern),
            )
        )
        .order_by(
            NewsArticleModel.published_at.desc().nulls_last(),
            NewsArticleModel.fetched_at.desc(),
        )
        .limit(limit)
    )

    return list(db.execute(statement).scalars().all())


"""
Purpose:
This function identifies article URLs that already exist in PostgreSQL.

It allows the news pipeline to skip previously collected articles
before downloading and extracting their webpage content.
"""


def get_existing_article_urls(
    db: Session,
    article_urls: list[str],
) -> set[str]:
    """Return URLs that are already stored in the database."""

    if not article_urls:
        return set()

    statement = select(NewsArticleModel.url).where(
        NewsArticleModel.url.in_(article_urls)
    )

    return set(db.execute(statement).scalars().all())


"""
Purpose:
These repository functions retrieve news articles based on their
Gemini AI analysis status and sentiment.
"""


def get_ai_analyzed_articles(
    db: Session,
    limit: int = 20,
    offset: int = 0,
):
    """Retrieve articles that have an AI-generated summary."""

    statement = (
        select(NewsArticleModel)
        .where(NewsArticleModel.ai_summary.is_not(None))
        .order_by(
            NewsArticleModel.published_at.desc().nulls_last(),
            NewsArticleModel.fetched_at.desc(),
        )
        .limit(limit)
        .offset(offset)
    )

    return db.scalars(statement).all()


def get_ai_pending_articles(
    db: Session,
    limit: int = 20,
    offset: int = 0,
):
    """Retrieve articles that do not yet have an AI summary."""

    statement = (
        select(NewsArticleModel)
        .where(NewsArticleModel.ai_summary.is_(None))
        .order_by(NewsArticleModel.fetched_at.desc())
        .limit(limit)
        .offset(offset)
    )

    return db.scalars(statement).all()


def get_articles_by_ai_sentiment(
    db: Session,
    sentiment: str,
    limit: int = 20,
    offset: int = 0,
):
    """Retrieve articles matching a specific AI sentiment."""

    statement = (
        select(NewsArticleModel)
        .where(NewsArticleModel.ai_sentiment == sentiment)
        .order_by(
            NewsArticleModel.published_at.desc().nulls_last(),
            NewsArticleModel.fetched_at.desc(),
        )
        .limit(limit)
        .offset(offset)
    )

    return db.scalars(statement).all()


"""
Purpose:
These functions retrieve Gemini-classified news categories
and articles belonging to a selected AI category.
"""


def get_ai_categories(db: Session) -> list[str]:
    """Return distinct categories assigned by Gemini."""

    statement = (
        select(NewsArticleModel.ai_category)
        .where(
            NewsArticleModel.ai_category.is_not(None),
            NewsArticleModel.ai_category != "",
        )
        .distinct()
        .order_by(NewsArticleModel.ai_category)
    )

    return list(db.execute(statement).scalars().all())


def get_articles_by_ai_category(
    db: Session,
    category: str,
    limit: int = 20,
    offset: int = 0,
):
    """Retrieve articles filtered by their Gemini-assigned category."""

    statement = (
        select(NewsArticleModel)
        .where(NewsArticleModel.ai_category.ilike(category))
        .order_by(
            NewsArticleModel.published_at.desc().nulls_last(),
            NewsArticleModel.fetched_at.desc(),
        )
        .limit(limit)
        .offset(offset)
    )

    return db.scalars(statement).all()


def get_article_counts_by_ai_category(db: Session) -> list[dict]:
    """
    Return article counts grouped by AI-generated category.

    Articles without an AI category are excluded from this analysis.
    """

    statement = (
        select(
            NewsArticleModel.ai_category.label("category"),
            func.count(NewsArticleModel.id).label("article_count"),
        )
        .where(
            NewsArticleModel.ai_category.is_not(None),
            func.trim(NewsArticleModel.ai_category) != "",
        )
        .group_by(NewsArticleModel.ai_category)
        .order_by(func.count(NewsArticleModel.id).desc())
    )

    results = db.execute(statement).all()

    return [
        {
            "category": category,
            "article_count": article_count,
        }
        for category, article_count in results
    ]


def get_daily_publishing_trends(
    db: Session,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[dict]:
    """
    Return daily article publication counts.

    Optional date_from and date_to filters restrict the reporting period.
    Articles without a publication date are excluded.
    """

    published_date = func.date(NewsArticleModel.published_at)

    statement = select(
        published_date.label("published_date"),
        func.count(NewsArticleModel.id).label("article_count"),
    ).where(NewsArticleModel.published_at.is_not(None))

    if date_from:
        statement = statement.where(published_date >= date_from)

    if date_to:
        statement = statement.where(published_date <= date_to)

    statement = statement.group_by(published_date).order_by(published_date.asc())

    results = db.execute(statement).all()

    return [
        {
            "date": published_date.isoformat(),
            "article_count": article_count,
        }
        for published_date, article_count in results
    ]
