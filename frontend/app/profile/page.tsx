"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { AppShell } from "@/components/AppShell";
import { useTheme } from "@/components/ThemeProvider";
import { ApiError, apiFetch } from "@/lib/api";
import { getStoredToken, updateStoredUser } from "@/lib/auth";
import { formatDateTime } from "@/lib/format";
import type { ProfileResponse, ThemePreference, User } from "@/types";

export default function ProfilePage() {
  const router = useRouter();
  const { setTheme } = useTheme();
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const storedToken = getStoredToken();
    if (!storedToken) {
      router.push("/auth");
      return;
    }
    setToken(storedToken);

    apiFetch<ProfileResponse>("/profile", {}, storedToken)
      .then((response) => setUser(response.user))
      .catch((requestError) => {
        if (requestError instanceof ApiError && requestError.isAuthError) {
          router.push("/auth");
          return;
        }
        setError(requestError instanceof Error ? requestError.message : "Unable to load profile.");
      })
      .finally(() => setLoading(false));
  }, [router]);

  async function handleSave(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || !user) {
      return;
    }

    setSaving(true);
    setMessage(null);
    setError(null);

    try {
      const response = await apiFetch<ProfileResponse>(
        "/profile",
        {
          method: "PUT",
          body: JSON.stringify({
            full_name: user.full_name,
            job_title: user.job_title,
            organization: user.organization,
            commute_line: user.commute_line,
            theme_preference: user.theme_preference
          })
        },
        token
      );
      setUser(response.user);
      updateStoredUser(response.user);
      setTheme(response.user.theme_preference as ThemePreference);
      setMessage("Profile updated successfully.");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to save profile.");
    } finally {
      setSaving(false);
    }
  }

  function updateField<K extends keyof User>(field: K, value: User[K]) {
    setUser((current) => (current ? { ...current, [field]: value } : current));
  }

  return (
    <AppShell
      title="User Profile"
      subtitle="Manage account details, role metadata, and visual preferences."
    >
      {loading ? <div className="glass-card section-card">Loading profile…</div> : null}
      {error ? <div className="glass-card section-card text-[var(--danger)]">{error}</div> : null}

      {user ? (
        <div className="grid gap-6 xl:grid-cols-[0.72fr_1.28fr]">
          <section className="glass-card section-card fade-up">
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">Account</p>
            <h2 className="mt-2 text-2xl font-semibold">{user.full_name}</h2>
            <p className="mt-1 text-sm text-[var(--muted)]">{user.email}</p>

            <div className="mt-6 space-y-4 rounded-[24px] bg-[color:var(--panel)] p-4">
              <div>
                <p className="text-sm text-[var(--muted)]">Role</p>
                <p className="mt-1 font-semibold capitalize">{user.role}</p>
              </div>
              <div>
                <p className="text-sm text-[var(--muted)]">Created</p>
                <p className="mt-1 font-semibold">{formatDateTime(user.created_at)}</p>
              </div>
              <div>
                <p className="text-sm text-[var(--muted)]">Security</p>
                <p className="mt-1 font-semibold">JWT session · bcrypt password hashing</p>
              </div>
            </div>
          </section>

          <section className="glass-card section-card fade-up">
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">Preferences</p>
            <form onSubmit={handleSave} className="mt-6 grid gap-4 md:grid-cols-2">
              <label className="space-y-2">
                <span className="text-sm font-medium">Full Name</span>
                <input
                  className="input-field"
                  value={user.full_name}
                  onChange={(event) => updateField("full_name", event.target.value)}
                />
              </label>

              <label className="space-y-2">
                <span className="text-sm font-medium">Job Title</span>
                <input
                  className="input-field"
                  value={user.job_title ?? ""}
                  onChange={(event) => updateField("job_title", event.target.value)}
                />
              </label>

              <label className="space-y-2">
                <span className="text-sm font-medium">Organization</span>
                <input
                  className="input-field"
                  value={user.organization ?? ""}
                  onChange={(event) => updateField("organization", event.target.value)}
                />
              </label>

              <label className="space-y-2">
                <span className="text-sm font-medium">Commute Line</span>
                <input
                  className="input-field"
                  value={user.commute_line ?? ""}
                  onChange={(event) => updateField("commute_line", event.target.value)}
                />
              </label>

              <label className="space-y-2 md:col-span-2">
                <span className="text-sm font-medium">Theme Preference</span>
                <select
                  className="select-field"
                  value={user.theme_preference}
                  onChange={(event) => updateField("theme_preference", event.target.value as ThemePreference)}
                >
                  <option value="system">System</option>
                  <option value="light">Light</option>
                  <option value="dark">Dark</option>
                </select>
              </label>

              <div className="md:col-span-2 flex items-center justify-between gap-3">
                <div className="text-sm text-[var(--muted)]">
                  {message ? <span className="text-[var(--good)]">{message}</span> : "Profile changes sync to local session and backend."}
                </div>
                <button type="submit" className="button-primary" disabled={saving}>
                  {saving ? "Saving..." : "Save Profile"}
                </button>
              </div>
            </form>
          </section>
        </div>
      ) : null}
    </AppShell>
  );
}
