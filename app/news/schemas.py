"""
Purpose:
Pydantic schemas for the AI News Intelligence API.

NewsArticleResponse  — scraped article data (no AI fields).
AIAnalysisResponse   — one AI analysis record.
NewsArticleWithAnalysis — article + optional analysis, used by unified endpoints.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class NewsArticle(BaseModel):
    """Standard data model for a scraped news article."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

    title: str = Field(..., min_length=1)
    url: HttpUrl
    source: str = Field(..., min_length=1)

    description: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = None
    category: Optional[str] = None
    language: str = "en"
    published_at: Optional[datetime] = None
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    content_hash: Optional[str] = None


class NewsArticleResponse(NewsArticle):
    """API response schema for a scraped news article."""

    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True, extra="ignore")

    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AIAnalysisResponse(BaseModel):
    """API response schema for one AI analysis record."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    article_id: int
    ai_model: str
    summary: Optional[str] = None
    key_points: Optional[list[str]] = None
    category: Optional[str] = None
    sentiment: Optional[str] = None
    status: str
    attempt_count: int
    error_message: Optional[str] = None
    analyzed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
