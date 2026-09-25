"use client";

import { WARNING_COLORS, WARNING_LABELS } from "@/lib/types";
import type { DistrictForecast } from "@/lib/types";
import { useState } from "react";
import { Download, Search } from "lucide-react";

interface Props {
  districts: DistrictForecast[];
}

export function DistrictTable({ districts }: Props) {
  const [search, setSearch] = useState("");
  const [warningFilter, setWarningFilter] = useState<string>("all");
  const [sortBy, setSortBy] = useState<"corrected_rf_mm" | "prob_heavy_pct">(
    "corrected_rf_mm",
  );

  const filtered = districts
    .filter((d) => {
      const matchSearch =
        d.district.toLowerCase().includes(search.toLowerCase()) ||
        d.state.toLowerCase().includes(search.toLowerCase());
      const matchFilter =
        warningFilter === "all" || d.warning_level === warningFilter;
      return matchSearch && matchFilter;
    })
    .sort((a, b) => b[sortBy] - a[sortBy]);

  const handleDownload = () => {
    const header = "District,State,Corrected RF (mm),P(Heavy) %,P(V.Heavy) %,Warning";
    const rows = filtered.map(
      (d) =>
        `${d.district},${d.state},${d.corrected_rf_mm},${d.prob_heavy_pct},${d.prob_very_heavy_pct},${WARNING_LABELS[d.warning_level]}`,
    );
    const csv = [header, ...rows].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "district_rainfall_forecast.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="bg-slate-800 rounded-2xl border border-slate-700">
      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-3 p-4 border-b border-slate-700">
        <h3 className="text-sm font-semibold uppercase tracking-widest text-slate-400 flex-1">
          📋 District-Level Forecast
        </h3>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-2.5 top-2.5 w-4 h-4 text-slate-500" />
          <input
            type="text"
            placeholder="Search district / state..."
            className="pl-9 pr-3 py-2 bg-slate-900 border border-slate-600 rounded-lg text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-blue-500 w-52"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        {/* Warning filter */}
        <select
          className="px-3 py-2 bg-slate-900 border border-slate-600 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-blue-500"
          value={warningFilter}
          onChange={(e) => setWarningFilter(e.target.value)}
        >
          <option value="all">All Warnings</option>
          <option value="red">🔴 Red</option>
          <option value="orange">🟠 Orange</option>
          <option value="yellow">🟡 Yellow</option>
          <option value="none">⚪ None</option>
        </select>

        {/* Sort */}
        <select
          className="px-3 py-2 bg-slate-900 border border-slate-600 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-blue-500"
          value={sortBy}
          onChange={(e) =>
            setSortBy(e.target.value as "corrected_rf_mm" | "prob_heavy_pct")
          }
        >
          <option value="corrected_rf_mm">Sort: Rainfall ↓</option>
          <option value="prob_heavy_pct">Sort: P(Heavy) ↓</option>
        </select>

        <button
          onClick={handleDownload}
          className="flex items-center gap-2 px-3 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-colors"
        >
          <Download className="w-4 h-4" />
          Download CSV
        </button>
      </div>

      {/* Table */}
      <div className="overflow-x-auto max-h-96 overflow-y-auto">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-slate-800">
            <tr className="text-xs text-slate-400 uppercase tracking-wider border-b border-slate-700">
              <th className="px-4 py-3 text-left">District</th>
              <th className="px-4 py-3 text-left">State</th>
              <th className="px-4 py-3 text-right">RF (mm)</th>
              <th className="px-4 py-3 text-right">P(Heavy)</th>
              <th className="px-4 py-3 text-right">P(V.Heavy)</th>
              <th className="px-4 py-3 text-center">Warning</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((d, i) => (
              <tr
                key={i}
                className="border-b border-slate-700/50 hover:bg-slate-700/30 transition-colors"
              >
                <td className="px-4 py-3 font-medium text-slate-200">
                  {d.district}
                </td>
                <td className="px-4 py-3 text-slate-400">{d.state}</td>
                <td className="px-4 py-3 text-right font-mono text-blue-300">
                  {d.corrected_rf_mm.toFixed(1)}
                </td>
                <td className="px-4 py-3 text-right">
                  <ProbBadge value={d.prob_heavy_pct} />
                </td>
                <td className="px-4 py-3 text-right">
                  <ProbBadge value={d.prob_very_heavy_pct} />
                </td>
                <td className="px-4 py-3 text-center">
                  <WarningBadge level={d.warning_level} />
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td
                  colSpan={6}
                  className="px-4 py-8 text-center text-slate-500"
                >
                  No districts match your filter.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="px-4 py-2 text-xs text-slate-500 border-t border-slate-700">
        Showing {filtered.length} of {districts.length} districts
      </div>
    </div>
  );
}

function ProbBadge({ value }: { value: number }) {
  const color =
    value >= 70
      ? "text-red-400 bg-red-900/40"
      : value >= 40
      ? "text-orange-400 bg-orange-900/40"
      : value >= 20
      ? "text-yellow-400 bg-yellow-900/40"
      : "text-slate-400 bg-slate-700";
  return (
    <span className={`inline-block px-2 py-0.5 rounded font-mono text-xs ${color}`}>
      {value.toFixed(1)}%
    </span>
  );
}

function WarningBadge({ level }: { level: string }) {
  const configs: Record<string, { label: string; classes: string }> = {
    red: { label: "🔴 Red", classes: "bg-red-900/50 text-red-300 border-red-700" },
    orange: { label: "🟠 Orange", classes: "bg-orange-900/50 text-orange-300 border-orange-700" },
    yellow: { label: "🟡 Yellow", classes: "bg-yellow-900/50 text-yellow-300 border-yellow-700" },
    none: { label: "⚪ None", classes: "bg-slate-700 text-slate-400 border-slate-600" },
  };
  const cfg = configs[level] ?? configs.none;
  return (
    <span className={`inline-block px-2 py-0.5 rounded border text-xs font-medium ${cfg.classes}`}>
      {cfg.label}
    </span>
  );
}
