"""
Model Comparison Experiment: AQI Classification
Strictly compares:
1. Logistic Regression (StandardScaler + LogisticRegression)
2. Random Forest (Existing production baseline evaluated on same test set)
3. XGBoost (XGBClassifier)

Rules:
- Exact same dataset (city_day.csv)
- Exact same 6 features: PM2.5, PM10, NO2, CO, SO2, O3
- Exact same target: AQI_Bucket
- Exact same 80/20 stratified train/test split (random_state=42)
- Exact same SimpleImputer(strategy="median")
- No modification of production files or models
- Results saved to ml_results/comparison/
"""

import os
import sys
import time
import json
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)

# Headless matplotlib
plt.switch_backend('Agg')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = r"C:\Users\Lenovo\Desktop\airquality\city_day.csv"
MODELS_DIR = os.path.join(BASE_DIR, "models")
COMPARISON_DIR = os.path.join(BASE_DIR, "ml_results", "comparison")
os.makedirs(COMPARISON_DIR, exist_ok=True)

LIVE_FEATURE_COLS = ["PM2.5", "PM10", "NO2", "CO", "SO2", "O3"]
TARGET_COL = "AQI_Bucket"

def run_experiment():
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Dataset not found at {DATA_PATH}")

    # 1. Load Data
    df = pd.read_csv(DATA_PATH)
    total_raw_samples = len(df)
    df = df.dropna(subset=[TARGET_COL]).copy()
    total_samples = len(df)

    for col in LIVE_FEATURE_COLS:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    X = df[LIVE_FEATURE_COLS].copy()
    y = df[TARGET_COL].astype(str)

    target_classes = sorted(list(y.unique()))

    # 2. Stratified Train/Test Split (Exact same as production model)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # 3. SimpleImputer with median (Exact same as production pipeline)
    imputer = SimpleImputer(strategy="median")
    X_train_imp = pd.DataFrame(imputer.fit_transform(X_train), columns=LIVE_FEATURE_COLS)
    X_test_imp = pd.DataFrame(imputer.transform(X_test), columns=LIVE_FEATURE_COLS)

    train_samples = len(X_train_imp)
    test_samples = len(X_test_imp)

    # ==========================================================
    # MODEL 1: LOGISTIC REGRESSION
    # ==========================================================
    # Use StandardScaler in a Pipeline since features have different scales
    lr_pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("lr", LogisticRegression(
            max_iter=2000,
            class_weight="balanced",
            random_state=42
        ))
    ])

    lr_start_train = time.perf_counter()
    lr_pipeline.fit(X_train_imp, y_train)
    lr_train_time = time.perf_counter() - lr_start_train

    lr_start_pred = time.perf_counter()
    lr_y_pred = lr_pipeline.predict(X_test_imp)
    lr_pred_time = time.perf_counter() - lr_start_pred

    lr_acc = accuracy_score(y_test, lr_y_pred)
    lr_prec_weighted = precision_score(y_test, lr_y_pred, average="weighted", zero_division=0)
    lr_prec_macro = precision_score(y_test, lr_y_pred, average="macro", zero_division=0)
    lr_rec_weighted = recall_score(y_test, lr_y_pred, average="weighted", zero_division=0)
    lr_rec_macro = recall_score(y_test, lr_y_pred, average="macro", zero_division=0)
    lr_f1_macro = f1_score(y_test, lr_y_pred, average="macro", zero_division=0)
    lr_f1_weighted = f1_score(y_test, lr_y_pred, average="weighted", zero_division=0)
    lr_cm = confusion_matrix(y_test, lr_y_pred, labels=target_classes)

    # Save Logistic Regression Confusion Matrix
    plt.figure(figsize=(8, 6))
    sns.heatmap(
        lr_cm, annot=True, fmt="d", cmap="Blues",
        xticklabels=target_classes, yticklabels=target_classes
    )
    plt.title("Logistic Regression - AQI Classification\nConfusion Matrix (6 Pollutants)")
    plt.xlabel("Predicted Label")
    plt.ylabel("True Label")
    plt.tight_layout()
    lr_cm_path = os.path.join(COMPARISON_DIR, "logistic_regression_confusion_matrix.png")
    plt.savefig(lr_cm_path, dpi=300)
    plt.close()

    # ==========================================================
    # MODEL 2: RANDOM FOREST (EXISTING FINAL MODEL)
    # ==========================================================
    rf_model_path = os.path.join(MODELS_DIR, "live_aqi_model.pkl")
    rf_results_path = os.path.join(BASE_DIR, "ml_results", "live_aqi_results.json")

    # Load existing production model artifact
    rf_artifact = joblib.load(rf_model_path)
    rf_model = rf_artifact["model"]

    # Evaluate on the exact same test set
    rf_start_pred = time.perf_counter()
    rf_y_pred = rf_model.predict(X_test_imp)
    rf_pred_time = time.perf_counter() - rf_start_pred

    rf_acc = accuracy_score(y_test, rf_y_pred)
    rf_prec_weighted = precision_score(y_test, rf_y_pred, average="weighted", zero_division=0)
    rf_prec_macro = precision_score(y_test, rf_y_pred, average="macro", zero_division=0)
    rf_rec_weighted = recall_score(y_test, rf_y_pred, average="weighted", zero_division=0)
    rf_rec_macro = recall_score(y_test, rf_y_pred, average="macro", zero_division=0)
    rf_f1_macro = f1_score(y_test, rf_y_pred, average="macro", zero_division=0)
    rf_f1_weighted = f1_score(y_test, rf_y_pred, average="weighted", zero_division=0)
    rf_cm = confusion_matrix(y_test, rf_y_pred, labels=target_classes)

    # Estimate training time from a benchmark fit or recorded result
    # To be precise, time fit on X_train_imp without saving to production file
    from sklearn.ensemble import RandomForestClassifier
    rf_bench = RandomForestClassifier(
        n_estimators=300,
        random_state=42,
        n_jobs=-1,
        class_weight="balanced"
    )
    rf_start_train = time.perf_counter()
    rf_bench.fit(X_train_imp, y_train)
    rf_train_time = time.perf_counter() - rf_start_train

    # ==========================================================
    # MODEL 3: XGBOOST
    # ==========================================================
    xgb_failed = False
    xgb_fail_reason = ""
    xgb_acc = 0.0
    xgb_prec_weighted = 0.0
    xgb_prec_macro = 0.0
    xgb_rec_weighted = 0.0
    xgb_rec_macro = 0.0
    xgb_f1_macro = 0.0
    xgb_f1_weighted = 0.0
    xgb_train_time = 0.0
    xgb_pred_time = 0.0
    xgb_cm = []

    try:
        import xgboost as xgb
        from xgboost import XGBClassifier

        # Encode string target labels consistently to integers for XGBoost
        label_encoder = LabelEncoder()
        label_encoder.fit(target_classes)
        y_train_encoded = label_encoder.transform(y_train)
        y_test_encoded = label_encoder.transform(y_test)

        # Baseline fair multiclass configuration
        xgb_model = XGBClassifier(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            eval_metric="mlogloss",
            n_jobs=-1
        )

        xgb_start_train = time.perf_counter()
        xgb_model.fit(X_train_imp, y_train_encoded)
        xgb_train_time = time.perf_counter() - xgb_start_train

        xgb_start_pred = time.perf_counter()
        xgb_y_pred_encoded = xgb_model.predict(X_test_imp)
        xgb_pred_time = time.perf_counter() - xgb_start_pred

        # Decode back to original string labels
        xgb_y_pred = label_encoder.inverse_transform(xgb_y_pred_encoded)

        xgb_acc = accuracy_score(y_test, xgb_y_pred)
        xgb_prec_weighted = precision_score(y_test, xgb_y_pred, average="weighted", zero_division=0)
        xgb_prec_macro = precision_score(y_test, xgb_y_pred, average="macro", zero_division=0)
        xgb_rec_weighted = recall_score(y_test, xgb_y_pred, average="weighted", zero_division=0)
        xgb_rec_macro = recall_score(y_test, xgb_y_pred, average="macro", zero_division=0)
        xgb_f1_macro = f1_score(y_test, xgb_y_pred, average="macro", zero_division=0)
        xgb_f1_weighted = f1_score(y_test, xgb_y_pred, average="weighted", zero_division=0)
        xgb_cm = confusion_matrix(y_test, xgb_y_pred, labels=target_classes)

        # Save XGBoost Confusion Matrix
        plt.figure(figsize=(8, 6))
        sns.heatmap(
            xgb_cm, annot=True, fmt="d", cmap="Purples",
            xticklabels=target_classes, yticklabels=target_classes
        )
        plt.title("XGBoost - AQI Classification\nConfusion Matrix (6 Pollutants)")
        plt.xlabel("Predicted Label")
        plt.ylabel("True Label")
        plt.tight_layout()
        xgb_cm_path = os.path.join(COMPARISON_DIR, "xgboost_confusion_matrix.png")
        plt.savefig(xgb_cm_path, dpi=300)
        plt.close()

    except Exception as e:
        xgb_failed = True
        xgb_fail_reason = str(e)

    # ==========================================================
    # SAVE STRUCTURED COMPARISON RESULTS JSON
    # ==========================================================
    results_json = {
        "dataset": "India Air Quality (city_day.csv)",
        "samples": total_samples,
        "train_samples": train_samples,
        "test_samples": test_samples,
        "split": "Stratified 80/20 train/test split (random_state=42)",
        "features": LIVE_FEATURE_COLS,
        "target": TARGET_COL,
        "classes": target_classes,
        "logistic_regression": {
            "accuracy": float(lr_acc),
            "weighted_precision": float(lr_prec_weighted),
            "macro_precision": float(lr_prec_macro),
            "weighted_recall": float(lr_rec_weighted),
            "macro_recall": float(lr_rec_macro),
            "macro_f1": float(lr_f1_macro),
            "weighted_f1": float(lr_f1_weighted),
            "training_time": float(lr_train_time),
            "prediction_time": float(lr_pred_time),
            "confusion_matrix": lr_cm.tolist()
        },
        "random_forest": {
            "accuracy": float(rf_acc),
            "weighted_precision": float(rf_prec_weighted),
            "macro_precision": float(rf_prec_macro),
            "weighted_recall": float(rf_rec_weighted),
            "macro_recall": float(rf_rec_macro),
            "macro_f1": float(rf_f1_macro),
            "weighted_f1": float(rf_f1_weighted),
            "training_time": float(rf_train_time),
            "prediction_time": float(rf_pred_time),
            "confusion_matrix": rf_cm.tolist()
        },
        "xgboost": {
            "status": "FAILED" if xgb_failed else "SUCCESS",
            "failure_reason": xgb_fail_reason if xgb_failed else None,
            "accuracy": float(xgb_acc) if not xgb_failed else None,
            "weighted_precision": float(xgb_prec_weighted) if not xgb_failed else None,
            "macro_precision": float(xgb_prec_macro) if not xgb_failed else None,
            "weighted_recall": float(xgb_rec_weighted) if not xgb_failed else None,
            "macro_recall": float(xgb_rec_macro) if not xgb_failed else None,
            "macro_f1": float(xgb_f1_macro) if not xgb_failed else None,
            "weighted_f1": float(xgb_f1_weighted) if not xgb_failed else None,
            "training_time": float(xgb_train_time) if not xgb_failed else None,
            "prediction_time": float(xgb_pred_time) if not xgb_failed else None,
            "confusion_matrix": xgb_cm.tolist() if not xgb_failed else None
        }
    }

    json_path = os.path.join(COMPARISON_DIR, "model_comparison.json")
    with open(json_path, "w") as f:
        json.dump(results_json, f, indent=2)

    # ==========================================================
    # PRINT REQUIRED TERMINAL OUTPUT
    # ==========================================================
    print("============================================================")
    print("MODEL COMPARISON — AQI CLASSIFICATION")
    print("============================================================")
    print()
    print("Dataset:")
    print("India Air Quality (city_day.csv)")
    print()
    print("Samples:")
    print(total_samples)
    print()
    print("Features:")
    print("PM2.5, PM10, NO2, CO, SO2, O3")
    print()
    print("Target:")
    print(TARGET_COL)
    print()
    print("Train samples:")
    print(train_samples)
    print()
    print("Test samples:")
    print(test_samples)
    print()
    print("Split:")
    print("Stratified 80/20 train/test split (random_state=42)")
    print()
    print("============================================================")
    print("LOGISTIC REGRESSION")
    print("============================================================")
    print()
    print("Accuracy:")
    print(f"{lr_acc * 100:.2f}%")
    print()
    print("Weighted Precision:")
    print(f"{lr_prec_weighted * 100:.2f}%")
    print()
    print("Macro Precision:")
    print(f"{lr_prec_macro * 100:.2f}%")
    print()
    print("Weighted Recall:")
    print(f"{lr_rec_weighted * 100:.2f}%")
    print()
    print("Macro Recall:")
    print(f"{lr_rec_macro * 100:.2f}%")
    print()
    print("Macro F1:")
    print(f"{lr_f1_macro * 100:.2f}%")
    print()
    print("Weighted F1:")
    print(f"{lr_f1_weighted * 100:.2f}%")
    print()
    print("Training Time:")
    print(f"{lr_train_time:.2f} seconds")
    print()
    print("Prediction Time:")
    print(f"{lr_pred_time:.2f} seconds")
    print()
    print("============================================================")
    print("RANDOM FOREST")
    print("============================================================")
    print()
    print("Accuracy:")
    print(f"{rf_acc * 100:.2f}%")
    print()
    print("Weighted Precision:")
    print(f"{rf_prec_weighted * 100:.2f}%")
    print()
    print("Macro Precision:")
    print(f"{rf_prec_macro * 100:.2f}%")
    print()
    print("Weighted Recall:")
    print(f"{rf_rec_weighted * 100:.2f}%")
    print()
    print("Macro Recall:")
    print(f"{rf_rec_macro * 100:.2f}%")
    print()
    print("Macro F1:")
    print(f"{rf_f1_macro * 100:.2f}%")
    print()
    print("Weighted F1:")
    print(f"{rf_f1_weighted * 100:.2f}%")
    print()
    print("Training Time:")
    print(f"{rf_train_time:.2f} seconds")
    print()
    print("Prediction Time:")
    print(f"{rf_pred_time:.2f} seconds")
    print()
    print("============================================================")
    print("XGBOOST")
    print("============================================================")
    print()
    if xgb_failed:
        print("XGBOOST: FAILED")
        print(f"Reason: {xgb_fail_reason}")
    else:
        print("Accuracy:")
        print(f"{xgb_acc * 100:.2f}%")
        print()
        print("Weighted Precision:")
        print(f"{xgb_prec_weighted * 100:.2f}%")
        print()
        print("Macro Precision:")
        print(f"{xgb_prec_macro * 100:.2f}%")
        print()
        print("Weighted Recall:")
        print(f"{xgb_rec_weighted * 100:.2f}%")
        print()
        print("Macro Recall:")
        print(f"{xgb_rec_macro * 100:.2f}%")
        print()
        print("Macro F1:")
        print(f"{xgb_f1_macro * 100:.2f}%")
        print()
        print("Weighted F1:")
        print(f"{xgb_f1_weighted * 100:.2f}%")
        print()
        print("Training Time:")
        print(f"{xgb_train_time:.2f} seconds")
        print()
        print("Prediction Time:")
        print(f"{xgb_pred_time:.2f} seconds")
    print()
    print("============================================================")
    print("FINAL COMPARISON")
    print("============================================================")
    print()
    print(f"{'Model':<22} {'Accuracy':<12} {'Weighted F1':<14} {'Train Time':<12}")
    print("-------------------------------------------------------------")
    print(f"{'Logistic Regression':<22} {lr_acc * 100:>6.2f}%     {lr_f1_weighted * 100:>8.2f}%      {lr_train_time:>6.2f}s")
    print(f"{'Random Forest':<22} {rf_acc * 100:>6.2f}%     {rf_f1_weighted * 100:>8.2f}%      {rf_train_time:>6.2f}s")
    if xgb_failed:
        print(f"{'XGBoost':<22} {'FAILED':>7}       {'FAILED':>9}      {'N/A':>7}")
    else:
        print(f"{'XGBoost':<22} {xgb_acc * 100:>6.2f}%     {xgb_f1_weighted * 100:>8.2f}%      {xgb_train_time:>6.2f}s")
    print("============================================================")
    print()
    print("============================================================")
    print("VIVA SUMMARY")
    print("============================================================")
    print()
    print("Logistic Regression:")
    print(f"Accuracy = {lr_acc * 100:.2f}%")
    print()
    print("Random Forest:")
    print(f"Accuracy = {rf_acc * 100:.2f}%")
    print()
    print("XGBoost:")
    if xgb_failed:
        print(f"FAILED ({xgb_fail_reason})")
    else:
        print(f"Accuracy = {xgb_acc * 100:.2f}%")
    print()
    print("The comparison is experimental and all three models were evaluated on the same held-out test set.")
    print()
    print("Production application remains unchanged.")
    print("============================================================")

if __name__ == "__main__":
    run_experiment()
