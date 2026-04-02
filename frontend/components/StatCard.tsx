import type { DashboardKpi } from "@/types";

export function StatCard({ label, value, change, tone }: DashboardKpi) {
  const toneClass =
    tone === "critical"
      ? "text-[var(--danger)]"
      : tone === "warning"
        ? "text-[var(--warning)]"
        : tone === "good"
          ? "text-[var(--good)]"
          : "text-[var(--muted)]";

  return (
    <div className="glass-card metric-card fade-up">
      <p className="text-sm text-[var(--muted)]">{label}</p>
      <p className="mt-3 text-3xl font-semibold tracking-[-0.03em]">{value}</p>
      <p className={`mt-3 text-sm ${toneClass}`}>{change}</p>
    </div>
  );
}
