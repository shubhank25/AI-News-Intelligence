"""
Purpose:
Process pending news articles through the local Ollama service.
Save successful analysis and failed attempts in the dedicated
Ollama analysis table without changing Gemini data.
"""

import logging

from app.database.connection import SessionLocal
from app.ollama.repository import (
    get_pending_ollama_articles,
    save_ollama_analysis,
)
from app.services.ollama_service import analyze_article

logger = logging.getLogger(__name__)

MAX_ARTICLES_PER_RUN = 5
MAX_ATTEMPTS = 3


async def run_ollama_analysis_batch() -> dict:
    """
    Analyze up to five pending articles in one batch.

    Database sessions are closed before calling Ollama so that
    long-running inference does not hold database connections.
    """

    # Step 1: Fetch pending articles from the database.
    with SessionLocal() as db:
        articles = get_pending_ollama_articles(
            db=db,
            limit=MAX_ARTICLES_PER_RUN,
            max_attempts=MAX_ATTEMPTS,
        )

        article_data = [
            {
                "id": article.id,
                "title": article.title,
                "content": article.content,
            }
            for article in articles
        ]

    if not article_data:
        logger.info("Ollama processor: No pending articles found.")

        return {
            "status": "completed",
            "total": 0,
            "successful": 0,
            "failed": 0,
        }

    successful = 0
    failed = 0

    logger.info(
        "Ollama processor: Starting batch of %s articles.",
        len(article_data),
    )

    # Step 2: Analyze articles one by one.
    for article in article_data:
        article_id = article["id"]

        try:
            analysis = await analyze_article(
                title=article["title"],
                content=article["content"],
            )

        except Exception as exc:
            logger.exception(
                "Ollama analysis failed for article ID %s",
                article_id,
            )

            # Step 3: Save failed attempt.
            try:
                with SessionLocal() as db:
                    save_ollama_analysis(
                        db=db,
                        article_id=article_id,
                        status="failed",
                        error_message=str(exc),
                    )

                failed += 1

            except Exception:
                logger.exception(
                    "Could not save failure for article ID %s",
                    article_id,
                )

            continue

        # Step 4: Save successful analysis.
        try:
            with SessionLocal() as db:
                save_ollama_analysis(
                    db=db,
                    article_id=article_id,
                    analysis=analysis,
                    status="completed",
                )

            successful += 1

            logger.info(
                "Ollama analysis saved for article ID %s",
                article_id,
            )

        except Exception:
            logger.exception(
                "Could not save analysis for article ID %s",
                article_id,
            )

    result = {
        "status": "completed",
        "total": len(article_data),
        "successful": successful,
        "failed": failed,
    }

    logger.info("Ollama batch completed: %s", result)

    return result
