"""GET /api/zones — all Delhi zone metadata and current status."""
from fastapi import APIRouter, HTTPException
from app.services.forecast_service import run_forecast
from app.services.risk_engine import compute_zone_risk
from app.core.config import settings

router = APIRouter()

ZONE_META = {
    "delhi_north":     {"zone_name": "North Delhi", "discom": "TPDDL", "description": "Pitampura, Rohini, Narela"},
    "delhi_south":     {"zone_name": "South Delhi", "discom": "BRPL", "description": "Saket, Hauz Khas, Mehrauli"},
    "delhi_east":      {"zone_name": "East Delhi",  "discom": "BYPL", "description": "Preet Vihar, Laxmi Nagar, Patparganj"},
    "delhi_west":      {"zone_name": "West Delhi",  "discom": "BRPL", "description": "Janakpuri, Dwarka, Punjabi Bagh"},
    "delhi_central":   {"zone_name": "Central Delhi","discom": "NDMC","description": "Connaught Place, Lutyens Zone"},
    "delhi_northeast": {"zone_name": "North-East Delhi","discom": "TPDDL","description": "Shahdara, Yamuna Vihar, Mustafabad"},
}
ZONE_IDS = list(settings.ZONE_CAPACITY_MW.keys())


@router.get("/zones")
def zones():
    fc = run_forecast(hours=1)
    forecast = fc.get("forecast", [])
    total_pred = forecast[0].get("predicted_demand_mw", 0) if forecast else 0
    total_cap  = sum(settings.ZONE_CAPACITY_MW.values())

    result = []
    for z in ZONE_IDS:
        cap = settings.ZONE_CAPACITY_MW[z]
        zone_demand = total_pred * (cap / total_cap) if total_cap > 0 else 0
        risk = compute_zone_risk(z, zone_demand)
        meta = ZONE_META.get(z, {})
        result.append({**meta, **risk})

    return {"zones": result, "total": len(result)}


@router.get("/zones/{zone_id}")
def zone_detail(zone_id: str):
    if zone_id not in ZONE_IDS:
        raise HTTPException(status_code=404, detail=f"Zone '{zone_id}' not found")

    fc = run_forecast(hours=24)
    forecast = fc.get("forecast", [])
    total_cap  = sum(settings.ZONE_CAPACITY_MW.values())
    cap = settings.ZONE_CAPACITY_MW[zone_id]

    zone_fc = []
    for entry in forecast:
        total_pred = entry.get("predicted_demand_mw", 0)
        zone_demand = total_pred * (cap / total_cap)
        risk = compute_zone_risk(zone_id, zone_demand)
        zone_fc.append({
            "timestamp": entry["timestamp"],
            **risk,
        })

    meta = ZONE_META.get(zone_id, {})
    return {
        "zone_id": zone_id,
        **meta,
        "capacity_mw": cap,
        "capacity_note": "Demo/configurable — not official SLDC limits",
        "forecast_24h": zone_fc,
        "actuals_24h":  fc.get("actuals", []),
    }
