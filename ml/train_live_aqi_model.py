"""
Model 1B: Live-Compatible Environmental AQI Classification
Trained strictly on pollutant features reliably provided by Open-Meteo Air Quality API:
['PM2.5', 'PM10', 'NO2', 'CO', 'SO2', 'O3']
Target: AQI_Bucket (Good, Satisfactory, Moderate, Poor, Very Poor, Severe)
IMPORTANT: AQI column is EXCLUDED to strictly prevent target leakage.
"""

import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix,
)
import shap

# Set headless backend for matplotlib
plt.switch_backend('Agg')

# Base directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = r"C:\Users\Lenovo\Desktop\airquality\city_day.csv"
MODELS_DIR = os.path.join(BASE_DIR, "models")
RESULTS_DIR = os.path.join(BASE_DIR, "ml_results")
SHAP_DIR = os.path.join(RESULTS_DIR, "shap")

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(SHAP_DIR, exist_ok=True)

# Live features reliably available from Open-Meteo Air Quality API
LIVE_FEATURE_COLS = ["PM2.5", "PM10", "NO2", "CO", "SO2", "O3"]

def train_live_aqi():
    print(f"Loading Air Quality dataset for Live AQI Model from: {DATA_PATH}")
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Dataset not found at {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)
    print(f"Raw shape: {df.shape}")

    target_col = "AQI_Bucket"
    df = df.dropna(subset=[target_col]).copy()
    print(f"Shape after dropping missing targets: {df.shape}")

    print(f"Using {len(LIVE_FEATURE_COLS)} Open-Meteo compatible features: {LIVE_FEATURE_COLS}")

    # Convert features to numeric
    for col in LIVE_FEATURE_COLS:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    X = df[LIVE_FEATURE_COLS].copy()
    y = df[target_col].astype(str)

    target_classes = sorted(list(y.unique()))
    print(f"AQI Bucket Classes ({len(target_classes)}): {target_classes}")

    # Train/Test Split (Stratified)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"Train samples: {len(X_train)}, Test samples: {len(X_test)}")

    # Impute missing pollutant values using median from training data
    imputer = SimpleImputer(strategy="median")
    X_train_imp = pd.DataFrame(imputer.fit_transform(X_train), columns=LIVE_FEATURE_COLS)
    X_test_imp = pd.DataFrame(imputer.transform(X_test), columns=LIVE_FEATURE_COLS)

    # Train Random Forest Classifier
    print("Training Live-Compatible Random Forest Classifier (n_estimators=300, class_weight='balanced')...")
    rf = RandomForestClassifier(
        n_estimators=300,
        random_state=42,
        n_jobs=-1,
        class_weight="balanced"
    )
    rf.fit(X_train_imp, y_train)

    # Predictions and Evaluation
    y_pred = rf.predict(X_test_imp)

    acc = accuracy_score(y_test, y_pred)
    prec_weighted = precision_score(y_test, y_pred, average="weighted", zero_division=0)
    rec_weighted = recall_score(y_test, y_pred, average="weighted", zero_division=0)
    f1_weighted = f1_score(y_test, y_pred, average="weighted", zero_division=0)

    prec_macro = precision_score(y_test, y_pred, average="macro", zero_division=0)
    rec_macro = recall_score(y_test, y_pred, average="macro", zero_division=0)
    f1_macro = f1_score(y_test, y_pred, average="macro", zero_division=0)

    report_dict = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
    report_str = classification_report(y_test, y_pred, zero_division=0)

    print("\n--- Live AQI Model Evaluation ---")
    print(f"Accuracy:     {acc:.4f}")
    print(f"Macro F1:     {f1_macro:.4f}")
    print(f"Weighted F1:  {f1_weighted:.4f}")
    print("\nClassification Report:\n", report_str)

    # Confusion Matrix
    cm = confusion_matrix(y_test, y_pred, labels=target_classes)
    plt.figure(figsize=(8, 6))
    sns.heatmap(
        cm, annot=True, fmt="d", cmap="YlGnBu",
        xticklabels=target_classes, yticklabels=target_classes
    )
    plt.title("Live-Compatible AQI Classification - Confusion Matrix\n(Open-Meteo 6 Pollutants)")
    plt.xlabel("Predicted Label")
    plt.ylabel("True Label")
    plt.tight_layout()
    cm_path = os.path.join(RESULTS_DIR, "live_aqi_confusion_matrix.png")
    plt.savefig(cm_path, dpi=300)
    plt.close()
    print(f"Confusion matrix saved to {cm_path}")

    # Feature Importance
    feat_imp = pd.DataFrame({
        "Feature": LIVE_FEATURE_COLS,
        "Importance": rf.feature_importances_
    }).sort_values(by="Importance", ascending=False)
    
    fi_path = os.path.join(RESULTS_DIR, "live_aqi_feature_importance.csv")
    feat_imp.to_csv(fi_path, index=False)
    print(f"Feature importance saved to {fi_path}")

    # Save Model Artifacts
    model_artifact = {
        "model": rf,
        "imputer": imputer,
        "classes": target_classes,
        "features": LIVE_FEATURE_COLS,
    }
    model_path = os.path.join(MODELS_DIR, "live_aqi_model.pkl")
    joblib.dump(model_artifact, model_path)
    print(f"Model saved to {model_path}")

    features_path = os.path.join(MODELS_DIR, "live_aqi_features.pkl")
    joblib.dump(LIVE_FEATURE_COLS, features_path)
    print(f"Features saved to {features_path}")

    # Save JSON metrics
    results_json = {
        "model_name": "Live AQI Random Forest Classifier (Open-Meteo Compatible)",
        "dataset": "India Air Quality (city_day.csv)",
        "features": LIVE_FEATURE_COLS,
        "classes": target_classes,
        "train_samples": len(X_train),
        "test_samples": len(y_test),
        "accuracy": float(acc),
        "precision_macro": float(prec_macro),
        "recall_macro": float(rec_macro),
        "macro_f1": float(f1_macro),
        "precision_weighted": float(prec_weighted),
        "recall_weighted": float(rec_weighted),
        "weighted_f1": float(f1_weighted),
        "confusion_matrix": cm.tolist(),
        "classification_report": report_dict,
        "top_features": feat_imp.to_dict(orient="records")
    }
    results_path = os.path.join(RESULTS_DIR, "live_aqi_results.json")
    with open(results_path, "w") as f:
        json.dump(results_json, f, indent=2)
    print(f"Results saved to {results_path}")

    # SHAP Explainability
    print("\nCalculating SHAP values for Live AQI Model...")
    try:
        X_shap_sample = X_test_imp.sample(n=min(150, len(X_test_imp)), random_state=42)
        explainer = shap.TreeExplainer(rf)
        shap_values = explainer.shap_values(X_shap_sample)

        plt.figure(figsize=(10, 6))
        if isinstance(shap_values, list):
            class_idx = 0
            shap.summary_plot(shap_values[class_idx], X_shap_sample, show=False)
            plt.title(f"SHAP Summary Plot for Live AQI (Class: {target_classes[class_idx]})", fontsize=12)
        elif hasattr(shap_values, 'shape') and len(shap_values.shape) == 3:
            shap.summary_plot(shap_values[:, :, 0], X_shap_sample, show=False)
            plt.title("SHAP Summary Plot (Live Air Quality)", fontsize=12)
        else:
            shap.summary_plot(shap_values, X_shap_sample, show=False)
            plt.title("SHAP Summary Plot (Live Air Quality)", fontsize=12)

        shap_plot_path = os.path.join(SHAP_DIR, "live_aqi_shap_summary.png")
        plt.tight_layout()
        plt.savefig(shap_plot_path, dpi=300, bbox_inches="tight")
        plt.close()
        print(f"SHAP summary plot saved to {shap_plot_path}")
    except Exception as e:
        print(f"SHAP generation warning: {e}")

    print("\nLive AQI Model Training Complete!")

if __name__ == "__main__":
    train_live_aqi()
