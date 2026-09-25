"use client";

import type { ForecastData } from "@/lib/types";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";

interface Props {
  data: ForecastData;
}

const METRICS = [
  { key: "rmse", label: "RMSE (mm)", lowerIsBetter: true },
  { key: "ets", label: "ETS (>64.5mm)", lowerIsBetter: false },
  { key: "fss_100km", label: "FSS @ 100km", lowerIsBetter: false },
];

export function MetricsScorecard({ data }: Props) {
  const { metrics } = data;

  const cards = [
    {
      label: "RMSE",
      raw: metrics.rmse_raw,
      corrected: metrics.rmse_corrected,
      unit: "mm",
      lowerIsBetter: true,
    },
    {
      label: "ETS",
      raw: metrics.ets_raw,
      corrected: metrics.ets_corrected,
      unit: "",
      lowerIsBetter: false,
    },
    {
      label: "FSS @ 100km",
      raw: metrics.fss_100km_raw,
      corrected: metrics.fss_100km_corrected,
      unit: "",
      lowerIsBetter: false,
    },
  ];

  return (
    <div className="bg-slate-800 rounded-2xl p-6 border border-slate-700">
      <h3 className="text-sm font-semibold uppercase tracking-widest text-slate-400 mb-4">
        📊 Skill Score Comparison
      </h3>
      <div className="grid grid-cols-3 gap-4">
        {cards.map((c) => {
          const improved = c.lowerIsBetter
            ? c.corrected < c.raw
            : c.corrected > c.raw;
          const pct = Math.abs(
            ((c.corrected - c.raw) / (Math.abs(c.raw) || 1)) * 100,
          ).toFixed(1);

          return (
            <div
              key={c.label}
              className="bg-slate-900 rounded-xl p-4 text-center"
            >
              <p className="text-xs text-slate-400 uppercase tracking-wider mb-2">
                {c.label}
              </p>
              <div className="flex justify-around items-end mb-2">
                <div>
                  <p className="text-[10px] text-slate-500">Raw NWP</p>
                  <p className="text-lg font-bold text-red-400">
                    {c.raw.toFixed(2)}
                    <span className="text-xs ml-0.5">{c.unit}</span>
                  </p>
                </div>
                <span className="text-slate-600 text-xl">→</span>
                <div>
                  <p className="text-[10px] text-slate-500">Corrected</p>
                  <p className="text-lg font-bold text-green-400">
                    {c.corrected.toFixed(2)}
                    <span className="text-xs ml-0.5">{c.unit}</span>
                  </p>
                </div>
              </div>
              <span
                className={`inline-block text-xs font-semibold px-2 py-0.5 rounded-full ${
                  improved
                    ? "bg-green-900 text-green-300"
                    : "bg-red-900 text-red-300"
                }`}
              >
                {improved ? "▲" : "▼"} {pct}%{" "}
                {improved ? "improvement" : "worse"}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
