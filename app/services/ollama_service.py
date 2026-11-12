"""
Purpose:
Provides an independent integration with the local Ollama API
for AI-powered news article analysis.

This service does not modify or depend on the existing Gemini service.
"""

import json
import os
import re
from typing import Any

import httpx

# Ollama configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:4b")

OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "120"))


# Supported analysis values
ALLOWED_CATEGORIES = {
    "AI",
    "Technology",
    "Business",
    "Science",
    "Security",
}

ALLOWED_SENTIMENTS = {
    "Positive",
    "Negative",
    "Neutral",
}


class OllamaServiceError(Exception):
    """Raised when Ollama analysis fails."""


def _clean_response(content: str) -> str:
    """
    Remove unwanted thinking tags and Markdown fences
    before parsing the model response.
    """

    content = re.sub(
        r"<think>.*?</think>",
        "",
        content,
        flags=re.DOTALL | re.IGNORECASE,
    )

    content = content.strip()

    content = re.sub(r"^```(?:json)?\s*", "", content)
    content = re.sub(r"\s*```$", "", content)

    return content.strip()


"""
Validate and normalize the generated news analysis.
"""


def _validate_analysis(data: Any) -> dict:
    if not isinstance(data, dict):
        raise OllamaServiceError("Invalid JSON object.")

    summary = data.get("summary")
    key_points = data.get("key_points")
    category = data.get("category")
    sentiment = data.get("sentiment")

    if not isinstance(summary, list) or len(summary) != 3:
        raise OllamaServiceError("Summary must contain exactly 3 sentence items.")

    if not all(isinstance(item, str) and item.strip() for item in summary):
        raise OllamaServiceError("Invalid summary sentences.")

    if not isinstance(key_points, list) or len(key_points) != 3:
        raise OllamaServiceError("Analysis must contain exactly 3 key points.")

    if not all(isinstance(point, str) and point.strip() for point in key_points):
        raise OllamaServiceError("Invalid key points.")

    if category not in ALLOWED_CATEGORIES:
        raise OllamaServiceError(f"Unsupported category: {category}")

    if sentiment not in ALLOWED_SENTIMENTS:
        raise OllamaServiceError(f"Unsupported sentiment: {sentiment}")

    return {
        "summary": " ".join(item.strip() for item in summary),
        "key_points": [point.strip() for point in key_points],
        "category": category,
        "sentiment": sentiment,
    }


"""
Purpose:
Analyze news articles using the locally hosted Ollama model.
Returns validated summaries, key points, categories and sentiment.
"""


async def analyze_article(
    title: str,
    content: str,
) -> dict:
    """
    Analyze a news article using the configured local Ollama model.

    Args:
        title: News article title.
        content: Extracted article text.

    Returns:
        Validated structured news analysis.

    Raises:
        OllamaServiceError: If the API request or validation fails.
    """

    if not isinstance(title, str) or not title.strip():
        raise OllamaServiceError("Article title is required.")

    if not isinstance(content, str) or not content.strip():
        raise OllamaServiceError("Article content is required.")

    prompt = f"""
You are shubhAI, a professional AI news analyst.

Analyze the following news article carefully.

ARTICLE TITLE:
{title}

ARTICLE CONTENT:
{content[:12000]}

Return ONLY a valid JSON object with this exact structure:

{{
    "summary": [
        "First complete factual sentence.",
        "Second complete factual sentence.",
        "Third complete factual sentence."
    ],
    "key_points": [
        "First important point",
        "Second important point",
        "Third important point"
    ],
    "category": "AI",
    "sentiment": "Neutral"
}}

STRICT RULES:

1. Summary must be a JSON array containing exactly 3 sentences.
2. Each summary array item must contain exactly ONE complete sentence.
3. Every summary sentence must be concise and factual.
4. Provide exactly 3 meaningful key points.
5. Category must be exactly one of:
   AI, Technology, Business, Science, Security.
6. Sentiment must be exactly one of:
   Positive, Negative, Neutral.
7. Do not invent facts or information.
8. Use only the supplied article.
9. Do not repeat the same information unnecessarily.
10. Do not include Markdown or explanations outside JSON.
11. Return valid JSON only.
"""

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
        "stream": False,
        "format": "json",
        "think": False,
        "options": {
            "temperature": 0.2,
        },
    }

    url = f"{OLLAMA_BASE_URL.rstrip('/')}/api/chat"

    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            response = await client.post(
                url,
                json=payload,
            )

            response.raise_for_status()
            result = response.json()

    except httpx.TimeoutException as exc:
        raise OllamaServiceError("Ollama request timed out.") from exc

    except httpx.HTTPStatusError as exc:
        raise OllamaServiceError(
            f"Ollama API returned HTTP {exc.response.status_code}."
        ) from exc

    except httpx.RequestError as exc:
        raise OllamaServiceError(f"Could not connect to Ollama: {exc}") from exc

    except ValueError as exc:
        raise OllamaServiceError("Ollama returned an invalid API response.") from exc

    message = result.get("message", {})
    raw_content = message.get("content", "")

    if not raw_content:
        raise OllamaServiceError("Ollama returned an empty response.")

    try:
        cleaned_content = _clean_response(raw_content)
        analysis = json.loads(cleaned_content)

    except (json.JSONDecodeError, TypeError) as exc:
        raise OllamaServiceError("Could not parse Ollama's analysis as JSON.") from exc

    return _validate_analysis(analysis)
