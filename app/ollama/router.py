"""
Purpose:
Provide read-only REST API endpoints for ShubhAI article analyses,
pending articles, sentiment distribution, and dashboard statistics.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import NewsArticleModel, OllamaArticleAnalysis
from app.ollama.repository import (
    count_pending_ollama_articles,
    get_pending_ollama_articles,
)

router = APIRouter(
    prefix="/api/ollama",
    tags=["ShubhAI Analysis"],
)


def _format_analysis(analysis, article):
    """Build a response containing article details and Ollama analysis."""

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


def _format_pending_article(article):
    """Build a response for an article awaiting ShubhAI analysis."""

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
    """Retrieve completed ShubhAI analyses with pagination and filters."""

    query = (
        db.query(OllamaArticleAnalysis, NewsArticleModel)
        .join(
            NewsArticleModel,
            NewsArticleModel.id == OllamaArticleAnalysis.article_id,
        )
        .filter(OllamaArticleAnalysis.status == "completed")
    )

    if category:
        query = query.filter(
            func.lower(OllamaArticleAnalysis.category) == category.lower()
        )

    if sentiment:
        query = query.filter(
            func.lower(OllamaArticleAnalysis.sentiment) == sentiment.lower()
        )

    total = query.count()

    records = (
        query.order_by(OllamaArticleAnalysis.analyzed_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [_format_analysis(analysis, article) for analysis, article in records],
    }


@router.get("/pending")
def list_ollama_pending_articles(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """Retrieve articles that are awaiting ShubhAI analysis."""

    total = count_pending_ollama_articles(db)

    records = get_pending_ollama_articles(
        db,
        limit=None,
    )

    items = records[offset : offset + limit]

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [_format_pending_article(article) for article in items],
    }


@router.get("/analyses/{article_id}")
def get_ollama_analysis(
    article_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve ShubhAI analysis for a specific article."""

    record = (
        db.query(OllamaArticleAnalysis, NewsArticleModel)
        .join(
            NewsArticleModel,
            NewsArticleModel.id == OllamaArticleAnalysis.article_id,
        )
        .filter(
            OllamaArticleAnalysis.article_id == article_id,
            OllamaArticleAnalysis.status == "completed",
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
def get_ollama_analysis_status(
    db: Session = Depends(get_db),
):
    """Retrieve ShubhAI dashboard counts, coverage, and sentiment distribution."""

    total_articles = (
        db.query(func.count(NewsArticleModel.id))
        .filter(
            NewsArticleModel.content.isnot(None),
            func.trim(NewsArticleModel.content) != "",
        )
        .scalar()
        or 0
    )

    completed = (
        db.query(func.count(OllamaArticleAnalysis.id))
        .filter(OllamaArticleAnalysis.status == "completed")
        .scalar()
        or 0
    )

    failed = (
        db.query(func.count(OllamaArticleAnalysis.id))
        .filter(OllamaArticleAnalysis.status == "failed")
        .scalar()
        or 0
    )

    pending = count_pending_ollama_articles(db)

    sentiment_rows = (
        db.query(
            func.lower(OllamaArticleAnalysis.sentiment),
            func.count(OllamaArticleAnalysis.id),
        )
        .filter(OllamaArticleAnalysis.status == "completed")
        .group_by(func.lower(OllamaArticleAnalysis.sentiment))
        .all()
    )

    sentiment_distribution = {
        "positive": 0,
        "negative": 0,
        "neutral": 0,
    }

    for sentiment, count in sentiment_rows:
        if sentiment in sentiment_distribution:
            sentiment_distribution[sentiment] = count

    coverage_percentage = (
        round((completed / total_articles) * 100, 1) if total_articles > 0 else 0.0
    )

    return {
        "total_articles": total_articles,
        "analyzed_articles": completed,
        "completed": completed,
        "pending": pending,
        "failed": failed,
        "coverage_percentage": coverage_percentage,
        "sentiment_distribution": sentiment_distribution,
    }
