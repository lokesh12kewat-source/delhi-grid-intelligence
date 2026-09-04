"""
app/services/forecast_service.py
----------------------------------
Loads the trained model and runs 24-hour demand forecasts.

Inference pipeline:
  1. Load recent hourly load history from processed CSV
  2. Fetch weather forecast from weather_service
  3. Build feature vector for each future hour (no future leakage)
  4. Predict with saved model
  5. Return timestamped forecast + risk levels
"""

import json
import logging
from pathlib import Path
from typing import Optional
import numpy as np
import pandas as pd
import joblib

from app.core.config import settings
from app.services.weather_service import get_forecast_weather
from app.services.risk_engine import classify_risk

logger = logging.getLogger(__name__)

MODEL_FILE     = settings.MODELS_DIR / "forecast_model.pkl"
FEAT_LIST_FILE = settings.MODELS_DIR / "feature_list.json"
HOURLY_FILE    = settings.PROCESSED_DIR / "load_hourly.csv"

DELHI_HOLIDAYS = [
    "2025-08-15","2025-10-02","2025-10-20","2025-12-25",
    "2026-01-26","2026-03-18","2026-04-14","2026-08-15",
]

# ── Module-level cache for model ──────────────────────────────────────────────
_model       = None
_feature_list: list = []
_meta: dict  = {}


def _load_model():
    global _model, _feature_list, _meta
    if _model is not None:
        return

    if not MODEL_FILE.exists():
        logger.error(f"Model file not found: {MODEL_FILE}")
        return

    _model = joblib.load(MODEL_FILE)
    if FEAT_LIST_FILE.exists():
        _meta = json.loads(FEAT_LIST_FILE.read_text(encoding="utf-8"))
        _feature_list = _meta.get("features", [])
    logger.info(f"Model loaded: {_meta.get('model_name','unknown')}  |  features: {len(_feature_list)}")


def _load_history(hours: int = 200) -> Optional[pd.DataFrame]:
    """Load the most recent N hours of actual load data."""
    if not HOURLY_FILE.exists():
        return None
    df = pd.read_csv(HOURLY_FILE, parse_dates=["timestamp"])
    if "long_gap_flag" in df.columns:
        df = df[~df["long_gap_flag"]]
    df = df.dropna(subset=["load_MW"]).sort_values("timestamp").tail(hours).reset_index(drop=True)
    if df["timestamp"].dt.tz is None:
        df["timestamp"] = df["timestamp"].dt.tz_localize("Asia/Kolkata")
    return df


def _cyclical(value: float, period: float) -> tuple[float, float]:
    return np.sin(2 * np.pi * value / period), np.cos(2 * np.pi * value / period)


def _build_inference_row(
    forecast_ts: pd.Timestamp,
    history: pd.DataFrame,
    temp_c: Optional[float],
    humidity: Optional[float],
) -> dict:
    """Build one feature row for a future timestamp — only backward-looking features."""
    h = forecast_ts.hour
    dow = forecast_ts.dayofweek
    month = forecast_ts.month

    hour_sin, hour_cos = _cyclical(h, 24)
    dow_sin,  dow_cos  = _cyclical(dow, 7)
    month_sin, month_cos = _cyclical(month, 12)
    is_weekend = int(dow >= 5)
    holiday_dates = pd.to_datetime(DELHI_HOLIDAYS).normalize()
    is_holiday = int(forecast_ts.normalize() in
                     holiday_dates.tz_localize("Asia/Kolkata"))

    # Lag features — look into history for past actual readings
    def get_lag(hrs: int) -> float:
        target_ts = forecast_ts - pd.Timedelta(hours=hrs)
        row = history[history["timestamp"] == target_ts]
        if len(row) > 0:
            return float(row.iloc[0]["load_MW"])
        # Nearest fallback
        diff = (history["timestamp"] - target_ts).abs()
        if diff.min() <= pd.Timedelta(hours=2):
            return float(history.loc[diff.idxmin(), "load_MW"])
        return float("nan")

    lag_1h   = get_lag(1)
    lag_24h  = get_lag(24)
    lag_168h = get_lag(168)

    # Rolling from history (last N actual observations)
    recent = history["load_MW"].dropna().tail(24).values
    roll_mean_3h  = float(recent[-3:].mean()) if len(recent) >= 3  else float("nan")
    roll_mean_24h = float(recent.mean())        if len(recent) >= 1  else float("nan")
    roll_std_24h  = float(recent.std())         if len(recent) >= 2  else 0.0

    # Weather features
    cooling = max(0, temp_c - 24) if temp_c is not None else float("nan")
    temp_lag_24h = float("nan")
    row_minus24 = history[history["timestamp"] == forecast_ts - pd.Timedelta(hours=24)]
    # temp_lag_24h would be yesterday's temperature — use from forecast if available
    # For now set to current temp as approximation (same-day lag)
    temp_lag_24h = temp_c if temp_c is not None else float("nan")

    return {
        "hour_sin": hour_sin, "hour_cos": hour_cos,
        "dow_sin":  dow_sin,  "dow_cos":  dow_cos,
        "month_sin": month_sin, "month_cos": month_cos,
        "month": month,
        "is_weekend": is_weekend, "is_holiday": is_holiday,
        "lag_1h": lag_1h, "lag_24h": lag_24h, "lag_168h": lag_168h,
        "roll_mean_3h": roll_mean_3h, "roll_mean_24h": roll_mean_24h,
        "roll_std_24h": roll_std_24h,
        "temperature_c": temp_c if temp_c is not None else float("nan"),
        "humidity_pct":  humidity if humidity is not None else float("nan"),
        "cooling_degree_hrs": cooling,
        "temp_lag_24h": temp_lag_24h,
    }


