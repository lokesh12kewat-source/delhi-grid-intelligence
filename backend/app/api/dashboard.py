"""GET /api/dashboard — full dashboard data in one call."""
from fastapi import APIRouter
import pandas as pd

from app.services.forecast_service import run_forecast
from app.services.weather_service  import get_current_weather, get_zone_weather_panel
from app.services.risk_engine       import compute_grid_risk, compute_zone_risk, find_peak_hour, generate_alerts
from app.services.recommendation_engine import generate_recommendation
from app.core.config import settings

router = APIRouter()

ZONE_IDS = list(settings.ZONE_CAPACITY_MW.keys())


@router.get("/dashboard")
def dashboard():
    import traceback
    try:
        # 1. Forecast
        fc_result = run_forecast(hours=24)
        forecast  = fc_result.get("forecast", [])

        # 2. Weather
        weather   = get_current_weather()
        zone_wx   = get_zone_weather_panel()

        # 3. Zone risks from current-hour forecast
        current_demand_mw = 0
        zone_risks = []
        if forecast:
            cur = forecast[0]
            total_pred = cur.get("predicted_demand_mw", 0)
            current_demand_mw = total_pred
            total_cap = sum(settings.ZONE_CAPACITY_MW.values())
            for z in ZONE_IDS:
                cap = settings.ZONE_CAPACITY_MW[z]
                zone_demand = total_pred * (cap / total_cap)
                zone_risks.append(compute_zone_risk(z, zone_demand))

        # 4. Grid-level risk
        grid_risk = compute_grid_risk(zone_risks) if zone_risks else {
            "total_demand_mw": current_demand_mw,
            "total_capacity_mw": settings.DELHI_GRID_CAPACITY_MW,
            "utilization_pct": 0, "headroom_mw": settings.DELHI_GRID_CAPACITY_MW,
            "risk_level": "LOW", "n_critical_zones": 0, "n_high_zones": 0,
        }

        # 5. Peak hour
        peak_info = find_peak_hour(forecast)

        # 6. Alerts
        alerts = generate_alerts(zone_risks, forecast)

        # 7. Recommendation
        recommendation = generate_recommendation(grid_risk, zone_risks, weather, peak_info)

        return {
            "generated_at": pd.Timestamp.now(tz="Asia/Kolkata").isoformat(),
            "grid_summary": grid_risk,
            "weather": weather,
            "zone_weather": zone_wx,
            "zone_risks": zone_risks,
            "peak_info": peak_info,
            "active_alerts": len(alerts),
            "alerts": alerts[:5],
            "recommendation": recommendation,
            "forecast_preview": forecast[:6],
            "model_meta": fc_result.get("model_meta", {}),
        }

    except Exception as e:
        tb = traceback.format_exc()
        import logging
        logging.getLogger(__name__).error(f"Dashboard error: {e}\n{tb}")
        return {
            "error": str(e),
            "traceback": tb[-1000:],
            "generated_at": pd.Timestamp.now(tz="Asia/Kolkata").isoformat(),
            "grid_summary": {"total_demand_mw": 0, "utilization_pct": 0, "risk_level": "UNKNOWN"},
            "weather": {}, "zone_weather": [], "zone_risks": [],
            "peak_info": {}, "active_alerts": 0, "alerts": [],
            "recommendation": {"action_text": "Backend error — check /debug endpoint"},
            "forecast_preview": [], "model_meta": {},
        }
