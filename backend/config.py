import os
from pathlib import Path

# Try to load dotenv, fallback to manual parsing if not installed
env_path = Path(__file__).resolve().parent / ".env"
if env_path.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=env_path)
    except ImportError:
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())

AQI_API_URL = os.getenv("AQI_API_URL", "https://air-quality-api.open-meteo.com/v1/air-quality")
AQI_API_KEY = os.getenv("AQI_API_KEY", "")
AQI_LOCATION = os.getenv("AQI_LOCATION", "Delhi")
AQI_LAT = float(os.getenv("AQI_LAT", "28.6139"))
AQI_LON = float(os.getenv("AQI_LON", "77.2090"))
BACKEND_HOST = os.getenv("BACKEND_HOST", "0.0.0.0")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
RESULTS_DIR = BASE_DIR / "ml_results"
SHAP_DIR = RESULTS_DIR / "shap"
LIVE_PREDICTIONS_DIR = RESULTS_DIR / "live_predictions"
LIVE_PREDICTIONS_FILE = LIVE_PREDICTIONS_DIR / "live_predictions.jsonl"
LIVE_PREDICTIONS_DIR.mkdir(parents=True, exist_ok=True)
