<div align="center">

# 🧠 AI News Intelligence Aggregator

### *Collect. Analyze. Understand.*

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon_Cloud-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://neon.tech)
[![Gemini](https://img.shields.io/badge/Google_Gemini-AI-8E75B2?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev)
[![Ollama](https://img.shields.io/badge/Ollama-ShubhAI-FF6B35?style=for-the-badge)](https://ollama.com)
[![License](https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge)](LICENSE)

<br/>

> An AI-powered news collection, analysis, and visualization platform.
> Fetches articles from RSS feeds, enriches them with **Google Gemini** and a
> local **ShubhAI (Ollama/Qwen3)** model — summaries, key points, categories,
> sentiment — stores everything in **Neon PostgreSQL**, and serves it through
> a **FastAPI** backend and a **React** dashboard with a global AI model selector.

</div>

---

## ⚡ Architecture

```
📡 RSS Feeds
    └─► 🔄 Scraping Pipeline ──► 🗄️ news_articles (PostgreSQL / Neon)
                                        │
                          ┌─────────────┴─────────────┐
                          ▼                           ▼
                  🤖 Gemini Scheduler         🤖 ShubhAI Scheduler
                  (every 5 min)               (every 5 min, Ollama)
                          │                           │
                          └─────────────┬─────────────┘
                                        ▼
                          🗄️ article_ai_analyses
                          (ai_model = 'gemini' | 'shubhAI')
                                        │
                                        ▼
                          🚀 FastAPI  ──►  🖥️ React Dashboard
```

| 🏗️ Layer | 🛠️ Tech |
|---|---|
| 🐍 Backend | Python 3.11+, FastAPI 0.116, SQLAlchemy 2 |
| 🤖 Gemini AI | Google Gemini (`google-genai`), cloud API |
| 🤖 ShubhAI | Ollama + Qwen3:4b, runs locally via Docker |
| 🗄️ Database | Neon Cloud PostgreSQL (`psycopg`) |
| 🎨 Frontend | React 19, TypeScript, Vite, Tailwind CSS, Recharts |
| 🐳 Deployment | Docker Compose (backend + frontend + nginx) |

---

## 🗄️ Database Schema

Two clean, purpose-separated tables.

### `news_articles` — scraped content only

| Column | Type | Notes |
|---|---|---|
| `id` | SERIAL PK | |
| `title` | VARCHAR(500) | NOT NULL |
| `url` | VARCHAR(2048) | UNIQUE |
| `source` | VARCHAR(150) | Indexed |
| `description` | TEXT | |
| `content` | TEXT | Full extracted article text |
| `author` | VARCHAR(255) | |
| `category` | VARCHAR(150) | RSS feed category, indexed |
| `language` | VARCHAR(20) | Default `en` |
| `published_at` | TIMESTAMPTZ | Indexed |
| `fetched_at` | TIMESTAMPTZ | NOT NULL |
| `content_hash` | VARCHAR(64) | UNIQUE — deduplication |
| `created_at` | TIMESTAMPTZ | Auto-set |
| `updated_at` | TIMESTAMPTZ | Auto-updated |

### `article_ai_analyses` — unified AI analysis

| Column | Type | Notes |
|---|---|---|
| `id` | SERIAL PK | |
| `article_id` | INTEGER | FK → `news_articles.id` ON DELETE RESTRICT |
| `ai_model` | VARCHAR(20) | `'gemini'` or `'shubhAI'` — CHECK constraint |
| `summary` | TEXT | |
| `key_points` | JSONB | Array of strings |
| `category` | VARCHAR(150) | AI-assigned category |
| `sentiment` | VARCHAR(20) | `positive`, `negative`, `neutral` — CHECK constraint |
| `status` | VARCHAR(20) | `pending`, `completed`, `failed` — CHECK constraint |
| `attempt_count` | INTEGER | Retry counter |
| `error_message` | TEXT | Failure details |
| `analyzed_at` | TIMESTAMPTZ | |
| `created_at` | TIMESTAMPTZ | Auto-set |
| `updated_at` | TIMESTAMPTZ | Auto-updated |

**Key constraints:**
- `UNIQUE (article_id, ai_model)` — one analysis record per article per model
- `CHECK (ai_model IN ('gemini', 'shubhAI'))` — no invalid model names
- `ON DELETE RESTRICT` — articles cannot be deleted while analysis exists
- Indexes on `article_id`, `ai_model`, `status`, `sentiment`

---

## 📁 Project Structure

```
ai-news-intelligence/
├── 📦 app/
│   ├── main.py                    # FastAPI app, CORS, dual AI schedulers
│   ├── 🗄️ database/
│   │   ├── connection.py          # SQLAlchemy engine & session (Neon)
│   │   ├── models.py              # NewsArticleModel + ArticleAIAnalysis ORM
│   │   └── repository.py         # All DB queries, unified by ai_model param
│   ├── 📰 news/
│   │   ├── feeds.py               # RSS feed sources
│   │   ├── pipeline.py            # Scraping + Gemini analysis pipelines
│   │   ├── rss_parser.py          # RSS parsing
│   │   ├── scraper.py             # HTML fetching
│   │   ├── extractor.py           # Article text extraction
│   │   ├── cleaner.py             # Text cleaning
│   │   ├── router.py              # News API endpoints
│   │   ├── schemas.py             # Pydantic schemas
│   │   └── config.py              # Pipeline configuration
│   ├── 🤖 ollama/
│   │   ├── processor.py           # ShubhAI batch analysis runner
│   │   ├── repository.py          # ShubhAI DB operations (delegates to unified repo)
│   │   └── router.py              # ShubhAI API endpoints
│   └── 🔧 services/
│       ├── gemini_service.py      # Google Gemini API integration
│       └── ollama_service.py      # Local Ollama/Qwen3 integration
├── 🎨 frontend/
│   └── src/
│       ├── context/
│       │   ├── AIModelContext.tsx  # Global AI model selector (gemini | shubhAI)
│       │   └── ThemeContext.tsx    # Light/dark theme
│       ├── pages/
│       │   ├── Dashboard.tsx       # Live stats, sentiment chart, sources
│       │   ├── News.tsx            # All News — API-level pagination + filters
│       │   ├── Analytics.tsx       # Charts — categories, sentiment, trends
│       │   └── AIInsights.tsx      # AI analysis dashboard per model
│       ├── components/
│       │   ├── OllamaInsights.tsx  # ShubhAI insights panel
│       │   ├── layout/Sidebar.tsx  # Navigation + AI model selector
│       │   └── dashboard/          # StatCard, SentimentChart
│       ├── services/api.ts         # Axios API client — all calls pass ai_model
│       └── types/news.ts           # TypeScript interfaces
├── 💾 data/raw/                    # JSON backups of scraped articles
├── 🧪 tests/                       # 44 pytest tests
│   ├── test_database_repository.py # 15 unified schema integration tests
│   ├── test_pipeline.py
│   ├── test_ollama_service.py
│   ├── test_cleaner.py
│   ├── test_extractor.py
│   └── test_rss_parser.py
├── logs/                           # Rotating log files (app.log)
├── docker-compose.yml
├── Dockerfile
├── init_db.py                      # Creates both tables in PostgreSQL
├── .env.example
└── requirements.txt
```

---

## 🚀 Setup

### ✅ Prerequisites

| Requirement | Version |
|---|---|
| 🐍 Python | 3.11+ |
| 🟢 Node.js | 18+ |
| 🐳 Docker | Latest (for ShubhAI / deployment) |
| 🐘 PostgreSQL | Neon Cloud or local |

### 1️⃣ Clone & Configure

```bash
git clone <repo-url>
cd ai-news-intelligence
cp .env.example .env
```

Edit `.env`:

```env
# PostgreSQL (Neon Cloud or local)
DB_HOST=your-neon-host.neon.tech
DB_PORT=5432
DB_NAME=ai_news_intelligence
DB_USER=your_user
DB_PASSWORD=your_password
DB_SSLMODE=require          # remove for local PostgreSQL

# Google Gemini AI
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.0-flash

# ShubhAI (Ollama — local or Docker)
OLLAMA_BASE_URL=http://host.docker.internal:11434  # Docker backend -> Ollama on Windows host
OLLAMA_MODEL=qwen3:4b
OLLAMA_TIMEOUT=120
```

### 2️⃣ Backend

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

### 3️⃣ Database Setup

For local PostgreSQL, create the database first:

```sql
CREATE DATABASE ai_news_intelligence;
```

Then create both tables:

```bash
python init_db.py
```

Expected output:
```
Testing database connection...
Connection successful.
Creating tables...
Done. Tables created:
  + news_articles
  + article_ai_analyses
```

> `init_db.py` / SQLAlchemy `create_all()` creates missing tables only; it does not alter existing columns or constraints. Use a versioned Alembic migration for schema changes. Back up the Neon database before applying migrations.

### 4️⃣ ShubhAI (Ollama) — optional

Pull and run the Qwen3 model locally:

```bash
ollama pull qwen3:4b
ollama serve
```

Or via Docker (already configured in `docker-compose.yml`):

```bash
docker compose up -d
```

### 5️⃣ Start the Backend

```bash
uvicorn app.main:app --reload
```

> API → `http://localhost:8000`
> Docs → `http://localhost:8000/docs`

### 6️⃣ Frontend

```bash
cd frontend
npm install
npm run dev
```

> Frontend → `http://localhost:5173`

---

## 🐳 Docker Deployment

Build and run the full stack:

```bash
docker compose up -d --build
```

Build only the frontend:

```bash
docker compose up -d --build frontend
```

---

## 🔄 News Pipeline

### Scraping only (no AI)

```
GET /api/news/pipeline/scrape
```

| Step | Action |
|---|---|
| 1 | Fetch articles from RSS feeds |
| 2 | Scrape and extract full article content |
| 3 | Deduplicate by URL and content hash |
| 4 | Save to `news_articles` and JSON backup in `data/raw/` |

### Gemini analysis only

```
GET /api/news/pipeline/analyze
```

Runs Gemini on all articles pending for `ai_model='gemini'`. Saves results to `article_ai_analyses`.

### Full pipeline (scrape + Gemini analysis)

```
GET /api/news/pipeline/run
```

### Automatic schedulers

Both AI schedulers run automatically every 5 minutes when the backend starts:

| Scheduler | Model | Trigger |
|---|---|---|
| Gemini scheduler | `gemini` | Every 5 min, processes up to 5 pending articles |
| ShubhAI scheduler | `shubhAI` | Every 5 min, processes up to 5 pending articles |

Schedulers are independent — Gemini pending and ShubhAI pending are calculated separately per model.

---

## 🛣️ API Endpoints

### 📰 Articles

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/news` | Paginated article list (`limit`, `offset`, `category`) |
| `GET` | `/api/news/{id}` | Article by ID |
| `GET` | `/api/news/search?q=` | Keyword search across title, description, content |
| `GET` | `/api/news/categories` | RSS feed categories |
| `GET` | `/api/news/stats?ai_model=` | Dashboard statistics scoped to AI model |

### 🔍 Unified All-News Endpoint

```
GET /api/news/unified
```

All filters applied at the database level before pagination. Returns `{total, limit, offset, items}`.

| Parameter | Type | Description |
|---|---|---|
| `limit` | int | Records per page (default 10, max 100) |
| `offset` | int | Records to skip |
| `search` | string | Keyword search |
| `ai_category` | string | Filter by AI-assigned category |
| `ai_sentiment` | string | `positive`, `negative`, `neutral` |
| `ai_model` | string | `gemini` or `shubhAI` |

Example:
```
GET /api/news/unified?ai_model=shubhAI&ai_sentiment=positive&limit=10&offset=0
GET /api/news/unified?ai_model=gemini&ai_category=Technology&limit=10&offset=20
```

### 🤖 AI Analysis (scoped by `ai_model`)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/news/ai/analyzed?ai_model=` | Analyzed articles for model |
| `GET` | `/api/news/ai/analyzed/count?ai_model=` | Count of analyzed articles |
| `GET` | `/api/news/ai/pending?ai_model=` | Pending articles for model |
| `GET` | `/api/news/ai/categories?ai_model=` | AI-assigned categories for model |

### 📊 Analytics

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/news/analytics/categories?ai_model=` | Article counts by AI category |
| `GET` | `/api/news/analytics/publishing-trends` | Daily publishing counts (optional `date_from`, `date_to`) |

### 🤖 ShubhAI Endpoints (`/api/ollama/`)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/ollama/analyses` | Completed ShubhAI analyses (`limit`, `offset`, `category`, `sentiment`) |
| `GET` | `/api/ollama/analyses/{article_id}` | ShubhAI analysis for one article |
| `GET` | `/api/ollama/pending` | Articles pending ShubhAI analysis |
| `GET` | `/api/ollama/categories` | ShubhAI-assigned categories |
| `GET` | `/api/ollama/analytics/categories` | Article counts by ShubhAI category |
| `GET` | `/api/ollama/status` | ShubhAI coverage, counts, sentiment distribution |

### 🔧 Pipeline Triggers

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/news/pipeline/run` | Full pipeline (scrape + Gemini analysis) |
| `GET` | `/api/news/pipeline/scrape` | Scrape only |
| `GET` | `/api/news/pipeline/analyze` | Gemini analysis only |

---

## 🖥️ Frontend Features

### Global AI Model Selector

The sidebar contains a persistent AI model toggle (stored in `localStorage`):

- **Gemini** — shows Google Gemini analysis across all pages
- **ShubhAI** — shows local Ollama/Qwen3 analysis across all pages

Switching models reloads all data for the selected model. The two models' data are never mixed.

### Pages

| Page | Features |
|---|---|
| **Dashboard** | Total articles, analyzed/pending counts, AI coverage %, sentiment pie chart, articles by source — all scoped to selected AI model |
| **All News** | API-level pagination (10/page), debounced search, AI category dropdown, sentiment dropdown, "Showing X–Y of Z" display — all filters applied server-side |
| **Analytics** | Articles by source bar chart, AI category bar chart, sentiment pie chart, daily publishing trend line chart with date filters — all scoped to selected AI model |
| **AI Insights** | Analyzed/Pending tabs with API-level pagination, coverage progress bar, sentiment distribution chart — separate implementations for Gemini and ShubhAI |

### Pagination

All paginated views use API-level `limit`/`offset` — no client-side slicing. Every page change fetches only the required records from the database.

---

## 📡 RSS Feed Sources

Configured in `app/news/feeds.py`:

| Source | Category |
|---|---|
| BBC Technology | Technology |
| Hacker News (frontpage) | Technology |
| Google AI Blog | Artificial Intelligence |

Add more feeds by appending to `NEWS_FEEDS` in `app/news/feeds.py`.

---

## 🧪 Running Tests

```bash
pytest tests/
```

Skip manual tests that require live API keys:

```bash
pytest tests/ --ignore=tests/test_gemini_models_manual.py --ignore=tests/test_gemini_service_manual.py
```

### Test coverage (44 tests)

| File | Tests | Coverage |
|---|---|---|
| `test_database_repository.py` | 15 | Unified schema: article CRUD, both AI models, unique constraint, independent pending, sentiment/category filtering, pagination, cross-model isolation |
| `test_pipeline.py` | 10 | URL normalization, content hashing, article processing, JSON backup, pipeline orchestration |
| `test_ollama_service.py` | 6 | ShubhAI response validation |
| `test_cleaner.py` | 4 | Text cleaning |
| `test_extractor.py` | 4 | Article extraction |
| `test_rss_parser.py` | 5 | RSS parsing |

---

## ⚙️ Key Configuration

| Variable | File | Default |
|---|---|---|
| `MAX_ARTICLES_PER_RUN` | `app/news/config.py` | `5` |
| `MAX_ARTICLES_PER_FEED` | `app/news/config.py` | `20` |
| `REQUEST_TIMEOUT` | `app/news/config.py` | `15s` |
| `GEMINI_MODEL` | `.env` | `gemini-2.0-flash` |
| `OLLAMA_MODEL` | `.env` | `qwen3:4b` |
| `OLLAMA_TIMEOUT` | `.env` | `120s` |
| `OLLAMA_SCHEDULER_INTERVAL` | `app/main.py` | `300s` |
| `GEMINI_SCHEDULER_INTERVAL` | `app/main.py` | `300s` |

---

## 📄 License

This project is licensed under the **MIT License**.

```
MIT License

Copyright (c) 2025 Shubhank

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

<div align="center">

*🧠 AI News Intelligence — Collect. Analyze. Understand.* — Built with ❤️ by **Shubhank**

</div>
