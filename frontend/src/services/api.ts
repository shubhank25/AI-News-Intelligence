/**
 * Purpose:
 * Centralizes HTTP communication with the FastAPI backend.
 * All AI-specific calls pass ai_model to scope results correctly.
 */

import axios from "axios";

import type {
  AIModel,
  CategoryStatistic,
  NewsArticle,
  NewsPageResponse,
  NewsStatistics,
  OllamaAnalysisListResponse,
  OllamaAnalysisStatus,
  OllamaAnalyzedArticle,
  OllamaPendingListResponse,
  PublishingTrend,
} from "../types/news";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "/api",
  timeout: 120000,
});

// ---------------------------------------------------------------------------
// Statistics
// ---------------------------------------------------------------------------

export const getNewsStatistics = async (
  aiModel: AIModel = "gemini",
): Promise<NewsStatistics> => {
  const response = await api.get<NewsStatistics>("/news/stats", {
    params: { ai_model: aiModel },
  });
  return response.data;
};

// ---------------------------------------------------------------------------
// Unified All-News endpoint (API-level pagination + all filters)
// ---------------------------------------------------------------------------

export const getUnifiedNews = async (
  limit = 10,
  offset = 0,
  search?: string,
  aiCategory?: string,
  aiSentiment?: string,
  aiModel?: AIModel,
): Promise<NewsPageResponse> => {
  const response = await api.get<NewsPageResponse>("/news/unified", {
    params: {
      limit,
      offset,
      ...(search ? { search } : {}),
      ...(aiCategory ? { ai_category: aiCategory } : {}),
      ...(aiSentiment ? { ai_sentiment: aiSentiment } : {}),
      ...(aiModel ? { ai_model: aiModel } : {}),
    },
  });
  return response.data;
};

// ---------------------------------------------------------------------------
// Basic article endpoints
// ---------------------------------------------------------------------------

export const getLatestNews = async (limit = 5): Promise<NewsArticle[]> => {
  const response = await api.get<NewsArticle[]>("/news", {
    params: { limit, offset: 0 },
  });
  return response.data;
};

export const getNewsArticles = async (
  limit = 10,
  offset = 0,
  category?: string,
): Promise<NewsArticle[]> => {
  const response = await api.get<NewsArticle[]>("/news", {
    params: { limit, offset, ...(category ? { category } : {}) },
  });
  return response.data;
};

export const getNewsCategories = async (): Promise<string[]> => {
  const response = await api.get<string[]>("/news/categories");
  return response.data;
};

// ---------------------------------------------------------------------------
// AI analysis endpoints — all scoped by ai_model
// ---------------------------------------------------------------------------

export const getAIAnalyzedArticles = async (
  aiModel: AIModel = "gemini",
  limit = 10,
  offset = 0,
): Promise<NewsArticle[]> => {
  const response = await api.get<NewsArticle[]>("/news/ai/analyzed", {
    params: { ai_model: aiModel, limit, offset },
  });
  return response.data;
};

export const getAIPendingArticles = async (
  aiModel: AIModel = "gemini",
  limit = 10,
  offset = 0,
): Promise<NewsArticle[]> => {
  const response = await api.get<NewsArticle[]>("/news/ai/pending", {
    params: { ai_model: aiModel, limit, offset },
  });
  return response.data;
};

export const getAICategories = async (
  aiModel: AIModel = "gemini",
): Promise<string[]> => {
  const response = await api.get<string[]>("/news/ai/categories", {
    params: { ai_model: aiModel },
  });
  return response.data;
};

export const getAIAnalyzedCount = async (
  aiModel: AIModel = "gemini",
): Promise<number> => {
  const response = await api.get<{ ai_model: string; total: number }>(
    "/news/ai/analyzed/count",
    { params: { ai_model: aiModel } },
  );
  return response.data.total;
};

// ---------------------------------------------------------------------------
// Analytics
// ---------------------------------------------------------------------------

export const getCategoryAnalytics = async (
  aiModel: AIModel = "gemini",
): Promise<CategoryStatistic[]> => {
  const response = await api.get<CategoryStatistic[]>(
    "/news/analytics/categories",
    { params: { ai_model: aiModel } },
  );
  return response.data;
};

export const getPublishingTrends = async (
  dateFrom?: string,
  dateTo?: string,
): Promise<PublishingTrend[]> => {
  const response = await api.get<PublishingTrend[]>(
    "/news/analytics/publishing-trends",
    { params: { date_from: dateFrom, date_to: dateTo } },
  );
  return response.data;
};

// ---------------------------------------------------------------------------
// ShubhAI (Ollama) endpoints — /api/ollama/*
// ---------------------------------------------------------------------------

export const getOllamaAnalyses = async (
  limit = 10,
  offset = 0,
): Promise<OllamaAnalysisListResponse> => {
  const response = await api.get<OllamaAnalysisListResponse>("/ollama/analyses", {
    params: { limit, offset },
  });
  return response.data;
};

export const getOllamaAnalysisByArticle = async (
  articleId: number,
): Promise<OllamaAnalyzedArticle> => {
  const response = await api.get<OllamaAnalyzedArticle>(
    `/ollama/analyses/${articleId}`,
  );
  return response.data;
};

export const getOllamaAnalysisStatus =
  async (): Promise<OllamaAnalysisStatus> => {
    const response = await api.get<OllamaAnalysisStatus>("/ollama/status");
    return response.data;
  };

export const getOllamaPendingArticles = async (
  limit = 10,
  offset = 0,
): Promise<OllamaPendingListResponse> => {
  const response = await api.get<OllamaPendingListResponse>("/ollama/pending", {
    params: { limit, offset },
  });
  return response.data;
};

export const getOllamaCategories = async (): Promise<string[]> => {
  const response = await api.get<string[]>("/ollama/categories");
  return response.data;
};

export const getOllamaCategoryAnalytics =
  async (): Promise<CategoryStatistic[]> => {
    const response = await api.get<CategoryStatistic[]>(
      "/ollama/analytics/categories",
    );
    return response.data;
  };

export default api;
