"""
Purpose:
This file integrates the complete news collection and processing workflow.

It coordinates RSS parsing, URL deduplication, webpage scraping,
article extraction, text cleaning, content hashing, and JSON backup.

It also stores processed articles in PostgreSQL through the database
repository, while keeping JSON backups for recovery and debugging.
"""

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import urlsplit, urlunsplit

from sqlalchemy.exc import SQLAlchemyError

from app.database.connection import SessionLocal
from app.database.repository import (
    create_articles_bulk,
    get_ai_pending_articles,
    get_existing_article_urls,
    upsert_ai_analysis,
    AI_MODEL_GEMINI,
)
from app.news.cleaner import clean_article_text
from app.news.config import MAX_ARTICLES_PER_RUN, RAW_DATA_DIR
from app.news.extractor import extract_article_text
from app.news.rss_parser import parse_all_feeds
from app.news.scraper import fetch_article_html
from app.services.gemini_service import generate_news_summary

logger = logging.getLogger(__name__)


def get_publication_sort_key(article):
    """
    Return the publication date for sorting.

    Articles without a publication date are placed last.
    """

    published_at = getattr(article, "published_at", None)

    if published_at is None:
        return datetime.min.replace(tzinfo=timezone.utc)

    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=timezone.utc)

    return published_at


def normalize_url(url: str) -> str:
    """Normalize URLs by removing tracking parameters and fragments."""

    parsed = urlsplit(url.strip())

    tracking_parameters = {
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "utm_term",
        "utm_content",
        "fbclid",
        "gclid",
    }

    query_parts = [
        part
        for part in parsed.query.split("&")
        if part and part.split("=")[0].lower() not in tracking_parameters
    ]

    return urlunsplit(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path.rstrip("/") or "/",
            "&".join(query_parts),
            "",
        )
    )


def generate_content_hash(content: str) -> str:
    """Generate a SHA-256 hash for article content."""

    return hashlib.sha256(content.encode("utf-8")).hexdigest()


"""
Purpose:
This function processes an individual news article.

It downloads the webpage, extracts and cleans its content,
generates a content hash, and optionally enriches the article
with AI-generated summary, key points, category, and sentiment.
"""


def scrape_article(article) -> Optional[dict]:
    """Download, extract, and clean one article. No AI analysis."""

    html = fetch_article_html(str(article.url))

    if not html:
        return None

    extracted_content = extract_article_text(html)

    if not extracted_content:
        return None

    cleaned_content = clean_article_text(extracted_content)

    if not cleaned_content:
        return None

    article.content = cleaned_content
    article.content_hash = generate_content_hash(cleaned_content)

    return article.model_dump(mode="json")


def process_article(article) -> Optional[dict]:
    """Download, extract, and clean one article. AI analysis is handled separately."""

    html = fetch_article_html(str(article.url))

    if not html:
        return None

    extracted_content = extract_article_text(html)

    if not extracted_content:
        return None

    cleaned_content = clean_article_text(extracted_content)

    if not cleaned_content:
        return None

    article.content = cleaned_content
    article.content_hash = generate_content_hash(cleaned_content)

    return article.model_dump(mode="json")


def save_articles(articles: list[dict]) -> Path:
    """Save processed articles as a timestamped JSON backup."""

    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    output_file = RAW_DATA_DIR / f"news_{timestamp}.json"

    with output_file.open("w", encoding="utf-8") as file:
        json.dump(
            articles,
            file,
            ensure_ascii=False,
            indent=4,
        )

    return output_file


def save_articles_to_database(articles: list[dict]) -> int:
    """Bulk-insert processed articles into PostgreSQL."""

    if not articles:
        return 0

    with SessionLocal() as db:
        return create_articles_bulk(db, articles)


"""
Purpose:
This function executes the complete news collection pipeline.

It sorts RSS entries by publication date, skips previously stored URLs,
processes new articles, removes duplicates, and saves the results
to JSON and PostgreSQL.
"""


def run_scraping_pipeline() -> dict:
    """Fetch RSS feeds, scrape articles, and save to DB without AI analysis."""

    logger.info("Starting scraping pipeline")

    rss_articles = parse_all_feeds()

    rss_articles.sort(key=get_publication_sort_key, reverse=True)

    article_urls = [normalize_url(str(article.url)) for article in rss_articles]

    try:
        with SessionLocal() as db:
            database_urls = get_existing_article_urls(db, article_urls)
    except SQLAlchemyError as error:
        logger.exception("Failed to check existing article URLs")
        return {
            "status": "failed",
            "error": str(error),
            "rss_articles_found": len(rss_articles),
            "scraped_articles": 0,
            "skipped_duplicates": 0,
            "failed_articles": 0,
            "database_inserted": 0,
        }

    seen_urls = set(database_urls)
    seen_content_hashes = set()
    scraped_articles = []
    skipped_duplicates = 0
    failed_articles = 0

    for article in rss_articles:
        if len(scraped_articles) >= MAX_ARTICLES_PER_RUN:
            break

        normalized_url = normalize_url(str(article.url))

        if normalized_url in seen_urls:
            skipped_duplicates += 1
            continue

        seen_urls.add(normalized_url)

        scraped = scrape_article(article)

        if not scraped:
            failed_articles += 1
            continue

        if scraped["content_hash"] in seen_content_hashes:
            skipped_duplicates += 1
            continue

        seen_content_hashes.add(scraped["content_hash"])
        scraped_articles.append(scraped)

    output_file = None
    if scraped_articles:
        output_file = save_articles(scraped_articles)

    database_inserted = 0
    database_error = None

    try:
        database_inserted = save_articles_to_database(scraped_articles)
        database_status = "completed"
    except SQLAlchemyError as error:
        database_status = "failed"
        database_error = str(error)
        logger.exception("Failed to save scraped articles to PostgreSQL")

    result = {
        "status": "completed" if database_status == "completed" else "completed_with_database_error",
        "rss_articles_found": len(rss_articles),
        "scraped_articles": len(scraped_articles),
        "skipped_duplicates": skipped_duplicates,
        "failed_articles": failed_articles,
        "database_inserted": database_inserted,
        "database_status": database_status,
        "database_error": database_error,
        "output_file": str(output_file) if output_file else None,
    }

    logger.info("Scraping pipeline completed: %s", result)
    return result


