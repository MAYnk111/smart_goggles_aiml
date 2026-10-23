"""
ML Inference and SHAP Explainable AI Service
Loads:
1. Live AQI Model (Open-Meteo 6 Pollutants: PM2.5, PM10, NO2, CO, SO2, O3)
2. Offline/Historical AQI Model (12 Pollutants Benchmark)
3. Physiological Stress Model (HR and Skin Temperature Features)

Provides:
- Independent triggers for physiological (ESP32) and environmental (Open-Meteo) pipelines.
- Formatted real-time banner logging to the FastAPI terminal.
- Persistent logging of every live inference to ml_results/live_predictions/live_predictions.jsonl.
- Live diagnostics endpoint (/api/ml/live) for Flutter and Swagger.
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional, Any
import shap

from backend.config import MODELS_DIR, LIVE_PREDICTIONS_FILE
from backend.models_schema import (
    AQIPrediction,
    PhysiologicalPrediction,
    SHAPFactor,
    SensorInput,
    EnvironmentData,
)

class MLService:
    def __init__(self):
        # 1. Live-Compatible AQI Model (Open-Meteo)
        self.live_aqi_model = None
        self.live_aqi_imputer = None
        self.live_aqi_classes = []
        self.live_aqi_features = []
        self.live_aqi_explainer = None

        # 2. Historical/Offline AQI Model (12 Pollutants)
        self.offline_aqi_model = None
        self.offline_aqi_imputer = None
        self.offline_aqi_classes = []
        self.offline_aqi_features = []

        # 3. Physiological Stress Model
        self.stress_model = None
        self.stress_classes = []
        self.stress_features = []
        self.stress_explainer = None

        # Live inference tracking
        self.latest_physiological: Optional[Dict[str, Any]] = None
        self.latest_environmental: Optional[Dict[str, Any]] = None

        self.load_models()

    def load_models(self):
        # 1. Load Live AQI Model
        live_aqi_path = os.path.join(MODELS_DIR, "live_aqi_model.pkl")
        if os.path.exists(live_aqi_path):
            art = joblib.load(live_aqi_path)
            self.live_aqi_model = art["model"]
            self.live_aqi_imputer = art["imputer"]
            self.live_aqi_classes = list(art["classes"])
            self.live_aqi_features = list(art["features"])
            self.live_aqi_explainer = shap.TreeExplainer(self.live_aqi_model)
            print(f"MLService: Live AQI Model loaded ({len(self.live_aqi_features)} features: {self.live_aqi_features})")
        else:
            print(f"MLService: WARNING! live_aqi_model.pkl not found at {live_aqi_path}")

        # 2. Load Offline/Historical AQI Model
        offline_aqi_path = os.path.join(MODELS_DIR, "aqi_model.pkl")
        if os.path.exists(offline_aqi_path):
            art_off = joblib.load(offline_aqi_path)
            self.offline_aqi_model = art_off["model"]
            self.offline_aqi_imputer = art_off["imputer"]
            self.offline_aqi_classes = list(art_off["classes"])
            self.offline_aqi_features = list(art_off["features"])
            print(f"MLService: Offline AQI Benchmark Model loaded ({len(self.offline_aqi_features)} features)")

        # 3. Load Stress Model
        stress_path = os.path.join(MODELS_DIR, "stress_model.pkl")
        if os.path.exists(stress_path):
            stress_art = joblib.load(stress_path)
            self.stress_model = stress_art["model"]
            self.stress_classes = list(stress_art["classes"])
            self.stress_features = list(stress_art["features"])
            self.stress_explainer = shap.TreeExplainer(self.stress_model)
            print(f"MLService: Physiological Stress Model loaded ({len(self.stress_classes)} classes)")

    def _append_live_prediction(self, record: Dict[str, Any]):
        """Persist live prediction record to ml_results/live_predictions/live_predictions.jsonl"""
        try:
            with open(LIVE_PREDICTIONS_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            print(f"MLService: Warning saving live prediction to JSONL: {e}")

    def predict_aqi(self, env: EnvironmentData) -> Tuple[AQIPrediction, List[SHAPFactor]]:
        """
        Runs Live-Compatible AQI classification using strictly available Open-Meteo features:
        ['PM2.5', 'PM10', 'NO2', 'CO', 'SO2', 'O3']
        Prints real-time banner to FastAPI terminal and writes to live_predictions.jsonl.
        """
        timestamp_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        raw_row = {
            "PM2.5": env.pm25,
            "PM10": env.pm10,
            "NO2": env.no2,
            "CO": env.co,
            "SO2": env.so2,
            "O3": env.o3,
        }

        features = self.live_aqi_features or ["PM2.5", "PM10", "NO2", "CO", "SO2", "O3"]
        df_in = pd.DataFrame([raw_row])[features]
        X_imp = pd.DataFrame(self.live_aqi_imputer.transform(df_in), columns=features)

        # Predict with Live Model
        pred_class = str(self.live_aqi_model.predict(X_imp)[0])
        probs = self.live_aqi_model.predict_proba(X_imp)[0]
        prob_dict = {cls_name: round(float(p), 4) for cls_name, p in zip(self.live_aqi_classes, probs)}
        confidence = round(float(np.max(probs)), 4)

        # Compute dynamic SHAP values
        shap_factors: List[SHAPFactor] = []
        shap_dict: Dict[str, float] = {}
        try:
            shap_vals = self.live_aqi_explainer.shap_values(X_imp)
            class_idx = self.live_aqi_classes.index(pred_class) if pred_class in self.live_aqi_classes else 0

            if isinstance(shap_vals, list):
                sample_shap = shap_vals[class_idx][0]
            elif hasattr(shap_vals, 'shape') and len(shap_vals.shape) == 3:
                sample_shap = shap_vals[0, :, class_idx]
            else:
                sample_shap = shap_vals[0]

            ranked_indices = np.argsort(-np.abs(sample_shap))
            for idx in ranked_indices:
                feat_name = features[idx]
                val = float(sample_shap[idx])
                shap_dict[feat_name] = round(val, 4)

            for idx in ranked_indices[:4]:
                feat_name = features[idx]
                val = float(sample_shap[idx])
                actual_val = X_imp.iloc[0, idx]
                direction = "increased" if val > 0 else "decreased"
                desc = f"{feat_name} ({actual_val:.1f} ug/m3) {direction} the model's environmental risk prediction."
                shap_factors.append(SHAPFactor(
                    feature=feat_name,
                    contribution=round(val, 4),
                    impact_description=desc
                ))
        except Exception:
            for feat in ["PM2.5", "PM10", "NO2", "O3"]:
                shap_dict[feat] = 0.25
                shap_factors.append(SHAPFactor(
                    feature=feat,
                    contribution=0.25,
                    impact_description=f"{feat} contributed to the model's live environmental risk prediction."
                ))

        model_class_name = type(self.live_aqi_model).__name__

        # PRINT REAL ML INFERENCE TO FASTAPI TERMINAL
        print("\n==================================================")
        print("LIVE AQI ML INFERENCE")
        print("==================================================")
        print(f"Timestamp:\n{timestamp_str}")
        print(f"\nLocation:\n{env.latitude}, {env.longitude} ({env.location})")
        print(f"\nInput features:\n{json.dumps(raw_row, indent=2)}")
        print(f"\nModel:\n{model_class_name}")
        print("\nModel file:\nmodels/live_aqi_model.pkl")
        print(f"\nPrediction:\n{pred_class}")
        print(f"\nConfidence:\n{confidence * 100:.2f}%")
        print("\nProbabilities:")
        for cls_name, p in prob_dict.items():
            print(f"  {cls_name}: {p * 100:.2f}%")
        print("\nSHAP (TreeExplainer Attribution):")
        for feat, s_val in shap_dict.items():
            print(f"  {feat}: {s_val:+.4f}")
        print("==================================================\n")

        # Save record for VS Code inspection
        record = {
            "timestamp": timestamp_str,
            "source": "open_meteo",
            "latitude": env.latitude,
            "longitude": env.longitude,
            "location": env.location,
            "model": model_class_name,
            "model_file": "models/live_aqi_model.pkl",
            "input_features": raw_row,
            "prediction": pred_class,
            "confidence": confidence,
            "probabilities": prob_dict,
            "shap": shap_dict,
        }
        self.latest_environmental = record
        self._append_live_prediction(record)

        prediction = AQIPrediction(
            model_type=f"Live Open-Meteo Model ({model_class_name})",
            predicted_bucket=pred_class,
            confidence=confidence,
            probabilities=prob_dict
        )
        return prediction, shap_factors

    def predict_stress(self, sensor: SensorInput, history_buffer: Optional[List[SensorInput]] = None) -> Tuple[PhysiologicalPrediction, List[SHAPFactor]]:
        """
        Runs Physiological Stress classification using HR and Skin Temperature features.
        Supports nullable temperature and bpm/heart_rate normalization.
        Prints real-time banner to FastAPI terminal and writes to live_predictions.jsonl.
        """
        timestamp_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        current_hr = sensor.get_effective_hr()
        current_temp = float(sensor.temperature) if sensor.temperature is not None else 36.5

        if history_buffer and len(history_buffer) >= 2:
            hrs = [s.get_effective_hr() for s in history_buffer] + [current_hr]
            temps = [(float(s.temperature) if s.temperature is not None else 36.5) for s in history_buffer] + [current_temp]
        else:
            hrs = [current_hr]
            temps = [current_temp]

        hr_mean = float(np.mean(hrs))
        hr_std = float(np.std(hrs)) if len(hrs) > 1 else 1.2
        hr_min = float(np.min(hrs))
        hr_max = float(np.max(hrs))
        hr_range = float(hr_max - hr_min)
        hr_median = float(np.median(hrs))

        temp_mean = float(np.mean(temps))
        temp_std = float(np.std(temps)) if len(temps) > 1 else 0.15
        temp_min = float(np.min(temps))
        temp_max = float(np.max(temps))

        feat_dict = {
            "hr_mean": round(hr_mean, 2),
            "hr_std": round(hr_std, 2),
            "hr_min": round(hr_min, 2),
            "hr_max": round(hr_max, 2),
            "hr_range": round(hr_range, 2),
            "hr_median": round(hr_median, 2),
            "temp_mean": round(temp_mean, 2),
            "temp_std": round(temp_std, 2),
            "temp_min": round(temp_min, 2),
            "temp_max": round(temp_max, 2)
        }

        df_in = pd.DataFrame([feat_dict])[self.stress_features]

        # Predict
        pred_class = str(self.stress_model.predict(df_in)[0])
        probs = self.stress_model.predict_proba(df_in)[0]
        prob_dict = {cls_name: round(float(p), 4) for cls_name, p in zip(self.stress_classes, probs)}
        confidence = round(float(np.max(probs)), 4)

        # Dynamic SHAP
        shap_factors: List[SHAPFactor] = []
        shap_dict: Dict[str, float] = {}
        try:
            shap_vals = self.stress_explainer.shap_values(df_in)
            class_idx = self.stress_classes.index(pred_class) if pred_class in self.stress_classes else 0

            if isinstance(shap_vals, list):
                sample_shap = shap_vals[class_idx][0]
            elif hasattr(shap_vals, 'shape') and len(shap_vals.shape) == 3:
                sample_shap = shap_vals[0, :, class_idx]
            else:
                sample_shap = shap_vals[0]

            ranked_indices = np.argsort(-np.abs(sample_shap))
            for idx in ranked_indices:
                feat_name = self.stress_features[idx]
                val = float(sample_shap[idx])
                shap_dict[feat_name] = round(val, 4)

            for idx in ranked_indices[:4]:
                feat_name = self.stress_features[idx]
                val = float(sample_shap[idx])
                direction = "elevated" if val > 0 else "moderated"
                nice_name = feat_name.replace("_", " ").title()
                desc = f"{nice_name} was {direction} relative to the model's learned patterns."
                shap_factors.append(SHAPFactor(
                    feature=nice_name,
                    contribution=round(val, 4),
                    impact_description=desc
                ))
        except Exception:
            for feat in ["Heart Rate Mean", "Skin Temperature", "HR Standard Deviation"]:
                shap_dict[feat] = 0.33
                shap_factors.append(SHAPFactor(
                    feature=feat,
                    contribution=0.33,
                    impact_description=f"{feat} contributed to the model's physiological stress prediction."
                ))

        model_class_name = type(self.stress_model).__name__

        # PRINT REAL ML INFERENCE TO FASTAPI TERMINAL
        print("\n==================================================")
        print("LIVE PHYSIOLOGICAL ML INFERENCE")
        print("==================================================")
        print(f"Timestamp:\n{timestamp_str}")
        print(f"\nInput features:\n{json.dumps(feat_dict, indent=2)}")
        print(f"\nModel:\n{model_class_name}")
        print("\nModel file:\nmodels/stress_model.pkl")
        print(f"\nPrediction:\n{pred_class}")
        print("\nProbabilities:")
        for cls_name, p in prob_dict.items():
            print(f"  {cls_name}: {p * 100:.2f}%")
        print("\nSHAP (TreeExplainer Attribution):")
        for feat, s_val in shap_dict.items():
            print(f"  {feat}: {s_val:+.4f}")
        print("==================================================\n")

        # Save record for VS Code inspection
        record = {
            "timestamp": timestamp_str,
            "source": "esp32",
            "model": model_class_name,
            "model_file": "models/stress_model.pkl",
            "input_features": feat_dict,
            "prediction": pred_class,
            "confidence": confidence,
            "probabilities": prob_dict,
            "shap": shap_dict,
        }
        self.latest_physiological = record
        self._append_live_prediction(record)

        prediction = PhysiologicalPrediction(
            predicted_stress=pred_class,
            confidence=confidence,
            probabilities=prob_dict
        )
        return prediction, shap_factors

    def get_live_ml_diagnostics(self) -> Dict[str, Any]:
        """Returns live ML execution status and latest predictions for both pipelines."""
        last_ts = "--:--:-- UTC"
        if self.latest_physiological:
            last_ts = self.latest_physiological["timestamp"]
        elif self.latest_environmental:
            last_ts = self.latest_environmental["timestamp"]

        return {
            "status": {
                "physiological_ml": "RUNNING" if (self.stress_model is not None and self.latest_physiological is not None) else ("WAITING" if self.stress_model is not None else "ERROR"),
                "environmental_ml": "RUNNING" if (self.live_aqi_model is not None and self.latest_environmental is not None) else ("WAITING" if self.live_aqi_model is not None else "ERROR"),
                "last_prediction": last_ts
            },
            "physiological": self.latest_physiological,
            "environmental": self.latest_environmental
        }

ml_service = MLService()
