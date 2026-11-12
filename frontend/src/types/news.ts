
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



/**
 * Purpose:
 * Defines TypeScript interfaces for ShubhAI (Ollama) article
 * analysis, pending articles, pagination and dashboard statistics.
 */

export interface OllamaArticleAnalysis {
  summary: string;
  key_points: string[];
  category: string;
  sentiment: string;
  status: "completed" | "failed";
  attempt_count: number;
  analyzed_at: string | null;
}

export interface OllamaAnalyzedArticle {
  article_id: number;
  title: string;
  url: string | null;
  source: string | null;
  analysis: OllamaArticleAnalysis;
}

export interface OllamaPendingArticle {
  article_id: number;
  title: string;
  url: string | null;
  source: string | null;
}

export interface OllamaAnalysisListResponse {
  total: number;
  limit: number;
  offset: number;
  items: OllamaAnalyzedArticle[];
}

export interface OllamaPendingListResponse {
  total: number;
  limit: number;
  offset: number;
  items: OllamaPendingArticle[];
}

export interface OllamaSentimentDistribution {
  positive: number;
  negative: number;
  neutral: number;
}

export interface OllamaAnalysisStatus {
  total_articles: number;
  analyzed_articles: number;
  completed: number;
  pending: number;
  failed: number;
  coverage_percentage: number;
  sentiment_distribution: OllamaSentimentDistribution;
}
