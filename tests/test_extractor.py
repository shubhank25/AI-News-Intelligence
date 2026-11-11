"""
Purpose:
This file contains automated tests for the article extractor.

It verifies that the extractor handles valid HTML, empty HTML,
and HTML pages without extractable article content.
"""

from unittest.mock import patch

from app.news.extractor import extract_article_text


def test_extract_article_text_success():
    html = """
    <html>
        <head><title>Test Article</title></head>
        <body>
            <article>
                <h1>Artificial Intelligence</h1>
                <p>
                    Artificial Intelligence is transforming
                    the technology industry.
                </p>
                <p>
                    It is being used across multiple industries.
                </p>
            </article>
        </body>
    </html>
    """

    result = extract_article_text(html)

    assert result is not None
    assert "Artificial Intelligence" in result
    assert "technology industry" in result


def test_extract_article_text_empty_html():
    result = extract_article_text("")

    assert result is None


def test_extract_article_text_whitespace_html():
    result = extract_article_text("   ")

    assert result is None


@patch("app.news.extractor.trafilatura.extract")
def test_extract_article_text_no_content(mock_extract):
    mock_extract.return_value = None

    result = extract_article_text("<html><body>Test</body></html>")

    assert result is None
    mock_extract.assert_called_once()