def run_ai_analysis_pipeline() -> dict:
    """Run Gemini AI analysis on pending articles, saving to article_ai_analyses."""

    logger.info("Starting Gemini AI analysis pipeline")

    try:
        with SessionLocal() as db:
            pending = get_ai_pending_articles(db, ai_model=AI_MODEL_GEMINI, limit=MAX_ARTICLES_PER_RUN)
    except SQLAlchemyError as error:
        logger.exception("Failed to fetch pending articles for Gemini")
        return {"status": "failed", "error": str(error)}

    if not pending:
        return {"status": "completed", "analyzed": 0, "failed": 0, "message": "No pending articles found."}

    analyzed = 0
    failed = 0

    for article in pending:
        if not article.content:
            failed += 1
            continue

        try:
            ai_result = generate_news_summary(
                title=article.title,
                content=article.content[:20000],
            )

            with SessionLocal() as db:
                upsert_ai_analysis(
                    db=db,
                    article_id=article.id,
                    ai_model=AI_MODEL_GEMINI,
                    analysis=ai_result,
                    status="completed",
                )

            analyzed += 1
            logger.info("Gemini analysis saved for article ID %s: %s", article.id, article.title)

        except Exception as exc:
            failed += 1
            logger.exception("Gemini analysis failed for article ID %s", article.id)
            try:
                with SessionLocal() as db:
                    upsert_ai_analysis(
                        db=db,
                        article_id=article.id,
                        ai_model=AI_MODEL_GEMINI,
                        status="failed",
                        error_message=str(exc),
                    )
            except Exception:
                logger.exception("Could not save Gemini failure for article ID %s", article.id)

    result = {"status": "completed", "analyzed": analyzed, "failed": failed}
    logger.info("Gemini analysis pipeline completed: %s", result)
    return result


def run_news_pipeline() -> dict:
    """Execute the complete news collection and storage pipeline."""

    logger.info("Starting news collection pipeline")

    rss_articles = parse_all_feeds()

    rss_articles.sort(
        key=get_publication_sort_key,
        reverse=True,
    )

    # Normalize URLs before checking for existing records.
    article_urls = [normalize_url(str(article.url)) for article in rss_articles]

    database_urls = []

    try:
        with SessionLocal() as db:
            database_urls = get_existing_article_urls(
                db,
                article_urls,
            )
    except SQLAlchemyError as error:
        logger.exception("Failed to check existing article URLs")

        return {
            "status": "failed",
            "error": str(error),
            "rss_articles_found": len(rss_articles),
            "articles_selected": 0,
            "processed_articles": 0,
            "skipped_duplicates": 0,
            "failed_articles": 0,
            "database_inserted": 0,
            "database_status": "failed",
        }

    seen_urls = set(database_urls)
    seen_content_hashes = set()

    processed_articles = []
    skipped_duplicates = 0
    failed_articles = 0

    for article in rss_articles:
        if len(processed_articles) >= MAX_ARTICLES_PER_RUN:
            break

        normalized_url = normalize_url(str(article.url))

        # Skip articles already stored or repeated in the RSS feeds.
        if normalized_url in seen_urls:
            skipped_duplicates += 1
            continue

        seen_urls.add(normalized_url)

        processed_article = process_article(article)

        if not processed_article:
            failed_articles += 1
            continue

        content_hash = processed_article["content_hash"]

        # Skip articles with identical content.
        if content_hash in seen_content_hashes:
            skipped_duplicates += 1
            continue

        seen_content_hashes.add(content_hash)
        processed_articles.append(processed_article)

    output_file = None

    if processed_articles:
        output_file = save_articles(processed_articles)

    database_inserted = 0
    database_error = None

    try:
        database_inserted = save_articles_to_database(processed_articles)
        database_status = "completed"

    except SQLAlchemyError as error:
        database_status = "failed"
        database_error = str(error)

        logger.exception("Failed to save articles to PostgreSQL")

    result = {
        "rss_articles_found": len(rss_articles),
        "articles_selected": len(processed_articles),
        "processed_articles": len(processed_articles),
        "skipped_duplicates": skipped_duplicates,
        "failed_articles": failed_articles,
        "database_inserted": database_inserted,
        "database_status": database_status,
        "database_error": database_error,
        "output_file": str(output_file) if output_file else None,
        "status": (
            "completed"
            if database_status == "completed"
            else "completed_with_database_error"
        ),
    }

    logger.info("Pipeline completed: %s", result)

    return result
