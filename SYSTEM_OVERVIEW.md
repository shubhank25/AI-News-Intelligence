<div align="center">

# 🧠 AI News Intelligence — System Overview

### How It Works: From Raw News to AI-Powered Insights

> This document explains the complete technical workflow of the AI News Intelligence platform —
> how news is collected, processed, analyzed by AI, stored, and served to the dashboard.
> Written for clients, managers, and stakeholders.

</div>

---

## 📌 What Does This System Do?

The AI News Intelligence platform **automatically collects news articles** from trusted sources on the internet, **reads and understands each article using Google Gemini AI**, and **presents the insights** through a live dashboard — all without any manual effort.

In simple terms:

```
Internet News  →  Our System Reads It  →  AI Understands It  →  You See the Insights
```

---

## 🏗️ System Architecture

The platform is made up of 4 major layers that work together:

```
┌─────────────────────────────────────────────────────────────────┐
│                        🖥️  React Dashboard                       │
│         (What the user sees — charts, articles, insights)        │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP API calls
┌──────────────────────────▼──────────────────────────────────────┐
│                      🚀  FastAPI Backend                         │
│         (Handles all requests, runs the pipeline, serves data)   │
└──────────┬────────────────────────────────────┬─────────────────┘
           │                                    │
┌──────────▼──────────┐              ┌──────────▼──────────────────┐
│   🤖 Google Gemini  │              │     🗄️ PostgreSQL Database   │
│   (AI Analysis)     │              │  (Stores all articles & AI   │
│                     │              │   results permanently)       │
└─────────────────────┘              └─────────────────────────────┘
```

| Layer | Technology | Purpose |
|---|---|---|
| 🖥️ Frontend | React 19, TypeScript, Tailwind CSS, Recharts | User-facing dashboard |
| 🚀 Backend | Python, FastAPI, SQLAlchemy | API server & pipeline orchestration |
| 🤖 AI | Google Gemini (`gemini-2.0-flash`) | Article analysis & summarization |
| 🗄️ Database | PostgreSQL | Persistent storage of all articles |

---

## 🔄 The Complete Data Flow

Here is the full journey of a news article — from the internet to your dashboard:

```
Step 1: RSS Feeds         →   BBC, Hacker News, Google AI Blog publish new articles
Step 2: RSS Parser        →   System reads the feed and collects article titles & URLs
Step 3: Deduplication     →   Already-seen URLs are skipped (no duplicates)
Step 4: Web Scraper       →   System visits each article URL and downloads the webpage
Step 5: Text Extractor    →   Removes ads, menus, scripts — keeps only article text
Step 6: Text Cleaner      →   Fixes encoding, removes junk characters, normalizes text
Step 7: Content Hashing   →   SHA-256 fingerprint generated to detect duplicate content
Step 8: Gemini AI         →   Article sent to Google Gemini for intelligent analysis
Step 9: Database Storage  →   Article + AI results saved to PostgreSQL
Step 10: JSON Backup      →   A timestamped JSON file is also saved locally
Step 11: API              →   FastAPI serves the data to the React dashboard
Step 12: Dashboard        →   User sees articles, summaries, sentiment, charts
```

---

## 📡 Step 1 — RSS Feed Collection

**File:** `app/news/feeds.py` + `app/news/rss_parser.py`

### What is an RSS Feed?

RSS (Really Simple Syndication) is a standard format that news websites use to publish their latest articles. Instead of visiting each website manually, our system subscribes to these feeds and gets notified of new articles automatically.

### Configured Sources

| Source | URL | Category |
|---|---|---|
| 🔴 BBC Technology | `feeds.bbci.co.uk/news/technology/rss.xml` | Technology |
| 🟠 Hacker News | `hnrss.org/frontpage` | Technology |
| 🔵 Google AI Blog | `blog.google/technology/google-labs/rss/` | Artificial Intelligence |

### What Data is Extracted from RSS?

For each article found in the feed, the system extracts:

| Field | Example |
|---|---|
| Title | "OpenAI releases new model" |
| URL | `https://bbc.com/news/technology/...` |
| Source | "BBC Technology" |
| Description | Short preview text |
| Author | "Jane Smith" |
| Published Date | "2025-01-15 10:30:00" |
| Category | "Technology" |
| Language | "en" |

