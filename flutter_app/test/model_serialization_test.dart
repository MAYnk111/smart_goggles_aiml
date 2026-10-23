import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_app/models/sensor_data.dart';
import 'package:flutter_app/models/telemetry_model.dart';

void main() {
  group('Smart Goggle Models & JSON Schema Tests', () {
    test('ESP32 Firmware exact payload parsing (final_bpm_and_mpu.ino)', () {
      final firmwarePayload = {
        "bpm": 84.5,
        "temperature": 36.6,
        "fall": false,
        "finger": true,
        "emergency": false
      };

      final data = SensorData.fromJson(firmwarePayload);
      expect(data.heartRate, 84.5);
      expect(data.spo2, isNull); // Firmware does NOT calculate SpO2 - verified null!
      expect(data.temperature, 36.6);
      expect(data.finger, true);
      expect(data.fall, false);
      expect(data.emergency, false);
      expect(data.displayHeartRate, "85");
      expect(data.displaySpo2, "--");
      expect(data.displayTemperature, "36.6");

      final outJson = data.toJson();
      expect(outJson["bpm"], 84.5);
      expect(outJson["heart_rate"], 84.5);
      expect(outJson["temperature"], 36.6);
      expect(outJson.containsKey("spo2"), false); // Null keys excluded or null
      expect(outJson["finger"], true);
      expect(outJson["fall"], false);
      expect(outJson["emergency"], false);
    });

    test('Fall and Emergency event payload parsing', () {
      final emergencyPayload = {
        "bpm": 120.0,
        "temperature": 37.2,
        "fall": true,
        "finger": true,
        "emergency": true
      };

      final data = SensorData.fromJson(emergencyPayload);
      expect(data.fall, true);
      expect(data.emergency, true);
      expect(data.heartRate, 120.0);
    });

    test('No finger placed on sensor payload parsing', () {
      final noFingerPayload = {
        "bpm": 0.0,
        "temperature": 36.0,
        "fall": false,
        "finger": false,
        "emergency": false
      };

      final data = SensorData.fromJson(noFingerPayload, defaultSource: "REAL ESP32");
      expect(data.finger, false);
      expect(data.displayHeartRate, "--");
    });

    test('TelemetryResponse parsing from backend with nullable SpO2', () {
      final sampleBackendJson = {
        "success": true,
        "timestamp": "12:34:56",
        "sensor_data": {
          "bpm": 82.0,
          "heart_rate": 82.0,
          "spo2": null,
          "temperature": 36.5,
          "fall": false,
          "finger": true,
          "emergency": false
        },
        "environment": {
          "pm25": 48.5,
          "pm10": 92.0,
          "source": "Open-Meteo Live API",
          "location": "GPS (28.6139, 77.2090)"
        },
        "aqi_prediction": {
          "predicted_bucket": "Moderate",
          "confidence": 0.8024,
          "probabilities": {"Moderate": 0.80, "Satisfactory": 0.20}
        },
        "physiological_prediction": {
          "predicted_stress": "Low",
          "confidence": 0.8333,
          "probabilities": {"Low": 0.83, "Medium": 0.17}
        },
        "personalized_risk": {
          "risk_score": 34.0,
          "risk_level": "Low",
          "environmental_component": 18.0,
          "physiological_component": 16.0,
          "vital_modifiers": {},
          "status_summary": "Low risk composite score.",
          "prototype_disclaimer": "College prototype demonstration."
        },
        "explanation": {
          "environmental_factors": [
            {
              "feature": "PM2.5",
              "contribution": 0.08,
              "impact_description": "PM2.5 contributed to the model's environmental risk prediction."
            }
          ],
          "physiological_factors": [
            {
              "feature": "heart_rate",
              "contribution": -0.02,
              "impact_description": "Heart rate was in the expected range for the predicted stress state."
            }
          ],
          "model_contribution_note": "SHAP TreeExplainer weights."
        }
      };

      final response = TelemetryResponse.fromJson(sampleBackendJson);
      expect(response.success, true);
      expect(response.sensorData.heartRate, 82.0);
      expect(response.sensorData.spo2, isNull);
      expect(response.sensorData.displaySpo2, "--");
      expect(response.aqiPrediction.predictedBucket, "Moderate");
      expect(response.physiologicalPrediction.predictedStress, "Low");
      expect(response.personalizedRisk.riskScore, 34.0);
      expect(response.personalizedRisk.riskLevel, "Low");
      expect(response.explanation.environmentalFactors.length, 1);
    });
  });
}
