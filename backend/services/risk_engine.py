"""
Personalized Risk Engine
Combines:
- Environmental Model Output (0 - 50 scale)
- Physiological Stress Model Output (0 - 50 scale)
- Live Vital Modifiers (Heart Rate, Skin Temp, nullable SpO2, Emergency/Fall)
= Composite Prototype Risk Score (0 - 100 scale)
NON-DIAGNOSTIC RESEARCH DEMONSTRATION / PROTOTYPE RISK INDICATOR.
"""

from typing import Dict
from backend.models_schema import (
    SensorInput,
    EnvironmentData,
    AQIPrediction,
    PhysiologicalPrediction,
    RiskAssessment,
)

AQI_BASE_SCORES: Dict[str, float] = {
    "Good": 6.0,
    "Satisfactory": 14.0,
    "Moderate": 26.0,
    "Poor": 36.0,
    "Very Poor": 44.0,
    "Severe": 50.0,
}

STRESS_BASE_SCORES: Dict[str, float] = {
    "Low": 8.0,
    "Medium": 22.0,
    "High": 36.0,
}

class RiskEngine:
    @staticmethod
    def calculate_risk(
        sensor: SensorInput,
        env: EnvironmentData,
        aqi_pred: AQIPrediction,
        stress_pred: PhysiologicalPrediction,
    ) -> RiskAssessment:
        """
        Calculates prototype composite risk score (0-100).
        """
        # 1. Environmental Component (Max 50.0)
        env_score = AQI_BASE_SCORES.get(aqi_pred.predicted_bucket, 20.0)
        if env.pm25 is not None and env.pm25 > 120.0:
            env_score = min(50.0, env_score + 5.0)

        # 2. Physiological Component (Max 50.0)
        stress_base = STRESS_BASE_SCORES.get(stress_pred.predicted_stress, 15.0)
        vital_modifiers: Dict[str, float] = {}

        # SpO2 modifier (ONLY applied if SpO2 is provided, otherwise omitted)
        spo2_pen = 0.0
        if sensor.spo2 is not None:
            if sensor.spo2 < 93.0:
                spo2_pen = 14.0
                vital_modifiers["spo2_severe_desaturation"] = 14.0
            elif sensor.spo2 < 95.0:
                spo2_pen = 8.0
                vital_modifiers["spo2_mild_desaturation"] = 8.0
            elif sensor.spo2 < 97.0:
                spo2_pen = 3.0
                vital_modifiers["spo2_low_normal"] = 3.0
            else:
                vital_modifiers["spo2_optimal"] = 0.0
        else:
            vital_modifiers["spo2_sensor"] = 0.0  # Not measured by current ESP32 firmware

        # Heart Rate modifier
        hr_val = sensor.get_effective_hr()
        hr_pen = 0.0
        if hr_val > 115.0:
            hr_pen = 8.0
            vital_modifiers["hr_elevated_tachycardia"] = 8.0
        elif hr_val > 95.0:
            hr_pen = 4.0
            vital_modifiers["hr_mild_elevation"] = 4.0
        elif hr_val < 50.0 and hr_val > 0.0:
            hr_pen = 4.0
            vital_modifiers["hr_bradycardia"] = 4.0
        else:
            vital_modifiers["hr_normal"] = 0.0

        # Temperature modifier (applied if measured)
        temp_pen = 0.0
        if sensor.temperature is not None:
            if sensor.temperature > 38.0:
                temp_pen = 8.0
                vital_modifiers["temp_high_pyrexia"] = 8.0
            elif sensor.temperature > 37.3:
                temp_pen = 3.0
                vital_modifiers["temp_warm"] = 3.0
            elif sensor.temperature < 35.0:
                temp_pen = 4.0
                vital_modifiers["temp_hypothermic"] = 4.0
            else:
                vital_modifiers["temp_normal"] = 0.0

        phys_score = min(50.0, stress_base + spo2_pen + hr_pen + temp_pen)

        # Emergency or Fall overrides
        fall_alert = sensor.fall
        emergency_alert = sensor.emergency
        if emergency_alert or fall_alert:
            phys_score = 50.0

        total_risk = round(min(100.0, max(0.0, env_score + phys_score)), 1)

        # Categorize into UI Prototype Risk Levels
        if emergency_alert or fall_alert or total_risk > 80.0:
            level = "Very High"
            summary = "Emergency or severe environmental/vital strain detected. Immediate attention recommended."
        elif total_risk <= 20.0:
            level = "Low"
            summary = "Optimal physiological vitals and favorable ambient environment."
        elif total_risk <= 40.0:
            level = "Mild"
            summary = "Mild ambient pollutants or slightly elevated physiological stress detected."
        elif total_risk <= 60.0:
            level = "Moderate"
            summary = "Moderate environmental exposure and noticeable physiological stress response."
        else:
            level = "High"
            summary = "Elevated risk indicator driven by high air pollution or acute physiological strain."

        return RiskAssessment(
            risk_score=total_risk,
            risk_level=level,
            environmental_component=round(env_score, 1),
            physiological_component=round(phys_score, 1),
            vital_modifiers=vital_modifiers,
            status_summary=summary,
            fall_alert=fall_alert,
            emergency_alert=emergency_alert,
            finger_status=sensor.finger
        )

risk_engine = RiskEngine()
