
/**
 * Purpose:
 * Displays live news intelligence metrics by fetching dashboard
 * statistics from FastAPI and visualizing AI sentiment and sources.
 * Supports both light and dark themes.
 */

import { useEffect, useState } from "react";
import {
  Newspaper,
  BrainCircuit,
  Clock3,
  Target,
  RefreshCw,
} from "lucide-react";

import StatCard from "../components/dashboard/StatCard";
import SentimentChart from "../components/dashboard/SentimentChart";
import { getNewsStatistics } from "../services/api";
import type { NewsStatistics } from "../types/news";
import { useTheme } from "../context/ThemeContext";

function Dashboard() {
  const { theme } = useTheme();
  const isDark = theme === "dark";

  const [stats, setStats] = useState<NewsStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError("");

      const data = await getNewsStatistics();
      setStats(data);
    } catch (err) {
      console.error("Dashboard API error:", err);
      setError(
        "Unable to load dashboard statistics. Please check whether the backend is running."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void fetchDashboardData();
  }, []);

  if (loading) {
    return (
      <div
        className={`flex min-h-64 items-center justify-center ${isDark ? "text-slate-400" : "text-slate-500"
          }`}
      >
        Loading dashboard statistics...
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div
        className={`rounded-2xl border p-6 ${isDark
            ? "border-rose-900 bg-rose-950/30"
            : "border-rose-200 bg-rose-50"
          }`}
      >
        <p className={isDark ? "text-rose-300" : "text-rose-700"}>
          {error || "No dashboard data available."}
        </p>

        <button
          onClick={() => void fetchDashboardData()}
          className="mt-4 rounded-lg bg-rose-700 px-4 py-2 text-sm text-white hover:bg-rose-600"
        >
          Try again
        </button>
      </div>
    );
  }

  const ai = stats.ai_analysis;

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1
            className={`text-2xl font-bold ${isDark ? "text-white" : "text-slate-900"
              }`}
          >
            Good to see you!
          </h1>

          <p
            className={`mt-2 text-sm ${isDark ? "text-slate-400" : "text-slate-500"
              }`}
          >
            Here's what's happening across your news intelligence platform.
          </p>
        </div>

        <button
          onClick={() => void fetchDashboardData()}
          className={`flex items-center gap-2 rounded-xl border px-4 py-2 text-sm transition-colors ${isDark
              ? "border-slate-700 text-slate-300 hover:bg-slate-800"
              : "border-slate-300 text-slate-600 hover:bg-slate-100"
            }`}
        >
          <RefreshCw size={16} />
          Refresh
        </button>
      </div>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          title="Total Articles"
          value={stats.total_articles.toLocaleString()}
          description="Articles collected in database"
          icon={Newspaper}
          iconColor="text-indigo-400"
        />

        <StatCard
          title="AI Analyzed"
          value={ai.analyzed_articles.toLocaleString()}
          description="Articles successfully analyzed"
          icon={BrainCircuit}
          iconColor="text-emerald-400"
        />

        <StatCard
          title="Pending Analysis"
          value={ai.pending_articles.toLocaleString()}
          description="Articles awaiting AI analysis"
          icon={Clock3}
          iconColor="text-amber-400"
        />

        <StatCard
          title="AI Coverage"
          value={`${ai.coverage_percentage.toFixed(1)}%`}
          description="Share of articles analyzed by AI"
          icon={Target}
          iconColor="text-purple-400"
        />
      </section>

      <section className="grid gap-5 xl:grid-cols-2">
        <SentimentChart data={ai.sentiment_distribution} />

        <div
          className={`rounded-2xl border p-5 shadow-sm transition-colors ${isDark
              ? "border-slate-800 bg-slate-900"
              : "border-slate-200 bg-white"
            }`}
        >
          <h3
            className={`text-lg font-semibold ${isDark ? "text-white" : "text-slate-900"
              }`}
          >
            News Sources
          </h3>

          <p
            className={`mt-1 text-sm ${isDark ? "text-slate-400" : "text-slate-500"
              }`}
          >
            Articles collected from each source
          </p>

          <div className="mt-6 space-y-5">
            {stats.articles_by_source.length > 0 ? (
              stats.articles_by_source.map((source) => {
                const percentage =
                  stats.total_articles > 0
                    ? (source.article_count / stats.total_articles) * 100
                    : 0;

                return (
                  <div key={source.source}>
                    <div className="mb-2 flex justify-between gap-3 text-sm">
                      <span
                        className={`truncate ${isDark ? "text-slate-300" : "text-slate-700"
                          }`}
                      >
                        {source.source}
                      </span>

                      <span className={isDark ? "text-slate-400" : "text-slate-500"}>
                        {source.article_count}
                      </span>
                    </div>

                    <div
                      className={`h-2 overflow-hidden rounded-full ${isDark ? "bg-slate-800" : "bg-slate-100"
                        }`}
                    >
                      <div
                        className="h-full rounded-full bg-indigo-500"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                );
              })
            ) : (
              <p className="text-sm text-slate-500">
                No source statistics available.
              </p>
            )}
          </div>

          <div
            className={`mt-6 border-t pt-4 ${isDark ? "border-slate-800" : "border-slate-200"
              }`}
          >
            <p className={`text-sm ${isDark ? "text-slate-400" : "text-slate-500"}`}>
              Total sources:{" "}
              <span className={`font-semibold ${isDark ? "text-white" : "text-slate-900"}`}>
                {stats.total_sources}
              </span>
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}

export default Dashboard;
