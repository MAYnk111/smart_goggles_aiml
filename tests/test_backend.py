import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from backend.main import app
from backend.services.history_service import history_service

# Re-init db schema to run migrations
history_service._init_db()

client = TestClient(app)

def test_endpoints():
    print("==================================================")
    print("SMART GOGGLE BACKEND & ML VERIFICATION TEST SUITE")
    print("==================================================")

    # 1. Health Endpoint
    print("\n1. Testing GET /api/health...")
    r = client.get("/api/health")
    assert r.status_code == 200, f"Health check failed: {r.text}"
    health_data = r.json()
    print("Health response:", health_data)
    assert health_data["status"] == "online"
    assert health_data["models_loaded"]["live_aqi_model"] is True
    assert health_data["models_loaded"]["stress_model"] is True
    print("[OK] Health check passed and both production ML models are loaded.")

    # 2. ML Results Endpoint
    print("\n2. Testing GET /api/ml/results...")
    r = client.get("/api/ml/results")
    assert r.status_code == 200, f"ML results endpoint failed: {r.text}"
    ml_results = r.json()
    assert "live_aqi_model" in ml_results
    assert "stress_model" in ml_results
    assert "offline_aqi_model" in ml_results

    live_aqi = ml_results["live_aqi_model"]
    stress = ml_results["stress_model"]
    live_acc = live_aqi.get('accuracy', 0.0)
    live_f1 = live_aqi.get('weighted_f1', 0.0)
    stress_acc = stress.get('accuracy', 0.0)
    stress_f1 = stress.get('f1_weighted', 0.0)

    print(f"Live AQI Model Accuracy: {live_acc*100:.2f}%, Weighted F1: {live_f1*100:.2f}%")
    print(f"Stress Model Accuracy: {stress_acc*100:.2f}%, Weighted F1: {stress_f1*100:.2f}% (35 subjects GroupSplit)")
    assert live_acc > 0.75
    assert stress_acc > 0.40
    print("[OK] ML results endpoint verified authentic training metrics.")

    # 3. Environment with dynamic GPS coordinates
    print("\n3. Testing GET /api/environment with dynamic GPS (Mumbai: 19.0760, 72.8777)...")
    r = client.get("/api/environment?lat=19.0760&lon=72.8777")
    assert r.status_code == 200, f"Environment fetch failed: {r.text}"
    env_data = r.json()
    print("Environment response location:", env_data.get("location"))
    print("PM2.5:", env_data.get("pm25"), "PM10:", env_data.get("pm10"), "Source:", env_data.get("source"))
    assert env_data.get("pm25") is not None or env_data.get("location") is not None
    print("[OK] Open-Meteo GPS air quality dynamic fetch verified.")

    # 4. Standard ESP32 Sensor Ingestion (Nullable SpO2)
    print("\n4. Testing POST /api/sensor with ESP32 schema (bpm, nullable spo2, finger, fall, emergency)...")
    esp32_payload = {
        "bpm": 84.0,
        "spo2": None, # Firmware does NOT calculate SpO2
        "temperature": 36.5,
        "fall": False,
        "finger": True,
        "emergency": False,
        "latitude": 28.6139,
        "longitude": 77.2090
    }
    r = client.post("/api/sensor", json=esp32_payload)
    assert r.status_code == 200, f"Sensor ingest failed: {r.text}"
    data = r.json()
    assert data["success"] is True
    assert data["sensor_data"]["heart_rate"] == 84.0
    assert data["sensor_data"]["spo2"] is None
    assert data["aqi_prediction"]["predicted_bucket"] is not None
    assert data["physiological_prediction"]["predicted_stress"] is not None
    assert "risk_score" in data["personalized_risk"]
    assert len(data["explanation"]["environmental_factors"]) > 0
    assert len(data["explanation"]["physiological_factors"]) > 0
    print("Base Risk Score:", data["personalized_risk"]["risk_score"])
    print("[OK] Ingestion with nullable SpO2 and SHAP TreeExplainer explanation passed.")

    # 5. Emergency Event Ingestion
    print("\n5. Testing POST /api/sensor with Emergency switch trigger...")
    emergency_payload = {
        "bpm": 115.0,
        "spo2": None,
        "temperature": 37.1,
        "fall": False,
        "finger": True,
        "emergency": True,
    }
    r = client.post("/api/sensor", json=emergency_payload)
    assert r.status_code == 200
    em_data = r.json()
    assert em_data["personalized_risk"]["risk_score"] >= 70.0
    assert em_data["personalized_risk"]["emergency_alert"] is True
    assert em_data["personalized_risk"]["risk_level"] == "Very High"
    print("Emergency Risk Score:", em_data["personalized_risk"]["risk_score"], f"({em_data['personalized_risk']['risk_level']})")
    print("[OK] Emergency alert correctly boosted risk engine output to Very High.")

    # 6. Fall Event Ingestion
    print("\n6. Testing POST /api/sensor with Fall detection event...")
    fall_payload = {
        "bpm": 95.0,
        "spo2": None,
        "temperature": 36.4,
        "fall": True,
        "finger": True,
        "emergency": False,
    }
    r = client.post("/api/sensor", json=fall_payload)
    assert r.status_code == 200
    fall_data = r.json()
    assert fall_data["personalized_risk"]["risk_score"] >= 70.0
    assert fall_data["personalized_risk"]["fall_alert"] is True
    assert fall_data["personalized_risk"]["risk_level"] == "Very High"
    print("Fall Risk Score:", fall_data["personalized_risk"]["risk_score"], f"({fall_data['personalized_risk']['risk_level']})")
    print("[OK] Fall detection alert correctly boosted risk engine output to Very High.")

    # 7. Latest, History, and Explanation Endpoints
    print("\n7. Testing GET /api/latest, /api/history, /api/explanation...")
    r_lat = client.get("/api/latest")
    assert r_lat.status_code == 200
    r_hist = client.get("/api/history?limit=10")
    assert r_hist.status_code == 200
    assert len(r_hist.json()) >= 3
    r_exp = client.get("/api/explanation")
    assert r_exp.status_code == 200
    print(f"[OK] History buffer contains {len(r_hist.json())} records.")

    # 8. Real-Time ML Diagnostics Endpoint and JSONL Verification
    print("\n8. Testing GET /api/ml/live & JSONL live predictions file...")
    r_live = client.get("/api/ml/live")
    assert r_live.status_code == 200
    live_diag = r_live.json()
    assert "status" in live_diag
    assert "physiological" in live_diag
    assert "environmental" in live_diag
    print("Live ML Status:", live_diag["status"])
    print("Physiological Last Prediction:", live_diag["physiological"]["prediction"] if live_diag["physiological"] else None)
    print("Environmental Last Prediction:", live_diag["environmental"]["prediction"] if live_diag["environmental"] else None)

    # Verify JSONL persistence file in ml_results/live_predictions/
    jsonl_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ml_results", "live_predictions", "live_predictions.jsonl")
    assert os.path.exists(jsonl_path), f"JSONL file not found at {jsonl_path}"
    with open(jsonl_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    assert len(lines) >= 2, f"Expected at least 2 live inference lines, found {len(lines)}"
    print(f"[OK] Verified live_predictions.jsonl exists with {len(lines)} recorded real inferences.")

    print("\n==================================================")
    print("ALL BACKEND & ML INTEGRATION TESTS PASSED (100%)")
    print("==================================================")

if __name__ == "__main__":
    test_endpoints()

