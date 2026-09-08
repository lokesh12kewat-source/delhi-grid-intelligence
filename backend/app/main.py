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
    """Run full data pipeline if model is missing (handles Render ephemeral disk)."""
    model_file = settings.MODELS_DIR / "forecast_model.pkl"
    if model_file.exists():
        logger.info(f"Model found at {model_file} — skipping pipeline")
        return

    logger.warning("Model not found — running build pipeline on startup...")
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
