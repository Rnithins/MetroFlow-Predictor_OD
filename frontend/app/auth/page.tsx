"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { apiFetch } from "@/lib/api";
import { persistSession } from "@/lib/auth";
import type { AuthResponse } from "@/types";

type Mode = "login" | "register";

type FormState = {
  email: string;
  password: string;
  full_name: string;
  organization: string;
  job_title: string;
  commute_line: string;
};

const initialState: FormState = {
  email: "",
  password: "",
  full_name: "",
  organization: "",
  job_title: "",
  commute_line: ""
};

export default function AuthPage() {
  const router = useRouter();
  const [mode, setMode] = useState<Mode>("login");
  const [form, setForm] = useState<FormState>({
    ...initialState,
    email: "admin@metroflow.ai",
    password: "admin12345"
  });
  const [errors, setErrors] = useState<Partial<Record<keyof FormState, string>>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function updateField(field: keyof FormState, value: string) {
    setForm((current) => ({ ...current, [field]: value }));
    setErrors((current) => ({ ...current, [field]: undefined }));
  }

  function validate(): boolean {
    const nextErrors: Partial<Record<keyof FormState, string>> = {};

    if (!form.email.includes("@")) {
      nextErrors.email = "Enter a valid email address.";
    }
    if (form.password.length < 8) {
      nextErrors.password = "Password must be at least 8 characters.";
    }

    if (mode === "register") {
      if (form.full_name.trim().length < 2) {
        nextErrors.full_name = "Full name is required.";
      }
      if (!form.organization.trim()) {
        nextErrors.organization = "Organization is required.";
      }
      if (!form.job_title.trim()) {
        nextErrors.job_title = "Job title is required.";
      }
    }

    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    if (!validate()) {
      return;
    }

    setLoading(true);
    try {
      const response = await apiFetch<AuthResponse>(
        mode === "login" ? "/auth/login" : "/auth/register",
        {
          method: "POST",
          body: JSON.stringify(
            mode === "login"
              ? { email: form.email, password: form.password }
              : {
                  email: form.email,
                  password: form.password,
                  full_name: form.full_name,
                  organization: form.organization,
                  job_title: form.job_title,
                  commute_line: form.commute_line
                }
          )
        }
      );

      persistSession(response);
      router.push("/dashboard");
      router.refresh();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Authentication failed.");
    } finally {
      setLoading(false);
    }
  }

  const fillDemo = (email: string, pass: string) => {
    setMode("login");
    setForm({ ...initialState, email, password: pass });
    setErrors({});
    setError(null);
  };

  return (
    <main className="app-shell flex min-h-screen items-center justify-center py-10">
      <div className="grid w-full max-w-5xl gap-6 lg:grid-cols-[0.9fr_1.1fr] items-stretch">
        {/* Left Info Card */}
        <section className="glass-card section-card fade-up flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2">
              <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-cyan-400 p-[1px] shadow-md shadow-blue-500/20">
                <div className="flex h-full w-full items-center justify-center rounded-[14px] bg-white/20 backdrop-blur-md text-white font-bold text-xs">
                  MF
                </div>
              </div>
              <span className="text-xs font-bold tracking-tight text-[var(--text)]">MetroFlowNet OS</span>
            </div>

            <h1 className="mt-6 text-3xl font-bold tracking-[-0.04em] sm:text-4xl text-[var(--text)]">
              Transit Operator Sign In
            </h1>
            <p className="mt-3 text-sm leading-relaxed text-[var(--muted)]">
              Secure enterprise gateway with bcrypt key derivation and JWT role-based access for transit controllers.
            </p>
          </div>

          {/* Quick Click Autofill Demo Cards */}
          <div className="mt-8 space-y-3">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-[var(--muted)]">
              Click to Autofill Demo Credentials
            </p>
            <div className="grid gap-2.5 sm:grid-cols-2">
              <button
                type="button"
                onClick={() => fillDemo("admin@metroflow.ai", "admin12345")}
                className="rounded-2xl border border-[var(--panel-border)] bg-black/[0.02] dark:bg-white/[0.04] p-3 text-left hover:border-[var(--accent)] hover:bg-[var(--accent)]/5 transition-all"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-[var(--text)]">Admin Demo</span>
                  <span className="text-[10px] text-[var(--accent)] font-semibold">Autofill</span>
                </div>
                <p className="text-[11px] font-mono text-[var(--muted)] mt-1">admin@metroflow.ai</p>
                <p className="text-[10px] text-[var(--muted)]">Pass: admin12345</p>
              </button>

              <button
                type="button"
                onClick={() => fillDemo("user@metroflow.ai", "user12345")}
                className="rounded-2xl border border-[var(--panel-border)] bg-black/[0.02] dark:bg-white/[0.04] p-3 text-left hover:border-[var(--accent)] hover:bg-[var(--accent)]/5 transition-all"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-[var(--text)]">Analyst Demo</span>
                  <span className="text-[10px] text-[var(--accent)] font-semibold">Autofill</span>
                </div>
                <p className="text-[11px] font-mono text-[var(--muted)] mt-1">user@metroflow.ai</p>
                <p className="text-[10px] text-[var(--muted)]">Pass: user12345</p>
              </button>
            </div>
          </div>
        </section>

        {/* Right Form Card */}
        <section className="glass-card section-card fade-up flex flex-col justify-between">
          <div>
            {/* Cupertino Segmented Tabs */}
            <div className="apple-segmented-track w-full justify-between mb-6">
              {(["login", "register"] as const).map((value) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => {
                    setMode(value);
                    setError(null);
                    setErrors({});
                    setForm(
                      value === "login"
                        ? { ...initialState, email: "admin@metroflow.ai", password: "admin12345" }
                        : initialState
                    );
                  }}
                  className={`apple-segmented-item flex-1 text-center py-2 ${
                    mode === value ? "active" : ""
                  }`}
                >
                  {value === "login" ? "Sign In" : "Register Operator"}
                </button>
              ))}
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              {mode === "register" && (
                <div className="grid gap-3 sm:grid-cols-2">
                  <div>
                    <label className="text-[11px] font-semibold uppercase tracking-wider text-[var(--muted)] mb-1 block">Full Name</label>
                    <input
                      className="input-field text-xs"
                      value={form.full_name}
                      onChange={(event) => updateField("full_name", event.target.value)}
                      placeholder="Pooja Sharma"
                    />
                    {errors.full_name && <span className="text-xs text-[var(--danger)]">{errors.full_name}</span>}
                  </div>

                  <div>
                    <label className="text-[11px] font-semibold uppercase tracking-wider text-[var(--muted)] mb-1 block">Job Title</label>
                    <input
                      className="input-field text-xs"
                      value={form.job_title}
                      onChange={(event) => updateField("job_title", event.target.value)}
                      placeholder="Operations Controller"
                    />
                    {errors.job_title && <span className="text-xs text-[var(--danger)]">{errors.job_title}</span>}
                  </div>

                  <div>
                    <label className="text-[11px] font-semibold uppercase tracking-wider text-[var(--muted)] mb-1 block">Organization</label>
                    <input
                      className="input-field text-xs"
                      value={form.organization}
                      onChange={(event) => updateField("organization", event.target.value)}
                      placeholder="DMRC / Namma Metro"
                    />
                    {errors.organization && <span className="text-xs text-[var(--danger)]">{errors.organization}</span>}
                  </div>

                  <div>
                    <label className="text-[11px] font-semibold uppercase tracking-wider text-[var(--muted)] mb-1 block">Metro Corridor</label>
                    <input
                      className="input-field text-xs"
                      value={form.commute_line}
                      onChange={(event) => updateField("commute_line", event.target.value)}
                      placeholder="Blue / Yellow Line"
                    />
                  </div>
                </div>
              )}

              <div>
                <label className="text-[11px] font-semibold uppercase tracking-wider text-[var(--muted)] mb-1 block">Work Email</label>
                <input
                  className="input-field text-xs"
                  type="email"
                  value={form.email}
                  onChange={(event) => updateField("email", event.target.value)}
                  placeholder="admin@metroflow.ai"
                />
                {errors.email && <span className="text-xs text-[var(--danger)]">{errors.email}</span>}
              </div>

              <div>
                <label className="text-[11px] font-semibold uppercase tracking-wider text-[var(--muted)] mb-1 block">Password</label>
                <input
                  className="input-field text-xs"
                  type="password"
                  value={form.password}
                  onChange={(event) => updateField("password", event.target.value)}
                  placeholder="••••••••"
                />
                {errors.password && <span className="text-xs text-[var(--danger)]">{errors.password}</span>}
              </div>

              <button type="submit" className="button-primary w-full py-3" disabled={loading}>
                {loading ? (
                  <span className="flex items-center gap-2">
                    <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Authenticating Session...
                  </span>
                ) : mode === "login" ? (
                  "Access Operations Center"
                ) : (
                  "Create Account"
                )}
              </button>

              {error && (
                <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-xs text-[var(--danger)]">
                  {error}
                </div>
              )}
            </form>
          </div>

          <div className="mt-6 pt-4 border-t border-[var(--panel-border)]/60 flex items-center justify-between text-xs text-[var(--muted)]">
            <span>Encrypted with bcrypt & JWT</span>
            <Link href="/" className="font-semibold text-[var(--accent)] hover:underline">
              ← Return Home
            </Link>
          </div>
        </section>
      </div>
    </main>
  );
}
