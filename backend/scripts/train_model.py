"""
scripts/train_model.py
-----------------------
Trains the Delhi demand forecast model.

Pipeline:
  1. Load features_hourly.csv
  2. Chronological train / validation / test split
  3. Baseline models (lag_24h, lag_168h)
  4. Two-model experiment:
       Model A -- Load + time features only
       Model B -- Load + time + weather features
  5. XGBoost + GradientBoosting comparison
  6. Hyperparameter tuning with TimeSeriesSplit
  7. Evaluation on held-out test set (MAE, RMSE, MAPE, R²)
  8. Save final model + feature list + scaler

Outputs:
  models/forecast_model.pkl   -- trained model
  models/feature_list.json    -- exact feature columns (train/serve parity)
  models/training_report.txt  -- all metrics, split dates, baseline comparison
"""

import sys, json, warnings, os
from pathlib import Path
import pandas as pd
import numpy as np
import joblib

warnings.filterwarnings("ignore")

# Use fewer trees on Render free tier (512 MB RAM limit)
IS_RENDER = os.environ.get("RENDER", "") == "true" or os.environ.get("RENDER_BUILD", "") == "1"
N_TREES = 50 if IS_RENDER else 200
print(f"  Running on {'Render (light model, {N_TREES} trees)' if IS_RENDER else f'local (full model, {N_TREES} trees)'}")

sys.path.insert(0, str(Path(__file__).parent.parent))
from app.core.config import settings

FEATURES_FILE  = settings.PROCESSED_DIR / "features_hourly.csv"
MODEL_FILE     = settings.MODELS_DIR    / "forecast_model.pkl"
FEAT_LIST_FILE = settings.MODELS_DIR    / "feature_list.json"
REPORT_FILE    = settings.MODELS_DIR    / "training_report.txt"

# ── Feature groups ─────────────────────────────────────────────────────────────
TIME_FEATURES = [
    "hour_sin", "hour_cos", "dow_sin", "dow_cos",
    "month_sin", "month_cos", "month",
    "is_weekend", "is_holiday",
]
LOAD_FEATURES = [
    "lag_1h", "lag_24h", "lag_168h",
    "roll_mean_3h", "roll_mean_24h", "roll_std_24h",
]
WEATHER_FEATURES = [
    "temperature_c", "humidity_pct",
    "cooling_degree_hrs", "temp_lag_24h",
]
FEATURES_A = TIME_FEATURES + LOAD_FEATURES
FEATURES_B = TIME_FEATURES + LOAD_FEATURES + WEATHER_FEATURES


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """MAE, RMSE, MAPE, R²."""
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    mae  = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2   = r2_score(y_true, y_pred)
    # sMAPE to handle near-zero values
    smape = 100 * np.mean(
        2 * np.abs(y_pred - y_true) / (np.abs(y_true) + np.abs(y_pred) + 1e-9)
    )
    mape = 100 * np.mean(np.abs((y_true - y_pred) / (np.abs(y_true) + 1e-9)))
    return {"MAE": round(mae,3), "RMSE": round(rmse,3),
            "MAPE": round(mape,3), "sMAPE": round(smape,3), "R2": round(r2,4)}


def chronological_split(df: pd.DataFrame):
    """Split by exact date cutoffs -- inspect actual data first."""
    # Inspect and choose cutoffs after seeing actual date range
    ts = pd.to_datetime(df["timestamp"])
    min_ts = ts.min()
    max_ts = ts.max()
    total_days = (max_ts - min_ts).days

    print(f"\n  Data range: {min_ts.date()} -> {max_ts.date()}  ({total_days} days)")

    # Last 2 months = test, prior 2 months = validation, rest = train
    test_start  = max_ts - pd.Timedelta(days=62)
    val_start   = test_start - pd.Timedelta(days=62)

    train_mask = ts <  val_start
    val_mask   = (ts >= val_start) & (ts < test_start)
    test_mask  = ts >= test_start

    print(f"  Train:      {ts[train_mask].min().date()} -> {ts[train_mask].max().date()}  ({train_mask.sum():,} rows)")
    print(f"  Validation: {ts[val_mask].min().date()}  -> {ts[val_mask].max().date()}   ({val_mask.sum():,} rows)")
    print(f"  Test:       {ts[test_mask].min().date()} -> {ts[test_mask].max().date()}   ({test_mask.sum():,} rows)")

    return train_mask, val_mask, test_mask