> Each article is validated using **Pydantic** — if any required field is missing or malformed, the article is skipped with a warning logged.

---

## 🌐 Step 2 — Web Scraping

**File:** `app/news/scraper.py`

RSS feeds only give us a **title and short description** — not the full article. To get the complete content, the system visits each article's URL and downloads the full webpage.

### How It Works

1. The system sends an HTTP GET request to the article URL
2. It identifies itself with a proper `User-Agent` header (good practice, avoids being blocked)
3. It validates the response — only `text/html` pages are accepted
4. A **1-second delay** is added between requests to be respectful to news servers
5. If the request fails (timeout, 404, etc.), the article is skipped and the error is logged

### Protection Against Failures

- **Timeout:** 15 seconds maximum per request
- **Error handling:** Network errors, HTTP errors, and timeouts are all caught gracefully
- **Content-type check:** Non-HTML responses (PDFs, XML, etc.) are rejected

---

## 🔍 Step 3 — Text Extraction

**File:** `app/news/extractor.py`

A downloaded webpage contains a lot of **noise** — navigation menus, advertisements, cookie banners, social media buttons, footers, and scripts. We only want the actual article text.

### Tool Used: Trafilatura

The system uses **Trafilatura**, a specialized Python library built specifically for extracting main article content from webpages. It uses machine learning heuristics to identify the "main content zone" of any webpage.

### What Gets Removed

| Removed | Kept |
|---|---|
| Navigation menus | Article headline |
| Advertisements | Article body paragraphs |
| Cookie banners | Author information |
| Social share buttons | Publication date context |
| Comment sections | Subheadings |
| Scripts & styles | Quotes and key statements |

### Configuration

```
include_comments  = False   ← No reader comments
include_tables    = False   ← No data tables
include_links     = False   ← No hyperlinks
favor_precision   = True    ← Prefer accuracy over recall
```

---

## 🧹 Step 4 — Text Cleaning

**File:** `app/news/cleaner.py`

Even after extraction, the text may contain invisible characters, encoding issues, or inconsistent whitespace. The cleaner normalizes everything.

### Cleaning Steps Applied

| Step | What It Does |
|---|---|
| Unicode normalization (NFC) | Fixes accented characters and special symbols |
| Non-breaking space removal | Replaces `\xa0` with regular spaces |
| Control character removal | Strips invisible/junk characters |
| Line normalization | Trims each line, removes blank lines |
| Whitespace normalization | Collapses multiple spaces into one |

The result is **clean, consistent, storage-ready text** suitable for AI processing.

---

## 🔐 Step 5 — Deduplication

**File:** `app/news/pipeline.py`

The system uses two layers of deduplication to ensure no article is stored twice:

### Layer 1 — URL Deduplication

Before scraping, all article URLs are **normalized** (tracking parameters like `utm_source`, `fbclid`, `gclid` are stripped) and checked against the database. Already-stored URLs are skipped entirely.

```
https://bbc.com/article?utm_source=rss&utm_medium=feed
                    ↓ normalized to
https://bbc.com/article
```

### Layer 2 — Content Hash Deduplication

After scraping, a **SHA-256 fingerprint** of the article content is generated. If two articles from different URLs have identical content (syndicated articles), only one is stored.

```
Article Content  →  SHA-256 Hash  →  "a3f9c2d1e8b7..."  →  Check DB  →  Skip if exists
```

---

## 🤖 Step 6 — Google Gemini AI Analysis

**File:** `app/services/gemini_service.py`

This is the intelligence layer of the platform. Each article is sent to **Google Gemini** (`gemini-2.0-flash`) for deep analysis.

### What Gemini Produces

For every article, Gemini returns 4 structured outputs:

| Output | Description | Example |
|---|---|---|
| `summary` | 3–5 sentence factual summary | "Apple announced a new chip..." |
| `key_points` | 3–5 bullet point takeaways | ["Revenue grew 12%", "New AI features added"] |
| `category` | AI-assigned news category | "Artificial Intelligence", "Finance", "Politics" |
| `sentiment` | Emotional tone of the article | `positive`, `negative`, or `neutral` |

### How the Prompt Works

