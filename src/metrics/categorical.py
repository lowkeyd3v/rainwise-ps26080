"""
Verification Metrics Engine for PS 26080

Computes all required skill scores:
  - RMSE, Bias (deterministic)
  - ETS, CSI, POD, FAR (categorical)
  - FSS at multiple spatial scales (spatial skill)
  - Reliability diagram data (probabilistic)

Reference:
  - Roberts & Lean (2008): Fractions Skill Score (FSS)
  - WMO standard definitions for ETS, CSI, POD, FAR
"""

import numpy as np
from scipy.ndimage import uniform_filter


# ─── Deterministic Metrics ───────────────────────────────────────────────────

def rmse(obs: np.ndarray, fcst: np.ndarray) -> float:
    """Root Mean Square Error."""
    return float(np.sqrt(np.nanmean((fcst - obs) ** 2)))


def mean_bias(obs: np.ndarray, fcst: np.ndarray) -> float:
    """Mean Bias (Forecast - Observation)."""
    return float(np.nanmean(fcst - obs))


def correlation(obs: np.ndarray, fcst: np.ndarray) -> float:
    """Pearson Correlation Coefficient."""
    mask = ~(np.isnan(obs) | np.isnan(fcst))
    return float(np.corrcoef(obs[mask], fcst[mask])[0, 1])


# ─── Contingency Table ───────────────────────────────────────────────────────

def contingency_table(
    obs: np.ndarray,
    fcst: np.ndarray,
    threshold: float,
) -> dict[str, int]:
    """
    Build 2x2 contingency table for a given threshold.
    Returns: hits (H), misses (M), false alarms (FA), correct negatives (CN)
    """
    obs_bin = obs >= threshold
    fcst_bin = fcst >= threshold
    H  = int(np.sum(obs_bin & fcst_bin))
    M  = int(np.sum(obs_bin & ~fcst_bin))
    FA = int(np.sum(~obs_bin & fcst_bin))
    CN = int(np.sum(~obs_bin & ~fcst_bin))
    return {"H": H, "M": M, "FA": FA, "CN": CN}


def ets(ct: dict) -> float:
    """Equitable Threat Score (Gilbert Skill Score)."""
    H, M, FA, CN = ct["H"], ct["M"], ct["FA"], ct["CN"]
    total = H + M + FA + CN
    if total == 0:
        return np.nan
    H_ref = (H + M) * (H + FA) / total
    denom = H + M + FA - H_ref
    return float((H - H_ref) / denom) if denom != 0 else np.nan


def csi(ct: dict) -> float:
    """Critical Success Index (Threat Score)."""
    H, M, FA = ct["H"], ct["M"], ct["FA"]
    denom = H + M + FA
    return float(H / denom) if denom > 0 else np.nan


def pod(ct: dict) -> float:
    """Probability of Detection (Hit Rate)."""
    H, M = ct["H"], ct["M"]
    return float(H / (H + M)) if (H + M) > 0 else np.nan


def far(ct: dict) -> float:
    """False Alarm Ratio."""
    H, FA = ct["H"], ct["FA"]
    return float(FA / (H + FA)) if (H + FA) > 0 else np.nan


# ─── Fractions Skill Score (FSS) ─────────────────────────────────────────────

def fss(
    obs: np.ndarray,
    fcst: np.ndarray,
    threshold: float,
    scale_km: float,
    grid_spacing_km: float = 27.75,  # ~0.25 degree at India latitudes
) -> float:
    """
    Fractions Skill Score (Roberts & Lean, 2008).
    Measures spatial skill at a given neighbourhood scale.

    Args:
        obs: 2D observed rainfall [lat, lon]
        fcst: 2D forecast rainfall [lat, lon]
        threshold: rainfall threshold in mm
        scale_km: neighbourhood scale in km
        grid_spacing_km: km per grid cell

    Returns:
        FSS score in [0, 1] (1 = perfect)
    """
    n = max(1, int(round(scale_km / grid_spacing_km)))  # Window size in grid cells
    n = n if n % 2 == 1 else n + 1  # Make odd for symmetric window

    obs_bin = (obs >= threshold).astype(float)
    fcst_bin = (fcst >= threshold).astype(float)

    # Fraction fields (local rainfall frequency)
    obs_frac = uniform_filter(obs_bin, size=n, mode="constant")
    fcst_frac = uniform_filter(fcst_bin, size=n, mode="constant")

    # MSE of fractions
    mse = np.nanmean((fcst_frac - obs_frac) ** 2)

    # Reference MSE (assuming no spatial skill)
    mse_ref = np.nanmean(obs_frac ** 2) + np.nanmean(fcst_frac ** 2)

    if mse_ref == 0:
        return 1.0
    return float(1.0 - mse / mse_ref)