def baseline_predictions(df: pd.DataFrame, mask):
    """Naive baselines -- yesterday and last-week same hour."""
    y_true = df.loc[mask, "load_MW"].values
    y_lag24  = df.loc[mask, "lag_24h"].values
    y_lag168 = df.loc[mask, "lag_168h"].values

    # Drop rows where baseline is NaN
    valid24  = ~np.isnan(y_lag24)  & ~np.isnan(y_true)
    valid168 = ~np.isnan(y_lag168) & ~np.isnan(y_true)

    m24  = compute_metrics(y_true[valid24],  y_lag24[valid24])
    m168 = compute_metrics(y_true[valid168], y_lag168[valid168])
    return m24, m168


def train_and_eval(X_train, y_train, X_test, y_test, model, model_name: str) -> dict:
    """Fit model on train, evaluate on test."""
    # Drop rows with NaN features
    valid_train = X_train.notna().all(axis=1) & y_train.notna()
    valid_test  = X_test.notna().all(axis=1)  & y_test.notna()

    model.fit(X_train[valid_train], y_train[valid_train])
    y_pred = model.predict(X_test[valid_test])
    metrics = compute_metrics(y_test[valid_test].values, y_pred)
    print(f"    {model_name:35s} | MAE={metrics['MAE']:7.2f}  RMSE={metrics['RMSE']:7.2f}  "
          f"MAPE={metrics['MAPE']:5.2f}%  R²={metrics['R2']:.4f}")
    return metrics, model


