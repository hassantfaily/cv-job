import { useState, useEffect } from "react";
import { settingsApi } from "../api";
import { CheckCircle, AlertCircle, Loader, Mail, User, Bot } from "lucide-react";

export default function SettingsPage() {
  const [settings, setSettings] = useState<any>(null);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; error?: string } | null>(null);

  useEffect(() => {
    settingsApi.get().then((r) => setSettings(r.data)).catch(() => {});
  }, []);

  const testEmail = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const r = await settingsApi.testEmail();
      setTestResult(r.data);
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-gray-400 text-sm mt-1">Configure your email and personal details in the .env file</p>
      </div>

      {settings ? (
        <div className="space-y-4">
          <div className="card">
            <div className="flex items-center gap-2 mb-4">
              <Mail size={16} className="text-brand-400" />
              <h2 className="font-semibold">Email Configuration</h2>
              <span className={`ml-auto badge ${settings.email.configured ? "bg-green-500/20 text-green-400" : "bg-red-500/20 text-red-400"}`}>
                {settings.email.configured ? "✓ Configured" : "⚠ Not configured"}
              </span>
            </div>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <p className="label">Provider</p>
                <p className="font-medium capitalize">{settings.email.provider}</p>
              </div>
              <div>
                <p className="label">Send as</p>
                <p className="font-medium">{settings.email.display_name || "—"}</p>
              </div>
              <div className="col-span-2">
                <p className="label">Email address</p>
                <p className="font-medium">{settings.email.address || "—"}</p>
              </div>
            </div>
            <div className="mt-4 pt-4 border-t border-gray-800">
              <button onClick={testEmail} disabled={testing || !settings.email.configured}
                className="btn-primary flex items-center gap-2">
                {testing ? <Loader size={14} className="animate-spin" /> : <Mail size={14} />}
                {testing ? "Sending test…" : "Send test email"}
              </button>
              {testResult && (
                <div className={`mt-2 flex items-center gap-2 text-sm ${testResult.success ? "text-green-400" : "text-red-400"}`}>
                  {testResult.success ? <CheckCircle size={14} /> : <AlertCircle size={14} />}
                  {testResult.success ? "Test email sent! Check your inbox." : testResult.error}
                </div>
              )}
            </div>
          </div>

          <div className="card">
            <div className="flex items-center gap-2 mb-4">
              <User size={16} className="text-green-400" />
              <h2 className="font-semibold">Personal Info</h2>
              <span className="ml-auto badge bg-green-500/20 text-green-400 text-xs">
                {settings.user.source}
              </span>
            </div>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <p className="label">Name</p>
                <p className="font-medium">{settings.user.name || "—"}</p>
              </div>
              <div>
                <p className="label">Email</p>
                <p className="font-medium">{settings.user.email || "—"}</p>
              </div>
              <div>
                <p className="label">Phone</p>
                <p className="font-medium">{settings.user.phone || "—"}</p>
              </div>
              <div>
                <p className="label">Location</p>
                <p className="font-medium">{settings.user.location || "—"}</p>
              </div>
              <div>
                <p className="label">LinkedIn</p>
                <p className="font-medium truncate">{settings.user.linkedin_url || "—"}</p>
              </div>
              <div>
                <p className="label">GitHub</p>
                <p className="font-medium truncate">{settings.user.github_url || "—"}</p>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center gap-2 mb-4">
              <Bot size={16} className="text-purple-400" />
              <h2 className="font-semibold">AI (Claude)</h2>
              <span className={`ml-auto badge ${settings.ai.configured ? "bg-green-500/20 text-green-400" : "bg-red-500/20 text-red-400"}`}>
                {settings.ai.configured ? "✓ API key set" : "⚠ No API key"}
              </span>
            </div>
            <p className="text-sm text-gray-400">Provider: <span className="text-gray-200">{settings.ai.provider}</span> · Model: <span className="text-gray-200">{settings.ai.model}</span></p>
            <p className="text-xs text-gray-500 mt-2">
              GPT reads every job description and writes a completely unique, human-sounding CV and cover letter for each application.
            </p>
          </div>

          <div className="card border-dashed border-gray-700">
            <h2 className="font-semibold mb-2">How to configure</h2>
            <ol className="text-sm text-gray-400 space-y-1.5">
              <li>1. Copy <code className="text-brand-300 bg-gray-800 px-1 rounded">.env.example</code> to <code className="text-brand-300 bg-gray-800 px-1 rounded">.env</code></li>
              <li>2. Set your <code className="text-green-300 bg-gray-800 px-1 rounded">OPENAI_API_KEY</code></li>
              <li>3. Set your Gmail/iCloud App Password in <code className="text-green-300 bg-gray-800 px-1 rounded">EMAIL_PASSWORD</code></li>
              <li>4. Fill in your personal details (used for auto account creation on portals)</li>
              <li>5. Restart with <code className="text-yellow-300 bg-gray-800 px-1 rounded">docker compose restart api worker</code></li>
            </ol>
            <div className="mt-3 p-3 bg-blue-950/40 border border-blue-800 rounded-lg">
              <p className="text-xs text-blue-300">
                <strong>Gmail:</strong> Enable 2FA → go to myaccount.google.com/apppasswords → create "JobBot" password<br/>
                <strong>iCloud:</strong> Go to appleid.apple.com → Sign-In and Security → App-Specific Passwords
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div className="flex items-center justify-center py-20">
          <Loader className="animate-spin text-brand-400" size={24} />
        </div>
      )}
    </div>
  );
}
