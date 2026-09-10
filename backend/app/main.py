"""
app/main.py
------------
FastAPI application entry point for Delhi Grid Intelligence Platform.
"""

import os
import asyncio
import logging
import subprocess
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import dashboard, forecast, weather, alerts, recommendations, predict, zones
from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)
logger = logging.getLogger(__name__)

SCRIPTS = Path(__file__).parent.parent / "scripts"


def _run_pipeline():
    """
    Run data pipeline ONLY if model is missing AND we are NOT on Render.
    On Render the pre-trained model is committed to git — no training needed.
    Training on Render free tier (512 MB RAM) causes OOM crashes.
    """
    model_file = settings.MODELS_DIR / "forecast_model.pkl"

    if model_file.exists():
        logger.info(f"Model found at {model_file} — skipping pipeline")
        return

    # On Render, never attempt training — it will OOM
    is_render = bool(os.environ.get("RENDER") or os.environ.get("RENDER_SERVICE_ID"))
    if is_render:
        logger.error(
            "Model missing on Render but training is disabled to prevent OOM. "
            "Please commit the model file to git and redeploy."
        )
        return

    # Local-only: run full pipeline
    logger.warning("Model not found — running build pipeline locally...")
    env = {**os.environ, "RENDER_BUILD": "1", "PYTHONIOENCODING": "utf-8"}
    base = SCRIPTS.parent

    steps = [
        ("generate_demo_data", [sys.executable, str(SCRIPTS / "generate_demo_data.py")]),
        ("preprocess_load",    [sys.executable, str(SCRIPTS / "preprocess_load.py")]),
        ("build_features",     [sys.executable, str(SCRIPTS / "build_features.py")]),
        ("train_model",        [sys.executable, str(SCRIPTS / "train_model.py")]),
    ]

    for name, cmd in steps:
        if name == "preprocess_load" and (settings.PROCESSED_DIR / "load_hourly.csv").exists():
            logger.info(f"[SKIP] {name}"); continue
        if name == "build_features" and (settings.PROCESSED_DIR / "features_hourly.csv").exists():
            logger.info(f"[SKIP] {name}"); continue
        if name == "generate_demo_data" and (settings.RAW_DATA_DIR / "load_data.csv").exists():
            logger.info(f"[SKIP] {name}"); continue

        logger.info(f"[RUN] {name}...")
        result = subprocess.run(cmd, cwd=str(base), env=env, capture_output=False)
        if result.returncode != 0:
            logger.error(f"Pipeline step failed: {name}")
            return

    logger.info("Pipeline complete — model ready")


async def _keep_alive_loop():
    """
    Ping /health every 14 minutes so Render free tier never sleeps.
    Render spins down after 15 min of inactivity — this prevents that.
    """
    # Wait 2 min after startup before first ping
    await asyncio.sleep(120)
    port = os.environ.get("PORT", "8000")
    url  = f"http://localhost:{port}/health"
    while True:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url)
                logger.info(f"Keep-alive ping -> {resp.status_code}")
        except Exception as e:
            logger.debug(f"Keep-alive ping failed (non-critical): {e}")
        # Ping every 14 minutes
        await asyncio.sleep(14 * 60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Train model if missing (Render ephemeral disk)
    _run_pipeline()

    # 2. Start keep-alive background loop (prevents Render free tier sleep)
    task = asyncio.create_task(_keep_alive_loop())
    logger.info("Keep-alive loop started (pings every 14 min)")

    yield

    # Cleanup
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="Delhi Grid Intelligence API",
    description="AI-based Electricity Demand Prediction System for Delhi",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(dashboard.router,       prefix="/api", tags=["Dashboard"])
app.include_router(forecast.router,        prefix="/api", tags=["Forecast"])
app.include_router(weather.router,         prefix="/api", tags=["Weather"])
app.include_router(alerts.router,          prefix="/api", tags=["Alerts"])
app.include_router(recommendations.router, prefix="/api", tags=["Recommendations"])
app.include_router(predict.router,         prefix="/api", tags=["Predict"])
app.include_router(zones.router,           prefix="/api", tags=["Zones"])


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "service": "Delhi Grid Intelligence API"}


@app.get("/debug", tags=["Health"])
def debug():
    """Debug endpoint — shows model/data status and any import errors."""
    import traceback
    info = {}

    # Check model
    try:
        from app.core.config import settings
        model_path = settings.MODELS_DIR / "forecast_model.pkl"
        hourly_path = settings.PROCESSED_DIR / "load_hourly.csv"
        info["model_exists"]  = model_path.exists()
        info["hourly_exists"] = hourly_path.exists()
        info["model_path"]    = str(model_path)
        info["hourly_path"]   = str(hourly_path)
    except Exception as e:
        info["config_error"] = str(e)

    # Try loading model
    try:
        import joblib
        from app.core.config import settings
        m = joblib.load(settings.MODELS_DIR / "forecast_model.pkl")
        info["model_load"] = "OK"
        info["model_type"] = type(m).__name__
    except Exception as e:
        info["model_load_error"] = str(e)
        info["model_traceback"]  = traceback.format_exc()[-800:]

    # Try importing forecast_service
    try:
        from app.services.forecast_service import run_forecast
        info["forecast_import"] = "OK"
    except Exception as e:
        info["forecast_import_error"] = str(e)
        info["forecast_traceback"]    = traceback.format_exc()[-800:]

    # Try running forecast
    try:
        from app.services.forecast_service import run_forecast
        result = run_forecast(hours=2)
        fc = result.get("forecast", [])
        info["forecast_run"] = f"OK — {len(fc)} items"
        if fc:
            info["first_forecast"] = {k: v for k, v in fc[0].items() if k != "risk_color"}
        if "error" in result:
            info["forecast_error_key"] = result["error"]
    except Exception as e:
        info["forecast_run_error"] = str(e)
        info["forecast_run_tb"]   = traceback.format_exc()[-800:]

    return info
