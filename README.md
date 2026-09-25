# PS 26080 — Regime-Aware AI Post-Processing of Monsoon Rainfall Forecasts
## NCMRWF / Ministry of Earth Sciences | Smart India Hackathon

---

## 🎯 Problem

Rainfall forecast errors over India vary significantly with weather regimes (active monsoon,
break monsoon, depressions, orographic events). A single bias-correction method performs
poorly across all situations. This project builds a **regime-first, regime-specific** AI pipeline.

---

## 🏗️ Solution Architecture

```
Raw NWP Forecast
      ↓
[1] Regime Classifier (SOM + Transformer)
      ↓ regime label + confidence
[2] Mixture-of-Experts Bias Corrector (U-Net × 6 expert heads)
      ↓ bias-corrected gridded rainfall
[3] QRNN Heavy Rainfall Probability Estimator
      ↓ P(RF > 64.5mm), P(RF > 115mm)
[4] District Aggregation + Streamlit Dashboard
[5] Verification Report (RMSE, ETS, CSI, POD, FAR, FSS)
```

---

## 📦 Project Structure

```
megha/
├── app/main.py                         # Streamlit dashboard
├── src/
│   ├── data/era5_loader.py             # ERA5 CDS API downloader
│   ├── models/
│   │   ├── som_classifier.py           # SOM regime clustering
│   │   ├── moe_unet.py                 # Mixture-of-Experts U-Net
│   │   └── qrnn.py                     # Quantile Regression NN
│   └── metrics/categorical.py          # Verification metrics
├── configs/
│   ├── model_config.yaml
│   └── data_config.yaml
├── notebooks/                          # Step-by-step Jupyter notebooks
├── requirements.txt
└── README.md
```

---

## 🚀 Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure CDS API (for ERA5)
```bash
# Create ~/.cdsapirc with your CDS credentials:
# url: https://cds.climate.copernicus.eu/api/v2
# key: YOUR_KEY_HERE
```

### 3. Download data
```bash
python src/data/era5_loader.py --years 2015 2020
```

### 4. Train regime classifier (SOM stage)
```bash
python src/models/som_classifier.py --config configs/data_config.yaml
```

### 5. Launch dashboard
```bash
streamlit run app/main.py
```

### 6. Run verification
```bash
python src/metrics/categorical.py
```

---

## 📊 Weather Regimes

| # | Regime | Key Signals |
|---|---|---|
| 0 | Active Monsoon | Strong SW 850hPa wind, low OLR, positive MISO |
| 1 | Break Monsoon | Suppressed convection, weak winds, dry core zone |
| 2 | Depression/Low | Closed vortex, strong low-level convergence |
| 3 | Orographic | Terrain uplift, approach wind, coastal proximity |
| 4 | Coastal | Sea-breeze fronts, shallow convection |
| 5 | Western Disturbance | Extratropical system, NW India focus |

---

## 📈 Expected Performance Improvement

| Metric | Raw NWP | Our System |
|---|---|---|
| RMSE (mm) | ~18.5 | ~12.8 (-31%) |
| ETS (>64.5mm) | 0.22 | 0.48 (+118%) |
| FSS @ 100km | 0.38 | 0.64 (+68%) |
| POD (heavy RF) | 0.54 | 0.78 (+44%) |

---

## 🧑‍💻 Tech Stack

- **ML**: PyTorch (U-Net, Transformer), scikit-learn (SOM via MiniSom)
- **Data**: xarray, netCDF4, cdsapi (ERA5), geopandas
- **Metrics**: Custom FSS, xskillscore
- **Dashboard**: Streamlit + Plotly + Folium
- **Infra**: Docker, MLflow

---

## 📚 References

- Rasp & Lerch (2018) — Neural networks for post-processing ensemble weather forecasts
- Pai et al. (2014) — IMD 0.25° gridded rainfall dataset
- Roberts & Lean (2008) — Fractions Skill Score for spatial verification
- Rajeevan & Bhate (2009) — Active/break monsoon classification

---

*PS 26080 | Ministry of Earth Sciences | National Centre for Medium Range Weather Forecasting*
