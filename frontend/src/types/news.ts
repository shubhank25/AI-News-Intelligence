
/**
 * Purpose:
 * Defines TypeScript types for news articles and dashboard
 * statistics returned by the FastAPI backend.
 */

export interface NewsArticle {
  id: number;
  title: string;
  source?: string;
  url?: string;
  published_at?: string | null;
  ai_summary?: string | null;
  ai_key_points?: string[] | null;
  ai_category?: string | null;
  ai_sentiment?: "positive" | "negative" | "neutral" | null;
}

export interface SourceStatistic {
  source: string;
  article_count: number;
}

export interface SentimentDistribution {
  positive: number;
  negative: number;
  neutral: number;
}

export interface AIAnalysisStatistics {
  analyzed_articles: number;
  pending_articles: number;
  coverage_percentage: number;
  sentiment_distribution: SentimentDistribution;
}

export interface NewsStatistics {
  total_articles: number;
  total_sources: number;
  articles_by_source: SourceStatistic[];
  ai_analysis: AIAnalysisStatistics;
}

/**
 * Purpose:
 * Defines TypeScript types for category-wise and daily publishing
 * analytics data returned by the FastAPI backend.
 */

export interface CategoryStatistic {
  category: string;
  article_count: number;
}

export interface PublishingTrend {
  date: string;
  article_count: number;
}