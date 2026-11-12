
/**
 * Purpose:
 * Centralizes HTTP communication with the FastAPI backend.
 * Provides reusable methods for fetching news and statistics.
 */

import axios from "axios";
import type { NewsArticle, NewsStatistics } from "../types/news";

import type {
  CategoryStatistic,
  PublishingTrend,
} from "../types/news";

import type {
  OllamaAnalysisListResponse,
  OllamaAnalysisStatus,
  OllamaAnalyzedArticle,
  OllamaPendingListResponse,
} from "../types/news";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "/api",
  timeout: 120000,
});

export const getNewsStatistics = async (): Promise<NewsStatistics> => {
  const response = await api.get<NewsStatistics>("/news/stats");
  return response.data;
};

export const getLatestNews = async (
  limit = 5,
): Promise<NewsArticle[]> => {
  const response = await api.get<NewsArticle[]>("/news", {
    params: { limit, offset: 0 },
  });

  return response.data;
};

/**
 * Purpose:
 * Fetches paginated news articles with an optional category filter.
 */

export const getNewsArticles = async (
  limit = 10,
  offset = 0,
  category?: string,
): Promise<NewsArticle[]> => {
  const response = await api.get<NewsArticle[]>("/news", {
    params: {
      limit,
      offset,
      ...(category ? { category } : {}),
    },
  });

  return response.data;
};


/**
 * Purpose:
 * Provides API methods for retrieving news categories and
 * filtering articles by AI-generated sentiment.
 */

export const getNewsCategories = async (): Promise<string[]> => {
  const response = await api.get<string[]>("/news/categories");
  return response.data;
};

export const getNewsBySentiment = async (
  sentiment: "positive" | "negative" | "neutral",
  limit = 100,
  offset = 0,
): Promise<NewsArticle[]> => {
  const response = await api.get<NewsArticle[]>(
    `/news/ai/sentiment/${sentiment}`,
    { params: { limit, offset } },
  );

  return response.data;
};


/**
 * Purpose:
 * Retrieves news articles belonging to a selected AI-generated category.
 */

export const getNewsByCategory = async (
  category: string,
  limit = 100,
  offset = 0,
): Promise<NewsArticle[]> => {
  const response = await api.get<NewsArticle[]>(
    `/news/ai/category/${encodeURIComponent(category)}`,
    { params: { limit, offset } },
  );

  return response.data;
};


/**
 * Purpose:
 * Fetches distinct AI-generated news categories from the backend
 * for the All News page category filter.
 */
export const getAICategories = async (): Promise<string[]> => {
  const response = await api.get<string[]>("/news/ai/categories");
  return response.data;
};


/**
 * Purpose:
 * Retrieves AI-analyzed and AI-pending news articles.
 * These functions power the AI Insights dashboard.
 */
export const getAIAnalyzedArticles = async (
  limit = 10,
  offset = 0
): Promise<NewsArticle[]> => {
  const response = await api.get<NewsArticle[]>("/news/ai/analyzed", {
    params: { limit, offset },
  });

  return response.data;
};

export const getAIPendingArticles = async (
  limit = 10,
  offset = 0
): Promise<NewsArticle[]> => {
  const response = await api.get<NewsArticle[]>("/news/ai/pending", {
    params: { limit, offset },
  });

  return response.data;
};

/**
 * Purpose:
 * Fetches AI-generated category-wise article counts
 * for the News Analytics dashboard.
 */
export const getCategoryAnalytics = async (): Promise<CategoryStatistic[]> => {
  const response = await api.get<CategoryStatistic[]>(
    "/news/analytics/categories"
  );

  return response.data;
};

/**
 * Purpose:
 * Fetches daily article publishing counts for the
 * News Analytics dashboard, with optional date filters.
 */
export const getPublishingTrends = async (
  dateFrom?: string,
  dateTo?: string
): Promise<PublishingTrend[]> => {
  const response = await api.get<PublishingTrend[]>(
    "/news/analytics/publishing-trends",
    {
      params: {
        date_from: dateFrom,
        date_to: dateTo,
      },
    }
  );

  return response.data;
};


/**
 * Purpose:
 * Retrieves Ollama-generated article analyses and processing status.
 * These endpoints are separate from the existing Gemini APIs.
 */

export const getOllamaAnalyses = async (
  limit = 10,
  offset = 0,
): Promise<OllamaAnalysisListResponse> => {
  const response = await api.get<OllamaAnalysisListResponse>(
    "/ollama/analyses",
    {
      params: { limit, offset },
    },
  );

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
    const response = await api.get<OllamaAnalysisStatus>(
      "/ollama/status",
    );

    return response.data;
  };

/**
* Purpose:
* Retrieves pending articles waiting for ShubhAI analysis.
*/
export const getOllamaPendingArticles = async (
  limit = 10,
  offset = 0,
): Promise<OllamaPendingListResponse> => {
  const response = await api.get<OllamaPendingListResponse>(
    "/ollama/pending",
    {
      params: { limit, offset },
    },
  );

  return response.data;
};

export default api;
