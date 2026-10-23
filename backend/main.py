"""
FastAPI Backend Application - Smart Goggle System
Endpoints:
  GET  /api/health
  POST /api/sensor
  GET  /api/environment
  GET  /api/latest
  GET  /api/history
  POST /api/predict
  GET  /api/explanation
  GET  /api/ml/results
  GET  /api/ml/live
"""

import os
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from backend.config import BACKEND_HOST, BACKEND_PORT, RESULTS_DIR
from backend.models_schema import (
    SensorInput,
    EnvironmentData,
    AQIPrediction,
    PhysiologicalPrediction,
    RiskAssessment,
    ExplanationDetail,
    SensorTelemetryResponse,
    MLResultsResponse,
)
from backend.services.aqi_service import aqi_service
from backend.services.ml_service import ml_service
from backend.services.risk_engine import risk_engine
from backend.services.history_service import history_service

app = FastAPI(
    title="Smart Goggle AI Health & Environment Monitoring API",
    version="2.1.0",
    description="Research Demonstration System uniting ESP32 BLE physiological monitoring, Open-Meteo GPS air quality, dual ML classifiers, and SHAP Explainable AI."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cached latest AQI prediction object
_cached_aqi_pred: Optional[AQIPrediction] = None
_cached_env_shap: List[Any] = []

@app.get("/api/health", summary="Health Check")
async def health_check():
    return {
        "status": "online",
        "service": "Smart Goggle Backend API",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "models_loaded": {
            "live_aqi_model": ml_service.live_aqi_model is not None,
            "offline_aqi_model": ml_service.offline_aqi_model is not None,
            "stress_model": ml_service.stress_model is not None
        },
        "disclaimer": "PROTOTYPE SYSTEM ONLY. Not for medical diagnosis."
    }

@app.post("/api/sensor", response_model=SensorTelemetryResponse, summary="Ingest ESP32 Physiological Sensor Data")
async def ingest_sensor_data(sensor: SensorInput):
    """
    Primary physiological ingestion endpoint called when ESP32 transmits vitals:
    Triggers physiological stress ML inference with rolling history buffer.
    Combines with latest ambient environment in the risk engine.
    """
    global _cached_aqi_pred, _cached_env_shap
    try:
        # 1. Independent Trigger: Run Physiological Stress ML Model on ESP32 packet
        stress_pred, phys_shap = ml_service.predict_stress(
            sensor, history_service.rolling_sensor_buffer
        )

        # 2. Obtain current environmental context
        if aqi_service._cached_data is not None and _cached_aqi_pred is not None:
            env = aqi_service._cached_data
            aqi_pred = _cached_aqi_pred
            env_shap = _cached_env_shap
        else:
            # First run or fresh fetch
            env = await aqi_service.fetch_current_environment(
                latitude=sensor.latitude,
                longitude=sensor.longitude
            )
            aqi_pred, env_shap = ml_service.predict_aqi(env)
            _cached_aqi_pred = aqi_pred
            _cached_env_shap = env_shap

        # 3. Compute Personalized Prototype Risk
        risk = risk_engine.calculate_risk(sensor, env, aqi_pred, stress_pred)

        # 4. Build SHAP explanation
        explanation = ExplanationDetail(
            environmental_factors=env_shap,
            physiological_factors=phys_shap,
            model_contribution_note=(
                "Feature impacts reflect model contribution weights calculated via SHAP TreeExplainer, "
                "not causal medical diagnoses."
            )
        )

        # 5. Formulate full response
        response = SensorTelemetryResponse(
            success=True,
            timestamp=datetime.now(timezone.utc).strftime("%H:%M:%S"),
            sensor_data=sensor,
            environment=env,
            aqi_prediction=aqi_pred,
            physiological_prediction=stress_pred,
            personalized_risk=risk,
            explanation=explanation,
        )

        # 6. Record to history
        history_service.record_telemetry(response)

        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing sensor telemetry: {str(e)}"
        )

