"""GET /api/forecast?hours=24 — full forecast with actuals overlay."""
from fastapi import APIRouter, Query
from app.services.forecast_service import run_forecast

router = APIRouter()


@router.get("/forecast")
def forecast(hours: int = Query(default=24, ge=1, le=168,
                                description="Forecast horizon in hours (1-168)")):
    return run_forecast(hours=hours)
