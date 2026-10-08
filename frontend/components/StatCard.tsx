import type { DashboardKpi } from "@/types";

export function StatCard({ label, value, change, tone }: DashboardKpi) {
  const toneConfig =
    tone === "critical"
      ? {
          badge: "bg-red-500/10 text-[var(--danger)] border-red-500/20",
          dot: "bg-red-500",
        }
      : tone === "warning"
        ? {
            badge: "bg-amber-500/10 text-[var(--warning)] border-amber-500/20",
            dot: "bg-amber-500",
          }
        : tone === "good"
          ? {
              badge: "bg-emerald-500/10 text-[var(--good)] border-emerald-500/20",
              dot: "bg-emerald-500",
            }
          : {
              badge: "bg-black/[0.04] dark:bg-white/[0.06] text-[var(--muted)] border-transparent",
              dot: "bg-gray-400",
            };

  return (
    <div className="glass-card metric-card fade-up group cursor-default hover:-translate-y-1 transition-all duration-300">
      <div className="flex items-center justify-between">
        <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--muted)]">
          {label}
        </p>
        <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[11px] font-medium backdrop-blur-md ${toneConfig.badge}`}>
          <span className={`h-1.5 w-1.5 rounded-full ${toneConfig.dot}`} />
          {change}
        </span>
      </div>

      <div className="mt-3.5 flex items-baseline justify-between">
        <p className="text-3xl sm:text-4xl font-bold tracking-tight text-[var(--text)]">
          {value}
        </p>
      </div>

      {/* Subtle micro ambient glow at the bottom edge */}
      <div className="mt-2 h-[2px] w-full rounded-full bg-gradient-to-r from-transparent via-[var(--accent)]/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
    </div>
  );
}