@app.get("/api/environment", response_model=EnvironmentData, summary="Fetch Live Environment & Trigger AQI ML Inference")
async def get_environment(
    lat: Optional[float] = Query(None, description="Current latitude"),
    lon: Optional[float] = Query(None, description="Current longitude")
):
    """
    Independent environmental ingestion trigger:
    Called when smartphone GPS updates or user requests environmental monitoring.
    Fetches Open-Meteo live pollutants and executes Live AQI ML model.
    """
    global _cached_aqi_pred, _cached_env_shap
    env = await aqi_service.fetch_current_environment(latitude=lat, longitude=lon)
    aqi_pred, env_shap = ml_service.predict_aqi(env)
    _cached_aqi_pred = aqi_pred
    _cached_env_shap = env_shap
    return env

@app.get("/api/latest", summary="Get Latest Recorded Telemetry State")
async def get_latest_telemetry():
    latest = history_service.get_latest()
    if latest is None:
        default_sensor = SensorInput(bpm=76.0, temperature=36.4, finger=True, fall=False, emergency=False)
        return await ingest_sensor_data(default_sensor)
    return latest

@app.get("/api/history", summary="Get Historical Readings for Charts")
async def get_history(limit: int = 50):
    return history_service.get_history(limit=limit)

@app.post("/api/predict", summary="Simulate Ad-hoc Prediction")
async def adhoc_predict(sensor: SensorInput, env: Optional[EnvironmentData] = None):
    if env is None:
        env = await aqi_service.fetch_current_environment(latitude=sensor.latitude, longitude=sensor.longitude)
    aqi_pred, env_shap = ml_service.predict_aqi(env)
    stress_pred, phys_shap = ml_service.predict_stress(sensor)
    risk = risk_engine.calculate_risk(sensor, env, aqi_pred, stress_pred)
    return {
        "aqi_prediction": aqi_pred,
        "stress_prediction": stress_pred,
        "personalized_risk": risk
    }

@app.get("/api/explanation", summary="Get Latest Model Explanation")
async def get_explanation():
    latest = history_service.get_latest()
    if latest:
        return latest.explanation
    env = await aqi_service.fetch_current_environment()
    _, env_shap = ml_service.predict_aqi(env)
    _, phys_shap = ml_service.predict_stress(SensorInput(bpm=76.0, temperature=36.4))
    return ExplanationDetail(
        environmental_factors=env_shap,
        physiological_factors=phys_shap,
        model_contribution_note="Prototype SHAP TreeExplainer feature importance weights."
    )

@app.get("/api/ml/results", summary="Get Verified Static ML Evaluation Benchmarks")
async def get_ml_results():
    """
    Returns authentic training and evaluation results directly from generated JSON artifacts:
    - Offline AQI Model (12 features)
    - Live AQI Model (6 features)
    - Physiological Stress Model (35 subjects GroupSplit)
    """
    offline_aqi = {}
    live_aqi = {}
    stress = {}

    p_off = os.path.join(RESULTS_DIR, "aqi_results.json")
    if os.path.exists(p_off):
        with open(p_off, "r") as f:
            offline_aqi = json.load(f)

    p_live = os.path.join(RESULTS_DIR, "live_aqi_results.json")
    if os.path.exists(p_live):
        with open(p_live, "r") as f:
            live_aqi = json.load(f)

    p_stress = os.path.join(RESULTS_DIR, "stress_results.json")
    if os.path.exists(p_stress):
        with open(p_stress, "r") as f:
            stress = json.load(f)

    return {
        "offline_aqi_model": offline_aqi,
        "live_aqi_model": live_aqi,
        "stress_model": stress
    }

@app.get("/api/ml/live", summary="Get Latest Real-Time ML Inferences & Execution Diagnostics")
async def get_live_ml():
    """
    Returns real-time execution telemetry for both independent ML inference pipelines:
    - Physiological ML (last ESP32 packet inference)
    - Environmental ML (last Open-Meteo GPS air quality inference)
    - Live model class names, input features, probabilities, and SHAP weights.
    """
    return ml_service.get_live_ml_diagnostics()

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host=BACKEND_HOST, port=BACKEND_PORT, reload=False)
