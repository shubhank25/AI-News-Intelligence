"""
Purpose:
This file extracts the main readable article content from raw HTML.

It uses Trafilatura to identify article text while excluding irrelevant
webpage elements such as navigation, scripts, and advertisements.

The extracted text will later be used for cleaning, summarization,
categorization, and RAG processing.
"""

import logging
from typing import Optional

import trafilatura

logger = logging.getLogger(__name__)


def extract_article_text(html: str) -> Optional[str]:
    """
    Extract the main article text from HTML.

    Args:
        html: Raw HTML content of an article webpage.

    Returns:
        Extracted article text, or None if extraction fails.
    """

    if not html or not html.strip():
        logger.warning("Empty HTML received for extraction")
        return None

    try:
        extracted_text = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=False,
            include_links=False,
            favor_precision=True,
        )

        if not extracted_text:
            logger.warning(
                "No article content could be extracted from HTML "
                "(HTML length: %d characters)",
                len(html),
            )
            return None

        return extracted_text.strip()

    except Exception as error:
        logger.exception("Article extraction failed: %s", error)
        return None
