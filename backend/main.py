"""
RainWise FastAPI Backend — PS 26080
Deployed on Render (free tier)

Routes:
  GET /api/regime          → Weather regime classification
  GET /api/forecast        → Bias-corrected rainfall + metrics
  GET /api/districts       → District-level aggregated forecast
  GET /health              → Health check (required by Render)
"""

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import date
import numpy as np
import math

app = FastAPI(
    title="RainWise API",
    description="Regime-Aware Monsoon Rainfall Post-Processing — PS 26080",
    version="1.0.0",
)

# Allow Vercel frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://rainwise.vercel.app",
        "https://*.vercel.app",  # Preview deployments
    ],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


# ─── Health Check ────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "service": "RainWise API", "ps": "26080"}


# ─── Regime Endpoint ─────────────────────────────────────────────────────────

REGIMES = [
    "Active Monsoon",
    "Break Monsoon",
    "Depression/Low",
    "Orographic",
    "Coastal",
    "Western Disturbance",
]


@app.get("/api/regime")
def get_regime(
    date_str: str = Query(default=str(date.today()), alias="date"),
    lead_h: int = Query(default=24),
):
    """
    Returns weather regime classification.
    In production: runs the Transformer classifier on ERA5 analysis fields.
    Currently: deterministic mock based on date seed.
    """
    seed = sum(ord(c) for c in date_str) + lead_h
    rng = np.random.RandomState(seed)

    raw_probs = rng.dirichlet(alpha=[3, 1, 1.5, 0.8, 0.8, 0.4])
    regime_probs = {REGIMES[i]: float(raw_probs[i]) for i in range(len(REGIMES))}
    detected = max(regime_probs, key=lambda k: regime_probs[k])
    confidence = regime_probs[detected]

    return {
        "data": {
            "detected_regime": detected,
            "regime_probs": regime_probs,
            "confidence": confidence,
            "indicators": {
                "wind_speed_850": float(rng.uniform(8, 18)),
                "olr_anomaly": float(rng.uniform(-35, 15)),
                "miso_phase": f"Phase {rng.randint(1, 9)} ({'Active' if rng.rand() > 0.5 else 'Suppressed'})",
            },
        },
        "status": "ok",
    }


# ─── Forecast Endpoint ───────────────────────────────────────────────────────

@app.get("/api/forecast")
def get_forecast(
    date_str: str = Query(default=str(date.today()), alias="date"),
    lead_h: int = Query(default=24),
):
    """
    Returns gridded rainfall forecast (raw NWP + corrected + probabilities).
    In production: runs MoE U-Net inference on NWP GRIB files.
    Currently: deterministic synthetic grid.
    """
    seed = sum(ord(c) for c in date_str) + lead_h
    rows, cols = 32, 40
    lat = [round(6.5 + i * 1.0, 2) for i in range(rows)]
    lon = [round(66.5 + j * 0.85, 2) for j in range(cols)]

    def seeded_grid(scale: float, s_offset: int = 0) -> list[list[float]]:
        return [
            [
                max(0.0, abs(math.sin((r + s_offset) * 2.7 + c * 1.3 + seed * 0.01)
                             * math.cos(r * 0.9 + (c + s_offset) * 2.1)) * scale)
                for c in range(cols)
            ]
            for r in range(rows)
        ]

    raw_nwp = seeded_grid(200)
    corrected = [[max(0.0, v * 0.82) for v in row] for row in seeded_grid(165, 5)]
    prob_heavy = [[min(1.0, v / 180.0) for v in row] for row in seeded_grid(220, 10)]
    prob_vh = [[min(1.0, v / 300.0) for v in row] for row in seeded_grid(220, 15)]

    return {
        "data": {
            "date": date_str,
            "lead_time_h": lead_h,
            "grid": {
                "lat": lat,
                "lon": lon,
                "raw_nwp": raw_nwp,
                "corrected": corrected,
                "prob_heavy": prob_heavy,
                "prob_very_heavy": prob_vh,
            },
            "metrics": {
                "rmse_raw": 18.4,
                "rmse_corrected": 12.8,
                "ets_raw": 0.22,
                "ets_corrected": 0.48,
                "fss_100km_raw": 0.38,
                "fss_100km_corrected": 0.64,
            },
        },
        "status": "ok",
    }


# ─── Districts Endpoint ───────────────────────────────────────────────────────

STATES = [
    "Maharashtra", "Madhya Pradesh", "Rajasthan", "Gujarat", "Karnataka",
    "Andhra Pradesh", "Telangana", "Odisha", "West Bengal", "Assam",
    "Kerala", "Tamil Nadu", "Uttar Pradesh", "Bihar", "Jharkhand",
]


@app.get("/api/districts")
def get_districts(
    date_str: str = Query(default=str(date.today()), alias="date"),
    lead_h: int = Query(default=24),
):
    """
    Returns district-level aggregated rainfall forecasts.
    In production: spatial averaging of corrected grid to district polygons.
    """
    seed = sum(ord(c) for c in date_str) + lead_h

    def seeded_rand(i: int, offset: float = 1.0) -> float:
        x = math.sin(i * offset + seed * 0.01) * 10000
        return x - math.floor(x)

    districts = []
    for i in range(60):
        rf = max(0.0, seeded_rand(i, 7.3) * 200)
        prob_h = min(100.0, rf * 0.6 + seeded_rand(i, 2.1) * 30)
        prob_vh = min(100.0, rf * 0.3 + seeded_rand(i, 3.7) * 15)
        warning = "red" if rf > 204 else "orange" if rf > 115 else "yellow" if rf > 64.5 else "none"
        state_idx = int(seeded_rand(i, 5.1) * len(STATES))

        districts.append({
            "district": f"District {i + 1}",
            "state": STATES[state_idx],
            "corrected_rf_mm": round(rf, 1),
            "prob_heavy_pct": round(prob_h, 1),
            "prob_very_heavy_pct": round(prob_vh, 1),
            "warning_level": warning,
            "lat": round(8 + seeded_rand(i, 4.2) * 28, 4),
            "lon": round(68 + seeded_rand(i, 6.5) * 30, 4),
        })

    return {"data": districts, "status": "ok"}
