"""GET /api/forecast?hours=24 — full forecast with actuals overlay."""
import traceback
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from app.services.forecast_service import run_forecast

router = APIRouter()


@router.get("/forecast")
def forecast(hours: int = Query(default=24, ge=1, le=168,
                                description="Forecast horizon in hours (1-168)")):
    try:
        return run_forecast(hours=hours)
    except Exception as e:
        tb = traceback.format_exc()
        return JSONResponse(status_code=500, content={"error": str(e), "traceback": tb[-2000:]})
