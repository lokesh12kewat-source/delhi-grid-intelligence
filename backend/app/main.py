"""
app/main.py
------------
FastAPI application entry point for Delhi Grid Intelligence Platform.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import dashboard, forecast, weather, alerts, recommendations, predict, zones

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)

app = FastAPI(
    title="Delhi Grid Intelligence API",
    description="AI-based Electricity Demand Prediction System for Delhi",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # restrict in production
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
