"use client";

import React, { useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { apiFetch } from "@/lib/api";
import { getStoredToken } from "@/lib/auth";

interface GTFSFeed {
  id: string;
  feed_name: string;
  city: string;
  uploaded_at: string;
  total_stops: number;
  total_connections: number;
  interchange_count: number;
  status: string;
}

interface GraphNode {
  code: string;
  name: string;
  line: string;
  latitude: number;
  longitude: number;
  is_interchange: boolean;
}

interface GraphEdge {
  from_station: string;
  to_station: string;
  route_name: string;
  route_color: string;
  travel_seconds: number;
}

interface GraphResponse {
  city: string;
  total_nodes: number;
  total_edges: number;
  interchange_count: number;
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export default function GTFSWorkbenchPage() {
  const [city, setCity] = useState("Delhi");
  const [feeds, setFeeds] = useState<GTFSFeed[]>([]);
  const [graphData, setGraphData] = useState<GraphResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [ingesting, setIngesting] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const token = getStoredToken() ?? undefined;
      const [feedsRes, graphRes] = await Promise.all([
        apiFetch<GTFSFeed[]>(`/gtfs/feeds?city=${city}`, {}, token),
        apiFetch<GraphResponse>(`/gtfs/graph?city=${city}`, {}, token),
      ]);
      setFeeds(feedsRes);
      setGraphData(graphRes);
    } catch (err) {
      console.warn("Using baseline GTFS state:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [city]);

  const handleSampleIngest = async () => {
    setIngesting(true);
    setStatusMessage(null);
    try {
      const token = getStoredToken() ?? undefined;
      const res = await apiFetch<{ message: string }>(`/gtfs/sample-ingest?city=${city}`, { method: "POST" }, token);
      setStatusMessage(res.message);
      await loadData();
    } catch (err: any) {
      setStatusMessage(`Error: ${err.message || "Failed to ingest GTFS feed"}`);
    } finally {
      setIngesting(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIngesting(true);
    setStatusMessage(null);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("city", city);
    formData.append("feed_name", file.name);

    try {
      const token = getStoredToken() ?? undefined;
      const res = await apiFetch<{ message: string }>("/gtfs/upload", {
        method: "POST",
        body: formData,
      }, token);
      setStatusMessage(res.message);
      await loadData();
    } catch (err: any) {
      setStatusMessage(`Error: ${err.message || "GTFS file upload failed"}`);
    } finally {
      setIngesting(false);
    }
  };

  return (
    <AppShell title="GTFS Feed Pipeline" subtitle="Official GTFS Ingestion, Pandas Cleaning & Station Graph Engine">
      <div className="space-y-6">
        {/* Top Controls & Uploader */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900/80 border border-slate-800 p-6 rounded-2xl backdrop-blur-md">
          <div>
            <div className="flex items-center gap-2.5">
              <span className="p-2 bg-indigo-600/20 text-indigo-400 rounded-xl border border-indigo-500/30">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                </svg>
              </span>
              <div>
                <h1 className="text-xl font-bold text-white">GTFS Feed Ingestion & Graph Builder</h1>
                <p className="text-xs text-slate-400">Extract stops.txt, routes.txt, trips.txt, stop_times.txt into MongoDB GeoJSON.</p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <select
              value={city}
              onChange={(e) => setCity(e.target.value)}
              className="bg-slate-800 border border-slate-700 text-white text-sm rounded-xl px-3.5 py-2 focus:ring-2 focus:ring-indigo-500 outline-none"
            >
              <option value="Delhi">Delhi Metro</option>
              <option value="Mumbai">Mumbai Metro</option>
              <option value="Bengaluru">Bengaluru Metro</option>
            </select>

            <label className="cursor-pointer flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold px-4 py-2.5 rounded-xl transition-all shadow-lg shadow-indigo-600/20">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              Upload GTFS ZIP
              <input type="file" accept=".zip" onChange={handleFileUpload} className="hidden" />
            </label>

            <button
              onClick={handleSampleIngest}
              disabled={ingesting}
              className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium px-4 py-2.5 rounded-xl border border-slate-700 transition-all"
            >
              <svg className={`w-4 h-4 text-emerald-400 ${ingesting ? "animate-spin" : ""}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              Ingest Sample Feed
            </button>
          </div>
        </div>

        {statusMessage && (
          <div className="bg-indigo-950/80 border border-indigo-500/30 p-4 rounded-xl text-xs text-indigo-200 font-medium flex items-center gap-2">
            <svg className="w-4 h-4 text-indigo-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {statusMessage}
          </div>
        )}

        {/* Pipeline Summary KPIs */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-slate-900/90 border border-slate-800 p-5 rounded-2xl backdrop-blur-md">
            <p className="text-xs font-medium text-slate-400">Total Extracted Stops</p>
            <h3 className="text-2xl font-bold text-white mt-1">{graphData?.total_nodes || 0}</h3>
            <p className="text-xs text-emerald-400 mt-1">GeoJSON Points Verified</p>
          </div>

          <div className="bg-slate-900/90 border border-slate-800 p-5 rounded-2xl backdrop-blur-md">
            <p className="text-xs font-medium text-slate-400">Sequence Connection Edges</p>
            <h3 className="text-2xl font-bold text-white mt-1">{graphData?.total_edges || 0}</h3>
            <p className="text-xs text-indigo-400 mt-1">Directed Route Links</p>
          </div>

          <div className="bg-slate-900/90 border border-slate-800 p-5 rounded-2xl backdrop-blur-md">
            <p className="text-xs font-medium text-slate-400">Interchange Transfers</p>
            <h3 className="text-2xl font-bold text-white mt-1">{graphData?.interchange_count || 0}</h3>
            <p className="text-xs text-purple-400 mt-1">Multi-Route Junctions</p>
          </div>

          <div className="bg-slate-900/90 border border-slate-800 p-5 rounded-2xl backdrop-blur-md">
            <p className="text-xs font-medium text-slate-400">Active GTFS Manifests</p>
            <h3 className="text-2xl font-bold text-white mt-1">{feeds.length}</h3>
            <p className="text-xs text-cyan-400 mt-1">City Network Feeds</p>
          </div>
        </div>

        {/* Connection Graph Edges Table */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-2xl backdrop-blur-md">
          <div className="flex items-center justify-between gap-4 mb-4">
            <div>
              <h3 className="text-lg font-semibold text-white">Extracted Station Connections Graph</h3>
              <p className="text-xs text-slate-400 mt-0.5">Consecutive station sequence links computed from trips.txt & stop_times.txt.</p>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950/60 text-slate-400 uppercase font-medium">
                <tr>
                  <th className="p-3">From Station Code</th>
                  <th className="p-3">To Station Code</th>
                  <th className="p-3">Route Name</th>
                  <th className="p-3">Est. Travel Time</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50 font-mono">
                {(graphData?.edges || []).slice(0, 12).map((edge, i) => (
                  <tr key={i} className="hover:bg-slate-800/30 transition-colors">
                    <td className="p-3 text-white font-semibold">{edge.from_station}</td>
                    <td className="p-3 text-white font-semibold">{edge.to_station}</td>
                    <td className="p-3">
                      <span className="px-2 py-0.5 rounded text-[11px] font-sans font-medium bg-indigo-950 text-indigo-300 border border-indigo-500/30">
                        {edge.route_name}
                      </span>
                    </td>
                    <td className="p-3 text-emerald-400">{Math.round(edge.travel_seconds / 60)} mins ({edge.travel_seconds}s)</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
