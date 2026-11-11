"""
Purpose:
This file contains automated tests for the RSS parser.

It verifies publication date parsing, RSS entry validation,
successful feed processing, and HTTP failure handling without
making real network requests.
"""

from unittest.mock import Mock, patch

import requests

from app.news.rss_parser import (
    parse_published_date,
    parse_single_feed,
)


def test_parse_published_date_valid():
    result = parse_published_date("Mon, 10 Nov 2026 10:00:00 GMT")

    assert result is not None
    assert result.year == 2026


def test_parse_published_date_invalid():
    result = parse_published_date("invalid-date")

    assert result is None


def test_parse_published_date_empty():
    assert parse_published_date(None) is None


@patch("requests.get")
def test_parse_single_feed_success(mock_get):
    mock_response = Mock()
    mock_response.content = b"""
    <rss version="2.0">
        <channel>
            <title>Test Feed</title>
            <item>
                <title>AI Testing Article</title>
                <link>https://example.com/article</link>
                <description>Test description</description>
            </item>
        </channel>
    </rss>
    """
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    feed_config = {
        "name": "Test Source",
        "url": "https://example.com/rss",
        "category": "Technology",
        "language": "en",
    }

    result = parse_single_feed(feed_config)

    assert len(result) == 1
    assert result[0].title == "AI Testing Article"
    assert result[0].source == "Test Source"


@patch("requests.get")
def test_parse_single_feed_http_failure(mock_get):
    mock_get.side_effect = requests.RequestException("Connection failed")

    feed_config = {
        "name": "Test Source",
        "url": "https://example.com/rss",
        "category": "Technology",
        "language": "en",
    }

    result = parse_single_feed(feed_config)

    assert result == []
