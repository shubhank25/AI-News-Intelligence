
/**
 * Purpose:
 * Provides the main navigation sidebar for the dashboard.
 * Dynamically adjusts its colors according to the selected theme.
 */

import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Newspaper,
  BrainCircuit,
  ChartNoAxesCombined,
  Radio,
} from "lucide-react";
import { useTheme } from "../../context/ThemeContext";

const navigation = [
  { name: "Dashboard", path: "/", icon: LayoutDashboard },
  { name: "All News", path: "/news", icon: Newspaper },
  { name: "AI Insights", path: "/ai-insights", icon: BrainCircuit },
  { name: "Analytics", path: "/analytics", icon: ChartNoAxesCombined },
];

function Sidebar() {
  const { theme } = useTheme();
  const isDark = theme === "dark";

  return (
    <aside
      className={`w-full border-b p-5 transition-colors md:min-h-screen md:w-64 md:border-b-0 md:border-r ${
        isDark
          ? "border-slate-800 bg-slate-900 text-slate-100"
          : "border-slate-200 bg-white text-slate-900"
      }`}
    >
      <div className="mb-8 flex items-center gap-3">
        <div className="rounded-xl bg-indigo-600 p-2 text-white">
          <Radio size={23} />
        </div>

        <div>
          <h1 className="text-lg font-bold">News Intelligence</h1>
          <p className={`text-xs ${isDark ? "text-slate-400" : "text-slate-500"}`}>
            AI-powered platform
          </p>
        </div>
      </div>

      <p
        className={`mb-3 text-xs font-semibold uppercase tracking-wider ${
          isDark ? "text-slate-500" : "text-slate-400"
        }`}
      >
        Workspace
      </p>

      <nav className="flex gap-2 overflow-x-auto md:flex-col">
        {navigation.map(({ name, path, icon: Icon }) => (
          <NavLink
            key={path}
            to={path}
            end={path === "/"}
            className={({ isActive }) =>
              `flex shrink-0 items-center gap-3 rounded-xl px-4 py-3 text-sm transition-colors ${
                isActive
                  ? "bg-indigo-600 text-white"
                  : isDark
                    ? "text-slate-400 hover:bg-slate-800 hover:text-white"
                    : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
              }`
            }
          >
            <Icon size={19} />
            {name}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}

export default Sidebar;
