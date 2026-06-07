import { useEffect, useState } from "react";
import { applicationsApi, jobsApi, cvApi } from "../api";
import { Send, Briefcase, FileText, CheckCircle, Clock, AlertCircle, TrendingUp } from "lucide-react";
import { Link } from "react-router-dom";

interface Stats {
  sent?: number;
  pending?: number;
  error?: number;
  customizing?: number;
  ready?: number;
}

export default function Dashboard() {
  const [stats, setStats] = useState<Stats>({});
  const [recentApps, setRecentApps] = useState<any[]>([]);
  const [jobCount, setJobCount] = useState(0);
  const [profileCount, setProfileCount] = useState(0);

  useEffect(() => {
    applicationsApi.stats().then((r) => setStats(r.data)).catch(() => {});
    applicationsApi.list({ limit: 5 }).then((r) => setRecentApps(r.data)).catch(() => {});
    jobsApi.list({ limit: 1 }).then((r) => setJobCount(r.data.length)).catch(() => {});
    cvApi.listProfiles().then((r) => setProfileCount(r.data.length)).catch(() => {});
  }, []);

  const total = Object.values(stats).reduce((a, b) => a + (b || 0), 0);

  const statCards = [
    { label: "Total Applied", value: total, icon: Send, color: "text-brand-400" },
    { label: "Emails Sent", value: stats.sent || 0, icon: CheckCircle, color: "text-green-400" },
    { label: "In Progress", value: (stats.pending || 0) + (stats.customizing || 0), icon: Clock, color: "text-yellow-400" },
    { label: "Errors", value: stats.error || 0, icon: AlertCircle, color: "text-red-400" },
  ];

  const statusColor: Record<string, string> = {
    sent: "bg-green-500/20 text-green-400",
    pending: "bg-yellow-500/20 text-yellow-400",
    error: "bg-red-500/20 text-red-400",
    customizing: "bg-blue-500/20 text-blue-400",
    ready: "bg-gray-500/20 text-gray-400",
    sending: "bg-purple-500/20 text-purple-400",
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-gray-400 text-sm mt-1">Your job application command center</p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="card flex items-center gap-4">
            <div className={`p-2.5 rounded-lg bg-gray-800 ${color}`}>
              <Icon size={20} />
            </div>
            <div>
              <p className="text-2xl font-bold">{value}</p>
              <p className="text-xs text-gray-400">{label}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold">Quick Actions</h2>
          </div>
          <div className="space-y-2">
            <Link to="/cv" className="flex items-center gap-3 p-3 bg-gray-800 rounded-lg hover:bg-gray-700 transition-colors">
              <FileText size={16} className="text-brand-400" />
              <div>
                <p className="text-sm font-medium">Upload your CV</p>
                <p className="text-xs text-gray-400">{profileCount} profile{profileCount !== 1 ? "s" : ""} loaded</p>
              </div>
            </Link>
            <Link to="/jobs" className="flex items-center gap-3 p-3 bg-gray-800 rounded-lg hover:bg-gray-700 transition-colors">
              <Briefcase size={16} className="text-green-400" />
              <div>
                <p className="text-sm font-medium">Search for jobs</p>
                <p className="text-xs text-gray-400">LinkedIn, RemoteOK, Arbeitnow & more</p>
              </div>
            </Link>
            <Link to="/applications" className="flex items-center gap-3 p-3 bg-gray-800 rounded-lg hover:bg-gray-700 transition-colors">
              <Send size={16} className="text-purple-400" />
              <div>
                <p className="text-sm font-medium">View applications</p>
                <p className="text-xs text-gray-400">{total} total applications</p>
              </div>
            </Link>
          </div>
        </div>

        <div className="card">
          <h2 className="font-semibold mb-4">Recent Applications</h2>
          {recentApps.length === 0 ? (
            <p className="text-gray-500 text-sm">No applications yet. Start by finding jobs.</p>
          ) : (
            <div className="space-y-2">
              {recentApps.map((app: any) => (
                <div key={app.id} className="flex items-center justify-between p-2.5 bg-gray-800 rounded-lg">
                  <div>
                    <p className="text-sm font-medium">{app.job?.title}</p>
                    <p className="text-xs text-gray-400">{app.job?.company}</p>
                  </div>
                  <span className={`badge ${statusColor[app.status] || "bg-gray-700 text-gray-300"}`}>
                    {app.status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="card">
        <div className="flex items-center gap-2 mb-3">
          <TrendingUp size={16} className="text-brand-400" />
          <h2 className="font-semibold">How it works</h2>
        </div>
        <ol className="grid grid-cols-1 md:grid-cols-4 gap-3">
          {[
            ["1. Upload CV", "Drop your PDF CV — Claude extracts all your experience"],
            ["2. Search Jobs", "Find jobs across LinkedIn, RemoteOK, Arbeitnow, and more"],
            ["3. AI Customizes", "Claude tailors your CV + writes a human cover letter per job"],
            ["4. Auto Apply", "Sends email or applies directly on company portal"],
          ].map(([title, desc]) => (
            <div key={title} className="bg-gray-800 rounded-lg p-3">
              <p className="text-xs font-semibold text-brand-400">{title}</p>
              <p className="text-xs text-gray-400 mt-1">{desc}</p>
            </div>
          ))}
        </ol>
      </div>
    </div>
  );
}
