"use client";

import React, { useState } from "react";

export interface ODMatrixCell {
  originCode: string;
  originName: string;
  destCode: string;
  destName: string;
  volume: number;
}

interface ODMatrixHeatmapProps {
  stationCodes?: string[];
  stationNames?: string[];
  matrixData?: number[][];
}

export function ODMatrixHeatmap({
  stationCodes = ["ST01", "ST02", "ST03", "ST04", "ST05", "ST06"],
  stationNames = ["Central Terminal", "North Hub", "South Junction", "East Crossing", "West Gate", "Tech Park"],
  matrixData,
}: ODMatrixHeatmapProps) {
  const [hoveredCell, setHoveredCell] = useState<ODMatrixCell | null>(null);

  const defaultMatrix = [
    [0, 480, 390, 450, 520, 310],
    [410, 0, 350, 290, 380, 240],
    [380, 320, 0, 340, 290, 210],
    [430, 300, 310, 0, 610, 270],
    [500, 360, 280, 580, 0, 330],
    [320, 260, 220, 280, 350, 0],
  ];

  const grid =
    Array.isArray(matrixData) && matrixData.length > 0 && Array.isArray(matrixData[0])
      ? matrixData
      : defaultMatrix;
  const maxFlow = Math.max(1, ...grid.flatMap((row) => (Array.isArray(row) ? row : [0])));

  const getBgColor = (val: number) => {
    if (val === 0) return "bg-black/[0.02] dark:bg-white/[0.02] text-[var(--muted)] opacity-50";
    const pct = val / maxFlow;
    if (pct > 0.8) return "bg-purple-500/80 text-white font-bold shadow-sm";
    if (pct > 0.6) return "bg-purple-500/50 text-purple-900 dark:text-purple-100 font-semibold";
    if (pct > 0.4) return "bg-blue-500/40 text-blue-900 dark:text-blue-100";
    if (pct > 0.2) return "bg-blue-500/20 text-blue-800 dark:text-blue-200";
    return "bg-black/[0.03] dark:bg-white/[0.05] text-[var(--muted)]";
  };

  return (
    <div className="glass-card section-card fade-up">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <div>
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-500 border border-indigo-500/20">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
              </svg>
            </div>
            <h3 className="text-base sm:text-lg font-semibold tracking-tight text-[var(--text)]">
              Station Origin–Destination Matrix
            </h3>
          </div>
          <p className="text-xs text-[var(--muted)] mt-0.5">
            Inter-station passenger volume density grid (commuters/hr).
          </p>
        </div>

        {hoveredCell ? (
          <div className="flex items-center gap-2 rounded-full border border-purple-500/30 bg-purple-500/10 px-3.5 py-1 text-xs text-purple-600 dark:text-purple-300 backdrop-blur-md self-start sm:self-auto">
            <span className="font-semibold">{hoveredCell.originName}</span>
            <span className="text-[var(--accent)]">→</span>
            <span className="font-semibold">{hoveredCell.destName}</span>
            <span className="ml-1 font-bold text-emerald-500">{hoveredCell.volume} pass/hr</span>
          </div>
        ) : (
          <span className="text-[11px] text-[var(--muted)] self-start sm:self-auto hidden sm:block">
            Hover cell to inspect corridor
          </span>
        )}
      </div>

      {/* Grid Container */}
      <div className="overflow-x-auto rounded-xl border border-[var(--panel-border)] bg-black/[0.02] dark:bg-white/[0.02] p-2">
        <table className="w-full text-xs text-center border-collapse">
          <thead>
            <tr>
              <th className="p-2 text-[11px] font-semibold uppercase tracking-wider text-[var(--muted)] text-left">
                Origin \ Dest
              </th>
              {stationCodes.slice(0, grid.length).map((code) => (
                <th key={code} className="p-2 text-[11px] font-mono font-semibold text-[var(--muted)]">
                  {code}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {Array.isArray(grid) &&
              grid.map((row, i) => {
                const safeRow = Array.isArray(row) ? row : [];
                return (
                  <tr key={stationCodes[i] || i} className="border-t border-[var(--panel-border)]/40">
                    <td className="p-2 text-left font-mono font-semibold text-[var(--muted)]">
                      {stationCodes[i]}
                    </td>
                    {safeRow.map((val, j) => (
                      <td
                        key={`${i}-${j}`}
                        onMouseEnter={() =>
                          setHoveredCell({
                            originCode: stationCodes[i],
                            originName: stationNames[i] || stationCodes[i],
                            destCode: stationCodes[j],
                            destName: stationNames[j] || stationCodes[j],
                            volume: val,
                          })
                        }
                        onMouseLeave={() => setHoveredCell(null)}
                        className={`p-2 sm:p-2.5 rounded-lg transition-all duration-150 cursor-pointer m-0.5 font-medium ${getBgColor(
                          val
                        )} hover:scale-105 hover:shadow-md`}
                      >
                        {val === 0 ? "—" : val}
                      </td>
                    ))}
                  </tr>
                );
              })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
