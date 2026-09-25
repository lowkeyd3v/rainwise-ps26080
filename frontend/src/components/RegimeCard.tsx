"use client";

import { REGIME_META } from "@/lib/types";
import type { RegimeData } from "@/lib/types";
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  Radar,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
} from "recharts";

interface Props {
  data: RegimeData;
}

export function RegimeCard({ data }: Props) {
  const meta = REGIME_META[data.detected_regime] ?? {
    color: "#94a3b8",
    bgColor: "rgba(148,163,184,0.15)",
    icon: "🌤️",
    description: "Unknown regime",
  };

  const barData = Object.entries(data.regime_probs).map(([name, prob]) => ({
    name: name.split(" ")[0], // Short label
    fullName: name,
    prob: Math.round(prob * 100),
    color: REGIME_META[name]?.color ?? "#94a3b8",
  }));

  return (
    <div className="bg-slate-800 rounded-2xl p-6 border border-slate-700">
      {/* Detected Regime Badge */}
      <div
        className="flex items-start gap-4 p-4 rounded-xl mb-5"
        style={{ backgroundColor: meta.bgColor, borderLeft: `4px solid ${meta.color}` }}
      >
        <span className="text-4xl">{meta.icon}</span>
        <div>
          <p className="text-xs font-semibold uppercase tracking-widest text-slate-400 mb-1">
            Detected Regime
          </p>
          <h2 className="text-2xl font-bold" style={{ color: meta.color }}>
            {data.detected_regime}
          </h2>
          <p className="text-sm text-slate-300 mt-1">{meta.description}</p>
          <div className="flex items-center gap-2 mt-2">
            <div className="h-1.5 rounded-full bg-slate-600 w-32">
              <div
                className="h-1.5 rounded-full transition-all"
                style={{
                  width: `${Math.round(data.confidence * 100)}%`,
                  backgroundColor: meta.color,
                }}
              />
            </div>
            <span className="text-xs text-slate-300">
              {Math.round(data.confidence * 100)}% confidence
            </span>
          </div>
        </div>
      </div>

      {/* Regime Probability Bar Chart */}
      <p className="text-xs font-semibold uppercase tracking-widest text-slate-400 mb-3">
        Regime Probabilities
      </p>
      <ResponsiveContainer width="100%" height={160}>
        <BarChart data={barData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
          <XAxis
            dataKey="name"
            tick={{ fill: "#94a3b8", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: "#94a3b8", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            unit="%"
          />
          <Tooltip
            formatter={(val, _, { payload }) => [
              `${val}%`,
              payload?.fullName ?? "",
            ]}
            contentStyle={{
              background: "#1e293b",
              border: "1px solid #334155",
              borderRadius: 8,
              color: "#e2e8f0",
            }}
          />
          <Bar dataKey="prob" radius={[4, 4, 0, 0]}>
            {barData.map((entry, i) => (
              <Cell key={i} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Atmospheric Indicators */}
      <div className="grid grid-cols-3 gap-3 mt-4">
        <Indicator
          label="850hPa Wind"
          value={`${data.indicators.wind_speed_850.toFixed(1)} m/s`}
          trend="up"
        />
        <Indicator
          label="OLR Anomaly"
          value={`${data.indicators.olr_anomaly.toFixed(0)} W/m²`}
          trend={data.indicators.olr_anomaly < 0 ? "down" : "up"}
        />
        <Indicator
          label="MISO Phase"
          value={data.indicators.miso_phase}
          trend="neutral"
        />
      </div>
    </div>
  );
}

function Indicator({
  label,
  value,
  trend,
}: {
  label: string;
  value: string;
  trend: "up" | "down" | "neutral";
}) {
  const trendColor =
    trend === "up" ? "text-green-400" : trend === "down" ? "text-blue-400" : "text-slate-400";
  return (
    <div className="bg-slate-900 rounded-lg p-3 text-center">
      <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-1">{label}</p>
      <p className={`text-sm font-semibold ${trendColor}`}>{value}</p>
    </div>
  );
}
