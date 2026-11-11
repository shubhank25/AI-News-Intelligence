
/**
 * Purpose:
 * Displays the dashboard header with dynamic page titles,
 * system status, light/dark theme toggle, and notifications dropdown.
 */

import { useState } from "react";
import { useLocation } from "react-router-dom";
import {
  Activity,
  Bell,
  Sun,
  Moon,
  X,
} from "lucide-react";
import { useTheme } from "../../context/ThemeContext";

const pageTitles: Record<string, string> = {
  "/": "Dashboard Overview",
  "/news": "Latest News",
  "/ai-insights": "AI Insights",
  "/analytics": "News Analytics",
};

function Header() {
  const location = useLocation();
  const { theme, toggleTheme } = useTheme();

  const [showNotifications, setShowNotifications] = useState(false);

  const isDark = theme === "dark";
  const title = pageTitles[location.pathname] ?? "News Intelligence";

  const buttonStyle = isDark
    ? "border-slate-700 text-slate-300 hover:bg-slate-800"
    : "border-slate-200 text-slate-600 hover:bg-slate-100";

  return (
    <header
      className={`relative z-20 flex items-center justify-between border-b px-5 py-5 transition-colors md:px-8 ${
        isDark
          ? "border-slate-800 bg-slate-950 text-slate-100"
          : "border-slate-200 bg-white text-slate-900"
      }`}
    >
      {/* Page title */}
      <div>
        <h2 className="text-xl font-semibold">{title}</h2>
        <p className={`mt-1 text-xs ${isDark ? "text-slate-400" : "text-slate-500"}`}>
          Your AI-powered news intelligence workspace
        </p>
      </div>

      {/* Header actions */}
      <div className="flex items-center gap-3">

        {/* System status */}
        <span className="hidden items-center gap-2 text-xs text-emerald-500 sm:flex">
          <Activity size={16} />
          System online
        </span>

        {/* Theme toggle */}
        <button
          type="button"
          onClick={toggleTheme}
          title={isDark ? "Switch to light mode" : "Switch to dark mode"}
          aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
          className={`rounded-lg border p-2 transition-colors ${buttonStyle}`}
        >
          {isDark ? (
            <Sun size={20} className="text-amber-400" />
          ) : (
            <Moon size={20} className="text-indigo-600" />
          )}
        </button>

        {/* Notifications */}
        <div className="relative">
          <button
            type="button"
            onClick={() => setShowNotifications((current) => !current)}
            aria-label="Notifications"
            aria-expanded={showNotifications}
            title="Notifications"
            className={`relative rounded-lg border p-2 transition-colors ${buttonStyle}`}
          >
            <Bell size={20} />

            <span className="absolute right-1 top-1 h-2 w-2 rounded-full bg-red-500 ring-2 ring-white dark:ring-slate-950" />
          </button>

          {/* Notification dropdown */}
          {showNotifications && (
            <div
              className={`absolute right-0 top-12 z-50 w-80 overflow-hidden rounded-xl border shadow-xl ${
                isDark
                  ? "border-slate-700 bg-slate-900 text-slate-100"
                  : "border-slate-200 bg-white text-slate-900"
              }`}
            >
              <div className="flex items-center justify-between border-b border-inherit p-4">
                <h3 className="font-semibold">Notifications</h3>

                <button
                  type="button"
                  onClick={() => setShowNotifications(false)}
                  aria-label="Close notifications"
                  className="rounded p-1 text-slate-400 hover:bg-slate-700/20"
                >
                  <X size={18} />
                </button>
              </div>

              <div className="p-6 text-center">
                <Bell
                  size={28}
                  className={`mx-auto mb-3 ${
                    isDark ? "text-slate-500" : "text-slate-400"
                  }`}
                />

                <p className="text-sm font-medium">
                  No notifications yet
                </p>

                <p className={`mt-1 text-xs ${
                  isDark ? "text-slate-400" : "text-slate-500"
                }`}>
                  Your news and system updates will appear here.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

export default Header;
