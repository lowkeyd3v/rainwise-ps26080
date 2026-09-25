"""
ERA5 Data Loader for PS 26080 - Regime-Aware Monsoon Rainfall Post-Processing

Downloads pressure-level and single-level ERA5 data for the Indian monsoon domain
using the Copernicus CDS API.

Requirements:
  - CDS API key configured at ~/.cdsapirc
  - pip install cdsapi xarray netCDF4
"""

import cdsapi
import xarray as xr
import numpy as np
from pathlib import Path
import yaml
import logging
import click

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def load_config(config_path: str = "configs/data_config.yaml") -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def download_era5_pressure_levels(
    config: dict,
    year: int,
    output_dir: Path,
    months: list[int] = None,
) -> Path:
    """Download ERA5 pressure-level data for a single year."""
    c = cdsapi.Client()
    cfg = config["era5"]
    dom = config["domain"]

    months = months or dom["monsoon_months"]
    month_strs = [f"{m:02d}" for m in months]

    output_path = output_dir / f"era5_plev_{year}_JJAS.nc"
    if output_path.exists():
        logger.info(f"Already exists: {output_path}")
        return output_path

    logger.info(f"Downloading ERA5 pressure levels for {year}...")
    c.retrieve(
        "reanalysis-era5-pressure-levels",
        {
            "product_type": "reanalysis",
            "variable": cfg["variables"],
            "pressure_level": [str(p) for p in cfg["pressure_levels"]],
            "year": str(year),
            "month": month_strs,
            "day": [f"{d:02d}" for d in range(1, 32)],
            "time": ["00:00", "06:00", "12:00", "18:00"],
            "area": [
                dom["lat_max"],
                dom["lon_min"],
                dom["lat_min"],
                dom["lon_max"],
            ],
            "format": "netcdf",
        },
        str(output_path),
    )
    logger.info(f"Saved: {output_path}")
    return output_path


def download_era5_single_levels(
    config: dict,
    year: int,
    output_dir: Path,
    months: list[int] = None,
) -> Path:
    """Download ERA5 single-level variables (OLR proxy, SST, precip)."""
    c = cdsapi.Client()
    cfg = config["era5"]
    dom = config["domain"]

    months = months or dom["monsoon_months"]
    month_strs = [f"{m:02d}" for m in months]

    output_path = output_dir / f"era5_sfc_{year}_JJAS.nc"
    if output_path.exists():
        logger.info(f"Already exists: {output_path}")
        return output_path

    logger.info(f"Downloading ERA5 single levels for {year}...")
    c.retrieve(
        "reanalysis-era5-single-levels",
        {
            "product_type": "reanalysis",
            "variable": cfg["single_level_variables"],
            "year": str(year),
            "month": month_strs,
            "day": [f"{d:02d}" for d in range(1, 32)],
            "time": ["00:00", "06:00", "12:00", "18:00"],
            "area": [
                dom["lat_max"],
                dom["lon_min"],
                dom["lat_min"],
                dom["lon_max"],
            ],
            "format": "netcdf",
        },
        str(output_path),
    )
    logger.info(f"Saved: {output_path}")
    return output_path


def compute_daily_composites(plev_path: Path, sfc_path: Path) -> xr.Dataset:
    """
    Compute daily-mean composites from 6-hourly ERA5 data.
    Key feature: daily mean 850hPa U,V wind + OLR proxy.
    """
    ds_plev = xr.open_dataset(plev_path)
    ds_sfc = xr.open_dataset(sfc_path)

    # Daily means
    ds_plev_daily = ds_plev.resample(time="1D").mean()
    ds_sfc_daily = ds_sfc.resample(time="1D").mean()

    # Extract key levels
    u850 = ds_plev_daily["u"].sel(pressure_level=850)
    v850 = ds_plev_daily["v"].sel(pressure_level=850)
    z500 = ds_plev_daily["z"].sel(pressure_level=500)
    t850 = ds_plev_daily["t"].sel(pressure_level=850)
    q850 = ds_plev_daily["q"].sel(pressure_level=850)
    u200 = ds_plev_daily["u"].sel(pressure_level=200)
    v200 = ds_plev_daily["v"].sel(pressure_level=200)

    # OLR proxy: negative of top thermal radiation
    olr = -ds_sfc_daily["mtnlwrf"] if "mtnlwrf" in ds_sfc_daily else None

    # Wind speed and direction at 850hPa
    ws850 = np.sqrt(u850**2 + v850**2)

    ds_composite = xr.Dataset({
        "u850": u850,
        "v850": v850,
        "ws850": ws850,
        "z500": z500,
        "t850": t850,
        "q850": q850,
        "u200": u200,
        "v200": v200,
    })
    if olr is not None:
        ds_composite["olr"] = olr

    ds_plev.close()
    ds_sfc.close()

    return ds_composite


@click.command()
@click.option("--config", default="configs/data_config.yaml", help="Data config path")
@click.option("--years", nargs=2, type=int, default=(2015, 2020), help="Start and end year")
@click.option("--months", default="6,7,8,9", help="Comma-separated months (JJAS=6,7,8,9)")
def main(config, years, months):
    """Download ERA5 data for the specified year range."""
    cfg = load_config(config)
    output_dir = Path(cfg["era5"]["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    month_list = [int(m) for m in months.split(",")]
    start_year, end_year = years

    for year in range(start_year, end_year + 1):
        try:
            plev_path = download_era5_pressure_levels(cfg, year, output_dir, month_list)
            sfc_path = download_era5_single_levels(cfg, year, output_dir, month_list)
            logger.info(f"Computing daily composites for {year}...")
            ds = compute_daily_composites(plev_path, sfc_path)
            composite_path = Path(cfg["processed"]["features_dir"]) / f"features_{year}_JJAS.nc"
            composite_path.parent.mkdir(parents=True, exist_ok=True)
            ds.to_netcdf(composite_path)
            logger.info(f"Features saved: {composite_path}")
        except Exception as e:
            logger.error(f"Failed for year {year}: {e}")
            raise


if __name__ == "__main__":
    main()
