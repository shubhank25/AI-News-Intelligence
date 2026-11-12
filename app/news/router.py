"""
Purpose:
REST API endpoints for news articles and AI analysis.

All AI-specific endpoints accept an ai_model query parameter
('gemini' or 'shubhAI') to scope results to the correct model.
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.repository import (
    AI_MODEL_GEMINI,
    AI_MODEL_SHUBHAI,
    count_ai_analyzed_articles,
    get_ai_analyzed_articles,
    get_ai_categories,
    get_ai_pending_articles,
    get_article_by_id,
    get_article_counts_by_ai_category,
    get_articles,
    get_categories,
    get_daily_publishing_trends,
    get_news_statistics,
    get_unified_articles,
    search_articles,
)
from app.news.pipeline import (
    run_ai_analysis_pipeline,
    run_news_pipeline,
    run_scraping_pipeline,
)
from app.news.schemas import NewsArticleResponse

router = APIRouter(prefix="/api/news", tags=["News"])

_AI_MODELS = {AI_MODEL_GEMINI, AI_MODEL_SHUBHAI}


def _validate_ai_model(ai_model: str) -> str:
    if ai_model not in _AI_MODELS:
        raise HTTPException(
            status_code=400,
            detail=f"ai_model must be one of: {sorted(_AI_MODELS)}",
        )
    return ai_model


# ---------------------------------------------------------------------------
# Unified paginated endpoint (All News page)
# ---------------------------------------------------------------------------

@router.get("/unified")
def list_news_unified(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search: str | None = Query(default=None),
    ai_category: str | None = Query(default=None),
    ai_sentiment: str | None = Query(default=None),
    ai_model: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """
    Unified paginated news endpoint.
    All filters applied at DB level before pagination.
    Returns {total, limit, offset, items}.
    """
    if ai_model:
        _validate_ai_model(ai_model)
    return get_unified_articles(
        db=db,
        limit=limit,
        offset=offset,
        search=search,
        ai_category=ai_category,
        ai_sentiment=ai_sentiment,
        ai_model=ai_model,
    )


# ---------------------------------------------------------------------------
# Basic article endpoints
# ---------------------------------------------------------------------------

@router.get("", response_model=list[NewsArticleResponse])
def list_news(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    category: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Paginated article list with optional RSS category filter."""
    return get_articles(db=db, limit=limit, offset=offset, category=category)


@router.get("/categories", response_model=list[str])
def list_categories(db: Session = Depends(get_db)):
    """All distinct RSS feed categories."""
    return get_categories(db)


@router.get("/stats")
def news_statistics(
    ai_model: str = Query(default=AI_MODEL_GEMINI),
    db: Session = Depends(get_db),
):
    """Aggregated statistics. AI metrics scoped to ai_model."""
    _validate_ai_model(ai_model)
    return get_news_statistics(db, ai_model=ai_model)


@router.get("/search", response_model=list[NewsArticleResponse])
def search_news(
    q: str = Query(..., min_length=2),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Keyword search across title, description, and content."""
    return search_articles(db=db, keyword=q, limit=limit)


# ---------------------------------------------------------------------------
# AI analysis endpoints — all scoped by ai_model
# ---------------------------------------------------------------------------

@router.get("/ai/analyzed", response_model=list[NewsArticleResponse])
def list_ai_analyzed_news(
    ai_model: str = Query(default=AI_MODEL_GEMINI),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """Articles with completed AI analysis for the given model."""
    _validate_ai_model(ai_model)
    return get_ai_analyzed_articles(db=db, ai_model=ai_model, limit=limit, offset=offset)


@router.get("/ai/analyzed/count")
def count_analyzed_news(
    ai_model: str = Query(default=AI_MODEL_GEMINI),
    db: Session = Depends(get_db),
):
    """Total count of analyzed articles for the given model."""
    _validate_ai_model(ai_model)
    return {"ai_model": ai_model, "total": count_ai_analyzed_articles(db, ai_model)}


@router.get("/ai/pending", response_model=list[NewsArticleResponse])
def list_ai_pending_news(
    ai_model: str = Query(default=AI_MODEL_GEMINI),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """Articles pending AI analysis for the given model."""
    _validate_ai_model(ai_model)
    return get_ai_pending_articles(db=db, ai_model=ai_model, limit=limit, offset=offset)


@router.get("/ai/categories", response_model=list[str])
def list_ai_categories(
    ai_model: str = Query(default=AI_MODEL_GEMINI),
    db: Session = Depends(get_db),
):
    """Distinct categories assigned by the given AI model."""
    _validate_ai_model(ai_model)
    return get_ai_categories(db, ai_model=ai_model)


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------

@router.get("/analytics/categories")
def get_category_analytics(
    ai_model: str = Query(default=AI_MODEL_GEMINI),
    db: Session = Depends(get_db),
):
    """Article counts grouped by AI-assigned category."""
    _validate_ai_model(ai_model)
    return get_article_counts_by_ai_category(db, ai_model=ai_model)


@router.get("/analytics/publishing-trends")
def get_publishing_trends(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Daily article publication counts with optional date filters."""
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=400, detail="date_from cannot be later than date_to.")
    return get_daily_publishing_trends(db=db, date_from=date_from, date_to=date_to)


# ---------------------------------------------------------------------------
# Pipeline triggers
# ---------------------------------------------------------------------------

@router.get("/pipeline/run")
def trigger_pipeline():
    """Trigger the full news collection and Gemini analysis pipeline."""
    return run_news_pipeline()


@router.get("/pipeline/scrape")
def trigger_scraping():
    """Fetch RSS feeds and scrape articles without AI analysis."""
    return run_scraping_pipeline()


@router.get("/pipeline/analyze")
def trigger_ai_analysis():
    """Run Gemini AI analysis on pending articles."""
    return run_ai_analysis_pipeline()


# ---------------------------------------------------------------------------
# Article by ID — must be last to avoid catching /unified, /stats etc.
# ---------------------------------------------------------------------------

@router.get("/{article_id}", response_model=NewsArticleResponse)
def get_news_by_id(article_id: int, db: Session = Depends(get_db)):
    """Retrieve a specific article by ID."""
    article = get_article_by_id(db, article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="News article not found")
    return article
