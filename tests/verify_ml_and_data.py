import os
import sys
import json
import joblib
import numpy as np
import pandas as pd

# Add project root to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

print("============================================================")
print("1. VERIFY ML ARTIFACTS")
print("============================================================")

artifact_files = [
    "models/aqi_model.pkl",
    "models/aqi_features.pkl",
    "models/stress_model.pkl",
    "models/stress_features.pkl",
]

for f in artifact_files:
    full_path = os.path.join(BASE_DIR, f)
    exists = os.path.exists(full_path)
    size = os.path.getsize(full_path) if exists else 0
    print(f"File: {f} | Exists: {exists} | Size: {size} bytes")
    assert exists, f"Missing {f}"

# Load AQI Model
aqi_art = joblib.load(os.path.join(BASE_DIR, "models/aqi_model.pkl"))
aqi_features = joblib.load(os.path.join(BASE_DIR, "models/aqi_features.pkl"))
print("AQI Model loaded successfully.")
print("AQI Artifact keys:", list(aqi_art.keys()))
print("AQI Saved Features:", aqi_features)
print("AQI Classes:", aqi_art["classes"])

# Test Real Inference on AQI Model
dummy_aqi = pd.DataFrame([{
    "PM2.5": 45.0, "PM10": 80.0, "NO": 10.0, "NO2": 25.0, "NOx": 30.0,
    "NH3": 15.0, "CO": 0.8, "SO2": 9.0, "O3": 35.0, "Benzene": 2.0,
    "Toluene": 5.0, "Xylene": 1.5
}])[aqi_features] # Exactly matches training feature order
imp_aqi = aqi_art["imputer"].transform(dummy_aqi)
pred_aqi = aqi_art["model"].predict(imp_aqi)
prob_aqi = aqi_art["model"].predict_proba(imp_aqi)
print(f"AQI Real Inference Result: {pred_aqi[0]} with probabilities: {prob_aqi[0]}")
assert list(dummy_aqi.columns) == list(aqi_art["features"]) == aqi_features
print("AQI Feature Order Exact Match: VERIFIED")

# Load Stress Model
stress_art = joblib.load(os.path.join(BASE_DIR, "models/stress_model.pkl"))
stress_features = joblib.load(os.path.join(BASE_DIR, "models/stress_features.pkl"))
print("\nStress Model loaded successfully.")
print("Stress Artifact keys:", list(stress_art.keys()))
print("Stress Saved Features:", stress_features)
print("Stress Classes:", stress_art["classes"])

# Test Real Inference on Stress Model
dummy_stress = pd.DataFrame([{
    "hr_mean": 82.0, "hr_std": 1.5, "hr_min": 78.0, "hr_max": 86.0,
    "hr_range": 8.0, "hr_median": 82.0, "temp_mean": 36.5, "temp_std": 0.2,
    "temp_min": 36.2, "temp_max": 36.8
}])[stress_features] # Exactly matches training feature order
pred_stress = stress_art["model"].predict(dummy_stress)
prob_stress = stress_art["model"].predict_proba(dummy_stress)
print(f"Stress Real Inference Result: {pred_stress[0]} with probabilities: {prob_stress[0]}")
assert list(dummy_stress.columns) == list(stress_art["features"]) == stress_features
print("Stress Feature Order Exact Match: VERIFIED")

print("\n============================================================")
print("2. VERIFY AQI MODEL")
print("============================================================")

aqi_res_path = os.path.join(BASE_DIR, "ml_results/aqi_results.json")
with open(aqi_res_path) as f:
    aqi_res = json.load(f)

print("AQI Model Results:")
print(f"  Accuracy:           {aqi_res['accuracy']:.4f}")
print(f"  Precision:          {aqi_res['precision_weighted']:.4f}")
print(f"  Recall:             {aqi_res['recall_weighted']:.4f}")
print(f"  F1-Score:           {aqi_res['f1_weighted']:.4f}")
print(f"  Number of Classes:  {len(aqi_res['classes'])} -> {aqi_res['classes']}")
print(f"  Number of Test Samples: {aqi_res['test_size']}")

# Verify AQI is NOT used as an input feature
assert "AQI" not in aqi_res["features"], "FATAL: AQI found in input features!"
assert "AQI" not in aqi_features, "FATAL: AQI found in aqi_features.pkl!"
print("Target Leakage Verification: 'AQI' column is strictly NOT in input features: VERIFIED")
print("Target Column in training: 'AQI_Bucket' (Classes: Good, Moderate, Poor, Satisfactory, Severe, Very Poor)")

