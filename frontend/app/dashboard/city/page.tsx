"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { AppShell } from "@/components/AppShell";
import { ApiError, apiFetch } from "@/lib/api";
import { getStoredToken } from "@/lib/auth";
import { formatNumber } from "@/lib/format";
import { StatCard } from "@/components/StatCard";

interface StationLoad {
  id: string;
  code: string;
  name: string;
  line: string;
  latitude: number;
  longitude: number;
  baseline_capacity: number;
  is_interchange: boolean;
  current_flow: number;
  load_level: "good" | "warning" | "critical";
}

interface TrainState {
  id: string;
  code: string;
  name: string;
  line: string;
  capacity: number;
  status: string;
  speed_kmh: number;
  current_station_code: string;
}

interface ODMatrixItem {
  origin_station_code: string;
  origin_station_name: string;
  destination_station_code: string;
  destination_station_name: string;
  passenger_flow: number;
}

interface CityNetworkDetails {
  city: string;
  state: string;
  stations: StationLoad[];
  trains: TrainState[];
  od_matrix: ODMatrixItem[];
}

const AVAILABLE_CITIES = ["Delhi", "Bengaluru", "Mumbai", "Hyderabad", "Chennai", "Kolkata", "Kochi", "Pune", "Srinagar"];

function CityDashboardContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [token, setToken] = useState<string | null>(null);
  
  const selectedCity = searchParams.get("city") || "Delhi";
  const [network, setNetwork] = useState<CityNetworkDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedStation, setSelectedStation] = useState<StationLoad | null>(null);

  useEffect(() => {
    const storedToken = getStoredToken();
    if (!storedToken) {
      router.push("/auth");
      return;
    }
    setToken(storedToken);
    loadCityDetails(selectedCity, storedToken);
  }, [selectedCity, router]);

  function loadCityDetails(city: string, activeToken: string) {
    setLoading(true);
    setError(null);
    apiFetch<CityNetworkDetails>(`/networks/city/${city}`, {}, activeToken)
      .then((data) => {
        setNetwork(data);
        if (data.stations.length > 0) {
          setSelectedStation(data.stations[0]);
        }
        setLoading(false);
      })
      .catch((err) => {
        if (err instanceof ApiError && err.isAuthError) {
          router.push("/auth");
          return;
        }
        setError(err instanceof Error ? err.message : "Failed to load network details.");
        setLoading(false);
      });
  }

  function handleCityChange(newCity: string) {
    router.push(`/dashboard/city?city=${newCity}`);
  }

  return (
    <AppShell
      title={`${selectedCity} Transit Network`}
      subtitle="GIS line topology mapping, real-time train positions, and origin-destination flow matrices."
      actions={
        <select
          className="select-field min-w-[200px]"
          value={selectedCity}
          onChange={(e) => handleCityChange(e.target.value)}
        >
          {AVAILABLE_CITIES.map((city) => (
            <option key={city} value={city}>
              {city} Network
            </option>
          ))}
        </select>
      }
    >
      {loading && (
        <div className="glass-card section-card text-center py-12 animate-pulse text-[var(--muted)]">
          Fetching network topology for {selectedCity}…
        </div>
      )}
      {error && <div className="glass-card section-card text-[var(--danger)]">{error}</div>}

      {network && !loading && (
        <div className="space-y-6">
          {/* Operations Metrics */}
          <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard
              label="Trains in Service"
              value={network.trains.length.toString()}
              change="Subways synced & running"
              tone="good"
            />
            <StatCard
              label="Average Speed"
              value="41.2 km/h"
              change="Within target schedules"
              tone="neutral"
            />
            <StatCard
              label="Line Congestion Index"
              value={network.stations.some(s => s.load_level === "critical") ? "High Risk" : "Normal"}
              change="Based on platform densities"
              tone={network.stations.some(s => s.load_level === "critical") ? "critical" : "good"}
            />
            <StatCard
              label="Active Interchange Hubs"
              value={network.stations.filter(s => s.is_interchange).length.toString()}
              change="Multi-corridor terminals"
              tone="neutral"
            />
          </section>

          {/* Interactive Topology and Detail Inspector */}
          <section className="grid gap-6 lg:grid-cols-[1.3fr_0.7fr]">
            {/* GIS SVG Topology Mapping */}
            <div className="glass-card section-card flex flex-col items-center">
              <div className="w-full border-b border-[var(--panel-border)] pb-3 mb-4 flex justify-between items-center">
                <div>
                  <h2 className="text-xl font-bold tracking-tight">Active GIS Line Topology</h2>
                  <p className="text-xs text-[var(--muted)]">Inspect corridors, interchange status, and real-time crowd heat.</p>
                </div>
              </div>

              {/* Renders dynamic coordinate grid representing station layouts */}
              <div className="relative w-full h-[400px] bg-[color:var(--panel)] rounded-2xl overflow-hidden border border-[var(--panel-border)]/50 flex items-center justify-center p-4">
                <svg viewBox="0 0 800 400" className="w-full h-full text-slate-700 select-none">
                  {/* Drawing connections (Lines) */}
                  <path
                    d="M 100,200 L 250,200 L 400,200 L 550,200 L 700,200"
                    fill="none"
                    stroke="#3b82f6"
                    strokeWidth="5"
                    opacity="0.6"
                  />
                  <path
                    d="M 250,80 L 250,200 L 250,320"
                    fill="none"
                    stroke="#10b981"
                    strokeWidth="5"
                    opacity="0.6"
                  />
                  <path
                    d="M 550,80 L 550,200 L 550,320"
                    fill="none"
                    stroke="#f59e0b"
                    strokeWidth="5"
                    opacity="0.6"
                  />

                  {/* Draw Stations as nodes */}
                  {network.stations.map((st, index) => {
                    // Lay out nodes systematically on grid for visual clarity
                    const row = index % 3;
                    const col = Math.floor(index / 3);
                    const x = 120 + col * 160;
                    const y = 100 + row * 100;

                    const isSelected = selectedStation?.id === st.id;
                    const color =
                      st.load_level === "critical"
                        ? "fill-red-500"
                        : st.load_level === "warning"
                          ? "fill-amber-500"
                          : "fill-emerald-500";

                    return (
                      <g
                        key={st.id}
                        className="cursor-pointer"
                        onClick={() => setSelectedStation(st)}
                      >
                        {/* Outer Glow ring */}
                        <circle
                          cx={x}
                          cy={y}
                          r={isSelected ? 18 : st.is_interchange ? 14 : 10}
                          className={`${color}/20 stroke-[var(--panel-border)] transition-all`}
                          strokeWidth={isSelected ? 3 : 1}
                        />
                        {/* Core station dot */}
                        <circle
                          cx={x}
                          cy={y}
                          r={st.is_interchange ? 7 : 5}
                          className={`${color} transition-all`}
                        />
                        {/* Text label */}
                        <text
                          x={x}
                          y={y - 18}
                          textAnchor="middle"
                          className={`text-[10px] font-semibold fill-[var(--text)] transition-all ${
                            isSelected ? "text-xs font-bold fill-[var(--accent)]" : "opacity-80"
                          }`}
                        >
                          {st.name}
                        </text>
                      </g>
                    );
                  })}
                </svg>
              </div>
            </div>

            {/* Station details & active watchlist */}
            <div className="glass-card section-card flex flex-col justify-between">
              <div>
                <h2 className="text-xl font-bold tracking-tight mb-2">Station Load Inspector</h2>
                {selectedStation ? (
                  <div className="space-y-4 mt-4">
                    <div className="rounded-2xl bg-[color:var(--panel)] p-4 border border-[var(--panel-border)]/50">
                      <p className="text-xs uppercase tracking-[0.14em] text-[var(--muted)]">Selected Terminal</p>
                      <h3 className="text-2xl font-bold mt-1 text-[var(--accent)]">{selectedStation.name}</h3>
                      <p className="text-sm text-[var(--muted)] mt-1">{selectedStation.line} Corridor · Zone {selectedStation.code.slice(0,3)}</p>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div className="rounded-xl bg-[color:var(--panel)] p-3">
                        <p className="text-xs text-[var(--muted)]">Ridership Flow</p>
                        <p className="text-xl font-bold mt-1 font-mono">{formatNumber(selectedStation.current_flow)} /h</p>
                      </div>
                      <div className="rounded-xl bg-[color:var(--panel)] p-3">
                        <p className="text-xs text-[var(--muted)]">Design Capacity</p>
                        <p className="text-xl font-bold mt-1 font-mono">{formatNumber(selectedStation.baseline_capacity)}</p>
                      </div>
                    </div>

                    <div className="flex items-center justify-between rounded-xl bg-[color:var(--panel)] p-3">
                      <div>
                        <p className="text-xs text-[var(--muted)]">Current Load Level</p>
                        <p className="text-sm font-semibold capitalize mt-1">{selectedStation.load_level}</p>
                      </div>
                      <span
                        className={`status-pill ${
                          selectedStation.load_level === "critical"
                            ? "bg-red-500/12 text-red-600"
                            : selectedStation.load_level === "warning"
                              ? "bg-amber-500/12 text-amber-600"
                              : "bg-emerald-500/12 text-emerald-600"
                        }`}
                      >
                        {selectedStation.load_level.toUpperCase()}
                      </span>
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-[var(--muted)]">Click on a station node to inspect details.</p>
                )}
              </div>

              {/* Active Trains listing */}
              <div className="mt-6 pt-4 border-t border-[var(--panel-border)]">
                <h3 className="text-sm font-bold uppercase tracking-[0.14em] text-[var(--muted)] mb-3">Live Trains Tracker</h3>
                <div className="space-y-2 max-h-[140px] overflow-y-auto">
                  {network.trains.map((train) => (
                    <div key={train.id} className="flex items-center justify-between p-2 rounded-lg bg-[color:var(--panel)] text-xs">
                      <div>
                        <span className="font-semibold">{train.name}</span>
                        <span className="text-[var(--muted)] ml-2">({train.line})</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono">{train.speed_kmh} km/h</span>
                        <span className="status-pill bg-emerald-500/12 text-emerald-600 scale-90">LIVE</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </section>

          {/* Animated OD Flow Matrix Panel */}
          <section className="glass-card section-card">
            <h2 className="text-xl font-bold tracking-tight mb-2">Adaptive Origin-Destination (OD) Flow Matrix</h2>
            <p className="text-sm text-[var(--muted)] mb-4">
              Real-time visualization of commuter paths and boarding density between source and exit stations.
            </p>
            <div className="table-shell overflow-x-auto max-h-[300px]">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Boarding Terminal (Origin)</th>
                    <th>Exit Terminal (Destination)</th>
                    <th className="text-right">Commuters Flow Volume /hr</th>
                    <th>Load Profile Indicator</th>
                  </tr>
                </thead>
                <tbody>
                  {network.od_matrix.map((row, idx) => (
                    <tr key={idx} className="hover:bg-[var(--panel-border)]/10 transition-colors">
                      <td className="font-semibold">{row.origin_station_name}</td>
                      <td className="font-semibold">{row.destination_station_name}</td>
                      <td className="text-right font-mono font-medium">{formatNumber(row.passenger_flow)}</td>
                      <td>
                        <div className="w-full bg-[var(--panel)] rounded-full h-2 overflow-hidden border border-[var(--panel-border)]/40">
                          <div
                            className={`h-full rounded-full ${
                              row.passenger_flow > 250
                                ? "bg-red-500"
                                : row.passenger_flow > 120
                                  ? "bg-amber-500"
                                  : "bg-emerald-500"
                            }`}
                            style={{ width: `${Math.min(100, (row.passenger_flow / 350) * 100)}%` }}
                          />
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </div>
      )}
    </AppShell>
  );
}

export default function CityDashboardPage() {
  return (
    <Suspense fallback={<div className="p-6">Loading network view...</div>}>
      <CityDashboardContent />
    </Suspense>
  );
}
