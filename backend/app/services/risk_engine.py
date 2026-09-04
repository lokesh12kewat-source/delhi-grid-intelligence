"""
app/services/risk_engine.py
----------------------------
Converts predicted MW demand into risk levels + actionable metrics.

Principles:
  - ML predicts demand
  - Rules assess risk   ← this file
  - LLM explains       ← recommendation_engine.py
  - Dashboard shows    ← frontend

Risk thresholds are CONFIGURABLE (loaded from .env).
They are NOT official Delhi grid limits unless verified from an
authoritative source such as SLDC/POSOCO. This is a demo system.
"""

from app.core.config import settings

# ── Risk level labels ─────────────────────────────────────────────────────────
LEVELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
LEVEL_COLORS = {
    "LOW":      "#00ff88",
    "MEDIUM":   "#ffcc00",
    "HIGH":     "#ff6600",
    "CRITICAL": "#ff3366",
}


def classify_risk(demand_mw: float, capacity_mw: float) -> str:
    """
    Classify demand risk given predicted demand and configured capacity.

    Thresholds (configurable via .env):
        LOW:      < 60% of capacity
        MEDIUM:   60% – 75%
        HIGH:     75% – 90%
        CRITICAL: >= 90%
    """
    if capacity_mw <= 0:
        return "UNKNOWN"

    utilization = demand_mw / capacity_mw

    if utilization >= settings.RISK_HIGH:
        return "CRITICAL"
    elif utilization >= settings.RISK_MEDIUM:
        return "HIGH"
    elif utilization >= settings.RISK_LOW:
        return "MEDIUM"
    else:
        return "LOW"


def compute_zone_risk(zone_id: str, predicted_demand_mw: float) -> dict:
    """
    Full risk metrics for a single zone.

    Returns:
        zone_id, predicted_demand_mw, capacity_mw, utilization_pct,
        headroom_mw, risk_level, risk_color
    """
    capacity = settings.ZONE_CAPACITY_MW.get(zone_id, settings.DELHI_GRID_CAPACITY_MW / 6)
    utilization = predicted_demand_mw / capacity if capacity > 0 else 0
    headroom    = capacity - predicted_demand_mw
    risk_level  = classify_risk(predicted_demand_mw, capacity)

    return {
        "zone_id":             zone_id,
        "predicted_demand_mw": round(predicted_demand_mw, 1),
        "capacity_mw":         round(capacity, 1),
        "utilization_pct":     round(utilization * 100, 1),
        "headroom_mw":         round(headroom, 1),
        "risk_level":          risk_level,
        "risk_color":          LEVEL_COLORS[risk_level],
        "capacity_note":       "Demo capacity — configurable via .env. Not official SLDC limits.",
    }


def compute_grid_risk(zone_risks: list[dict]) -> dict:
    """
    Aggregate zone risks into a city-level grid summary.

    Args:
        zone_risks: list of compute_zone_risk() outputs

    Returns:
        total_demand_mw, total_capacity_mw, utilization_pct,
        headroom_mw, risk_level, n_critical_zones, n_high_zones
    """
    total_demand   = sum(z["predicted_demand_mw"] for z in zone_risks)
    total_capacity = sum(z["capacity_mw"]         for z in zone_risks)
    headroom       = total_capacity - total_demand
    utilization    = total_demand / total_capacity if total_capacity > 0 else 0

    # Grid risk = worst zone risk
    level_order = {l: i for i, l in enumerate(LEVELS)}
    worst_level = max(zone_risks, key=lambda z: level_order.get(z["risk_level"], 0))["risk_level"]

    n_critical = sum(1 for z in zone_risks if z["risk_level"] == "CRITICAL")
    n_high     = sum(1 for z in zone_risks if z["risk_level"] == "HIGH")

    return {
        "total_demand_mw":    round(total_demand, 1),
        "total_capacity_mw":  round(total_capacity, 1),
        "utilization_pct":    round(utilization * 100, 1),
        "headroom_mw":        round(headroom, 1),
        "risk_level":         worst_level,
        "risk_color":         LEVEL_COLORS[worst_level],
        "n_critical_zones":   n_critical,
        "n_high_zones":       n_high,
        "capacity_note":      "Demo capacity — configurable via .env. Not official SLDC limits.",
    }


def find_peak_hour(forecast: list[dict]) -> dict:
    """
    Find the peak demand hour in a 24h forecast.

    Args:
        forecast: list of {timestamp, predicted_demand_mw, ...}

    Returns:
        peak timestamp, demand, risk level
    """
    if not forecast:
        return {}

    peak = max(forecast, key=lambda x: x.get("predicted_demand_mw", 0))
    return {
        "peak_timestamp":    peak.get("timestamp"),
        "peak_demand_mw":    peak.get("predicted_demand_mw"),
        "peak_risk_level":   peak.get("risk_level", "UNKNOWN"),
    }


def generate_alerts(zone_risks: list[dict], forecast: list[dict]) -> list[dict]:
    """
    Generate structured capacity risk alerts from zone risks and forecast.

    Returns a list of alerts, sorted by severity (CRITICAL first).
    """
    alerts = []
    level_order = {l: i for i, l in enumerate(reversed(LEVELS))}

    for zone in zone_risks:
        if zone["risk_level"] in ("HIGH", "CRITICAL"):
            alert_type = "CAPACITY_RISK" if zone["risk_level"] == "CRITICAL" else "PEAK_WARNING"
            alerts.append({
                "zone_id":           zone["zone_id"],
                "alert_type":        alert_type,
                "risk_level":        zone["risk_level"],
                "risk_color":        zone["risk_color"],
                "predicted_demand_mw": zone["predicted_demand_mw"],
                "capacity_mw":       zone["capacity_mw"],
                "headroom_mw":       zone["headroom_mw"],
                "utilization_pct":   zone["utilization_pct"],
                "message": (
                    f"{zone['zone_id'].replace('_',' ').title()} is at "
                    f"{zone['utilization_pct']:.0f}% capacity "
                    f"({zone['predicted_demand_mw']:.0f} MW / {zone['capacity_mw']:.0f} MW). "
                    f"Headroom: {zone['headroom_mw']:.0f} MW."
                ),
            })

    # Sort: CRITICAL first, then HIGH
    alerts.sort(key=lambda a: level_order.get(a["risk_level"], 0))
    return alerts
