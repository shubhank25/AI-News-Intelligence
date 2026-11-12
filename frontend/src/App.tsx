
/**
 * Purpose:
 * Defines the main application layout and route configuration.
 * Wraps all application pages and shared components inside
 * ThemeProvider so every component can access the selected theme.
 */

import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import Sidebar from "./components/layout/Sidebar";
import Header from "./components/layout/Header";

import Dashboard from "./pages/Dashboard";
import News from "./pages/News";
import AIInsights from "./pages/AIInsights";
import Analytics from "./pages/Analytics";

import { ThemeProvider, useTheme } from "./context/ThemeContext";
import { AIModelProvider } from "./context/AIModelContext";

import { useEffect } from "react";
import { useLocation } from "react-router-dom";

function AppLayout() {
  const { theme } = useTheme();
  const location = useLocation();

  useEffect(() => {
    const pageTitles: Record<string, string> = {
      "/": "Dashboard",
      "/news": "News",
      "/ai-insights": "AI Insights",
      "/analytics": "Analytics",
    };

    const currentPage = pageTitles[location.pathname] || "Dashboard";

    document.title = `News Intelligence - ${currentPage}`;
  }, [location.pathname]);

  return (
    <div
      className={`min-h-screen md:flex ${theme === "dark"
          ? "bg-slate-950 text-slate-100"
          : "bg-slate-50 text-slate-900"
        }`}
    >
      <Sidebar />

      <div className="min-w-0 flex-1">
        <Header />

        <main className="p-5 md:p-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/news" element={<News />} />
            <Route path="/ai-insights" element={<AIInsights />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

function App() {
  return (
    <ThemeProvider>
      <AIModelProvider>
        <BrowserRouter>
          <AppLayout />
        </BrowserRouter>
      </AIModelProvider>
    </ThemeProvider>
  );
}

export default App;
