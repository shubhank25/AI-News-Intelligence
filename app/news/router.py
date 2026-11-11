"""
Purpose:
This file defines REST API endpoints for retrieving news articles.

It supports pagination, category filtering, individual article
retrieval, category listing, statistics, keyword search, and
Gemini-powered AI analysis filters.
"""

from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.repository import (
    get_ai_analyzed_articles,
    get_ai_categories,
    get_ai_pending_articles,
    get_article_by_id,
    get_article_counts_by_ai_category,
    get_articles,
    get_articles_by_ai_category,
    get_articles_by_ai_sentiment,
    get_categories,
    get_daily_publishing_trends,
    get_news_statistics,
    search_articles,
)
from app.news.schemas import NewsArticleResponse

router = APIRouter(
    prefix="/api/news",
    tags=["News"],
)


@router.get(
    "",
    response_model=list[NewsArticleResponse],
)
def list_news(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    category: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Retrieve news articles with pagination and category filtering."""

    return get_articles(
        db=db,
        limit=limit,
        offset=offset,
        category=category,
    )


@router.get("/categories", response_model=list[str])
def list_categories(db: Session = Depends(get_db)):
    """Retrieve all available RSS article categories."""

    return get_categories(db)


@router.get("/stats")
def news_statistics(db: Session = Depends(get_db)):
    """Retrieve aggregated news statistics."""

    return get_news_statistics(db)


@router.get(
    "/search",
    response_model=list[NewsArticleResponse],
)
def search_news(
    q: str = Query(
        ...,
        min_length=2,
        description="Keyword to search in news articles",
    ),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Search article titles, descriptions, and full content."""

    return search_articles(
        db=db,
        keyword=q,
        limit=limit,
    )


@router.get(
    "/ai/analyzed",
    response_model=list[NewsArticleResponse],
)
def list_ai_analyzed_news(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """Retrieve articles that have completed AI analysis."""

    return get_ai_analyzed_articles(
        db=db,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/ai/pending",
    response_model=list[NewsArticleResponse],
)
def list_ai_pending_news(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """Retrieve articles that do not yet have an AI summary."""

    return get_ai_pending_articles(
        db=db,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/ai/sentiment/{sentiment}",
    response_model=list[NewsArticleResponse],
)
def list_news_by_ai_sentiment(
    sentiment: Literal["positive", "negative", "neutral"],
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """Retrieve AI-analyzed articles filtered by sentiment."""

    return get_articles_by_ai_sentiment(
        db=db,
        sentiment=sentiment,
        limit=limit,
        offset=offset,
    )


"""
Purpose:
These API endpoints expose Gemini-assigned news categories
and allow clients to filter articles by AI category.
"""


@router.get("/ai/categories", response_model=list[str])
def list_ai_categories(
    db: Session = Depends(get_db),
):
    """Retrieve all distinct AI-generated news categories."""

    return get_ai_categories(db)


@router.get(
    "/ai/category/{category}",
    response_model=list[NewsArticleResponse],
)
def list_news_by_ai_category(
    category: str,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """Retrieve articles belonging to a Gemini-assigned category."""

    return get_articles_by_ai_category(
        db=db,
        category=category,
        limit=limit,
        offset=offset,
    )


@router.get("/analytics/categories")
def get_category_analytics(
    db: Session = Depends(get_db),
):
    """
    Return article counts grouped by AI-generated category.
    """

    return get_article_counts_by_ai_category(db)


@router.get("/analytics/publishing-trends")
def get_publishing_trends(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """
    Return daily article publication counts with optional date filters.
    """

    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=400,
            detail="date_from cannot be later than date_to.",
        )

    return get_daily_publishing_trends(
        db=db,
        date_from=date_from,
        date_to=date_to,
    )


@router.get(
    "/{article_id}",
    response_model=NewsArticleResponse,
)
def get_news_by_id(
    article_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve a specific news article by its ID."""

    article = get_article_by_id(db, article_id)

    if article is None:
        raise HTTPException(
            status_code=404,
            detail="News article not found",
        )

    return article
