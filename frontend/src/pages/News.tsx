
/**
 * Purpose:
 * Displays the All News page with searchable news articles,
 * AI-generated category and sentiment filters, and pagination.
 * Supports both light and dark themes using the global ThemeContext.
 */

import { useEffect, useMemo, useState } from "react";

import {
  getAICategories,
  getNewsArticles,
  getNewsByCategory,
  getNewsBySentiment,
} from "../services/api";

import type { NewsArticle } from "../types/news";
import { useTheme } from "../context/ThemeContext";

const PAGE_SIZE = 10;

// Purpose: Restrict sentiment filters to values supported by the backend API.
type Sentiment = "positive" | "negative" | "neutral";

export default function News() {
  const { theme } = useTheme();
  const isDark = theme === "dark";

  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [sentiment, setSentiment] = useState<Sentiment | "">("");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const styles = {
    heading: isDark ? "text-white" : "text-slate-900",
    description: isDark ? "text-slate-400" : "text-slate-500",
    muted: isDark ? "text-slate-400" : "text-slate-500",

    control: isDark
      ? "border-slate-700 bg-slate-900 text-white placeholder:text-slate-400"
      : "border-slate-300 bg-white text-slate-900 placeholder:text-slate-400",

    article: isDark
      ? "border-slate-700 bg-slate-900 text-slate-100"
      : "border-slate-200 bg-white text-slate-900",

    articleTitle: isDark ? "text-white" : "text-slate-900",
    articleSummary: isDark ? "text-slate-300" : "text-slate-700",
    keyPoints: isDark ? "text-slate-400" : "text-slate-600",

    button: isDark
      ? "border-slate-700 text-slate-200 hover:bg-slate-800"
      : "border-slate-300 text-slate-700 hover:bg-slate-100",

    empty: isDark
      ? "border-slate-700 bg-slate-900 text-slate-400"
      : "border-slate-200 bg-white text-slate-500",
  };

  useEffect(() => {
    getAICategories()
      .then(setCategories)
      .catch(() => setError("Unable to load AI categories."));
  }, []);

  useEffect(() => {
    let active = true;

    async function loadArticles() {
      setLoading(true);
      setError("");

      try {
        let result: NewsArticle[];

        if (category) {
          result = await getNewsByCategory(category, 100, 0);
        } else if (sentiment) {
          result = await getNewsBySentiment(sentiment, 100, 0);
        } else {
          result = await getNewsArticles(100, 0);
        }

        if (active) {
          setArticles(result);
          setPage(1);
        }
      } catch {
        if (active) {
          setError("Unable to load news articles. Please check the backend.");
          setArticles([]);
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    loadArticles();

    return () => {
      active = false;
    };
  }, [category, sentiment]);

  const filteredArticles = useMemo(() => {
    const query = search.trim().toLowerCase();

    return articles.filter((article) => {
      const matchesSearch =
        !query ||
        article.title?.toLowerCase().includes(query) ||
        article.ai_summary?.toLowerCase().includes(query) ||
        article.source?.toLowerCase().includes(query);

      const matchesSentiment =
        !sentiment || article.ai_sentiment === sentiment;

      return matchesSearch && matchesSentiment;
    });
  }, [articles, search, sentiment]);

  const totalPages = Math.max(
    1,
    Math.ceil(filteredArticles.length / PAGE_SIZE)
  );

  const currentArticles = filteredArticles.slice(
    (page - 1) * PAGE_SIZE,
    page * PAGE_SIZE
  );

  function clearFilters() {
    setSearch("");
    setCategory("");
    setSentiment("");
    setPage(1);
  }

  return (
    <div className="space-y-6">
      {/* Page heading */}
      <div>
        <h1 className={`text-2xl font-bold ${styles.heading}`}>
          All News
        </h1>

        <p className={`mt-1 text-sm ${styles.description}`}>
          Explore, search and filter AI-analyzed news articles.
        </p>
      </div>

      {/* Search and filters */}
      <div className="grid gap-3 md:grid-cols-3">
        <input
          type="text"
          value={search}
          onChange={(event) => {
            setSearch(event.target.value);
            setPage(1);
          }}
          placeholder="Search title, summary or source..."
          className={`w-full rounded-lg border px-4 py-3 text-sm outline-none transition-colors focus:border-blue-500 ${styles.control}`}
        />

        <select
          value={category}
          onChange={(event) => setCategory(event.target.value)}
          className={`w-full rounded-lg border px-4 py-3 text-sm outline-none transition-colors focus:border-blue-500 ${styles.control}`}
        >
          <option value="">All AI Categories</option>

          {categories.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>

        <select
          value={sentiment}
          onChange={(event) =>
            setSentiment(event.target.value as Sentiment | "")
          }
          className={`w-full rounded-lg border px-4 py-3 text-sm outline-none transition-colors focus:border-blue-500 ${styles.control}`}
        >
          <option value="">All Sentiments</option>
          <option value="positive">Positive</option>
          <option value="negative">Negative</option>
          <option value="neutral">Neutral</option>
        </select>
      </div>

      {/* Results count and clear filters */}
      <div className="flex items-center justify-between">
        <p className={`text-sm ${styles.muted}`}>
          {filteredArticles.length} articles found
        </p>

        <button
          type="button"
          onClick={clearFilters}
          className="text-sm text-blue-500 transition-colors hover:text-blue-600"
        >
          Clear filters
        </button>
      </div>

      {/* Loading state */}
      {loading && (
        <p className={`py-10 text-center text-sm ${styles.muted}`}>
          Loading news articles...
        </p>
      )}

      {/* Error state */}
      {!loading && error && (
        <p className="rounded-lg border border-red-300 bg-red-50 p-4 text-red-700">
          {error}
        </p>
      )}

      {/* Empty state */}
      {!loading && !error && currentArticles.length === 0 && (
        <p className={`rounded-lg border p-8 text-center ${styles.empty}`}>
          No articles found. Try changing your filters.
        </p>
      )}

      {/* News articles */}
      {!loading && !error && (
        <div className="space-y-4">
          {currentArticles.map((article) => (
            <article
              key={article.id}
              className={`rounded-xl border px-5 py-5 text-sm shadow-sm transition-colors ${styles.article}`}
            >
              {/* Source and AI labels */}
              <div className="mb-3 flex flex-wrap items-center gap-2 text-xs">
                <span className={styles.muted}>
                  {article.source || "Unknown source"}
                </span>

                {article.ai_category && (
                  <span className="rounded-full bg-blue-500/15 px-3 py-1 text-blue-500">
                    {article.ai_category}
                  </span>
                )}

                {article.ai_sentiment && (
                  <span
                    className={`rounded-full px-3 py-1 capitalize ${article.ai_sentiment === "positive"
                      ? "bg-green-500/15 text-green-600"
                      : article.ai_sentiment === "negative"
                        ? "bg-red-500/15 text-red-600"
                        : "bg-slate-500/15 text-slate-500"
                      }`}
                  >
                    {article.ai_sentiment}
                  </span>
                )}
              </div>

              {/* Article title */}
              <h2 className={`text-lg font-semibold ${styles.articleTitle}`}>
                {article.title}
              </h2>

              {/* Published date */}
              {article.published_at && (
                <p className={`mt-2 text-xs ${styles.muted}`}>
                  {new Date(article.published_at).toLocaleString()}
                </p>
              )}

              {/* AI summary */}
              {article.ai_summary && (
                <p className={`mt-4 text-sm leading-7 ${styles.articleSummary}`}>
                  {article.ai_summary}
                </p>
              )}

              {/* AI key points */}
              {article.ai_key_points &&
                article.ai_key_points.length > 0 && (
                  <ul
                    className={`mt-4 list-disc space-y-2 pl-5 text-sm ${styles.keyPoints}`}
                  >
                    {article.ai_key_points.map((point, index) => (
                      <li key={index}>{point}</li>
                    ))}
                  </ul>
                )}

              {/* Original article link */}
              {article.url && (
                <a
                  href={article.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-4 inline-block text-sm font-medium text-blue-500 transition-colors hover:text-blue-600"
                >
                  Read original article →
                </a>
              )}
            </article>
          ))}
        </div>
      )}

      {/* Pagination */}
      {!loading && !error && totalPages > 1 && (
        <div className="flex items-center justify-center gap-4 pt-4">
          <button
            type="button"
            disabled={page === 1}
            onClick={() => setPage((current) => current - 1)}
            className={`rounded-lg border px-4 py-2 text-sm transition-colors disabled:cursor-not-allowed disabled:opacity-40 ${styles.button}`}
          >
            Previous
          </button>

          <span className={`text-sm ${styles.muted}`}>
            Page {page} of {totalPages}
          </span>

          <button
            type="button"
            disabled={page === totalPages}
            onClick={() => setPage((current) => current + 1)}
            className={`rounded-lg border px-4 py-2 text-sm transition-colors disabled:cursor-not-allowed disabled:opacity-40 ${styles.button}`}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
