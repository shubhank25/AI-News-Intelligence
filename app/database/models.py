"""
Purpose:
This file defines SQLAlchemy ORM models for the application.

It maps collected news articles and their AI-generated analysis
to PostgreSQL columns, including summaries, key points, categories,
and sentiment.
"""

from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class NewsArticleModel(Base):
    """
    Database model representing a collected news article
    and its optional AI-generated analysis.
    """

    __tablename__ = "news_articles"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

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

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    content: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    author: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

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

    # AI-generated analysis fields

    ai_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    ai_key_points: Mapped[list[str] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    ai_category: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    ai_sentiment: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    def __repr__(self) -> str:
        return (
            f"NewsArticleModel("
            f"id={self.id}, "
            f"title={self.title!r}, "
            f"source={self.source!r})"
        )
