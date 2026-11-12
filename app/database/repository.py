"""
Purpose:
Database repository for the AI News Intelligence application.

All article queries operate on news_articles only.
All AI analysis queries filter by ai_model ('gemini' or 'shubhAI').
Pending status is calculated independently per AI model.
"""

from datetime import date, datetime, timezone

from sqlalchemy import and_, func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database.models import ArticleAIAnalysis, NewsArticleModel

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

AI_MODEL_GEMINI = "gemini"
AI_MODEL_SHUBHAI = "shubhAI"
MAX_ANALYSIS_ATTEMPTS = 3


# ---------------------------------------------------------------------------
# Article helpers
# ---------------------------------------------------------------------------

def prepare_article_data(article_data: dict) -> dict:
    """Convert ISO datetime strings to datetime objects."""
    prepared = article_data.copy()
    for field in ("published_at", "fetched_at"):
        value = prepared.get(field)
        if isinstance(value, str):
            prepared[field] = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return prepared


# ---------------------------------------------------------------------------
# Article writes
# ---------------------------------------------------------------------------

def create_article(db: Session, article_data: dict) -> NewsArticleModel | None:
    """Insert one article. Returns None if URL or content_hash already exists."""
    prepared = prepare_article_data(article_data)
    try:
        stmt = (
            insert(NewsArticleModel)
            .values(**prepared)
            .on_conflict_do_nothing()
            .returning(NewsArticleModel.id)
        )
        inserted_id = db.execute(stmt).scalar_one_or_none()
        db.commit()
        if inserted_id is None:
            return None
        return db.get(NewsArticleModel, inserted_id)
    except SQLAlchemyError:
        db.rollback()
        raise


def create_articles_bulk(db: Session, articles: list[dict]) -> int:
    """Bulk-insert articles. Returns count of newly inserted rows."""
    if not articles:
        return 0
    prepared = [prepare_article_data(a) for a in articles]
    try:
        stmt = (
            insert(NewsArticleModel)
            .values(prepared)
            .on_conflict_do_nothing()
            .returning(NewsArticleModel.id)
        )
        result = db.execute(stmt)
        inserted_ids = result.scalars().all()
        db.commit()
        return len(inserted_ids)
    except SQLAlchemyError:
        db.rollback()
        raise


# ---------------------------------------------------------------------------
# Article reads
# ---------------------------------------------------------------------------

def get_article_by_id(db: Session, article_id: int) -> NewsArticleModel | None:
    return db.get(NewsArticleModel, article_id)


def get_article_by_url(db: Session, url: str) -> NewsArticleModel | None:
    return db.execute(
        select(NewsArticleModel).where(NewsArticleModel.url == url)
    ).scalar_one_or_none()


def get_articles(
    db: Session,
    limit: int = 50,
    offset: int = 0,
    category: str | None = None,
) -> list[NewsArticleModel]:
    """Paginated article list with optional RSS category filter."""
    stmt = select(NewsArticleModel)
    if category:
        stmt = stmt.where(NewsArticleModel.category.ilike(category))
    stmt = (
        stmt.order_by(
            NewsArticleModel.published_at.desc().nulls_last(),
            NewsArticleModel.fetched_at.desc(),
        )
        .limit(limit)
        .offset(offset)
    )
    return list(db.execute(stmt).scalars().all())


def count_articles(db: Session, category: str | None = None) -> int:
    stmt = select(func.count()).select_from(NewsArticleModel)
    if category:
        stmt = stmt.where(NewsArticleModel.category.ilike(category))
    return db.execute(stmt).scalar_one()


def get_categories(db: Session) -> list[str]:
    """Distinct non-empty RSS feed categories."""
    stmt = (
        select(NewsArticleModel.category)
        .where(
            NewsArticleModel.category.is_not(None),
            NewsArticleModel.category != "",
        )
        .distinct()
        .order_by(NewsArticleModel.category)
    )
    return list(db.execute(stmt).scalars().all())


def get_existing_article_urls(db: Session, urls: list[str]) -> set[str]:
    if not urls:
        return set()
    stmt = select(NewsArticleModel.url).where(NewsArticleModel.url.in_(urls))
    return set(db.execute(stmt).scalars().all())


