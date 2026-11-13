"""
Purpose:
Database operations for ShubhAI (Ollama) article analysis.

All queries filter by ai_model='shubhAI' in the unified
article_ai_analyses table. Gemini records are never touched.
"""

from sqlalchemy.orm import Session

from app.database.models import ArticleAIAnalysis, NewsArticleModel
from app.database.repository import (
    AI_MODEL_SHUBHAI,
    count_ai_pending_articles,
    get_ai_pending_articles,
    upsert_ai_analysis,
)


def get_pending_ollama_articles(
    db: Session,
    limit: int | None = 5,
    max_attempts: int = 3,
) -> list[NewsArticleModel]:
    """Fetch articles pending ShubhAI analysis."""
    return get_ai_pending_articles(
        db=db,
        ai_model=AI_MODEL_SHUBHAI,
        limit=limit if limit is not None else 10000,
        offset=0,
    )


def count_pending_ollama_articles(db: Session, max_attempts: int = 3) -> int:
    """Count articles pending ShubhAI analysis."""
    return count_ai_pending_articles(db, ai_model=AI_MODEL_SHUBHAI)


def save_ollama_analysis(
    db: Session,
    article_id: int,
    analysis: dict | None = None,
    status: str = "completed",
    error_message: str | None = None,
) -> ArticleAIAnalysis:
    """Insert or update a ShubhAI analysis record."""
    return upsert_ai_analysis(
        db=db,
        article_id=article_id,
        ai_model=AI_MODEL_SHUBHAI,
        analysis=analysis,
        status=status,
        error_message=error_message,
    )
