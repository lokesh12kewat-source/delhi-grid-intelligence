"""
scripts/preprocess_load.py
---------------------------
Reproducible preprocessing pipeline for Delhi load data.

Steps:
  1. Load raw load_data.csv (no modification to raw file)
  2. Parse + standardize timestamps to IST
  3. Sort chronologically
  4. Remove duplicates
  5. Validate 5-minute intervals
  6. Detect + report missing timestamps
  7. Detect + report missing load values
  8. Interpolate short gaps (≤ 2 hours = 24 readings)
  9. Flag long gaps (> 2 hours) for exclusion during training
  10. Detect abnormal values (IQR outlier filter — conservative 3×)
  11. Aggregate to hourly (mean of up to 12 readings)
  12. Save preprocessed outputs + report

Outputs:
  data/processed/load_5min_clean.csv    — cleaned 5-min data
  data/processed/load_hourly.csv        — hourly aggregated (training-ready)
  data/processed/preprocessing_report.txt
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from io import StringIO

sys.path.insert(0, str(Path(__file__).parent.parent))
from app.core.config import settings

RAW_FILE            = settings.RAW_DATA_DIR  / "load_data.csv"
CLEAN_5MIN_FILE     = settings.PROCESSED_DIR / "load_5min_clean.csv"
HOURLY_FILE         = settings.PROCESSED_DIR / "load_hourly.csv"
REPORT_FILE         = settings.PROCESSED_DIR / "preprocessing_report.txt"


def run():
    report_lines = []

    def log(msg=""):
        print(msg)
        report_lines.append(msg)

    log("=" * 65)
    log("  DELHI LOAD DATA — PREPROCESSING REPORT")
    log("=" * 65)

    # ── 1. Load raw file ──────────────────────────────────────────────────────
    log("\n[1] Loading raw file...")
    if not RAW_FILE.exists():
        log(f"  ERROR: {RAW_FILE} not found. Drop load_data.csv into data/raw/")
        sys.exit(1)

    df = pd.read_csv(RAW_FILE)
    log(f"  Rows: {len(df):,}  |  Columns: {list(df.columns)}")

    # ── 2. Identify columns ───────────────────────────────────────────────────
    ts_col   = None
    load_col = None
    for col in df.columns:
        cl = col.lower().strip()
        if any(k in cl for k in ["time", "date", "timestamp"]) and ts_col is None:
            ts_col = col
        if any(k in cl for k in ["load", "mw", "demand", "power"]) and load_col is None:
            load_col = col
    if ts_col is None:
        ts_col   = df.columns[0]
    if load_col is None:
        load_col = df.columns[1]

    log(f"  Timestamp column: '{ts_col}'  |  Load column: '{load_col}'")

    # ── 3. Parse timestamps ───────────────────────────────────────────────────
    log("\n[2] Parsing timestamps...")
    df[ts_col] = pd.to_datetime(df[ts_col], infer_datetime_format=True)

    # Standardize to IST (UTC+05:30)
    if df[ts_col].dt.tz is None:
        log("  Timestamps are timezone-naive. Localizing to Asia/Kolkata (IST).")
        df[ts_col] = df[ts_col].dt.tz_localize("Asia/Kolkata", ambiguous="infer", nonexistent="shift_forward")
    else:
        log(f"  Timestamps have tz: {df[ts_col].dt.tz}. Converting to IST.")
        df[ts_col] = df[ts_col].dt.tz_convert("Asia/Kolkata")

    df = df.sort_values(ts_col).reset_index(drop=True)
    log(f"  Date range: {df[ts_col].min()} → {df[ts_col].max()}")

    # Rename for consistency
    df = df.rename(columns={ts_col: "timestamp", load_col: "load_MW"})
    df["load_MW"] = pd.to_numeric(df["load_MW"], errors="coerce")

    # ── 4. Remove duplicates ──────────────────────────────────────────────────
    log("\n[3] Removing duplicate timestamps...")
    n_before = len(df)
    df = df.drop_duplicates(subset="timestamp", keep="first").reset_index(drop=True)
    n_dropped = n_before - len(df)
    log(f"  Dropped {n_dropped:,} duplicate rows. Remaining: {len(df):,}")

    # ── 5. Detect sampling interval ───────────────────────────────────────────
    log("\n[4] Detecting sampling interval...")
    intervals = df["timestamp"].diff().dropna()
    dominant  = intervals.mode().iloc[0]
    log(f"  Dominant interval: {dominant}")
    log(f"  Expected freq:     5 minutes")

    # ── 6. Build complete 5-min index → detect missing ────────────────────────
    log("\n[5] Checking for missing timestamps...")
    full_index = pd.date_range(
        start=df["timestamp"].min(),
        end=df["timestamp"].max(),
        freq="5min",
        tz="Asia/Kolkata"
    )
    df_full = pd.DataFrame({"timestamp": full_index})
    df_full = df_full.merge(df[["timestamp","load_MW"]], on="timestamp", how="left")

    n_missing = df_full["load_MW"].isna().sum()
    log(f"  Expected 5-min rows: {len(full_index):,}")
    log(f"  Missing rows:        {n_missing:,}  ({100*n_missing/len(full_index):.2f}%)")

    # Find consecutive missing blocks
    is_missing = df_full["load_MW"].isna()
    blocks = []
    in_gap = False
    gap_start_idx = None
    for i, val in enumerate(is_missing):
        if val and not in_gap:
            in_gap = True
            gap_start_idx = i
        elif not val and in_gap:
            blocks.append((
                df_full["timestamp"].iloc[gap_start_idx],
                df_full["timestamp"].iloc[i-1],
                i - gap_start_idx
            ))
            in_gap = False
    if in_gap:
        blocks.append((df_full["timestamp"].iloc[gap_start_idx], df_full["timestamp"].iloc[-1], len(df_full)-gap_start_idx))

    log(f"\n  Consecutive missing blocks: {len(blocks)}")
    if blocks:
        blocks_sorted = sorted(blocks, key=lambda x: -x[2])
        log("  Top 10 largest gaps:")
        for s, e, n in blocks_sorted[:10]:
            hrs = n * 5 / 60
            log(f"    {s}  →  {e}  ({n} readings = {hrs:.1f}h)")

    # ── 7. Interpolate short gaps, flag long ones ─────────────────────────────
    log("\n[6] Interpolating short gaps (≤ 2 hours = 24 readings)...")
    SHORT_GAP_THRESHOLD = 24   # 24 × 5min = 2 hours

    # Mark long-gap rows before interpolating
    df_full["long_gap_flag"] = False
    for s, e, n in blocks:
        if n > SHORT_GAP_THRESHOLD:
            mask = (df_full["timestamp"] >= s) & (df_full["timestamp"] <= e)
            df_full.loc[mask, "long_gap_flag"] = True

    # Interpolate all (then we'll set long-gap rows back to NaN)
    df_full["load_MW"] = df_full["load_MW"].interpolate(method="linear", limit_direction="both")
    df_full.loc[df_full["long_gap_flag"], "load_MW"] = np.nan

    n_still_nan = df_full["load_MW"].isna().sum()
    n_long_gap  = df_full["long_gap_flag"].sum()
    log(f"  Rows in long gaps (kept as NaN): {n_long_gap:,}")
    log(f"  Remaining NaN after short-gap interpolation: {n_still_nan:,}")

    # ── 8. Outlier detection (conservative — don't remove real peaks) ─────────
    log("\n[7] Outlier detection (IQR × 3 — conservative)...")
    q1   = df_full["load_MW"].quantile(0.25)
    q3   = df_full["load_MW"].quantile(0.75)
    iqr  = q3 - q1
    lower = q1 - 3 * iqr
    upper = q3 + 3 * iqr
    out_mask = df_full["load_MW"].notna() & (
        (df_full["load_MW"] < lower) | (df_full["load_MW"] > upper)
    )
    n_outliers = out_mask.sum()
    log(f"  IQR bounds (3×): [{lower:.1f}, {upper:.1f}]")
    log(f"  Outlier rows:    {n_outliers:,}  (flagged — NOT removed, operator decides)")
    df_full["outlier_flag"] = out_mask

    # ── 9. Save clean 5-min ───────────────────────────────────────────────────
    log("\n[8] Saving clean 5-min dataset...")
    settings.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df_clean = df_full[["timestamp","load_MW","long_gap_flag","outlier_flag"]].copy()
    df_clean.to_csv(CLEAN_5MIN_FILE, index=False)
    log(f"  Saved: {CLEAN_5MIN_FILE}  ({CLEAN_5MIN_FILE.stat().st_size/1024:.1f} KB)")

    # ── 10. Hourly aggregation ────────────────────────────────────────────────
    log("\n[9] Aggregating to hourly resolution...")
    # Floor timestamp to hour, then mean — only rows without long-gap flag
    df_valid = df_full[~df_full["long_gap_flag"]].copy()
    df_valid["hour_ts"] = df_valid["timestamp"].dt.floor("h")

    hourly = (
        df_valid.groupby("hour_ts")
        .agg(
            load_MW        = ("load_MW",        "mean"),
            reading_count  = ("load_MW",        "count"),
            outlier_in_hr  = ("outlier_flag",   "any"),
        )
        .reset_index()
        .rename(columns={"hour_ts": "timestamp"})
    )

    # Flag hours with < 9 of 12 readings (75% threshold)
    hourly["low_coverage"] = hourly["reading_count"] < 9

    n_hourly = len(hourly)
    n_low    = hourly["low_coverage"].sum()
    log(f"  Hourly rows:            {n_hourly:,}")
    log(f"  Hours with < 9 readings: {n_low:,}  (flagged)")
    log(f"  Load MW — hourly stats:")
    log(f"    Min:    {hourly['load_MW'].min():.1f}")
    log(f"    Max:    {hourly['load_MW'].max():.1f}")
    log(f"    Mean:   {hourly['load_MW'].mean():.1f}")
    log(f"    Median: {hourly['load_MW'].median():.1f}")

    hourly.to_csv(HOURLY_FILE, index=False)
    log(f"\n  Saved: {HOURLY_FILE}  ({HOURLY_FILE.stat().st_size/1024:.1f} KB)")

    # ── 11. Final summary ─────────────────────────────────────────────────────
    log("\n" + "=" * 65)
    log("  PREPROCESSING COMPLETE")
    log("=" * 65)
    log(f"  Raw 5-min rows:    {len(df):,}")
    log(f"  Clean 5-min rows:  {len(df_clean):,}")
    log(f"  Hourly rows:       {n_hourly:,}")
    log(f"  Date range:        {hourly['timestamp'].min()} → {hourly['timestamp'].max()}")
    log(f"  Timezone:          Asia/Kolkata (IST, UTC+05:30)")
    log(f"  Aggregation:       Mean of 5-min readings per hour")
    log(f"  Long gaps (NaN):   {n_long_gap:,} 5-min rows (> 2h consecutive)")
    log(f"  Outliers flagged:  {n_outliers:,} (kept — review manually)")
    log("\n  NEXT STEP: python scripts/fetch_historical_weather.py")
    log("  THEN:      python scripts/build_features.py")
    log("=" * 65)

    # Write report to file
    REPORT_FILE.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"\nReport saved → {REPORT_FILE}")

    return hourly


if __name__ == "__main__":
    run()
