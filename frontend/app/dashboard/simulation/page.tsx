"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { AppShell } from "@/components/AppShell";
import { ApiError, apiFetch } from "@/lib/api";
import { getStoredToken } from "@/lib/auth";

interface SimStation {
  station_code: string;
  station_name: string;
  line: string;
  queue_length: number;
  escalator_load_pct: number;
  platform_density_pct: number;
  safety_status: string;
  exit_vectors: { exit_name: string; vector_x: number; vector_y: number; flow_rate: number }[];
}

interface SimTrain {
  code: string;
  name: string;
  line: string;
  capacity: number;
  speed_kmh: number;
  status: string;
  current_station: string;
  occupancy_pct: number;
}

interface SimResponse {
  city: string;
  scenario: string;
  stations: SimStation[];
  trains: SimTrain[];
  is_active: boolean;
  message: string;
}

export default function SimulationDashboardPage() {
  const router = useRouter();
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  const [token, setToken] = useState<string | null>(null);
  const [selectedCity, setSelectedCity] = useState("Delhi");
  
  // Sim parameters
  const [passengerRate, setPassengerRate] = useState(1.0);
  const [trainSpeed, setTrainSpeed] = useState(1.0);
  const [scenario, setScenario] = useState("normal");
  
  // Sim output state
  const [simState, setSimState] = useState<SimResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Evacuation toggle
  const [isEvacuation, setIsEvacuation] = useState(false);

  useEffect(() => {
    const storedToken = getStoredToken();
    if (!storedToken) {
      router.push("/auth");
      return;
    }
    setToken(storedToken);
    triggerSimStep(storedToken, "normal", 1.0, 1.0);
  }, [router]);

  // Handle parameter adjustment trigger
  function handleParamChange(newScenario: string, newRate: number, newSpeed: number) {
    if (!token) return;
    triggerSimStep(token, newScenario, newRate, newSpeed);
  }

  function triggerSimStep(activeToken: string, curScenario: string, curRate: number, curSpeed: number) {
    apiFetch<SimResponse>(
      "/simulation/run",
      {
        method: "POST",
        body: JSON.stringify({
          city: selectedCity,
          scenario: curScenario,
          passenger_rate: curRate,
          train_speed: curSpeed,
        }),
      },
      activeToken
    )
      .then((data) => {
        setSimState(data);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Simulation step failure.");
      });
  }

  // Toggle emergency evacuation
  function handleEvacuationToggle() {
    const nextEvac = !isEvacuation;
    setIsEvacuation(nextEvac);
    const nextScenario = nextEvac ? "evacuation" : "normal";
    setScenario(nextScenario);
    if (token) {
      triggerSimStep(token, nextScenario, passengerRate, trainSpeed);
    }
  }

  // Animation effect inside Canvas
  useEffect(() => {
    if (!canvasRef.current || !simState) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animFrameId: number;
    let offset = 0;

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Render backgrounds grid
      ctx.strokeStyle = "rgba(148, 163, 184, 0.05)";
      ctx.lineWidth = 1;
      const step = 40;
      for (let i = 0; i < canvas.width; i += step) {
        ctx.beginPath();
        ctx.moveTo(i, 0);
        ctx.lineTo(i, canvas.height);
        ctx.stroke();
      }
      for (let j = 0; j < canvas.height; j += step) {
        ctx.beginPath();
        ctx.moveTo(0, j);
        ctx.lineTo(canvas.width, j);
        ctx.stroke();
      }

      // Draw Main Tracks (Lines)
      ctx.strokeStyle = "rgba(59, 130, 246, 0.4)";
      ctx.lineWidth = 6;
      ctx.lineCap = "round";
      ctx.beginPath();
      ctx.moveTo(100, 200);
      ctx.lineTo(700, 200);
      ctx.stroke();

      ctx.strokeStyle = "rgba(16, 185, 129, 0.4)";
      ctx.beginPath();
      ctx.moveTo(250, 80);
      ctx.lineTo(250, 320);
      ctx.stroke();

      // Station coordinates layouts
      const stationCoords: Record<string, { x: number; y: number }> = {};
      simState.stations.forEach((st, idx) => {
        const row = idx % 3;
        const col = Math.floor(idx / 3);
        const x = 150 + col * 180;
        const y = 100 + row * 100;
        stationCoords[st.station_code] = { x, y };

        // Draw station platform occupancy circle
        const heatColor =
          st.safety_status === "evacuating"
            ? "rgba(239, 68, 68, 0.8)"
            : st.safety_status === "overcrowded"
              ? "rgba(245, 158, 11, 0.8)"
              : "rgba(16, 185, 129, 0.8)";

        ctx.fillStyle = heatColor;
        ctx.beginPath();
        ctx.arc(x, y, 16 + (st.platform_density_pct / 6), 0, Math.PI * 2);
        ctx.fill();

        // Draw core node
        ctx.fillStyle = "#ffffff";
        ctx.beginPath();
        ctx.arc(x, y, 6, 0, Math.PI * 2);
        ctx.fill();

        // Station text details
        ctx.fillStyle = "#ffffff";
        ctx.font = "bold 11px sans-serif";
        ctx.fillText(st.station_name, x - 40, y - 22);

        ctx.fillStyle = "rgba(255, 255, 255, 0.6)";
        ctx.font = "9px monospace";
        ctx.fillText(`Plat: ${st.platform_density_pct}% | Esc: ${st.escalator_load_pct}%`, x - 40, y + 22);

        // Emergency Evacuation Vectors Rendering
        if (st.safety_status === "evacuating") {
          ctx.strokeStyle = "rgba(239, 68, 68, 0.8)";
          ctx.lineWidth = 2;
          // Draw radiating waves out from center
          ctx.beginPath();
          ctx.arc(x, y, 35 + (offset % 25), 0, Math.PI * 2);
          ctx.stroke();

          // Render evacuation exit path arrows
          ctx.strokeStyle = "#ef4444";
          ctx.lineWidth = 3;
          ctx.beginPath();
          ctx.moveTo(x, y);
          ctx.lineTo(x + 40, y - 40);
          ctx.stroke();

          // Draw arrowhead
          ctx.fillStyle = "#ef4444";
          ctx.beginPath();
          ctx.moveTo(x + 40, y - 40);
          ctx.lineTo(x + 30, y - 40);
          ctx.lineTo(x + 40, y - 30);
          ctx.fill();
        }
      });

      // Draw moving trains
      offset += 0.8;
      simState.trains.forEach((tr, idx) => {
        const coord = stationCoords[tr.current_station];
        if (coord) {
          // Calculate movement offset based on speed
          const xOffset = Math.sin((offset + idx * 20) * 0.05) * 45;
          const tx = coord.x + (tr.line.includes("Blue") ? xOffset : 0);
          const ty = coord.y + (tr.line.includes("Green") ? xOffset : 0);

          // Draw train box
          ctx.fillStyle = tr.status === "evacuation_mode" ? "#ef4444" : "#3b82f6";
          ctx.fillRect(tx - 15, ty - 8, 30, 16);

          ctx.strokeStyle = "#ffffff";
          ctx.lineWidth = 1;
          ctx.strokeRect(tx - 15, ty - 8, 30, 16);

          // Train labels
          ctx.fillStyle = "#ffffff";
          ctx.font = "bold 8px monospace";
          ctx.fillText(tr.code, tx - 12, ty + 3);
        }
      });

      animFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animFrameId);
    };
  }, [simState]);

  return (
    <AppShell
      title="Real-Time Operations Simulator"
      subtitle="Configure variables, choose emergency drills, and inspect crowd evacuation vector maps."
    >
      {error && <div className="glass-card section-card text-[var(--danger)] mb-4">{error}</div>}

      <div className="grid gap-6 lg:grid-cols-[0.85fr_1.15fr]">
        {/* Simulation Controls Panel */}
        <section className="glass-card section-card flex flex-col justify-between">
          <div>
            <h2 className="text-xl font-bold tracking-tight mb-2">Simulator Controllers</h2>
            <p className="text-sm text-[var(--muted)] mb-6">
              Manually ingest commuter spikes, adjust subway frequencies, and trigger emergency scenarios.
            </p>

            <div className="space-y-6">
              {/* Scenario Selection */}
              <div>
                <label className="block text-xs uppercase tracking-[0.14em] text-[var(--muted)] mb-2">Simulated Scenario</label>
                <div className="grid grid-cols-2 gap-2">
                  {[
                    ["normal", "Normal Operations"],
                    ["monsoon", "Monsoon Heavy Rain"],
                    ["festival", "Festival Spikes"],
                  ].map(([sc, label]) => (
                    <button
                      key={sc}
                      type="button"
                      disabled={isEvacuation}
                      className={`px-3 py-2 text-xs font-semibold rounded-lg border transition ${
                        scenario === sc
                          ? "bg-[var(--accent)] text-white border-[var(--accent)]"
                          : "bg-[var(--panel)] border-[var(--panel-border)] text-[var(--muted)]"
                      }`}
                      onClick={() => {
                        setScenario(sc);
                        handleParamChange(sc, passengerRate, trainSpeed);
                      }}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Commuter Inflow Rate */}
              <div>
                <label className="block text-xs uppercase tracking-[0.14em] text-[var(--muted)] mb-2">
                  Commuters Generation Inflow ({passengerRate.toFixed(1)}x)
                </label>
                <input
                  type="range"
                  min="0.5"
                  max="3.0"
                  step="0.1"
                  value={passengerRate}
                  onChange={(e) => {
                    const r = Number(e.target.value);
                    setPassengerRate(r);
                    handleParamChange(scenario, r, trainSpeed);
                  }}
                  className="w-full h-1 bg-[var(--panel-border)] rounded-lg appearance-none cursor-pointer accent-[var(--accent)]"
                />
              </div>

              {/* Train Headways Velocity */}
              <div>
                <label className="block text-xs uppercase tracking-[0.14em] text-[var(--muted)] mb-2">
                  Train Frequency velocity ({trainSpeed.toFixed(1)}x)
                </label>
                <input
                  type="range"
                  min="0.5"
                  max="2.5"
                  step="0.1"
                  value={trainSpeed}
                  onChange={(e) => {
                    const s = Number(e.target.value);
                    setTrainSpeed(s);
                    handleParamChange(scenario, passengerRate, s);
                  }}
                  className="w-full h-1 bg-[var(--panel-border)] rounded-lg appearance-none cursor-pointer accent-[var(--accent)]"
                />
              </div>
            </div>
          </div>

          {/* Red Emergency Evacuation drill */}
          <div className="pt-6 mt-6 border-t border-[var(--panel-border)] flex flex-col items-center">
            <button
              type="button"
              className={`w-full py-4 rounded-xl font-bold tracking-wider text-sm transition-all duration-300 ${
                isEvacuation
                  ? "bg-emerald-600 text-white shadow-[0_0_15px_rgba(16,185,129,0.4)]"
                  : "bg-red-600 hover:bg-red-700 text-white shadow-[0_0_15px_rgba(239,68,68,0.4)]"
              }`}
              onClick={handleEvacuationToggle}
            >
              {isEvacuation ? "CANCEL DRILL & SECURE GRID" : "ACTIVATE EMERGENCY EVACUATION DRILL"}
            </button>
            <p className="text-[10px] text-[var(--muted)] text-center mt-2 uppercase tracking-[0.14em]">
              {isEvacuation ? "Drill active: Simulating exit safety vector paths." : "Warning: Triggers passenger vector exits to exit gates."}
            </p>
          </div>
        </section>

        {/* Real-time 2D Canvas Visualizer */}
        <section className="glass-card section-card flex flex-col justify-between">
          <div>
            <h2 className="text-xl font-bold tracking-tight mb-2">Live Evacuation & Crowd Visualizer</h2>
            <p className="text-sm text-[var(--muted)] mb-4">
              Canvas plots active train indicators along tracks and platform occupancy heat.
            </p>

            <div className="border border-[var(--panel-border)]/50 rounded-2xl overflow-hidden bg-slate-950 flex items-center justify-center">
              <canvas
                ref={canvasRef}
                width={800}
                height={400}
                className="w-full h-auto block select-none bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-slate-900 via-slate-950 to-black"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 mt-4">
            <div className="rounded-xl p-3 bg-[color:var(--panel)] text-xs border border-[var(--panel-border)]/50">
              <span className="font-semibold block mb-1">Evacuation Pathings</span>
              <span className="text-[var(--muted)]">Gate exit vectoring: Gate A (-0.8x, 0.5y), Gate B (0.9x, -0.2y).</span>
            </div>
            <div className="rounded-xl p-3 bg-[color:var(--panel)] text-xs border border-[var(--panel-border)]/50">
              <span className="font-semibold block mb-1">Simulation Message</span>
              <span className="text-[var(--muted)] truncate">{simState?.message || "Running normal operations."}</span>
            </div>
          </div>
        </section>
      </div>
    </AppShell>
  );
}
