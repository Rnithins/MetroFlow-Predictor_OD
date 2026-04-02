import Link from "next/link";

export default function HomePage() {
  return (
    <main className="app-shell flex items-center">
      <div className="grid w-full gap-6 lg:grid-cols-[1.15fr_0.85fr]">
        <section className="glass-card section-card fade-up overflow-hidden">
          <span className="status-pill bg-[var(--accent-soft)] text-[var(--accent)]">MetroFlow Predictor</span>
          <h1 className="mt-6 max-w-3xl text-4xl font-semibold tracking-[-0.04em] sm:text-6xl">
            Forecast station crowding before the platform feels it.
          </h1>
          <p className="mt-5 max-w-2xl text-base leading-7 text-[var(--muted)] sm:text-lg">
            A full-stack metro analytics workspace with JWT auth, MongoDB-backed historical data, and a Python
            forecasting module for hourly passenger flow prediction.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link href="/auth" className="button-primary">
              Open Dashboard
            </Link>
            <Link href="/history" className="button-secondary">
              Explore Historical Trends
            </Link>
          </div>
          <div className="mt-10 grid gap-4 sm:grid-cols-3">
            {[
              ["Forecasting", "Hourly and daily passenger flow projections"],
              ["Operations", "Heatmaps, alerts, recent predictions, admin uploads"],
              ["Security", "JWT sessions, protected routes, bcrypt password hashing"]
            ].map(([title, description]) => (
              <div key={title} className="rounded-[24px] bg-[color:var(--panel)] p-4 backdrop-blur-sm">
                <h2 className="text-sm font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">{title}</h2>
                <p className="mt-3 text-sm leading-6">{description}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="space-y-6">
          <div className="glass-card section-card fade-up">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">Live Snapshot</p>
                <h2 className="mt-2 text-2xl font-semibold">Minimal, responsive operations view</h2>
              </div>
              <div className="status-pill bg-emerald-500/12 text-emerald-600">AI Ready</div>
            </div>
            <div className="mt-6 grid gap-3 sm:grid-cols-2">
              {[
                ["Predicted next-hour load", "684 riders", "warning"],
                ["Model confidence", "88%", "good"],
                ["Alert corridors", "3 active", "critical"],
                ["Data freshness", "< 5 min", "good"]
              ].map(([label, value, tone]) => (
                <div key={label} className="rounded-[22px] bg-[color:var(--panel)] p-4">
                  <p className="text-sm text-[var(--muted)]">{label}</p>
                  <p className="mt-2 text-2xl font-semibold">{value}</p>
                  <p
                    className={`mt-2 text-sm ${
                      tone === "critical"
                        ? "text-[var(--danger)]"
                        : tone === "warning"
                          ? "text-[var(--warning)]"
                          : "text-[var(--good)]"
                    }`}
                  >
                    {tone === "critical" ? "Take action" : tone === "warning" ? "Monitor closely" : "Within target"}
                  </p>
                </div>
              ))}
            </div>
          </div>

          <div className="glass-card section-card fade-up">
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">Included Modules</p>
            <ul className="mt-4 space-y-3 text-sm leading-6 text-[var(--muted)]">
              <li>Login/register flow with validation and protected navigation</li>
              <li>Dashboard charts, heatmaps, tables, and forecast generation</li>
              <li>Historical daily and hourly trend analytics</li>
              <li>Profile management and admin CRUD for station flow records</li>
            </ul>
          </div>
        </section>
      </div>
    </main>
  );
}
