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
import { PredictionComposer } from "@/components/PredictionComposer";
import { StatCard } from "@/components/StatCard";
import { ApiError, apiFetch } from "@/lib/api";
import { getStoredToken } from "@/lib/auth";
import { downloadCsv } from "@/lib/export";
import { formatDateTime, formatNumber } from "@/lib/format";
import type { DashboardOverview, Station } from "@/types";

export default function DashboardPage() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [stations, setStations] = useState<Station[]>([]);
  const [selectedStationId, setSelectedStationId] = useState("");
  const [overview, setOverview] = useState<DashboardOverview | null>(null);
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

  async function loadDashboard(stationId: string, activeToken: string) {
    setLoading(true);
    setError(null);
    try {
      const response = await apiFetch<DashboardOverview>(
        `/dashboard/overview?station_id=${stationId}`,
        {},
        activeToken
      );
      setOverview(response);
    } catch (requestError) {
      if (requestError instanceof ApiError && requestError.isAuthError) {
        router.push("/auth");
        return;
      }
      setError(requestError instanceof Error ? requestError.message : "Unable to load dashboard.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (token && selectedStationId) {
      void loadDashboard(selectedStationId, token);
    }
  }, [selectedStationId, token]);

  return (
    <AppShell
      title="Operations Dashboard"
      subtitle="Monitor demand, forecast the next surge, and export recent predictions."
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
          {overview?.recent_predictions.length ? (
            <button
              type="button"
              className="button-secondary"
              onClick={() =>
                downloadCsv(
                  "metroflow-recent-predictions.csv",
                  overview.recent_predictions.map((item) => ({
                    station: item.station_name,
                    line: item.line,
                    target_timestamp: item.target_timestamp,
                    predicted_count: item.predicted_count,
                    confidence_score: item.confidence_score,
                    anomaly_score: item.anomaly_score,
                    recommendation: item.recommended_action
                  }))
                )
              }
            >
              Export Predictions
            </button>
          ) : null}
        </div>
      }
    >
      {loading ? (
        <div className="glass-card section-card">Loading dashboard…</div>
      ) : null}
      {error ? <div className="glass-card section-card text-[var(--danger)]">{error}</div> : null}

      {overview ? (
        <div className="space-y-6">
          <section className="glass-card section-card fade-up">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
                  Station Insight
                </p>
                <h2 className="mt-2 text-3xl font-semibold tracking-[-0.04em]">{overview.selected_station_name}</h2>
                <p className="mt-3 max-w-3xl text-sm leading-7 text-[var(--muted)]">{overview.insight}</p>
              </div>
              <div className="rounded-[24px] bg-[color:var(--panel)] p-4 text-sm">
                <p className="text-[var(--muted)]">Model version</p>
                <p className="mt-1 font-semibold">{overview.model_version}</p>
                <p className="mt-3 text-[var(--muted)]">Generated</p>
                <p className="mt-1 font-semibold">{formatDateTime(overview.generated_at)}</p>
              </div>
            </div>
          </section>

          <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {overview.kpis.map((item) => (
              <StatCard key={item.label} {...item} />
            ))}
          </section>

          <section className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
            <div className="glass-card section-card fade-up">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">Trend</p>
                  <h2 className="mt-2 text-2xl font-semibold">Actual vs forecasted riders</h2>
                </div>
              </div>
              <div className="mt-6 h-[340px]">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={overview.trend}>
                    <defs>
                      <linearGradient id="actualFill" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#2563eb" stopOpacity={0.35} />
                        <stop offset="95%" stopColor="#2563eb" stopOpacity={0.02} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.2)" />
                    <XAxis dataKey="label" tick={{ fontSize: 11 }} minTickGap={42} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Area type="monotone" dataKey="actual" stroke="#0f172a" fill="url(#actualFill)" strokeWidth={2.6} />
                    <Area type="monotone" dataKey="forecast" stroke="#2563eb" fill="transparent" strokeWidth={2.4} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            {token ? (
              <PredictionComposer token={token} stations={stations} onPredictionCreated={() => loadDashboard(selectedStationId, token)} />
            ) : null}
          </section>

          <section className="grid gap-6 xl:grid-cols-[0.85fr_1.15fr]">
            <div className="glass-card section-card fade-up">
              <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">Hourly Load Shape</p>
              <h2 className="mt-2 text-2xl font-semibold">Average hourly flow</h2>
              <div className="mt-6 h-[320px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={overview.hourly_distribution}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.2)" />
                    <XAxis dataKey="label" tick={{ fontSize: 11 }} minTickGap={18} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Bar dataKey="value" fill="#2563eb" radius={[12, 12, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="glass-card section-card fade-up">
              <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">Heatmap</p>
              <h2 className="mt-2 text-2xl font-semibold">Last 7 days by hour</h2>
              <div className="mt-6 overflow-x-auto">
                <HeatmapGrid rows={overview.heatmap} />
              </div>
            </div>
          </section>

          <section className="grid gap-6 xl:grid-cols-[0.85fr_1.15fr]">
            <div className="glass-card section-card fade-up">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">Alerts</p>
                  <h2 className="mt-2 text-2xl font-semibold">Operational watchlist</h2>
                </div>
              </div>
              <div className="mt-6 space-y-3">
                {overview.alerts.length ? (
                  overview.alerts.map((alert) => (
                    <div key={`${alert.title}-${alert.timestamp}`} className="rounded-[24px] bg-[color:var(--panel)] p-4">
                      <div className="flex items-center justify-between gap-3">
                        <p className="font-semibold">{alert.title}</p>
                        <span
                          className={`status-pill ${
                            alert.severity === "critical"
                              ? "bg-orange-500/12 text-orange-600"
                              : "bg-amber-500/12 text-amber-600"
                          }`}
                        >
                          {alert.severity}
                        </span>
                      </div>
                      <p className="mt-2 text-sm text-[var(--muted)]">{alert.detail}</p>
                      <p className="mt-3 text-xs uppercase tracking-[0.14em] text-[var(--muted)]">
                        {formatDateTime(alert.timestamp)}
                      </p>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-[var(--muted)]">No elevated alerts for the selected station.</p>
                )}
              </div>
            </div>

            <div className="grid gap-6">
              <div className="glass-card section-card fade-up">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">Recent Predictions</p>
                    <h2 className="mt-2 text-2xl font-semibold">Stored forecast results</h2>
                  </div>
                </div>
                <div className="table-shell mt-6 overflow-x-auto">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Target</th>
                        <th>Predicted</th>
                        <th>Confidence</th>
                      </tr>
                    </thead>
                    <tbody>
                      {overview.recent_predictions.map((prediction) => (
                        <tr key={prediction.id}>
                          <td>
                            <div className="font-semibold">{formatDateTime(prediction.target_timestamp)}</div>
                            <div className="text-xs text-[var(--muted)]">{prediction.recommended_action}</div>
                          </td>
                          <td>{formatNumber(Math.round(prediction.predicted_count))}</td>
                          <td>{(prediction.confidence_score * 100).toFixed(0)}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="glass-card section-card fade-up">
                <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">Recent Station Records</p>
                <div className="table-shell mt-6 overflow-x-auto">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Timestamp</th>
                        <th>Passengers</th>
                        <th>Context</th>
                      </tr>
                    </thead>
                    <tbody>
                      {overview.recent_flows.map((flow) => (
                        <tr key={flow.id}>
                          <td>
                            <div className="font-semibold">{formatDateTime(flow.timestamp)}</div>
                            <div className="text-xs text-[var(--muted)]">{flow.source}</div>
                          </td>
                          <td>{formatNumber(flow.passenger_count)}</td>
                          <td>{flow.event_flag ? flow.event_name ?? "Event-linked" : flow.weather_code}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </section>
        </div>
      ) : null}
    </AppShell>
  );
}
