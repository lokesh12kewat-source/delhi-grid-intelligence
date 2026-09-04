"""
app/services/recommendation_engine.py
---------------------------------------
Architecture:
  ML predicts demand  ->  risk_engine assesses risk
  ->  THIS FILE produces structured recommendation
  ->  LLM (Gemini) explains it in natural language
  ->  API sends both to dashboard

The LLM ONLY explains structured data produced here.
It never invents numbers or claims unsupported facts.
"""

import logging
try:
    from google import genai as genai_client
    GENAI_NEW = True
except ImportError:
    GENAI_NEW = False

from app.core.config import settings
from app.services.risk_engine import LEVELS

logger = logging.getLogger(__name__)

# ── Gemini client ─────────────────────────────────────────────────────────────
_gemini_client = None

def _get_gemini_client():
    global _gemini_client
    if _gemini_client is not None:
        return _gemini_client
    if not settings.GEMINI_API_KEY:
        return None
    try:
        if GENAI_NEW:
            _gemini_client = genai_client.Client(api_key=settings.GEMINI_API_KEY)
        else:
            import google.generativeai as legacy_genai
            legacy_genai.configure(api_key=settings.GEMINI_API_KEY)
            _gemini_client = "legacy"
    except Exception as e:
        logger.error(f"Gemini configuration failed: {e}")
    return _gemini_client


# ── Action codes ──────────────────────────────────────────────────────────────
ACTION_CODES = {
    "LOW":      "MONITOR",
    "MEDIUM":   "PREPARE",
    "HIGH":     "ALERT",
    "CRITICAL": "EMERGENCY",
}

ACTION_TEMPLATES = {
    "MONITOR": (
        "Grid operating comfortably. Continue routine monitoring. "
        "No immediate action required."
    ),
    "PREPARE": (
        "Demand is approaching {utilization_pct:.0f}% of configured capacity. "
        "Consider pre-positioning reserve capacity and notifying standby units. "
        "Peak expected around {peak_time}."
    ),
    "ALERT": (
        "HIGH demand alert. {n_high_zones} zone(s) above 75% capacity utilization. "
        "Headroom is {headroom_mw:.0f} MW. Activate demand-side management protocols. "
        "Monitor feeders at {peak_time}."
    ),
    "EMERGENCY": (
        "CRITICAL CAPACITY RISK. {n_critical_zones} zone(s) at or above 90% capacity. "
        "Headroom: {headroom_mw:.0f} MW. Immediate action: activate emergency reserves, "
        "consider load shedding contingency. Peak at {peak_time}."
    ),
}


def _build_structured_recommendation(
    grid_risk: dict,
    zone_risks: list,
    weather: dict,
    peak_info: dict,
) -> dict:
    """Build structured recommendation — ground truth the LLM only explains."""
    risk_level  = grid_risk.get("risk_level", "LOW")
    action_code = ACTION_CODES.get(risk_level, "MONITOR")

    n_critical = grid_risk.get("n_critical_zones", 0)
    n_high     = grid_risk.get("n_high_zones", 0)
    headroom   = grid_risk.get("headroom_mw", 0)
    util_pct   = grid_risk.get("utilization_pct", 0)

    peak_ts   = peak_info.get("peak_timestamp")
    peak_time = "unknown"
    if peak_ts:
        try:
            import pandas as pd
            peak_time = pd.Timestamp(peak_ts).strftime("%H:%M IST")
        except Exception:
            peak_time = str(peak_ts)

    template    = ACTION_TEMPLATES.get(action_code, ACTION_TEMPLATES["MONITOR"])
    action_text = template.format(
        utilization_pct=util_pct,
        peak_time=peak_time,
        n_high_zones=n_high,
        n_critical_zones=n_critical,
        headroom_mw=headroom,
    )

    avg_temp = weather.get("delhi_avg_temp")
    avg_hum  = weather.get("delhi_avg_humidity")
    cooling  = round(max(0, avg_temp - 24), 1) if avg_temp is not None else None

    demand_drivers = {
        "temperature":    f"{avg_temp:.1f}C" if avg_temp else "N/A",
        "humidity":       f"{avg_hum:.0f}%" if avg_hum else "N/A",
        "cooling_degree": f"{cooling}C above comfort" if cooling else "N/A",
        "peak_hour":      peak_time,
    }

    critical_zones = [z["zone_id"] for z in zone_risks if z["risk_level"] == "CRITICAL"]
    high_zones     = [z["zone_id"] for z in zone_risks if z["risk_level"] == "HIGH"]

    return {
        "risk_level":      risk_level,
        "action_code":     action_code,
        "action_text":     action_text,
        "peak_time":       peak_time,
        "peak_demand_mw":  peak_info.get("peak_demand_mw"),
        "headroom_mw":     headroom,
        "utilization_pct": util_pct,
        "critical_zones":  critical_zones,
        "high_zones":      high_zones,
        "demand_drivers":  demand_drivers,
        "data_note":       "Capacity thresholds are demo/configurable — not official SLDC limits.",
    }


def _explain_with_llm(structured: dict, weather: dict) -> str:
    """Ask Gemini to explain the structured recommendation in plain English."""
    client = _get_gemini_client()
    if client is None:
        logger.warning("Gemini not configured — returning rule-based text")
        return structured["action_text"]

    prompt = (
        "You are an AI assistant for the Delhi Electricity Grid Intelligence Platform.\n\n"
        "A demand forecasting system has produced the following structured assessment:\n\n"
        f"Risk Level: {structured['risk_level']}\n"
        f"Action Required: {structured['action_code']}\n"
        f"Peak Demand: {structured['peak_demand_mw']} MW at {structured['peak_time']}\n"
        f"Grid Headroom: {structured['headroom_mw']} MW\n"
        f"Grid Utilization: {structured['utilization_pct']}%\n"
        f"Critical Zones: {', '.join(structured['critical_zones']) or 'None'}\n"
        f"High-Risk Zones: {', '.join(structured['high_zones']) or 'None'}\n"
        f"Delhi Temperature: {structured['demand_drivers']['temperature']}\n"
        f"Delhi Humidity: {structured['demand_drivers']['humidity']}\n"
        f"Cooling Load: {structured['demand_drivers']['cooling_degree']}\n\n"
        "RULES: Write 2-3 sentences for a grid operator. "
        "Only use numbers from the data above. "
        "Mention weather driver if temperature is above 30C. "
        "Include the action code. Be concise and actionable.\n\n"
        "Write the operator recommendation:"
    )

    try:
        if GENAI_NEW:
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt,
            )
            return response.text.strip()
        else:
            import google.generativeai as legacy_genai
            model = legacy_genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini LLM call failed: {e}")
        return structured["action_text"]


def generate_recommendation(
    grid_risk: dict,
    zone_risks: list,
    weather: dict,
    peak_info: dict,
) -> dict:
    """Full recommendation pipeline: structured + LLM explanation."""
    structured      = _build_structured_recommendation(grid_risk, zone_risks, weather, peak_info)
    llm_explanation = _explain_with_llm(structured, weather)
    return {**structured, "llm_explanation": llm_explanation}
