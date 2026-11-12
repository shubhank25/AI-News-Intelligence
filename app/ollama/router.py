"""
Purpose:
REST API endpoints for ShubhAI article analyses.

All queries filter by ai_model='shubhAI' in the unified
article_ai_analyses table. Gemini records are never exposed here.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import ArticleAIAnalysis, NewsArticleModel
from app.database.repository import (
    AI_MODEL_SHUBHAI,
    count_ai_pending_articles,
    get_ai_pending_articles,
)

router = APIRouter(prefix="/api/ollama", tags=["ShubhAI Analysis"])


def _format_analysis(analysis: ArticleAIAnalysis, article: NewsArticleModel) -> dict:
    return {
        "article_id": article.id,
        "title": article.title,
        "url": article.url,
        "source": article.source,
        "analysis": {
            "summary": analysis.summary,
            "key_points": analysis.key_points or [],
            "category": analysis.category,
            "sentiment": analysis.sentiment,
            "status": analysis.status,
            "attempt_count": analysis.attempt_count,
            "analyzed_at": analysis.analyzed_at,
        },
    }


def _format_pending(article: NewsArticleModel) -> dict:
    return {
        "article_id": article.id,
        "title": article.title,
        "url": article.url,
        "source": article.source,
    }


@router.get("/analyses")
def list_ollama_analyses(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    category: str | None = Query(default=None),
    sentiment: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Completed ShubhAI analyses with pagination and optional filters."""
    query = (
        db.query(ArticleAIAnalysis, NewsArticleModel)
        .join(NewsArticleModel, NewsArticleModel.id == ArticleAIAnalysis.article_id)
        .filter(
            ArticleAIAnalysis.ai_model == AI_MODEL_SHUBHAI,
            ArticleAIAnalysis.status == "completed",
        )
    )

    if category:
        query = query.filter(
            func.lower(ArticleAIAnalysis.category) == category.lower()
        )
    if sentiment:
        query = query.filter(
            func.lower(ArticleAIAnalysis.sentiment) == sentiment.lower()
        )

    total = query.count()
    records = (
        query.order_by(ArticleAIAnalysis.analyzed_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [_format_analysis(a, art) for a, art in records],
    }


@router.get("/pending")
def list_ollama_pending(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """Articles awaiting ShubhAI analysis."""
    total = count_ai_pending_articles(db, ai_model=AI_MODEL_SHUBHAI)
    articles = get_ai_pending_articles(
        db, ai_model=AI_MODEL_SHUBHAI, limit=limit, offset=offset
    )
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [_format_pending(a) for a in articles],
    }


@router.get("/categories")
def list_ollama_categories(db: Session = Depends(get_db)):
    """Distinct categories assigned by ShubhAI."""
    rows = (
        db.query(ArticleAIAnalysis.category)
        .filter(
            ArticleAIAnalysis.ai_model == AI_MODEL_SHUBHAI,
            ArticleAIAnalysis.status == "completed",
            ArticleAIAnalysis.category.isnot(None),
            func.trim(ArticleAIAnalysis.category) != "",
        )
        .distinct()
        .order_by(ArticleAIAnalysis.category)
        .all()
    )
    return [r[0] for r in rows]


@router.get("/analytics/categories")
def get_ollama_category_analytics(db: Session = Depends(get_db)):
    """Article counts grouped by ShubhAI-assigned category."""
    rows = (
        db.query(
            ArticleAIAnalysis.category,
            func.count(ArticleAIAnalysis.id).label("article_count"),
        )
        .filter(
            ArticleAIAnalysis.ai_model == AI_MODEL_SHUBHAI,
            ArticleAIAnalysis.status == "completed",
            ArticleAIAnalysis.category.isnot(None),
            func.trim(ArticleAIAnalysis.category) != "",
        )
        .group_by(ArticleAIAnalysis.category)
        .order_by(func.count(ArticleAIAnalysis.id).desc())
        .all()
    )
    return [{"category": cat, "article_count": cnt} for cat, cnt in rows]


@router.get("/analyses/{article_id}")
def get_ollama_analysis(article_id: int, db: Session = Depends(get_db)):
    """ShubhAI analysis for a specific article."""
    record = (
        db.query(ArticleAIAnalysis, NewsArticleModel)
        .join(NewsArticleModel, NewsArticleModel.id == ArticleAIAnalysis.article_id)
        .filter(
            ArticleAIAnalysis.article_id == article_id,
            ArticleAIAnalysis.ai_model == AI_MODEL_SHUBHAI,
            ArticleAIAnalysis.status == "completed",
        )
        .first()
    )
    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Completed ShubhAI analysis not found for this article.",
        )
    analysis, article = record
    return _format_analysis(analysis, article)


@router.get("/status")
def get_ollama_status(db: Session = Depends(get_db)):
    """ShubhAI dashboard counts, coverage, and sentiment distribution."""
    total_articles = (
        db.query(func.count(NewsArticleModel.id))
        .filter(
            NewsArticleModel.content.isnot(None),
            func.trim(NewsArticleModel.content) != "",
        )
        .scalar() or 0
    )

    completed = (
        db.query(func.count(ArticleAIAnalysis.id))
        .filter(
            ArticleAIAnalysis.ai_model == AI_MODEL_SHUBHAI,
            ArticleAIAnalysis.status == "completed",
        )
        .scalar() or 0
    )

    failed = (
        db.query(func.count(ArticleAIAnalysis.id))
        .filter(
            ArticleAIAnalysis.ai_model == AI_MODEL_SHUBHAI,
            ArticleAIAnalysis.status == "failed",
        )
        .scalar() or 0
    )

    pending = count_ai_pending_articles(db, ai_model=AI_MODEL_SHUBHAI)

    sentiment_rows = (
        db.query(
            func.lower(ArticleAIAnalysis.sentiment),
            func.count(ArticleAIAnalysis.id),
        )
        .filter(
            ArticleAIAnalysis.ai_model == AI_MODEL_SHUBHAI,
            ArticleAIAnalysis.status == "completed",
        )
        .group_by(func.lower(ArticleAIAnalysis.sentiment))
        .all()
    )

    sentiment_distribution = {"positive": 0, "negative": 0, "neutral": 0}
    for sentiment, cnt in sentiment_rows:
        if sentiment in sentiment_distribution:
            sentiment_distribution[sentiment] = cnt

    coverage = round((completed / total_articles) * 100, 1) if total_articles > 0 else 0.0

    return {
        "total_articles": total_articles,
        "analyzed_articles": completed,
        "completed": completed,
        "pending": pending,
        "failed": failed,
        "coverage_percentage": coverage,
        "sentiment_distribution": sentiment_distribution,
    }
