
/**
 * Purpose:
 * Visualizes positive, negative and neutral news sentiment
 * using a responsive donut chart with light/dark theme support.
 */

import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
} from "recharts";

import type { SentimentDistribution } from "../../types/news";
import { useTheme } from "../../context/ThemeContext";

interface SentimentChartProps {
  data: SentimentDistribution;
}

const COLORS = ["#10b981", "#f43f5e", "#64748b"];

function SentimentChart({ data }: SentimentChartProps) {
  const { theme } = useTheme();
  const isDark = theme === "dark";

  const chartData = [
    { name: "Positive", value: data.positive },
    { name: "Negative", value: data.negative },
    { name: "Neutral", value: data.neutral },
  ];

  const hasData = chartData.some((item) => item.value > 0);

  const textColor = isDark ? "#cbd5e1" : "#475569";
  const tooltipBackground = isDark ? "#0f172a" : "#ffffff";
  const tooltipBorder = isDark ? "#334155" : "#e2e8f0";

  return (
    <div
      className={`rounded-2xl border p-5 shadow-sm transition-colors ${
        isDark
          ? "border-slate-800 bg-slate-900"
          : "border-slate-200 bg-white"
      }`}
    >
      <h3 className={`text-lg font-semibold ${isDark ? "text-white" : "text-slate-900"}`}>
        Sentiment Distribution
      </h3>

      <p className={`mt-1 text-sm ${isDark ? "text-slate-400" : "text-slate-500"}`}>
        AI-classified news sentiment
      </p>

      <div className="mt-5 h-72">
        {hasData ? (
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="45%"
                innerRadius={65}
                outerRadius={95}
                paddingAngle={4}
              >
                {chartData.map((entry, index) => (
                  <Cell key={entry.name} fill={COLORS[index]} />
                ))}
              </Pie>

              <Tooltip
                contentStyle={{
                  backgroundColor: tooltipBackground,
                  border: `1px solid ${tooltipBorder}`,
                  borderRadius: "10px",
                  color: textColor,
                }}
                itemStyle={{ color: textColor }}
                labelStyle={{ color: textColor }}
              />

              <Legend
                formatter={(value) => (
                  <span style={{ color: textColor }}>{value}</span>
                )}
              />
            </PieChart>
          </ResponsiveContainer>
        ) : (
          <div
            className={`flex h-full items-center justify-center text-sm ${
              isDark ? "text-slate-500" : "text-slate-400"
            }`}
          >
            No sentiment data available yet.
          </div>
        )}
      </div>
    </div>
  );
}

export default SentimentChart;
