"""
scripts/build_features.py
--------------------------
Builds the final ML-ready training dataset by merging:
  - Cleaned hourly load data (load_hourly.csv)
  - Historical Delhi weather (delhi_weather_historical.csv)

Feature groups:
  A. Temporal    -- hour_sin/cos, dow_sin/cos, month, is_weekend, is_holiday
  B. Load lags   -- lag_1h, lag_24h, lag_168h
  C. Rolling     -- roll_mean_3h, roll_mean_24h, roll_std_24h
  D. Weather     -- temperature_c, humidity_pct, cooling_degree_hrs, temp_lag_24h

Output:
  data/processed/features_hourly.csv  -- full feature matrix (training-ready)
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))
from app.core.config import settings

HOURLY_FILE     = settings.PROCESSED_DIR / "load_hourly.csv"
WEATHER_FILE    = settings.WEATHER_DIR   / "delhi_weather_historical.csv"
FEATURES_FILE   = settings.PROCESSED_DIR / "features_hourly.csv"

# Delhi public holidays (add more as needed)
DELHI_HOLIDAYS = [
    # 2023
    "2023-01-26", "2023-03-08", "2023-04-07", "2023-04-14",
    "2023-08-15", "2023-10-02", "2023-10-24", "2023-11-13",
    "2023-12-25",
    # 2024
    "2024-01-26", "2024-03-25", "2024-04-14", "2024-08-15",
    "2024-10-02", "2024-11-01", "2024-12-25",
    # 2025
    "2025-01-26", "2025-03-14", "2025-04-14", "2025-08-15",
    "2025-10-02", "2025-10-20", "2025-12-25",
    # 2026
    "2026-01-26", "2026-08-15",
]


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """Cyclical time encoding + calendar features."""
    df = df.copy()
    ts = df["timestamp"]

    df["hour"]       = ts.dt.hour
    df["day_of_week"]= ts.dt.dayofweek      # 0=Monday, 6=Sunday
    df["day_of_month"]= ts.dt.day
    df["month"]      = ts.dt.month
    df["is_weekend"] = (ts.dt.dayofweek >= 5).astype(int)

    # Cyclical encoding so hour 23 and hour 0 are numerically close
    df["hour_sin"]   = np.sin(2 * np.pi * df["hour"] / 24)
    df["hour_cos"]   = np.cos(2 * np.pi * df["hour"] / 24)
    df["dow_sin"]    = np.sin(2 * np.pi * df["day_of_week"] / 7)
    df["dow_cos"]    = np.cos(2 * np.pi * df["day_of_week"] / 7)
    df["month_sin"]  = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"]  = np.cos(2 * np.pi * df["month"] / 12)

    # Holiday flag
    holiday_dates = pd.to_datetime(DELHI_HOLIDAYS).normalize()
    df["is_holiday"] = ts.dt.normalize().isin(
        holiday_dates.tz_localize("Asia/Kolkata") if ts.dt.tz else holiday_dates
    ).astype(int)

    return df


def add_lag_features(df: pd.DataFrame) -> pd.DataFrame:
    """Lag features for load -- CRITICAL: these must only look backward."""
    df = df.copy().sort_values("timestamp").reset_index(drop=True)

    df["lag_1h"]   = df["load_MW"].shift(1)    # 1 hour ago
    df["lag_24h"]  = df["load_MW"].shift(24)   # same hour yesterday
    df["lag_168h"] = df["load_MW"].shift(168)  # same hour last week

    return df


def add_rolling_features(df: pd.DataFrame) -> pd.DataFrame:
    """Rolling window statistics -- all backward-looking (no leakage)."""
    df = df.copy().sort_values("timestamp").reset_index(drop=True)

    load = df["load_MW"]

    # min_periods=1: compute even if window not full (start of series)
    df["roll_mean_3h"]  = load.rolling(window=3,  min_periods=1).mean()
    df["roll_mean_24h"] = load.rolling(window=24, min_periods=1).mean()
    df["roll_std_24h"]  = load.rolling(window=24, min_periods=2).std().fillna(0)

    return df


def add_weather_features(df: pd.DataFrame, weather_df: pd.DataFrame) -> pd.DataFrame:
    """Merge historical weather and derive demand-relevant features."""
    df = df.copy()

    # Normalize timestamps for merging
    if hasattr(df["timestamp"].dt, "tz") and df["timestamp"].dt.tz is not None:
        df["ts_merge"] = df["timestamp"].dt.floor("h")
    else:
        df["ts_merge"] = pd.to_datetime(df["timestamp"]).dt.floor("h")

    if hasattr(weather_df["timestamp"].dt, "tz") and weather_df["timestamp"].dt.tz is not None:
        weather_df = weather_df.copy()
        weather_df["ts_merge"] = weather_df["timestamp"].dt.floor("h")
    else:
        weather_df = weather_df.copy()
        weather_df["ts_merge"] = pd.to_datetime(weather_df["timestamp"]).dt.floor("h")

    weather_slim = weather_df[["ts_merge","temperature_c","humidity_pct"]].copy()

    df = df.merge(weather_slim, on="ts_merge", how="left")
    df = df.drop(columns=["ts_merge"])

    # Cooling degree hours: how far above 24 degC (AC demand driver)
    # A Delhi-specific threshold -- AC kicks in above ~24 degC
    df["cooling_degree_hrs"] = (df["temperature_c"] - 24).clip(lower=0)

    # Yesterday's temperature (available at forecast time -- not future leakage)
    df["temp_lag_24h"] = df["temperature_c"].shift(24)

    return df


def build_features() -> pd.DataFrame:
    print("\n" + "="*65)
    print("  FEATURE ENGINEERING PIPELINE")
    print("="*65)

    # ── Load inputs ───────────────────────────────────────────────────────────
    print("\n[1/5] Loading hourly load data...")
    if not HOURLY_FILE.exists():
        print(f"  ERROR: {HOURLY_FILE} not found. Run preprocess_load.py first.")
        sys.exit(1)
    df = pd.read_csv(HOURLY_FILE, parse_dates=["timestamp"])
    print(f"  Rows: {len(df):,}  |  Range: {df['timestamp'].min()} -> {df['timestamp'].max()}")

    # Ensure IST timezone
    if df["timestamp"].dt.tz is None:
        df["timestamp"] = df["timestamp"].dt.tz_localize("Asia/Kolkata")

    # Use only rows with valid load (no long-gap rows)
    if "long_gap_flag" in df.columns:
        before = len(df)
        df = df[~df["long_gap_flag"]].copy()
        print(f"  Excluded {before - len(df):,} long-gap rows.")

    # ── Add time features ─────────────────────────────────────────────────────
    print("\n[2/5] Adding time features...")
    df = add_time_features(df)
    print(f"  Added: hour_sin, hour_cos, dow_sin, dow_cos, month_sin, month_cos, is_weekend, is_holiday")

    # ── Add lag features ──────────────────────────────────────────────────────
    print("\n[3/5] Adding lag features...")
    df = add_lag_features(df)
    print(f"  Added: lag_1h, lag_24h, lag_168h")
    n_nan_lag = df["lag_168h"].isna().sum()
    print(f"  NaN in lag_168h (first 168 hours): {n_nan_lag}")

    # ── Add rolling features ──────────────────────────────────────────────────
    print("\n[4/5] Adding rolling features...")
    df = add_rolling_features(df)
    print(f"  Added: roll_mean_3h, roll_mean_24h, roll_std_24h")

    # ── Add weather features ──────────────────────────────────────────────────
    print("\n[5/5] Adding weather features...")
    if not WEATHER_FILE.exists():
        print(f"  WARNING: {WEATHER_FILE} not found.")
        print("  Weather features will be NaN. Run fetch_historical_weather.py first.")
        df["temperature_c"]      = np.nan
        df["humidity_pct"]       = np.nan
        df["cooling_degree_hrs"] = np.nan
        df["temp_lag_24h"]       = np.nan
    else:
        weather_df = pd.read_csv(WEATHER_FILE, parse_dates=["timestamp"])
        if weather_df["timestamp"].dt.tz is None:
            weather_df["timestamp"] = weather_df["timestamp"].dt.tz_localize("Asia/Kolkata")
        df = add_weather_features(df, weather_df)
        n_temp_nan = df["temperature_c"].isna().sum()
        print(f"  Added: temperature_c, humidity_pct, cooling_degree_hrs, temp_lag_24h")
        print(f"  Weather NaN rows: {n_temp_nan:,} ({100*n_temp_nan/len(df):.1f}%)")

    # ── Feature summary ───────────────────────────────────────────────────────
    print("\n" + "="*65)
    print("  FEATURE SUMMARY")
    print("="*65)

    FEATURE_COLS = [
        "hour_sin", "hour_cos", "dow_sin", "dow_cos",
        "month_sin", "month_cos", "month",
        "is_weekend", "is_holiday",
        "lag_1h", "lag_24h", "lag_168h",
        "roll_mean_3h", "roll_mean_24h", "roll_std_24h",
        "temperature_c", "humidity_pct",
        "cooling_degree_hrs", "temp_lag_24h",
    ]

    available = [c for c in FEATURE_COLS if c in df.columns]
    print(f"  Total features:  {len(available)}")
    print(f"  Target column:   load_MW")
    print(f"  Total rows:      {len(df):,}")

    nan_summary = df[available].isna().sum()
    nan_cols = nan_summary[nan_summary > 0]
    if len(nan_cols) > 0:
        print(f"\n  Columns with NaN (will be handled by model training):")
        for col, n in nan_cols.items():
            print(f"    {col:25s}: {n:,}")

    # ── Save ──────────────────────────────────────────────────────────────────
    settings.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    cols_to_save = ["timestamp", "load_MW"] + available
    if "reading_count" in df.columns:
        cols_to_save.append("reading_count")
    df[cols_to_save].to_csv(FEATURES_FILE, index=False)
    print(f"\n  Saved: {FEATURES_FILE}  ({FEATURES_FILE.stat().st_size/1024:.1f} KB)")
    print("\n  NEXT STEP: python scripts/train_model.py")
    print("="*65)

    return df, available


if __name__ == "__main__":
    build_features()
