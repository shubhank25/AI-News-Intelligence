"""
Purpose:
This file maintains the RSS feed sources used by the application.

It provides a centralized list of news sources, including their names,
feed URLs, and categories, so the RSS parser can process them.
"""

# RSS feed configuration
NEWS_FEEDS = [
    {
        "name": "BBC Technology",
        "url": "https://feeds.bbci.co.uk/news/technology/rss.xml",
        "category": "Technology",
        "language": "en",
    },
    {
        "name": "Hacker News",
        "url": "https://hnrss.org/frontpage",
        "category": "Technology",
        "language": "en",
    },
    {
        "name": "Google AI Blog",
        "url": "https://blog.google/technology/google-labs/rss/",
        "category": "Artificial Intelligence",
        "language": "en",
    },
]


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
