"""
app/services/weather_service.py
--------------------------------
Single point of contact for ALL weather data needs.

Responsibilities:
  - Current weather for Delhi (6 zones)
  - 24h/7d weather forecast
  - Historical weather (used only during training data fetch)
  - Normalization across all 6 zone CSVs
  - In-memory caching (TTL-based)
  - Error handling + fallback

ML code must NOT call Open-Meteo directly. Import from here.
"""

import time
import logging
from pathlib import Path
from typing import Optional
import requests
import pandas as pd
import numpy as np

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Zone file mapping ─────────────────────────────────────────────────────────
# Maps zone IDs to the CSV files dropped by the team
ZONE_CSV_FILES = {
    "delhi_north":     settings.BASE_DIR.parent / "HackerEarth" / "TEMPERATURE NORTHDELHI 3 MONTHS.csv",
    "delhi_south":     settings.BASE_DIR.parent / "HackerEarth" / "TEMPERATURE SOUTHDELHI 3 MONTHS.csv",
    "delhi_east":      settings.BASE_DIR.parent / "HackerEarth" / "TEMPERATURE EASTDELHI 3 MONTHS.csv",
    "delhi_west":      settings.BASE_DIR.parent / "HackerEarth" / "TEMPERATURE WESTDELHI 3 MONTHS.csv",
    "delhi_central":   settings.BASE_DIR.parent / "HackerEarth" / "TEMPERATURE CENTRALDELHI 3MONTHS.csv",
    "delhi_northeast": settings.BASE_DIR.parent / "HackerEarth" / "TEMPERATURE NEASTDELHI 3 MONTHS.csv",
}

ZONE_DISPLAY = {
    "delhi_north":     "North Delhi (TPDDL)",
    "delhi_south":     "South Delhi (BRPL)",
    "delhi_east":      "East Delhi (BYPL)",
    "delhi_west":      "West Delhi (BRPL)",
    "delhi_central":   "Central Delhi (NDMC)",
    "delhi_northeast": "North-East Delhi (TPDDL)",
}

# ── Simple TTL cache ──────────────────────────────────────────────────────────
_cache: dict = {}
CACHE_TTL_SECONDS = 300   # 5 minutes


def _cache_get(key: str):
    entry = _cache.get(key)
    if entry and (time.time() - entry["ts"]) < CACHE_TTL_SECONDS:
        return entry["value"]
    return None


def _cache_set(key: str, value):
    _cache[key] = {"ts": time.time(), "value": value}


# ── Parse zone CSV ────────────────────────────────────────────────────────────
def _parse_zone_csv(zone_id: str) -> Optional[pd.DataFrame]:
    """
    Parse one zone's CSV from the Open-Meteo export format.
    File structure:
      Line 1: lat,lon,elevation,utc_offset_seconds,timezone,timezone_abbreviation
      Line 2: <values>
      Line 3: (blank)
      Line 4: header row (time,temperature_2m (°C)[,relative_humidity_2m (%)])
      Line 5+: data rows
    """
    csv_path = ZONE_CSV_FILES.get(zone_id)
    if not csv_path or not Path(csv_path).exists():
        logger.warning(f"Zone CSV not found for {zone_id}: {csv_path}")
        return None

    try:
        df = pd.read_csv(csv_path, skiprows=3)
        df = df.rename(columns={
            "time": "timestamp",
            "temperature_2m (°C)": "temperature_c",
            "temperature_2m (Â°C)": "temperature_c",   # encoding variant
        })

        # Handle humidity if present
        for hcol in ["relative_humidity_2m (%)", "relative_humidity_2m (Â%)"]:
            if hcol in df.columns:
                df = df.rename(columns={hcol: "humidity_pct"})
                break

        df["timestamp"] = pd.to_datetime(df["timestamp"])

        # Drop NaN rows (the future-forecast padding at the top)
        df = df.dropna(subset=["temperature_c"]).reset_index(drop=True)

        # Localize to IST
        if df["timestamp"].dt.tz is None:
            df["timestamp"] = df["timestamp"].dt.tz_localize("Asia/Kolkata")

        df["zone_id"]   = zone_id
        df["zone_name"] = ZONE_DISPLAY.get(zone_id, zone_id)

        return df

    except Exception as e:
        logger.error(f"Error parsing zone CSV {zone_id}: {e}")
        return None


