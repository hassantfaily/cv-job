import { Routes, Route, NavLink, useLocation } from "react-router-dom";
import { LayoutDashboard, FileText, Search, Send, Settings, Bot } from "lucide-react";
import clsx from "clsx";
import Dashboard from "./pages/Dashboard";
import CVPage from "./pages/CVPage";
import JobsPage from "./pages/JobsPage";
import ApplicationsPage from "./pages/ApplicationsPage";
import SettingsPage from "./pages/SettingsPage";

const navItems = [
  { to: "/", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/cv", icon: FileText, label: "My CV" },
  { to: "/jobs", icon: Search, label: "Find Jobs" },
  { to: "/applications", icon: Send, label: "Applications" },
  { to: "/settings", icon: Settings, label: "Settings" },
];

export default function App() {
  return (
    <div className="flex h-screen overflow-hidden">
      <aside className="w-56 bg-gray-900 border-r border-gray-800 flex flex-col shrink-0">
        <div className="p-5 border-b border-gray-800">
          <div className="flex items-center gap-2">
            <Bot className="text-brand-500" size={22} />
            <span className="font-bold text-lg tracking-tight">JobBot</span>
          </div>
          <p className="text-xs text-gray-500 mt-0.5">AI-powered applications</p>
        </div>
        <nav className="flex-1 p-3 space-y-0.5">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) =>
                clsx(
                  "flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                  isActive
                    ? "bg-brand-600 text-white"
                    : "text-gray-400 hover:text-gray-100 hover:bg-gray-800"
                )
              }
            >
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="p-3 border-t border-gray-800">
          <p className="text-xs text-gray-600 text-center">v1.0.0</p>
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto bg-gray-950">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/cv" element={<CVPage />} />
          <Route path="/jobs" element={<JobsPage />} />
          <Route path="/applications" element={<ApplicationsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </main>
    </div>
  );
}
