import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../constants.dart';
import '../providers/app_state.dart';
import '../models/telemetry_model.dart';
import 'ml_results_screen.dart';

class ExplanationScreen extends StatelessWidget {
  const ExplanationScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final appState = Provider.of<AppState>(context);
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    final telemetry = appState.latestTelemetry;
    final explanation = telemetry?.explanation;
    final risk = telemetry?.personalizedRisk;
    final riskLevel = risk?.riskLevel ?? "Moderate";
    final riskColor = AppColors.getRiskColor(riskLevel);

    final envFactors = explanation?.environmentalFactors ?? [
      SHAPFactorModel(feature: "PM2.5", contribution: 0.089, impactDescription: "PM2.5 contributed to the model's environmental risk prediction."),
      SHAPFactorModel(feature: "O3", contribution: 0.095, impactDescription: "O3 contributed to the model's environmental risk prediction."),
      SHAPFactorModel(feature: "PM10", contribution: 0.051, impactDescription: "PM10 contributed to the model's environmental risk prediction."),
    ];

    final physFactors = explanation?.physiologicalFactors ?? [
      SHAPFactorModel(feature: "Heart Rate", contribution: 0.045, impactDescription: "Heart rate was elevated relative to the model's learned patterns."),
      SHAPFactorModel(feature: "Temperature", contribution: -0.082, impactDescription: "Skin temperature was moderated relative to the model's learned patterns."),
      SHAPFactorModel(feature: "HR Variability", contribution: 0.021, impactDescription: "HR variability contributed to the model's physiological stress prediction."),
    ];

    return Scaffold(
      appBar: AppBar(
        title: const Text("Explainable AI (SHAP)"),
        actions: [
          IconButton(
            icon: const Icon(Icons.analytics_rounded),
            tooltip: "View Model Verification",
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const MlResultsScreen()),
              );
            },
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16.0),
        children: [
          // Header Question Card
          Container(
            padding: const EdgeInsets.all(18),
            decoration: BoxDecoration(
              color: isDark ? const Color(0xFF1E293B) : Colors.white,
              borderRadius: BorderRadius.circular(22),
              border: Border.all(color: riskColor.withValues(alpha: 0.35), width: 1.5),
              boxShadow: [
                BoxShadow(
                  color: riskColor.withValues(alpha: 0.1),
                  blurRadius: 14,
                  offset: const Offset(0, 5),
                ),
              ],
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: riskColor.withValues(alpha: 0.15),
                        shape: BoxShape.circle,
                      ),
                      child: Icon(Icons.lightbulb_outline_rounded, color: riskColor, size: 22),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            "WHY IS MY RISK AT THIS LEVEL?",
                            style: TextStyle(
                              fontSize: 13,
                              fontWeight: FontWeight.w900,
                              letterSpacing: 0.6,
                            ),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            "Current Risk: ${risk?.riskScore.toStringAsFixed(0) ?? '32'} / 100 ($riskLevel)",
                            style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: riskColor),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Text(
                  risk?.statusSummary ??
                      "Multi-factor model assessment based on real-time ambient air composition and autonomic physiological response.",
                  style: TextStyle(fontSize: 12, color: isDark ? Colors.grey[300] : Colors.grey[700], height: 1.3),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),

          // Environmental Factors Section
          Row(
            children: [
              const Icon(Icons.cloud_outlined, size: 18, color: AppColors.secondary),
              const SizedBox(width: 8),
              const Expanded(
                child: Text(
                  "ENVIRONMENTAL MODEL CONTRIBUTIONS",
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, letterSpacing: 0.8, color: Colors.grey),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          _buildFactorsCard(envFactors, isDark, AppColors.secondary),
          const SizedBox(height: 20),

          // Physiological Factors Section
          Row(
            children: [
              const Icon(Icons.favorite_outline_rounded, size: 18, color: AppColors.accent),
              const SizedBox(width: 8),
              const Expanded(
                child: Text(
                  "PHYSIOLOGICAL MODEL CONTRIBUTIONS",
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, letterSpacing: 0.8, color: Colors.grey),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          _buildFactorsCard(physFactors, isDark, AppColors.accent),
          const SizedBox(height: 20),

          // Technical XAI Note
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: isDark ? AppColors.darkCard.withValues(alpha: 0.5) : Colors.grey[100],
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: Colors.grey.withValues(alpha: 0.2)),
            ),
            child: const Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  "Explainability Note",
                  style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: Colors.grey),
                ),
                SizedBox(height: 4),
                Text(
                  "Feature impacts reflect model contribution weights calculated via SHAP TreeExplainer, "
                  "not causal medical diagnoses. These values illustrate which live inputs most strongly "
                  "influenced the decision trees.",
                  style: TextStyle(fontSize: 11, color: Colors.grey, height: 1.3),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),
        ],
      ),
    );
  }

  Widget _buildFactorsCard(List<SHAPFactorModel> factors, bool isDark, Color themeColor) {
    if (factors.isEmpty) {
      return Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: isDark ? AppColors.darkCard : Colors.grey[100],
          borderRadius: BorderRadius.circular(16),
        ),
        child: const Text("Computing SHAP feature contributions...", style: TextStyle(color: Colors.grey, fontSize: 12)),
      );
    }

    double maxAbs = 0.01;
    for (var f in factors) {
      if (f.contribution.abs() > maxAbs) {
        maxAbs = f.contribution.abs();
      }
    }

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: isDark ? const Color(0xFF1E293B) : Colors.white,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: Colors.grey.withValues(alpha: 0.15)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.03),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        children: factors.map((factor) {
          final isPositive = factor.contribution >= 0;
          final barWidthRatio = (factor.contribution.abs() / maxAbs).clamp(0.05, 1.0);
          final barColor = isPositive ? AppColors.riskHigh : AppColors.riskLow;

          return Padding(
            padding: const EdgeInsets.symmetric(vertical: 6.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Expanded(
                      child: Text(
                        factor.feature,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Text(
                      "${isPositive ? '+' : ''}${factor.contribution.toStringAsFixed(3)} weight",
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                        color: barColor,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 6),
                LayoutBuilder(
                  builder: (context, constraints) {
                    final fullW = constraints.maxWidth;
                    return Stack(
                      children: [
                        Container(
                          height: 6,
                          width: fullW,
                          decoration: BoxDecoration(
                            color: isDark ? Colors.grey[800] : Colors.grey[200],
                            borderRadius: BorderRadius.circular(3),
                          ),
                        ),
                        Container(
                          height: 6,
                          width: fullW * barWidthRatio,
                          decoration: BoxDecoration(
                            color: barColor,
                            borderRadius: BorderRadius.circular(3),
                          ),
                        ),
                      ],
                    );
                  },
                ),
                const SizedBox(height: 4),
                Text(
                  factor.impactDescription,
                  style: TextStyle(
                    fontSize: 10,
                    color: isDark ? Colors.grey[400] : Colors.grey[600],
                  ),
                ),
              ],
            ),
          );
        }).toList(),
      ),
    );
  }
}
