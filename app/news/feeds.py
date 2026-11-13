"""
Purpose:
This file manages the RSS feed sources used by the application.

It loads RSS feed configurations from environment variables,
including source names, feed URLs, categories, and languages.
This allows news sources to be added, updated, or removed
without modifying the application code.
"""

import json
import os

NEWS_FEEDS = json.loads(os.getenv("NEWS_FEEDS", "[]"))


def get_all_feeds():
    """
    Return all configured RSS feeds.
    """
    return NEWS_FEEDS


def get_feed_by_category(category: str):
    """
    Return RSS feeds matching a category.
    """
    return [feed for feed in NEWS_FEEDS if feed["category"].lower() == category.lower()]
