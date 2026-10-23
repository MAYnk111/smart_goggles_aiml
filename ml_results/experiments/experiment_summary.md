# Comparative Environmental AQI Machine Learning Experiment (5 Models)

## 1. Executive Summary
This experiment benchmarked five machine-learning and deep-learning architectures for multi-class Air Quality Index (AQI) classification on the Indian National Air Quality dataset (`city_day.csv`, $N = 24,850$ usable records).

Strict evaluation protocol:
- **Features Used**: Strictly 6 Open-Meteo compatible pollutants (`PM2.5`, `PM10`, `NO2`, `CO`, `SO2`, `O3`).
- **Target**: `AQI_Bucket` (6 classes: `Good`, `Moderate`, `Poor`, `Satisfactory`, `Severe`, `Very Poor`).
- **Data Partition**: Identical Stratified **70% Training** ($17,395$), **15% Validation** ($3,727$), and **15% Final Testing** ($3,728$) with fixed `random_state=42`.
- **Zero Leakage**: Imputation and feature scaling were fitted **strictly on training data**. Numerical AQI was excluded. Production application models and files were **completely untouched**.

---

## 2. Consolidated Comparison Table

| Model Architecture | Family | Val Accuracy | Val Macro F1 | **Test Accuracy** | **Test Macro F1** | **Test Weighted F1** | Train Duration | Inference Latency | Model Size |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Extra Trees** | Ensemble (Extremely Randomized Trees) | 79.13% | 77.65% | **79.61%** | **78.31%** | **79.67%** | 3.68s | 0.0637 ms/sample | 208850.77 KB |
| **XGBoost** | Ensemble (Gradient Boosting) | 79.88% | 77.39% | **79.96%** | **77.31%** | **79.79%** | 5.21s | 0.0193 ms/sample | 5733.38 KB |
| **Random Forest** | Ensemble (Bagging) | 79.9% | 77.32% | **80.26%** | **77.64%** | **80.03%** | 5.33s | 0.0245 ms/sample | 201572.82 KB |
| **CatBoost** | Ensemble (Gradient Boosting with Oblivious Trees) | 77.03% | 75.52% | **78.51%** | **77.53%** | **78.75%** | 17.06s | 0.0021 ms/sample | 4889.52 KB |
| **TabNet** | Deep Learning (Sequential Attention & Sparsemax) | 77.38% | 72.8% | **76.39%** | **71.94%** | **75.91%** | 38.79s | 0.0295 ms/sample | 94.61 KB |

---

## 3. Analysis & Key Findings

### A. Winner by Metrics
- **Highest Test Accuracy**: **Random Forest (80.26%)**
- **Highest Macro F1-Score**: **Extra Trees (78.31%)**
- **Lowest Inference Latency**: **CatBoost (0.0021 ms/sample)**

### B. Did TabNet Improve Over Tree-Based Models?
- **Finding**: **No.** TabNet achieved **76.39% Test Accuracy** and **71.94% Macro F1**, trailing behind the tree ensembles (Random Forest, Extra Trees, XGBoost, CatBoost which scored ~80%).
- **Technical Reason**: Tabular data with orthogonal axis-aligned threshold boundaries (like environmental pollutant breakpoint tables) is inherently well-suited to recursive binary partitioning in tree ensembles. Deep attention mechanisms (TabNet) require larger sample volumes (>100k samples) or continuous spatial-temporal context to surpass ensemble trees on small tabular feature spaces ($D=6$).

### C. Which Classes Were Hardest to Classify?
- Based on the confusion matrices across all models, the primary misclassifications occur between:
  1. **`Moderate` vs `Satisfactory`**: The concentration boundaries for PM2.5 and PM10 between Satisfactory (51-100 AQI) and Moderate (101-200 AQI) frequently overlap when secondary pollutants (NO2, SO2, CO) are low.
  2. **`Poor` vs `Very Poor`**: Borderline particulate spikes cause mutual confusion between adjacent severity tiers.
  3. **`Good` and `Severe`** had the highest individual precision and recall across all models due to distinct extreme pollutant values.

### D. Impact of Class Imbalance
- The training set contains $6,180$ Moderate and $5,757$ Satisfactory samples, but only $939$ Good and $936$ Severe samples (a ~6.5:1 ratio).
- Without class weighting, models prioritize majority classes. Applying `class_weight='balanced'` in Random Forest, Extra Trees, and CatBoost substantially elevated Macro Recall for minority classes (`Good` and `Severe`) above 82%.

### E. Limitations and Data Leakage Considerations
1. **Rule Reproduction vs Forecasting**: The dataset labels (`AQI_Bucket`) are mathematically defined by Indian CPCB sub-index lookup tables. This task evaluates the machine learning algorithm's ability to approximate non-linear multi-pollutant threshold functions rather than forecasting future air quality.
2. **Temporal Correlation**: In `city_day.csv`, consecutive daily readings from the same city share temporal autocorrelation. Stratified random sampling evaluates spatial-temporal point-in-time classification.

---

## 4. Generated Artifacts
All experimental artifacts are stored in `ml_results/experiments/`:
- `model_comparison.csv`
- `model_comparison.json`
- `classification_reports.txt`
- `confusion_matrices.png`
- `model_metrics_comparison.png`
- `training_time_comparison.png`
- `tabnet_feature_importance.png`
- `experiment_metadata.json`
- Saved experimental models in `ml_results/experiments/models/`
