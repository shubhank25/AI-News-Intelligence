"""
Purpose:
Handle database operations for Ollama-generated article analysis.
Fetch eligible pending articles, count pending records, and save
successful or failed analysis without modifying Gemini records.
"""

from datetime import datetime, timezone

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.database.models import (
    NewsArticleModel,
    OllamaArticleAnalysis,
)

MAX_OLLAMA_ATTEMPTS = 3


def _pending_ollama_query(
    db: Session,
    max_attempts: int = MAX_OLLAMA_ATTEMPTS,
):
    """Build the common query used to identify Ollama-pending articles."""

    return (
        db.query(NewsArticleModel)
        .outerjoin(
            OllamaArticleAnalysis,
            NewsArticleModel.id == OllamaArticleAnalysis.article_id,
        )
        .filter(
            NewsArticleModel.content.isnot(None),
            func.trim(NewsArticleModel.content) != "",
            or_(
                OllamaArticleAnalysis.id.is_(None),
                and_(
                    OllamaArticleAnalysis.status == "failed",
                    OllamaArticleAnalysis.attempt_count < max_attempts,
                ),
            ),
        )
    )


def get_pending_ollama_articles(
    db: Session,
    limit: int | None = 5,
    max_attempts: int = MAX_OLLAMA_ATTEMPTS,
) -> list[NewsArticleModel]:
    """
    Fetch articles not yet successfully analyzed by Ollama.

    Failed articles are included if they are still eligible for retry.
    Pass limit=None to retrieve all eligible pending articles.
    """

    query = _pending_ollama_query(db, max_attempts)

    query = query.order_by(NewsArticleModel.fetched_at.asc())

    if limit is not None:
        query = query.limit(limit)

    return query.all()


def count_pending_ollama_articles(
    db: Session,
    max_attempts: int = MAX_OLLAMA_ATTEMPTS,
) -> int:
    """Return the total number of articles eligible for Ollama analysis."""

    return (
        _pending_ollama_query(db, max_attempts)
        .with_entities(func.count(NewsArticleModel.id))
        .scalar()
        or 0
    )


def save_ollama_analysis(
    db: Session,
    article_id: int,
    analysis: dict | None = None,
    status: str = "completed",
    error_message: str | None = None,
) -> OllamaArticleAnalysis:
    """
    Insert or update one article's Ollama analysis.

    Existing analysis records are updated instead of duplicated.
    """

    if status not in {"completed", "failed"}:
        raise ValueError("Status must be 'completed' or 'failed'.")

    existing = db.scalar(
        select(OllamaArticleAnalysis).where(
            OllamaArticleAnalysis.article_id == article_id
        )
    )

    if existing is None:
        record = OllamaArticleAnalysis(
            article_id=article_id,
            attempt_count=1,
        )
        db.add(record)
    else:
        record = existing
        record.attempt_count += 1

    record.status = status
    record.error_message = error_message[:2000] if error_message else None

    if status == "completed":
        if not analysis:
            raise ValueError("Analysis data is required for completed status.")

        record.summary = analysis["summary"]
        record.key_points = analysis["key_points"]
        record.category = analysis["category"]
        record.sentiment = analysis["sentiment"]
        record.analyzed_at = datetime.now(timezone.utc)
        record.error_message = None
    else:
        record.analyzed_at = None

    try:
        db.commit()
        db.refresh(record)
        return record
    except Exception:
        db.rollback()
        raise
