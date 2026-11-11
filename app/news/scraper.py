"""
Purpose:
This file downloads the HTML webpages of news articles discovered
through RSS feeds.

It handles HTTP requests, timeouts, response validation, and basic
content-type checks. The downloaded HTML is passed to the extractor
module for extracting readable article content.
"""

import logging
import time
from typing import Optional

import requests

from app.news.config import REQUEST_TIMEOUT, USER_AGENT

logger = logging.getLogger(__name__)

# Delay between requests to avoid sending requests too frequently.
REQUEST_DELAY = 1


def fetch_article_html(url: str) -> Optional[str]:
    """
    Download the HTML content of an article webpage.

    Args:
        url: Original article URL.

    Returns:
        HTML content as a string, or None if the request fails.
    """

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml",
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "").lower()

        if "text/html" not in content_type:
            logger.warning(
                "Unsupported content type for %s: %s",
                url,
                content_type,
            )
            return None

        time.sleep(REQUEST_DELAY)

        return response.text

    except requests.RequestException as error:
        logger.error(
            "Failed to download article %s: %s",
            url,
            error,
        )
        return None
