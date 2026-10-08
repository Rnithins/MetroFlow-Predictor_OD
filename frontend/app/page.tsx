import Link from "next/link";
import { ThemeToggle } from "@/components/ThemeToggle";

export default function HomePage() {
  return (
    <main className="app-shell flex flex-col justify-between py-6">
      {/* Top Apple Floating Island Nav */}
      <header className="glass-card mb-8 flex items-center justify-between p-4 px-6">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-cyan-400 p-[1px] shadow-md shadow-blue-500/20">
            <div className="flex h-full w-full items-center justify-center rounded-[11px] bg-white/20 backdrop-blur-md text-white font-bold text-xs">
              MF
            </div>
          </div>
          <div>
            <span className="text-xs font-bold tracking-tight text-[var(--text)]">MetroFlowNet</span>
            <span className="ml-2 rounded-full bg-blue-500/10 px-2 py-0.5 text-[10px] font-semibold text-[var(--accent)] border border-blue-500/20">
              Transit SaaS
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <ThemeToggle />
          <Link href="/auth" className="button-primary text-xs py-2 px-4">
            Launch Platform
          </Link>
        </div>
      </header>

      {/* Hero Bento Grid */}
      <div className="grid w-full gap-6 lg:grid-cols-[1.15fr_0.85fr] items-stretch my-auto">
        {/* Left Hero Card */}
        <section className="glass-card section-card fade-up flex flex-col justify-between overflow-hidden">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-blue-500/25 bg-blue-500/10 px-3.5 py-1 text-xs font-semibold text-[var(--accent)] backdrop-blur-md">
              <span className="h-1.5 w-1.5 rounded-full bg-[var(--accent)] animate-pulse" />
              National Metro Intelligence Platform · India
            </div>

            <h1 className="mt-6 max-w-3xl text-3xl font-bold tracking-[-0.04em] sm:text-5xl lg:text-6xl text-[var(--text)] leading-[1.08]">
              Next-Generation <br />
              <span className="bg-gradient-to-r from-blue-600 via-indigo-600 to-cyan-500 bg-clip-text text-transparent">
                Transit Intelligence
              </span>{" "}
              for Smart Metros.
            </h1>

            <p className="mt-5 max-w-xl text-sm leading-relaxed text-[var(--muted)] sm:text-base">
              Adaptive spatial-temporal graph neural networks modeling Origin-Destination passenger flows, multi-horizon crowd surges, and smart train dispatching across 9 Indian metropolitan networks.
            </p>

            <div className="mt-8 flex flex-wrap gap-3">
              <Link href="/dashboard" className="button-primary px-6 py-3 text-sm">
                Enter Operations Center →
              </Link>
              <Link href="/auth" className="button-secondary px-6 py-3 text-sm">
                Operator Sign In
              </Link>
            </div>
          </div>

          <div className="mt-10 grid gap-3 sm:grid-cols-3 pt-6 border-t border-[var(--panel-border)]/60">
            {[
              ["Surge Forecasts", "Multi-horizon projections: 15m, 30m, 1h, and 24h"],
              ["OD Flow Matrices", "Real-time travel pathways between stations"],
              ["Route Optimizer", "Multi-objective transit corridor routing"]
            ].map(([title, description]) => (
              <div key={title} className="rounded-2xl bg-black/[0.02] dark:bg-white/[0.04] p-4 border border-[var(--panel-border)]/50">
                <h2 className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--muted)]">{title}</h2>
                <p className="mt-1.5 text-xs text-[var(--muted)] leading-5">{description}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Right Bento Grid */}
        <section className="space-y-6 flex flex-col justify-between">
          <div className="glass-card section-card fade-up">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">Active Deployment</p>
                <h2 className="mt-1 text-xl font-bold tracking-tight text-[var(--text)]">National Transit Infrastructure</h2>
              </div>
              <span className="status-pill bg-emerald-500/10 text-[var(--good)] border border-emerald-500/20">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                PyTorch AFFN
              </span>
            </div>

            <div className="mt-6 grid gap-3 sm:grid-cols-2">
              {[
                ["Monitored Stations", "16 Active Terminal Nodes", "good"],
                ["Synchronized Networks", "9 Metro Cities", "good"],
                ["Alert Watchlist", "3 Stations at Risk", "warning"],
                ["Average Network Speed", "41.2 km/h", "good"]
              ].map(([label, value, tone]) => (
                <div key={label} className="rounded-2xl bg-black/[0.02] dark:bg-white/[0.04] p-4 border border-[var(--panel-border)]/60">
                  <p className="text-[11px] text-[var(--muted)]">{label}</p>
                  <p className="mt-1.5 text-lg font-bold text-[var(--text)]">{value}</p>
                  <p
                    className={`mt-1.5 text-[10px] font-semibold uppercase tracking-[0.12em] ${
                      tone === "critical"
                        ? "text-[var(--danger)]"
                        : tone === "warning"
                          ? "text-[var(--warning)]"
                          : "text-[var(--good)]"
                    }`}
                  >
                    {tone === "critical" ? "Action Required" : tone === "warning" ? "Surge Watch" : "Operational"}
                  </p>
                </div>
              ))}
            </div>
          </div>

          <div className="glass-card section-card fade-up">
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">Core AI Architecture</p>
            <ul className="mt-4 space-y-3 text-xs leading-5 text-[var(--muted)]">
              <li className="flex items-start gap-2.5">
                <span className="text-[var(--accent)] font-bold">✔</span>
                <span>Spatial-Temporal GNN-LSTM encoders for network loading topologies</span>
              </li>
              <li className="flex items-start gap-2.5">
                <span className="text-[var(--accent)] font-bold">✔</span>
                <span>Adaptive Feature Fusion gates dynamic weather & festival rush multipliers</span>
              </li>
              <li className="flex items-start gap-2.5">
                <span className="text-[var(--accent)] font-bold">✔</span>
                <span>Interactive particle vector flow canvas with real-time station diagnostics</span>
              </li>
            </ul>
          </div>
        </section>
      </div>

      {/* Apple Footer */}
      <footer className="mt-8 text-center text-xs text-[var(--muted)] py-2">
        <p>MetroFlowNet Transit OS · Built with Next.js 14, FastAPI & PyTorch · Apple Glassmorphic Architecture</p>
      </footer>
    </main>
  );
}
