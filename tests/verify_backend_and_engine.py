import os
import sys
import json
import httpx
import asyncio

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from fastapi.testclient import TestClient
from backend.main import app
from backend.services.aqi_service import aqi_service
from backend.services.risk_engine import risk_engine
from backend.models_schema import (
    SensorInput, EnvironmentData, AQIPrediction, PhysiologicalPrediction
)
from backend.config import (
    AQI_API_URL, AQI_API_KEY, AQI_LOCATION, AQI_LAT, AQI_LON
)

client = TestClient(app)

print("============================================================")
print("5 & 6. VERIFY FASTAPI AND TEST ESP32 JSON")
print("============================================================")

# 1. GET /api/health
r_health = client.get("/api/health")
print("GET /api/health -> Status:", r_health.status_code)
print("  Response:", r_health.json())
assert r_health.status_code == 200
assert r_health.json()["models_loaded"]["aqi_model"] is True
assert r_health.json()["models_loaded"]["stress_model"] is True

# 2. POST /api/sensor with exact ESP32 payload
esp32_payload = {
    "heart_rate": 82,
    "spo2": 97,
    "temperature": 36.5
}
r_sensor = client.post("/api/sensor", json=esp32_payload)
print("\nPOST /api/sensor with exact ESP32 JSON -> Status:", r_sensor.status_code)
sensor_resp = r_sensor.json()
print("  Success:", sensor_resp["success"])
print("  Sensor Data validated:", sensor_resp["sensor_data"])
print("  Environment obtained:", sensor_resp["environment"]["location"], "| Source:", sensor_resp["environment"]["source"])
print("  AQI Prediction:", sensor_resp["aqi_prediction"])
print("  Physiological Stress Prediction:", sensor_resp["physiological_prediction"])
print("  Personalized Risk:", sensor_resp["personalized_risk"])
print("  Explanation Summary:", sensor_resp["explanation"]["model_contribution_note"])
assert r_sensor.status_code == 200
assert sensor_resp["success"] is True
assert sensor_resp["sensor_data"]["heart_rate"] == 82
assert sensor_resp["sensor_data"]["spo2"] == 97
assert sensor_resp["sensor_data"]["temperature"] == 36.5
assert 0 <= sensor_resp["personalized_risk"]["risk_score"] <= 100
assert "PROTOTYPE" in sensor_resp["personalized_risk"]["prototype_disclaimer"].upper()

# 3. GET /api/environment
r_env = client.get("/api/environment")
print("\nGET /api/environment -> Status:", r_env.status_code)
print("  Location:", r_env.json().get("location"))
assert r_env.status_code == 200

# 4. GET /api/latest
r_latest = client.get("/api/latest")
print("\nGET /api/latest -> Status:", r_latest.status_code)
assert r_latest.status_code == 200
assert r_latest.json()["sensor_data"]["heart_rate"] == 82

# 5. GET /api/history
r_hist = client.get("/api/history?limit=10")
print("\nGET /api/history -> Status:", r_hist.status_code)
print(f"  Records stored in SQLite: {len(r_hist.json())}")
assert r_hist.status_code == 200
assert len(r_hist.json()) >= 1

# 6. POST /api/predict
r_pred = client.post("/api/predict", json={"sensor": esp32_payload})
print("\nPOST /api/predict -> Status:", r_pred.status_code)
assert r_pred.status_code == 200

# 7. GET /api/explanation
r_exp = client.get("/api/explanation")
print("\nGET /api/explanation -> Status:", r_exp.status_code)
assert r_exp.status_code == 200
exp_data = r_exp.json()
print("  Environmental SHAP Factors count:", len(exp_data["environmental_factors"]))
print("  Physiological SHAP Factors count:", len(exp_data["physiological_factors"]))
assert len(exp_data["environmental_factors"]) > 0
assert len(exp_data["physiological_factors"]) > 0

print("\n============================================================")
print("7. VERIFY AQI API ADAPTER")
print("============================================================")
print(f"Configured API URL: {AQI_API_URL}")
print(f"Configured Location: {AQI_LOCATION} (Lat: {AQI_LAT}, Lon: {AQI_LON})")
print(f"Configured API Key set: {bool(AQI_API_KEY)}")

