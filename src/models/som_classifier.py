"""
SOM-based Weather Regime Classifier (Stage 1 of PS 26080 pipeline)

Uses Self-Organizing Maps (MiniSom) to cluster Indian monsoon synoptic patterns
into 6 regimes: Active, Break, Depression, Orographic, Coastal, Western Disturbance.

Flow:
  1. Load daily ERA5 feature composites
  2. Flatten spatial fields to feature vectors
  3. Train SOM on JJAS days (1991-2015)
  4. Assign regime labels to all days
  5. Save regime label CSV for use in downstream modules

Reference: SOM applied to Indian monsoon regimes - common in literature
"""

import numpy as np
import pandas as pd
import xarray as xr
from minisom import MiniSom
from pathlib import Path
import matplotlib.pyplot as plt
import pickle
import logging
import click
import yaml

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Human-readable names for 6 SOM nodes (assigned post-training based on composites)
REGIME_NAMES = {
    0: "active_monsoon",
    1: "break_monsoon",
    2: "depression_low",
    3: "orographic",
    4: "coastal",
    5: "western_disturbance",
}


def load_features(features_dir: Path, years: range) -> tuple[np.ndarray, pd.DatetimeIndex]:
    """Load and stack ERA5 daily feature composites across years."""
    datasets = []
    dates = []
    for year in years:
        fpath = features_dir / f"features_{year}_JJAS.nc"
        if not fpath.exists():
            logger.warning(f"Missing: {fpath}, skipping {year}")
            continue
        ds = xr.open_dataset(fpath)
        # Stack: [time, lat, lon, n_vars]
        vars_to_use = ["u850", "v850", "z500", "olr"]
        available = [v for v in vars_to_use if v in ds]
        arr = np.stack([ds[v].values for v in available], axis=-1)  # [T, lat, lon, V]
        # Flatten spatial dims
        T, lat, lon, V = arr.shape
        arr_flat = arr.reshape(T, lat * lon * V)
        datasets.append(arr_flat)
        dates.extend(pd.to_datetime(ds["time"].values))
        ds.close()

    X = np.vstack(datasets)
    return X, pd.DatetimeIndex(dates)


def normalize(X: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Standardize features."""
    mu = X.mean(axis=0)
    sigma = X.std(axis=0) + 1e-8
    return (X - mu) / sigma, mu, sigma


def train_som(
    X_norm: np.ndarray,
    grid_x: int = 3,
    grid_y: int = 2,
    n_iterations: int = 10000,
    sigma: float = 1.0,
    lr: float = 0.5,
    seed: int = 42,
) -> MiniSom:
    """Train a Self-Organizing Map."""
    som = MiniSom(
        x=grid_x,
        y=grid_y,
        input_len=X_norm.shape[1],
        sigma=sigma,
        learning_rate=lr,
        random_seed=seed,
        neighborhood_function="gaussian",
    )
    som.random_weights_init(X_norm)
    logger.info(f"Training SOM ({grid_x}x{grid_y}) on {len(X_norm)} samples...")
    som.train_random(X_norm, n_iterations)
    logger.info("SOM training complete.")
    return som


def assign_labels(som: MiniSom, X_norm: np.ndarray) -> np.ndarray:
    """Assign each sample to its Best Matching Unit (BMU) → regime label."""
    labels = []
    for x in X_norm:
        bmu_x, bmu_y = som.winner(x)
        label = bmu_x * som.get_weights().shape[1] + bmu_y  # Flatten 2D node to 1D
        labels.append(label)
    return np.array(labels)


def plot_som_umatrix(som: MiniSom, output_path: Path):
    """Plot U-Matrix (distance map) for visualization."""
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.pcolor(som.distance_map().T, cmap="bone_r")
    ax.set_title("SOM U-Matrix (Regime Distance Map)")
    ax.set_xlabel("SOM node X")
    ax.set_ylabel("SOM node Y")
    plt.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    logger.info(f"U-Matrix saved: {output_path}")


@click.command()
@click.option("--config", default="configs/data_config.yaml")
@click.option("--model-config", default="configs/model_config.yaml")
@click.option("--output-dir", default="data/processed/regime_labels/")
def main(config, model_config, output_dir):
    """Run SOM clustering to assign weather regime labels."""
    with open(config) as f:
        cfg = yaml.safe_load(f)
    with open(model_config) as f:
        mcfg = yaml.safe_load(f)

    som_cfg = mcfg["regime_classifier"]["som"]
    domain_cfg = cfg["domain"]

    features_dir = Path(cfg["processed"]["features_dir"])
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    train_years = range(*domain_cfg["training_years"])
    val_years = range(*domain_cfg["validation_years"])
    test_years = range(*domain_cfg["test_years"])
    all_years = list(train_years) + list(val_years) + list(test_years)

    logger.info("Loading training features...")
    X_train, dates_train = load_features(features_dir, train_years)

    X_norm_train, mu, sigma = normalize(X_train)

    som = train_som(
        X_norm_train,
        grid_x=som_cfg["grid_x"],
        grid_y=som_cfg["grid_y"],
        n_iterations=som_cfg["n_iterations"],
        sigma=som_cfg["sigma"],
        lr=som_cfg["learning_rate"],
    )

    # Save SOM model
    som_path = out_dir / "som_model.pkl"
    with open(som_path, "wb") as f:
        pickle.dump({"som": som, "mu": mu, "sigma": sigma}, f)
    logger.info(f"SOM saved: {som_path}")

    # U-Matrix plot
    plot_som_umatrix(som, out_dir / "som_umatrix.png")

    # Assign labels to all years
    logger.info("Assigning regime labels to all years...")
    X_all, dates_all = load_features(features_dir, all_years)
    X_all_norm = (X_all - mu) / (sigma + 1e-8)
    labels = assign_labels(som, X_all_norm)

    # Save label CSV
    df = pd.DataFrame({
        "date": dates_all,
        "regime_id": labels,
        "regime_name": [REGIME_NAMES.get(l, f"regime_{l}") for l in labels],
    })
    label_path = out_dir / "regime_labels_all.csv"
    df.to_csv(label_path, index=False)
    logger.info(f"Regime labels saved: {label_path}")

    # Print distribution
    logger.info("Regime distribution:\n" + str(df["regime_name"].value_counts()))


if __name__ == "__main__":
    main()
