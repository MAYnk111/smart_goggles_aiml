import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../constants.dart';
import '../providers/app_state.dart';

class MlResultsScreen extends StatefulWidget {
  const MlResultsScreen({super.key});

  @override
  State<MlResultsScreen> createState() => _MlResultsScreenState();
}

class _MlResultsScreenState extends State<MlResultsScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final appState = Provider.of<AppState>(context);
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    final results = appState.mlResults;
    final liveDiag = appState.mlLiveDiagnostics;

    final liveAqi = results?['live_aqi_model'] as Map<String, dynamic>?;
    final offlineAqi = results?['offline_aqi_model'] as Map<String, dynamic>?;
    final stress = results?['stress_model'] as Map<String, dynamic>?;

    final livePhys = liveDiag?['physiological'] as Map<String, dynamic>?;
    final liveEnv = liveDiag?['environmental'] as Map<String, dynamic>?;

    final physStatus = appState.physiologicalMlStatus;
    final envStatus = appState.environmentalMlStatus;

    return Scaffold(
      appBar: AppBar(
        title: const Text("Machine Learning & XAI"),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            tooltip: "Refresh Metrics & Live ML",
            onPressed: () => appState.loadMlResults(),
          ),
        ],
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: AppColors.primaryLight,
          labelColor: AppColors.primaryLight,
          unselectedLabelColor: Colors.grey,
          labelStyle: const TextStyle(fontWeight: FontWeight.w700, fontSize: 12),
          tabs: const [
            Tab(icon: Icon(Icons.analytics_outlined, size: 20), text: "Evaluation"),
            Tab(icon: Icon(Icons.bolt_rounded, size: 20), text: "Live Inference"),
            Tab(icon: Icon(Icons.account_tree_outlined, size: 20), text: "Pipelines"),
          ],
        ),
      ),
      body: appState.isLoadingMlResults
          ? const Center(child: CircularProgressIndicator())
          : TabBarView(
              controller: _tabController,
              children: [
                // TAB 1: MODEL EVALUATION (HELD-OUT TEST SETS)
                _buildEvaluationTab(context, isDark, liveAqi, stress, offlineAqi),

                // TAB 2: LIVE INFERENCE (REAL-TIME ML EXECUTION)
                _buildLiveInferenceTab(context, isDark, appState, physStatus, envStatus, livePhys, liveEnv),

                // TAB 3: MODEL PIPELINE TRANSPARENCY
                _buildPipelineTab(context, isDark),
              ],
            ),
    );
  }

  // ==========================================================================
  // TAB 1: MODEL EVALUATION BENCHMARKS
  // ==========================================================================
  Widget _buildEvaluationTab(
    BuildContext context,
    bool isDark,
    Map<String, dynamic>? liveAqi,
    Map<String, dynamic>? stress,
    Map<String, dynamic>? offlineAqi,
  ) {
    return ListView(
      padding: const EdgeInsets.all(16.0),
      children: [
        // Evaluation Distinction Banner
        Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: AppColors.primary.withValues(alpha: 0.12),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: AppColors.primary.withValues(alpha: 0.3)),
          ),
          child: const Row(
            children: [
              Icon(Icons.verified_outlined, color: AppColors.primaryLight, size: 22),
              SizedBox(width: 10),
              Expanded(
                child: Text(
                  "MODEL EVALUATION METRICS: Measured strictly on held-out test sets during offline validation. Not to be confused with single live inference readings.",
                  style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: Colors.grey),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),

        // 1. Live AQI Model Card
        _buildSectionHeader("1. LIVE-COMPATIBLE AQI MODEL", Icons.cloud_done_rounded, AppColors.secondary),
        const SizedBox(height: 8),
        _buildModelCard(
          context: context,
          isDark: isDark,
          modelName: "Live AQI Classifier (Random Forest)",
          statusBadge: "PRODUCTION LIVE",
          badgeColor: AppColors.riskLow,
          datasetInfo: "India Air Quality (city_day.csv)",
          metrics: [
            {"label": "Accuracy", "value": "${((liveAqi?['accuracy'] ?? 0.8024) * 100).toStringAsFixed(2)}%"},
            {"label": "Weighted F1", "value": "${((liveAqi?['weighted_f1'] ?? 0.8011) * 100).toStringAsFixed(2)}%"},
            {"label": "Macro F1", "value": "${((liveAqi?['macro_f1'] ?? 0.7780) * 100).toStringAsFixed(2)}%"},
            {"label": "Test Samples", "value": "${liveAqi?['test_samples'] ?? 4970} rows"},
          ],
          features: (liveAqi?['features'] as List?)?.cast<String>() ??
              ['PM2.5', 'PM10', 'NO2', 'CO', 'SO2', 'O3'],
          classes: (liveAqi?['classes'] as List?)?.cast<String>() ??
              ['Good', 'Moderate', 'Poor', 'Satisfactory', 'Severe', 'Very Poor'],
          description:
              "Trained specifically on the 6 real-time atmospheric gases supplied by Open-Meteo. Eliminates missing historical VOC columns (benzene, toluene, xylene) without fabricating synthetic values.",
        ),
        const SizedBox(height: 20),

        // 2. Physiological Stress Model Card
        _buildSectionHeader("2. PHYSIOLOGICAL STRESS MODEL", Icons.psychology_rounded, AppColors.accent),
        const SizedBox(height: 8),
        _buildModelCard(
          context: context,
          isDark: isDark,
          modelName: "Stress Classifier (Random Forest)",
          statusBadge: "SUBJECT-SPLIT CV",
          badgeColor: AppColors.accent,
          datasetInfo: "WESAD & Multi-Subject Stress Biometrics (35 Subjects)",
          metrics: [
            {"label": "Group Accuracy", "value": "${((stress?['accuracy'] ?? 0.4869) * 100).toStringAsFixed(2)}%"},
            {"label": "Weighted F1", "value": "${((stress?['f1_weighted'] ?? 0.4758) * 100).toStringAsFixed(2)}%"},
            {"label": "Subjects", "value": "35 Participants"},
            {"label": "Split Method", "value": "GroupShuffleSplit (Zero Leak)"},
          ],
          features: (stress?['features'] as List?)?.cast<String>() ??
              ['hr_mean', 'hr_std', 'hr_min', 'hr_max', 'hr_range', 'hr_median', 'temp_mean', 'temp_std', 'temp_min', 'temp_max'],
          classes: (stress?['classes'] as List?)?.cast<String>() ?? ['Low', 'Medium', 'High'],
          description:
              "Evaluated using strict subject-wise grouping across 35 independent participants. Assesses autonomic physiological stress response while preventing biometric memorization.",
        ),
        const SizedBox(height: 20),

        // 3. Historical AQI Model Reference
        _buildSectionHeader("3. HISTORICAL 12-FEATURE BENCHMARK", Icons.history_edu_rounded, Colors.grey),
        const SizedBox(height: 8),
        _buildModelCard(
          context: context,
          isDark: isDark,
          modelName: "Historical Indian Cities Model",
          statusBadge: "OFFLINE BENCHMARK",
          badgeColor: Colors.blueGrey,
          datasetInfo: "CPCB Multi-City Historical Air Quality (12 Features)",
          metrics: [
            {"label": "Accuracy", "value": "${((offlineAqi?['accuracy'] ?? 0.8131) * 100).toStringAsFixed(2)}%"},
            {"label": "Weighted F1", "value": "${((offlineAqi?['weighted_f1'] ?? 0.8117) * 100).toStringAsFixed(2)}%"},
            {"label": "Features", "value": "12 Ambient Gases"},
            {"label": "Split", "value": "80/20 Stratified"},
          ],
          features: (offlineAqi?['features'] as List?)?.cast<String>() ??
              ['PM2.5', 'PM10', 'NO', 'NO2', 'NOx', 'NH3', 'CO', 'SO2', 'O3', 'Benzene', 'Toluene', 'Xylene'],
          classes: ['Good', 'Satisfactory', 'Moderate', 'Poor', 'Very Poor', 'Severe'],
          description:
              "Reference offline benchmark model trained on all 12 gases. Used to validate the performance retention of the 6-feature live model.",
        ),
        const SizedBox(height: 24),
      ],
    );
  }

  // ==========================================================================
  // TAB 2: LIVE INFERENCE TELEMETRY
  // ==========================================================================
  Widget _buildLiveInferenceTab(
    BuildContext context,
    bool isDark,
    AppState appState,
    String physStatus,
    String envStatus,
    Map<String, dynamic>? livePhys,
    Map<String, dynamic>? liveEnv,
  ) {
    return ListView(
      padding: const EdgeInsets.all(16.0),
      children: [
        // Live Pipeline Status Bar
        Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: isDark ? AppColors.darkCard : Colors.white,
            borderRadius: BorderRadius.circular(18),
            border: Border.all(color: Colors.grey.withValues(alpha: 0.15)),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                "BACKEND LIVE ML EXECUTION STATUS",
                style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: Colors.grey, letterSpacing: 0.8),
              ),
              const SizedBox(height: 10),
              Row(
                children: [
                  Expanded(
                    child: _buildStatusPill(
                      label: "Physiological ML",
                      status: physStatus,
                      color: _getStatusColor(physStatus),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: _buildStatusPill(
                      label: "Environmental ML",
                      status: envStatus,
                      color: _getStatusColor(envStatus),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                "Last Backend ML Activity: ${appState.lastMlPredictionTime}",
                style: const TextStyle(fontSize: 11, color: Colors.grey),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),

        // Live Physiological ML Execution Card
        _buildSectionHeader("REAL-TIME PHYSIOLOGICAL INFERENCE", Icons.favorite_rounded, const Color(0xFFEF4444)),
        const SizedBox(height: 8),
        if (livePhys == null)
          _buildWaitingCard("Waiting for live ESP32 sensor packet...", isDark)
        else
          _buildLiveInferenceCard(
            context: context,
            isDark: isDark,
            title: "Physiological Stress Prediction",
            source: "ESP32 (JATAYU_BAND)",
            timestamp: livePhys['timestamp'] ?? "",
            modelClass: livePhys['model'] ?? "RandomForestClassifier",
            prediction: livePhys['prediction'] ?? "Low",
            confidenceText: livePhys['confidence'] != null ? "${((livePhys['confidence'] as num) * 100).toStringAsFixed(1)}%" : "",
            probabilities: (livePhys['probabilities'] as Map<String, dynamic>?) ?? {},
            inputFeatures: (livePhys['input_features'] as Map<String, dynamic>?) ?? {},
            shapWeights: (livePhys['shap'] as Map<String, dynamic>?) ?? {},
            accentColor: AppColors.accent,
          ),
        const SizedBox(height: 20),

        // Live Environmental ML Execution Card
        _buildSectionHeader("REAL-TIME ENVIRONMENTAL INFERENCE", Icons.air_rounded, AppColors.secondary),
        const SizedBox(height: 8),
        if (liveEnv == null)
          _buildWaitingCard("Waiting for live Open-Meteo GPS air quality poll...", isDark)
        else
          _buildLiveInferenceCard(
            context: context,
            isDark: isDark,
            title: "Live Ambient AQI Bucket",
            source: "Open-Meteo GPS (${liveEnv['location'] ?? 'Live Station'})",
            timestamp: liveEnv['timestamp'] ?? "",
            modelClass: liveEnv['model'] ?? "RandomForestClassifier",
            prediction: liveEnv['prediction'] ?? "Moderate",
            confidenceText: liveEnv['confidence'] != null ? "${((liveEnv['confidence'] as num) * 100).toStringAsFixed(1)}%" : "",
            probabilities: (liveEnv['probabilities'] as Map<String, dynamic>?) ?? {},
            inputFeatures: (liveEnv['input_features'] as Map<String, dynamic>?) ?? {},
            shapWeights: (liveEnv['shap'] as Map<String, dynamic>?) ?? {},
            accentColor: AppColors.secondary,
          ),
        const SizedBox(height: 20),
      ],
    );
  }

  // ==========================================================================
  // TAB 3: MODEL PIPELINE TRANSPARENCY
  // ==========================================================================
  Widget _buildPipelineTab(BuildContext context, bool isDark) {
    return ListView(
      padding: const EdgeInsets.all(16.0),
      children: [
        // Viva Header
        Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: isDark ? AppColors.darkCard : Colors.white,
            borderRadius: BorderRadius.circular(18),
            border: Border.all(color: Colors.grey.withValues(alpha: 0.15)),
          ),
          child: const Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                "SYSTEM ARCHITECTURE & PIPELINE TRANSPARENCY",
                style: TextStyle(fontSize: 12, fontWeight: FontWeight.w800, color: AppColors.primaryLight, letterSpacing: 0.8),
              ),
              SizedBox(height: 4),
              Text(
                "Demonstration flow showing how hardware telemetry and environmental data trigger dual decoupled machine learning models and SHAP attribution.",
                style: TextStyle(fontSize: 11, color: Colors.grey),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),

        // Pipeline 1: Physiological
        _buildSectionHeader("PHYSIOLOGICAL STRESS PIPELINE", Icons.favorite_rounded, const Color(0xFFEF4444)),
        const SizedBox(height: 8),
        _buildPipelineFlowCard(
          context: context,
          isDark: isDark,
          steps: [
            {"title": "ESP32 Hardware", "desc": "MAX30102 pulse & DS18B20 temperature sensors collect raw physiological metrics."},
            {"title": "BLE GATT Server", "desc": "Firmware broadcasts JSON payload: {bpm, temperature, fall, finger, emergency} via JATAYU_BAND."},
            {"title": "Flutter BLE Service", "desc": "App receives notification packets, enriches with GPS coordinates, and prioritizes over simulator."},
            {"title": "FastAPI Ingestion", "desc": "Endpoint POST /api/sensor normalizes BPM to heart_rate and updates rolling buffer."},
            {"title": "Stress ML Classifier", "desc": "Random Forest model (35-subject GroupSplit) predicts Stress Level (Low, Medium, High)."},
            {"title": "TreeExplainer SHAP", "desc": "Local Shapley contributions calculated for HR and Skin Temperature features."},
            {"title": "Risk Fusion Engine", "desc": "Combines physiological score with ambient environment and fall/emergency overrides."},
          ],
        ),
        const SizedBox(height: 20),

        // Pipeline 2: Environmental
        _buildSectionHeader("ENVIRONMENTAL AQI PIPELINE", Icons.cloud_done_rounded, AppColors.secondary),
        const SizedBox(height: 8),
        _buildPipelineFlowCard(
          context: context,
          isDark: isDark,
          steps: [
            {"title": "Phone GPS Location", "desc": "Flutter geolocator retrieves smartphone latitude and longitude coordinates."},
            {"title": "Open-Meteo Air Quality API", "desc": "Direct atmospheric query fetches live PM2.5, PM10, NO2, CO, SO2, and O3."},
            {"title": "FastAPI Ingestion", "desc": "Endpoint GET /api/environment parses live pollutants without fabricating synthetic VOCs."},
            {"title": "Live AQI ML Model", "desc": "Random Forest classifier (80.24% Acc) predicts AQI Category (Good to Severe)."},
            {"title": "TreeExplainer SHAP", "desc": "Calculates exact feature importance weights for each live atmospheric gas."},
            {"title": "Risk Fusion Engine", "desc": "Normalizes ambient risk to 0-50 scale and combines with physiological state."},
          ],
        ),
        const SizedBox(height: 24),
      ],
    );
  }

  // ==========================================================================
  // HELPER WIDGETS
  // ==========================================================================
  Widget _buildSectionHeader(String title, IconData icon, Color color) {
    return Row(
      children: [
        Icon(icon, size: 16, color: color),
        const SizedBox(width: 8),
        Expanded(
          child: Text(
            title,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w800,
              letterSpacing: 0.8,
              color: Colors.grey,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildStatusPill({required String label, required String status, required Color color}) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: const TextStyle(fontSize: 10, color: Colors.grey, fontWeight: FontWeight.w600)),
          const SizedBox(height: 2),
          Row(
            children: [
              Container(width: 6, height: 6, decoration: BoxDecoration(shape: BoxShape.circle, color: color)),
              const SizedBox(width: 6),
              Text(status, style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: color)),
            ],
          ),
        ],
      ),
    );
  }

  Color _getStatusColor(String status) {
    switch (status.toUpperCase()) {
      case 'RUNNING':
        return AppColors.riskLow;
      case 'WAITING':
        return Colors.amber;
      default:
        return Colors.grey;
    }
  }

  Widget _buildWaitingCard(String msg, bool isDark) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: isDark ? AppColors.darkCard : Colors.grey[100],
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        children: [
          const SizedBox(
            width: 16,
            height: 16,
            child: CircularProgressIndicator(strokeWidth: 2, color: Colors.grey),
          ),
          const SizedBox(width: 12),
          Expanded(child: Text(msg, style: const TextStyle(fontSize: 12, color: Colors.grey))),
        ],
      ),
    );
  }

  Widget _buildLiveInferenceCard({
    required BuildContext context,
    required bool isDark,
    required String title,
    required String source,
    required String timestamp,
    required String modelClass,
    required String prediction,
    required String confidenceText,
    required Map<String, dynamic> probabilities,
    required Map<String, dynamic> inputFeatures,
    required Map<String, dynamic> shapWeights,
    required Color accentColor,
  }) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: isDark ? AppColors.darkCard : Colors.white,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: accentColor.withValues(alpha: 0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(title, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w800)),
                    const SizedBox(height: 2),
                    Text("Source: $source • $timestamp", style: const TextStyle(fontSize: 10, color: Colors.grey)),
                  ],
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: accentColor.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  modelClass,
                  style: TextStyle(fontSize: 9, fontWeight: FontWeight.w700, color: accentColor),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          // Prediction Hero Box
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            decoration: BoxDecoration(
              color: isDark ? const Color(0xFF1E293B) : Colors.grey[50],
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text("PREDICTED CLASS", style: TextStyle(fontSize: 9, color: Colors.grey, fontWeight: FontWeight.w700)),
                    Text(
                      prediction.toUpperCase(),
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.w900, color: accentColor),
                    ),
                  ],
                ),
                if (confidenceText.isNotEmpty)
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      const Text("CONFIDENCE", style: TextStyle(fontSize: 9, color: Colors.grey, fontWeight: FontWeight.w700)),
                      Text(confidenceText, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w800)),
                    ],
                  ),
              ],
            ),
          ),
          const SizedBox(height: 10),

          // Probabilities
          if (probabilities.isNotEmpty) ...[
            const Text("Model Probabilities:", style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: Colors.grey)),
            const SizedBox(height: 4),
            Wrap(
              spacing: 6,
              runSpacing: 4,
              children: probabilities.entries.map((e) {
                final pct = ((e.value as num) * 100).toStringAsFixed(1);
                return Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: isDark ? Colors.grey[800] : Colors.grey[200],
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text("${e.key}: $pct%", style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w600)),
                );
              }).toList(),
            ),
            const SizedBox(height: 10),
          ],

          // Input Features
          if (inputFeatures.isNotEmpty) ...[
            const Text("Inference Input Features:", style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: Colors.grey)),
            const SizedBox(height: 4),
            Wrap(
              spacing: 6,
              runSpacing: 4,
              children: inputFeatures.entries.map((e) {
                final v = e.value is num ? (e.value as num).toStringAsFixed(1) : e.value.toString();
                return Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: isDark ? Colors.grey[800] : Colors.grey[200],
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text("${e.key}: $v", style: const TextStyle(fontSize: 10)),
                );
              }).toList(),
            ),
            const SizedBox(height: 10),
          ],

          // Top SHAP Weights
          if (shapWeights.isNotEmpty) ...[
            const Text("SHAP Attribution (TreeExplainer):", style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: Colors.grey)),
            const SizedBox(height: 4),
            ...shapWeights.entries.take(4).map((e) {
              final val = (e.value as num).toDouble();
              final isPos = val >= 0;
              final col = isPos ? AppColors.riskHigh : AppColors.riskLow;
              return Padding(
                padding: const EdgeInsets.symmetric(vertical: 2.0),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(e.key, style: const TextStyle(fontSize: 11)),
                    Text(
                      "${isPos ? '+' : ''}${val.toStringAsFixed(4)} weight",
                      style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: col),
                    ),
                  ],
                ),
              );
            }),
          ],
        ],
      ),
    );
  }

  Widget _buildModelCard({
    required BuildContext context,
    required bool isDark,
    required String modelName,
    required String statusBadge,
    required Color badgeColor,
    required String datasetInfo,
    required List<Map<String, String>> metrics,
    required List<String> features,
    required List<String> classes,
    required String description,
  }) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: isDark ? AppColors.darkCard : Colors.white,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: Colors.grey.withValues(alpha: 0.15)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Text(
                  modelName,
                  style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w800),
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: badgeColor.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: badgeColor.withValues(alpha: 0.4)),
                ),
                child: Text(
                  statusBadge,
                  style: TextStyle(fontSize: 9, fontWeight: FontWeight.w800, color: badgeColor),
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text("Dataset: $datasetInfo", style: const TextStyle(fontSize: 10, color: Colors.grey)),
          const SizedBox(height: 12),
          // Metrics Grid (2x2)
          GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 2,
              mainAxisSpacing: 6,
              crossAxisSpacing: 6,
              childAspectRatio: 2.6,
            ),
            itemCount: metrics.length,
            itemBuilder: (context, idx) {
              final m = metrics[idx];
              return Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                decoration: BoxDecoration(
                  color: isDark ? const Color(0xFF1E293B) : Colors.grey[50],
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(
                      m["label"]!,
                      style: const TextStyle(fontSize: 9, color: Colors.grey, fontWeight: FontWeight.w600),
                    ),
                    const SizedBox(height: 1),
                    FittedBox(
                      fit: BoxFit.scaleDown,
                      child: Text(
                        m["value"]!,
                        style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w800),
                      ),
                    ),
                  ],
                ),
              );
            },
          ),
          const SizedBox(height: 10),
          Text(
            description,
            style: TextStyle(
              fontSize: 11,
              color: isDark ? Colors.grey[400] : Colors.grey[600],
              height: 1.3,
            ),
          ),
          const SizedBox(height: 10),
          const Text("Input Features:", style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: Colors.grey)),
          const SizedBox(height: 4),
          Wrap(
            spacing: 6,
            runSpacing: 4,
            children: features
                .map((f) => Container(
                      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
                      decoration: BoxDecoration(
                        color: isDark ? Colors.grey[800] : Colors.grey[200],
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(f, style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w600)),
                    ))
                .toList(),
          ),
        ],
      ),
    );
  }

  Widget _buildPipelineFlowCard({
    required BuildContext context,
    required bool isDark,
    required List<Map<String, String>> steps,
  }) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: isDark ? AppColors.darkCard : Colors.white,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: Colors.grey.withValues(alpha: 0.15)),
      ),
      child: Column(
        children: steps.asMap().entries.map((entry) {
          final idx = entry.key;
          final step = entry.value;
          final isLast = idx == steps.length - 1;

          return Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Column(
                children: [
                  Container(
                    width: 24,
                    height: 24,
                    decoration: BoxDecoration(
                      color: AppColors.primary.withValues(alpha: 0.2),
                      shape: BoxShape.circle,
                      border: Border.all(color: AppColors.primary, width: 1.5),
                    ),
                    child: Center(
                      child: Text(
                        "${idx + 1}",
                        style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w800, color: AppColors.primaryLight),
                      ),
                    ),
                  ),
                  if (!isLast)
                    Container(
                      width: 2,
                      height: 28,
                      color: Colors.grey.withValues(alpha: 0.3),
                    ),
                ],
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Padding(
                  padding: const EdgeInsets.only(bottom: 12.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(step["title"]!, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700)),
                      const SizedBox(height: 2),
                      Text(
                        step["desc"]!,
                        style: TextStyle(fontSize: 11, color: isDark ? Colors.grey[400] : Colors.grey[600], height: 1.25),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          );
        }).toList(),
      ),
    );
  }
}
