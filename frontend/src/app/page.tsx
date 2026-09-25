import { RegimeCard } from "@/components/RegimeCard";
import { MetricsScorecard } from "@/components/MetricsScorecard";
import { DistrictTable } from "@/components/DistrictTable";
import { getMockRegime, getMockForecast, getMockDistricts } from "@/lib/mockData";
import { CloudRain, Cpu, BarChart3, Map } from "lucide-react";

// Note: When backend is live on Render, replace mock calls with:
// import { getRegime, getForecast, getDistricts } from "@/lib/api";

export const revalidate = 1800; // Re-fetch every 30 minutes (ISR)

export default async function Home() {
  // Demo mode: deterministic mock data
  const regimeData = getMockRegime();
  const forecastData = getMockForecast();
  const districts = getMockDistricts();

  const today = new Date().toLocaleDateString("en-IN", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  return (
    <div className="min-h-screen bg-slate-900">
      {/* ── Top Nav ── */}
      <nav className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-blue-600 flex items-center justify-center">
              <CloudRain className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="font-bold text-slate-100 leading-none">RainWise</h1>
              <p className="text-[10px] text-slate-500 leading-none mt-0.5">
                PS 26080 · NCMRWF / MoES
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4 text-sm text-slate-400">
            <span className="hidden md:block">{today}</span>
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
              Live · Day+1 Forecast
            </span>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 py-6 space-y-6">

        {/* ── Step Breadcrumb ── */}
        <div className="flex flex-wrap gap-2">
          {[
            { icon: <Cpu className="w-3.5 h-3.5" />, label: "1 · Regime Detection" },
            { icon: <BarChart3 className="w-3.5 h-3.5" />, label: "2 · Bias Correction" },
            { icon: <CloudRain className="w-3.5 h-3.5" />, label: "3 · Heavy Rain Prob." },
            { icon: <Map className="w-3.5 h-3.5" />, label: "4 · District Product" },
          ].map((step, i) => (
            <span
              key={i}
              className="flex items-center gap-1.5 px-3 py-1 bg-slate-800 border border-slate-700 rounded-full text-xs text-slate-300"
            >
              {step.icon} {step.label}
            </span>
          ))}
        </div>

        {/* ── Row 1: Regime + Metrics ── */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          <div className="lg:col-span-2">
            <RegimeCard data={regimeData} />
          </div>
          <div className="lg:col-span-3 flex flex-col gap-6">
            <MetricsScorecard data={forecastData} />

            {/* Quick stats strip */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {[
                { label: "Bias Improvement", value: "−31%", sub: "RMSE vs raw NWP", color: "text-green-400" },
                { label: "ETS Gain", value: "+118%", sub: "for Heavy RF", color: "text-blue-400" },
                { label: "POD Heavy RF", value: "78%", sub: "vs 54% raw NWP", color: "text-purple-400" },
                { label: "Districts Warned", value: `${districts.filter(d => d.warning_level !== "none").length}`, sub: "out of 60 sampled", color: "text-orange-400" },
              ].map((stat, i) => (
                <div key={i} className="bg-slate-800 rounded-xl p-4 border border-slate-700">
                  <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-1">
                    {stat.label}
                  </p>
                  <p className={`text-2xl font-bold ${stat.color}`}>{stat.value}</p>
                  <p className="text-[10px] text-slate-500 mt-0.5">{stat.sub}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ── Row 2: Rainfall Grid Heatmaps ── */}
        <div className="bg-slate-800 rounded-2xl p-6 border border-slate-700">
          <h3 className="text-sm font-semibold uppercase tracking-widest text-slate-400 mb-4">
            🗺️ Gridded Rainfall Forecast (India, 0.25°)
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <GridHeatmap
              title="❌ Raw NWP Forecast"
              grid={forecastData.grid.raw_nwp}
              maxVal={200}
              badgeColor="bg-red-900 text-red-300"
            />
            <GridHeatmap
              title="✅ Regime-Aware Corrected"
              grid={forecastData.grid.corrected}
              maxVal={200}
              badgeColor="bg-green-900 text-green-300"
            />
          </div>
          <p className="text-xs text-slate-500 mt-3 text-center">
            Color scale: 0mm (white) → 200mm+ (deep blue) · Grid: 32×40 cells (demo resolution)
          </p>
        </div>

        {/* ── Row 3: Probability Maps ── */}
        <div className="bg-slate-800 rounded-2xl p-6 border border-slate-700">
          <h3 className="text-sm font-semibold uppercase tracking-widest text-slate-400 mb-4">
            ⚠️ Heavy Rainfall Probability (from QRNN)
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <GridHeatmap
              title="P(RF > 64.5mm) — Heavy"
              grid={forecastData.grid.prob_heavy}
              maxVal={1}
              colorScale="reds"
              badgeColor="bg-orange-900 text-orange-300"
            />
            <GridHeatmap
              title="P(RF > 115mm) — Very Heavy"
              grid={forecastData.grid.prob_very_heavy}
              maxVal={1}
              colorScale="reds"
              badgeColor="bg-red-900 text-red-300"
            />
          </div>
        </div>

        {/* ── Row 4: District Table ── */}
        <DistrictTable districts={districts} />

        {/* ── Footer ── */}
        <footer className="text-center text-xs text-slate-600 py-6 border-t border-slate-800">
          🌧️ <strong className="text-slate-500">RainWise</strong> · Regime-Aware AI Post-Processing of Monsoon Rainfall Forecasts ·{" "}
          PS 26080 · NCMRWF / Ministry of Earth Sciences ·{" "}
          <span className="text-blue-600">Smart India Hackathon</span>
        </footer>
      </main>
    </div>
  );
}

// ── Inline SVG Heatmap (no canvas/WebGL needed, Vercel-safe) ─────────────────

function GridHeatmap({
  title,
  grid,
  maxVal,
  colorScale = "blues",
  badgeColor,
}: {
  title: string;
  grid: number[][];
  maxVal: number;
  colorScale?: "blues" | "reds";
  badgeColor: string;
}) {
  const rows = grid.length;
  const cols = grid[0]?.length ?? 0;
  const cellW = 100 / cols;
  const cellH = 100 / rows;

  function toColor(val: number): string {
    const t = Math.min(1, Math.max(0, val / maxVal));
    if (colorScale === "reds") {
      const r = Math.round(255);
      const g = Math.round(255 * (1 - t * 0.9));
      const b = Math.round(255 * (1 - t));
      return `rgb(${r},${g},${b})`;
    }
    // Blues
    const r = Math.round(255 * (1 - t * 0.85));
    const g = Math.round(255 * (1 - t * 0.7));
    const b = Math.round(255 * (0.5 + t * 0.5));
    return `rgb(${r},${g},${b})`;
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <p className="text-sm font-medium text-slate-300">{title}</p>
        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${badgeColor}`}>
          Model output
        </span>
      </div>
      <div className="rounded-lg overflow-hidden border border-slate-700 bg-slate-900">
        <svg
          viewBox={`0 0 ${cols} ${rows}`}
          className="w-full"
          style={{ aspectRatio: `${cols}/${rows}` }}
          preserveAspectRatio="none"
        >
          {grid.map((row, r) =>
            row.map((val, c) => (
              <rect
                key={`${r}-${c}`}
                x={c}
                y={r}
                width={1}
                height={1}
                fill={toColor(val)}
              />
            )),
          )}
        </svg>
      </div>
    </div>
  );
}
