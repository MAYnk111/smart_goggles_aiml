"""
Model 2: Physiological Stress Classification
Dataset: Wearable Device Dataset from Induced Stress and Structured Exercise Sessions
Target: Stress Classification (Low, Medium, High) derived from authentic self-reported VAS scale (0-10)
Input Features: Physiological signals available from live ESP32 sensors (Heart Rate and Temperature)
IMPORTANT: SpO2 is NOT in the wearable dataset, so it is strictly NOT trained here (handled by rule-based risk fusion).
VALIDATION: Group/Subject-wise train-test split strictly applied to prevent data leakage across temporal windows.
"""

import os
import sys
import json
import datetime
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import GroupShuffleSplit
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix,
)
import shap

# Headless matplotlib
plt.switch_backend('Agg')

# Directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEARABLE_BASE = r"C:\Users\Lenovo\Desktop\wearable-device-dataset-from-induced-stress-and-structured-exercise-sessions-1.0.1\wearable-device-dataset-from-induced-stress-and-structured-exercise-sessions-1.0.1"
MODELS_DIR = os.path.join(BASE_DIR, "models")
RESULTS_DIR = os.path.join(BASE_DIR, "ml_results")
SHAP_DIR = os.path.join(RESULTS_DIR, "shap")

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(SHAP_DIR, exist_ok=True)

FEATURE_COLS = [
    "hr_mean", "hr_std", "hr_min", "hr_max", "hr_range", "hr_median",
    "temp_mean", "temp_std", "temp_min", "temp_max"
]

def map_stress_score_to_class(score: float) -> str:
    """
    Standard Visual Analog Scale (VAS 0-10) categorization:
    - Low: 0.0 - 3.0 (Resting, baseline, relaxed)
    - Medium: 3.1 - 6.0 (Mild to moderate cognitive stress)
    - High: 6.1 - 10.0 (High stress, intense task pressure)
    """
    if score <= 3.0:
        return "Low"
    elif score <= 6.0:
        return "Medium"
    else:
        return "High"