def _load_all_zones() -> pd.DataFrame:
    """Load and combine all 6 zone CSVs into a unified wide DataFrame."""
    frames = []
    for zone_id in ZONE_CSV_FILES:
        df = _parse_zone_csv(zone_id)
        if df is not None:
            frames.append(df)

    if not frames:
        logger.error("No zone weather CSVs could be loaded!")
        return pd.DataFrame()

    # Combine long → pivot to wide
    long_df = pd.concat(frames, ignore_index=True)

    # Create unified timestamp-indexed wide table
    zone_ids = long_df["zone_id"].unique()
    wide_frames = []

    for zone_id in zone_ids:
        z = long_df[long_df["zone_id"] == zone_id][["timestamp","temperature_c"]].copy()
        z = z.rename(columns={"temperature_c": f"{zone_id}_temp"})
        wide_frames.append(z.set_index("timestamp"))

        if "humidity_pct" in long_df.columns:
            zh = long_df[long_df["zone_id"] == zone_id][["timestamp","humidity_pct"]].copy()
            if not zh["humidity_pct"].isna().all():
                zh = zh.rename(columns={"humidity_pct": f"{zone_id}_humidity"})
                wide_frames.append(zh.set_index("timestamp"))

    wide = pd.concat(wide_frames, axis=1).reset_index()
    wide = wide.sort_values("timestamp").reset_index(drop=True)
    return wide


# ── Spatial aggregation ───────────────────────────────────────────────────────
def _compute_delhi_aggregates(wide: pd.DataFrame) -> pd.DataFrame:
    """
    From wide zone data, compute:
      delhi_avg_temp, delhi_max_temp, delhi_min_temp,
      delhi_temp_spread, delhi_avg_humidity
    """
    temp_cols = [c for c in wide.columns if c.endswith("_temp")]
    hum_cols  = [c for c in wide.columns if c.endswith("_humidity")]

    if temp_cols:
        wide["delhi_avg_temp"]    = wide[temp_cols].mean(axis=1)
        wide["delhi_max_temp"]    = wide[temp_cols].max(axis=1)
        wide["delhi_min_temp"]    = wide[temp_cols].min(axis=1)
        wide["delhi_temp_spread"] = wide["delhi_max_temp"] - wide["delhi_min_temp"]

    if hum_cols:
        wide["delhi_avg_humidity"] = wide[hum_cols].mean(axis=1)

    return wide


# ── Public API ────────────────────────────────────────────────────────────────
def get_current_weather() -> dict:
    """
    Returns current weather snapshot for all 6 Delhi zones.
    Uses cached zone CSV data (refreshed every 5 min from disk).
    Falls back to Open-Meteo API if CSV is stale.
    """
    cached = _cache_get("current_weather")
    if cached:
        return cached

    wide = _load_all_zones()
    if wide.empty:
        logger.warning("Zone CSV data unavailable — falling back to Open-Meteo API")
        return _fetch_current_from_api()

    wide = _compute_delhi_aggregates(wide)

    # Get most recent row
    latest = wide.iloc[-1]
    zones = []
    for zone_id in ZONE_CSV_FILES:
        temp_col = f"{zone_id}_temp"
        hum_col  = f"{zone_id}_humidity"
        zones.append({
            "zone_id":      zone_id,
            "zone_name":    ZONE_DISPLAY.get(zone_id, zone_id),
            "temperature_c": round(float(latest.get(temp_col, float("nan"))), 1)
                             if not pd.isna(latest.get(temp_col, float("nan"))) else None,
            "humidity_pct":  round(float(latest.get(hum_col, float("nan"))), 0)
                             if hum_col in latest.index and not pd.isna(latest.get(hum_col, float("nan"))) else None,
            "has_humidity":  settings.ZONE_COORDS[zone_id]["has_humidity"],
        })

    result = {
        "timestamp":         latest["timestamp"].isoformat() if hasattr(latest["timestamp"], "isoformat") else str(latest["timestamp"]),
        "delhi_avg_temp":    round(float(latest.get("delhi_avg_temp", float("nan"))), 1) if "delhi_avg_temp" in latest.index else None,
        "delhi_max_temp":    round(float(latest.get("delhi_max_temp", float("nan"))), 1) if "delhi_max_temp" in latest.index else None,
        "delhi_min_temp":    round(float(latest.get("delhi_min_temp", float("nan"))), 1) if "delhi_min_temp" in latest.index else None,
        "delhi_temp_spread": round(float(latest.get("delhi_temp_spread", float("nan"))), 1) if "delhi_temp_spread" in latest.index else None,
        "delhi_avg_humidity":round(float(latest.get("delhi_avg_humidity", float("nan"))), 0) if "delhi_avg_humidity" in latest.index else None,
        "zones":             zones,
        "source":            "csv_cache",
        "data_note":         "Zone weather data from Open-Meteo API export (6 Delhi locations)",
    }

    _cache_set("current_weather", result)
    return result


