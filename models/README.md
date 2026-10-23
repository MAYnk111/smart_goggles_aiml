# Models Directory

Trained model pickle files (`.pkl`) are excluded from git version control as several models exceed GitHub's 100 MB file size limit (ranging up to 220 MB).

## Training Models Locally
You can reproduce and generate the model artifacts at any time using the training scripts in `ml/`:

1. **Live AQI Model (Random Forest)**:
   ```bash
   python ml/train_live_aqi_model.py
   ```
2. **Physiological Stress Model (Random Forest)**:
   ```bash
   python ml/train_stress_model.py
   ```
3. **Comprehensive 5-Model Comparative Experiment (Extra Trees, Random Forest, XGBoost, CatBoost, TabNet)**:
   ```bash
   python ml/run_5models_experiment.py
   ```

*Note: All evaluation metrics, classification reports, confusion matrices, and SHAP explainability visualizations are preserved in `ml_results/`.*