def extract_physiological_features():
    print(f"Reading wearable dataset from: {WEARABLE_BASE}")
    stress_dir = os.path.join(WEARABLE_BASE, "Wearable_Dataset", "STRESS")
    v1_df = pd.read_csv(os.path.join(WEARABLE_BASE, "Stress_Level_v1.csv"), index_col=0)
    v2_df = pd.read_csv(os.path.join(WEARABLE_BASE, "Stress_Level_v2.csv"), index_col=0)

    records = []

    # Process v1 ('S' subjects)
    for sub in v1_df.index:
        s_dir = os.path.join(stress_dir, sub)
        if not os.path.exists(s_dir):
            continue
        try:
            hr_raw = pd.read_csv(os.path.join(s_dir, "HR.csv"))
            temp_raw = pd.read_csv(os.path.join(s_dir, "TEMP.csv"))
            tags_raw = pd.read_csv(os.path.join(s_dir, "tags.csv"), header=None)

            start_utc = datetime.datetime.strptime(hr_raw.columns[0], '%Y-%m-%d %H:%M:%S')
            hr_fs = float(hr_raw.iloc[0, 0])
            hr_vals = hr_raw.iloc[1:, 0].values.astype(float)

            temp_fs = float(temp_raw.iloc[0, 0])
            temp_vals = temp_raw.iloc[1:, 0].values.astype(float)

            tag_times = []
            for _, r in tags_raw.iterrows():
                t = datetime.datetime.strptime(str(r[0]), '%Y-%m-%d %H:%M:%S')
                tag_times.append((t - start_utc).total_seconds())

            if len(tag_times) < 12:
                continue

            # Stage intervals for protocol v1
            stages = [
                ("Baseline", 0, tag_times[1]),
                ("Stroop", tag_times[2], tag_times[3]),
                ("First Rest", tag_times[3], tag_times[4]),
                ("TMCT", tag_times[4], tag_times[5]),
                ("Second Rest", tag_times[5], tag_times[6]),
                ("Real Opinion", tag_times[6], tag_times[7]),
                ("Opposite Opinion", tag_times[8], tag_times[9]),
                ("Subtract", tag_times[10], tag_times[11])
            ]

            for st_name, t_start, t_end in stages:
                if st_name not in v1_df.columns:
                    continue
                score = v1_df.loc[sub, st_name]
                if pd.isna(score):
                    continue

                hr_idx_s = max(0, int(t_start * hr_fs))
                hr_idx_e = min(len(hr_vals), int(t_end * hr_fs))
                hr_sub = hr_vals[hr_idx_s:hr_idx_e]

                temp_idx_s = max(0, int(t_start * temp_fs))
                temp_idx_e = min(len(temp_vals), int(t_end * temp_fs))
                temp_sub = temp_vals[temp_idx_s:temp_idx_e]

                if len(hr_sub) < 5 or len(temp_sub) < 5:
                    continue

                # Sliding window of 30 seconds with 15 second step
                w_hr = int(30 * hr_fs)
                s_hr = int(15 * hr_fs)
                w_temp = int(30 * temp_fs)
                s_temp = int(15 * temp_fs)

                n_windows = max(1, (len(hr_sub) - w_hr) // s_hr + 1)
                for w in range(n_windows):
                    hw = hr_sub[w * s_hr: min(len(hr_sub), w * s_hr + w_hr)]
                    tw = temp_sub[w * s_temp: min(len(temp_sub), w * s_temp + w_temp)]
                    if len(hw) < 5 or len(tw) < 5:
                        continue
                    records.append({
                        "subject": sub,
                        "stage": st_name,
                        "hr_mean": float(np.mean(hw)),
                        "hr_std": float(np.std(hw)),
                        "hr_min": float(np.min(hw)),
                        "hr_max": float(np.max(hw)),
                        "hr_range": float(np.max(hw) - np.min(hw)),
                        "hr_median": float(np.median(hw)),
                        "temp_mean": float(np.mean(tw)),
                        "temp_std": float(np.std(tw)),
                        "temp_min": float(np.min(tw)),
                        "temp_max": float(np.max(tw)),
                        "stress_score": float(score),
                        "stress_class": map_stress_score_to_class(float(score))
                    })
        except Exception as e:
            print(f"Error parsing subject {sub}: {e}")

    # Process v2 ('f' subjects)
    for sub in v2_df.index:
        s_dir = os.path.join(stress_dir, sub)
        if not os.path.exists(s_dir):
            continue
        try:
            hr_raw = pd.read_csv(os.path.join(s_dir, "HR.csv"))
            temp_raw = pd.read_csv(os.path.join(s_dir, "TEMP.csv"))
            tags_raw = pd.read_csv(os.path.join(s_dir, "tags.csv"), header=None)

            start_utc = datetime.datetime.strptime(hr_raw.columns[0], '%Y-%m-%d %H:%M:%S')
            hr_fs = float(hr_raw.iloc[0, 0])
            hr_vals = hr_raw.iloc[1:, 0].values.astype(float)

            temp_fs = float(temp_raw.iloc[0, 0])
            temp_vals = temp_raw.iloc[1:, 0].values.astype(float)

            tag_times = []
            for _, r in tags_raw.iterrows():
                t = datetime.datetime.strptime(str(r[0]), '%Y-%m-%d %H:%M:%S')
                tag_times.append((t - start_utc).total_seconds())

            if len(tag_times) < 8:
                continue

            # Stage intervals for protocol v2
            stages = [
                ("Baseline", 0, tag_times[1]),
                ("TMCT", tag_times[1], tag_times[2]),
                ("First Rest", tag_times[2], tag_times[3]),
                ("Real Opinion", tag_times[3], tag_times[4]),
                ("Opposite Opinion", tag_times[5], tag_times[6]),
                ("Second Rest", tag_times[6], tag_times[7]),
                ("Subtract", tag_times[7], tag_times[8])
            ]

            for st_name, t_start, t_end in stages:
                if st_name not in v2_df.columns:
                    continue
                score = v2_df.loc[sub, st_name]
                if pd.isna(score):
                    continue

                hr_idx_s = max(0, int(t_start * hr_fs))
                hr_idx_e = min(len(hr_vals), int(t_end * hr_fs))
                hr_sub = hr_vals[hr_idx_s:hr_idx_e]

                temp_idx_s = max(0, int(t_start * temp_fs))
                temp_idx_e = min(len(temp_vals), int(t_end * temp_fs))
                temp_sub = temp_vals[temp_idx_s:temp_idx_e]

                if len(hr_sub) < 5 or len(temp_sub) < 5:
                    continue

                w_hr = int(30 * hr_fs)
                s_hr = int(15 * hr_fs)
                w_temp = int(30 * temp_fs)
                s_temp = int(15 * temp_fs)

                n_windows = max(1, (len(hr_sub) - w_hr) // s_hr + 1)
                for w in range(n_windows):
                    hw = hr_sub[w * s_hr: min(len(hr_sub), w * s_hr + w_hr)]
                    tw = temp_sub[w * s_temp: min(len(temp_sub), w * s_temp + w_temp)]
                    if len(hw) < 5 or len(tw) < 5:
                        continue
                    records.append({
                        "subject": sub,
                        "stage": st_name,
                        "hr_mean": float(np.mean(hw)),
                        "hr_std": float(np.std(hw)),
                        "hr_min": float(np.min(hw)),
                        "hr_max": float(np.max(hw)),
                        "hr_range": float(np.max(hw) - np.min(hw)),
                        "hr_median": float(np.median(hw)),
                        "temp_mean": float(np.mean(tw)),
                        "temp_std": float(np.std(tw)),
                        "temp_min": float(np.min(tw)),
                        "temp_max": float(np.max(tw)),
                        "stress_score": float(score),
                        "stress_class": map_stress_score_to_class(float(score))
                    })
        except Exception as e:
            print(f"Error parsing subject {sub}: {e}")

    df = pd.DataFrame(records)
    print(f"Extracted {len(df)} total windows across {df['subject'].nunique()} subjects.")
    print("Class distribution:\n", df['stress_class'].value_counts())
    return df

def train_stress():
    df = extract_physiological_features()
    if df.empty:
        raise ValueError("No physiological data extracted.")

    X = df[FEATURE_COLS].copy()
    y = df["stress_class"].copy()
    groups = df["subject"].copy()

    classes = ["Low", "Medium", "High"]

    # SUBJECT-WISE GROUP TRAIN-TEST SPLIT
    # Note: Using GroupShuffleSplit ensures all windows from the same participant
    # remain solely in train OR solely in test, completely preventing temporal leakage.
    print("\nApplying Subject-Wise Group Split (80% train subjects, 20% test subjects)...")
    gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_idx, test_idx = next(gss.split(X, y, groups=groups))

    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
    train_subjects = groups.iloc[train_idx].unique()
    test_subjects = groups.iloc[test_idx].unique()

    print(f"Train samples: {len(X_train)} across {len(train_subjects)} subjects: {list(train_subjects)}")
    print(f"Test samples:  {len(X_test)} across {len(test_subjects)} subjects: {list(test_subjects)}")

    # Train Random Forest Classifier
    print("Training Random Forest Classifier for Stress Detection (n_estimators=300, class_weight='balanced')...")
    rf = RandomForestClassifier(
        n_estimators=300,
        random_state=42,
        n_jobs=-1,
        class_weight="balanced"
    )
    rf.fit(X_train, y_train)

    # Predictions & Honest Evaluation on Unseen Subjects
    y_pred = rf.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, average="weighted", zero_division=0)
    rec = recall_score(y_test, y_pred, average="weighted", zero_division=0)
    f1 = f1_score(y_test, y_pred, average="weighted", zero_division=0)
    report_dict = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
    report_str = classification_report(y_test, y_pred, zero_division=0)

    print("\n--- Honest Subject-Wise Evaluation on Unseen Subjects ---")
    print(f"Accuracy:  {acc:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall:    {rec:.4f}")
    print(f"F1 Score:  {f1:.4f}")
    print("\nClassification Report:\n", report_str)

    # Confusion Matrix
    cm = confusion_matrix(y_test, y_pred, labels=classes)
    plt.figure(figsize=(7, 5))
    sns.heatmap(
        cm, annot=True, fmt="d", cmap="Purples",
        xticklabels=classes, yticklabels=classes
    )
    plt.title("Physiological Stress Classification - Confusion Matrix\n(Subject-Wise Unseen Test Set)")
    plt.xlabel("Predicted Stress")
    plt.ylabel("True Stress")
    plt.tight_layout()
    cm_path = os.path.join(RESULTS_DIR, "stress_confusion_matrix.png")
    plt.savefig(cm_path, dpi=300)
    plt.close()
    print(f"Confusion matrix saved to {cm_path}")

    # Feature Importance
    feat_imp = pd.DataFrame({
        "Feature": FEATURE_COLS,
        "Importance": rf.feature_importances_
    }).sort_values(by="Importance", ascending=False)
    fi_path = os.path.join(RESULTS_DIR, "stress_feature_importance.csv")
    feat_imp.to_csv(fi_path, index=False)
    print(f"Feature importance saved to {fi_path}")

    # Save Model Artifacts
    model_artifact = {
        "model": rf,
        "classes": classes,
        "features": FEATURE_COLS,
        "vas_thresholds": {
            "Low": "<= 3.0",
            "Medium": "3.1 to 6.0",
            "High": "> 6.0"
        }
    }
    model_path = os.path.join(MODELS_DIR, "stress_model.pkl")
    joblib.dump(model_artifact, model_path)
    print(f"Stress model saved to {model_path}")

    features_path = os.path.join(MODELS_DIR, "stress_features.pkl")
    joblib.dump(FEATURE_COLS, features_path)
    print(f"Stress features saved to {features_path}")

    # Save JSON results
    results_json = {
        "model_name": "Physiological Stress Random Forest Classifier",
        "validation_strategy": "Subject-Wise Group Train-Test Split (GroupShuffleSplit)",
        "train_subjects": list(train_subjects),
        "test_subjects": list(test_subjects),
        "features": FEATURE_COLS,
        "classes": classes,
        "accuracy": float(acc),
        "precision_weighted": float(prec),
        "recall_weighted": float(rec),
        "f1_weighted": float(f1),
        "classification_report": report_dict,
        "top_features": feat_imp.to_dict(orient="records")
    }
    results_path = os.path.join(RESULTS_DIR, "stress_results.json")
    with open(results_path, "w") as f:
        json.dump(results_json, f, indent=2)
    print(f"Results saved to {results_path}")

    # SHAP Explainability
    print("\nComputing SHAP values for Physiological Stress Model...")
    try:
        X_shap_sample = X_test.sample(n=min(150, len(X_test)), random_state=42)
        explainer = shap.TreeExplainer(rf)
        shap_values = explainer.shap_values(X_shap_sample)

        plt.figure(figsize=(10, 6))
        if isinstance(shap_values, list):
            shap.summary_plot(shap_values[0], X_shap_sample, show=False)
            plt.title("SHAP Summary Plot for Stress Detection (Low Stress Class)", fontsize=12)
        elif hasattr(shap_values, 'shape') and len(shap_values.shape) == 3:
            shap.summary_plot(shap_values[:, :, 0], X_shap_sample, show=False)
            plt.title("SHAP Summary Plot for Stress Detection", fontsize=12)
        else:
            shap.summary_plot(shap_values, X_shap_sample, show=False)
            plt.title("SHAP Summary Plot for Stress Detection", fontsize=12)

        shap_plot_path = os.path.join(SHAP_DIR, "stress_shap_summary.png")
        plt.tight_layout()
        plt.savefig(shap_plot_path, dpi=300, bbox_inches="tight")
        plt.close()
        print(f"SHAP summary plot saved to {shap_plot_path}")
    except Exception as e:
        print(f"SHAP generation warning: {e}")

    print("\nPhysiological Stress Model Training Complete!")

if __name__ == "__main__":
    train_stress()
