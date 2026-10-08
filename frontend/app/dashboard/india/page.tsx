"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AppShell } from "@/components/AppShell";
import { ApiError, apiFetch } from "@/lib/api";
import { getStoredToken } from "@/lib/auth";
import { formatNumber } from "@/lib/format";
import { StatCard } from "@/components/StatCard";

interface CitySummary {
  name: string;
  state: string;
  stations_count: number;
  lines_count: number;
  lines: string[];
}

interface NationalOverview {
  total_stations: number;
  total_cities: number;
  total_states: number;
  total_trains: number;
  passenger_flow_24h: number;
  active_alerts: number;
  states: { name: string; stations_count: number }[];
  cities: CitySummary[];
}

// Coordinate mappings of Indian cities on a 500x550 schematic coordinate system
const CITY_COORDINATES: Record<string, { x: number; y: number }> = {
  Delhi: { x: 200, y: 150 },
  Noida: { x: 215, y: 155 },
  Mumbai: { x: 120, y: 360 },
  Bengaluru: { x: 210, y: 460 },
  Hyderabad: { x: 230, y: 370 },
  Chennai: { x: 250, y: 465 },
  Kolkata: { x: 380, y: 280 },
  Kochi: { x: 195, y: 505 },
  Pune: { x: 135, y: 380 },
  Srinagar: { x: 175, y: 40 },
};

