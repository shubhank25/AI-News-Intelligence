"""
Purpose:
Unit tests for the Ollama news analysis service.
Tests response validation without requiring a live Ollama server.
"""

import pytest

from app.services.ollama_service import (
    OllamaServiceError,
    _validate_analysis,
)


@pytest.fixture
def valid_analysis():
    return {
        "summary": [
            "OpenAI introduced new AI capabilities.",
            "The company improved developer tools and APIs.",
            "These updates aim to improve model reasoning.",
        ],
        "key_points": [
            "Improved model reasoning",
            "Enhanced developer tools",
            "Improved API capabilities",
        ],
        "category": "AI",
        "sentiment": "Neutral",
    }


def test_valid_analysis(valid_analysis):
    result = _validate_analysis(valid_analysis)

    assert result["category"] == "AI"
    assert result["sentiment"] == "Neutral"
    assert result["summary"] == (
        "OpenAI introduced new AI capabilities. "
        "The company improved developer tools and APIs. "
        "These updates aim to improve model reasoning."
    )
    assert len(result["key_points"]) == 3


def test_invalid_summary(valid_analysis):
    valid_analysis["summary"] = "Only one sentence."

    with pytest.raises(OllamaServiceError):
        _validate_analysis(valid_analysis)


def test_invalid_key_points(valid_analysis):
    valid_analysis["key_points"] = [
        "First point",
        "Second point",
    ]

    with pytest.raises(OllamaServiceError):
        _validate_analysis(valid_analysis)


def test_invalid_category(valid_analysis):
    valid_analysis["category"] = "Sports"

    with pytest.raises(OllamaServiceError):
        _validate_analysis(valid_analysis)


def test_invalid_sentiment(valid_analysis):
    valid_analysis["sentiment"] = "Unknown"

    with pytest.raises(OllamaServiceError):
        _validate_analysis(valid_analysis)


def test_empty_analysis():
    with pytest.raises(OllamaServiceError):
        _validate_analysis({})
