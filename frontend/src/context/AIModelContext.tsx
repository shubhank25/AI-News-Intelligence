
/**
 * Purpose:
 * Provides global AI model selection state across the application.
 * Persists the selected model using localStorage so navigation
 * and browser refresh do not reset the selection.
 */

import {
  createContext,
  useContext,
  useState,
  type ReactNode,
} from "react";

export type AIProvider = "shubhAI" | "gemini";

interface AIModelContextType {
  aiProvider: AIProvider;
  setAIProvider: (provider: AIProvider) => void;
}

const STORAGE_KEY = "news-ai-provider";

const AIModelContext = createContext<AIModelContextType | undefined>(undefined);

export function AIModelProvider({ children }: { children: ReactNode }) {
  const [aiProvider, setAIProviderState] = useState<AIProvider>(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    return saved === "gemini" ? "gemini" : "shubhAI";
  });

  const setAIProvider = (provider: AIProvider) => {
    localStorage.setItem(STORAGE_KEY, provider);
    setAIProviderState(provider);
  };

  return (
    <AIModelContext.Provider value={{ aiProvider, setAIProvider }}>
      {children}
    </AIModelContext.Provider>
  );
}

export function useAIModel() {
  const context = useContext(AIModelContext);

  if (!context) {
    throw new Error("useAIModel must be used inside AIModelProvider");
  }

  return context;
}
