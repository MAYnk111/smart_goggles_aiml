from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, model_validator

class SensorInput(BaseModel):
    """
    Physiological payload from ESP32 or Flutter:
    {
      "bpm": 82,            // or "heart_rate": 82
      "spo2": null,         // nullable, ESP32 does not calculate SpO2
      "temperature": 36.5,  // nullable
      "fall": false,
      "finger": true,
      "emergency": false,
      "latitude": 28.6139,  // optional GPS
      "longitude": 77.2090
    }
    """
    heart_rate: Optional[float] = None
    bpm: Optional[float] = None
    spo2: Optional[float] = None
    temperature: Optional[float] = None
    fall: bool = False
    finger: bool = True
    emergency: bool = False
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Normalize bpm -> heart_rate
            if "heart_rate" not in data or data["heart_rate"] is None:
                if "bpm" in data and data["bpm"] is not None:
                    data["heart_rate"] = float(data["bpm"])
            elif "bpm" not in data or data["bpm"] is None:
                if "heart_rate" in data and data["heart_rate"] is not None:
                    data["bpm"] = float(data["heart_rate"])
        return data

    def get_effective_hr(self) -> float:
        if self.heart_rate is not None and self.heart_rate > 0:
            return float(self.heart_rate)
        if self.bpm is not None and self.bpm > 0:
            return float(self.bpm)
        return 75.0

class EnvironmentData(BaseModel):
    pm25: Optional[float] = None
    pm10: Optional[float] = None
    no: Optional[float] = None
    no2: Optional[float] = None
    nox: Optional[float] = None
    nh3: Optional[float] = None
    co: Optional[float] = None
    so2: Optional[float] = None
    o3: Optional[float] = None
    benzene: Optional[float] = None
    toluene: Optional[float] = None
    xylene: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    source: str = "Open-Meteo Air Quality API"
    location: str = "Current Location"
    updated_at: Optional[str] = None

    def get_active_pollutants(self) -> Dict[str, float]:
        res = {}
        if self.pm25 is not None: res["PM2.5"] = self.pm25
        if self.pm10 is not None: res["PM10"] = self.pm10
        if self.no2 is not None: res["NO2"] = self.no2
        if self.co is not None: res["CO"] = self.co
        if self.so2 is not None: res["SO2"] = self.so2
        if self.o3 is not None: res["O3"] = self.o3
        return res

class AQIPrediction(BaseModel):
    model_type: str = "Live Open-Meteo Model"
    predicted_bucket: str
    confidence: float
    probabilities: Dict[str, float]

class PhysiologicalPrediction(BaseModel):
    predicted_stress: str
    confidence: float
    probabilities: Dict[str, float]

class RiskAssessment(BaseModel):
    risk_score: float = Field(..., ge=0.0, le=100.0)
    risk_level: str
    environmental_component: float
    physiological_component: float
    vital_modifiers: Dict[str, float]
    status_summary: str
    fall_alert: bool = False
    emergency_alert: bool = False
    finger_status: bool = True
    prototype_disclaimer: str = (
        "COLLEGE PROTOTYPE / RESEARCH DEMONSTRATION ONLY. "
        "Not a medical diagnostic device. Health and risk outputs are prototype risk indicators."
    )

class SHAPFactor(BaseModel):
    feature: str
    contribution: float
    impact_description: str

class ExplanationDetail(BaseModel):
    environmental_factors: List[SHAPFactor]
    physiological_factors: List[SHAPFactor]
    model_contribution_note: str

class SensorTelemetryResponse(BaseModel):
    success: bool
    timestamp: str
    sensor_data: SensorInput
    environment: EnvironmentData
    aqi_prediction: AQIPrediction
    physiological_prediction: PhysiologicalPrediction
    personalized_risk: RiskAssessment
    explanation: ExplanationDetail

class MLModelMetrics(BaseModel):
    model_name: str
    model_type: str
    dataset: str
    features: List[str]
    classes: List[str]
    accuracy: float
    precision_weighted: float
    recall_weighted: float
    weighted_f1: float
    macro_f1: Optional[float] = None
    train_samples: Optional[int] = None
    test_samples: Optional[int] = None
    subjects: Optional[int] = None
    split_method: Optional[str] = None
    confusion_matrix: Optional[List[List[int]]] = None

class MLResultsResponse(BaseModel):
    offline_aqi_model: Dict[str, Any]
    live_aqi_model: Dict[str, Any]
    stress_model: Dict[str, Any]
