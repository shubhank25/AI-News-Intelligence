
/**
 * Purpose:
 * Displays the complete ShubhAI dashboard including article statistics,
 * analysis coverage, sentiment distribution, and analyzed or pending news.
 * Uses local Ollama analysis data independently from Gemini.
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
    getOllamaAnalyses,
    getOllamaAnalysisStatus,
    getOllamaPendingArticles,
} from "../services/api";

import type {
    OllamaAnalyzedArticle,
    OllamaAnalysisStatus,
    OllamaPendingArticle,
} from "../types/news";

import { useTheme } from "../context/ThemeContext";

type ArticleTab = "analyzed" | "pending";

const SENTIMENT_COLORS: Record<string, string> = {
    positive: "#22c55e",
    negative: "#ef4444",
    neutral: "#94a3b8",
};

export default function OllamaInsights() {
    const { theme } = useTheme();
    const isDark = theme === "dark";

    const [status, setStatus] = useState<OllamaAnalysisStatus | null>(null);
    const [analyzedArticles, setAnalyzedArticles] = useState<OllamaAnalyzedArticle[]>([]);
    const [pendingArticles, setPendingArticles] = useState<OllamaPendingArticle[]>([]);

    const [activeTab, setActiveTab] = useState<ArticleTab>("analyzed");
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [error, setError] = useState("");

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

    const loadDashboard = useCallback(async () => {
        try {
            setRefreshing(true);
            setError("");

            const [stats, analyzed, pending] = await Promise.all([
                getOllamaAnalysisStatus(),
                getOllamaAnalyses(10, 0),
                getOllamaPendingArticles(10, 0),
            ]);

            setStatus(stats);
            setAnalyzedArticles(analyzed.items);
            setPendingArticles(pending.items);
        } catch (err) {
            console.error("ShubhAI dashboard loading failed:", err);
            setError("Unable to load ShubhAI dashboard. Please check the backend APIs.");
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    }, []);

    useEffect(() => {
        void loadDashboard();
    }, [loadDashboard]);

    const sentimentData = status
        ? [
            { name: "Positive", value: status.sentiment_distribution.positive },
            { name: "Negative", value: status.sentiment_distribution.negative },
            { name: "Neutral", value: status.sentiment_distribution.neutral },
        ].filter((item) => item.value > 0)
        : [];

    const coverage = Math.min(
        100,
        Math.max(0, status?.coverage_percentage ?? 0),
    );

    const visibleArticles =
        activeTab === "analyzed" ? analyzedArticles : pendingArticles;

    const tooltipStyle = {
        backgroundColor: isDark ? "#0f172a" : "#ffffff",
        border: `1px solid ${isDark ? "#334155" : "#e2e8f0"}`,
        borderRadius: "10px",
        color: isDark ? "#f8fafc" : "#0f172a",
    };

    if (loading) {
        return (
            <div className={`py-16 text-center ${colors.text}`}>
                Loading ShubhAI dashboard...
            </div>
        );
    }

    if (error || !status) {
        return (
            <div
                className={`rounded-xl border p-5 ${isDark
                    ? "border-red-900 bg-red-950/30 text-red-300"
                    : "border-red-200 bg-red-50 text-red-700"
                    }`}
            >
                <p>{error || "ShubhAI statistics are unavailable."}</p>
                <button
                    type="button"
                    onClick={() => void loadDashboard()}
                    className="mt-3 rounded-lg bg-blue-600 px-4 py-2 text-sm text-white"
                >
                    Retry
                </button>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Dashboard heading */}
            <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                    <h2 className={`text-2xl font-bold ${colors.heading}`}>
                        ShubhAI Insights
                    </h2>
                    <p className={`mt-1 text-sm ${colors.text}`}>
                        Monitor locally generated AI analysis and sentiment across your articles.
                    </p>
                </div>
            </div>

            {/* Statistics cards */}
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                <StatCard
                    title="Total Articles"
                    value={status.total_articles}
                    description="Articles eligible for analysis"
                    isDark={isDark}
                />

                <StatCard
                    title="AI Analyzed"
                    value={status.completed}
                    description="Successfully analyzed by ShubhAI"
                    isDark={isDark}
                />

                <StatCard
                    title="Pending Analysis"
                    value={status.pending}
                    description="Waiting for ShubhAI processing"
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
                <section
                    className={`rounded-xl border p-6 shadow-sm ${colors.panel}`}
                >
                    <h3 className={`text-lg font-semibold ${colors.heading}`}>
                        AI Analysis Coverage
                    </h3>

                    <div className="mt-6 flex items-end justify-between gap-3">
                        <span className={`text-3xl font-bold ${colors.heading}`}>
                            {coverage.toFixed(1)}%
                        </span>

                        <span className={`text-sm ${colors.text}`}>
                            {status.completed} of {status.total_articles} articles
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
                        This represents the percentage of eligible stored articles
                        successfully analyzed by ShubhAI.
                    </p>
                </section>

                <section
                    className={`rounded-xl border p-6 shadow-sm ${colors.panel}`}
                >
                    <h3 className={`text-lg font-semibold ${colors.heading}`}>
                        Sentiment Distribution
                    </h3>

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
            {/* Article tabs */}
            <section
                className={`rounded-xl border p-5 shadow-sm transition-colors ${colors.panel}`}
            >
                <div className="flex flex-wrap items-center justify-between gap-4">
                    <h3 className={`text-lg font-semibold ${colors.heading}`}>
                        ShubhAI Article Analysis
                    </h3>

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
                                onClick={() => setActiveTab("analyzed")}
                                className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${activeTab === "analyzed"
                                        ? "bg-blue-600 text-white"
                                        : colors.inactiveTab
                                    }`}
                            >
                                Analyzed ({status.completed})
                            </button>

                            <button
                                type="button"
                                onClick={() => setActiveTab("pending")}
                                className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${activeTab === "pending"
                                        ? "bg-blue-600 text-white"
                                        : colors.inactiveTab
                                    }`}
                            >
                                Pending ({status.pending})
                            </button>
                        </div>
                    </div>
                </div>

                <div className="mt-5 space-y-4">
                    {visibleArticles.length === 0 && (
                        <p className={`py-8 text-center text-sm ${colors.text}`}>
                            No {activeTab} articles found.
                        </p>
                    )}

                    {activeTab === "analyzed" &&
                        analyzedArticles.map((article) => (
                            <article
                                key={article.article_id}
                                className={`rounded-lg border p-4 transition-colors ${colors.article}`}
                            >
                                <div className="flex flex-wrap items-center gap-2">
                                    {article.source && (
                                        <span className={`text-xs ${colors.text}`}>
                                            {article.source}
                                        </span>
                                    )}

                                    <span className="rounded-full bg-blue-500/15 px-3 py-1 text-xs font-medium text-blue-600">
                                        {article.analysis.category}
                                    </span>

                                    <span
                                        className={`rounded-full px-3 py-1 text-xs capitalize ${article.analysis.sentiment.toLowerCase() === "positive"
                                            ? "bg-green-500/15 text-green-600"
                                            : article.analysis.sentiment.toLowerCase() === "negative"
                                                ? "bg-red-500/15 text-red-600"
                                                : isDark
                                                    ? "bg-slate-700 text-slate-200"
                                                    : "bg-slate-200 text-slate-700"
                                            }`}
                                    >
                                        {article.analysis.sentiment}
                                    </span>
                                </div>

                                <h4 className={`mt-3 font-semibold ${colors.heading}`}>
                                    {article.title}
                                </h4>

                                <p className={`mt-3 text-sm leading-7 ${colors.body}`}>
                                    {article.analysis.summary}
                                </p>

                                {article.analysis.key_points.length > 0 && (
                                    <ul className={`mt-3 list-disc space-y-1 pl-5 text-sm ${colors.body}`}>
                                        {article.analysis.key_points.map((point, index) => (
                                            <li key={index}>{point}</li>
                                        ))}
                                    </ul>
                                )}

                                <div className={`mt-4 flex flex-wrap justify-between gap-2 text-xs ${colors.text}`}>
                                    <span>Attempts: {article.analysis.attempt_count}</span>
                                    <span>
                                        {article.analysis.analyzed_at
                                            ? new Date(article.analysis.analyzed_at).toLocaleString()
                                            : "Analysis date unavailable"}
                                    </span>
                                </div>

                                {article.url && (
                                    <a
                                        href={article.url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="mt-3 inline-block text-sm font-medium text-blue-500 hover:text-blue-600"
                                    >
                                        Read original article →
                                    </a>
                                )}
                            </article>
                        ))}

                    {activeTab === "pending" &&
                        pendingArticles.map((article) => (
                            <article
                                key={article.article_id}
                                className={`rounded-lg border p-4 transition-colors ${colors.article}`}
                            >
                                <div className="flex flex-wrap items-center gap-2">
                                    {article.source && (
                                        <span className={`text-xs ${colors.text}`}>
                                            {article.source}
                                        </span>
                                    )}
                                    <span className="rounded-full bg-amber-500/15 px-3 py-1 text-xs text-amber-600">
                                        Pending
                                    </span>
                                </div>

                                <h4 className={`mt-3 font-semibold ${colors.heading}`}>
                                    {article.title}
                                </h4>

                                <p className={`mt-2 text-sm ${colors.text}`}>
                                    Waiting for ShubhAI analysis.
                                </p>

                                {article.url && (
                                    <a
                                        href={article.url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="mt-3 inline-block text-sm font-medium text-blue-500 hover:text-blue-600"
                                    >
                                        Read original article →
                                    </a>
                                )}
                            </article>
                        ))}
                </div>
            </section>
        </div>
    );
}

/**
 * Purpose:
 * Renders a reusable ShubhAI dashboard statistics card.
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
            className={`rounded-xl border p-5 shadow-sm ${isDark
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
