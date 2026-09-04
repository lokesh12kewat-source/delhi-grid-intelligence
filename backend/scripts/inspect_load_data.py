"""
scripts/inspect_load_data.py
-----------------------------
Comprehensive inspection of load_data.csv.
Run this FIRST before any preprocessing.

Usage:
    python scripts/inspect_load_data.py

Reports:
  - exact row count, date range, sampling interval
  - duplicate timestamps
  - missing timestamps
  - missing load_MW values
  - consecutive missing-data gaps
  - min / max / mean / median load
  - suspicious values / outliers
  - timezone / format
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))
from app.core.config import settings

RAW_FILE = settings.RAW_DATA_DIR / "load_data.csv"


def inspect():
    if not RAW_FILE.exists():
        print(f"ERROR: {RAW_FILE} not found.")
        print("Please drop load_data.csv into backend/data/raw/")
        sys.exit(1)

    file_size_mb = RAW_FILE.stat().st_size / 1024 / 1024
    print(f"\n{'='*65}")
    print(f"  LOAD DATA INSPECTION REPORT")
    print(f"  File: {RAW_FILE.name}  ({file_size_mb:.1f} MB)")
    print(f"{'='*65}\n")

    # ── Step 1: Peek at raw file ───────────────────────────────────────────────
    print("[1/9] Raw file preview (first 5 lines):")
    with open(RAW_FILE, encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f):
            print(f"  {line.rstrip()}")
            if i >= 4:
                break
    print()

    # ── Step 2: Load the file ─────────────────────────────────────────────────
    print("[2/9] Loading CSV...")
    try:
        df = pd.read_csv(RAW_FILE)
    except Exception as e:
        print(f"  ERROR reading CSV: {e}")
        sys.exit(1)

    print(f"  Columns detected: {list(df.columns)}")
    print(f"  Total rows:       {len(df):,}")
    print(f"  Total columns:    {len(df.columns)}")
    print()

    # ── Step 3: Identify timestamp and load columns ────────────────────────────
    print("[3/9] Identifying timestamp and load columns...")
    ts_col   = None
    load_col = None

    for col in df.columns:
        cl = col.lower().strip()
        if any(k in cl for k in ["time", "date", "timestamp"]):
            ts_col = col
        if any(k in cl for k in ["load", "mw", "demand", "power", "kwh"]):
            load_col = col

    if ts_col is None:
        print(f"  WARNING: No obvious timestamp column found.")
        print(f"  Columns: {list(df.columns)}")
        ts_col = df.columns[0]
        print(f"  Assuming first column is timestamp: '{ts_col}'")

    if load_col is None:
        print(f"  WARNING: No obvious load column found.")
        load_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]
        print(f"  Assuming second column is load: '{load_col}'")

    print(f"  Timestamp column: '{ts_col}'")
    print(f"  Load column:      '{load_col}'")
    print()

    # ── Step 4: Parse timestamps ───────────────────────────────────────────────
    print("[4/9] Parsing timestamps...")
    try:
        df[ts_col] = pd.to_datetime(df[ts_col], infer_datetime_format=True)
    except Exception as e:
        print(f"  ERROR parsing timestamps: {e}")
        print(f"  Sample values: {df[ts_col].head().tolist()}")
        sys.exit(1)

    df = df.sort_values(ts_col).reset_index(drop=True)

    print(f"  First timestamp:  {df[ts_col].iloc[0]}")
    print(f"  Last timestamp:   {df[ts_col].iloc[-1]}")
    total_days = (df[ts_col].iloc[-1] - df[ts_col].iloc[0]).days
    print(f"  Total span:       {total_days} days ({total_days/365.25:.2f} years)")

    tz_info = df[ts_col].dt.tz
    print(f"  Timezone info:    {tz_info if tz_info else 'None (naive — assuming IST)'}")
    print()

    # ── Step 5: Sampling interval ─────────────────────────────────────────────
    print("[5/9] Sampling interval analysis...")
    intervals = df[ts_col].diff().dropna()
    interval_counts = intervals.value_counts().head(5)
    print("  Interval frequency (top 5):")
    for interval, count in interval_counts.items():
        pct = 100 * count / len(intervals)
        print(f"    {str(interval):25s}  {count:>10,} ({pct:.1f}%)")
    dominant_interval = interval_counts.index[0]
    print(f"  Dominant interval: {dominant_interval}")
    print()

    # ── Step 6: Duplicate timestamps ──────────────────────────────────────────
    print("[6/9] Duplicate timestamp check...")
    dupes = df[df.duplicated(subset=ts_col, keep=False)]
    print(f"  Duplicate timestamps: {df.duplicated(subset=ts_col).sum():,} rows")
    if len(dupes) > 0:
        print(f"  Sample duplicates:")
        print(dupes.head(4).to_string(index=False))
    print()

    # ── Step 7: Missing timestamp gaps ────────────────────────────────────────
    print("[7/9] Missing timestamp gaps...")
    expected_range = pd.date_range(
        start=df[ts_col].min(),
        end=df[ts_col].max(),
        freq=dominant_interval
    )
    actual_set   = set(df[ts_col])
    missing_ts   = [t for t in expected_range if t not in actual_set]
    print(f"  Expected timestamps: {len(expected_range):,}")
    print(f"  Actual timestamps:   {len(df):,}")
    print(f"  Missing timestamps:  {len(missing_ts):,}")

    if missing_ts:
        # Find consecutive gaps
        missing_s = pd.Series(missing_ts)
        gap_groups = []
        gap_start = missing_s.iloc[0]
        prev = missing_s.iloc[0]
        for ts in missing_s.iloc[1:]:
            if (ts - prev) > dominant_interval * 1.5:
                gap_groups.append((gap_start, prev))
                gap_start = ts
            prev = ts
        gap_groups.append((gap_start, prev))

        print(f"  Consecutive gap blocks: {len(gap_groups)}")
        print("  Top 5 longest gaps:")
        gap_lengths = [(g[0], g[1], g[1]-g[0]) for g in gap_groups]
        gap_lengths.sort(key=lambda x: x[2], reverse=True)
        for s, e, dur in gap_lengths[:5]:
            print(f"    {s}  →  {e}  ({dur})")
    print()

    # ── Step 8: Load value analysis ───────────────────────────────────────────
    print("[8/9] Load value analysis...")
    try:
        df[load_col] = pd.to_numeric(df[load_col], errors="coerce")
    except Exception:
        pass

    load = df[load_col]
    null_count = load.isna().sum()
    zero_count = (load == 0).sum()
    neg_count  = (load < 0).sum()

    print(f"  NaN / missing:   {null_count:,}")
    print(f"  Zero values:     {zero_count:,}")
    print(f"  Negative values: {neg_count:,}")
    print(f"  Minimum:         {load.min():.2f}")
    print(f"  Maximum:         {load.max():.2f}")
    print(f"  Mean:            {load.mean():.2f}")
    print(f"  Median:          {load.median():.2f}")
    print(f"  Std dev:         {load.std():.2f}")

    # Outlier detection (IQR method, 3x)
    q1, q3 = load.quantile(0.25), load.quantile(0.75)
    iqr = q3 - q1
    lower_bound = q1 - 3 * iqr
    upper_bound = q3 + 3 * iqr
    outliers = df[(load < lower_bound) | (load > upper_bound)]
    print(f"\n  IQR outlier bounds (3×): [{lower_bound:.1f}, {upper_bound:.1f}]")
    print(f"  Outlier rows:    {len(outliers):,}")
    if len(outliers) > 0:
        print(f"  Outlier samples:")
        print(outliers[[ts_col, load_col]].head(5).to_string(index=False))

    # Percentile distribution
    pcts = [1, 5, 10, 25, 50, 75, 90, 95, 99]
    print(f"\n  Percentile distribution:")
    for p in pcts:
        print(f"    P{p:3d}: {load.quantile(p/100):>8.2f}")
    print()

    # ── Step 9: Summary + recommendations ────────────────────────────────────
    print("[9/9] Summary and recommendations:")
    print(f"  Load unit (inferred):  {'MW' if load.mean() > 100 else 'kW (small scale — verify)'}")
    print(f"  Resolution:            {dominant_interval}")
    print(f"  Date range:            {df[ts_col].min().date()} → {df[ts_col].max().date()}")
    print(f"  Duration:              {total_days} days")
    print(f"  Data completeness:     {100*(1 - null_count/len(df)):.2f}%")
    print()
    print("  Recommended preprocessing steps:")
    print("  1. Parse timestamps → set IST timezone if naive")
    print("  2. Sort chronologically")
    if df.duplicated(subset=ts_col).sum() > 0:
        print("  3. Remove duplicate timestamps (keep first)")
    print("  4. Build complete 5-min date_range → find all missing slots")
    print("  5. Interpolate short gaps (≤ 1 hour), flag long gaps")
    print("  6. Aggregate to hourly (mean of 12 readings per hour)")
    print("  7. Merge with historical weather on timestamp")
    print()
    print("  NEXT STEP: python scripts/preprocess_load.py")
    print("=" * 65)

    return df, ts_col, load_col


if __name__ == "__main__":
    inspect()
