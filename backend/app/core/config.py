"""
app/core/config.py
------------------
Central configuration loaded from .env.
All other modules import from here — never read os.environ directly elsewhere.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from backend root
load_dotenv(Path(__file__).parent.parent.parent / ".env")


class Settings:
    # ── API Keys ──────────────────────────────────────────────────────────────
    GEMINI_API_KEY: str     = os.getenv("GEMINI_API_KEY", "")
    SUPABASE_URL:   str     = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY:   str     = os.getenv("SUPABASE_KEY", "")

    # ── App ───────────────────────────────────────────────────────────────────
    APP_ENV:  str = os.getenv("APP_ENV", "development")
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))

    # ── Grid capacity (demo / configurable — NOT official Delhi limits) ───────
    DELHI_GRID_CAPACITY_MW: float = float(os.getenv("DELHI_GRID_CAPACITY_MW", "8000"))
    ZONE_CAPACITY_MW: dict = {
        "delhi_north":     float(os.getenv("NORTH_CAPACITY_MW",    "1800")),
        "delhi_south":     float(os.getenv("SOUTH_CAPACITY_MW",    "2200")),
        "delhi_east":      float(os.getenv("EAST_CAPACITY_MW",     "1200")),
        "delhi_west":      float(os.getenv("WEST_CAPACITY_MW",     "1600")),
        "delhi_central":   float(os.getenv("CENTRAL_CAPACITY_MW",  "600")),
        "delhi_northeast": float(os.getenv("NORTHEAST_CAPACITY_MW","600")),
    }

    # ── Risk thresholds (fraction of capacity) ────────────────────────────────
    RISK_LOW:      float = float(os.getenv("RISK_LOW_THRESHOLD",    "0.60"))
    RISK_MEDIUM:   float = float(os.getenv("RISK_MEDIUM_THRESHOLD", "0.75"))
    RISK_HIGH:     float = float(os.getenv("RISK_HIGH_THRESHOLD",   "0.90"))

    # ── Open-Meteo ────────────────────────────────────────────────────────────
    OPEN_METEO_ARCHIVE_URL:  str = os.getenv("OPEN_METEO_ARCHIVE_URL",
                                             "https://archive-api.open-meteo.com/v1/archive")
    OPEN_METEO_FORECAST_URL: str = os.getenv("OPEN_METEO_FORECAST_URL",
                                             "https://api.open-meteo.com/v1/forecast")

    # ── Data / model paths ────────────────────────────────────────────────────
    BASE_DIR:        Path = Path(__file__).parent.parent.parent
    RAW_DATA_DIR:    Path = BASE_DIR / os.getenv("RAW_DATA_DIR",       "data/raw")
    PROCESSED_DIR:   Path = BASE_DIR / os.getenv("PROCESSED_DATA_DIR", "data/processed")
    WEATHER_DIR:     Path = BASE_DIR / os.getenv("WEATHER_DATA_DIR",   "data/weather")
    MODELS_DIR:      Path = BASE_DIR / os.getenv("MODELS_DIR",         "models")

    # ── Delhi zone weather coordinates ────────────────────────────────────────
    ZONE_COORDS: dict = {
        "delhi_north":     {"lat": 28.717047, "lon": 77.054794, "has_humidity": False},
        "delhi_south":     {"lat": 28.506150, "lon": 77.201360, "has_humidity": False},
        "delhi_east":      {"lat": 28.646748, "lon": 77.274800, "has_humidity": True},
        "delhi_west":      {"lat": 28.646748, "lon": 77.069560, "has_humidity": True},
        "delhi_central":   {"lat": 28.646748, "lon": 77.172180, "has_humidity": True},
        "delhi_northeast": {"lat": 28.717047, "lon": 77.260280, "has_humidity": True},
    }

    # ── Timezone ──────────────────────────────────────────────────────────────
    TIMEZONE: str = "Asia/Kolkata"
    UTC_OFFSET_HOURS: float = 5.5


settings = Settings()
