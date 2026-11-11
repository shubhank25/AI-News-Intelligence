"""
Purpose:
This file centralizes configuration settings for the news collection module.

It defines project directories, HTTP request settings, RSS processing limits,
and other shared configuration values used across the application.
"""

from pathlib import Path

# Project root directory
BASE_DIR = Path(__file__).resolve().parents[2]

# Data storage directories
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"

# Create directories if they do not exist
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

# HTTP request configuration
REQUEST_TIMEOUT = 15

USER_AGENT = "AI-News-Intelligence-Aggregator/1.0 (Educational and research project)"

# RSS configuration
MAX_ARTICLES_PER_FEED = 20

# Supported content types
SUPPORTED_CONTENT_TYPES = [
    "text/html",
    "application/rss+xml",
    "application/xml",
]

# Maximum number of latest news articles processed per pipeline run.
MAX_ARTICLES_PER_RUN = 5
