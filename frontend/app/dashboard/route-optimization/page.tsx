"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AppShell } from "@/components/AppShell";
import { ApiError, apiFetch } from "@/lib/api";
import { getStoredToken } from "@/lib/auth";
import type { Station } from "@/types";

interface RouteStation {
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

interface RouteOptimizeResponse {
  path: RouteStation[];
  total_stations: number;
  interchanges: string[];
  estimated_duration_minutes: number;
  congestion_index: number;
  alternative_path: RouteStation[] | null;
  alternative_duration_minutes: number | null;
  alternative_congestion_index: number | null;
}

export default function RouteOptimizationPage() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);

  // Stations state
  const [stations, setStations] = useState<Station[]>([]);
  const [cities, setCities] = useState<string[]>([]);
  const [selectedCity, setSelectedCity] = useState("Delhi");

  // Selection state
  const [originId, setOriginId] = useState("");
  const [destinationId, setDestinationId] = useState("");
  const [avoidCongestion, setAvoidCongestion] = useState(false);

  // Result state
  const [result, setResult] = useState<RouteOptimizeResponse | null>(null);
  const [activePathType, setActivePathType] = useState<"optimized" | "alternative">("optimized");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const storedToken = getStoredToken();
    if (!storedToken) {
      router.push("/auth");
      return;
    }
    setToken(storedToken);

    // Fetch all stations
    apiFetch<Station[]>("/stations", {}, storedToken)
      .then((data) => {
        setStations(data);
        // Extract unique cities
        const uniqueCities = Array.from(new Set(data.map((s) => s.city)));
        setCities(uniqueCities);
        if (uniqueCities.includes("Delhi")) {
          setSelectedCity("Delhi");
        } else if (uniqueCities[0]) {
          setSelectedCity(uniqueCities[0]);
        }
      })
      .catch((err) => {
        setError("Failed to load stations list.");
      });
  }, [router]);

  // Update dropdown values when city changes
  useEffect(() => {
    const cityStations = stations.filter((s) => s.city === selectedCity);
    if (cityStations.length >= 2) {
      setOriginId(cityStations[0].id);
      setDestinationId(cityStations[1].id);
    } else if (cityStations.length > 0) {
      setOriginId(cityStations[0].id);
      setDestinationId(cityStations[0].id);
    } else {
      setOriginId("");
      setDestinationId("");
    }
    setResult(null);
  }, [selectedCity, stations]);

  const handleRouteSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !originId || !destinationId) return;

    setLoading(true);
    setError(null);
    setResult(null);
    setActivePathType("optimized");

    try {
      const data = await apiFetch<RouteOptimizeResponse>(
        "/networks/route-optimize",
        {
          method: "POST",
          body: JSON.stringify({
            origin_station_id: originId,
            destination_station_id: destinationId,
            avoid_congestion: avoidCongestion,
          }),
        },
        token
      );
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Routing optimization failed.");
    } finally {
      setLoading(false);
    }
  };

  const cityStations = stations.filter((s) => s.city === selectedCity);

  // Render SVG Node-Link Route map
  const renderRouteSvg = (pathStations: RouteStation[]) => {
    if (pathStations.length === 0) return null;

    const width = 500;
    const height = 300;
    const pad = 50;

    // Normalize coordinates
    const lats = pathStations.map((s) => s.latitude);
    const lons = pathStations.map((s) => s.longitude);

    const minLat = Math.min(...lats);
    const maxLat = Math.max(...lats);
    const minLon = Math.min(...lons);
    const maxLon = Math.max(...lons);

    const latRange = maxLat - minLat || 0.00001;
    const lonRange = maxLon - minLon || 0.00001;

    const coords = pathStations.map((s) => {
      const x = pad + ((s.longitude - minLon) / lonRange) * (width - 2 * pad);
      const y = height - pad - ((s.latitude - minLat) / latRange) * (height - 2 * pad);
      return { ...s, x, y };
    });

    const getLineColor = (line: string) => {
      const l = line.toLowerCase();
      if (l.includes("blue")) return "#3b82f6";
      if (l.includes("yellow")) return "#fbbf24";
      if (l.includes("red")) return "#ef4444";
      if (l.includes("green")) return "#10b981";
      if (l.includes("purple")) return "#8b5cf6";
      if (l.includes("magenta")) return "#ec4899";
      if (l.includes("violet")) return "#a855f7";
      return "#64748b";
    };

    return (
      <svg width="100%" height="100%" viewBox={`0 0 ${width} ${height}`} className="overflow-visible">
        {/* Draw track lines */}
        {coords.map((curr, idx) => {
          if (idx === 0) return null;
          const prev = coords[idx - 1];
          const strokeColor = getLineColor(curr.line);
          return (
            <g key={`link-${idx}`}>
              <line
                x1={prev.x}
                y1={prev.y}
                x2={curr.x}
                y2={curr.y}
                stroke={strokeColor}
                strokeWidth={5}
                strokeLinecap="round"
                className="opacity-20"
              />
              <line
                x1={prev.x}
                y1={prev.y}
                x2={curr.x}
                y2={curr.y}
                stroke={strokeColor}
                strokeWidth={3}
                strokeLinecap="round"
              />
            </g>
          );
        })}

        {/* Draw stations */}
        {coords.map((st, idx) => {
          const isOrigin = idx === 0;
          const isDest = idx === coords.length - 1;
          const loadColor =
            st.load_level === "critical"
              ? "fill-[var(--danger)] stroke-[var(--danger-soft)]"
              : st.load_level === "warning"
              ? "fill-[var(--warning)] stroke-[var(--warning-soft)]"
              : "fill-[var(--success)] stroke-[var(--success-soft)]";

          return (
            <g key={`station-${st.id}`} className="group cursor-pointer">
              <circle
                cx={st.x}
                cy={st.y}
                r={st.is_interchange ? 10 : 7}
                className={`${loadColor} stroke-2 transition duration-200 group-hover:scale-125`}
              />
              {st.is_interchange && (
                <circle cx={st.x} cy={st.y} r={4} className="fill-white" />
              )}
              {/* Tooltip trigger or always visible key labels */}
              {(isOrigin || isDest || st.is_interchange) && (
                <text
                  x={st.x}
                  y={st.y - (st.is_interchange ? 14 : 12)}
                  textAnchor="middle"
                  className="fill-[var(--foreground)] text-[10px] font-bold"
                >
                  {st.name}
                </text>
              )}
              <title>{`${st.name} (${st.line}) - Load: ${st.load_level.toUpperCase()}`}</title>
            </g>
          );
        })}
      </svg>
    );
  };

  const getActivePath = () => {
    if (!result) return [];
    return activePathType === "optimized"
      ? result.path
      : result.alternative_path || [];
  };

  const activePath = getActivePath();
  const currentDuration =
    activePathType === "optimized"
      ? result?.estimated_duration_minutes
      : result?.alternative_duration_minutes;
  const currentCongestion =
    activePathType === "optimized"
      ? result?.congestion_index
      : result?.alternative_congestion_index;

  return (
    <AppShell
      title="Adaptive Dijkstra Multi-Agent Route Optimizer"
      subtitle="Input origins and destinations to compute transit times, line switches, and congestion-avoiding schedules."
    >
      {error && <div className="glass-card section-card text-[var(--danger)] mb-4">{error}</div>}

      <div className="grid gap-6 lg:grid-cols-[0.8fr_1.2fr]">
        {/* Navigation Console */}
        <section className="glass-card section-card">
          <h2 className="text-xl font-bold tracking-tight mb-2">Transit Router Console</h2>
          <p className="text-sm text-[var(--muted)] mb-6">
            Configure Origin-Destination pairs and configure real-time weights to calculate paths dynamically.
          </p>

          <form onSubmit={handleRouteSearch} className="space-y-5">
            <div>
              <label className="block text-xs uppercase tracking-[0.14em] text-[var(--muted)] mb-2">Metro Network City</label>
              <select
                className="select-field w-full"
                value={selectedCity}
                onChange={(e) => setSelectedCity(e.target.value)}
              >
                {cities.map((city) => (
                  <option key={city} value={city}>
                    {city} Metro System
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs uppercase tracking-[0.14em] text-[var(--muted)] mb-2">Origin Station</label>
              <select
                className="select-field w-full"
                value={originId}
                onChange={(e) => setOriginId(e.target.value)}
              >
                {cityStations.map((st) => (
                  <option key={st.id} value={st.id}>
                    {st.name} ({st.line})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs uppercase tracking-[0.14em] text-[var(--muted)] mb-2">Destination Station</label>
              <select
                className="select-field w-full"
                value={destinationId}
                onChange={(e) => setDestinationId(e.target.value)}
              >
                {cityStations.map((st) => (
                  <option key={st.id} value={st.id}>
                    {st.name} ({st.line})
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-center justify-between p-3 rounded-2xl bg-[color:var(--panel-border)]/20 border border-[var(--panel-border)]/50">
              <div>
                <span className="block text-sm font-semibold">Avoid Commuter Congestion</span>
                <span className="block text-xs text-[var(--muted)] mt-0.5">Route around heavily loaded stations</span>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={avoidCongestion}
                  onChange={(e) => setAvoidCongestion(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-[color:var(--panel-border)] peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[var(--accent)]"></div>
              </label>
            </div>

            <button
              type="submit"
              disabled={loading || !originId || !destinationId}
              className="button-primary w-full py-3"
            >
              {loading ? "Calculating adaptive routes..." : "Optimize Transit Path"}
            </button>
          </form>
        </section>

        {/* Path Outputs & Visualizer */}
        <section className="space-y-6">
          {result ? (
            <div className="glass-card section-card">
              {/* Route Type Selector Tabs (Only if Alternative exists) */}
              {result.alternative_path && (
                <div className="flex rounded-xl bg-[color:var(--panel-border)]/35 p-1 mb-6 max-w-md">
                  <button
                    className={`flex-1 text-center py-2 text-xs font-semibold rounded-lg transition ${
                      activePathType === "optimized"
                        ? "bg-[var(--panel)] border border-[var(--panel-border)]/80 text-[var(--foreground)]"
                        : "text-[var(--muted)]"
                    }`}
                    onClick={() => setActivePathType("optimized")}
                  >
                    Optimized Path {avoidCongestion ? "(Congestion Avoided)" : "(Shortest)"}
                  </button>
                  <button
                    className={`flex-1 text-center py-2 text-xs font-semibold rounded-lg transition ${
                      activePathType === "alternative"
                        ? "bg-[var(--panel)] border border-[var(--panel-border)]/80 text-[var(--foreground)]"
                        : "text-[var(--muted)]"
                    }`}
                    onClick={() => setActivePathType("alternative")}
                  >
                    Alternative Path {!avoidCongestion ? "(Congestion Avoided)" : "(Shortest)"}
                  </button>
                </div>
              )}

              {/* Journey Metrics */}
              <div className="grid gap-4 sm:grid-cols-4 mb-6">
                <div className="rounded-2xl p-4 bg-[color:var(--panel)] border border-[var(--panel-border)]/50">
                  <p className="text-xs uppercase tracking-[0.14em] text-[var(--muted)]">Transit Time</p>
                  <p className="mt-1 text-2xl font-bold font-mono text-[var(--accent)]">{currentDuration}m</p>
                </div>
                <div className="rounded-2xl p-4 bg-[color:var(--panel)] border border-[var(--panel-border)]/50">
                  <p className="text-xs uppercase tracking-[0.14em] text-[var(--muted)]">Stops</p>
                  <p className="mt-1 text-2xl font-bold font-mono">{activePath.length}</p>
                </div>
                <div className="rounded-2xl p-4 bg-[color:var(--panel)] border border-[var(--panel-border)]/50">
                  <p className="text-xs uppercase tracking-[0.14em] text-[var(--muted)]">Interchanges</p>
                  <p className="mt-1 text-2xl font-bold font-mono">
                    {activePathType === "optimized" ? result.interchanges.length : 0}
                  </p>
                </div>
                <div className="rounded-2xl p-4 bg-[color:var(--panel)] border border-[var(--panel-border)]/50">
                  <p className="text-xs uppercase tracking-[0.14em] text-[var(--muted)]">Avg Load Factor</p>
                  <p className="mt-1 text-2xl font-bold font-mono">
                    {((currentCongestion || 0) * 100).toFixed(0)}%
                  </p>
                </div>
              </div>

              {/* Visual Map Render */}
              <div className="rounded-2xl border border-[var(--panel-border)]/50 bg-black/5 p-4 flex items-center justify-center h-[280px] overflow-hidden mb-6">
                {renderRouteSvg(activePath)}
              </div>

              {/* Step-by-Step Directions */}
              <div>
                <h3 className="text-sm uppercase tracking-[0.14em] text-[var(--muted)] mb-4">Journey Directions</h3>
                <div className="relative border-l border-[var(--panel-border)] ml-3 pl-6 space-y-6">
                  {activePath.map((station, idx) => {
                    const isTransfer = idx > 0 && activePath[idx - 1].line !== station.line;
                    const loadColor =
                      station.load_level === "critical"
                        ? "bg-red-500/15 text-red-500 border-red-500/20"
                        : station.load_level === "warning"
                        ? "bg-yellow-500/15 text-yellow-600 border-yellow-500/20"
                        : "bg-emerald-500/15 text-emerald-600 border-emerald-500/20";

                    return (
                      <div key={station.id} className="relative">
                        {/* Timeline Bullet */}
                        <div
                          className={`absolute -left-[31px] top-1.5 w-2.5 h-2.5 rounded-full border-2 border-[var(--panel)] ${
                            station.is_interchange ? "bg-[var(--accent)]" : "bg-[var(--muted)]"
                          }`}
                        />

                        {isTransfer && (
                          <div className="mb-2 p-2 rounded-xl bg-[var(--accent)]/10 text-xs font-semibold text-[var(--accent)] border border-[var(--accent)]/20 inline-block">
                            ⇄ Interchange: Switch to {station.line}
                          </div>
                        )}

                        <div className="flex items-center justify-between">
                          <div>
                            <span className="font-semibold text-sm">{station.name}</span>
                            <span className="text-xs text-[var(--muted)] ml-2">{station.line}</span>
                          </div>
                          <span className={`status-pill ${loadColor} text-[10px] uppercase font-bold tracking-wider px-2 py-0.5`}>
                            {station.load_level} Load ({station.current_flow} pax)
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          ) : (
            <div className="glass-card section-card text-center py-20 text-[var(--muted)] text-sm">
              {loading ? (
                <div className="space-y-4">
                  <div className="animate-spin h-8 w-8 border-4 border-[var(--accent)] border-t-transparent rounded-full mx-auto" />
                  <p>Running adaptive Dijkstra route optimizer layers...</p>
                </div>
              ) : (
                "Configure Origin and Destination and click 'Optimize Transit Path' to fetch travel routing paths."
              )}
            </div>
          )}
        </section>
      </div>
    </AppShell>
  );
}
