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
import { ApiError, apiFetch } from "@/lib/api";
import { getStoredToken } from "@/lib/auth";
import type { Station, PredictionResponse, DashboardOverview } from "@/types";

export default function PredictionsDashboardPage() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [stations, setStations] = useState<Station[]>([]);
  const [selectedStationId, setSelectedStationId] = useState("");
  
  // Predict parameters
  const [weatherFactor, setWeatherFactor] = useState(1.0);
  const [eventFactor, setEventFactor] = useState(1.0);
  const [currentCount, setCurrentCount] = useState<number>(350);

  // Predictions output
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
  const [recentPredictions, setRecentPredictions] = useState<PredictionResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const storedToken = getStoredToken();
    if (!storedToken) {
      router.push("/auth");
      return;
    }
    setToken(storedToken);

    // Fetch stations
    apiFetch<Station[]>("/stations", {}, storedToken)
      .then((data) => {
        setStations(data);
        if (data[0]) {
          setSelectedStationId(data[0].id);
        }
      })
      .catch((err) => {
        setError("Failed to load stations.");
      });
  }, [router]);

  async function handlePredict(e: React.FormEvent) {
    e.preventDefault();
    if (!token || !selectedStationId) return;

    setLoading(true);
    setError(null);

    try {
      const res = await apiFetch<PredictionResponse>(
        "/predict",
        {
          method: "POST",
          body: JSON.stringify({
            station_id: selectedStationId,
            weather_factor: weatherFactor,
            event_factor: eventFactor,
            current_count: currentCount,
            horizon_hours: 1
          })
        },
        token
      );
      setPrediction(res);
      // Reload recent predictions list
      const recent = await apiFetch<DashboardOverview>(
        `/dashboard/overview?station_id=${selectedStationId}`,
        {},
        token
      );
      setRecentPredictions(recent.recent_predictions || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Inference calculation failed.");
    } finally {
      setLoading(false);
    }
  }

  // Map horizons to chart format if prediction exists
  const chartData = prediction?.horizons
    ? Object.entries(prediction.horizons).map(([key, val]) => ({
        label: key,
        passengers: val,
        baseline: Math.round(prediction.baseline_count * (key === "15m" ? 1.01 : key === "30m" ? 1.03 : key === "1h" ? 1.08 : key === "3h" ? 1.15 : 0.95))
      }))
    : [];

  return (
    <AppShell
      title="Adaptive Multi-Feature Fusion Forecasts"
      subtitle="Interact with PyTorch STGCN-Attention models to project passenger flow curves and anomaly risks."
    >
      {error && <div className="glass-card section-card text-[var(--danger)] mb-4">{error}</div>}

      <div className="grid gap-6 lg:grid-cols-[0.8fr_1.2fr]">
        {/* Forecast configuration console */}
        <section className="glass-card section-card">
          <h2 className="text-xl font-bold tracking-tight mb-2">Parameters Tweak Console</h2>
          <p className="text-sm text-[var(--muted)] mb-6">
            Modify spatial-temporal parameters and contextual factors to trigger simulation inference weights.
          </p>

          <form onSubmit={handlePredict} className="space-y-5">
            <div>
              <label className="block text-xs uppercase tracking-[0.14em] text-[var(--muted)] mb-2">Target Terminal Station</label>
              <select
                className="select-field w-full"
                value={selectedStationId}
                onChange={(e) => setSelectedStationId(e.target.value)}
              >
                {stations.map((st) => (
                  <option key={st.id} value={st.id}>
                    {st.name} ({st.line})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs uppercase tracking-[0.14em] text-[var(--muted)] mb-2">
                Commuter Load Baseline ({currentCount})
              </label>
              <input
                type="range"
                min="50"
                max="2500"
                step="25"
                value={currentCount}
                onChange={(e) => setCurrentCount(Number(e.target.value))}
                className="w-full h-1 bg-[var(--panel-border)] rounded-lg appearance-none cursor-pointer accent-[var(--accent)]"
              />
            </div>

            <div>
              <label className="block text-xs uppercase tracking-[0.14em] text-[var(--muted)] mb-2">
                Monsoon/Weather Multiplier ({weatherFactor.toFixed(2)}x)
              </label>
              <input
                type="range"
                min="0.6"
                max="1.7"
                step="0.05"
                value={weatherFactor}
                onChange={(e) => setWeatherFactor(Number(e.target.value))}
                className="w-full h-1 bg-[var(--panel-border)] rounded-lg appearance-none cursor-pointer accent-[var(--accent)]"
              />
            </div>

            <div>
              <label className="block text-xs uppercase tracking-[0.14em] text-[var(--muted)] mb-2">
                Festival/Events Multiplier ({eventFactor.toFixed(2)}x)
              </label>
              <input
                type="range"
                min="0.7"
                max="2.2"
                step="0.05"
                value={eventFactor}
                onChange={(e) => setEventFactor(Number(e.target.value))}
                className="w-full h-1 bg-[var(--panel-border)] rounded-lg appearance-none cursor-pointer accent-[var(--accent)]"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="button-primary w-full py-3"
            >
              {loading ? "Re-weighting network layers…" : "Trigger Model Inference"}
            </button>
          </form>
        </section>

        {/* Prediction Outputs and Visualizer */}
        <section className="space-y-6">
          <div className="glass-card section-card">
            <h2 className="text-xl font-bold tracking-tight mb-2">Multi-Horizon Passenger Surge Curve</h2>
            
            {prediction ? (
              <div className="mt-6">
                <div className="h-[280px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={chartData}>
                      <defs>
                        <linearGradient id="predictFill" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.35} />
                          <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.02} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.15)" />
                      <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                      <YAxis tick={{ fontSize: 11 }} />
                      <Tooltip />
                      <Area type="monotone" dataKey="passengers" stroke="#3b82f6" fill="url(#predictFill)" strokeWidth={3} name="Predicted Flow" />
                      <Area type="monotone" dataKey="baseline" stroke="#64748b" fill="transparent" strokeWidth={1.5} strokeDasharray="5 5" name="Blended Baseline" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>

                {/* Recommendation & Anomaly panels */}
                <div className="grid gap-4 md:grid-cols-2 mt-6">
                  <div className="rounded-2xl p-4 bg-[color:var(--panel)] border border-[var(--panel-border)]/50">
                    <p className="text-xs uppercase tracking-[0.14em] text-[var(--muted)]">Model Recommendation</p>
                    <p className="mt-2 text-sm font-semibold">{prediction.recommended_action}</p>
                  </div>
                  <div className="rounded-2xl p-4 bg-[color:var(--panel)] border border-[var(--panel-border)]/50 flex flex-col justify-between">
                    <div>
                      <p className="text-xs uppercase tracking-[0.14em] text-[var(--muted)]">Anomaly Probability</p>
                      <p className="mt-1 text-2xl font-bold font-mono">{(prediction.anomaly_score * 100).toFixed(0)}%</p>
                    </div>
                    {prediction.anomaly_score > 0.15 && (
                      <span className="status-pill bg-red-500/12 text-red-600 scale-90 self-start mt-2">
                        SURGE RISK ALERT
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-20 text-[var(--muted)] text-sm">
                No active forecast query. Tweak the console parameters and click "Trigger Model Inference" to query the network weights.
              </div>
            )}
          </div>
        </section>
      </div>
    </AppShell>
  );
}
