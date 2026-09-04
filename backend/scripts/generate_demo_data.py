"""
scripts/generate_demo_data.py
------------------------------
Generates realistic Delhi-scale synthetic load data for demo/testing
when load_data.csv is not yet available.

This creates data ONLY for demo purposes and clearly labels it synthetic.
Output: data/raw/load_data.csv (synthetic Delhi load at 5-min resolution)

DO NOT use this for real forecasting — replace with actual load data.
Designed to match Delhi 2023-2025 seasonal/daily patterns:
  - Summer peak: ~7,000-7,500 MW (May-June)
  - Winter mid: ~4,000-4,500 MW (Dec-Jan)
  - Morning peak: ~07:00, Evening peak: ~20:00
  - 5-minute resolution
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
from app.core.config import settings

OUTPUT_FILE = settings.RAW_DATA_DIR / "load_data.csv"
SEED = 42
rng  = np.random.default_rng(SEED)


def seasonal_capacity(day_of_year: np.ndarray) -> np.ndarray:
    """Delhi seasonal load shape — peaks in summer (June), trough in winter (Jan)."""
    # Phase shift: peak around day ~165 (mid-June)
    return 5500 + 1800 * np.sin(2 * np.pi * (day_of_year - 80) / 365)


def daily_shape(hour: np.ndarray, minute: np.ndarray) -> np.ndarray:
    """Double-peak Delhi load profile."""
    t = hour + minute / 60
    morning_peak = 0.35 * np.exp(-((t - 9.5) ** 2) / 6)
    evening_peak = 0.50 * np.exp(-((t - 20.0) ** 2) / 8)
    base = 0.60
    return base + morning_peak + evening_peak


def generate_delhi_load(
    start: str = "2023-04-01",
    end:   str = "2026-01-31",
) -> pd.DataFrame:

    print(f"Generating synthetic Delhi 5-min load: {start} to {end}")
    timestamps = pd.date_range(start=start, end=end, freq="5min", tz="Asia/Kolkata")
    n = len(timestamps)
    print(f"  Total 5-min rows: {n:,}")

    hour = timestamps.hour.to_numpy()
    minute = timestamps.minute.to_numpy()
    doy = timestamps.dayofyear.to_numpy()
    dow = timestamps.dayofweek.to_numpy()

    season = seasonal_capacity(doy)
    shape  = daily_shape(hour, minute)

    # Weekend reduction
    weekend_factor = np.where(dow >= 5, 0.82, 1.0)

    # AC demand amplification (>34°C)
    temp = 28 + 16 * np.sin(2 * np.pi * (doy - 80) / 365) + rng.normal(0, 3, n)
    ac_boost = np.clip((temp - 34) * 50, 0, 500)

    load_mw = season * shape * weekend_factor + ac_boost + rng.normal(0, 80, n)
    load_mw = np.clip(load_mw, 500, None)

    # Inject realistic missing data (0.5% — maintenance windows, sensor faults)
    missing_idx = rng.choice(n, size=int(0.005 * n), replace=False)
    load_mw[missing_idx] = np.nan

    # Inject a few night-time maintenance outages (3-4 hour gaps)
    for _ in range(12):
        start_idx = rng.integers(0, n - 50)
        # Only during 01:00-04:00
        if timestamps[start_idx].hour in (1, 2, 3):
            load_mw[start_idx:start_idx + rng.integers(12, 50)] = np.nan

    df = pd.DataFrame({
        "timestamp": timestamps.strftime("%Y-%m-%d %H:%M:%S"),
        "load_MW": np.round(load_mw, 2),
    })

    return df


def main():
    settings.RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    if OUTPUT_FILE.exists():
        print(f"File already exists: {OUTPUT_FILE}")
        print("Delete it and re-run to regenerate.")
        return

    df = generate_delhi_load()

    n_nan  = df["load_MW"].isna().sum()
    n_rows = len(df)
    print(f"  Rows: {n_rows:,}  |  NaN: {n_nan:,}  ({100*n_nan/n_rows:.2f}%)")
    print(f"  Load range: {df['load_MW'].min():.0f} MW - {df['load_MW'].max():.0f} MW")
    print(f"  Mean: {df['load_MW'].mean():.0f} MW")

    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\n  [SYNTHETIC DATA] Saved to {OUTPUT_FILE}")
    print("  Replace with real load_data.csv for production forecasting.")
    print("\n  NEXT: python scripts/inspect_load_data.py")


if __name__ == "__main__":
    main()
