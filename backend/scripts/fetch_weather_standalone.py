"""Standalone weather fetcher -- no app imports needed."""
import argparse, sys, time, os
from pathlib import Path
import requests
import pandas as pd

DELHI_LAT = 28.65
DELHI_LON = 77.27
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
OUTPUT_DIR  = Path(__file__).parent.parent / "data" / "weather"
OUTPUT_FILE = OUTPUT_DIR / "delhi_weather_historical.csv"


def fetch_chunk(start: str, end: str, retries=3) -> dict:
    params = {"latitude": DELHI_LAT, "longitude": DELHI_LON,
              "start_date": start, "end_date": end,
              "hourly": "temperature_2m,relative_humidity_2m",
              "timezone": "Asia/Kolkata"}
    for attempt in range(retries):
        try:
            r = requests.get(ARCHIVE_URL, params=params, timeout=60)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            if attempt < retries - 1:
                print(f"  Retry {attempt+1}: {e}")
                time.sleep(5)
            else:
                raise


def parse_chunk(data: dict) -> pd.DataFrame:
    h = data["hourly"]
    df = pd.DataFrame({
        "timestamp":    pd.to_datetime(h["time"]),
        "temperature_c": h.get("temperature_2m"),
        "humidity_pct":  h.get("relative_humidity_2m"),
    })
    df["timestamp"] = df["timestamp"].dt.tz_localize("Asia/Kolkata", ambiguous="infer", nonexistent="shift_forward")
    return df


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="2023-04-01")
    parser.add_argument("--end",   default="2026-01-31")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if OUTPUT_FILE.exists() and not args.force:
        print(f"Cached: {OUTPUT_FILE}")
        df = pd.read_csv(OUTPUT_FILE)
        print(f"  Rows: {len(df):,}  |  {df['timestamp'].iloc[0]} -> {df['timestamp'].iloc[-1]}")
        return

    print(f"Fetching Open-Meteo Archive: {args.start} to {args.end}")
    start = pd.Timestamp(args.start)
    end   = pd.Timestamp(args.end)
    chunks = []
    cursor = start
    while cursor <= end:
        chunk_end = min(cursor + pd.Timedelta(days=364), end)
        s, e = cursor.strftime("%Y-%m-%d"), chunk_end.strftime("%Y-%m-%d")
        print(f"  {s} -> {e} ...", end=" ", flush=True)
        data = fetch_chunk(s, e)
        df   = parse_chunk(data)
        n    = len(df)
        nan  = df["temperature_c"].isna().sum()
        print(f"{n} rows, {nan} NaN")
        chunks.append(df)
        cursor = chunk_end + pd.Timedelta(days=1)
        time.sleep(1)

    result = pd.concat(chunks).drop_duplicates("timestamp").sort_values("timestamp").reset_index(drop=True)
    print(f"\nTotal: {len(result):,} rows")
    print(f"Range: {result['timestamp'].iloc[0]} -> {result['timestamp'].iloc[-1]}")
    print(f"Temp:  {result['temperature_c'].min():.1f} degC -> {result['temperature_c'].max():.1f} degC")

    result.to_csv(OUTPUT_FILE, index=False)
    print(f"Saved -> {OUTPUT_FILE}  ({OUTPUT_FILE.stat().st_size/1024:.1f} KB)")


if __name__ == "__main__":
    main()
