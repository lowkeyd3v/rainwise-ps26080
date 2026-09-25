// Mock data generator — used when NEXT_PUBLIC_API_URL is not set
// Replace with real API calls once backend is deployed on Render

import type { RegimeData, ForecastData, DistrictForecast } from "./types";

export function getMockRegime(): RegimeData {
  return {
    detected_regime: "Active Monsoon",
    regime_probs: {
      "Active Monsoon": 0.62,
      "Break Monsoon": 0.08,
      "Depression/Low": 0.15,
      Orographic: 0.05,
      Coastal: 0.07,
      "Western Disturbance": 0.03,
    },
    confidence: 0.62,
    indicators: {
      wind_speed_850: 14.2,
      olr_anomaly: -24,
      miso_phase: "Phase 4 (Active)",
    },
  };
}

export function getMockForecast(): ForecastData {
  // Synthetic 32x40 grid (coarse, for demo)
  const rows = 32;
  const cols = 40;
  const lat = Array.from({ length: rows }, (_, i) => 6.5 + i * 1.0);
  const lon = Array.from({ length: cols }, (_, j) => 66.5 + j * 0.85);

  const seeded = (r: number, c: number, scale = 1) => {
    const v = Math.abs(Math.sin(r * 2.7 + c * 1.3) * Math.cos(r * 0.9 + c * 2.1));
    return Math.max(0, v * scale);
  };

  const raw_nwp = Array.from({ length: rows }, (_, r) =>
    Array.from({ length: cols }, (_, c) => seeded(r, c, 180)),
  );
  const corrected = Array.from({ length: rows }, (_, r) =>
    Array.from({ length: cols }, (_, c) => Math.max(0, seeded(r, c, 150))),
  );
  const prob_heavy = Array.from({ length: rows }, (_, r) =>
    Array.from({ length: cols }, (_, c) => Math.min(1, seeded(r, c, 1.2))),
  );
  const prob_very_heavy = Array.from({ length: rows }, (_, r) =>
    Array.from({ length: cols }, (_, c) => Math.min(1, seeded(r, c, 0.7))),
  );

  return {
    date: new Date().toISOString().slice(0, 10),
    lead_time_h: 24,
    grid: { lat, lon, raw_nwp, corrected, prob_heavy, prob_very_heavy },
    metrics: {
      rmse_raw: 18.4,
      rmse_corrected: 12.8,
      ets_raw: 0.22,
      ets_corrected: 0.48,
      fss_100km_raw: 0.38,
      fss_100km_corrected: 0.64,
    },
  };
}

const STATES = [
  "Maharashtra", "Madhya Pradesh", "Rajasthan", "Gujarat", "Karnataka",
  "Andhra Pradesh", "Telangana", "Odisha", "West Bengal", "Assam",
  "Kerala", "Tamil Nadu", "Uttar Pradesh", "Bihar", "Jharkhand",
];

const WARNING_LEVELS: Array<"none" | "yellow" | "orange" | "red"> = [
  "none", "yellow", "orange", "red",
];

function seededRandom(seed: number) {
  const x = Math.sin(seed) * 10000;
  return x - Math.floor(x);
}

export function getMockDistricts(): DistrictForecast[] {
  return Array.from({ length: 60 }, (_, i) => {
    const rf = Math.max(0, seededRandom(i * 7.3) * 200);
    const probH = Math.min(100, rf * 0.6 + seededRandom(i * 2.1) * 30);
    const probVH = Math.min(100, rf * 0.3 + seededRandom(i * 3.7) * 15);
    const warning: "none" | "yellow" | "orange" | "red" =
      rf > 204 ? "red" : rf > 115 ? "orange" : rf > 64.5 ? "yellow" : "none";

    return {
      district: `District ${i + 1}`,
      state: STATES[Math.floor(seededRandom(i * 5.1) * STATES.length)],
      corrected_rf_mm: Math.round(rf * 10) / 10,
      prob_heavy_pct: Math.round(probH * 10) / 10,
      prob_very_heavy_pct: Math.round(probVH * 10) / 10,
      warning_level: warning,
      lat: 8 + seededRandom(i * 4.2) * 28,
      lon: 68 + seededRandom(i * 6.5) * 30,
    };
  });
}
