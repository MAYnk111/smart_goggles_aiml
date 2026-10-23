# SMART GOGGLE: AI-Based Personalized Health + Environment Monitoring System

> **College Prototype / Research Demonstration Notice:**  
> This system is a research prototype and college demonstration system, **NOT a certified medical diagnostic device**.  
> The health, environmental, and personalized risk scores are prototype risk indicators designed to illustrate multi-modal sensor fusion and explainable AI.

---

## 1. System Architecture

```
ESP32 Wearable Goggle (BLE Server)
  { "heart_rate": 82, "spo2": 97, "temperature": 36.5 }
             │
             │ BLE GATT Notification (UUID: 4fafc201-1fb5-459e-8fcc-c5c9c331914b)
             ▼
    Flutter Mobile Application (Android / iOS / Desktop)
             │
             │ HTTP POST /api/sensor
             ▼
    FastAPI Machine Learning Backend (backend/main.py)
    ├── External Environmental API (Open-Meteo Air Quality / WAQI)
    ├── Model 1: Air Quality Classifier (Random Forest + SHAP)
    ├── Model 2: Physiological Stress Classifier (Random Forest + SHAP)
    ├── Personalized Risk Engine (0-100 Multi-Factor Risk Score)
    └── Persistent SQLite / History Service
             │
             │ Real-time Telemetry + XAI Explanations
             ▼
    Flutter Interactive Dashboard
    ├── Screen 1: Splash Screen
    ├── Screen 2: Real-Time Dashboard (Vitals, AQI, Stress, Risk)
    ├── Screen 3: Environmental Pollutants & ML Prediction
    ├── Screen 4: Physiological Vitals & Stress Probabilities
    ├── Screen 5: SHAP Feature Contribution Bar Charts
    ├── Screen 6: Interactive Historical Trends (fl_chart)
    └── Screen 7: BLE Device Pairing, Scanning & Hardware Simulation
```

---

## 2. Machine Learning Pipeline & Results

### Model 1: Environmental AQI Classification
- **Dataset:** India Air Quality (`city_day.csv`, 24,850 valid rows)
- **Features:** 12 Ambient Pollutants: `['PM2.5', 'PM10', 'NO', 'NO2', 'NOx', 'NH3', 'CO', 'SO2', 'O3', 'Benzene', 'Toluene', 'Xylene']`
- **Target Leakage Prevention:** `AQI` column was **strictly excluded** from input features.
- **Model:** `RandomForestClassifier(n_estimators=300, class_weight='balanced', random_state=42)`
- **Evaluation:**
  - **Accuracy:** 81.31%
  - **Weighted Precision:** 81.21%
  - **Weighted Recall:** 81.31%
  - **Weighted F1 Score:** 81.17%
- **Artifacts Generated:**
  - `models/aqi_model.pkl`
  - `models/aqi_features.pkl`
  - `ml_results/aqi_results.json`
  - `ml_results/aqi_feature_importance.csv`
  - `ml_results/aqi_confusion_matrix.png`
  - `ml_results/shap/aqi_shap_summary.png`

### Model 2: Physiological Stress Classification
- **Dataset:** Wearable Device Dataset from Induced Stress and Structured Exercise Sessions
- **Signals Used:** Empatica E4 Heart Rate (1 Hz) and Skin Temperature (4 Hz) aligned with experimental protocol tags and self-reported stress levels (VAS 0-10 scale).
- **Extracted Windows:** 4,756 authentic sliding windows across 35 participants.
- **Classes:** Low (<= 3.0), Medium (3.1 - 6.0), High (> 6.0).
- **Data Leakage Prevention:** **Subject-Wise Group Split (`GroupShuffleSplit`)** strictly applied across participants (28 train subjects, 7 test subjects). No participant windows exist in both train and test.
- **Artifacts Generated:**
  - `models/stress_model.pkl`
  - `models/stress_features.pkl`
  - `ml_results/stress_results.json`
  - `ml_results/stress_feature_importance.csv`
  - `ml_results/stress_confusion_matrix.png`
  - `ml_results/shap/stress_shap_summary.png`

---

## 3. Personalized Risk Fusion Engine

The Risk Engine combines:
- **Environmental Component (0 - 50 points):** Derived from predicted AQI bucket + extreme particulate levels.
- **Physiological Component (0 - 50 points):** Derived from predicted stress class + vital deviations (hypoxemia penalties for SpO2 < 95%, tachycardia penalties for HR > 100, thermal penalties for temperature > 37.5°C).
- **Composite Prototype Risk Score (0 - 100 points):**
  - `0 - 20`: **Low** (Optimal vitals, clean environment)
  - `21 - 40`: **Mild** (Slight ambient pollutants or mild stress)
  - `41 - 60`: **Moderate** (Moderate pollution, elevated autonomic stress response)
  - `61 - 80`: **High** (High pollutant exposure or acute physical strain)
  - `81 - 100`: **Very High** (Severe environment and vital strain)

---

## 4. FastAPI Backend Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Service health status and loaded ML models verification |
| `POST` | `/api/sensor` | Primary ingestion endpoint for ESP32 physiological JSON |
| `GET` | `/api/environment` | Live normalized ambient pollutants from Open-Meteo / WAQI |
| `GET` | `/api/latest` | Latest recorded telemetry state |
| `GET` | `/api/history` | Historical sensor and risk records for time-series charts |
| `POST` | `/api/predict` | Ad-hoc simulation prediction endpoint |
| `GET` | `/api/explanation` | Latest dynamic SHAP TreeExplainer feature contributions |

### Run Backend:
```bash
python run_backend.py
```
API Documentation will be accessible at: `http://localhost:8000/docs`.

---

## 5. Flutter Mobile Application

### Features:
- Built with **Material 3** with dark and light theme switching.
- Dedicated BLE Service (`lib/services/ble_service.dart`) with configurable UUID constants.
- Android BLE Permissions fully configured in `AndroidManifest.xml` (`BLUETOOTH_SCAN`, `BLUETOOTH_CONNECT`, `ACCESS_FINE_LOCATION`).
- Built-in **Hardware Simulation Mode**: Allows live demonstration and evaluation even without physical hardware powered on.
- Interactive charts powered by `fl_chart`.

### Run Flutter Application:
```bash
cd flutter_app
flutter run
```

---

## 6. ESP32 Firmware Reference

Reference Arduino sketch located at:
`esp32_firmware/smart_goggle_esp32.ino`
Transmits:
```json
{
  "heart_rate": 82,
  "spo2": 97,
  "temperature": 36.5
}
```
over BLE GATT characteristic notification every 1 second.