def search_articles(db: Session, keyword: str, limit: int = 20) -> list[NewsArticleModel]:
    pattern = f"%{keyword.strip()}%"
    stmt = (
        select(NewsArticleModel)
        .where(
            or_(
                NewsArticleModel.title.ilike(pattern),
                NewsArticleModel.description.ilike(pattern),
                NewsArticleModel.content.ilike(pattern),
            )
        )
        .order_by(
            NewsArticleModel.published_at.desc().nulls_last(),
            NewsArticleModel.fetched_at.desc(),
        )
        .limit(limit)
    )
    return list(db.execute(stmt).scalars().all())


# ---------------------------------------------------------------------------
# AI analysis writes
# ---------------------------------------------------------------------------

def upsert_ai_analysis(
    db: Session,
    article_id: int,
    ai_model: str,
    analysis: dict | None = None,
    status: str = "completed",
    error_message: str | None = None,
) -> ArticleAIAnalysis:
    """
    Insert or update one AI analysis record for (article_id, ai_model).

    - status must be 'pending', 'completed', or 'failed'.
    - ai_model must be 'gemini' or 'shubhAI'.
    - Gemini and ShubhAI records are fully isolated.
    """
    if status not in {"pending", "completed", "failed"}:
        raise ValueError(f"Invalid status: {status!r}")
    if ai_model not in {AI_MODEL_GEMINI, AI_MODEL_SHUBHAI}:
        raise ValueError(f"Invalid ai_model: {ai_model!r}")

    existing = db.execute(
        select(ArticleAIAnalysis).where(
            ArticleAIAnalysis.article_id == article_id,
            ArticleAIAnalysis.ai_model == ai_model,
        )
    ).scalar_one_or_none()

    if existing is None:
        record = ArticleAIAnalysis(
            article_id=article_id,
            ai_model=ai_model,
            attempt_count=1,
        )
        db.add(record)
    else:
        record = existing
        record.attempt_count += 1

    record.status = status
    record.error_message = error_message[:2000] if error_message else None
    record.updated_at = datetime.now(timezone.utc)

    if status == "completed":
        if not analysis:
            raise ValueError("analysis dict is required for completed status.")
        record.summary = analysis["summary"]
        record.key_points = analysis["key_points"]
        record.category = analysis["category"]
        record.sentiment = analysis["sentiment"].lower()
        record.analyzed_at = datetime.now(timezone.utc)
        record.error_message = None
    elif status == "failed":
        record.analyzed_at = None

    try:
        db.commit()
        db.refresh(record)
        return record
    except Exception:
        db.rollback()
        raise


# ---------------------------------------------------------------------------
# AI analysis reads — all filtered by ai_model
# ---------------------------------------------------------------------------

def _analysis_base_query(db: Session, ai_model: str):
    """Base query joining news_articles with completed analysis for one model."""
    return (
        db.query(ArticleAIAnalysis, NewsArticleModel)
        .join(NewsArticleModel, NewsArticleModel.id == ArticleAIAnalysis.article_id)
        .filter(
            ArticleAIAnalysis.ai_model == ai_model,
            ArticleAIAnalysis.status == "completed",
        )
    )


def get_ai_analyzed_articles(
    db: Session,
    ai_model: str,
    limit: int = 20,
    offset: int = 0,
) -> list[NewsArticleModel]:
    """Articles with completed analysis for the given AI model."""
    stmt = (
        select(NewsArticleModel)
        .join(
            ArticleAIAnalysis,
            and_(
                ArticleAIAnalysis.article_id == NewsArticleModel.id,
                ArticleAIAnalysis.ai_model == ai_model,
                ArticleAIAnalysis.status == "completed",
            ),
        )
        .order_by(
            NewsArticleModel.published_at.desc().nulls_last(),
            NewsArticleModel.fetched_at.desc(),
        )
        .limit(limit)
        .offset(offset)
    )
    return list(db.execute(stmt).scalars().all())


def count_ai_analyzed_articles(db: Session, ai_model: str) -> int:
    return db.execute(
        select(func.count(NewsArticleModel.id))
        .select_from(NewsArticleModel)
        .join(
            ArticleAIAnalysis,
            and_(
                ArticleAIAnalysis.article_id == NewsArticleModel.id,
                ArticleAIAnalysis.ai_model == ai_model,
                ArticleAIAnalysis.status == "completed",
            ),
        )
    ).scalar_one()


