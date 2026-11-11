<div align="center">

# 🧠 AI News Intelligence Aggregator

### *Collect. Analyze. Understand.*

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Latest-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Gemini](https://img.shields.io/badge/Google_Gemini-AI-8E75B2?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev)
[![License](https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge)](LICENSE)

<br/>

> An AI-powered news collection, analysis, and visualization platform.
> Fetches articles from RSS feeds, enriches them with **Google Gemini AI**
> (summaries, key points, category, sentiment), stores them in **PostgreSQL**,
> and serves them through a **FastAPI** backend and a **React** dashboard.

</div>

---

## ⚡ Architecture

```
📡 RSS Feeds  →  🔄 Pipeline  →  🤖 Gemini AI  →  🗄️ PostgreSQL  →  🚀 FastAPI  →  🖥️ React Frontend
```

| 🏗️ Layer | 🛠️ Tech |
|---|---|
| 🐍 Backend | Python, FastAPI, SQLAlchemy |
| 🤖 AI Analysis | Google Gemini (`google-genai`) |
| 🗄️ Database | PostgreSQL (`psycopg`) |
| 🎨 Frontend | React 19, TypeScript, Vite, Tailwind CSS, Recharts |

---

## 📁 Project Structure

```
ai-news-intelligence/
├── 📦 app/
│   ├── main.py                   # 🚀 FastAPI app entry point
│   ├── 🗄️ database/
│   │   ├── connection.py         # SQLAlchemy engine & session
│   │   ├── models.py             # NewsArticleModel ORM
│   │   └── repository.py        # DB queries
│   ├── 📰 news/
│   │   ├── feeds.py              # RSS feed sources
│   │   ├── pipeline.py          # Full collection pipeline
│   │   ├── rss_parser.py        # RSS parsing
│   │   ├── scraper.py           # HTML fetching
│   │   ├── extractor.py         # Article text extraction
│   │   ├── cleaner.py           # Text cleaning
│   │   ├── router.py            # API endpoints
│   │   └── schemas.py           # Pydantic schemas
│   └── 🤖 services/
│       └── gemini_service.py    # Gemini AI integration
├── 🎨 frontend/
│   └── src/
│       ├── pages/               # Dashboard, News, Analytics, AIInsights
│       ├── components/          # UI components
│       ├── services/api.ts      # Axios API client
│       └── types/news.ts        # TypeScript types
├── 💾 data/raw/                 # JSON backups of collected articles
├── 🧪 tests/                    # Pytest test suite
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
| 🐘 PostgreSQL | Latest |

### 1️⃣ Clone & Configure

```bash
git clone <repo-url>
cd ai-news-intelligence
cp .env.example .env
```

Edit your `.env` file:

```env
# 🗄️ PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ai_news_intelligence
DB_USER=postgres
DB_PASSWORD=your_password_here

# 🤖 Google Gemini AI
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.0-flash
```

### 2️⃣ Backend

```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

> 🌐 API → `http://localhost:8000`
> 📖 Docs → `http://localhost:8000/docs`

### 3️⃣ Frontend

```bash
cd frontend
npm install
npm run dev
```

> 🎨 Frontend → `http://localhost:5173`

---

## 🔄 Running the News Pipeline

Trigger article collection and AI analysis via the API:

```bash
POST http://localhost:8000/api/news/pipeline/run
```

The pipeline executes these steps in order:

| Step | Action |
|---|---|
| 1️⃣ | 📡 Fetch articles from configured RSS feeds |
| 2️⃣ | 🌐 Scrape and extract full article content |
| 3️⃣ | 🔍 Deduplicate by URL and content hash |
| 4️⃣ | 🤖 Analyze each article with Gemini AI |
| 5️⃣ | 💾 Save to PostgreSQL and JSON backup in `data/raw/` |

---

## 🛣️ API Endpoints

### 📰 Articles

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/news` | List articles (pagination, category filter) |
| `GET` | `/api/news/{id}` | Get article by ID |
| `GET` | `/api/news/search?q=` | Keyword search |
| `GET` | `/api/news/categories` | RSS categories |
| `GET` | `/api/news/stats` | Aggregated statistics |

### 🤖 AI Analysis

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/news/ai/analyzed` | AI-analyzed articles |
| `GET` | `/api/news/ai/pending` | Articles pending AI analysis |
| `GET` | `/api/news/ai/sentiment/{sentiment}` | Filter by sentiment |
| `GET` | `/api/news/ai/categories` | AI-generated categories |
| `GET` | `/api/news/ai/category/{category}` | Filter by AI category |

### 📊 Analytics

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/news/analytics/categories` | Article counts by AI category |
| `GET` | `/api/news/analytics/publishing-trends` | Daily publishing trends |

---

## 📡 RSS Feed Sources

Configured in `app/news/feeds.py`:

| Source | Category |
|---|---|
| 🔴 BBC Technology | Technology |
| 🟠 Hacker News (frontpage) | Technology |
| 🔵 Google AI Blog | Artificial Intelligence |

> ➕ Add more feeds by appending to the `NEWS_FEEDS` list in `app/news/feeds.py`

---

## 🧪 Running Tests

```bash
pytest tests/
```

---

## ⚙️ Key Configuration

| Variable | File | Default |
|---|---|---|
| `MAX_ARTICLES_PER_RUN` | `app/news/config.py` | `5` |
| `MAX_ARTICLES_PER_FEED` | `app/news/config.py` | `20` |
| `REQUEST_TIMEOUT` | `app/news/config.py` | `15s` |
| `GEMINI_MODEL` | `.env` | `gemini-2.0-flash` |

---

## 👨‍💻 Developer

<div align="center">



</div>

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

*🧠 AI News Intelligence — Collect. Analyze. Understand.* - Built with ❤️ by **Shubhank**

</div>
