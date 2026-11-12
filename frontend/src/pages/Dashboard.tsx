
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
import { getNewsStatistics, getOllamaAnalysisStatus } from "../services/api";
import type { NewsStatistics, OllamaAnalysisStatus } from "../types/news";
import { useTheme } from "../context/ThemeContext";
import { useAIModel } from "../context/AIModelContext";

function Dashboard() {
  const { theme } = useTheme();
  const isDark = theme === "dark";
  const { aiProvider } = useAIModel();

  const [geminiStats, setGeminiStats] = useState<NewsStatistics | null>(null);
  const [ollamaStats, setOllamaStats] = useState<OllamaAnalysisStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError("");

      const [gemini, ollama] = await Promise.all([
        getNewsStatistics("gemini"),
        getOllamaAnalysisStatus(),
      ]);

      setGeminiStats(gemini);
      setOllamaStats(ollama);
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
        className={`flex min-h-64 items-center justify-center ${
          isDark ? "text-slate-400" : "text-slate-500"
        }`}
      >
        Loading dashboard statistics...
      </div>
    );
  }

  if (error || !geminiStats || !ollamaStats) {
    return (
      <div
        className={`rounded-2xl border p-6 ${
          isDark ? "border-rose-900 bg-rose-950/30" : "border-rose-200 bg-rose-50"
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

  const isGemini = aiProvider === "gemini";

  const analyzed = isGemini
    ? geminiStats.ai_analysis.analyzed_articles
    : ollamaStats.completed;

  const pending = isGemini
    ? geminiStats.ai_analysis.pending_articles
    : ollamaStats.pending;

  const coverage = isGemini
    ? geminiStats.ai_analysis.coverage_percentage
    : ollamaStats.coverage_percentage;

  const sentiment = isGemini
    ? geminiStats.ai_analysis.sentiment_distribution
    : ollamaStats.sentiment_distribution;

  const providerLabel = isGemini ? "Gemini" : "ShubhAI";

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className={`text-2xl font-bold ${isDark ? "text-white" : "text-slate-900"}`}>
            Good to see you!
          </h1>

          <p className={`mt-2 text-sm ${isDark ? "text-slate-400" : "text-slate-500"}`}>
            Showing{" "}
            <span className="font-semibold text-indigo-500">{providerLabel}</span>{" "}
            analysis across your news intelligence platform.
          </p>
        </div>

        <button
          onClick={() => void fetchDashboardData()}
          className={`flex items-center gap-2 rounded-xl border px-4 py-2 text-sm transition-colors ${
            isDark
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
          value={geminiStats.total_articles.toLocaleString()}
          description="Articles collected in database"
          icon={Newspaper}
          iconColor="text-indigo-400"
        />

        <StatCard
          title="AI Analyzed"
          value={analyzed.toLocaleString()}
          description={`Analyzed by ${providerLabel}`}
          icon={BrainCircuit}
          iconColor="text-emerald-400"
        />

        <StatCard
          title="Pending Analysis"
          value={pending.toLocaleString()}
          description={`Awaiting ${providerLabel} analysis`}
          icon={Clock3}
          iconColor="text-amber-400"
        />

        <StatCard
          title="AI Coverage"
          value={`${Number(coverage).toFixed(1)}%`}
          description={`${providerLabel} coverage`}
          icon={Target}
          iconColor="text-purple-400"
        />
      </section>

      <section className="grid gap-5 xl:grid-cols-2">
        <SentimentChart data={sentiment} />

        <div
          className={`rounded-2xl border p-5 shadow-sm transition-colors ${
            isDark ? "border-slate-800 bg-slate-900" : "border-slate-200 bg-white"
          }`}
        >
          <h3 className={`text-lg font-semibold ${isDark ? "text-white" : "text-slate-900"}`}>
            News Sources
          </h3>

          <p className={`mt-1 text-sm ${isDark ? "text-slate-400" : "text-slate-500"}`}>
            Articles collected from each source
          </p>

          <div className="mt-6 space-y-5">
            {geminiStats.articles_by_source.length > 0 ? (
              geminiStats.articles_by_source.map((source) => {
                const percentage =
                  geminiStats.total_articles > 0
                    ? (source.article_count / geminiStats.total_articles) * 100
                    : 0;

                return (
                  <div key={source.source}>
                    <div className="mb-2 flex justify-between gap-3 text-sm">
                      <span className={`truncate ${isDark ? "text-slate-300" : "text-slate-700"}`}>
                        {source.source}
                      </span>

                      <span className={isDark ? "text-slate-400" : "text-slate-500"}>
                        {source.article_count}
                      </span>
                    </div>

                    <div
                      className={`h-2 overflow-hidden rounded-full ${
                        isDark ? "bg-slate-800" : "bg-slate-100"
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
              <p className="text-sm text-slate-500">No source statistics available.</p>
            )}
          </div>

          <div
            className={`mt-6 border-t pt-4 ${isDark ? "border-slate-800" : "border-slate-200"}`}
          >
            <p className={`text-sm ${isDark ? "text-slate-400" : "text-slate-500"}`}>
              Total sources:{" "}
              <span className={`font-semibold ${isDark ? "text-white" : "text-slate-900"}`}>
                {geminiStats.total_sources}
              </span>
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}

export default Dashboard;
