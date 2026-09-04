"""
scripts/render_build.py
------------------------
Render-optimised build script.
Runs the full pipeline but with memory-efficient settings for free tier (512MB RAM).
Called by Render's build command:
  python scripts/render_build.py
"""
import subprocess
import sys
import os
from pathlib import Path

BASE = Path(__file__).parent.parent

def run(cmd, cwd=None):
    print(f"\n>>> {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd or BASE)
    if result.returncode != 0:
        print(f"FAILED: {cmd}")
        sys.exit(1)

print("=" * 60)
print("  DELHI GRID INTELLIGENCE — RENDER BUILD")
print("=" * 60)

# Step 1: Fetch historical weather (cached if already exists)
weather_file = BASE / "data" / "weather" / "delhi_weather_historical.csv"
if weather_file.exists():
    print(f"\n[SKIP] Weather data already in repo ({weather_file.stat().st_size // 1024} KB)")
else:
    print("\n[1/4] Fetching historical weather...")
    run("python scripts/fetch_weather_standalone.py --start 2023-04-01 --end 2026-01-31")

# Step 2: Generate demo load data
raw_file = BASE / "data" / "raw" / "load_data.csv"
if raw_file.exists():
    print(f"\n[SKIP] Load data already exists ({raw_file.stat().st_size // 1024} KB)")
else:
    print("\n[2/4] Generating demo load data...")
    run("python scripts/generate_demo_data.py")

# Step 3: Preprocess
hourly_file = BASE / "data" / "processed" / "load_hourly.csv"
if hourly_file.exists():
    print(f"\n[SKIP] Processed data already exists")
else:
    print("\n[3/4] Preprocessing load data...")
    run("python scripts/preprocess_load.py")

# Step 4: Build features
feat_file = BASE / "data" / "processed" / "features_hourly.csv"
if feat_file.exists():
    print(f"\n[SKIP] Features already built")
else:
    print("\n[4/4] Building features...")
    run("python scripts/build_features.py")

# Step 5: Train model (always re-train to use latest data)
model_file = BASE / "models" / "forecast_model.pkl"
if model_file.exists():
    print(f"\n[SKIP] Model already trained ({model_file.stat().st_size // 1024 // 1024} MB)")
else:
    print("\n[5/5] Training model (this takes 3-5 min on Render free tier)...")
    # Set env var to use fewer trees for memory efficiency on free tier
    os.environ["RENDER_BUILD"] = "1"
    run("python scripts/train_model.py")

print("\n" + "=" * 60)
print("  BUILD COMPLETE")
print("=" * 60)
