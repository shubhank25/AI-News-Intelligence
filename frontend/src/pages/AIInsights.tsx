
/**
 * Purpose:
 * Displays AI analysis metrics, sentiment distribution,
 * analysis coverage, and analyzed or pending news articles.
 * Uses ThemeContext for consistent light and dark theme styling.
 */

import { useCallback, useEffect, useState } from "react";
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
} from "recharts";

import {
  getNewsStatistics,
  getAIAnalyzedArticles,
  getAIPendingArticles,
} from "../services/api";

import type {
  NewsArticleWithAnalysis,
  NewsStatistics,
} from "../types/news";

import { useTheme } from "../context/ThemeContext";
import OllamaInsights from "../components/OllamaInsights";
import { useAIModel } from "../context/AIModelContext";

type ArticleTab = "analyzed" | "pending";

const SENTIMENT_COLORS: Record<string, string> = {
  positive: "#22c55e",
  negative: "#ef4444",
  neutral: "#94a3b8",
};

function GeminiInsights() {
  const { theme } = useTheme();
  const isDark = theme === "dark";

  const [statistics, setStatistics] = useState<NewsStatistics | null>(null);
  const [analyzedArticles, setAnalyzedArticles] = useState<NewsArticleWithAnalysis[]>([]);
  const [pendingArticles, setPendingArticles] = useState<NewsArticleWithAnalysis[]>([]);
  const [activeTab, setActiveTab] = useState<ArticleTab>("analyzed");
  const [analyzedPage, setAnalyzedPage] = useState(1);
  const [pendingPage, setPendingPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [articlesLoading, setArticlesLoading] = useState(false);
  const [error, setError] = useState("");
  const [refreshing, setRefreshing] = useState(false);

  const PAGE_SIZE = 10;

  const colors = {
    heading: isDark ? "text-white" : "text-slate-900",
    text: isDark ? "text-slate-400" : "text-slate-500",
    body: isDark ? "text-slate-300" : "text-slate-600",
    panel: isDark
      ? "border-slate-800 bg-slate-900"
      : "border-slate-200 bg-white",
    article: isDark
      ? "border-slate-800 bg-slate-950/50 hover:border-slate-700"
      : "border-slate-200 bg-slate-50 hover:border-slate-300",
    inactiveTab: isDark
      ? "bg-slate-800 text-slate-300 hover:bg-slate-700"
      : "bg-slate-100 text-slate-600 hover:bg-slate-200",
  };

  const loadArticles = useCallback(async (tab: ArticleTab, page: number) => {
    setArticlesLoading(true);
    try {
      const offset = (page - 1) * PAGE_SIZE;
      if (tab === "analyzed") {
        setAnalyzedArticles(await getAIAnalyzedArticles("gemini", PAGE_SIZE, offset) as NewsArticleWithAnalysis[]);
      } else {
        setPendingArticles(await getAIPendingArticles("gemini", PAGE_SIZE, offset) as NewsArticleWithAnalysis[]);
      }
    } catch (err) {
      console.error("Failed to load articles:", err);
    } finally {
      setArticlesLoading(false);
    }
  }, [PAGE_SIZE]);

  const loadDashboard = useCallback(async () => {
    try {
      setRefreshing(true);
      setError("");
      const [stats, analyzed, pending] = await Promise.all([
        getNewsStatistics("gemini"),
        getAIAnalyzedArticles("gemini", PAGE_SIZE, 0),
        getAIPendingArticles("gemini", PAGE_SIZE, 0),
      ]);
      setStatistics(stats);
      setAnalyzedArticles(analyzed as NewsArticleWithAnalysis[]);
      setPendingArticles(pending as NewsArticleWithAnalysis[]);
      setAnalyzedPage(1);
      setPendingPage(1);
    } catch (err) {
      console.error("AI Insights loading failed:", err);
      setError("Unable to load AI insights. Please check the backend APIs.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [PAGE_SIZE]);

  useEffect(() => { void loadDashboard(); }, [loadDashboard]);

  useEffect(() => {
    if (activeTab === "analyzed" && analyzedPage > 1) void loadArticles("analyzed", analyzedPage);
  }, [analyzedPage, activeTab, loadArticles]);

  useEffect(() => {
    if (activeTab === "pending" && pendingPage > 1) void loadArticles("pending", pendingPage);
  }, [pendingPage, activeTab, loadArticles]);
  if (loading) {
    return (
      <div className={`py-16 text-center ${colors.text}`}>
        Loading AI insights...
      </div>
    );
  }

  if (error || !statistics) {
    return (
      <div
        className={`rounded-xl border p-5 ${isDark
          ? "border-red-900 bg-red-950/30 text-red-300"
          : "border-red-200 bg-red-50 text-red-700"
          }`}
      >
        {error || "Statistics are unavailable."}
      </div>
    );
  }

  const aiStats = statistics.ai_analysis;
  const sentiment = aiStats.sentiment_distribution;

  const sentimentData = [
    { name: "Positive", value: sentiment.positive },
    { name: "Negative", value: sentiment.negative },
    { name: "Neutral", value: sentiment.neutral },
  ].filter((item) => item.value > 0);

  const coverage = Math.min(
    100,
    Math.max(0, aiStats.coverage_percentage)
  );

  const visibleArticles = activeTab === "analyzed" ? analyzedArticles : pendingArticles;
  const currentPage = activeTab === "analyzed" ? analyzedPage : pendingPage;
  const total = activeTab === "analyzed" ? aiStats.analyzed_articles : aiStats.pending_articles;
  const totalPages = Math.ceil(total / PAGE_SIZE);

  const handleTabSwitch = (tab: ArticleTab) => {
    setActiveTab(tab);
    const page = tab === "analyzed" ? analyzedPage : pendingPage;
    void loadArticles(tab, page);
  };

  const handlePageChange = (page: number) => {
    if (activeTab === "analyzed") setAnalyzedPage(page);
    else setPendingPage(page);
    void loadArticles(activeTab, page);
  };

  const pageNumbers = (): (number | "...")[] => {
    if (totalPages <= 7) return Array.from({ length: totalPages }, (_, i) => i + 1);
    const pages: (number | "...")[] = [1];
    if (currentPage > 3) pages.push("...");
    for (let i = Math.max(2, currentPage - 1); i <= Math.min(totalPages - 1, currentPage + 1); i++) pages.push(i);
    if (currentPage < totalPages - 2) pages.push("...");
    pages.push(totalPages);
    return pages;
  };

  const tooltipStyle = {
    backgroundColor: isDark ? "#0f172a" : "#ffffff",
    border: `1px solid ${isDark ? "#334155" : "#e2e8f0"}`,
    borderRadius: "10px",
    color: isDark ? "#f8fafc" : "#0f172a",
  };

  return (
    <div className="space-y-6">
      {/* Page heading */}
      <div>
        <h1 className={`text-2xl font-bold ${colors.heading}`}>
          AI Insights
        </h1>

        <p className={`mt-1 text-sm ${colors.text}`}>
          Monitor AI-powered news analysis and sentiment across your articles.
        </p>
      </div>

      {/* AI analysis statistics */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          title="Total Articles"
          value={statistics.total_articles}
          description="Articles in database"
          isDark={isDark}
        />

        <StatCard
          title="AI Analyzed"
          value={aiStats.analyzed_articles}
          description="Successfully analyzed"
          isDark={isDark}
        />

        <StatCard
          title="Pending Analysis"
          value={aiStats.pending_articles}
          description="Waiting for AI processing"
          isDark={isDark}
        />

        <StatCard
          title="AI Coverage"
          value={`${coverage.toFixed(1)}%`}
          description="Overall analysis coverage"
          isDark={isDark}
        />
      </div>

      {/* Coverage and sentiment */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* AI Analysis Coverage */}
        <section
          className={`rounded-xl border p-6 shadow-sm transition-colors ${colors.panel}`}
        >
          <h2 className={`text-lg font-semibold ${colors.heading}`}>
            AI Analysis Coverage
          </h2>

          <div className="mt-6 flex items-end justify-between gap-3">
            <span className={`text-3xl font-bold ${colors.heading}`}>
              {coverage.toFixed(1)}%
            </span>

            <span className={`text-sm ${colors.text}`}>
              {aiStats.analyzed_articles} of {statistics.total_articles} articles
            </span>
          </div>

          <div
            className={`mt-4 h-3 overflow-hidden rounded-full ${isDark ? "bg-slate-700" : "bg-slate-200"
              }`}
          >
            <div
              className="h-full rounded-full bg-blue-600 transition-all duration-500"
              style={{ width: `${coverage}%` }}
            />
          </div>

          <p className={`mt-4 text-sm leading-6 ${colors.body}`}>
            This represents the percentage of stored articles that have an
            AI-generated summary.
          </p>
        </section>

        {/* Sentiment Distribution */}
        <section
          className={`rounded-xl border p-6 shadow-sm transition-colors ${colors.panel}`}
        >
          <h2 className={`text-lg font-semibold ${colors.heading}`}>
            Sentiment Distribution
          </h2>

          {sentimentData.length > 0 ? (
            <div className="mt-4 h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={sentimentData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={85}
                    innerRadius={48}
                    paddingAngle={3}
                  >
                    {sentimentData.map((entry) => (
                      <Cell
                        key={entry.name}
                        fill={SENTIMENT_COLORS[entry.name.toLowerCase()]}
                      />
                    ))}
                  </Pie>

                  <Tooltip
                    contentStyle={tooltipStyle}
                    itemStyle={{
                      color: isDark ? "#f8fafc" : "#0f172a",
                    }}
                    labelStyle={{
                      color: isDark ? "#f8fafc" : "#0f172a",
                    }}
                  />

                  <Legend
                    wrapperStyle={{
                      color: isDark ? "#f8fafc" : "#0f172a",
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p className={`py-16 text-center text-sm ${colors.text}`}>
              No sentiment data available yet.
            </p>
          )}
        </section>
      </div>

      {/* Article tabs */}
      <section
        className={`rounded-xl border p-5 shadow-sm transition-colors ${colors.panel}`}
      >
        <div className="flex flex-wrap items-center justify-between gap-4">
          <h2 className={`text-lg font-semibold ${colors.heading}`}>
            AI Article Analysis
          </h2>

          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={() => void loadDashboard()}
              disabled={refreshing}
              className={`rounded-lg border px-4 py-2 text-sm font-medium transition-colors ${isDark
                ? "border-slate-700 text-blue-400 hover:bg-slate-800"
                : "border-slate-300 text-blue-600 hover:bg-slate-100"
                } disabled:cursor-not-allowed disabled:opacity-60`}
            >
              {refreshing ? "Refreshing..." : "↻ Refresh"}
            </button>

            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => handleTabSwitch("analyzed")}
                className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${activeTab === "analyzed"
                  ? "bg-blue-600 text-white"
                  : colors.inactiveTab
                  }`}
              >
                Analyzed ({aiStats.analyzed_articles})
              </button>

              <button
                type="button"
                onClick={() => handleTabSwitch("pending")}
                className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${activeTab === "pending"
                  ? "bg-blue-600 text-white"
                  : colors.inactiveTab
                  }`}
              >
                Pending ({aiStats.pending_articles})
              </button>
            </div>
          </div>
        </div>

        {articlesLoading && (
          <p className={`mt-4 py-4 text-center text-sm ${colors.text}`}>Loading...</p>
        )}

        <div className="mt-5 space-y-4">
          {!articlesLoading && visibleArticles.length === 0 && (
            <p className={`py-8 text-center text-sm ${colors.text}`}>
              No {activeTab} articles found.
            </p>
          )}

          {visibleArticles.map((article) => (
            <article
              key={article.id}
              className={`rounded-lg border p-4 transition-colors ${colors.article}`}
            >
              <div className="flex flex-wrap items-center gap-2">
                {article.source && (
                  <span className={`text-xs ${colors.text}`}>
                    {article.source}
                  </span>
                )}

                {article.ai_category && (
                  <span
                    className={`rounded-full px-3 py-1 text-xs font-medium ${isDark
                      ? "bg-blue-500/15 text-blue-300"
                      : "bg-blue-100 text-blue-700"
                      }`}
                  >
                    {article.ai_category}
                  </span>
                )}

                {article.ai_sentiment && (
                  <span
                    className={`rounded-full px-3 py-1 text-xs capitalize ${isDark
                      ? "bg-slate-700 text-slate-200"
                      : "bg-slate-200 text-slate-700"
                      }`}
                  >
                    {article.ai_sentiment}
                  </span>
                )}
              </div>

              <h3 className={`mt-3 font-semibold ${colors.heading}`}>
                {article.title}
              </h3>

              {article.ai_summary && (
                <p className={`mt-2 text-sm leading-6 ${colors.body}`}>
                  {article.ai_summary}
                </p>
              )}

              {article.ai_key_points && article.ai_key_points.length > 0 && (
                <ul className={`mt-3 list-disc space-y-1 pl-5 text-sm ${colors.body}`}>
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
                  className={`mt-3 inline-block text-sm font-medium ${isDark
                    ? "text-blue-400 hover:text-blue-300"
                    : "text-blue-600 hover:text-blue-700"
                    }`}
                >
                  Read original article →
                </a>
              )}
            </article>
          ))}
        </div>

        {totalPages > 1 && (
          <div className="mt-6 flex flex-col items-center gap-3">
            <p className={`text-xs ${colors.text}`}>
              Showing {(currentPage - 1) * PAGE_SIZE + 1}–{Math.min(currentPage * PAGE_SIZE, total)} of {total}
            </p>
            <div className="flex flex-wrap items-center gap-1">
              <button
                type="button"
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
                className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-40 ${colors.inactiveTab}`}
              >
                ← Prev
              </button>
              {pageNumbers().map((p, i) =>
                p === "..." ? (
                  <span key={`ellipsis-${i}`} className={`px-2 text-sm ${colors.text}`}>…</span>
                ) : (
                  <button
                    key={p}
                    type="button"
                    onClick={() => handlePageChange(p as number)}
                    className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                      currentPage === p ? "bg-blue-600 text-white" : colors.inactiveTab
                    }`}
                  >
                    {p}
                  </button>
                )
              )}
              <button
                type="button"
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
                className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-40 ${colors.inactiveTab}`}
              >
                Next →
              </button>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}

/**
 * Purpose:
 * Renders a reusable statistics card with theme-aware
 * backgrounds, borders, titles and values.
 */
function StatCard({
  title,
  value,
  description,
  isDark,
}: {
  title: string;
  value: string | number;
  description: string;
  isDark: boolean;
}) {
  return (
    <div
      className={`rounded-xl border p-5 shadow-sm transition-colors ${isDark
        ? "border-slate-800 bg-slate-900"
        : "border-slate-200 bg-white"
        }`}
    >
      <p
        className={`text-sm font-medium ${isDark ? "text-slate-400" : "text-slate-500"
          }`}
      >
        {title}
      </p>

      <p
        className={`mt-3 text-3xl font-bold ${isDark ? "text-white" : "text-slate-900"
          }`}
      >
        {value}
      </p>

      <p
        className={`mt-2 text-xs ${isDark ? "text-slate-500" : "text-slate-500"
          }`}
      >
        {description}
      </p>
    </div>
  );
}

/**
 * Purpose:
 * Provides a unified AI Insights dashboard driven by the global
 * AI model selector in the sidebar. Removes the redundant
 * per-page model selection buttons.
 */

export default function AIInsights() {
  const { aiProvider } = useAIModel();

  return aiProvider === "shubhAI" ? <OllamaInsights /> : <GeminiInsights />;
}