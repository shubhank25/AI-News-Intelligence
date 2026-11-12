"""
Purpose:
Integration tests for the unified database schema.

Tests cover:
- Article creation and retrieval
- AI analysis upsert for both Gemini and ShubhAI
- Unique constraint on (article_id, ai_model)
- Independent pending queries per AI model
- Sentiment and category filtering
- API-level pagination with accurate totals
- Migration safety: no cross-model data leakage
"""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import delete

from app.database.connection import SessionLocal
from app.database.models import ArticleAIAnalysis, NewsArticleModel
from app.database.repository import (
    AI_MODEL_GEMINI,
    AI_MODEL_SHUBHAI,
    count_ai_analyzed_articles,
    count_ai_pending_articles,
    count_articles,
    create_article,
    get_ai_analyzed_articles,
    get_ai_categories,
    get_ai_pending_articles,
    get_article_by_url,
    get_unified_articles,
    upsert_ai_analysis,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _unique_url() -> str:
    return f"https://test.example.com/article-{uuid4().hex}"


def _make_article(db, url: str | None = None) -> NewsArticleModel:
    url = url or _unique_url()
    article = create_article(db, {
        "title": "Test Article",
        "url": url,
        "source": "Test Source",
        "language": "en",
        "fetched_at": datetime.now(timezone.utc),
        "content": "This is test article content for AI analysis.",
    })
    assert article is not None
    return article


def _cleanup(db, *article_ids):
    """Delete analysis records then articles (FK RESTRICT order)."""
    for aid in article_ids:
        db.execute(
            delete(ArticleAIAnalysis).where(ArticleAIAnalysis.article_id == aid)
        )
    for aid in article_ids:
        db.execute(
            delete(NewsArticleModel).where(NewsArticleModel.id == aid)
        )
    db.commit()


# ---------------------------------------------------------------------------
# Test 1: Article creation and retrieval
# ---------------------------------------------------------------------------

def test_create_and_retrieve_article():
    url = _unique_url()
    with SessionLocal() as db:
        try:
            initial = count_articles(db)
            article = _make_article(db, url)

            assert article.id is not None
            assert article.title == "Test Article"
            assert article.source == "Test Source"

            retrieved = get_article_by_url(db, url)
            assert retrieved is not None
            assert retrieved.id == article.id

            assert count_articles(db) == initial + 1
        finally:
            _cleanup(db, article.id)


def test_duplicate_url_returns_none():
    url = _unique_url()
    with SessionLocal() as db:
        try:
            a1 = _make_article(db, url)
            a2 = create_article(db, {
                "title": "Duplicate",
                "url": url,
                "source": "S",
                "language": "en",
                "fetched_at": datetime.now(timezone.utc),
            })
            assert a2 is None
        finally:
            _cleanup(db, a1.id)


# ---------------------------------------------------------------------------
# Test 2: AI analysis upsert — both models
# ---------------------------------------------------------------------------

def test_upsert_gemini_analysis():
    with SessionLocal() as db:
        article = _make_article(db)
        try:
            record = upsert_ai_analysis(
                db, article.id, AI_MODEL_GEMINI,
                analysis={
                    "summary": "Gemini summary.",
                    "key_points": ["Point 1", "Point 2", "Point 3"],
                    "category": "Technology",
                    "sentiment": "positive",
                },
                status="completed",
            )
            assert record.ai_model == AI_MODEL_GEMINI
            assert record.status == "completed"
            assert record.summary == "Gemini summary."
            assert record.sentiment == "positive"
            assert record.attempt_count == 1
        finally:
            _cleanup(db, article.id)


def test_upsert_shubhai_analysis():
    with SessionLocal() as db:
        article = _make_article(db)
        try:
            record = upsert_ai_analysis(
                db, article.id, AI_MODEL_SHUBHAI,
                analysis={
                    "summary": "ShubhAI summary.",
                    "key_points": ["A", "B", "C"],
                    "category": "AI",
                    "sentiment": "neutral",
                },
                status="completed",
            )
            assert record.ai_model == AI_MODEL_SHUBHAI
            assert record.sentiment == "neutral"
        finally:
            _cleanup(db, article.id)


def test_both_models_on_same_article():
    """One article can have both Gemini and ShubhAI analysis records."""
    with SessionLocal() as db:
        article = _make_article(db)
        try:
            g = upsert_ai_analysis(
                db, article.id, AI_MODEL_GEMINI,
                analysis={"summary": "G", "key_points": ["1", "2", "3"], "category": "Tech", "sentiment": "positive"},
                status="completed",
            )
            s = upsert_ai_analysis(
                db, article.id, AI_MODEL_SHUBHAI,
                analysis={"summary": "S", "key_points": ["a", "b", "c"], "category": "AI", "sentiment": "negative"},
                status="completed",
            )
            assert g.id != s.id
            assert g.ai_model == AI_MODEL_GEMINI
            assert s.ai_model == AI_MODEL_SHUBHAI
            assert g.sentiment == "positive"
            assert s.sentiment == "negative"
        finally:
            _cleanup(db, article.id)


# ---------------------------------------------------------------------------
# Test 3: Unique constraint on (article_id, ai_model)
# ---------------------------------------------------------------------------

def test_upsert_increments_attempt_count():
    """Re-upserting the same (article_id, ai_model) updates, not duplicates."""
    with SessionLocal() as db:
        article = _make_article(db)
        try:
            r1 = upsert_ai_analysis(
                db, article.id, AI_MODEL_GEMINI,
                analysis={"summary": "v1", "key_points": ["1", "2", "3"], "category": "Tech", "sentiment": "neutral"},
                status="completed",
            )
            assert r1.attempt_count == 1

            r2 = upsert_ai_analysis(
                db, article.id, AI_MODEL_GEMINI,
                analysis={"summary": "v2", "key_points": ["1", "2", "3"], "category": "Tech", "sentiment": "positive"},
                status="completed",
            )
            assert r2.id == r1.id          # same row updated
            assert r2.attempt_count == 2
            assert r2.summary == "v2"
            assert r2.sentiment == "positive"
        finally:
            _cleanup(db, article.id)


# ---------------------------------------------------------------------------
# Test 4: Independent pending queries per AI model
# ---------------------------------------------------------------------------

def test_pending_is_independent_per_model():
    """
    Article with Gemini analysis is still pending for ShubhAI,
    and vice versa.
    """
    with SessionLocal() as db:
        article = _make_article(db)
        try:
            # Initially pending for both
            gemini_pending_before = count_ai_pending_articles(db, AI_MODEL_GEMINI)
            shubhai_pending_before = count_ai_pending_articles(db, AI_MODEL_SHUBHAI)

            # Analyze with Gemini only
            upsert_ai_analysis(
                db, article.id, AI_MODEL_GEMINI,
                analysis={"summary": "G", "key_points": ["1", "2", "3"], "category": "Tech", "sentiment": "neutral"},
                status="completed",
            )

            gemini_pending_after = count_ai_pending_articles(db, AI_MODEL_GEMINI)
            shubhai_pending_after = count_ai_pending_articles(db, AI_MODEL_SHUBHAI)

            # Gemini pending count decreased by 1
            assert gemini_pending_after == gemini_pending_before - 1
            # ShubhAI pending count unchanged — article still pending for ShubhAI
            assert shubhai_pending_after == shubhai_pending_before
        finally:
            _cleanup(db, article.id)


def test_failed_analysis_stays_pending_within_retry_limit():
    with SessionLocal() as db:
        article = _make_article(db)
        try:
            pending_before = count_ai_pending_articles(db, AI_MODEL_GEMINI)

            upsert_ai_analysis(
                db, article.id, AI_MODEL_GEMINI,
                status="failed",
                error_message="Timeout",
            )

            # Still pending (attempt_count=1 < MAX=3)
            pending_after = count_ai_pending_articles(db, AI_MODEL_GEMINI)
            assert pending_after == pending_before
        finally:
            _cleanup(db, article.id)


# ---------------------------------------------------------------------------
# Test 5: Sentiment filtering
# ---------------------------------------------------------------------------

def test_sentiment_filter_gemini():
    with SessionLocal() as db:
        article = _make_article(db)
        try:
            upsert_ai_analysis(
                db, article.id, AI_MODEL_GEMINI,
                analysis={"summary": "S", "key_points": ["1", "2", "3"], "category": "Tech", "sentiment": "negative"},
                status="completed",
            )
            result = get_unified_articles(db, ai_model=AI_MODEL_GEMINI, ai_sentiment="negative")
            ids = [a.id for a in result["items"]]
            assert article.id in ids
            assert result["total"] >= 1
        finally:
            _cleanup(db, article.id)


def test_sentiment_filter_shubhai():
    with SessionLocal() as db:
        article = _make_article(db)
        try:
            upsert_ai_analysis(
                db, article.id, AI_MODEL_SHUBHAI,
                analysis={"summary": "S", "key_points": ["a", "b", "c"], "category": "AI", "sentiment": "positive"},
                status="completed",
            )
            result = get_unified_articles(db, ai_model=AI_MODEL_SHUBHAI, ai_sentiment="positive")
            ids = [a.id for a in result["items"]]
            assert article.id in ids
        finally:
            _cleanup(db, article.id)


def test_gemini_sentiment_does_not_leak_into_shubhai():
    """Gemini positive article must NOT appear in ShubhAI positive filter."""
    with SessionLocal() as db:
        article = _make_article(db)
        try:
            upsert_ai_analysis(
                db, article.id, AI_MODEL_GEMINI,
                analysis={"summary": "G", "key_points": ["1", "2", "3"], "category": "Tech", "sentiment": "positive"},
                status="completed",
            )
            # No ShubhAI analysis for this article
            result = get_unified_articles(db, ai_model=AI_MODEL_SHUBHAI, ai_sentiment="positive")
            ids = [a.id for a in result["items"]]
            assert article.id not in ids
        finally:
            _cleanup(db, article.id)


# ---------------------------------------------------------------------------
# Test 6: Category filtering
# ---------------------------------------------------------------------------

def test_category_filter_gemini():
    with SessionLocal() as db:
        article = _make_article(db)
        try:
            upsert_ai_analysis(
                db, article.id, AI_MODEL_GEMINI,
                analysis={"summary": "S", "key_points": ["1", "2", "3"], "category": "Science", "sentiment": "neutral"},
                status="completed",
            )
            cats = get_ai_categories(db, AI_MODEL_GEMINI)
            assert "Science" in cats

            result = get_unified_articles(db, ai_model=AI_MODEL_GEMINI, ai_category="Science")
            ids = [a.id for a in result["items"]]
            assert article.id in ids
        finally:
            _cleanup(db, article.id)


# ---------------------------------------------------------------------------
# Test 7: API-level pagination
# ---------------------------------------------------------------------------

def test_pagination_limit_and_offset():
    """Page 1 and page 2 return different non-overlapping articles."""
    with SessionLocal() as db:
        created_ids = []
        try:
            for i in range(12):
                a = _make_article(db)
                upsert_ai_analysis(
                    db, a.id, AI_MODEL_GEMINI,
                    analysis={"summary": f"S{i}", "key_points": ["1", "2", "3"], "category": "Tech", "sentiment": "neutral"},
                    status="completed",
                )
                created_ids.append(a.id)

            page1 = get_unified_articles(db, ai_model=AI_MODEL_GEMINI, limit=10, offset=0)
            page2 = get_unified_articles(db, ai_model=AI_MODEL_GEMINI, limit=10, offset=10)

            assert len(page1["items"]) == 10
            assert page1["total"] >= 12

            p1_ids = {a.id for a in page1["items"]}
            p2_ids = {a.id for a in page2["items"]}
            assert len(p1_ids & p2_ids) == 0  # no overlap
        finally:
            _cleanup(db, *created_ids)


def test_total_reflects_filters():
    """Total count must reflect applied filters, not the full table."""
    with SessionLocal() as db:
        pos_ids = []
        neg_ids = []
        try:
            for _ in range(3):
                a = _make_article(db)
                upsert_ai_analysis(
                    db, a.id, AI_MODEL_GEMINI,
                    analysis={"summary": "S", "key_points": ["1", "2", "3"], "category": "Tech", "sentiment": "positive"},
                    status="completed",
                )
                pos_ids.append(a.id)

            for _ in range(2):
                a = _make_article(db)
                upsert_ai_analysis(
                    db, a.id, AI_MODEL_GEMINI,
                    analysis={"summary": "S", "key_points": ["1", "2", "3"], "category": "Tech", "sentiment": "negative"},
                    status="completed",
                )
                neg_ids.append(a.id)

            pos_result = get_unified_articles(db, ai_model=AI_MODEL_GEMINI, ai_sentiment="positive")
            neg_result = get_unified_articles(db, ai_model=AI_MODEL_GEMINI, ai_sentiment="negative")

            assert pos_result["total"] >= 3
            assert neg_result["total"] >= 2
            # Totals are different — filters are applied correctly
            assert pos_result["total"] != neg_result["total"]
        finally:
            _cleanup(db, *pos_ids, *neg_ids)


# ---------------------------------------------------------------------------
# Test 8: Analyzed count
# ---------------------------------------------------------------------------

def test_analyzed_count_per_model():
    with SessionLocal() as db:
        article = _make_article(db)
        try:
            before_g = count_ai_analyzed_articles(db, AI_MODEL_GEMINI)
            before_s = count_ai_analyzed_articles(db, AI_MODEL_SHUBHAI)

            upsert_ai_analysis(
                db, article.id, AI_MODEL_GEMINI,
                analysis={"summary": "G", "key_points": ["1", "2", "3"], "category": "Tech", "sentiment": "neutral"},
                status="completed",
            )

            assert count_ai_analyzed_articles(db, AI_MODEL_GEMINI) == before_g + 1
            assert count_ai_analyzed_articles(db, AI_MODEL_SHUBHAI) == before_s
        finally:
            _cleanup(db, article.id)
