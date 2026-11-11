
/**
 * Purpose:
 * Renders a reusable dashboard KPI card with an icon,
 * title, value and supporting description.
 * Supports both light and dark themes.
 */

import type { LucideIcon } from "lucide-react";
import { useTheme } from "../../context/ThemeContext";

interface StatCardProps {
  title: string;
  value: string | number;
  description: string;
  icon: LucideIcon;
  iconColor: string;
}

function StatCard({
  title,
  value,
  description,
  icon: Icon,
  iconColor,
}: StatCardProps) {
  const { theme } = useTheme();
  const isDark = theme === "dark";

  return (
    <div
      className={`rounded-2xl border p-5 shadow-sm transition-colors ${
        isDark
          ? "border-slate-800 bg-slate-900"
          : "border-slate-200 bg-white"
      }`}
    >
      <div className="flex items-center justify-between">
        <p className={`text-sm ${isDark ? "text-slate-400" : "text-slate-500"}`}>
          {title}
        </p>

        <div
          className={`rounded-xl p-3 ${
            isDark ? "bg-slate-800" : "bg-slate-100"
          } ${iconColor}`}
        >
          <Icon size={21} />
        </div>
      </div>

      <h3
        className={`mt-5 text-3xl font-bold ${
          isDark ? "text-white" : "text-slate-900"
        }`}
      >
        {value}
      </h3>

      <p className={`mt-2 text-xs ${isDark ? "text-slate-500" : "text-slate-500"}`}>
        {description}
      </p>
    </div>
  );
}

export default StatCard;
