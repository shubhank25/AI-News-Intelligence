"""
Purpose:
This file fetches and parses RSS feeds from configured news sources.

It extracts article metadata such as title, URL, description, author,
publication date, and source, then validates each article using
the NewsArticle Pydantic model.
"""

import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Optional

import feedparser

from app.news.config import REQUEST_TIMEOUT, USER_AGENT
from app.news.feeds import get_all_feeds
from app.news.schemas import NewsArticle

logger = logging.getLogger(__name__)


def parse_published_date(date_value: Optional[str]):
    """
    Convert an RSS publication date into a Python datetime object.
    """

    if not date_value:
        return None

    try:
        return parsedate_to_datetime(date_value)
    except (TypeError, ValueError, OverflowError):
        return None


def parse_single_feed(feed_config: dict) -> list[NewsArticle]:
    """
    Fetch and parse one RSS feed.

    Args:
        feed_config: Configuration containing feed name, URL and category.

    Returns:
        A list of validated NewsArticle objects.
    """

    feed_url = feed_config["url"]
    source_name = feed_config["name"]

    headers = {"User-Agent": USER_AGENT}

    try:
        import requests

        response = requests.get(
            feed_url,
            headers=headers,
            timeout=(5, 30),
        )

        response.raise_for_status()

        parsed_feed = feedparser.parse(response.content)

        if parsed_feed.bozo and not parsed_feed.entries:
            logger.warning("Invalid RSS feed: %s", feed_url)
            return []

        articles = []

        for entry in parsed_feed.entries:
            title = entry.get("title", "").strip()
            article_url = entry.get("link", "").strip()

            if not title or not article_url:
                continue

            published_at = parse_published_date(
                entry.get("published") or entry.get("updated")
            )

            article_data = {
                "title": title,
                "url": article_url,
                "source": source_name,
                "description": entry.get("summary"),
                "author": entry.get("author"),
                "category": feed_config.get("category"),
                "language": feed_config.get("language", "en"),
                "published_at": published_at,
                "fetched_at": datetime.now(timezone.utc),
            }

            try:
                article = NewsArticle(**article_data)
                articles.append(article)

            except Exception as validation_error:
                logger.warning(
                    "Skipping invalid article from %s: %s",
                    source_name,
                    validation_error,
                )

        logger.info(
            "Collected %d articles from %s",
            len(articles),
            source_name,
        )

        return articles

    except requests.RequestException as error:
        logger.error(
            "Failed to fetch RSS feed %s: %s",
            source_name,
            error,
        )
        return []


def parse_all_feeds() -> list[NewsArticle]:
    """
    Fetch and parse all configured RSS feeds.
    """

    all_articles = []

    for feed_config in get_all_feeds():
        articles = parse_single_feed(feed_config)

        all_articles.extend(articles)

    return all_articles
