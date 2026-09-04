"""
scripts/fetch_historical_weather.py
------------------------------------
ONE-TIME script to fetch Delhi historical weather from Open-Meteo Archive API.
Run this ONCE before training. Output is cached to data/weather/delhi_weather_historical.csv

Usage:
    python scripts/fetch_historical_weather.py --start 2023-04-01 --end 2026-01-31

The script fetches hourly temperature_2m and relative_humidity_2m for central Delhi
(28.65°N, 77.27°E) over the specified period, aligns to Asia/Kolkata timezone,
and saves locally so training never calls the API again.
"""

import argparse
import sys
import time
from pathlib import Path
import requests
import pandas as pd

# Add backend root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.core.config import settings


# ── Constants ─────────────────────────────────────────────────────────────────
DELHI_LAT = 28.65
DELHI_LON = 77.27
OUTPUT_FILE = settings.WEATHER_DIR / "delhi_weather_historical.csv"

# Open-Meteo Archive API allows up to 1 year per call; we chunk by year
MAX_DAYS_PER_CALL = 365


def fetch_chunk(start_date: str, end_date: str, retries: int = 3) -> dict:
    """Fetch one chunk from Open-Meteo Archive API with retry logic."""
    params = {
        "latitude":  DELHI_LAT,
        "longitude": DELHI_LON,
        "start_date": start_date,
        "end_date":   end_date,
        "hourly":     "temperature_2m,relative_humidity_2m",
        "timezone":   "Asia/Kolkata",
    }

    for attempt in range(retries):
        try:
            resp = requests.get(settings.OPEN_METEO_ARCHIVE_URL, params=params, timeout=60)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            if attempt < retries - 1:
                print(f"  Attempt {attempt+1} failed: {e}. Retrying in 5s...")
                time.sleep(5)
            else:
                raise RuntimeError(f"Failed after {retries} attempts: {e}")


def parse_chunk(data: dict) -> pd.DataFrame:
    """Parse a single Open-Meteo Archive API response into a DataFrame."""
    hourly = data.get("hourly", {})
    if not hourly or "time" not in hourly:
        raise ValueError("Unexpected API response format")

    df = pd.DataFrame({
        "timestamp":    pd.to_datetime(hourly["time"]),
        "temperature_c": hourly.get("temperature_2m", [None] * len(hourly["time"])),
        "humidity_pct":  hourly.get("relative_humidity_2m", [None] * len(hourly["time"])),
    })

    # Localize to IST — Open-Meteo returns local time when timezone is specified
    df["timestamp"] = df["timestamp"].dt.tz_localize("Asia/Kolkata", ambiguous="infer", nonexistent="shift_forward")
    return df


def fetch_historical(start_date: str, end_date: str) -> pd.DataFrame:
    """Fetch full historical period, chunking into annual requests."""
    start = pd.Timestamp(start_date)
    end   = pd.Timestamp(end_date)

    chunks = []
    cursor = start

    while cursor <= end:
        chunk_end = min(cursor + pd.Timedelta(days=364), end)
        s_str = cursor.strftime("%Y-%m-%d")
        e_str = chunk_end.strftime("%Y-%m-%d")

        print(f"  Fetching {s_str} → {e_str} ...", end=" ", flush=True)
        data   = fetch_chunk(s_str, e_str)
        df     = parse_chunk(data)
        n_rows = len(df)
        n_nan  = df["temperature_c"].isna().sum()
        print(f"{n_rows} rows, {n_nan} NaN temp")

        chunks.append(df)
        cursor = chunk_end + pd.Timedelta(days=1)
        time.sleep(1)   # be polite to the API

    combined = pd.concat(chunks, ignore_index=True)
    combined = combined.drop_duplicates(subset="timestamp").sort_values("timestamp").reset_index(drop=True)
    return combined


def validate_and_report(df: pd.DataFrame) -> None:
    """Print a quality report on the fetched weather data."""
    print("\n" + "=" * 60)
    print("DELHI HISTORICAL WEATHER — QUALITY REPORT")
    print("=" * 60)
    print(f"  Rows:              {len(df):,}")
    print(f"  Date range:        {df['timestamp'].min()} → {df['timestamp'].max()}")
    print(f"  Temperature NaN:   {df['temperature_c'].isna().sum()}")
    print(f"  Humidity NaN:      {df['humidity_pct'].isna().sum()}")
    print(f"  Temp range:        {df['temperature_c'].min():.1f}°C → {df['temperature_c'].max():.1f}°C")
    print(f"  Humidity range:    {df['humidity_pct'].min():.0f}% → {df['humidity_pct'].max():.0f}%")

    # Check for hourly continuity
    ts_sorted = df["timestamp"].sort_values()
    gaps = ts_sorted.diff().dropna()
    expected_interval = pd.Timedelta("1h")
    bad_gaps = gaps[gaps != expected_interval]
    print(f"  Hourly gaps:       {len(bad_gaps)}")
    if len(bad_gaps) > 0:
        print(f"  Largest gap:       {bad_gaps.max()}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Fetch Delhi historical weather")
    parser.add_argument("--start", default="2023-04-01", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end",   default="2026-01-31", help="End date (YYYY-MM-DD)")
    parser.add_argument("--force", action="store_true",  help="Re-fetch even if cached file exists")
    args = parser.parse_args()

    settings.WEATHER_DIR.mkdir(parents=True, exist_ok=True)

    if OUTPUT_FILE.exists() and not args.force:
        print(f"Cached weather file found: {OUTPUT_FILE}")
        print("Use --force to re-fetch. Loading cached data...")
        df = pd.read_csv(OUTPUT_FILE, parse_dates=["timestamp"])
        validate_and_report(df)
        return

    print(f"Fetching Open-Meteo Archive weather for Delhi ({DELHI_LAT}°N, {DELHI_LON}°E)")
    print(f"Period: {args.start} → {args.end}  |  Timezone: Asia/Kolkata")
    print(f"Variables: temperature_2m, relative_humidity_2m")
    print("-" * 60)

    df = fetch_historical(args.start, args.end)
    validate_and_report(df)

    # Save with tz-aware timestamp (ISO format)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\nSaved → {OUTPUT_FILE}  ({OUTPUT_FILE.stat().st_size / 1024:.1f} KB)")
    print("Done. This file is now the cached weather source for model training.")


if __name__ == "__main__":
    main()
