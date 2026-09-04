# Delhi Grid Intelligence — Quick Start
# ======================================

## Hackathon: PS-1 — AI-based Electricity Demand Prediction System

### Architecture
```
Real Delhi Load Data (5-min, Apr 2023–Jan 2026)
         ↓ [Clean + validate + hourly aggregate]
Historical Weather (Open-Meteo Archive, cached ✅)
         ↓ [Feature engineering: lag + rolling + time + weather]
XGBoost Demand Forecast Model
         ↓
FastAPI Backend (7 endpoints)
         ↓
Risk Engine → Recommendation Engine → Gemini LLM Explanation
         ↓
React Dashboard (Vite + Tailwind + Recharts)
```

---

## Step 1 — Drop load_data.csv

```
Copy load_data.csv → backend/data/raw/load_data.csv
```

---

## Step 2 — Run the ML pipeline

```powershell
cd backend

# Inspect load data
python scripts/inspect_load_data.py

# Preprocess (5-min → hourly, clean gaps)
python scripts/preprocess_load.py

# Build features (lag + rolling + weather merge)
# Weather is already cached at data/weather/delhi_weather_historical.csv ✅
python scripts/build_features.py

# Train model (XGBoost vs RandomForest + baseline comparison)
python scripts/train_model.py
```

---

## Step 3 — Start the backend

```powershell
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: http://localhost:8000/docs

---

## Step 4 — Start the frontend

```powershell
cd frontend
npm install
npm run dev
```

Dashboard: http://localhost:5173

---

## Environment Variables (already in .env)

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Gemini LLM for recommendation explanations |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_KEY` | Supabase publishable key |
| `DELHI_GRID_CAPACITY_MW` | Demo capacity (default: 8000 MW) |
| `RISK_HIGH_THRESHOLD` | High-risk threshold (default: 0.90 = 90%) |

---

## API Endpoints

| Endpoint | Description |
|---|---|
| `GET /api/dashboard` | Full dashboard data (aggregated) |
| `GET /api/forecast?hours=24` | N-hour demand forecast |
| `GET /api/weather` | Current + forecast weather (6 zones) |
| `GET /api/alerts` | Active capacity risk alerts |
| `GET /api/recommendations` | AI recommendation + LLM explanation |
| `GET /api/zones` | All Delhi zone status |
| `GET /api/zones/{zone_id}` | Zone detail + 24h forecast |
| `POST /api/predict` | On-demand inference |

---

## Data Files (what's where)

| File | Status | Description |
|---|---|---|
| `data/raw/load_data.csv` | ⏳ Drop here | Delhi load data (5-min) |
| `data/weather/delhi_weather_historical.csv` | ✅ FETCHED | 24,888 rows, Apr 2023–Jan 2026 |
| `data/processed/load_hourly.csv` | After step 2 | Cleaned hourly aggregates |
| `data/processed/features_hourly.csv` | After step 2 | Full feature matrix |
| `models/forecast_model.pkl` | After step 2 | Trained XGBoost model |

---

## Disclaimer (Important for hackathon)

> Grid capacity thresholds are **configurable demo values** set in `.env`.
> They are **not** official Delhi/SLDC capacity figures.
> Weather data is from Open-Meteo API — `Asia/Kolkata` timezone.
> This is a **decision-support system** — all grid actions require human approval.

---

## Tech Stack

| Layer | Technology |
|---|---|
| ML | XGBoost + scikit-learn + pandas |
| Backend | FastAPI + uvicorn + python-dotenv |
| LLM | Google Gemini 1.5 Flash (`google-genai`) |
| Weather | Open-Meteo Archive + Forecast API |
| Frontend | React 18 + Vite + Tailwind CSS + Recharts |
| Database | Supabase (PostgreSQL) |
| Deploy | Render (backend) + Vercel (frontend) |
