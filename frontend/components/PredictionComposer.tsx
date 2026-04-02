"use client";

import { useEffect, useState } from "react";

import { apiFetch } from "@/lib/api";
import { downloadCsv } from "@/lib/export";
import { formatDateTime, formatNumber } from "@/lib/format";
import type { Prediction, Station } from "@/types";

type PredictionComposerProps = {
  token: string;
  stations: Station[];
  onPredictionCreated: () => Promise<void> | void;
};

export function PredictionComposer({ token, stations, onPredictionCreated }: PredictionComposerProps) {
  const [stationId, setStationId] = useState("");
  const [horizonHours, setHorizonHours] = useState(1);
  const [weatherFactor, setWeatherFactor] = useState(1);
  const [eventFactor, setEventFactor] = useState(1);
  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (stations.length && !stationId) {
      setStationId(stations[0].id);
    }
  }, [stationId, stations]);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await apiFetch<Prediction>(
        "/predict",
        {
          method: "POST",
          body: JSON.stringify({
            station_id: stationId,
            horizon_hours: horizonHours,
            weather_factor: weatherFactor,
            event_factor: eventFactor
          })
        },
        token
      );
      setPrediction(response);
      await onPredictionCreated();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to generate prediction.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="glass-card section-card fade-up">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">Forecast Composer</p>
          <h2 className="mt-2 text-2xl font-semibold tracking-[-0.03em]">Generate a station-level passenger forecast</h2>
        </div>
        {prediction ? (
          <button
            type="button"
            className="button-secondary"
            onClick={() =>
              downloadCsv("metroflow-prediction.csv", [
                {
                  station: prediction.station_name,
                  line: prediction.line,
                  target_timestamp: prediction.target_timestamp,
                  predicted_count: prediction.predicted_count,
                  baseline_count: prediction.baseline_count,
                  confidence_score: prediction.confidence_score,
                  anomaly_score: prediction.anomaly_score,
                  recommendation: prediction.recommended_action
                }
              ])
            }
          >
            Export CSV
          </button>
        ) : null}
      </div>

      <form onSubmit={handleSubmit} className="mt-6 grid gap-4 md:grid-cols-2">
        <label className="space-y-2">
          <span className="text-sm font-medium">Station</span>
          <select className="select-field" value={stationId} onChange={(event) => setStationId(event.target.value)}>
            {stations.map((station) => (
              <option key={station.id} value={station.id}>
                {station.name} · {station.line}
              </option>
            ))}
          </select>
        </label>

        <label className="space-y-2">
          <span className="text-sm font-medium">Horizon</span>
          <select
            className="select-field"
            value={horizonHours}
            onChange={(event) => setHorizonHours(Number(event.target.value))}
          >
            {[1, 2, 4, 8, 12, 24].map((hours) => (
              <option key={hours} value={hours}>
                {hours} hour{hours > 1 ? "s" : ""}
              </option>
            ))}
          </select>
        </label>

        <label className="space-y-2">
          <span className="text-sm font-medium">Weather Factor</span>
          <input
            className="input-field"
            type="number"
            min="0.6"
            max="1.7"
            step="0.05"
            value={weatherFactor}
            onChange={(event) => setWeatherFactor(Number(event.target.value))}
          />
        </label>

        <label className="space-y-2">
          <span className="text-sm font-medium">Event Factor</span>
          <input
            className="input-field"
            type="number"
            min="0.7"
            max="2.2"
            step="0.05"
            value={eventFactor}
            onChange={(event) => setEventFactor(Number(event.target.value))}
          />
        </label>

        <div className="md:col-span-2 flex items-center justify-between gap-3">
          <p className="text-sm text-[var(--muted)]">Predictions are generated from recent station history plus the Python ML module.</p>
          <button type="submit" className="button-primary" disabled={loading}>
            {loading ? "Forecasting..." : "Generate Prediction"}
          </button>
        </div>
      </form>

      {error ? <p className="mt-4 text-sm text-[var(--danger)]">{error}</p> : null}

      {prediction ? (
        <div className="mt-6 grid gap-3 rounded-[26px] bg-[color:var(--panel)] p-4 md:grid-cols-2">
          <div>
            <p className="text-sm text-[var(--muted)]">Predicted passenger count</p>
            <p className="mt-2 text-3xl font-semibold">{formatNumber(Math.round(prediction.predicted_count))}</p>
            <p className="mt-2 text-sm text-[var(--muted)]">{prediction.station_name} · {prediction.line}</p>
          </div>
          <div className="space-y-2 text-sm">
            <p>
              <span className="text-[var(--muted)]">Target time:</span> {formatDateTime(prediction.target_timestamp)}
            </p>
            <p>
              <span className="text-[var(--muted)]">Confidence:</span> {(prediction.confidence_score * 100).toFixed(0)}%
            </p>
            <p>
              <span className="text-[var(--muted)]">Anomaly score:</span> {(prediction.anomaly_score * 100).toFixed(0)}%
            </p>
            <p className="text-[var(--muted)]">{prediction.recommended_action}</p>
          </div>
        </div>
      ) : null}
    </div>
  );
}