# ─── Full Verification Report ─────────────────────────────────────────────────

def compute_full_verification(
    obs: np.ndarray,
    fcst_raw: np.ndarray,
    fcst_corrected: np.ndarray,
    thresholds_mm: list[float] = None,
    fss_scales_km: list[float] = None,
) -> dict:
    """
    Compute all required verification metrics comparing raw NWP vs corrected.

    Returns:
        results dict with keys: deterministic, categorical, spatial
    """
    thresholds_mm = thresholds_mm or [1.0, 10.0, 35.5, 64.5, 115.0]
    fss_scales_km = fss_scales_km or [50, 100, 200, 500]

    results = {
        "deterministic": {},
        "categorical": {},
        "spatial": {},
    }

    # Deterministic
    for name, fcst in [("raw_nwp", fcst_raw), ("corrected", fcst_corrected)]:
        results["deterministic"][name] = {
            "rmse": rmse(obs, fcst),
            "bias": mean_bias(obs, fcst),
            "correlation": correlation(obs, fcst),
        }

    # Categorical (threshold-based)
    for thr in thresholds_mm:
        results["categorical"][thr] = {}
        for name, fcst in [("raw_nwp", fcst_raw), ("corrected", fcst_corrected)]:
            ct = contingency_table(obs.flatten(), fcst.flatten(), thr)
            results["categorical"][thr][name] = {
                "ETS": ets(ct),
                "CSI": csi(ct),
                "POD": pod(ct),
                "FAR": far(ct),
                "contingency": ct,
            }

    # Spatial FSS
    for scale in fss_scales_km:
        results["spatial"][f"{scale}km"] = {}
        for thr in [35.5, 64.5, 115.0]:
            results["spatial"][f"{scale}km"][f"{thr}mm"] = {
                "raw_nwp": fss(obs, fcst_raw, thr, scale),
                "corrected": fss(obs, fcst_corrected, thr, scale),
            }

    return results


def print_verification_summary(results: dict):
    """Print a formatted summary of verification results."""
    print("\n" + "=" * 60)
    print("  VERIFICATION REPORT — PS 26080")
    print("=" * 60)

    det = results["deterministic"]
    print("\n📊 DETERMINISTIC METRICS")
    print(f"{'Metric':<12} {'Raw NWP':>10} {'Corrected':>10} {'Improvement':>12}")
    print("-" * 50)
    for metric in ["rmse", "bias", "correlation"]:
        raw_val = det["raw_nwp"][metric]
        cor_val = det["corrected"][metric]
        if metric == "rmse":
            improvement = f"{(raw_val - cor_val) / raw_val * 100:+.1f}%"
        else:
            improvement = f"{(cor_val - raw_val):+.3f}"
        print(f"{metric.upper():<12} {raw_val:>10.3f} {cor_val:>10.3f} {improvement:>12}")

    cat = results["categorical"]
    print("\n📊 CATEGORICAL METRICS (ETS / POD / FAR)")
    print(f"{'Threshold':<12} {'Model':<12} {'ETS':>8} {'CSI':>8} {'POD':>8} {'FAR':>8}")
    print("-" * 60)
    for thr in [64.5, 115.0]:
        if thr in cat:
            for name in ["raw_nwp", "corrected"]:
                m = cat[thr][name]
                print(
                    f"{thr:<12.1f} {name:<12} {m['ETS']:>8.3f} "
                    f"{m['CSI']:>8.3f} {m['POD']:>8.3f} {m['FAR']:>8.3f}"
                )

    sp = results["spatial"]
    print("\n📊 FRACTIONS SKILL SCORE (FSS)")
    print(f"{'Scale':<10} {'Threshold':<12} {'Raw NWP':>10} {'Corrected':>10}")
    print("-" * 44)
    for scale_key, thr_dict in sp.items():
        for thr_key, models in thr_dict.items():
            print(
                f"{scale_key:<10} {thr_key:<12} "
                f"{models['raw_nwp']:>10.3f} {models['corrected']:>10.3f}"
            )
    print("=" * 60)


if __name__ == "__main__":
    # Demo with synthetic data
    np.random.seed(42)
    obs = np.clip(np.random.exponential(10, (128, 160)), 0, 300)
    fcst_raw = obs * 1.4 + np.random.normal(0, 8, obs.shape)
    fcst_corrected = obs * 1.05 + np.random.normal(0, 3, obs.shape)

    results = compute_full_verification(obs, fcst_raw, fcst_corrected)
    print_verification_summary(results)
