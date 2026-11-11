"""
Purpose:
This file cleans and normalizes extracted news article text.

It removes unwanted control characters, normalizes Unicode,
standardizes whitespace, and prepares article content for storage,
LLM processing, and RAG indexing.
"""

import re
import unicodedata
from typing import Optional


def clean_article_text(text: Optional[str]) -> Optional[str]:
    """
    Clean and normalize extracted article text.

    Args:
        text: Raw article text extracted from a webpage.

    Returns:
        Cleaned article text, or None if the input is empty.
    """

    if not text:
        return None

    # Normalize Unicode characters.
    text = unicodedata.normalize("NFC", text)

    # Replace non-breaking spaces with normal spaces.
    text = text.replace("\xa0", " ")

    # Remove unwanted control characters while preserving newlines
    # and tabs for subsequent whitespace normalization.
    text = "".join(
        char for char in text if unicodedata.category(char) != "Cc" or char in "\n\t"
    )

    # Remove leading and trailing whitespace from each line.
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    # Join lines with a single space.
    text = " ".join(lines)

    # Replace multiple spaces with a single space.
    text = re.sub(r"\s+", " ", text)

    return text.strip() or None
