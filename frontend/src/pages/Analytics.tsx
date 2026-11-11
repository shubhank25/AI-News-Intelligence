
/**
 * Purpose:
 * Displays the News Analytics dashboard, including source-wise
 * article counts, AI category distribution, sentiment analysis,
 * and daily publishing trends.
 *
 * Supports light and dark themes using the application's ThemeContext.
 * Chart colors, labels, axes, tooltips, cards, and filters adapt
 * automatically to the currently selected theme.
 */

import { useEffect, useState } from "react";
import type { ReactNode } from "react";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import {
  getCategoryAnalytics,
  getNewsStatistics,
  getPublishingTrends,
} from "../services/api";

import type {
  CategoryStatistic,
  NewsStatistics,
  PublishingTrend,
} from "../types/news";

import { useTheme } from "../context/ThemeContext";

const SENTIMENT_COLORS = ["#16a34a", "#dc2626", "#64748b"];

export default function Analytics() {
  const { theme } = useTheme();
  const isDark = theme === "dark";

  const [statistics, setStatistics] = useState<NewsStatistics | null>(null);
  const [categories, setCategories] = useState<CategoryStatistic[]>([]);
  const [trends, setTrends] = useState<PublishingTrend[]>([]);

  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  const [loading, setLoading] = useState(true);
  const [trendLoading, setTrendLoading] = useState(false);
  const [error, setError] = useState("");

  // Theme-aware chart colors.
  const chartText = isDark ? "#cbd5e1" : "#64748b";
  const chartGrid = isDark ? "#334155" : "#e2e8f0";
  const chartBorder = isDark ? "#475569" : "#cbd5e1";
  const tooltipBackground = isDark ? "#0f172a" : "#ffffff";
  const tooltipText = isDark ? "#f1f5f9" : "#0f172a";

  const tooltipStyle = {
    backgroundColor: tooltipBackground,
    border: `1px solid ${chartBorder}`,
    borderRadius: "10px",
    color: tooltipText,
    boxShadow: isDark
      ? "0 10px 25px rgba(0,0,0,0.35)"
      : "0 10px 25px rgba(15,23,42,0.12)",
  };

  const axisTickStyle = {
    fill: chartText,
    fontSize: 12,
  };

  const headingClass = isDark
    ? "text-2xl font-bold text-white"
    : "text-2xl font-bold text-slate-900";

  const descriptionClass = isDark
    ? "mt-1 text-sm text-slate-400"
    : "mt-1 text-sm text-slate-500";

  // Load source, sentiment, and category analytics.
  useEffect(() => {
    let active = true;

    const loadAnalytics = async () => {
      try {
        setLoading(true);
        setError("");

        const [statsData, categoryData] = await Promise.all([
          getNewsStatistics(),
          getCategoryAnalytics(),
        ]);

        if (active) {
          setStatistics(statsData);
          setCategories(categoryData);
        }
      } catch (err) {
        console.error("Failed to load analytics:", err);

        if (active) {
          setError("Unable to load analytics. Please check the backend.");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    void loadAnalytics();

    return () => {
      active = false;
    };
  }, []);

  // Load publishing trends whenever the date filters change.
  useEffect(() => {
    let active = true;

    const loadTrends = async () => {
      try {
        setTrendLoading(true);

        const trendData = await getPublishingTrends(
          dateFrom || undefined,
          dateTo || undefined
        );

        if (active) {
          setTrends(trendData);
        }
      } catch (err) {
        console.error("Failed to load publishing trends:", err);

        if (active) {
          setError("Unable to load publishing trends.");
        }
      } finally {
        if (active) {
          setTrendLoading(false);
        }
      }
    };

    void loadTrends();

    return () => {
      active = false;
    };
  }, [dateFrom, dateTo]);

  const sentimentData = statistics
    ? [
        {
          name: "Positive",
          value: statistics.ai_analysis.sentiment_distribution.positive,
        },
        {
          name: "Negative",
          value: statistics.ai_analysis.sentiment_distribution.negative,
        },
        {
          name: "Neutral",
          value: statistics.ai_analysis.sentiment_distribution.neutral,
        },
      ]
    : [];

  if (loading) {
    return (
      <div
        className={`flex min-h-[60vh] items-center justify-center ${
          isDark ? "text-slate-400" : "text-slate-500"
        }`}
      >
        Loading analytics...
      </div>
    );
  }

  if (error && !statistics) {
    return (
      <div
        className={`rounded-xl border p-5 ${
          isDark
            ? "border-red-900 bg-red-950/40 text-red-300"
            : "border-red-200 bg-red-50 text-red-700"
        }`}
      >
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page heading */}
      <div>
        <h1 className={headingClass}>News Analytics</h1>

        <p className={descriptionClass}>
          Understand your news collection, AI categories, sentiment, and
          publishing activity.
        </p>
      </div>

      {error && (
        <div
          className={`rounded-lg border p-3 text-sm ${
            isDark
              ? "border-red-900 bg-red-950/40 text-red-300"
              : "border-red-200 bg-red-50 text-red-700"
          }`}
        >
          {error}
        </div>
      )}

      {/* Summary cards */}
      {statistics && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <SummaryCard
            title="Total Articles"
            value={statistics.total_articles}
            isDark={isDark}
          />

          <SummaryCard
            title="News Sources"
            value={statistics.total_sources}
            isDark={isDark}
          />

          <SummaryCard
            title="AI Analyzed"
            value={statistics.ai_analysis.analyzed_articles}
            isDark={isDark}
          />

          <SummaryCard
            title="AI Coverage"
            value={`${statistics.ai_analysis.coverage_percentage}%`}
            isDark={isDark}
          />
        </div>
      )}

      {/* Source and category charts */}
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <ChartCard title="Articles by Source" isDark={isDark}>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={statistics?.articles_by_source ?? []}>
              <CartesianGrid
                strokeDasharray="3 3"
                vertical={false}
                stroke={chartGrid}
              />

              <XAxis
                dataKey="source"
                tick={axisTickStyle}
                axisLine={{ stroke: chartBorder }}
                tickLine={{ stroke: chartBorder }}
              />

              <YAxis
                allowDecimals={false}
                tick={axisTickStyle}
                axisLine={{ stroke: chartBorder }}
                tickLine={{ stroke: chartBorder }}
              />

              <Tooltip contentStyle={tooltipStyle} />

              <Bar
                dataKey="article_count"
                name="Articles"
                fill="#6366f1"
                radius={[6, 6, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Articles by AI Category" isDark={isDark}>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={categories}>
              <CartesianGrid
                strokeDasharray="3 3"
                vertical={false}
                stroke={chartGrid}
              />

              <XAxis
                dataKey="category"
                tick={axisTickStyle}
                interval={0}
                angle={-15}
                textAnchor="end"
                height={65}
                axisLine={{ stroke: chartBorder }}
                tickLine={{ stroke: chartBorder }}
              />

              <YAxis
                allowDecimals={false}
                tick={axisTickStyle}
                axisLine={{ stroke: chartBorder }}
                tickLine={{ stroke: chartBorder }}
              />

              <Tooltip contentStyle={tooltipStyle} />

              <Bar
                dataKey="article_count"
                name="Articles"
                fill="#0d9488"
                radius={[6, 6, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* Sentiment chart */}
      <ChartCard title="AI Sentiment Distribution" isDark={isDark}>
        {sentimentData.every((item) => item.value === 0) ? (
          <EmptyState message="No AI sentiment data available yet." isDark={isDark} />
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={sentimentData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={100}
                label={{ fill: chartText }}
              >
                {sentimentData.map((entry, index) => (
                  <Cell
                    key={entry.name}
                    fill={SENTIMENT_COLORS[index]}
                  />
                ))}
              </Pie>

              <Tooltip contentStyle={tooltipStyle} />

              <Legend
                wrapperStyle={{
                  color: chartText,
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        )}
      </ChartCard>

      {/* Publishing trends */}
      <ChartCard title="Daily Publishing Trends" isDark={isDark}>
        <div className="mb-5 flex flex-wrap items-end gap-4">
          <div>
            <label
              className={`mb-1 block text-sm font-medium ${
                isDark ? "text-slate-300" : "text-slate-600"
              }`}
            >
              From date
            </label>

            <input
              type="date"
              value={dateFrom}
              max={dateTo || undefined}
              onChange={(event) => setDateFrom(event.target.value)}
              className={`rounded-lg border px-3 py-2 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 ${
                isDark
                  ? "border-slate-700 bg-slate-800 text-white"
                  : "border-slate-300 bg-white text-slate-800"
              }`}
            />
          </div>

          <div>
            <label
              className={`mb-1 block text-sm font-medium ${
                isDark ? "text-slate-300" : "text-slate-600"
              }`}
            >
              To date
            </label>

            <input
              type="date"
              value={dateTo}
              min={dateFrom || undefined}
              onChange={(event) => setDateTo(event.target.value)}
              className={`rounded-lg border px-3 py-2 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 ${
                isDark
                  ? "border-slate-700 bg-slate-800 text-white"
                  : "border-slate-300 bg-white text-slate-800"
              }`}
            />
          </div>

          <button
            onClick={() => {
              setDateFrom("");
              setDateTo("");
            }}
            className={`rounded-lg border px-4 py-2 text-sm font-medium transition ${
              isDark
                ? "border-slate-700 text-slate-300 hover:bg-slate-800"
                : "border-slate-300 text-slate-600 hover:bg-slate-100"
            }`}
          >
            Clear Filters
          </button>
        </div>

        {trendLoading ? (
          <EmptyState
            message="Loading publishing trends..."
            isDark={isDark}
          />
        ) : trends.length === 0 ? (
          <EmptyState
            message="No publishing data available for this date range."
            isDark={isDark}
          />
        ) : (
          <ResponsiveContainer width="100%" height={320}>
            <LineChart data={trends}>
              <CartesianGrid
                strokeDasharray="3 3"
                stroke={chartGrid}
              />

              <XAxis
                dataKey="date"
                tick={axisTickStyle}
                axisLine={{ stroke: chartBorder }}
                tickLine={{ stroke: chartBorder }}
              />

              <YAxis
                allowDecimals={false}
                tick={axisTickStyle}
                axisLine={{ stroke: chartBorder }}
                tickLine={{ stroke: chartBorder }}
              />

              <Tooltip contentStyle={tooltipStyle} />

              <Legend
                wrapperStyle={{
                  color: chartText,
                }}
              />

              <Line
                type="monotone"
                dataKey="article_count"
                name="Articles Published"
                stroke="#6366f1"
                strokeWidth={3}
                activeDot={{ r: 7 }}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </ChartCard>
    </div>
  );
}

/**
 * Purpose:
 * Renders a reusable analytics KPI card with theme-aware
 * background, border, title, and value colors.
 */
function SummaryCard({
  title,
  value,
  isDark,
}: {
  title: string;
  value: string | number;
  isDark: boolean;
}) {
  return (
    <div
      className={`rounded-xl border p-5 shadow-sm transition-colors ${
        isDark
          ? "border-slate-800 bg-slate-900"
          : "border-slate-200 bg-white"
      }`}
    >
      <p
        className={`text-sm font-medium ${
          isDark ? "text-slate-400" : "text-slate-500"
        }`}
      >
        {title}
      </p>

      <p
        className={`mt-2 text-2xl font-bold ${
          isDark ? "text-white" : "text-slate-900"
        }`}
      >
        {value}
      </p>
    </div>
  );
}

/**
 * Purpose:
 * Renders a reusable analytics chart panel with theme-aware
 * background, border, and heading colors.
 */
function ChartCard({
  title,
  children,
  isDark,
}: {
  title: string;
  children: ReactNode;
  isDark: boolean;
}) {
  return (
    <section
      className={`rounded-xl border p-5 shadow-sm transition-colors ${
        isDark
          ? "border-slate-800 bg-slate-900"
          : "border-slate-200 bg-white"
      }`}
    >
      <h2
        className={`mb-5 text-lg font-semibold ${
          isDark ? "text-white" : "text-slate-800"
        }`}
      >
        {title}
      </h2>

      {children}
    </section>
  );
}

/**
 * Purpose:
 * Displays a reusable empty or loading state inside chart panels
 * with text colors that adapt to the selected theme.
 */
function EmptyState({
  message,
  isDark,
}: {
  message: string;
  isDark: boolean;
}) {
  return (
    <div
      className={`flex h-[300px] items-center justify-center text-sm ${
        isDark ? "text-slate-400" : "text-slate-500"
      }`}
    >
      {message}
    </div>
  );
}
