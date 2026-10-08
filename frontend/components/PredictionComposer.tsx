"use client";

import { useEffect, useState } from "react";
import { downloadCsv } from "@/lib/export";
import type { Station } from "@/types";

type PredictionComposerProps = {
  token?: string;
  stations: Station[];
  onPredictionCreated?: () => Promise<void> | void;
};

const HORIZON_OPTIONS = [
  { value: 15, label: "15 min" },
  { value: 30, label: "30 min" },
  { value: 60, label: "1 hour" },
  { value: 1440, label: "24h Daily" },
];

export function PredictionComposer({ token, stations, onPredictionCreated }: PredictionComposerProps) {
  const [originId, setOriginId] = useState("");
  const [destId, setDestId] = useState("");
  const [horizonMins, setHorizonMins] = useState(15);
  const [weatherFactor, setWeatherFactor] = useState(1);
  const [eventFactor, setEventFactor] = useState(1);
  const [prediction, setPrediction] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (stations.length >= 2) {
      if (!originId) setOriginId(stations[0].id);
      if (!destId) setDestId(stations[1]?.id || stations[0].id);
    } else if (stations.length === 1) {
      if (!originId) setOriginId(stations[0].id);
      if (!destId) setDestId(stations[0].id);
    }
  }, [stations, originId, destId]);

  function handleSwapStations() {
    const temp = originId;
    setOriginId(destId);
    setDestId(temp);
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);

    const origStation = stations.find((s) => s.id === originId) || stations[0];
    const destStation = stations.find((s) => s.id === destId) || stations[1] || stations[0];

    const horizonLabel = horizonMins <= 15 ? "15 mins" : horizonMins <= 30 ? "30 mins" : horizonMins <= 60 ? "1 hour" : "Daily (24h)";

    try {
      const res = await fetch("/api/v1/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          origin_station_id: originId || stations[0]?.id,
          destination_station_id: destId || stations[1]?.id || stations[0]?.id,
          station_id: originId || stations[0]?.id,
          horizon_minutes: horizonMins,
          horizon_hours: Math.max(1, Math.round(horizonMins / 60)),
          weather_factor: weatherFactor,
          event_factor: eventFactor,
        }),
      });

      if (res.ok) {
        const json = await res.json();
        const predicted = json.predicted_count ?? 0;
        const congestion =
          json.congestion_level ??
          (predicted > 1500 ? "Severe" : predicted > 1200 ? "High" : predicted > 800 ? "Moderate" : "Low");
        setPrediction({
          origin_name: json.origin_station_name ?? origStation?.name ?? "—",
          destination_name: json.destination_station_name ?? destStation?.name ?? "—",
          current_passengers: json.current_passengers ?? 0,
          predicted_count: predicted,
          horizon_label: horizonLabel,
          horizons: json.horizons ?? { "15m": predicted, "30m": predicted, "1h": predicted, "24h": predicted * 18 },
          congestion_level: congestion,
          confidence_score: json.confidence_score ?? 0,
          confidence_percentage: json.confidence_percentage ?? `${Math.round((json.confidence_score ?? 0) * 100)}%`,
          st_weight: json.st_weight ?? 0.5,
          ext_weight: json.ext_weight ?? 0.5,
          recommended_action: json.recommended_action ?? "Monitor corridor and maintain scheduled headways.",
          generated_at: json.generated_at ?? new Date().toISOString(),
        });
      } else {
        const errText = await res.text().catch(() => "Unknown error");
        throw new Error(`API error ${res.status}: ${errText}`);
      }
      if (onPredictionCreated) await onPredictionCreated();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Prediction failed. Is the backend running?");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="glass-card section-card fade-up">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-5">
        <div>
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-blue-500/10 text-[var(--accent)] border border-blue-500/20">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <h2 className="text-base sm:text-lg font-semibold tracking-tight text-[var(--text)]">
              AFFN Flow Predictor
            </h2>
            <span className="rounded-full bg-blue-500/10 dark:bg-blue-400/15 px-2 py-0.5 text-[10px] font-semibold text-[var(--accent)]">
              PyTorch
            </span>
          </div>
          <p className="text-xs text-[var(--muted)] mt-1">
            Adaptive Feature Fusion Network modeling multi-horizon passenger density.
          </p>
        </div>

        {prediction && (
          <button
            type="button"
            className="button-secondary text-xs py-1.5 px-3 self-start sm:self-auto"
            onClick={() =>
              downloadCsv("metroflownet-od-prediction.csv", [
                {
                  origin: prediction.origin_name,
                  destination: prediction.destination_name,
                  current_passengers: prediction.current_passengers,
                  predicted_count: prediction.predicted_count,
                  horizon: prediction.horizon_label,
                  congestion_level: prediction.congestion_level,
                  confidence: prediction.confidence_percentage,
                  st_weight: prediction.st_weight,
                  ext_weight: prediction.ext_weight,
                },
              ])
            }
          >
            Export CSV
          </button>
        )}
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Origin & Destination with Cupertino Swap Button */}
        <div className="grid grid-cols-1 sm:grid-cols-[1fr_auto_1fr] items-center gap-2.5">
          <div>
            <label className="text-[11px] font-semibold uppercase tracking-wider text-[var(--muted)] mb-1 block">
              Origin Station
            </label>
            <select
              className="select-field text-xs"
              value={originId}
              onChange={(e) => setOriginId(e.target.value)}
            >
              {stations.map((s) => (
                <option key={s.id} value={s.id} className="bg-white dark:bg-slate-900 text-[var(--text)]">
                  {s.name} ({s.line})
                </option>
              ))}
            </select>
          </div>

          <div className="flex justify-center pt-4 sm:pt-4">
            <button
              type="button"
              onClick={handleSwapStations}
              className="flex h-8 w-8 items-center justify-center rounded-full border border-[var(--panel-border)] bg-black/[0.03] dark:bg-white/[0.06] text-[var(--muted)] hover:text-[var(--text)] hover:scale-105 active:scale-95 transition-all"
              title="Swap Origin and Destination"
            >
              ⇄
            </button>
          </div>

          <div>
            <label className="text-[11px] font-semibold uppercase tracking-wider text-[var(--muted)] mb-1 block">
              Destination Station
            </label>
            <select
              className="select-field text-xs"
              value={destId}
              onChange={(e) => setDestId(e.target.value)}
            >
              {stations.map((s) => (
                <option key={s.id} value={s.id} className="bg-white dark:bg-slate-900 text-[var(--text)]">
                  {s.name} ({s.line})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Cupertino Segmented Horizon Selector */}
        <div>
          <label className="text-[11px] font-semibold uppercase tracking-wider text-[var(--muted)] mb-1.5 block">
            Prediction Horizon
          </label>
          <div className="apple-segmented-track w-full justify-between">
            {HORIZON_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                type="button"
                className={`apple-segmented-item flex-1 text-center py-1.5 ${
                  horizonMins === opt.value ? "active" : ""
                }`}
                onClick={() => setHorizonMins(opt.value)}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        {/* Sliders for Weather & Event Multipliers */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
          <div className="rounded-xl border border-[var(--panel-border)] bg-black/[0.02] dark:bg-white/[0.03] p-3">
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-[var(--muted)]">Weather Factor</span>
              <span className="font-mono font-semibold text-[var(--accent)]">{weatherFactor.toFixed(2)}x</span>
            </div>
            <input
              type="range"
              min="0.7"
              max="1.8"
              step="0.05"
              value={weatherFactor}
              onChange={(e) => setWeatherFactor(Number(e.target.value))}
              className="w-full accent-[var(--accent)] cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-[var(--muted)] mt-0.5">
              <span>0.7x (Clear)</span>
              <span>1.8x (Monsoon)</span>
            </div>
          </div>

          <div className="rounded-xl border border-[var(--panel-border)] bg-black/[0.02] dark:bg-white/[0.03] p-3">
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-[var(--muted)]">Event Multiplier</span>
              <span className="font-mono font-semibold text-purple-500">{eventFactor.toFixed(2)}x</span>
            </div>
            <input
              type="range"
              min="0.7"
              max="2.5"
              step="0.05"
              value={eventFactor}
              onChange={(e) => setEventFactor(Number(e.target.value))}
              className="w-full accent-purple-500 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-[var(--muted)] mt-0.5">
              <span>0.7x (Regular)</span>
              <span>2.5x (Festival Peak)</span>
            </div>
          </div>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={loading}
          className="button-primary w-full py-3"
        >
          {loading ? (
            <span className="flex items-center gap-2">
              <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Inferring PyTorch AFFN Model...
            </span>
          ) : (
            <span className="flex items-center gap-2">
              <span>⚡</span> Generate Real-Time Forecast
            </span>
          )}
        </button>
      </form>

      {error && (
        <div className="mt-4 px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/20 text-xs text-[var(--danger)] flex items-start gap-2">
          <span>⚠️</span>
          <span>{error}</span>
        </div>
      )}

      {/* Prediction Output Section */}
      {prediction && (
        <div className="mt-6 rounded-2xl border border-[var(--panel-border)] bg-black/[0.02] dark:bg-white/[0.04] p-5 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--panel-border)] pb-3">
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold text-[var(--text)]">{prediction.origin_name}</span>
              <span className="text-[var(--accent)] font-bold">→</span>
              <span className="text-sm font-bold text-[var(--text)]">{prediction.destination_name}</span>
            </div>

            <div className="flex items-center gap-2">
              <span
                className={`status-pill ${
                  prediction.congestion_level === "Severe"
                    ? "bg-red-500/15 text-[var(--danger)] border border-red-500/25"
                    : prediction.congestion_level === "High"
                    ? "bg-amber-500/15 text-[var(--warning)] border border-amber-500/25"
                    : "bg-emerald-500/15 text-[var(--good)] border border-emerald-500/25"
                }`}
              >
                <span className="h-1.5 w-1.5 rounded-full bg-current" />
                {prediction.congestion_level} Congestion
              </span>

              <span className="status-pill bg-blue-500/15 text-[var(--accent)] border border-blue-500/25">
                {prediction.confidence_percentage} Confidence
              </span>
            </div>
          </div>

          {/* Bento metric cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
            <div className="rounded-xl border border-[var(--panel-border)] bg-white/40 dark:bg-black/20 p-3">
              <span className="text-[10px] uppercase tracking-wider text-[var(--muted)] block">Current Volume</span>
              <span className="text-lg font-bold text-[var(--text)]">{prediction.current_passengers.toLocaleString()}</span>
            </div>

            <div className="rounded-xl border border-[var(--accent)]/30 bg-[var(--accent)]/5 p-3">
              <span className="text-[10px] uppercase tracking-wider text-[var(--accent)] block">Predicted ({prediction.horizon_label})</span>
              <span className="text-lg font-bold text-[var(--accent)]">{prediction.predicted_count.toLocaleString()}</span>
            </div>

            <div className="rounded-xl border border-[var(--panel-border)] bg-white/40 dark:bg-black/20 p-3">
              <span className="text-[10px] uppercase tracking-wider text-[var(--muted)] block">30m Horizon</span>
              <span className="text-lg font-bold text-indigo-500">{prediction.horizons["30m"].toLocaleString()}</span>
            </div>

            <div className="rounded-xl border border-[var(--panel-border)] bg-white/40 dark:bg-black/20 p-3">
              <span className="text-[10px] uppercase tracking-wider text-[var(--muted)] block">24h Projection</span>
              <span className="text-lg font-bold text-purple-500">
                {(prediction.horizons?.["24h"] ?? prediction.predicted_count * 18).toLocaleString()}
              </span>
            </div>
          </div>

          {/* Feature Attention Weights Track */}
          <div className="space-y-1.5 pt-1">
            <div className="flex items-center justify-between text-xs">
              <span className="text-[11px] font-semibold text-[var(--muted)] uppercase tracking-wider">
                Learned Attention Distribution
              </span>
              <span className="text-[10px] text-[var(--muted)]">Softmax Gated</span>
            </div>

            <div className="w-full bg-black/[0.06] dark:bg-white/[0.08] h-2.5 rounded-full overflow-hidden flex p-0.5 gap-0.5">
              <div
                className="bg-gradient-to-r from-blue-500 to-cyan-400 h-full rounded-full transition-all duration-500"
                style={{ width: `${prediction.st_weight * 100}%` }}
                title={`Spatial-Temporal: ${(prediction.st_weight * 100).toFixed(1)}%`}
              />
              <div
                className="bg-gradient-to-r from-indigo-500 to-purple-500 h-full rounded-full transition-all duration-500"
                style={{ width: `${prediction.ext_weight * 100}%` }}
                title={`External Context: ${(prediction.ext_weight * 100).toFixed(1)}%`}
              />
            </div>

            <div className="flex justify-between text-[11px] font-medium pt-0.5">
              <span className="text-[var(--accent)]">Spatial-Temporal: {(prediction.st_weight * 100).toFixed(0)}%</span>
              <span className="text-purple-500">External Context: {(prediction.ext_weight * 100).toFixed(0)}%</span>
            </div>
          </div>

          <div className="rounded-xl bg-blue-500/5 dark:bg-blue-400/5 border border-blue-500/15 p-3 text-xs text-[var(--muted)]">
            <strong className="text-[var(--text)] font-semibold">Recommended Dispatch: </strong>
            {prediction.recommended_action}
          </div>
        </div>
      )}
    </div>
  );
}