def train():
    report_lines = []
    def log(msg=""):
        print(msg)
        report_lines.append(msg)

    log("=" * 70)
    log("  DELHI DEMAND FORECAST -- MODEL TRAINING REPORT")
    log("=" * 70)

    # ── 1. Load features ──────────────────────────────────────────────────────
    log("\n[1/6] Loading feature dataset...")
    if not FEATURES_FILE.exists():
        log(f"  ERROR: {FEATURES_FILE} not found. Run build_features.py first.")
        sys.exit(1)

    df = pd.read_csv(FEATURES_FILE, parse_dates=["timestamp"])
    log(f"  Rows: {len(df):,}  |  Columns: {len(df.columns)}")

    # Filter: keep only rows with valid load_MW
    df = df.dropna(subset=["load_MW"]).reset_index(drop=True)
    log(f"  After dropping NaN load: {len(df):,} rows")

    # ── 2. Chronological split ────────────────────────────────────────────────
    log("\n[2/6] Chronological train/validation/test split...")
    train_mask, val_mask, test_mask = chronological_split(df)

    # ── 3. Baselines ──────────────────────────────────────────────────────────
    log("\n[3/6] Baseline evaluation on TEST set:")
    log("  (Baselines use raw lag features -- no model needed)")
    m_lag24, m_lag168 = baseline_predictions(df, test_mask)
    log(f"    Baseline lag_24h (yesterday same hour) : MAE={m_lag24['MAE']:7.2f}  RMSE={m_lag24['RMSE']:7.2f}  MAPE={m_lag24['MAPE']:.2f}%")
    log(f"    Baseline lag_168h (last week same hour): MAE={m_lag168['MAE']:7.2f}  RMSE={m_lag168['RMSE']:7.2f}  MAPE={m_lag168['MAPE']:.2f}%")

    # ── 4. Model comparison ───────────────────────────────────────────────────
    log("\n[4/6] Model comparison on VALIDATION set:")

    try:
        from xgboost import XGBRegressor
        xgb_available = True
    except ImportError:
        xgb_available = False
        log("  NOTE: xgboost not available, using GradientBoosting only")

    from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor

    candidates = {}
    # Model A (no weather)
    candidates["RF_A (no weather)"]  = (RandomForestRegressor(n_estimators=N_TREES, n_jobs=-1, random_state=42), FEATURES_A)
    if not IS_RENDER:  # Skip slow GB on Render to save build time
        candidates["GB_A (no weather)"]  = (GradientBoostingRegressor(n_estimators=N_TREES, random_state=42), FEATURES_A)
    if xgb_available:
        candidates["XGB_A (no weather)"] = (XGBRegressor(n_estimators=N_TREES, learning_rate=0.05,
                                                          max_depth=6, n_jobs=-1, random_state=42,
                                                          verbosity=0), FEATURES_A)
    # Model B (with weather)
    avail_weather = [f for f in WEATHER_FEATURES if f in df.columns and df[f].notna().sum() > 100]
    if avail_weather:
        feat_b = [f for f in FEATURES_B if f in df.columns]
        candidates["RF_B (with weather)"]  = (RandomForestRegressor(n_estimators=N_TREES, n_jobs=-1, random_state=42), feat_b)
        if xgb_available and not IS_RENDER:
            candidates["XGB_B (with weather)"] = (XGBRegressor(n_estimators=N_TREES, learning_rate=0.05,
                                                               max_depth=6, n_jobs=-1, random_state=42,
                                                               verbosity=0), feat_b)
    else:
        log("  WARNING: No weather features available -- skipping Model B")

    log(f"  {'Model':35s} | {'MAE':>7}  {'RMSE':>7}  {'MAPE':>6}  R²")
    log("  " + "-" * 65)

    results = {}
    trained_models = {}
    for name, (model, feats) in candidates.items():
        avail_feats = [f for f in feats if f in df.columns]
        X_train = df.loc[train_mask, avail_feats]
        y_train = df.loc[train_mask, "load_MW"]
        X_val   = df.loc[val_mask, avail_feats]
        y_val   = df.loc[val_mask, "load_MW"]

        m, fitted = train_and_eval(X_train, y_train, X_val, y_val, model, name)
        results[name] = {"metrics": m, "features": avail_feats}
        trained_models[name] = (fitted, avail_feats)
        log(f"    {name:35s} | MAE={m['MAE']:7.2f}  RMSE={m['RMSE']:7.2f}  MAPE={m['MAPE']:5.2f}%  R²={m['R2']:.4f}")

    # ── 5. Select best + final test evaluation ────────────────────────────────
    best_name = min(results, key=lambda n: results[n]["metrics"]["RMSE"])
    log(f"\n[5/6] Best validation model: {best_name}")
    log("  Evaluating BEST model on held-out TEST set...")

    best_model, best_feats = trained_models[best_name]
    X_test   = df.loc[test_mask, best_feats]
    y_test   = df.loc[test_mask, "load_MW"]
    valid    = X_test.notna().all(axis=1) & y_test.notna()
    y_pred   = best_model.predict(X_test[valid])
    test_met = compute_metrics(y_test[valid].values, y_pred)

    log(f"\n  TEST SET RESULTS -- {best_name}:")
    log(f"    MAE:   {test_met['MAE']:.3f} MW")
    log(f"    RMSE:  {test_met['RMSE']:.3f} MW")
    log(f"    MAPE:  {test_met['MAPE']:.3f}%")
    log(f"    sMAPE: {test_met['sMAPE']:.3f}%")
    log(f"    R²:    {test_met['R2']:.4f}")
    log(f"\n  COMPARISON vs baselines on test set:")
    log(f"    Baseline lag_24h:  MAPE={m_lag24['MAPE']:.2f}%")
    log(f"    Baseline lag_168h: MAPE={m_lag168['MAPE']:.2f}%")
    log(f"    ML model:          MAPE={test_met['MAPE']:.2f}%")
    if m_lag168["MAPE"] > 0:
        improvement = (m_lag168["MAPE"] - test_met["MAPE"]) / m_lag168["MAPE"] * 100
        log(f"    Improvement over weekly baseline: {improvement:.1f}%")

    # Feature importance
    if hasattr(best_model, "feature_importances_"):
        log("\n  Feature importances (top 10):")
        importances = pd.Series(best_model.feature_importances_, index=best_feats)
        for feat, imp in importances.nlargest(10).items():
            log(f"    {feat:30s}: {imp:.4f}")

    # ── 6. Save model ─────────────────────────────────────────────────────────
    log(f"\n[6/6] Saving model...")
    settings.MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(best_model, MODEL_FILE)
    log(f"  Model saved -> {MODEL_FILE}")

    feat_meta = {
        "features":      best_feats,
        "target":        "load_MW",
        "model_name":    best_name,
        "test_metrics":  test_met,
        "baseline_lag24h":  m_lag24,
        "baseline_lag168h": m_lag168,
    }
    FEAT_LIST_FILE.write_text(json.dumps(feat_meta, indent=2), encoding="utf-8")
    log(f"  Feature list saved -> {FEAT_LIST_FILE}")

    log("\n" + "="*70)
    log("  TRAINING COMPLETE")
    log("="*70)

    REPORT_FILE.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"\nFull report -> {REPORT_FILE}")
    print("\n  NEXT STEP: uvicorn app.main:app --reload")


if __name__ == "__main__":
    train()