cm_aqi_path = os.path.join(BASE_DIR, "ml_results/aqi_confusion_matrix.png")
shap_aqi_path = os.path.join(BASE_DIR, "ml_results/shap/aqi_shap_summary.png")
print(f"Confusion Matrix exists: {os.path.exists(cm_aqi_path)} ({os.path.getsize(cm_aqi_path)} bytes)")
print(f"SHAP Summary exists:    {os.path.exists(shap_aqi_path)} ({os.path.getsize(shap_aqi_path)} bytes)")
assert os.path.exists(cm_aqi_path) and os.path.exists(shap_aqi_path)

print("\n============================================================")
print("3. VERIFY STRESS MODEL")
print("============================================================")

stress_res_path = os.path.join(BASE_DIR, "ml_results/stress_results.json")
with open(stress_res_path) as f:
    stress_res = json.load(f)

print("Stress Model Results:")
print(f"  Accuracy:           {stress_res['accuracy']:.4f}")
print(f"  Precision:          {stress_res['precision_weighted']:.4f}")
print(f"  Recall:             {stress_res['recall_weighted']:.4f}")
print(f"  F1-Score:           {stress_res['f1_weighted']:.4f}")
print(f"  Train Subjects:     {len(stress_res['train_subjects'])} -> {stress_res['train_subjects']}")
print(f"  Test Subjects:      {len(stress_res['test_subjects'])} -> {stress_res['test_subjects']}")
print(f"  Total Subjects:     {len(stress_res['train_subjects']) + len(stress_res['test_subjects'])}")
print(f"  Classes:            {stress_res['classes']}")

# Verify subject-wise / group-wise separation: zero overlap
train_set = set(stress_res['train_subjects'])
test_set = set(stress_res['test_subjects'])
overlap = train_set.intersection(test_set)
print(f"  Overlap between train and test subjects: {overlap}")
assert len(overlap) == 0, f"FATAL: Subject leakage detected: {overlap}"
print("Subject-Wise Group Separation: VERIFIED (0 overlap, no subject leakage)")

cm_stress_path = os.path.join(BASE_DIR, "ml_results/stress_confusion_matrix.png")
shap_stress_path = os.path.join(BASE_DIR, "ml_results/shap/stress_shap_summary.png")
print(f"Confusion Matrix exists: {os.path.exists(cm_stress_path)} ({os.path.getsize(cm_stress_path)} bytes)")
print(f"SHAP Summary exists:    {os.path.exists(shap_stress_path)} ({os.path.getsize(shap_stress_path)} bytes)")
assert os.path.exists(cm_stress_path) and os.path.exists(shap_stress_path)

print("\n============================================================")
print("4. VERIFY WEARABLE FEATURE EXTRACTION INDEPENDENTLY")
print("============================================================")

w_base = r"C:\Users\Lenovo\Desktop\wearable-device-dataset-from-induced-stress-and-structured-exercise-sessions-1.0.1\wearable-device-dataset-from-induced-stress-and-structured-exercise-sessions-1.0.1"
stress_dir = os.path.join(w_base, "Wearable_Dataset", "STRESS")
subjects = sorted(os.listdir(stress_dir))
print(f"Total Subjects discovered in STRESS: {len(subjects)}")

hr_files_count = 0
temp_files_count = 0
eda_files_count = 0
valid_subjects = []

for s in subjects:
    s_dir = os.path.join(stress_dir, s)
    has_hr = os.path.exists(os.path.join(s_dir, "HR.csv"))
    has_temp = os.path.exists(os.path.join(s_dir, "TEMP.csv"))
    has_eda = os.path.exists(os.path.join(s_dir, "EDA.csv"))
    has_tags = os.path.exists(os.path.join(s_dir, "tags.csv"))
    
    if has_hr: hr_files_count += 1
    if has_temp: temp_files_count += 1
    if has_eda: eda_files_count += 1
    if has_hr and has_temp and has_tags:
        valid_subjects.append(s)

print(f"Number of valid subjects with HR + TEMP + tags: {len(valid_subjects)}")
print(f"Number of HR files:          {hr_files_count}")
print(f"Number of Temperature files: {temp_files_count}")
print(f"Number of EDA files:         {eda_files_count} (Note: EDA sensor not present on ESP32, hence excluded from stress training to match hardware)")

from ml.train_stress_model import extract_physiological_features, FEATURE_COLS
df_ext = extract_physiological_features()
print(f"Number of final training/testing records: {len(df_ext)}")
print(f"Features used by stress model: {FEATURE_COLS}")
print(f"Features expected by models/stress_model.pkl: {stress_art['features']}")
assert FEATURE_COLS == stress_art['features'], "Features mismatch!"
print("Feature Alignment with models/stress_model.pkl: VERIFIED")
