"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AppShell } from "@/components/AppShell";
import { getStoredToken } from "@/lib/auth";

export default function SettingsDashboardPage() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);

  const [threshold, setThreshold] = useState(85);
  const [theme, setTheme] = useState("dark");
  const [frequency, setFrequency] = useState(30);

  useEffect(() => {
    const storedToken = getStoredToken();
    if (!storedToken) {
      router.push("/auth");
      return;
    }
    setToken(storedToken);
  }, [router]);

  return (
    <AppShell
      title="System Settings"
      subtitle="Configure regional parameters, trigger retrains, and manage alert levels."
    >
      <div className="glass-card section-card max-w-2xl mx-auto space-y-6">
        <div>
          <h2 className="text-xl font-bold tracking-tight mb-2">Notification & Threshold Settings</h2>
          <p className="text-sm text-[var(--muted)] mb-4">
            Custom thresholds for triggering warnings and dispatcher alerts on station congestion.
          </p>
          <div className="space-y-4">
            <div>
              <label className="block text-xs uppercase tracking-[0.14em] text-[var(--muted)] mb-2">
                Congestion Alert Threshold ({threshold}%)
              </label>
              <input
                type="range"
                min="60"
                max="95"
                step="5"
                value={threshold}
                onChange={(e) => setThreshold(Number(e.target.value))}
                className="w-full h-1 bg-[var(--panel-border)] rounded-lg appearance-none cursor-pointer accent-[var(--accent)]"
              />
            </div>

            <div>
              <label className="block text-xs uppercase tracking-[0.14em] text-[var(--muted)] mb-2">
                Real-Time Refresh Frequency ({frequency}s)
              </label>
              <input
                type="range"
                min="5"
                max="60"
                step="5"
                value={frequency}
                onChange={(e) => setFrequency(Number(e.target.value))}
                className="w-full h-1 bg-[var(--panel-border)] rounded-lg appearance-none cursor-pointer accent-[var(--accent)]"
              />
            </div>
          </div>
        </div>

        <div className="pt-6 border-t border-[var(--panel-border)]">
          <h2 className="text-xl font-bold tracking-tight mb-2">General Preferences</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-xs uppercase tracking-[0.14em] text-[var(--muted)] mb-2">Visual Theme</label>
              <select
                className="select-field w-full"
                value={theme}
                onChange={(e) => setTheme(e.target.value)}
              >
                <option value="light">Light Mode</option>
                <option value="dark">Dark Mode</option>
                <option value="system">Follow System Preferences</option>
              </select>
            </div>
          </div>
        </div>

        <div className="pt-6 border-t border-[var(--panel-border)] flex items-center justify-between">
          <div>
            <span className="font-semibold block text-sm">Database Sync State</span>
            <span className="text-xs text-[var(--muted)]">Last synced with MongoDB at Rajiv Chowk: 2 min ago</span>
          </div>
          <span className="status-pill bg-emerald-500/12 text-emerald-600 font-bold scale-90">ONLINE</span>
        </div>
      </div>
    </AppShell>
  );
}
