"""GET /api/alerts — active capacity risk alerts."""
from fastapi import APIRouter
from app.services.forecast_service import run_forecast
from app.services.risk_engine import compute_zone_risk, compute_grid_risk, generate_alerts
from app.core.config import settings

router = APIRouter()
ZONE_IDS = list(settings.ZONE_CAPACITY_MW.keys())


@router.get("/alerts")
def alerts():
    fc = run_forecast(hours=24)
    forecast = fc.get("forecast", [])
    if not forecast:
        return {"alerts": [], "total": 0}

    total_pred = forecast[0].get("predicted_demand_mw", 0)
    total_cap  = sum(settings.ZONE_CAPACITY_MW.values())
    zone_risks = [
        compute_zone_risk(z, total_pred * (settings.ZONE_CAPACITY_MW[z] / total_cap))
        for z in ZONE_IDS
    ]
    alert_list = generate_alerts(zone_risks, forecast)
    return {"alerts": alert_list, "total": len(alert_list)}
