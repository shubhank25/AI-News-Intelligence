
/**
 * Purpose:
 * Displays an individual news article with its source,
 * publication date, AI summary, category and sentiment.
 */

import { ExternalLink, CalendarDays, BrainCircuit } from "lucide-react";
import type { NewsArticleWithAnalysis } from "../../types/news";

interface NewsCardProps {
  article: NewsArticleWithAnalysis;
}

function NewsCard({ article }: NewsCardProps) {
  const sentimentStyles = {
    positive: "bg-emerald-500/10 text-emerald-400",
    negative: "bg-rose-500/10 text-rose-400",
    neutral: "bg-slate-700 text-slate-300",
  };

  const sentiment = article.ai_sentiment?.toLowerCase() as
    | "positive"
    | "negative"
    | "neutral"
    | undefined;

  const sentimentClass = sentiment
    ? sentimentStyles[sentiment] ?? sentimentStyles.neutral
    : sentimentStyles.neutral;

  const formattedDate = article.published_at
    ? new Date(article.published_at).toLocaleDateString()
    : "Date unavailable";

  return (
    <article className="rounded-2xl border border-slate-800 bg-slate-900 p-5 transition hover:border-slate-700">
      <div className="flex flex-wrap items-center gap-2 text-xs text-slate-400">
        <span className="rounded-lg bg-slate-800 px-3 py-1">
          {article.source || "Unknown source"}
        </span>

        <span className="flex items-center gap-1">
          <CalendarDays size={13} />
          {formattedDate}
        </span>
      </div>

      <h2 className="mt-4 text-lg font-semibold leading-7 text-white">
        {article.title}
      </h2>

      <div className="mt-3 flex flex-wrap gap-2">
        {article.ai_category && (
          <span className="rounded-lg bg-indigo-500/10 px-3 py-1 text-xs text-indigo-400">
            {article.ai_category}
          </span>
        )}

        {sentiment && (
          <span className={`rounded-lg px-3 py-1 text-xs capitalize ${sentimentClass}`}>
            {sentiment}
          </span>
        )}
      </div>

      {article.ai_summary ? (
        <div className="mt-5">
          <div className="mb-2 flex items-center gap-2 text-sm font-medium text-indigo-300">
            <BrainCircuit size={16} />
            AI Summary
          </div>

          <p className="text-sm leading-6 text-slate-400">
            {article.ai_summary}
          </p>
        </div>
      ) : (
        <p className="mt-5 text-sm italic text-slate-500">
          AI summary is not available for this article yet.
        </p>
      )}

      {article.ai_key_points && article.ai_key_points.length > 0 && (
        <div className="mt-4">
          <p className="mb-2 text-sm font-medium text-slate-300">
            Key Points
          </p>

          <ul className="space-y-2">
            {article.ai_key_points.map((point, index) => (
              <li key={index} className="flex gap-2 text-sm text-slate-400">
                <span className="text-indigo-400">•</span>
                <span>{point}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {article.url && (
        <a
          href={article.url}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-5 inline-flex items-center gap-2 text-sm font-medium text-indigo-400 hover:text-indigo-300"
        >
          Read original article
          <ExternalLink size={15} />
        </a>
      )}
    </article>
  );
}

export default NewsCard;
