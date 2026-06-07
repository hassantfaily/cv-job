import { useState, useEffect, useCallback } from "react";
import { cvApi } from "../api";
import { Upload, CheckCircle, Loader, User, Briefcase, GraduationCap, Code } from "lucide-react";

export default function CVPage() {
  const [profiles, setProfiles] = useState<any[]>([]);
  const [selected, setSelected] = useState<any>(null);
  const [uploading, setUploading] = useState(false);
  const [parsing, setParsing] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [taskId, setTaskId] = useState<string | null>(null);

  const loadProfiles = () =>
    cvApi.listProfiles().then((r) => {
      setProfiles(r.data);
      if (r.data.length > 0 && !selected) loadProfile(r.data[0].id);
    });

  const loadProfile = (id: string) =>
    cvApi.getProfile(id).then((r) => setSelected(r.data));

  useEffect(() => { loadProfiles(); }, []);

  useEffect(() => {
    if (!taskId) return;
    const iv = setInterval(() => {
      if (profiles.length > 0) {
        cvApi.getProfile(profiles[0].id).then((r) => {
          if (r.data.structured) {
            setSelected(r.data);
            setParsing(false);
            setTaskId(null);
            clearInterval(iv);
          }
        });
      }
    }, 2000);
    return () => clearInterval(iv);
  }, [taskId, profiles]);

  const handleFile = async (file: File) => {
    if (!file.name.endsWith(".pdf")) return alert("Only PDF files please");
    setUploading(true);
    try {
      const r = await cvApi.upload(file);
      setTaskId(r.data.task_id);
      setParsing(true);
      await loadProfiles();
    } finally {
      setUploading(false);
    }
  };

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }, []);

  const s = selected?.structured;

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">My CV</h1>
        <p className="text-gray-400 text-sm mt-1">Upload your PDF CV — Claude will extract and structure everything</p>
      </div>

      <div
        className={`border-2 border-dashed rounded-xl p-10 text-center transition-colors cursor-pointer ${
          dragOver ? "border-brand-500 bg-brand-500/5" : "border-gray-700 hover:border-gray-600"
        }`}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        onClick={() => document.getElementById("cv-input")?.click()}
      >
        <input
          id="cv-input"
          type="file"
          accept=".pdf"
          className="hidden"
          onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
        />
        {uploading || parsing ? (
          <div className="flex flex-col items-center gap-3">
            <Loader className="animate-spin text-brand-400" size={32} />
            <p className="text-sm text-gray-400">
              {uploading ? "Uploading…" : "Claude is parsing your CV…"}
            </p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3">
            <Upload className="text-gray-500" size={32} />
            <p className="text-sm text-gray-300">Drop your CV here or click to browse</p>
            <p className="text-xs text-gray-500">PDF only · Claude extracts all data automatically</p>
          </div>
        )}
      </div>

      {profiles.length > 0 && (
        <div className="flex gap-2 flex-wrap">
          {profiles.map((p: any) => (
            <button
              key={p.id}
              onClick={() => loadProfile(p.id)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                selected?.id === p.id ? "bg-brand-600 text-white" : "bg-gray-800 text-gray-300 hover:bg-gray-700"
              }`}
            >
              {p.name}
            </button>
          ))}
        </div>
      )}

      {s && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="card space-y-4 lg:col-span-1">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-brand-600 rounded-full flex items-center justify-center text-lg font-bold">
                {s.name?.charAt(0) || "?"}
              </div>
              <div>
                <p className="font-semibold">{s.name}</p>
                <p className="text-xs text-gray-400">{s.email}</p>
                <p className="text-xs text-gray-400">{s.phone}</p>
              </div>
            </div>
            {s.summary && (
              <div>
                <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">Summary</p>
                <p className="text-xs text-gray-300 leading-relaxed">{s.summary}</p>
              </div>
            )}
            {s.skills?.length > 0 && (
              <div>
                <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-2">Skills</p>
                <div className="flex flex-wrap gap-1">
                  {s.skills.map((sk: string) => (
                    <span key={sk} className="badge bg-brand-900 text-brand-300">{sk}</span>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="lg:col-span-2 space-y-4">
            {s.experience?.length > 0 && (
              <div className="card">
                <div className="flex items-center gap-2 mb-3">
                  <Briefcase size={15} className="text-brand-400" />
                  <h3 className="font-semibold text-sm">Experience</h3>
                </div>
                <div className="space-y-3">
                  {s.experience.map((exp: any, i: number) => (
                    <div key={i} className="border-l-2 border-brand-600 pl-3">
                      <p className="font-medium text-sm">{exp.title}</p>
                      <p className="text-xs text-gray-400">{exp.company} · {exp.start_date} – {exp.end_date}</p>
                      {exp.achievements?.slice(0, 2).map((a: string, j: number) => (
                        <p key={j} className="text-xs text-gray-300 mt-1">• {a}</p>
                      ))}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {s.education?.length > 0 && (
              <div className="card">
                <div className="flex items-center gap-2 mb-3">
                  <GraduationCap size={15} className="text-green-400" />
                  <h3 className="font-semibold text-sm">Education</h3>
                </div>
                {s.education.map((edu: any, i: number) => (
                  <div key={i} className="border-l-2 border-green-600 pl-3 mb-2">
                    <p className="font-medium text-sm">{edu.degree}</p>
                    <p className="text-xs text-gray-400">{edu.institution} · {edu.end_date}</p>
                  </div>
                ))}
              </div>
            )}

            {s.projects?.length > 0 && (
              <div className="card">
                <div className="flex items-center gap-2 mb-3">
                  <Code size={15} className="text-purple-400" />
                  <h3 className="font-semibold text-sm">Projects</h3>
                </div>
                {s.projects.map((p: any, i: number) => (
                  <div key={i} className="mb-2">
                    <p className="font-medium text-sm">{p.name}</p>
                    <p className="text-xs text-gray-400">{p.description}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