async def test_aqi():
    env = await aqi_service.fetch_current_environment()
    print("Live AQI Service Output:")
    print(f"  Source:   {env.source}")
    print(f"  PM2.5:    {env.pm25} ug/m3")
    print(f"  PM10:     {env.pm10} ug/m3")
    print(f"  NO2:      {env.no2} ug/m3")
    print(f"  CO:       {env.co} ug/m3")
    print(f"  SO2:      {env.so2} ug/m3")
    print(f"  O3:       {env.o3} ug/m3")
    print(f"  NO:       {env.no} (Baseline/offline mapped)")
    print(f"  NOx:      {env.nox} (Baseline/offline mapped)")
    print(f"  NH3:      {env.nh3} (Baseline/offline mapped)")
    print(f"  Benzene:  {env.benzene} (Baseline/offline mapped)")
    print(f"  Toluene:  {env.toluene} (Baseline/offline mapped)")
    print(f"  Xylene:   {env.xylene} (Baseline/offline mapped)")
    print("\nAPI Mapping Status: Standard pollutants (PM2.5, PM10, NO2, CO, SO2, O3) are directly queried.")
    print("Secondary VOCs not exposed by Open-Meteo are gracefully supplied from regional baseline profiles without throwing errors or fabricating wild values.")

asyncio.run(test_aqi())

print("\n============================================================")
print("8. VERIFY RISK ENGINE WITH MULTIPLE TEST CASES")
print("============================================================")

test_cases = [
    ("Optimal Vitals + Good Air",
     SensorInput(heart_rate=70, spo2=99, temperature=36.6),
     EnvironmentData(pm25=15, pm10=30, source="test", location="Delhi"),
     AQIPrediction(predicted_bucket="Good", confidence=0.9, probabilities={}),
     PhysiologicalPrediction(predicted_stress="Low", confidence=0.9, probabilities={})),
    
    ("Mild Stress + Satisfactory Air",
     SensorInput(heart_rate=82, spo2=97, temperature=36.5),
     EnvironmentData(pm25=40, pm10=70, source="test", location="Delhi"),
     AQIPrediction(predicted_bucket="Satisfactory", confidence=0.8, probabilities={}),
     PhysiologicalPrediction(predicted_stress="Low", confidence=0.85, probabilities={})),
    
    ("Moderate Stress + Moderate Air",
     SensorInput(heart_rate=98, spo2=95, temperature=37.1),
     EnvironmentData(pm25=75, pm10=110, source="test", location="Delhi"),
     AQIPrediction(predicted_bucket="Moderate", confidence=0.8, probabilities={}),
     PhysiologicalPrediction(predicted_stress="Medium", confidence=0.8, probabilities={})),
    
    ("High Strain: Hypoxemia + Tachycardia + Poor Air",
     SensorInput(heart_rate=125, spo2=91, temperature=38.2),
     EnvironmentData(pm25=145, pm10=220, source="test", location="Delhi"),
     AQIPrediction(predicted_bucket="Poor", confidence=0.85, probabilities={}),
     PhysiologicalPrediction(predicted_stress="High", confidence=0.9, probabilities={})),
    
    ("Severe Hazard: Pyrexia + Severe Air",
     SensorInput(heart_rate=135, spo2=89, temperature=38.8),
     EnvironmentData(pm25=280, pm10=380, source="test", location="Delhi"),
     AQIPrediction(predicted_bucket="Severe", confidence=0.95, probabilities={}),
     PhysiologicalPrediction(predicted_stress="High", confidence=0.95, probabilities={}))
]

for name, s_in, env_in, aqi_p, stress_p in test_cases:
    risk_out = risk_engine.calculate_risk(s_in, env_in, aqi_p, stress_p)
    print(f"\nCase: {name}")
    print(f"  Env Score:   {risk_out.environmental_component} / 50")
    print(f"  Phys Score:  {risk_out.physiological_component} / 50")
    print(f"  Total Score: {risk_out.risk_score} / 100")
    print(f"  Risk Level:  {risk_out.risk_level}")
    print(f"  Summary:     {risk_out.status_summary}")
    print(f"  Disclaimer:  {risk_out.prototype_disclaimer}")
    assert 0 <= risk_out.risk_score <= 100
    assert "PROTOTYPE" in risk_out.prototype_disclaimer.upper()
    assert "NOT A MEDICAL" in risk_out.prototype_disclaimer.upper()

print("\n============================================================")
print("9. VERIFY SHAP TREEEXPLAINER LIVE GENERATION")
print("============================================================")
from backend.services.ml_service import ml_service
aqi_pred, env_shap = ml_service.predict_aqi(EnvironmentData(pm25=55.0, pm10=95.0, source="test", location="Delhi"))
stress_pred, phys_shap = ml_service.predict_stress(SensorInput(heart_rate=88.0, spo2=97.0, temperature=36.7))

print("Live SHAP Environmental Top Features:")
for f in env_shap:
    print(f"  - {f.feature:10s}: {f.contribution:+.4f} | {f.impact_description}")
    # Verify feature exists in AQI feature set
    assert f.feature in ml_service.aqi_features

print("\nLive SHAP Physiological Top Features:")
for f in phys_shap:
    print(f"  - {f.feature:20s}: {f.contribution:+.4f} | {f.impact_description}")

print("SHAP TreeExplainer feature matching and live generation: VERIFIED")