def run_forecast(hours: int = 24) -> dict:
    """
    Generate next N-hour demand forecast.

    Returns:
        {
          "forecast": [{timestamp, predicted_demand_mw, risk_level, ...}],
          "actuals":  [{timestamp, actual_demand_mw}],   # last 24h
          "model_meta": {model_name, features, test_metrics},
          "generated_at": <ISO timestamp>,
        }
    """
    _load_model()

    history = _load_history(hours=200)
    if history is None or len(history) == 0:
        logger.warning("No load history available — returning empty forecast")
        return {"error": "No load history available. Run preprocessing first.", "forecast": []}

    # Fetch weather forecast
    weather_fc = get_forecast_weather(hours=hours)
    weather_map = {w["timestamp"][:16]: w for w in weather_fc}   # key: YYYY-MM-DDTHH:MM

    # Build future timestamps
    now = pd.Timestamp.now(tz="Asia/Kolkata").floor("h")
    future_timestamps = [now + pd.Timedelta(hours=i+1) for i in range(hours)]

    # Build feature rows
    rows = []
    for ts in future_timestamps:
        ts_key = ts.isoformat()[:16]
        weather_entry = weather_map.get(ts_key, {})
        temp = weather_entry.get("temperature_c")
        hum  = weather_entry.get("humidity_pct")
        row = _build_inference_row(ts, history, temp, hum)
        row["_timestamp"] = ts
        rows.append(row)

    df_infer = pd.DataFrame(rows)

    # Select features that model was trained on
    available_feats = [f for f in _feature_list if f in df_infer.columns] if _feature_list else []
    if not available_feats:
        # Fallback: use all non-metadata columns
        available_feats = [c for c in df_infer.columns if not c.startswith("_")]

    X = df_infer[available_feats]

    # Predict
    if _model is None:
        logger.error("Model not loaded")
        return {"error": "Model not loaded. Run train_model.py first.", "forecast": []}

    predictions = _model.predict(X)
    predictions = np.clip(predictions, 0, None)   # demand can't be negative

    # Build forecast output
    capacity = settings.DELHI_GRID_CAPACITY_MW
    forecast_out = []
    for i, (ts, pred) in enumerate(zip(future_timestamps, predictions)):
        pred_mw = round(float(pred), 1)
        risk = classify_risk(pred_mw, capacity)
        forecast_out.append({
            "timestamp":           ts.isoformat(),
            "predicted_demand_mw": pred_mw,
            "risk_level":          risk,
            "capacity_mw":         capacity,
            "utilization_pct":     round(pred_mw / capacity * 100, 1),
            "headroom_mw":         round(capacity - pred_mw, 1),
            "temperature_c":       rows[i].get("temperature_c"),
            "humidity_pct":        rows[i].get("humidity_pct"),
        })

    # Last 24h actuals for chart overlay
    actuals = history.tail(24)[["timestamp","load_MW"]].copy()
    actuals_out = [
        {"timestamp": row["timestamp"].isoformat(), "actual_demand_mw": round(float(row["load_MW"]), 1)}
        for _, row in actuals.iterrows()
    ]

    return {
        "generated_at": pd.Timestamp.now(tz="Asia/Kolkata").isoformat(),
        "horizon_hours": hours,
        "forecast":  forecast_out,
        "actuals":   actuals_out,
        "model_meta": {
            "model_name":   _meta.get("model_name", "unknown"),
            "n_features":   len(available_feats),
            "test_metrics": _meta.get("test_metrics", {}),
        },
    }
