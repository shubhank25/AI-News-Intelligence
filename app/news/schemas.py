"""
Purpose:
This file defines the standard data structure for news articles.

It uses Pydantic to validate and normalize article data collected
from different RSS feeds and news websites.
"""

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class NewsArticle(BaseModel):
    """
    Standard data model representing a single news article.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="ignore",
    )

    title: str = Field(..., min_length=1)
    url: HttpUrl
    source: str = Field(..., min_length=1)

    description: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = None

    category: Optional[str] = None
    language: str = "en"

    published_at: Optional[datetime] = None

    fetched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    content_hash: Optional[str] = None

    """
    Purpose:
    These fields represent optional AI-generated analysis for each article.
    They allow the pipeline to validate and serialize Gemini results
    alongside the original news article data.
    """

    ai_summary: Optional[str] = None
    ai_key_points: Optional[list[str]] = None
    ai_category: Optional[str] = None
    ai_sentiment: Optional[str] = None


class NewsArticleResponse(NewsArticle):
    """
    Purpose:
    This response schema represents a news article returned by the API.

    It enables Pydantic to serialize SQLAlchemy database objects
    into structured JSON responses.
    """

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        extra="ignore",
    )

    id: int
