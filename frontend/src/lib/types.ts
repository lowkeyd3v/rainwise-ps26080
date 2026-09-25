// Shared types used across frontend components

export interface RegimeData {
  detected_regime: string;
  regime_probs: Record<string, number>;
  confidence: number;
  indicators: {
    wind_speed_850: number;
    olr_anomaly: number;
    miso_phase: string;
  };
}

export interface ForecastData {
  date: string;
  lead_time_h: number;
  grid: {
    lat: number[];
    lon: number[];
    raw_nwp: number[][];
    corrected: number[][];
    prob_heavy: number[][];
    prob_very_heavy: number[][];
  };
  metrics: {
    rmse_raw: number;
    rmse_corrected: number;
    ets_raw: number;
    ets_corrected: number;
    fss_100km_raw: number;
    fss_100km_corrected: number;
  };
}

export interface DistrictForecast {
  district: string;
  state: string;
  corrected_rf_mm: number;
  prob_heavy_pct: number;
  prob_very_heavy_pct: number;
  warning_level: "none" | "yellow" | "orange" | "red";
  lat: number;
  lon: number;
}

export interface ApiResponse<T> {
  data: T;
  status: "ok" | "error";
  message?: string;
}

// Regime metadata
export const REGIME_META: Record<
  string,
  { color: string; bgColor: string; icon: string; description: string }
> = {
  "Active Monsoon": {
    color: "#3B82F6",
    bgColor: "rgba(59,130,246,0.15)",
    icon: "🌊",
    description: "Strong SW winds, low OLR, widespread heavy rainfall",
  },
  "Break Monsoon": {
    color: "#F59E0B",
    bgColor: "rgba(245,158,11,0.15)",
    icon: "☀️",
    description: "Suppressed convection, dry central India",
  },
  "Depression/Low": {
    color: "#EF4444",
    bgColor: "rgba(239,68,68,0.15)",
    icon: "🌀",
    description: "Closed cyclonic vortex, localized extreme rainfall",
  },
  Orographic: {
    color: "#10B981",
    bgColor: "rgba(16,185,129,0.15)",
    icon: "⛰️",
    description: "Terrain-forced uplift, Western Ghats / NE hills",
  },
  Coastal: {
    color: "#06B6D4",
    bgColor: "rgba(6,182,212,0.15)",
    icon: "🌊",
    description: "Sea-breeze fronts, coastal strip rainfall",
  },
  "Western Disturbance": {
    color: "#8B5CF6",
    bgColor: "rgba(139,92,246,0.15)",
    icon: "❄️",
    description: "Extratropical system, NW India / J&K",
  },
};

export const WARNING_COLORS: Record<string, string> = {
  none: "#1e293b",
  yellow: "#FCD34D",
  orange: "#FB923C",
  red: "#F87171",
};

export const WARNING_LABELS: Record<string, string> = {
  none: "No Warning",
  yellow: "Yellow — Heavy",
  orange: "Orange — Very Heavy",
  red: "Red — Extremely Heavy",
};
