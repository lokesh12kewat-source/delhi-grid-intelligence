"""GET /api/recommendations — AI-powered operator recommendations."""
from fastapi import APIRouter
from app.services.forecast_service import run_forecast
from app.services.weather_service import get_current_weather
from app.services.risk_engine import compute_zone_risk, compute_grid_risk, find_peak_hour, generate_alerts
from app.services.recommendation_engine import generate_recommendation
from app.core.config import settings

router = APIRouter()
ZONE_IDS = list(settings.ZONE_CAPACITY_MW.keys())


@router.get("/recommendations")
def recommendations():
    fc      = run_forecast(hours=24)
    forecast = fc.get("forecast", [])
    weather  = get_current_weather()

    if not forecast:
        return {"error": "No forecast available"}

    total_pred = forecast[0].get("predicted_demand_mw", 0)
    total_cap  = sum(settings.ZONE_CAPACITY_MW.values())
    zone_risks = [
        compute_zone_risk(z, total_pred * (settings.ZONE_CAPACITY_MW[z] / total_cap))
        for z in ZONE_IDS
    ]
    grid_risk = compute_grid_risk(zone_risks)
    peak_info = find_peak_hour(forecast)
    return generate_recommendation(grid_risk, zone_risks, weather, peak_info)
