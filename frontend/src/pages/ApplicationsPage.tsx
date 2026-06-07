import { useState, useEffect } from "react";
import { applicationsApi } from "../api";
import { Download, RefreshCw, CheckCircle, Clock, AlertCircle, Send, Loader } from "lucide-react";
import { formatDistanceToNow } from "date-fns";

const STATUS_CONFIG: Record<string, { label: string; color: string; icon: any }> = {
  sent: { label: "Sent", color: "bg-green-500/20 text-green-400", icon: CheckCircle },
  pending: { label: "Pending", color: "bg-yellow-500/20 text-yellow-400", icon: Clock },
  customizing: { label: "Customizing", color: "bg-blue-500/20 text-blue-400", icon: Loader },
  sending: { label: "Sending", color: "bg-purple-500/20 text-purple-400", icon: Send },
  ready: { label: "Ready", color: "bg-gray-500/20 text-gray-400", icon: CheckCircle },
  error: { label: "Error", color: "bg-red-500/20 text-red-400", icon: AlertCircle },
  portal_pending: { label: "Portal", color: "bg-orange-500/20 text-orange-400", icon: Clock },
};

export default function ApplicationsPage() {
  const [apps, setApps] = useState<any[]>([]);
  const [stats, setStats] = useState<Record<string, number>>({});
  const [filter, setFilter] = useState("all");
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const params = filter !== "all" ? { status: filter } : {};
      const [appsR, statsR] = await Promise.all([
        applicationsApi.list({ ...params, limit: 100 }),
        applicationsApi.stats(),
      ]);
      setApps(appsR.data);
      setStats(statsR.data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [filter]);

  const total = Object.values(stats).reduce((a, b) => a + b, 0);

  return (
    <div className="p-6 space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Applications</h1>
          <p className="text-gray-400 text-sm mt-1">{total} total applications tracked</p>
        </div>
        <button onClick={load} className="btn-secondary flex items-center gap-2">
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
          Refresh
        </button>
      </div>

      <div className="flex gap-2 flex-wrap">
        {[{ id: "all", label: `All (${total})` },
          ...Object.entries(stats).map(([k, v]) => ({ id: k, label: `${STATUS_CONFIG[k]?.label || k} (${v})` }))
        ].map(({ id, label }) => (
          <button key={id} onClick={() => setFilter(id)}
            className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
              filter === id ? "bg-brand-600 text-white" : "bg-gray-800 text-gray-400 hover:bg-gray-700"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="space-y-2">
        {apps.length === 0 && !loading && (
          <div className="card text-center text-gray-500 py-12">
            No applications yet. Go to Find Jobs to start applying.
          </div>
        )}
        {apps.map((app: any) => {
          const cfg = STATUS_CONFIG[app.status] || STATUS_CONFIG.pending;
          const Icon = cfg.icon;
          const isExpanded = expanded === app.id;

          return (
            <div key={app.id} className="card">
              <div className="flex items-center justify-between cursor-pointer"
                onClick={() => setExpanded(isExpanded ? null : app.id)}>
                <div className="flex items-center gap-3">
                  <div className={`p-1.5 rounded-lg ${cfg.color}`}>
                    <Icon size={14} className={app.status === "customizing" ? "animate-spin" : ""} />
                  </div>
                  <div>
                    <p className="font-medium text-sm">{app.job?.title}</p>
                    <p className="text-xs text-gray-400">
                      {app.job?.company} · {app.method === "email" ? `📧 ${app.email_to || "no email"}` : "🌐 portal"}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3 text-right">
                  <div>
                    <span className={`badge ${cfg.color}`}>{cfg.label}</span>
                    <p className="text-xs text-gray-500 mt-0.5">
                      {app.created_at ? formatDistanceToNow(new Date(app.created_at), { addSuffix: true }) : ""}
                    </p>
                  </div>
                </div>
              </div>

              {isExpanded && (
                <div className="mt-4 pt-4 border-t border-gray-800 space-y-3">
                  {app.subject && (
                    <div>
                      <p className="text-xs text-gray-500 font-medium">Email Subject</p>
                      <p className="text-sm mt-0.5">{app.subject}</p>
                    </div>
                  )}
                  {app.cover_letter_text && (
                    <div>
                      <p className="text-xs text-gray-500 font-medium">Cover Letter Preview</p>
                      <p className="text-xs text-gray-300 mt-1 leading-relaxed line-clamp-4 whitespace-pre-line">
                        {app.cover_letter_text}
                      </p>
                    </div>
                  )}
                  {app.error && (
                    <div className="bg-red-950/40 border border-red-800 rounded-lg p-3">
                      <p className="text-xs text-red-400 font-medium">Error</p>
                      <p className="text-xs text-red-300 mt-0.5">{app.error}</p>
                    </div>
                  )}
                  <div className="flex gap-2">
                    <a href={applicationsApi.downloadCv(app.id)} target="_blank" rel="noopener noreferrer"
                      className="btn-secondary text-xs flex items-center gap-1.5 py-1.5">
                      <Download size={12} /> Custom CV
                    </a>
                    <a href={applicationsApi.downloadCl(app.id)} target="_blank" rel="noopener noreferrer"
                      className="btn-secondary text-xs flex items-center gap-1.5 py-1.5">
                      <Download size={12} /> Cover Letter
                    </a>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
