"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { AppShell } from "@/components/AppShell";
import { ApiError, apiFetch } from "@/lib/api";
import { getStoredToken, getStoredUser } from "@/lib/auth";
import { formatDateTime, formatNumber } from "@/lib/format";
import type { PassengerFlow, Station, TrainResult, User } from "@/types";

function getDefaultTimestamp() {
  const now = new Date();
  now.setMinutes(0, 0, 0);
  return new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
}

export default function AdminPage() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [stations, setStations] = useState<Station[]>([]);
  const [flows, setFlows] = useState<PassengerFlow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [trainResult, setTrainResult] = useState<TrainResult | null>(null);
  const [saving, setSaving] = useState(false);
  const [training, setTraining] = useState(false);
  const [currentUser, setCurrentUser] = useState<User | null>(null);

  const [flowForm, setFlowForm] = useState({
    station_id: "",
    timestamp: getDefaultTimestamp(),
    passenger_count: 320,
    avg_dwell_minutes: 3.1,
    weather_code: "clear",
    event_flag: false,
    event_name: "",
    source: "admin-upload"
  });

  const [trainForm, setTrainForm] = useState({
    epochs: 24,
    learning_rate: 0.001,
    lookback_steps: 24
  });

  async function loadAdminData(activeToken: string) {
    const [stationsResponse, flowsResponse] = await Promise.all([
      apiFetch<Station[]>("/stations", {}, activeToken),
      apiFetch<PassengerFlow[]>("/admin/flows", {}, activeToken)
    ]);
    setStations(stationsResponse);
    setFlows(flowsResponse);
    if (!flowForm.station_id && stationsResponse[0]) {
      setFlowForm((current) => ({ ...current, station_id: stationsResponse[0].id }));
    }
  }

  useEffect(() => {
    const storedToken = getStoredToken();
    if (!storedToken) {
      router.push("/auth");
      return;
    }
    setCurrentUser(getStoredUser());
    setToken(storedToken);

    loadAdminData(storedToken).catch((requestError) => {
      if (requestError instanceof ApiError && requestError.isAuthError) {
        router.push("/auth");
        return;
      }
      setError(requestError instanceof Error ? requestError.message : "Unable to load admin data.");
    });
  }, [router]);

  async function handleCreateFlow(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) {
      return;
    }

    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      await apiFetch<PassengerFlow>(
        "/admin/flows",
        {
          method: "POST",
          body: JSON.stringify({
            ...flowForm,
            timestamp: new Date(flowForm.timestamp).toISOString(),
            event_name: flowForm.event_name || null
          })
        },
        token
      );
      await loadAdminData(token);
      setMessage("Flow record created.");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to create flow record.");
    } finally {
      setSaving(false);
    }
  }

  async function handleTrainModel(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) {
      return;
    }

    setTraining(true);
    setError(null);
    try {
      const response = await apiFetch<TrainResult>(
        "/train",
        {
          method: "POST",
          body: JSON.stringify(trainForm)
        },
        token
      );
      setTrainResult(response);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to train model.");
    } finally {
      setTraining(false);
    }
  }

  if (currentUser?.role !== "admin") {
    return (
      <AppShell title="Admin Console" subtitle="Restricted tools for data upload and model maintenance.">
        <div className="glass-card section-card">
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">Access Restricted</p>
          <h2 className="mt-2 text-2xl font-semibold">Admin privileges are required for this page.</h2>
          <p className="mt-3 text-sm text-[var(--muted)]">
            You can still use the forecasting and historical analytics tools from the regular dashboard.
          </p>
          <Link href="/dashboard" className="button-primary mt-6">
            Back to Dashboard
          </Link>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell
      title="Admin Console"
      subtitle="Upload new station flow records and retrain the forecasting module."
    >
      {error ? <div className="glass-card section-card text-[var(--danger)]">{error}</div> : null}
      {message ? <div className="glass-card section-card text-[var(--good)]">{message}</div> : null}

      <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <section className="glass-card section-card fade-up">
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">Upload Flow Record</p>
          <form onSubmit={handleCreateFlow} className="mt-6 grid gap-4">
            <label className="space-y-2">
              <span className="text-sm font-medium">Station</span>
              <select
                className="select-field"
                value={flowForm.station_id}
                onChange={(event) => setFlowForm((current) => ({ ...current, station_id: event.target.value }))}
              >
                {stations.map((station) => (
                  <option key={station.id} value={station.id}>
                    {station.name} · {station.line}
                  </option>
                ))}
              </select>
            </label>

            <label className="space-y-2">
              <span className="text-sm font-medium">Timestamp</span>
              <input
                className="input-field"
                type="datetime-local"
                value={flowForm.timestamp}
                onChange={(event) => setFlowForm((current) => ({ ...current, timestamp: event.target.value }))}
              />
            </label>

            <div className="grid gap-4 md:grid-cols-2">
              <label className="space-y-2">
                <span className="text-sm font-medium">Passenger Count</span>
                <input
                  className="input-field"
                  type="number"
                  value={flowForm.passenger_count}
                  onChange={(event) =>
                    setFlowForm((current) => ({ ...current, passenger_count: Number(event.target.value) }))
                  }
                />
              </label>

              <label className="space-y-2">
                <span className="text-sm font-medium">Dwell Minutes</span>
                <input
                  className="input-field"
                  type="number"
                  step="0.1"
                  value={flowForm.avg_dwell_minutes}
                  onChange={(event) =>
                    setFlowForm((current) => ({ ...current, avg_dwell_minutes: Number(event.target.value) }))
                  }
                />
              </label>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <label className="space-y-2">
                <span className="text-sm font-medium">Weather Code</span>
                <select
                  className="select-field"
                  value={flowForm.weather_code}
                  onChange={(event) => setFlowForm((current) => ({ ...current, weather_code: event.target.value }))}
                >
                  <option value="clear">Clear</option>
                  <option value="cloudy">Cloudy</option>
                  <option value="rain">Rain</option>
                </select>
              </label>

              <label className="space-y-2">
                <span className="text-sm font-medium">Source</span>
                <input
                  className="input-field"
                  value={flowForm.source}
                  onChange={(event) => setFlowForm((current) => ({ ...current, source: event.target.value }))}
                />
              </label>
            </div>

            <label className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={flowForm.event_flag}
                onChange={(event) => setFlowForm((current) => ({ ...current, event_flag: event.target.checked }))}
              />
              <span className="text-sm font-medium">Event-linked demand spike</span>
            </label>

            <label className="space-y-2">
              <span className="text-sm font-medium">Event Name</span>
              <input
                className="input-field"
                value={flowForm.event_name}
                onChange={(event) => setFlowForm((current) => ({ ...current, event_name: event.target.value }))}
                placeholder="Optional"
              />
            </label>

            <button type="submit" className="button-primary" disabled={saving}>
              {saving ? "Saving..." : "Create Flow Record"}
            </button>
          </form>
        </section>

        <section className="glass-card section-card fade-up">
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">Model Maintenance</p>
          <form onSubmit={handleTrainModel} className="mt-6 grid gap-4">
            <div className="grid gap-4 md:grid-cols-3">
              <label className="space-y-2">
                <span className="text-sm font-medium">Epochs</span>
                <input
                  className="input-field"
                  type="number"
                  value={trainForm.epochs}
                  onChange={(event) => setTrainForm((current) => ({ ...current, epochs: Number(event.target.value) }))}
                />
              </label>

              <label className="space-y-2">
                <span className="text-sm font-medium">Learning Rate</span>
                <input
                  className="input-field"
                  type="number"
                  step="0.0001"
                  value={trainForm.learning_rate}
                  onChange={(event) =>
                    setTrainForm((current) => ({ ...current, learning_rate: Number(event.target.value) }))
                  }
                />
              </label>

              <label className="space-y-2">
                <span className="text-sm font-medium">Lookback Steps</span>
                <input
                  className="input-field"
                  type="number"
                  value={trainForm.lookback_steps}
                  onChange={(event) =>
                    setTrainForm((current) => ({ ...current, lookback_steps: Number(event.target.value) }))
                  }
                />
              </label>
            </div>

            <button type="submit" className="button-primary" disabled={training}>
              {training ? "Training..." : "Run Training"}
            </button>
          </form>

          {trainResult ? (
            <div className="mt-6 rounded-[24px] bg-[color:var(--panel)] p-4 text-sm">
              <p className="font-semibold">{trainResult.message}</p>
              <p className="mt-2 text-[var(--muted)]">
                RMSE {trainResult.rmse} · MAE {trainResult.mae} · Version {trainResult.model_version}
              </p>
            </div>
          ) : null}

          <div className="table-shell mt-8 overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Station</th>
                  <th>Passengers</th>
                  <th>Context</th>
                </tr>
              </thead>
              <tbody>
                {flows.map((flow) => (
                  <tr key={flow.id}>
                    <td>{formatDateTime(flow.timestamp)}</td>
                    <td>
                      <div className="font-semibold">{flow.station_name}</div>
                      <div className="text-xs text-[var(--muted)]">{flow.line}</div>
                    </td>
                    <td>{formatNumber(flow.passenger_count)}</td>
                    <td>{flow.event_flag ? flow.event_name ?? "Event-linked" : flow.weather_code}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </AppShell>
  );
}