The system sends a carefully crafted prompt to Gemini that:
- Instructs it to act as a **news intelligence analyst**
- Provides the article title and full content
- Explicitly tells it to **ignore any instructions inside the article** (security measure against prompt injection)
- Requests a **strict JSON response** format
- Sets temperature to `0.2` (low creativity, high factual accuracy)

### Reliability — Retry with Exponential Backoff

If Gemini's servers are temporarily unavailable (503 error), the system automatically retries up to **3 times** with increasing delays:

```
Attempt 1 fails  →  Wait ~1 second  →  Retry
Attempt 2 fails  →  Wait ~2 seconds →  Retry
Attempt 3 fails  →  Raise error, log it, continue without AI
```

> If AI analysis fails for an article, the article is **still saved** to the database — just without AI fields. It can be analyzed later using the `/api/news/pipeline/analyze` endpoint.

### Response Validation

Every Gemini response is strictly validated:
- All 4 required fields must be present
- `key_points` must be a list of 3–5 non-empty strings
- `sentiment` must be exactly `positive`, `negative`, or `neutral`
- Any invalid response raises an error and is logged

---

## 🗄️ Step 7 — Database Storage

**File:** `app/database/models.py` + `app/database/repository.py`

All articles and their AI analysis are stored permanently in **PostgreSQL**.

### Database Table: `news_articles`

| Column | Type | Description |
|---|---|---|
| `id` | Integer (PK) | Auto-incremented unique ID |
| `title` | String(500) | Article headline |
| `url` | String(2048) | Unique article URL |
| `source` | String(150) | News source name |
| `description` | Text | RSS short description |
| `content` | Text | Full scraped article text |
| `author` | String(255) | Article author |
| `category` | String(150) | RSS feed category |
| `language` | String(20) | Language code (e.g. `en`) |
| `published_at` | DateTime | Original publication date |
| `fetched_at` | DateTime | When our system collected it |
| `content_hash` | String(64) | SHA-256 hash for deduplication |
| `ai_summary` | Text | Gemini-generated summary |
| `ai_key_points` | JSON | Gemini key takeaways (array) |
| `ai_category` | String(150) | Gemini-assigned category |
| `ai_sentiment` | String(20) | `positive` / `negative` / `neutral` |

### Duplicate Prevention at Database Level

Even if the pipeline sends a duplicate, PostgreSQL uses `ON CONFLICT DO NOTHING` — meaning duplicate URLs or content hashes are **silently ignored** at the database level. No errors, no crashes.

### JSON Backup

Every pipeline run also saves a **timestamped JSON file** to `data/raw/`:
```
data/raw/news_20250115_143022.json
```
This serves as a recovery backup and debugging aid.

---

## 🚀 Step 8 — FastAPI Backend

**File:** `app/main.py` + `app/news/router.py`

The backend is built with **FastAPI** — a modern, high-performance Python web framework. It exposes all data and pipeline controls through a REST API.

### Pipeline Endpoints

| Endpoint | What It Does |
|---|---|
| `GET /api/news/pipeline/run` | Full pipeline: scrape + AI analysis |
| `GET /api/news/pipeline/scrape` | Scrape only — no AI (faster) |
| `GET /api/news/pipeline/analyze` | AI analysis only — on pending articles |

### Data Endpoints

| Endpoint | What It Returns |
|---|---|
| `GET /api/news` | Paginated list of all articles |
| `GET /api/news/{id}` | Single article by ID |
| `GET /api/news/search?q=` | Full-text keyword search |
| `GET /api/news/stats` | Dashboard statistics |
| `GET /api/news/ai/analyzed` | Articles with AI analysis |
| `GET /api/news/ai/pending` | Articles awaiting AI analysis |
| `GET /api/news/ai/sentiment/{sentiment}` | Filter by positive/negative/neutral |
| `GET /api/news/analytics/categories` | Article counts by AI category |
| `GET /api/news/analytics/publishing-trends` | Daily publishing volume |

### Auto-Generated API Documentation

FastAPI automatically generates interactive API documentation at:
```
http://localhost:8000/docs
```

---

## 🖥️ Step 9 — React Dashboard

**Directory:** `frontend/src/`

The frontend is a modern **React 19** single-page application that consumes the FastAPI backend and visualizes everything.

### Pages

