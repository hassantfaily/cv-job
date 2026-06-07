import { useState, useEffect } from "react";
import { jobsApi, applicationsApi, cvApi, linkedinApi } from "../api";
import { Search, MapPin, ExternalLink, Send, Loader, CheckCircle, Globe, Linkedin } from "lucide-react";

const SOURCES = [
  { id: "remoteok", label: "RemoteOK", icon: "🌍" },
  { id: "arbeitnow", label: "Arbeitnow", icon: "🇩🇪" },
  { id: "themuse", label: "TheMuse", icon: "✨" },
  { id: "linkedin", label: "LinkedIn", icon: "🔗" },
];

export default function JobsPage() {
  const [jobs, setJobs] = useState<any[]>([]);
  const [profiles, setProfiles] = useState<any[]>([]);
  const [profileId, setProfileId] = useState("");
  const [query, setQuery] = useState("");
  const [location, setLocation] = useState("");
  const [sources, setSources] = useState(["remoteok", "arbeitnow", "themuse"]);
  const [searching, setSearching] = useState(false);
  const [applying, setApplying] = useState<Record<string, boolean>>({});
  const [applied, setApplied] = useState<Record<string, boolean>>({});
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [bulkApplying, setBulkApplying] = useState(false);
  const [method, setMethod] = useState("email");

  useEffect(() => {
    jobsApi.list({ limit: 50 }).then((r) => setJobs(r.data)).catch(() => {});
    cvApi.listProfiles().then((r) => {
      setProfiles(r.data);
      if (r.data.length > 0) setProfileId(r.data[0].id);
    }).catch(() => {});
  }, []);

  const toggleSource = (id: string) =>
    setSources((s) => s.includes(id) ? s.filter((x) => x !== id) : [...s, id]);

  const toggleSelect = (id: string) =>
    setSelected((s) => { const n = new Set(s); n.has(id) ? n.delete(id) : n.add(id); return n; });

  const doSearch = async () => {
    if (!query) return;
    setSearching(true);
    try {
      const apiSources = sources.filter((s) => s !== "linkedin");
      let newJobs: any[] = [];

      if (apiSources.length > 0) {
        const r = await jobsApi.search(query, location, apiSources);
        const runId = r.data.search_run_id;
        await new Promise<void>((resolve) => {
          const iv = setInterval(async () => {
            const status = await jobsApi.searchStatus(runId);
            if (status.data.status === "completed") { clearInterval(iv); resolve(); }
          }, 2000);
        });
      }

      if (sources.includes("linkedin")) {
        try {
          const lr = await linkedinApi.search(query, location);
          newJobs = lr.data.jobs || [];
        } catch {}
      }

      const all = await jobsApi.list({ limit: 100 });
      setJobs([...newJobs, ...all.data]);
    } finally {
      setSearching(false);
    }
  };

  const applyJob = async (job: any) => {
    if (!profileId) return alert("Upload your CV first");
    setApplying((a) => ({ ...a, [job.id]: true }));
    try {
      await applicationsApi.create(job.id, profileId, method, job.hr_email);
      setApplied((a) => ({ ...a, [job.id]: true }));
    } finally {
      setApplying((a) => ({ ...a, [job.id]: false }));
    }
  };

  const bulkApply = async () => {
    if (!profileId) return alert("Upload your CV first");
    if (selected.size === 0) return;
    setBulkApplying(true);
    try {
      const jobIds = Array.from(selected).filter((id) => !applied[id]);
      for (const jid of jobIds) {
        const job = jobs.find((j) => j.id === jid);
        if (job) await applicationsApi.create(jid, profileId, method, job.hr_email);
      }
      const newApplied = { ...applied };
      jobIds.forEach((id) => { newApplied[id] = true; });
      setApplied(newApplied);
      setSelected(new Set());
    } finally {
      setBulkApplying(false);
    }
  };

  const sourceColor: Record<string, string> = {
    linkedin: "bg-blue-900/40 text-blue-300",
    remoteok: "bg-green-900/40 text-green-300",
    arbeitnow: "bg-orange-900/40 text-orange-300",
    themuse: "bg-purple-900/40 text-purple-300",
  };

  return (
    <div className="p-6 space-y-5">
      <div>
        <h1 className="text-2xl font-bold">Find Jobs</h1>
        <p className="text-gray-400 text-sm mt-1">Search across multiple platforms simultaneously</p>
      </div>

      <div className="card space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div className="md:col-span-2">
            <label className="label">Job title or keywords</label>
            <input className="input" placeholder="e.g. Software Engineer, Product Manager"
              value={query} onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && doSearch()} />
          </div>
          <div>
            <label className="label">Location (optional)</label>
            <input className="input" placeholder="e.g. Remote, London, Berlin"
              value={location} onChange={(e) => setLocation(e.target.value)} />
          </div>
        </div>

        <div>
          <label className="label">Sources</label>
          <div className="flex gap-2 flex-wrap">
            {SOURCES.map(({ id, label, icon }) => (
              <button key={id}
                onClick={() => toggleSource(id)}
                className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
                  sources.includes(id) ? "bg-brand-600 text-white" : "bg-gray-800 text-gray-400 hover:bg-gray-700"
                }`}
              >
                {icon} {label}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button onClick={doSearch} disabled={searching || !query} className="btn-primary flex items-center gap-2">
            {searching ? <Loader size={14} className="animate-spin" /> : <Search size={14} />}
            {searching ? "Searching…" : "Search Jobs"}
          </button>

          {profiles.length > 0 && (
            <select className="input w-auto"
              value={profileId} onChange={(e) => setProfileId(e.target.value)}>
              {profiles.map((p: any) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          )}

          <select className="input w-auto" value={method} onChange={(e) => setMethod(e.target.value)}>
            <option value="email">📧 Via Email</option>
            <option value="portal">🌐 Via Portal</option>
          </select>

          {selected.size > 0 && (
            <button onClick={bulkApply} disabled={bulkApplying}
              className="btn-primary flex items-center gap-2 ml-auto">
              {bulkApplying ? <Loader size={14} className="animate-spin" /> : <Send size={14} />}
              Apply to {selected.size} selected
            </button>
          )}
        </div>
      </div>

      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-400">{jobs.length} jobs found</p>
        {jobs.length > 0 && (
          <button onClick={() => setSelected(jobs.length === selected.size ? new Set() : new Set(jobs.map((j) => j.id)))}
            className="text-xs text-brand-400 hover:text-brand-300">
            {selected.size === jobs.length ? "Deselect all" : "Select all"}
          </button>
        )}
      </div>

      <div className="space-y-3">
        {jobs.map((job: any) => (
          <div key={job.id || job.source_url}
            className={`card flex items-start gap-3 cursor-pointer transition-all ${
              selected.has(job.id) ? "border-brand-500 bg-brand-950/20" : ""
            }`}
            onClick={() => job.id && toggleSelect(job.id)}
          >
            <input type="checkbox" readOnly checked={selected.has(job.id)}
              className="mt-1 accent-brand-500 shrink-0" />
            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <p className="font-medium">{job.title}</p>
                  <p className="text-sm text-gray-400">{job.company}</p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <span className={`badge ${sourceColor[job.source] || "bg-gray-700 text-gray-400"}`}>
                    {job.source}
                  </span>
                  {job.source_url && (
                    <a href={job.source_url} target="_blank" rel="noopener noreferrer"
                      onClick={(e) => e.stopPropagation()}
                      className="text-gray-500 hover:text-gray-300">
                      <ExternalLink size={14} />
                    </a>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-3 mt-1.5 text-xs text-gray-500">
                {job.location && <span className="flex items-center gap-1"><MapPin size={11} />{job.location}</span>}
                {job.salary_range && <span>💰 {job.salary_range}</span>}
                {job.job_type && <span>📍 {job.job_type}</span>}
                {job.hr_email && <span className="text-green-400">✉ {job.hr_email}</span>}
              </div>
            </div>
            <button
              onClick={(e) => { e.stopPropagation(); applyJob(job); }}
              disabled={applying[job.id] || applied[job.id] || !job.id}
              className={`shrink-0 btn-primary text-xs py-1.5 px-3 flex items-center gap-1.5 ${
                applied[job.id] ? "bg-green-600 hover:bg-green-600" : ""
              }`}
            >
              {applying[job.id] ? <Loader size={12} className="animate-spin" /> :
               applied[job.id] ? <CheckCircle size={12} /> : <Send size={12} />}
              {applying[job.id] ? "Applying…" : applied[job.id] ? "Applied" : "Apply"}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