def get_forecast_weather(hours: int = 24) -> list[dict]:
    """
    Returns next N hours of Delhi weather forecast from Open-Meteo.
    Used during inference to compute weather features for future hours.
    """
    cached = _cache_get(f"forecast_{hours}h")
    if cached:
        return cached

    params = {
        "latitude":  28.65,
        "longitude": 77.27,
        "hourly":    "temperature_2m,relative_humidity_2m",
        "timezone":  "Asia/Kolkata",
        "forecast_days": max(1, (hours // 24) + 1),
    }

    try:
        resp = requests.get(settings.OPEN_METEO_FORECAST_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        hourly = data.get("hourly", {})
        times  = hourly.get("time", [])
        temps  = hourly.get("temperature_2m", [None]*len(times))
        hums   = hourly.get("relative_humidity_2m", [None]*len(times))

        now = pd.Timestamp.now(tz="Asia/Kolkata")
        result = []
        for t, temp, hum in zip(times, temps, hums):
            ts = pd.Timestamp(t).tz_localize("Asia/Kolkata")
            if ts >= now:
                result.append({
                    "timestamp":    ts.isoformat(),
                    "temperature_c": round(temp, 1) if temp is not None else None,
                    "humidity_pct":  round(hum, 0)  if hum  is not None else None,
                    "cooling_degree_hrs": round(max(0, temp - 24), 2) if temp is not None else None,
                })
                if len(result) >= hours:
                    break

        _cache_set(f"forecast_{hours}h", result)
        return result

    except Exception as e:
        logger.error(f"Open-Meteo forecast API error: {e}")
        return []


def get_zone_weather_panel() -> list[dict]:
    """
    Returns all 6 zone weather readings for the dashboard weather panel.
    This is separate from the forecast — it shows zone spatial variation.
    """
    cached = _cache_get("zone_panel")
    if cached:
        return cached

    result = []
    for zone_id in ZONE_CSV_FILES:
        df = _parse_zone_csv(zone_id)
        if df is not None and len(df) > 0:
            latest = df.iloc[-1]
            entry = {
                "zone_id":      zone_id,
                "zone_name":    ZONE_DISPLAY.get(zone_id, zone_id),
                "timestamp":    latest["timestamp"].isoformat(),
                "temperature_c": round(float(latest["temperature_c"]), 1) if not pd.isna(latest["temperature_c"]) else None,
                "humidity_pct":  round(float(latest["humidity_pct"]), 0)
                                 if "humidity_pct" in latest.index and not pd.isna(latest.get("humidity_pct", float("nan")))
                                 else None,
            }
            result.append(entry)

    _cache_set("zone_panel", result)
    return result


def _fetch_current_from_api() -> dict:
    """Fallback: fetch current conditions from Open-Meteo API."""
    params = {
        "latitude":  28.65,
        "longitude": 77.27,
        "current":   "temperature_2m,relative_humidity_2m",
        "timezone":  "Asia/Kolkata",
    }
    try:
        resp = requests.get(settings.OPEN_METEO_FORECAST_URL, params=params, timeout=10)
        resp.raise_for_status()
        data   = resp.json()
        cur    = data.get("current", {})
        temp   = cur.get("temperature_2m")
        hum    = cur.get("relative_humidity_2m")
        return {
            "timestamp":          cur.get("time"),
            "delhi_avg_temp":     round(temp, 1) if temp else None,
            "delhi_max_temp":     None,
            "delhi_min_temp":     None,
            "delhi_temp_spread":  None,
            "delhi_avg_humidity": round(hum, 0) if hum else None,
            "zones":              [],
            "source":             "open_meteo_api",
            "data_note":          "Live Open-Meteo API (zone CSVs unavailable)",
        }
    except Exception as e:
        logger.error(f"Open-Meteo current API fallback failed: {e}")
        return {"error": "Weather data unavailable", "source": "none"}
