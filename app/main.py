"""
Purpose:
This file initializes the FastAPI application.

It registers API routers and exposes basic application
health-check endpoints.
"""

from fastapi import FastAPI

from app.news.router import router as news_router

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
