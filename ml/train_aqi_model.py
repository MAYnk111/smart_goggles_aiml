"""
Model 1: Environmental AQI Classification
Dataset: India Air Quality (city_day.csv)
Target: AQI_Bucket (Good, Satisfactory, Moderate, Poor, Very Poor, Severe)
Input Features: Pollutants (PM2.5, PM10, NO, NO2, NOx, NH3, CO, SO2, O3, Benzene, Toluene, Xylene)
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

def train_aqi():
    print(f"Loading Air Quality dataset from: {DATA_PATH}")
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Dataset not found at {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)
    print(f"Raw shape: {df.shape}")

    # Inspect target distribution
    target_col = "AQI_Bucket"
    print(f"Target column: {target_col}")
    
    # Filter rows with valid target
    df = df.dropna(subset=[target_col]).copy()
    print(f"Shape after dropping missing targets: {df.shape}")

    # Feature columns: strictly pollutant measures, NO AQI column
    feature_cols = [
        "PM2.5", "PM10", "NO", "NO2", "NOx", "NH3",
        "CO", "SO2", "O3", "Benzene", "Toluene", "Xylene"
    ]
    
    # Verify all feature columns exist
    for col in feature_cols:
        if col not in df.columns:
            raise KeyError(f"Expected feature column '{col}' missing from dataset")
            
    print(f"Using {len(feature_cols)} pollutant features (AQI strictly excluded to avoid target leakage):")
    print(feature_cols)

    # Convert features to numeric
    for col in feature_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    X = df[feature_cols].copy()
    y = df[target_col].astype(str)

    target_classes = sorted(list(y.unique()))
    print(f"AQI Bucket Classes ({len(target_classes)}): {target_classes}")
    print(y.value_counts())

    # Train/Test Split (Stratified)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"Train samples: {len(X_train)}, Test samples: {len(X_test)}")

    # Impute missing pollutant values using median from training data
    imputer = SimpleImputer(strategy="median")
    X_train_imp = pd.DataFrame(imputer.fit_transform(X_train), columns=feature_cols)
    X_test_imp = pd.DataFrame(imputer.transform(X_test), columns=feature_cols)

    # Train Random Forest Classifier
    print("Training Random Forest Classifier (n_estimators=300, class_weight='balanced')...")
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
    prec = precision_score(y_test, y_pred, average="weighted", zero_division=0)
    rec = recall_score(y_test, y_pred, average="weighted", zero_division=0)
    f1 = f1_score(y_test, y_pred, average="weighted", zero_division=0)
    report_dict = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
    report_str = classification_report(y_test, y_pred, zero_division=0)

    print("\n--- Model Evaluation ---")
    print(f"Accuracy:  {acc:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall:    {rec:.4f}")
    print(f"F1 Score:  {f1:.4f}")
    print("\nClassification Report:\n", report_str)

    # Confusion Matrix
    cm = confusion_matrix(y_test, y_pred, labels=target_classes)
    plt.figure(figsize=(8, 6))
    sns.heatmap(
        cm, annot=True, fmt="d", cmap="Blues",
        xticklabels=target_classes, yticklabels=target_classes
    )
    plt.title("Air Quality Classification - Confusion Matrix")
    plt.xlabel("Predicted Label")
    plt.ylabel("True Label")
    plt.tight_layout()
    cm_path = os.path.join(RESULTS_DIR, "aqi_confusion_matrix.png")
    plt.savefig(cm_path, dpi=300)
    plt.close()
    print(f"Confusion matrix saved to {cm_path}")

    # Feature Importance
    feat_imp = pd.DataFrame({
        "Feature": feature_cols,
        "Importance": rf.feature_importances_
    }).sort_values(by="Importance", ascending=False)
    
    fi_path = os.path.join(RESULTS_DIR, "aqi_feature_importance.csv")
    feat_imp.to_csv(fi_path, index=False)
    print(f"Feature importance saved to {fi_path}")

    # Save Model Artifacts
    model_artifact = {
        "model": rf,
        "imputer": imputer,
        "classes": target_classes,
        "features": feature_cols,
    }
    model_path = os.path.join(MODELS_DIR, "aqi_model.pkl")
    joblib.dump(model_artifact, model_path)
    print(f"Model saved to {model_path}")

    features_path = os.path.join(MODELS_DIR, "aqi_features.pkl")
    joblib.dump(feature_cols, features_path)
    print(f"Features saved to {features_path}")

    # Save JSON metrics
    results_json = {
        "model_name": "AQI Random Forest Classifier",
        "dataset": "India Air Quality (city_day.csv)",
        "features": feature_cols,
        "classes": target_classes,
        "test_size": len(y_test),
        "accuracy": float(acc),
        "precision_weighted": float(prec),
        "recall_weighted": float(rec),
        "f1_weighted": float(f1),
        "classification_report": report_dict,
        "top_features": feat_imp.to_dict(orient="records")
    }
    results_path = os.path.join(RESULTS_DIR, "aqi_results.json")
    with open(results_path, "w") as f:
        json.dump(results_json, f, indent=2)
    print(f"Results saved to {results_path}")

    # SHAP Explainability
    print("\nCalculating SHAP values...")
    try:
        # Sample 150 test instances for fast and accurate TreeExplainer computation
        X_shap_sample = X_test_imp.sample(n=min(150, len(X_test_imp)), random_state=42)
        explainer = shap.TreeExplainer(rf)
        shap_values = explainer.shap_values(X_shap_sample)

        plt.figure(figsize=(10, 6))
        # Handle shap_values list or 3D array
        if isinstance(shap_values, list):
            class_idx = 0
            shap.summary_plot(shap_values[class_idx], X_shap_sample, show=False)
            plt.title(f"SHAP Summary Plot for AQI Class: {target_classes[class_idx]}", fontsize=12)
        elif hasattr(shap_values, 'shape') and len(shap_values.shape) == 3:
            shap.summary_plot(shap_values[:, :, 0], X_shap_sample, show=False)
            plt.title("SHAP Summary Plot (Air Quality)", fontsize=12)
        else:
            shap.summary_plot(shap_values, X_shap_sample, show=False)
            plt.title("SHAP Summary Plot (Air Quality)", fontsize=12)

        shap_plot_path = os.path.join(SHAP_DIR, "aqi_shap_summary.png")
        plt.tight_layout()
        plt.savefig(shap_plot_path, dpi=300, bbox_inches="tight")
        plt.close()
        print(f"SHAP summary plot saved to {shap_plot_path}")
    except Exception as e:
        print(f"SHAP generation warning: {e}")

    print("\nAQI Model Training Complete!")

if __name__ == "__main__":
    train_aqi()
