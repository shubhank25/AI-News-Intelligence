"""
Purpose:
This file initializes the FastAPI application.

It registers API routers and exposes basic application
health-check endpoints.
"""

import logging
import logging.handlers
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.news.router import router as news_router

# Logging setup
LOGS_DIR = Path(__file__).resolve().parents[1] / "logs"
LOGS_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.handlers.RotatingFileHandler(
            LOGS_DIR / "app.log",
            maxBytes=5 * 1024 * 1024,  # 5 MB
            backupCount=3,
            encoding="utf-8",
        ),
    ],
)

app = FastAPI(
    title="AI News Intelligence Aggregator",
    description="AI-powered news collection, analysis and RAG platform",
    version="1.0.0",
)


app.include_router(news_router)


@app.get("/")
def home():
    return {
        "message": "Welcome to AI News Intelligence Aggregator",
        "status": "running",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


# Purpose: Allow the deployed React frontend to communicate with the FastAPI backend.

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://ai-news-intelligence-frontend.onrender.com",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