| Page | What It Shows |
|---|---|
| 📊 Dashboard | Total articles, AI coverage %, sentiment chart, source breakdown |
| 📰 News | Browsable list of all collected articles with filters |
| 📈 Analytics | Publishing trends over time, category distribution charts |
| 🤖 AI Insights | Deep dive into AI-analyzed articles, key points, categories |

### Tech Stack

| Tool | Purpose |
|---|---|
| React 19 | UI framework |
| TypeScript | Type-safe code |
| Vite | Fast build tool |
| Tailwind CSS | Styling |
| Recharts | Charts and graphs |
| Axios | HTTP requests to FastAPI |
| React Router | Page navigation |

---

## 📊 Three Pipeline Modes

The system supports 3 ways to run the pipeline depending on the need:

### Mode 1 — Full Pipeline
```
GET /api/news/pipeline/run
```
Scrapes new articles AND runs Gemini AI on them in one go. Best for regular scheduled runs.

### Mode 2 — Scrape Only
```
GET /api/news/pipeline/scrape
```
Collects and stores articles without AI analysis. Faster and cheaper (no Gemini API calls). Useful when you want to collect first and analyze later.

### Mode 3 — AI Analysis Only
```
GET /api/news/pipeline/analyze
```
Picks up all articles in the database that don't have AI analysis yet and runs Gemini on them. Useful to backfill AI results or retry failed analyses.

---

## 🛡️ Reliability & Error Handling

The system is designed to **never crash** due to a single article failure:

| Scenario | What Happens |
|---|---|
| Article URL is unreachable | Skipped, error logged, pipeline continues |
| Webpage has no extractable content | Skipped, warning logged |
| Gemini AI fails or times out | Article saved without AI fields, error logged |
| Duplicate article detected | Silently skipped at URL or content hash level |
| Database connection fails | Error returned in API response with details |
| Gemini returns invalid JSON | Validation error raised, logged, article skipped |

All errors are written to `logs/app.log` with timestamps, severity levels, and full context.

---

## 📝 Logging

**File:** `app/main.py`

Every action in the system is logged. Logs are written to two places simultaneously:

| Destination | Details |
|---|---|
| Console (terminal) | Live output while server is running |
| `logs/app.log` | Persistent file, max 5 MB, 3 rotating backups |

### Log Format
```
2025-01-15 14:30:22 [INFO] app.news.pipeline: Starting news collection pipeline
2025-01-15 14:30:25 [INFO] app.news.rss_parser: Collected 20 articles from BBC Technology
2025-01-15 14:30:41 [INFO] app.services.gemini_service: Gemini successfully analyzed article: OpenAI releases GPT-5
2025-01-15 14:30:41 [INFO] app.news.pipeline: Pipeline completed: {'processed_articles': 5, ...}
```

---

## ⚙️ Configuration Reference

All key settings are controlled from two files:

### `.env` — Secrets & Credentials
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ai_news_intelligence
DB_USER=postgres
DB_PASSWORD=your_password
GEMINI_API_KEY=your_gemini_key
GEMINI_MODEL=gemini-2.0-flash
```

### `app/news/config.py` — Pipeline Behaviour
| Setting | Default | Meaning |
|---|---|---|
| `MAX_ARTICLES_PER_RUN` | `5` | Max articles processed per pipeline run |
| `MAX_ARTICLES_PER_FEED` | `20` | Max articles read from each RSS feed |
| `REQUEST_TIMEOUT` | `15s` | HTTP timeout for scraping |
| `REQUEST_DELAY` | `1s` | Pause between scraping requests |

---

## 🔁 Typical Daily Workflow

```
1. Trigger pipeline         →  GET /api/news/pipeline/run
2. System fetches RSS       →  Reads BBC, Hacker News, Google AI Blog
3. Deduplication            →  Skips already-stored articles
4. Scrapes new articles     →  Downloads full webpage content
5. Extracts & cleans text   →  Pure article text ready for AI
6. Gemini analyzes each     →  Summary, key points, category, sentiment
7. Saves to PostgreSQL      →  Permanent storage + JSON backup
8. Dashboard updates        →  React frontend shows new articles & insights
```

---

<div align="center">

*🧠 AI News Intelligence — Collect. Analyze. Understand.*

Built with ❤️ by **Shubhank**

</div>
