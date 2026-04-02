import { formatNumber } from "@/lib/format";
import type { DashboardHeatmapRow } from "@/types";

function getIntensity(value: number, maxValue: number): string {
  if (maxValue <= 0) {
    return "rgba(148, 163, 184, 0.14)";
  }
  const ratio = value / maxValue;
  return `rgba(37, 99, 235, ${Math.max(0.12, Math.min(0.9, ratio))})`;
}

export function HeatmapGrid({ rows }: { rows: DashboardHeatmapRow[] }) {
  const maxValue = Math.max(...rows.flatMap((row) => row.values), 1);

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-[84px_repeat(24,minmax(0,1fr))] gap-2 text-[11px] uppercase tracking-[0.16em] text-[var(--muted)]">
        <div>Day</div>
        {Array.from({ length: 24 }, (_, hour) => (
          <div key={hour} className="text-center">
            {hour}
          </div>
        ))}
      </div>

      {rows.map((row) => (
        <div key={row.day_label} className="grid grid-cols-[84px_repeat(24,minmax(0,1fr))] gap-2">
          <div className="flex items-center text-sm font-semibold text-[var(--muted)]">{row.day_label}</div>
          {row.values.map((value, index) => (
            <div
              key={`${row.day_label}-${index}`}
              className="heat-cell"
              style={{ background: getIntensity(value, maxValue), color: value > maxValue * 0.45 ? "white" : "var(--text)" }}
              title={`${row.day_label} ${index}:00 - ${formatNumber(value)} passengers`}
            >
              {value ? Math.round(value / 10) : "-"}
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
