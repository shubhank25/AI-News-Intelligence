"""
Purpose:
This file initializes the FastAPI application, registers API routers,
configures logging and CORS, and manages the automatic Ollama and
Gemini article-analysis schedulers through the application lifespan.
"""

import asyncio
import logging
import logging.handlers
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.news.pipeline import run_ai_analysis_pipeline
from app.news.router import router as news_router
from app.ollama.processor import run_ollama_analysis_batch
from app.ollama.router import router as ollama_router

# --------------------------------------------------
# Scheduler environment configuration
# --------------------------------------------------


def env_flag(name: str, default: bool = True) -> bool:
    """Read a boolean environment variable."""
    return os.getenv(name, str(default)).strip().lower() in (
        "true",
        "1",
        "yes",
        "on",
    )


ENABLE_OLLAMA_SCHEDULER = env_flag(
    "ENABLE_OLLAMA_SCHEDULER",
    True,
)

ENABLE_GEMINI_SCHEDULER = env_flag(
    "ENABLE_GEMINI_SCHEDULER",
    True,
)


# --------------------------------------------------
# Logging setup
# --------------------------------------------------

LOGS_DIR = Path(__file__).resolve().parents[1] / "logs"
LOGS_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.handlers.RotatingFileHandler(
            LOGS_DIR / "app.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        ),
    ],
)

logger = logging.getLogger(__name__)


# --------------------------------------------------
# Scheduler configuration
# --------------------------------------------------

OLLAMA_SCHEDULER_INTERVAL = 300  # 5 minutes
GEMINI_SCHEDULER_INTERVAL = 300  # 5 minutes


# --------------------------------------------------
# Ollama scheduler
# --------------------------------------------------


async def ollama_scheduler():
    """
    Run Ollama analysis automatically every five minutes.

    Each batch processes a maximum of five pending articles.
    """

    logger.info(
        "Ollama scheduler started. Interval: %s seconds",
        OLLAMA_SCHEDULER_INTERVAL,
    )

    while True:
        await asyncio.sleep(OLLAMA_SCHEDULER_INTERVAL)

        try:
            logger.info("Starting scheduled Ollama analysis batch...")

            result = await run_ollama_analysis_batch()

            logger.info(
                "Scheduled Ollama batch completed: %s",
                result,
            )

        except asyncio.CancelledError:
            logger.info("Ollama scheduler cancellation requested.")
            raise

        except Exception:
            logger.exception("Unexpected error in Ollama scheduler.")


# --------------------------------------------------
# Gemini scheduler
# --------------------------------------------------


async def gemini_scheduler():
    """
    Run Gemini analysis automatically every five minutes.

    Processes pending articles only.
    Does not execute the scraping pipeline.
    """

    logger.info(
        "Gemini scheduler started. Interval: %s seconds",
        GEMINI_SCHEDULER_INTERVAL,
    )

    while True:
        await asyncio.sleep(GEMINI_SCHEDULER_INTERVAL)

        try:
            logger.info("Starting scheduled Gemini analysis batch...")

            # Run synchronous Gemini processing without
            # blocking the FastAPI event loop.
            result = await asyncio.to_thread(run_ai_analysis_pipeline)

            logger.info(
                "Scheduled Gemini batch completed: %s",
                result,
            )

        except asyncio.CancelledError:
            logger.info("Gemini scheduler cancellation requested.")
            raise

        except Exception:
            logger.exception("Unexpected error in Gemini scheduler.")


# --------------------------------------------------
# FastAPI application lifespan
# --------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Start enabled AI schedulers and gracefully stop them
    when the FastAPI application shuts down.
    """

    scheduler_tasks = []

    if ENABLE_OLLAMA_SCHEDULER:
        logger.info("Ollama scheduler is ENABLED.")
        scheduler_tasks.append(asyncio.create_task(ollama_scheduler()))
    else:
        logger.info("Ollama scheduler is DISABLED.")

    if ENABLE_GEMINI_SCHEDULER:
        logger.info("Gemini scheduler is ENABLED.")
        scheduler_tasks.append(asyncio.create_task(gemini_scheduler()))
    else:
        logger.info("Gemini scheduler is DISABLED.")

    try:
        yield

    finally:
        for task in scheduler_tasks:
            task.cancel()

        if scheduler_tasks:
            await asyncio.gather(
                *scheduler_tasks,
                return_exceptions=True,
            )

        logger.info("All enabled AI schedulers stopped.")


# --------------------------------------------------
# FastAPI application
# --------------------------------------------------

app = FastAPI(
    title="AI News Intelligence Aggregator",
    description="AI-powered news collection, analysis and RAG platform",
    version="1.0.0",
    lifespan=lifespan,
)


# --------------------------------------------------
# Register API routers
# --------------------------------------------------

app.include_router(news_router)
app.include_router(ollama_router)


# --------------------------------------------------
# Health check endpoints
# --------------------------------------------------


@app.get("/")
def home():
    return {
        "message": "Welcome to AI News Intelligence Aggregator",
        "status": "running",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "schedulers": {
            "ollama": ENABLE_OLLAMA_SCHEDULER,
            "gemini": ENABLE_GEMINI_SCHEDULER,
        },
    }


# --------------------------------------------------
# CORS configuration
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://ai-news-intelligence-frontend.onrender.com",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
