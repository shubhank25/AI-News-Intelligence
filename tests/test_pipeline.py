"""
Purpose:
This file contains automated tests for the news pipeline.

It verifies URL normalization, content hashing, article processing,
JSON storage, duplicate detection, and pipeline orchestration.

External HTTP requests are mocked to keep tests fast and reliable.
"""

import json
from types import SimpleNamespace

from app.news.pipeline import (
    generate_content_hash,
    normalize_url,
    process_article,
    run_news_pipeline,
    save_articles,
)
from app.news.schemas import NewsArticle

# --------------------------------------------------
# URL NORMALIZATION TESTS
# --------------------------------------------------


def test_normalize_url_removes_tracking_parameters():
    url = "https://Example.com/article/?utm_source=google&utm_medium=rss&id=123"

    result = normalize_url(url)

    assert result == "https://example.com/article?id=123"


def test_normalize_url_removes_trailing_slash():
    url = "https://example.com/article/"

    result = normalize_url(url)

    assert result == "https://example.com/article"


def test_normalize_url_removes_fragment():
    url = "https://example.com/article#section"

    result = normalize_url(url)

    assert result == "https://example.com/article"


# --------------------------------------------------
# CONTENT HASH TESTS
# --------------------------------------------------


def test_generate_content_hash_returns_sha256():
    content = "Artificial Intelligence is changing technology."

    result = generate_content_hash(content)

    assert len(result) == 64


def test_generate_content_hash_is_consistent():
    content = "AI News Intelligence"

    first_hash = generate_content_hash(content)
    second_hash = generate_content_hash(content)

    assert first_hash == second_hash


def test_generate_content_hash_changes_with_content():
    first_hash = generate_content_hash("Article One")
    second_hash = generate_content_hash("Article Two")

    assert first_hash != second_hash


# --------------------------------------------------
# ARTICLE PROCESSING TESTS
# --------------------------------------------------


def test_process_article_success(monkeypatch):
    article = NewsArticle(
        title="Test Article",
        url="https://example.com/article",
        source="Test Source",
    )

    monkeypatch.setattr(
        "app.news.pipeline.fetch_article_html",
        lambda url: "<html>Test</html>",
    )

    monkeypatch.setattr(
        "app.news.pipeline.extract_article_text",
        lambda html: "  Artificial Intelligence is growing.  ",
    )

    result = process_article(article)

    assert result is not None
    assert result["content"] == "Artificial Intelligence is growing."
    assert len(result["content_hash"]) == 64


def test_process_article_returns_none_when_download_fails(monkeypatch):
    article = NewsArticle(
        title="Test Article",
        url="https://example.com/article",
        source="Test Source",
    )

    monkeypatch.setattr(
        "app.news.pipeline.fetch_article_html",
        lambda url: None,
    )

    result = process_article(article)

    assert result is None


# --------------------------------------------------
# JSON STORAGE TEST
# --------------------------------------------------


def test_save_articles_creates_json_file(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "app.news.pipeline.RAW_DATA_DIR",
        tmp_path,
    )

    articles = [
        {
            "title": "Test News",
            "content": "Test article content",
        }
    ]

    output_file = save_articles(articles)

    assert output_file.exists()

    with output_file.open("r", encoding="utf-8") as file:
        saved_data = json.load(file)

    assert len(saved_data) == 1
    assert saved_data[0]["title"] == "Test News"


# --------------------------------------------------
# COMPLETE PIPELINE ORCHESTRATION TEST
# --------------------------------------------------


def test_run_news_pipeline_handles_duplicates_and_failures(
    monkeypatch,
):
    articles = [
        SimpleNamespace(url="https://example.com/story?utm_source=rss"),
        SimpleNamespace(url="https://example.com/story"),
        SimpleNamespace(url="https://example.com/another-story"),
        SimpleNamespace(url="https://example.com/failed-story"),
    ]

    monkeypatch.setattr(
        "app.news.pipeline.parse_all_feeds",
        lambda: articles,
    )

    processed_urls = []

    def mock_process_article(article):
        processed_urls.append(str(article.url))

        if "failed-story" in str(article.url):
            return None

        return {
            "title": "Test Article",
            "url": str(article.url),
            "source": "Test Source",
            "description": "Test description",
            "content": "Test article content",
            "author": None,
            "category": "Technology",
            "language": "en",
            "published_at": None,
            "fetched_at": "2026-11-10T12:00:00+00:00",
            "content_hash": "same-content-hash",
        }

    monkeypatch.setattr(
        "app.news.pipeline.process_article",
        mock_process_article,
    )

    saved_articles = []

    def mock_save_articles(articles_to_save):
        saved_articles.extend(articles_to_save)
        return "test_output.json"

    monkeypatch.setattr(
        "app.news.pipeline.save_articles",
        mock_save_articles,
    )

    monkeypatch.setattr(
        "app.news.pipeline.save_articles_to_database",
        lambda articles: len(articles),
    )

    result = run_news_pipeline()

    assert result["rss_articles_found"] == 4
    assert result["processed_articles"] == 1
    assert result["skipped_duplicates"] == 2
    assert result["failed_articles"] == 1
    assert result["status"] == "completed"

    assert len(processed_urls) == 3
    assert len(saved_articles) == 1
