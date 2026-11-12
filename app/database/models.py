"""
Purpose:
SQLAlchemy ORM models for the AI News Intelligence application.

news_articles   — scraped article data only (no AI fields).
article_ai_analyses — unified AI analysis for both Gemini and ShubhAI,
                      distinguished by the ai_model column.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class NewsArticleModel(Base):
    """
    Scraped news article.  Contains only source/scraping data.
    AI analysis is stored separately in ArticleAIAnalysis.
    """

    __tablename__ = "news_articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    title: Mapped[str] = mapped_column(String(500), nullable=False)

    url: Mapped[str] = mapped_column(
        String(2048),
        unique=True,
        nullable=False,
    )

    source: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    content: Mapped[str | None] = mapped_column(Text, nullable=True)

    author: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # RSS feed category (e.g. "Technology") — not AI-assigned
    category: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
        index=True,
    )

    language: Mapped[str] = mapped_column(
        String(20),
        default="en",
        nullable=False,
    )

    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    content_hash: Mapped[str | None] = mapped_column(
        String(64),
        unique=True,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_now,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_now,
        onupdate=_now,
    )

    def __repr__(self) -> str:
        return (
            f"NewsArticleModel("
            f"id={self.id}, "
            f"title={self.title!r}, "
            f"source={self.source!r})"
        )


class ArticleAIAnalysis(Base):
    """
    Unified AI analysis record for a news article.

    One row per (article_id, ai_model) pair.
    ai_model must be 'gemini' or 'shubhAI'.
    status must be 'pending', 'completed', or 'failed'.

    Gemini and ShubhAI records are fully isolated by ai_model.
    Deleting a news article is blocked while analysis records exist
    (ON DELETE RESTRICT) to prevent accidental data loss.
    """

    __tablename__ = "article_ai_analyses"

    __table_args__ = (
        UniqueConstraint("article_id", "ai_model", name="uq_analyses_article_model"),
        CheckConstraint(
            "ai_model IN ('gemini', 'shubhAI')",
            name="ck_analyses_ai_model",
        ),
        CheckConstraint(
            "status IN ('pending', 'completed', 'failed')",
            name="ck_analyses_status",
        ),
        CheckConstraint(
            "sentiment IN ('positive', 'negative', 'neutral') OR sentiment IS NULL",
            name="ck_analyses_sentiment",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    article_id: Mapped[int] = mapped_column(
        ForeignKey("news_articles.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    ai_model: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    key_points: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    category: Mapped[str | None] = mapped_column(String(150), nullable=True)

    sentiment: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
    )

    attempt_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    analyzed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_now,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_now,
        onupdate=_now,
    )

    def __repr__(self) -> str:
        return (
            f"ArticleAIAnalysis("
            f"id={self.id}, "
            f"article_id={self.article_id}, "
            f"ai_model={self.ai_model!r}, "
            f"status={self.status!r})"
        )
