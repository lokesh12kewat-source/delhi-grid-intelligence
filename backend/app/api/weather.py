"""GET /api/weather — current weather for all 6 Delhi zones."""
from fastapi import APIRouter
from app.services.weather_service import get_current_weather, get_zone_weather_panel, get_forecast_weather

router = APIRouter()


@router.get("/weather")
def weather():
    return {
        "current": get_current_weather(),
        "zones":   get_zone_weather_panel(),
        "forecast_24h": get_forecast_weather(hours=24),
    }