def get_ai_pending_articles(
    db: Session,
    ai_model: str,
    limit: int = 20,
    offset: int = 0,
) -> list[NewsArticleModel]:
    """
    Articles pending analysis for the given AI model.

    Pending = no analysis record OR failed with attempts < MAX_ANALYSIS_ATTEMPTS.
    Articles without content are excluded.
    """
    stmt = (
        select(NewsArticleModel)
        .outerjoin(
            ArticleAIAnalysis,
            and_(
                ArticleAIAnalysis.article_id == NewsArticleModel.id,
                ArticleAIAnalysis.ai_model == ai_model,
            ),
        )
        .where(
            NewsArticleModel.content.is_not(None),
            func.trim(NewsArticleModel.content) != "",
            or_(
                ArticleAIAnalysis.id.is_(None),
                and_(
                    ArticleAIAnalysis.status == "failed",
                    ArticleAIAnalysis.attempt_count < MAX_ANALYSIS_ATTEMPTS,
                ),
            ),
        )
        .order_by(NewsArticleModel.fetched_at.asc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.execute(stmt).scalars().all())


def count_ai_pending_articles(db: Session, ai_model: str) -> int:
    stmt = (
        select(func.count(NewsArticleModel.id))
        .select_from(NewsArticleModel)
        .outerjoin(
            ArticleAIAnalysis,
            and_(
                ArticleAIAnalysis.article_id == NewsArticleModel.id,
                ArticleAIAnalysis.ai_model == ai_model,
            ),
        )
        .where(
            NewsArticleModel.content.is_not(None),
            func.trim(NewsArticleModel.content) != "",
            or_(
                ArticleAIAnalysis.id.is_(None),
                and_(
                    ArticleAIAnalysis.status == "failed",
                    ArticleAIAnalysis.attempt_count < MAX_ANALYSIS_ATTEMPTS,
                ),
            ),
        )
    )
    return db.execute(stmt).scalar_one()


def get_ai_categories(db: Session, ai_model: str) -> list[str]:
    """Distinct categories assigned by the given AI model."""
    stmt = (
        select(ArticleAIAnalysis.category)
        .where(
            ArticleAIAnalysis.ai_model == ai_model,
            ArticleAIAnalysis.status == "completed",
            ArticleAIAnalysis.category.is_not(None),
            func.trim(ArticleAIAnalysis.category) != "",
        )
        .distinct()
        .order_by(ArticleAIAnalysis.category)
    )
    return list(db.execute(stmt).scalars().all())


def get_article_counts_by_ai_category(db: Session, ai_model: str) -> list[dict]:
    """Article counts grouped by AI-assigned category for one model."""
    stmt = (
        select(
            ArticleAIAnalysis.category.label("category"),
            func.count(ArticleAIAnalysis.id).label("article_count"),
        )
        .where(
            ArticleAIAnalysis.ai_model == ai_model,
            ArticleAIAnalysis.status == "completed",
            ArticleAIAnalysis.category.is_not(None),
            func.trim(ArticleAIAnalysis.category) != "",
        )
        .group_by(ArticleAIAnalysis.category)
        .order_by(func.count(ArticleAIAnalysis.id).desc())
    )
    return [
        {"category": cat, "article_count": cnt}
        for cat, cnt in db.execute(stmt).all()
    ]


def get_analysis_for_article(
    db: Session,
    article_id: int,
    ai_model: str,
) -> ArticleAIAnalysis | None:
    """Fetch the completed analysis record for one article and model."""
    return db.execute(
        select(ArticleAIAnalysis).where(
            ArticleAIAnalysis.article_id == article_id,
            ArticleAIAnalysis.ai_model == ai_model,
            ArticleAIAnalysis.status == "completed",
        )
    ).scalar_one_or_none()


# ---------------------------------------------------------------------------
# Unified All-News query (used by /api/news/unified)
# ---------------------------------------------------------------------------

def get_unified_articles(
    db: Session,
    limit: int = 10,
    offset: int = 0,
    search: str | None = None,
    ai_category: str | None = None,
    ai_sentiment: str | None = None,
    ai_model: str | None = None,
) -> dict:
    """
    Paginated article query for the All News page.

    When ai_model is provided, JOINs with article_ai_analyses filtered
    by that model. All filters are applied before LIMIT/OFFSET.
    Returns {total, limit, offset, items}.
    """
    if ai_model:
        base = (
            select(NewsArticleModel)
            .join(
                ArticleAIAnalysis,
                and_(
                    ArticleAIAnalysis.article_id == NewsArticleModel.id,
                    ArticleAIAnalysis.ai_model == ai_model,
                    ArticleAIAnalysis.status == "completed",
                ),
            )
        )
        count_base = (
            select(func.count(NewsArticleModel.id))
            .select_from(NewsArticleModel)
            .join(
                ArticleAIAnalysis,
                and_(
                    ArticleAIAnalysis.article_id == NewsArticleModel.id,
                    ArticleAIAnalysis.ai_model == ai_model,
                    ArticleAIAnalysis.status == "completed",
                ),
            )
        )
    else:
        base = select(NewsArticleModel)
        count_base = select(func.count()).select_from(NewsArticleModel)

    if search:
        pattern = f"%{search.strip()}%"
        sf = or_(
            NewsArticleModel.title.ilike(pattern),
            NewsArticleModel.description.ilike(pattern),
            NewsArticleModel.content.ilike(pattern),
        )
        base = base.where(sf)
        count_base = count_base.where(sf)

    if ai_category and ai_model:
        cf = func.lower(ArticleAIAnalysis.category) == ai_category.lower()
        base = base.where(cf)
        count_base = count_base.where(cf)

    if ai_sentiment and ai_model:
        sf2 = func.lower(ArticleAIAnalysis.sentiment) == ai_sentiment.lower()
        base = base.where(sf2)
        count_base = count_base.where(sf2)

    total = db.execute(count_base).scalar_one()
    items = db.execute(
        base.order_by(
            NewsArticleModel.published_at.desc().nulls_last(),
            NewsArticleModel.fetched_at.desc(),
        )
        .limit(limit)
        .offset(offset)
    ).scalars().all()

    return {"total": total, "limit": limit, "offset": offset, "items": list(items)}


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

def get_news_statistics(db: Session, ai_model: str = AI_MODEL_GEMINI) -> dict:
    """
    Aggregated statistics for the dashboard.
    AI analysis metrics are scoped to the given ai_model.
    """
    total_articles = count_articles(db)
    analyzed = count_ai_analyzed_articles(db, ai_model)
    pending = count_ai_pending_articles(db, ai_model)

    sentiment_rows = db.execute(
        select(
            func.lower(ArticleAIAnalysis.sentiment),
            func.count(ArticleAIAnalysis.id),
        )
        .where(
            ArticleAIAnalysis.ai_model == ai_model,
            ArticleAIAnalysis.status == "completed",
            ArticleAIAnalysis.sentiment.is_not(None),
        )
        .group_by(func.lower(ArticleAIAnalysis.sentiment))
    ).all()

    sentiment_distribution = {"positive": 0, "negative": 0, "neutral": 0}
    for sentiment, cnt in sentiment_rows:
        if sentiment in sentiment_distribution:
            sentiment_distribution[sentiment] = cnt

    source_rows = db.execute(
        select(
            NewsArticleModel.source,
            func.count(NewsArticleModel.id).label("article_count"),
        )
        .group_by(NewsArticleModel.source)
        .order_by(func.count(NewsArticleModel.id).desc())
    ).all()

    coverage = (analyzed / total_articles * 100) if total_articles > 0 else 0.0

    return {
        "total_articles": total_articles,
        "total_sources": len(source_rows),
        "articles_by_source": [
            {"source": s, "article_count": c} for s, c in source_rows
        ],
        "ai_analysis": {
            "ai_model": ai_model,
            "analyzed_articles": analyzed,
            "pending_articles": pending,
            "coverage_percentage": round(coverage, 2),
            "sentiment_distribution": sentiment_distribution,
        },
    }


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------

def get_daily_publishing_trends(
    db: Session,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[dict]:
    published_date = func.date(NewsArticleModel.published_at)
    stmt = select(
        published_date.label("published_date"),
        func.count(NewsArticleModel.id).label("article_count"),
    ).where(NewsArticleModel.published_at.is_not(None))

    if date_from:
        stmt = stmt.where(published_date >= date_from)
    if date_to:
        stmt = stmt.where(published_date <= date_to)

    stmt = stmt.group_by(published_date).order_by(published_date.asc())

    return [
        {"date": pd.isoformat(), "article_count": cnt}
        for pd, cnt in db.execute(stmt).all()
    ]
