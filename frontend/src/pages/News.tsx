
/**
 * Purpose:
 * Displays the All News page with searchable news articles,
 * AI-generated category and sentiment filters, and API-level pagination.
 * Supports both light and dark themes using the global ThemeContext.
 */

import { useCallback, useEffect, useRef, useState } from "react";

import {
  getAICategories,
  getUnifiedNews,
} from "../services/api";

import type { NewsArticleWithAnalysis } from "../types/news";
import { useTheme } from "../context/ThemeContext";
import { useAIModel } from "../context/AIModelContext";

const PAGE_SIZE = 10;

type Sentiment = "positive" | "negative" | "neutral";

export default function News() {
  const { theme } = useTheme();
  const isDark = theme === "dark";
  const { aiProvider } = useAIModel();
  const isGemini = aiProvider === "gemini";
  const providerLabel = isGemini ? "Gemini" : "ShubhAI";

  const [articles, setArticles] = useState<NewsArticleWithAnalysis[]>([]);
  const [total, setTotal] = useState(0);
  const [categories, setCategories] = useState<string[]>([]);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [sentiment, setSentiment] = useState<Sentiment | "">("");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Debounce search input — only fire API after 350ms of no typing
  const searchTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [debouncedSearch, setDebouncedSearch] = useState("");

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

  // Reset filters and reload categories when provider switches
  useEffect(() => {
    setCategory("");
    setSentiment("");
    setSearch("");
    setDebouncedSearch("");
    setPage(1);

    const loader = () => getAICategories(isGemini ? "gemini" : "shubhAI");
    loader()
      .then(setCategories)
      .catch(() => setError("Unable to load AI categories."));
  }, [isGemini]);

  // Debounce search: update debouncedSearch 350ms after user stops typing
  useEffect(() => {
    if (searchTimer.current) clearTimeout(searchTimer.current);
    searchTimer.current = setTimeout(() => {
      setDebouncedSearch(search);
      setPage(1);
    }, 350);
    return () => {
      if (searchTimer.current) clearTimeout(searchTimer.current);
    };
  }, [search]);

  // Fetch articles from unified API whenever filters or page change
  const fetchArticles = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const result = await getUnifiedNews(
        PAGE_SIZE,
        (page - 1) * PAGE_SIZE,
        debouncedSearch || undefined,
        category || undefined,
        sentiment || undefined,
        isGemini ? "gemini" : "shubhAI",
      );
      setArticles(result.items);
      setTotal(result.total);
    } catch {
      setError("Unable to load news articles. Please check the backend.");
      setArticles([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [page, debouncedSearch, category, sentiment, isGemini]);

  useEffect(() => {
    void fetchArticles();
  }, [fetchArticles]);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  function clearFilters() {
    setSearch("");
    setDebouncedSearch("");
    setCategory("");
    setSentiment("");
    setPage(1);
  }

  const pageNumbers = (): (number | "...")[] => {
    if (totalPages <= 7) return Array.from({ length: totalPages }, (_, i) => i + 1);
    const pages: (number | "...")[] = [1];
    if (page > 3) pages.push("...");
    for (let i = Math.max(2, page - 1); i <= Math.min(totalPages - 1, page + 1); i++) pages.push(i);
    if (page < totalPages - 2) pages.push("...");
    pages.push(totalPages);
    return pages;
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className={`text-2xl font-bold ${styles.heading}`}>All News</h1>
        <p className={`mt-1 text-sm ${styles.description}`}>
          Showing{" "}
          <span className="font-semibold text-indigo-500">{providerLabel}</span>{" "}
          analysis — explore, search and filter AI-analyzed news articles.
        </p>
      </div>

      {/* Search and filters */}
      <div className="grid gap-3 md:grid-cols-3">
        <input
          type="text"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Search title, summary or source..."
          className={`w-full rounded-lg border px-4 py-3 text-sm outline-none transition-colors focus:border-indigo-500 ${styles.control}`}
        />

        <select
          value={category}
          onChange={(event) => {
            setCategory(event.target.value);
            setPage(1);
          }}
          className={`w-full rounded-lg border px-4 py-3 text-sm outline-none transition-colors focus:border-indigo-500 ${styles.control}`}
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
          onChange={(event) => {
            setSentiment(event.target.value as Sentiment | "");
            setPage(1);
          }}
          className={`w-full rounded-lg border px-4 py-3 text-sm outline-none transition-colors focus:border-indigo-500 ${styles.control}`}
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
          {loading ? "Loading..." : `${total} articles found`}
        </p>

        <button
          type="button"
          onClick={clearFilters}
          className="text-sm text-indigo-500 transition-colors hover:text-indigo-600"
        >
          Clear filters
        </button>
      </div>

      {loading && (
        <p className={`py-10 text-center text-sm ${styles.muted}`}>
          Loading news articles...
        </p>
      )}

      {!loading && error && (
        <p className="rounded-lg border border-red-300 bg-red-50 p-4 text-red-700">
          {error}
        </p>
      )}

      {!loading && !error && articles.length === 0 && (
        <p className={`rounded-lg border p-8 text-center ${styles.empty}`}>
          No articles found. Try changing your filters.
        </p>
      )}

      {!loading && !error && (
        <div className="space-y-4">
          {articles.map((article) => (
            <article
              key={article.id}
              className={`rounded-xl border px-5 py-5 text-sm shadow-sm transition-colors ${styles.article}`}
            >
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
                    className={`rounded-full px-3 py-1 capitalize ${
                      article.ai_sentiment === "positive"
                        ? "bg-green-500/15 text-green-600"
                        : article.ai_sentiment === "negative"
                          ? "bg-red-500/15 text-red-600"
                          : "bg-slate-500/15 text-slate-500"
                    }`}
                  >
                    {article.ai_sentiment}
                  </span>
                )}

                {article.analysis_status === "failed" ? (
                  <span className="rounded-full bg-red-500/15 px-3 py-1 text-red-600">
                    Failed
                  </span>
                ) : !article.ai_summary ? (
                  <span className="rounded-full bg-amber-500/15 px-3 py-1 text-amber-600">
                    Pending
                  </span>
                ) : null}
              </div>

              <h2 className={`text-lg font-semibold ${styles.articleTitle}`}>
                {article.title}
              </h2>

              {article.published_at && (
                <p className={`mt-2 text-xs ${styles.muted}`}>
                  {new Date(article.published_at).toLocaleString()}
                </p>
              )}

              {article.ai_summary && (
                <p className={`mt-4 text-sm leading-7 ${styles.articleSummary}`}>
                  {article.ai_summary}
                </p>
              )}

              {article.ai_key_points && article.ai_key_points.length > 0 && (
                <ul className={`mt-4 list-disc space-y-2 pl-5 text-sm ${styles.keyPoints}`}>
                  {article.ai_key_points.map((point, index) => (
                    <li key={index}>{point}</li>
                  ))}
                </ul>
              )}

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
        <div className="flex flex-col items-center gap-3 pt-4">
          <p className={`text-sm ${styles.muted}`}>
            Showing {Math.min((page - 1) * PAGE_SIZE + 1, total)}–
            {Math.min(page * PAGE_SIZE, total)} of {total} articles
          </p>

          <div className="flex items-center gap-2">
            <button
              type="button"
              disabled={page === 1}
              onClick={() => setPage((p) => p - 1)}
              className={`rounded-lg border px-4 py-2 text-sm transition-colors disabled:cursor-not-allowed disabled:opacity-40 ${styles.button}`}
            >
              Previous
            </button>

            {pageNumbers().map((item, idx) =>
              item === "..." ? (
                <span key={`ellipsis-${idx}`} className={`px-2 text-sm ${styles.muted}`}>
                  ...
                </span>
              ) : (
                <button
                  key={item}
                  type="button"
                  onClick={() => setPage(item as number)}
                  className={`min-w-[36px] rounded-lg border px-3 py-2 text-sm transition-colors ${
                    page === item
                      ? "border-indigo-600 bg-indigo-600 text-white"
                      : styles.button
                  }`}
                >
                  {item}
                </button>
              )
            )}

            <button
              type="button"
              disabled={page === totalPages}
              onClick={() => setPage((p) => p + 1)}
              className={`rounded-lg border px-4 py-2 text-sm transition-colors disabled:cursor-not-allowed disabled:opacity-40 ${styles.button}`}
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
