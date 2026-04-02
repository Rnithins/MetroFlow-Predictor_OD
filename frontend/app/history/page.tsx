"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

import { AppShell } from "@/components/AppShell";
import { HeatmapGrid } from "@/components/HeatmapGrid";
import { ApiError, apiFetch } from "@/lib/api";
import { getStoredToken } from "@/lib/auth";
import { formatDateTime, formatNumber } from "@/lib/format";
import type { HistoricalAnalytics, Station } from "@/types";

export default function HistoryPage() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [stations, setStations] = useState<Station[]>([]);
  const [selectedStationId, setSelectedStationId] = useState("");
  const [days, setDays] = useState(14);
  const [analytics, setAnalytics] = useState<HistoricalAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const storedToken = getStoredToken();
    if (!storedToken) {
      router.push("/auth");
      return;
    }

    setToken(storedToken);
    apiFetch<Station[]>("/stations", {}, storedToken)
      .then((response) => {
        setStations(response);
        if (response[0]) {
          setSelectedStationId(response[0].id);
        }
      })
      .catch((requestError) => {
        setError(requestError instanceof Error ? requestError.message : "Unable to load stations.");
        setLoading(false);
      });
  }, [router]);

  useEffect(() => {
    if (!token || !selectedStationId) {
      return;
    }

    setLoading(true);
    setError(null);
    apiFetch<HistoricalAnalytics>(
      `/historical/analytics?station_id=${selectedStationId}&days=${days}`,
      {},
      token
    )
      .then((response) => setAnalytics(response))
      .catch((requestError) => {
        if (requestError instanceof ApiError && requestError.isAuthError) {
          router.push("/auth");
          return;
        }
        setError(requestError instanceof Error ? requestError.message : "Unable to load historical analytics.");
      })
      .finally(() => setLoading(false));
  }, [days, router, selectedStationId, token]);

  return (
    <AppShell
      title="Historical Analytics"
      subtitle="Review daily totals, average hourly demand, and heatmaps for each station."
      actions={
        <div className="flex flex-wrap items-center gap-3">
          <select
            className="select-field min-w-[220px]"
            value={selectedStationId}
            onChange={(event) => setSelectedStationId(event.target.value)}
          >
            {stations.map((station) => (
              <option key={station.id} value={station.id}>
                {station.name} · {station.line}
              </option>
            ))}
          </select>
          <select className="select-field" value={days} onChange={(event) => setDays(Number(event.target.value))}>
            {[7, 14, 21, 30].map((value) => (
              <option key={value} value={value}>
                Last {value} days
              </option>
            ))}
          </select>
        </div>
      }
    >
      {loading ? <div className="glass-card section-card">Loading analytics…</div> : null}
      {error ? <div className="glass-card section-card text-[var(--danger)]">{error}</div> : null}

      {analytics ? (
        <div className="space-y-6">
          <section className="grid gap-6 xl:grid-cols-2">
            <div className="glass-card section-card fade-up">
              <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">Daily Totals</p>
              <h2 className="mt-2 text-2xl font-semibold">{analytics.station_name}</h2>
              <div className="mt-6 h-[320px]">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={analytics.daily_totals}>
                    <defs>
                      <linearGradient id="dailyGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#2563eb" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#2563eb" stopOpacity={0.02} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.2)" />
                    <XAxis dataKey="label" tick={{ fontSize: 11 }} minTickGap={18} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Area type="monotone" dataKey="total_passengers" stroke="#2563eb" fill="url(#dailyGradient)" strokeWidth={2.6} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="glass-card section-card fade-up">
              <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">Hourly Average</p>
              <h2 className="mt-2 text-2xl font-semibold">Average ridership by hour</h2>
              <div className="mt-6 h-[320px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={analytics.hourly_average}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.2)" />
                    <XAxis dataKey="label" tick={{ fontSize: 11 }} minTickGap={18} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Bar dataKey="value" fill="#0f172a" radius={[12, 12, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </section>

          <section className="glass-card section-card fade-up">
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">Heatmap</p>
            <h2 className="mt-2 text-2xl font-semibold">Hour-by-hour intensity</h2>
            <div className="mt-6 overflow-x-auto">
              <HeatmapGrid rows={analytics.heatmap} />
            </div>
          </section>

          <section className="glass-card section-card fade-up">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">Latest Records</p>
                <h2 className="mt-2 text-2xl font-semibold">Recent observed flows</h2>
              </div>
              <p className="text-sm text-[var(--muted)]">Generated {formatDateTime(analytics.generated_at)}</p>
            </div>
            <div className="table-shell mt-6 overflow-x-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Timestamp</th>
                    <th>Passengers</th>
                    <th>Dwell</th>
                    <th>Context</th>
                  </tr>
                </thead>
                <tbody>
                  {analytics.latest_records.map((record) => (
                    <tr key={record.id}>
                      <td>{formatDateTime(record.timestamp)}</td>
                      <td>{formatNumber(record.passenger_count)}</td>
                      <td>{record.avg_dwell_minutes.toFixed(1)} min</td>
                      <td>{record.event_flag ? record.event_name ?? "Event-linked" : record.weather_code}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </div>
      ) : null}
    </AppShell>
  );
}
