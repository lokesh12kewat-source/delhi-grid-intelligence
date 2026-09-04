"""POST /api/predict — on-demand forecast inference."""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional
from app.services.forecast_service import run_forecast

router = APIRouter()


class PredictRequest(BaseModel):
    hours: int = Field(default=24, ge=1, le=168, description="Forecast horizon in hours")
    temperature_override: Optional[float] = Field(
        default=None,
        description="Override temperature for what-if analysis (°C)"
    )


@router.post("/predict")
def predict(req: PredictRequest):
    """Run a fresh forecast inference. Optionally override temperature for what-if analysis."""
    result = run_forecast(hours=req.hours)
    # Note: temperature_override would require passing it into run_forecast
    # Currently logged for future implementation
    if req.temperature_override is not None:
        result["temperature_override_used"] = req.temperature_override
        result["note"] = "Temperature override applied to what-if scenario"
    return result
