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

  return (
    <main className="app-shell flex min-h-screen items-center justify-center">
      <div className="grid w-full max-w-6xl gap-6 lg:grid-cols-[0.9fr_1.1fr]">
        <section className="glass-card section-card fade-up flex flex-col justify-between">
          <div>
            <span className="status-pill bg-[var(--accent-soft)] text-[var(--accent)]">Secure Access</span>
            <h1 className="mt-6 text-4xl font-semibold tracking-[-0.04em] sm:text-5xl">
              Sign in to your metro operations workspace.
            </h1>
            <p className="mt-4 max-w-xl text-base leading-7 text-[var(--muted)]">
              Monitor station demand, generate passenger flow forecasts, and export analytics from a responsive,
              Apple-inspired interface.
            </p>
          </div>

          <div className="mt-10 grid gap-4 sm:grid-cols-2">
            <div className="rounded-[26px] bg-[color:var(--panel)] p-4">
              <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">Demo Admin</p>
              <p className="mt-3 text-sm">`admin@metroflow.ai`</p>
              <p className="text-sm">`admin12345`</p>
            </div>
            <div className="rounded-[26px] bg-[color:var(--panel)] p-4">
              <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">Demo User</p>
              <p className="mt-3 text-sm">`user@metroflow.ai`</p>
              <p className="text-sm">`user12345`</p>
            </div>
          </div>
        </section>

        <section className="glass-card section-card fade-up">
          <div className="inline-flex rounded-full border border-[var(--panel-border)] bg-[color:var(--panel)] p-1">
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
                className={`rounded-full px-5 py-2 text-sm font-semibold capitalize ${
                  mode === value ? "bg-[var(--accent)] text-white" : "text-[var(--muted)]"
                }`}
              >
                {value}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="mt-8 grid gap-4">
            {mode === "register" ? (
              <div className="grid gap-4 md:grid-cols-2">
                <label className="space-y-2">
                  <span className="text-sm font-medium">Full Name</span>
                  <input
                    className="input-field"
                    value={form.full_name}
                    onChange={(event) => updateField("full_name", event.target.value)}
                    placeholder="Aarav Menon"
                  />
                  {errors.full_name ? <span className="text-sm text-[var(--danger)]">{errors.full_name}</span> : null}
                </label>

                <label className="space-y-2">
                  <span className="text-sm font-medium">Job Title</span>
                  <input
                    className="input-field"
                    value={form.job_title}
                    onChange={(event) => updateField("job_title", event.target.value)}
                    placeholder="Transit Planner"
                  />
                  {errors.job_title ? <span className="text-sm text-[var(--danger)]">{errors.job_title}</span> : null}
                </label>

                <label className="space-y-2">
                  <span className="text-sm font-medium">Organization</span>
                  <input
                    className="input-field"
                    value={form.organization}
                    onChange={(event) => updateField("organization", event.target.value)}
                    placeholder="MetroFlow Transit"
                  />
                  {errors.organization ? <span className="text-sm text-[var(--danger)]">{errors.organization}</span> : null}
                </label>

                <label className="space-y-2">
                  <span className="text-sm font-medium">Commute Line</span>
                  <input
                    className="input-field"
                    value={form.commute_line}
                    onChange={(event) => updateField("commute_line", event.target.value)}
                    placeholder="Blue"
                  />
                </label>
              </div>
            ) : null}

            <label className="space-y-2">
              <span className="text-sm font-medium">Email</span>
              <input
                className="input-field"
                type="email"
                value={form.email}
                onChange={(event) => updateField("email", event.target.value)}
                placeholder="you@metroflow.ai"
              />
              {errors.email ? <span className="text-sm text-[var(--danger)]">{errors.email}</span> : null}
            </label>

            <label className="space-y-2">
              <span className="text-sm font-medium">Password</span>
              <input
                className="input-field"
                type="password"
                value={form.password}
                onChange={(event) => updateField("password", event.target.value)}
                placeholder="At least 8 characters"
              />
              {errors.password ? <span className="text-sm text-[var(--danger)]">{errors.password}</span> : null}
            </label>

            <button type="submit" className="button-primary mt-2 w-full" disabled={loading}>
              {loading ? "Please wait..." : mode === "login" ? "Sign In" : "Create Account"}
            </button>

            {error ? <p className="text-sm text-[var(--danger)]">{error}</p> : null}
          </form>

          <p className="mt-6 text-sm text-[var(--muted)]">
            JWT protects the application routes, while passwords are stored with bcrypt hashing on the backend.
          </p>
          <Link href="/" className="mt-4 inline-flex text-sm font-semibold text-[var(--accent)]">
            Back to overview
          </Link>
        </section>
      </div>
    </main>
  );
}
