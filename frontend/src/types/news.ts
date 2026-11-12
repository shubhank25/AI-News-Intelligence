/**
 * Purpose:
 * TypeScript interfaces for the AI News Intelligence application.
 *
 * NewsArticle        — scraped article data only (no AI fields).
 * AIAnalysis         — one analysis record from article_ai_analyses.
 * NewsArticleWithAnalysis — article merged with its analysis for display.
 */

// ---------------------------------------------------------------------------
// Core article (scraping data only)
// ---------------------------------------------------------------------------

export interface NewsArticle {
  id: number;
  title: string;
  source?: string;
  url?: string;
  published_at?: string | null;
  category?: string | null;       // RSS feed category, not AI-assigned
  description?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

// ---------------------------------------------------------------------------
// AI analysis record (unified for both Gemini and ShubhAI)
// ---------------------------------------------------------------------------

export type AIModel = "gemini" | "shubhAI";
export type AnalysisStatus = "pending" | "completed" | "failed";
export type Sentiment = "positive" | "negative" | "neutral";

export interface AIAnalysis {
  id: number;
  article_id: number;
  ai_model: AIModel;
  summary: string | null;
  key_points: string[] | null;
  category: string | null;
  sentiment: Sentiment | null;
  status: AnalysisStatus;
  attempt_count: number;
  error_message: string | null;
  analyzed_at: string | null;
  created_at: string | null;
  updated_at: string | null;
}

// ---------------------------------------------------------------------------
// Article merged with analysis — used for display in News / AI Insights
// ---------------------------------------------------------------------------

export interface NewsArticleWithAnalysis extends NewsArticle {
  ai_summary?: string | null;
  ai_key_points?: string[] | null;
  ai_category?: string | null;
  ai_sentiment?: Sentiment | null;
  ai_model?: AIModel | null;
  analysis_status?: AnalysisStatus | null;
}

// ---------------------------------------------------------------------------
// Paginated response from /api/news/unified
// ---------------------------------------------------------------------------

export interface NewsPageResponse {
  total: number;
  limit: number;
  offset: number;
  items: NewsArticleWithAnalysis[];
}

// ---------------------------------------------------------------------------
// Dashboard statistics
// ---------------------------------------------------------------------------

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
  ai_model: AIModel;
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

// ---------------------------------------------------------------------------
// Analytics
// ---------------------------------------------------------------------------

export interface CategoryStatistic {
  category: string;
  article_count: number;
}

export interface PublishingTrend {
  date: string;
  article_count: number;
}

// ---------------------------------------------------------------------------
// ShubhAI (Ollama) specific response shapes from /api/ollama/*
// ---------------------------------------------------------------------------

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