export default function IndiaOverviewPage() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [overview, setOverview] = useState<NationalOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hoveredCity, setHoveredCity] = useState<string | null>(null);

  useEffect(() => {
    const storedToken = getStoredToken();
    if (!storedToken) {
      router.push("/auth");
      return;
    }
    setToken(storedToken);

    apiFetch<NationalOverview>("/networks/overview", {}, storedToken)
      .then((data) => {
        setOverview(data);
        setLoading(false);
      })
      .catch((err) => {
        if (err instanceof ApiError && err.isAuthError) {
          router.push("/auth");
          return;
        }
        setError(err instanceof Error ? err.message : "Failed to load national overview.");
        setLoading(false);
      });
  }, [router]);

  function handleCityClick(cityName: string) {
    // If Noida is clicked, open Delhi network since they are linked in the seeded stations
    const targetCity = cityName === "Noida" ? "Delhi" : cityName;
    router.push(`/dashboard/city?city=${targetCity}`);
  }

  return (
    <AppShell
      title="National Intelligence Portal"
      subtitle="Aggregated metrics, state deployments, and interactive GIS connectivity across all Indian Metros."
    >
      {loading && (
        <div className="glass-card section-card text-center py-12 animate-pulse text-[var(--muted)]">
          Syncing national metro databases…
        </div>
      )}
      {error && <div className="glass-card section-card text-[var(--danger)]">{error}</div>}

      {overview && (
        <div className="space-y-6">
          {/* KPI Dashboard Cards */}
          <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard
              label="National Daily Flow"
              value={formatNumber(overview.passenger_flow_24h)}
              change="+12.4% vs last week"
              tone="good"
            />
            <StatCard
              label="Operational Metros"
              value={overview.total_cities.toString()}
              change="2 upcoming systems"
              tone="neutral"
            />
            <StatCard
              label="Total Active Stations"
              value={overview.total_stations.toString()}
              change="16 multi-line interchanges"
              tone="neutral"
            />
            <StatCard
              label="Active Alerts Watchlist"
              value={overview.active_alerts.toString()}
              change="Congestion / delay risks"
              tone={overview.active_alerts > 4 ? "critical" : "warning"}
            />
          </section>

          {/* Map & State Rankings Section */}
          <section className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
            {/* Interactive Schematic Map of India */}
            <div className="glass-card section-card flex flex-col items-center">
              <div className="w-full border-b border-[var(--panel-border)] pb-3 mb-4 flex justify-between items-center">
                <div>
                  <h2 className="text-xl font-bold tracking-tight">GIS National Metro Grid</h2>
                  <p className="text-xs text-[var(--muted)]">Hover nodes for active line metrics. Click to inspect topology.</p>
                </div>
                {hoveredCity && (
                  <span className="status-pill bg-[var(--accent-soft)] text-[var(--accent)] font-semibold transition-all">
                    {hoveredCity} Metro Grid
                  </span>
                )}
              </div>

              <div className="relative w-full max-w-[500px] h-[550px] bg-[var(--panel)] rounded-2xl overflow-hidden flex items-center justify-center p-2 border border-[var(--panel-border)]/50">
                <svg
                  viewBox="0 0 500 550"
                  className="w-full h-full text-slate-700 select-none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  {/* Styled outline of India (Schematic representation) */}
                  <path
                    d="M 200,30 L 220,50 L 230,80 L 220,120 L 240,150 L 280,170 L 320,180 L 350,200 L 400,230 L 420,260 L 380,270 L 390,300 L 330,310 L 300,350 L 290,380 L 280,410 L 260,450 L 250,510 L 230,530 L 210,510 L 190,460 L 170,430 L 130,410 L 110,390 L 105,350 L 130,310 L 120,290 L 80,270 L 90,240 L 130,220 L 150,180 L 165,130 L 180,80 Z"
                    fill="var(--background)"
                    stroke="var(--panel-border)"
                    strokeWidth="2"
                    strokeDasharray="4 2"
                    opacity="0.65"
                  />

                  {/* Connection Links showing national trunk routes */}
                  <line x1="200" y1="150" x2="210" y2="460" stroke="var(--accent)" strokeWidth="0.8" strokeDasharray="3 3" opacity="0.3" />
                  <line x1="200" y1="150" x2="120" y2="360" stroke="var(--accent)" strokeWidth="0.8" strokeDasharray="3 3" opacity="0.3" />
                  <line x1="210" y1="460" x2="120" y2="360" stroke="var(--accent)" strokeWidth="0.8" strokeDasharray="3 3" opacity="0.3" />
                  <line x1="230" y1="370" x2="210" y2="460" stroke="var(--accent)" strokeWidth="0.8" strokeDasharray="3 3" opacity="0.3" />
                  <line x1="230" y1="370" x2="380" y2="280" stroke="var(--accent)" strokeWidth="0.8" strokeDasharray="3 3" opacity="0.3" />

                  {/* Interactive City Nodes */}
                  {overview.cities.map((city) => {
                    const coords = CITY_COORDINATES[city.name];
                    if (!coords) return null;
                    const isHovered = hoveredCity === city.name;

                    return (
                      <g
                        key={city.name}
                        className="cursor-pointer group"
                        onMouseEnter={() => setHoveredCity(city.name)}
                        onMouseLeave={() => setHoveredCity(null)}
                        onClick={() => handleCityClick(city.name)}
                      >
                        {/* Ripple glowing outer ring */}
                        <circle
                          cx={coords.x}
                          cy={coords.y}
                          r={isHovered ? 16 : 8}
                          className="fill-[var(--accent)]/15 stroke-[var(--accent)] animate-pulse transition-all duration-300"
                          strokeWidth={isHovered ? 2 : 1}
                        />
                        {/* Core active node */}
                        <circle
                          cx={coords.x}
                          cy={coords.y}
                          r="4"
                          className="fill-[var(--accent)] group-hover:scale-125 transition-transform"
                        />
                        {/* Floating city label */}
                        <text
                          x={coords.x + 10}
                          y={coords.y + 4}
                          className={`text-[10px] font-bold fill-[var(--text)] transition-all select-none ${
                            isHovered ? "fill-[var(--accent)] text-xs scale-105" : "opacity-75"
                          }`}
                        >
                          {city.name}
                        </text>
                      </g>
                    );
                  })}
                </svg>
              </div>
            </div>

            {/* Metro Systems Breakdown Table */}
            <div className="glass-card section-card flex flex-col justify-between">
              <div>
                <h2 className="text-xl font-bold tracking-tight mb-2">Regional Grid Deployments</h2>
                <p className="text-sm text-[var(--muted)] mb-4">
                  Overview of currently monitored state transit networks, lines, and operational terminals.
                </p>
                <div className="table-shell max-h-[380px] overflow-y-auto">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>City / State</th>
                        <th className="text-center">Lines</th>
                        <th className="text-center">Stations</th>
                        <th className="text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {overview.cities.map((city) => (
                        <tr key={city.name} className="hover:bg-[var(--panel-border)]/20 transition-colors">
                          <td>
                            <div className="font-semibold">{city.name}</div>
                            <div className="text-xs text-[var(--muted)]">{city.state}</div>
                          </td>
                          <td className="text-center">
                            <span className="inline-flex h-6 px-2 items-center justify-center rounded-full bg-[var(--accent-soft)] text-xs font-semibold text-[var(--accent)]">
                              {city.lines_count} Lines
                            </span>
                          </td>
                          <td className="text-center font-mono font-medium">{city.stations_count}</td>
                          <td className="text-right">
                            <button
                              type="button"
                              className="button-ghost px-2 py-1 text-xs"
                              onClick={() => handleCityClick(city.name)}
                            >
                              Inspect →
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* State Wise Summary */}
              <div className="mt-4 pt-4 border-t border-[var(--panel-border)] grid grid-cols-3 gap-2">
                {overview.states.slice(0, 3).map((st) => (
                  <div key={st.name} className="rounded-xl bg-[color:var(--panel)] p-3 text-center border border-[var(--panel-border)]/50">
                    <p className="text-xs text-[var(--muted)] truncate">{st.name}</p>
                    <p className="text-lg font-bold mt-1 font-mono">{st.stations_count} Stns</p>
                  </div>
                ))}
              </div>
            </div>
          </section>
        </div>
      )}
    </AppShell>
  );
}
