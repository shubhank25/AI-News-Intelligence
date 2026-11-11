"""
Purpose:
This file contains automated tests for the article text cleaner.
It verifies that article text is normalized and unwanted whitespace
and control characters are removed correctly.
"""

from app.news.cleaner import clean_article_text


def test_clean_article_text_removes_extra_whitespace():
    input_text = "  Artificial   Intelligence \n\n is changing   technology.  "

    result = clean_article_text(input_text)

    assert result == "Artificial Intelligence is changing technology."


def test_clean_article_text_returns_none_for_empty_input():
    assert clean_article_text("") is None


def test_clean_article_text_returns_none_for_none_input():
    assert clean_article_text(None) is None


def test_clean_article_text_preserves_unicode():
    input_text = "Artificial Intelligence is भविष्य."

    result = clean_article_text(input_text)

    assert result == "Artificial Intelligence is भविष्य."
