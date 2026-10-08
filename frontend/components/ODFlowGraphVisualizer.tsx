"use client";

import React, { useEffect, useRef, useState } from "react";

export interface StationNode {
  code: string;
  name: string;
  line: string;
  x: number;
  y: number;
}

export interface ODFlowArc {
  origin: string;
  destination: string;
  flowCount: number;
  line: string;
}

interface ODFlowGraphVisualizerProps {
  city?: string;
}

export function ODFlowGraphVisualizer({ city = "Delhi" }: ODFlowGraphVisualizerProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [selectedNode, setSelectedNode] = useState<StationNode | null>(null);
  const [activeLine, setActiveLine] = useState<string>("All");
  const [animSpeed, setAnimSpeed] = useState<number>(1);

  // Sample stations with positions on network map canvas
  const stations: StationNode[] = [
    { code: "ST01", name: "Central Terminal", line: "Red Line", x: 280, y: 220 },
    { code: "ST02", name: "North Hub", line: "Red Line", x: 280, y: 100 },
    { code: "ST03", name: "South Junction", line: "Red Line", x: 280, y: 340 },
    { code: "ST04", name: "East Crossing", line: "Blue Line", x: 440, y: 220 },
    { code: "ST05", name: "West Gate", line: "Blue Line", x: 120, y: 220 },
    { code: "ST06", name: "Tech Park", line: "Yellow Line", x: 400, y: 120 },
    { code: "ST07", name: "Airport City", line: "Yellow Line", x: 160, y: 320 },
    { code: "ST08", name: "Metro City Center", line: "Blue Line", x: 280, y: 220 },
  ];

  const odFlows: ODFlowArc[] = [
    { origin: "ST02", destination: "ST01", flowCount: 480, line: "Red Line" },
    { origin: "ST01", destination: "ST03", flowCount: 390, line: "Red Line" },
    { origin: "ST05", destination: "ST01", flowCount: 520, line: "Blue Line" },
    { origin: "ST01", destination: "ST04", flowCount: 450, line: "Blue Line" },
    { origin: "ST06", destination: "ST01", flowCount: 310, line: "Yellow Line" },
    { origin: "ST01", destination: "ST07", flowCount: 290, line: "Yellow Line" },
    { origin: "ST05", destination: "ST04", flowCount: 610, line: "Blue Line" },
  ];

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationFrameId: number;
    let particleOffset = 0;

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Draw subtle background grid
      ctx.strokeStyle = "rgba(148, 163, 184, 0.08)";
      ctx.lineWidth = 1;
      const step = 40;
      for (let x = 0; x < canvas.width; x += step) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, canvas.height);
        ctx.stroke();
      }
      for (let y = 0; y < canvas.height; y += step) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(canvas.width, y);
        ctx.stroke();
      }

      // Draw OD Flow Arcs & Traveling Particles
      odFlows.forEach((flow) => {
        if (activeLine !== "All" && flow.line !== activeLine) return;

        const origNode = stations.find((s) => s.code === flow.origin);
        const destNode = stations.find((s) => s.code === flow.destination);
        if (!origNode || !destNode) return;

        // Draw track corridor line
        ctx.beginPath();
        ctx.moveTo(origNode.x, origNode.y);
        ctx.lineTo(destNode.x, destNode.y);
        ctx.strokeStyle =
          flow.line === "Red Line"
            ? "rgba(239, 68, 68, 0.35)"
            : flow.line === "Blue Line"
            ? "rgba(59, 130, 246, 0.35)"
            : "rgba(245, 158, 11, 0.35)";
        ctx.lineWidth = Math.min(6, Math.max(2, flow.flowCount / 120));
        ctx.stroke();

        // Traveling vector particle animation
        const particleCount = 4;
        for (let p = 0; p < particleCount; p++) {
          const t = ((particleOffset + (p * 1) / particleCount) % 1 + 1) % 1;
          const px = origNode.x + (destNode.x - origNode.x) * t;
          const py = origNode.y + (destNode.y - origNode.y) * t;

          ctx.beginPath();
          ctx.arc(px, py, 3.5, 0, Math.PI * 2);
          ctx.fillStyle =
            flow.line === "Red Line"
              ? "#ff453a"
              : flow.line === "Blue Line"
              ? "#2997ff"
              : "#ffd60a";
          ctx.shadowBlur = 10;
          ctx.shadowColor = ctx.fillStyle;
          ctx.fill();
          ctx.shadowBlur = 0;
        }
      });

      // Draw Station Nodes
      stations.forEach((node) => {
        const isSelected = selectedNode?.code === node.code;

        // Outer glow on selection
        if (isSelected) {
          ctx.beginPath();
          ctx.arc(node.x, node.y, 16, 0, Math.PI * 2);
          ctx.fillStyle = "rgba(0, 113, 227, 0.25)";
          ctx.fill();
        }

        // Station Dot
        ctx.beginPath();
        ctx.arc(node.x, node.y, isSelected ? 8 : 6, 0, Math.PI * 2);
        ctx.fillStyle =
          node.line === "Red Line"
            ? "#ef4444"
            : node.line === "Blue Line"
            ? "#3b82f6"
            : "#f59e0b";
        ctx.fill();
        ctx.lineWidth = 2;
        ctx.strokeStyle = "#ffffff";
        ctx.stroke();

        // Station Label
        ctx.fillStyle = "#f8fafc";
        ctx.font = "600 11px -apple-system, BlinkMacSystemFont, sans-serif";
        ctx.fillText(node.name, node.x + 12, node.y + 4);
      });

      particleOffset += animSpeed * 0.008;
      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
    };
  }, [activeLine, selectedNode, animSpeed]);

  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const clickY = e.clientY - rect.top;

    const clicked = stations.find((st) => {
      const dx = st.x - clickX;
      const dy = st.y - clickY;
      return Math.sqrt(dx * dx + dy * dy) < 16;
    });

    setSelectedNode(clicked || null);
  };

  return (
    <div className="glass-card section-card fade-up">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
        <div>
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-purple-500/10 text-purple-500 border border-purple-500/20">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <h3 className="text-base sm:text-lg font-semibold tracking-tight text-[var(--text)]">
              Interactive Network & Flow Particles
            </h3>
          </div>
          <p className="text-xs text-[var(--muted)] mt-0.5">
            Real-time vector particle telemetry across {city} Metro corridors.
          </p>
        </div>

        {/* Cupertino Line Segmented Tabs */}
        <div className="apple-segmented-track">
          {["All", "Red Line", "Blue Line", "Yellow Line"].map((line) => (
            <button
              key={line}
              onClick={() => setActiveLine(line)}
              className={`apple-segmented-item px-2.5 py-1 ${activeLine === line ? "active" : ""}`}
            >
              {line}
            </button>
          ))}
        </div>
      </div>

      <div className="relative overflow-hidden rounded-2xl border border-[var(--panel-border)] bg-slate-950/85 backdrop-blur-xl shadow-inner">
        <canvas
          ref={canvasRef}
          width={600}
          height={380}
          onClick={handleCanvasClick}
          className="w-full h-auto cursor-pointer block"
        />

        {selectedNode && (
          <div className="absolute top-4 right-4 glass-card p-3.5 max-w-xs text-xs text-[var(--text)] shadow-2xl border border-white/20 dark:border-white/10">
            <div className="flex items-center justify-between gap-3 mb-1.5">
              <span className="font-bold text-[var(--accent)]">{selectedNode.name}</span>
              <button
                onClick={() => setSelectedNode(null)}
                className="text-[var(--muted)] hover:text-[var(--text)] rounded-full h-4 w-4 flex items-center justify-center"
              >
                ✕
              </button>
            </div>
            <p className="text-[var(--muted)]">Corridor: <span className="text-[var(--text)] font-medium">{selectedNode.line}</span></p>
            <p className="text-[var(--muted)] mt-1">Peak Outflow OD Volume: <span className="text-[var(--good)] font-bold">480 pass/hr</span></p>
            <p className="text-[var(--muted)] mt-0.5">Primary Exit Destination: <span className="text-[var(--accent)] font-medium">East Crossing (ST04)</span></p>
          </div>
        )}
      </div>
    </div>
  );
}
