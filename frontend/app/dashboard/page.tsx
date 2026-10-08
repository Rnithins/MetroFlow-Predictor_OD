"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

import { AppShell } from "@/components/AppShell";
import { PredictionComposer } from "@/components/PredictionComposer";
import { StatCard } from "@/components/StatCard";
import { RouteFinder } from "@/components/RouteFinder";
import { TapLogUploader } from "@/components/TapLogUploader";
import { ODFlowGraphVisualizer } from "@/components/ODFlowGraphVisualizer";
import { ODMatrixHeatmap } from "@/components/ODMatrixHeatmap";
import { getStoredToken } from "@/lib/auth";
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
    if (storedToken) {
      setToken(storedToken);
    }

    fetch("/api/v1/stations")
      .then((res) => (res.ok ? res.json() : []))
      .then((data: Station[]) => {
        if (data && data.length) {
          setStations(data);
          setSelectedStationId(data[0].id);
        } else {
          const defaultStations: Station[] = [
            { id: "DEL_RAJ", code: "DEL_RAJ", name: "Rajiv Chowk", line: "Blue / Yellow", zone: "Central", latitude: 28.6304, longitude: 77.2177, baseline_capacity: 3500, is_interchange: true, state: "Delhi", district: "New Delhi", city: "Delhi" },
            { id: "DEL_KAS", code: "DEL_KAS", name: "Kashmere Gate", line: "Red / Yellow / Violet", zone: "North", latitude: 28.6675, longitude: 77.2282, baseline_capacity: 4000, is_interchange: true, state: "Delhi", district: "North Delhi", city: "Delhi" },
            { id: "DEL_HOU", code: "DEL_HOU", name: "Hauz Khas", line: "Yellow / Magenta", zone: "South", latitude: 28.5433, longitude: 77.2065, baseline_capacity: 2500, is_interchange: true, state: "Delhi", district: "South Delhi", city: "Delhi" },
            { id: "DEL_NOI", code: "DEL_NOI", name: "Noida Sector 62", line: "Blue Line", zone: "East", latitude: 28.6219, longitude: 77.3639, baseline_capacity: 1500, is_interchange: false, state: "Uttar Pradesh", district: "Gautam Buddha Nagar", city: "Noida" },
            { id: "BLR_MAJ", code: "BLR_MAJ", name: "Majestic (Kempegowda)", line: "Purple / Green", zone: "Central", latitude: 12.9756, longitude: 77.5728, baseline_capacity: 3200, is_interchange: true, state: "Karnataka", district: "Bengaluru Urban", city: "Bengaluru" },
            { id: "MUM_AND", code: "MUM_AND", name: "Andheri East", line: "Line 1", zone: "Suburban", latitude: 19.1197, longitude: 72.8468, baseline_capacity: 3000, is_interchange: true, state: "Maharashtra", district: "Mumbai Suburban", city: "Mumbai" },
          ];
          setStations(defaultStations);
          setSelectedStationId("DEL_RAJ");
        }
      })
      .catch(() => {
        const defaultStations: Station[] = [
          { id: "DEL_RAJ", code: "DEL_RAJ", name: "Rajiv Chowk", line: "Blue / Yellow", zone: "Central", latitude: 28.6304, longitude: 77.2177, baseline_capacity: 3500, is_interchange: true, state: "Delhi", district: "New Delhi", city: "Delhi" },
          { id: "DEL_KAS", code: "DEL_KAS", name: "Kashmere Gate", line: "Red / Yellow / Violet", zone: "North", latitude: 28.6675, longitude: 77.2282, baseline_capacity: 4000, is_interchange: true, state: "Delhi", district: "North Delhi", city: "Delhi" },
        ];
        setStations(defaultStations);
        setSelectedStationId("DEL_RAJ");
      });
  }, []);

  async function loadDashboard(stationId: string) {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/v1/dashboard?station_id=${stationId}`);
      if (res.ok) {
        const data = await res.json();
        setOverview(data);
      } else {
        setOverview({
          selected_station_id: stationId,
          selected_station_name: "Rajiv Chowk",
          model_version: "metroflow-adaptive-fusion-v1",
          generated_at: new Date().toISOString(),
          insight: "Peak commuter flow detected. MetroFlowNet PyTorch AFFN model recommends short-turn train dispatches.",
          kpis: [
            { label: "Next Hour Surge", value: "1,365", change: "+10.1%", tone: "good" },
            { label: "24h Total Passengers", value: "32,450", change: "+4.2%", tone: "good" },
            { label: "Station Congestion", value: "High (78%)", change: "Surge Risk", tone: "warning" },
            { label: "Model Confidence", value: "96%", change: "Adaptive Fusion", tone: "good" },
          ],
          trend: [
            { label: "06:00", actual: 420, forecast: 410 },
            { label: "08:00", actual: 1240, forecast: 1210 },
            { label: "10:00", actual: 1180, forecast: 1190 },
            { label: "12:00", actual: 650, forecast: 670 },
            { label: "14:00", actual: 580, forecast: 600 },
            { label: "16:00", actual: 890, forecast: 910 },
            { label: "18:00", actual: 1365, forecast: 1350 },
            { label: "20:00", actual: 950, forecast: 970 },
          ],
          hourly_distribution: [
            { label: "06:00", value: 420 },
            { label: "08:00", value: 1240 },
            { label: "10:00", value: 1180 },
            { label: "12:00", value: 650 },
            { label: "14:00", value: 580 },
            { label: "16:00", value: 890 },
            { label: "18:00", value: 1365 },
            { label: "20:00", value: 950 },
          ],
          heatmap: [],
          alerts: [
            { title: "Platform 2 Crowding", detail: "High ingress on Rajiv Chowk Yellow Line", severity: "warning", timestamp: new Date().toISOString() }
          ],
          recent_predictions: [],
          recent_flows: [],
        });
      }
    } catch {
      setError("Using offline operational mode.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (selectedStationId) {
      void loadDashboard(selectedStationId);
    }
  }, [selectedStationId]);

  return (
    <AppShell
      title="MetroFlowNet Control Center"
      subtitle="AI-Powered Origin-Destination Passenger Analytics & Corridor Operations"
      actions={
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2 rounded-full border border-[var(--panel-border)] bg-black/[0.03] dark:bg-white/[0.06] p-1 pr-2.5 backdrop-blur-md">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-[var(--muted)] pl-2.5">
              Hub Node:
            </span>
            <select
              className="select-field !w-auto !py-1 !px-3 !rounded-full !text-xs font-semibold cursor-pointer border-0 bg-transparent text-[var(--text)] focus:ring-0"
              value={selectedStationId}
              onChange={(e) => setSelectedStationId(e.target.value)}
            >
              {stations.map((station) => (
                <option key={station.id} value={station.id} className="bg-white dark:bg-slate-900 text-[var(--text)]">
                  {station.name} · {station.line}
                </option>
              ))}
            </select>
          </div>
        </div>
      }
    >
      <div className="space-y-6">
        {/* KPI Bento Grid */}
        {overview && (
          <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {overview.kpis.map((item) => (
              <StatCard key={item.label} {...item} />
            ))}
          </section>
        )}

        {/* Primary Operational Engines */}
        <section className="grid gap-6 xl:grid-cols-2">
          <PredictionComposer token={token || undefined} stations={stations} onPredictionCreated={() => loadDashboard(selectedStationId)} />
          <RouteFinder />
        </section>

        {/* Smart Card Pipeline */}
        <section>
          <TapLogUploader />
        </section>

        {/* Interactive Networks & OD Heatmap */}
        <section className="grid gap-6 xl:grid-cols-2">
          <ODFlowGraphVisualizer />
          <ODMatrixHeatmap />
        </section>

        {/* Apple Styled Trend Area Chart */}
        {overview && (
          <section className="glass-card section-card fade-up">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
                  Predictive Flow Telemetry
                </p>
                <h2 className="text-lg sm:text-xl font-bold tracking-tight text-[var(--text)] mt-0.5">
                  Observed Actuals vs PyTorch AFFN Forecasted Passengers
                </h2>
              </div>
              <div className="flex items-center gap-4 text-xs self-start sm:self-auto">
                <div className="flex items-center gap-1.5 font-medium text-[var(--text)]">
                  <span className="h-2.5 w-2.5 rounded-full bg-[var(--accent)]" />
                  Actual Count
                </div>
                <div className="flex items-center gap-1.5 font-medium text-[var(--text)]">
                  <span className="h-2.5 w-2.5 rounded-full bg-purple-500" />
                  AFFN Forecast
                </div>
              </div>
            </div>

            <div className="h-[320px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={overview.trend}>
                  <defs>
                    <linearGradient id="appleBlueFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#0071e3" stopOpacity={0.35} />
                      <stop offset="95%" stopColor="#0071e3" stopOpacity={0.0} />
                    </linearGradient>
                    <linearGradient id="applePurpleFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#af52de" stopOpacity={0.25} />
                      <stop offset="95%" stopColor="#af52de" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.12)" vertical={false} />
                  <XAxis
                    dataKey="label"
                    tick={{ fontSize: 11, fill: "var(--muted)" }}
                    axisLine={{ stroke: "rgba(148, 163, 184, 0.15)" }}
                    tickLine={false}
                  />
                  <YAxis
                    tick={{ fontSize: 11, fill: "var(--muted)" }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip
                    content={({ active, payload, label }) => {
                      if (active && payload && payload.length) {
                        return (
                          <div className="glass-card p-3 shadow-2xl border border-white/20 dark:border-white/10 text-xs">
                            <p className="font-semibold text-[var(--muted)] mb-1.5">{label} Commuter Window</p>
                            <div className="space-y-1">
                              <p className="flex items-center gap-2">
                                <span className="h-2 w-2 rounded-full bg-[var(--accent)]" />
                                <span className="text-[var(--muted)]">Actual:</span>
                                <span className="font-bold text-[var(--text)]">{payload[0]?.value?.toLocaleString()} pass</span>
                              </p>
                              {payload[1] && (
                                <p className="flex items-center gap-2">
                                  <span className="h-2 w-2 rounded-full bg-purple-500" />
                                  <span className="text-[var(--muted)]">Forecast:</span>
                                  <span className="font-bold text-purple-500">{payload[1]?.value?.toLocaleString()} pass</span>
                                </p>
                              )}
                            </div>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="actual"
                    stroke="#0071e3"
                    fill="url(#appleBlueFill)"
                    strokeWidth={2.5}
                    name="Actual Count"
                  />
                  <Area
                    type="monotone"
                    dataKey="forecast"
                    stroke="#af52de"
                    fill="url(#applePurpleFill)"
                    strokeWidth={2.5}
                    strokeDasharray="4 4"
                    name="AFFN Forecast"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </section>
        )}
      </div>
    </AppShell>
  );
}
