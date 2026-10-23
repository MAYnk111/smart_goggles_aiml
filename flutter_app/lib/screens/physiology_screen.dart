import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../constants.dart';
import '../providers/app_state.dart';
import '../widgets/vital_card.dart';

class PhysiologyScreen extends StatelessWidget {
  const PhysiologyScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final appState = Provider.of<AppState>(context);
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    final vitals = appState.currentVitals;
    final telemetry = appState.latestTelemetry;
    final physPred = telemetry?.physiologicalPrediction;
    final stressClass = physPred?.predictedStress ?? "Low";
    final confidence = physPred?.confidence ?? 0.85;
    final probs = physPred?.probabilities ?? {"Low": 0.70, "Medium": 0.20, "High": 0.10};
    final stressColor = AppColors.getRiskColor(stressClass);

    final history = appState.history;

    return Scaffold(
      appBar: AppBar(
        title: const Text("Physiological Telemetry"),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16.0),
        children: [
          // Sensor Hardware Status Row
          Row(
            children: [
              Expanded(
                child: _buildHardwareStatusChip(
                  icon: vitals.finger ? Icons.touch_app_rounded : Icons.fingerprint_rounded,
                  label: vitals.finger ? "Finger Detected" : "No Finger",
                  color: vitals.finger ? AppColors.riskLow : Colors.orange,
                  isDark: isDark,
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _buildHardwareStatusChip(
                  icon: vitals.fall ? Icons.warning_rounded : Icons.accessibility_new_rounded,
                  label: vitals.fall ? "FALL DETECTED" : "Posture Normal",
                  color: vitals.fall ? Colors.red : AppColors.riskLow,
                  isDark: isDark,
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _buildHardwareStatusChip(
                  icon: vitals.emergency ? Icons.emergency_rounded : Icons.verified_user_rounded,
                  label: vitals.emergency ? "EMERGENCY" : "Safe State",
                  color: vitals.emergency ? Colors.red : AppColors.riskLow,
                  isDark: isDark,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),

          // 3 Live Vitals Cards with LayoutBuilder
          LayoutBuilder(
            builder: (context, constraints) {
              return Row(
                children: [
                  Expanded(
                    child: VitalCard(
                      title: "Heart Rate",
                      value: vitals.displayHeartRate,
                      unit: vitals.finger ? "BPM" : "",
                      icon: Icons.favorite_rounded,
                      color: const Color(0xFFEF4444),
                      subtitle: vitals.finger
                          ? (vitals.heartRate > 100 ? "Tachycardia" : "Optimal")
                          : "Place Finger",
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: VitalCard(
                      title: "SpO2",
                      value: vitals.displaySpo2,
                      unit: vitals.spo2 != null ? "%" : "",
                      icon: Icons.water_drop_rounded,
                      color: const Color(0xFF0284C7),
                      subtitle: vitals.spo2 != null ? "Healthy" : "Firmware N/A",
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: VitalCard(
                      title: "Skin Temp",
                      value: vitals.displayTemperature,
                      unit: vitals.temperature != null ? "°C" : "",
                      icon: Icons.thermostat_rounded,
                      color: const Color(0xFFF59E0B),
                      subtitle: vitals.temperature != null
                          ? (vitals.temperature! > 37.5 ? "Warm" : "Normal")
                          : "--",
                    ),
                  ),
                ],
              );
            },
          ),
          const SizedBox(height: 20),

          // Stress Prediction Hero Card (Zero overflow guaranteed)
          Container(
            padding: const EdgeInsets.all(18),
            decoration: BoxDecoration(
              color: isDark ? const Color(0xFF1E293B) : Colors.white,
              borderRadius: BorderRadius.circular(22),
              border: Border.all(color: stressColor.withValues(alpha: 0.35), width: 1.5),
              boxShadow: [
                BoxShadow(
                  color: stressColor.withValues(alpha: 0.1),
                  blurRadius: 14,
                  offset: const Offset(0, 5),
                ),
              ],
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Expanded(
                      child: Row(
                        children: [
                          Icon(Icons.psychology_rounded, color: stressColor, size: 24),
                          const SizedBox(width: 8),
                          const Expanded(
                            child: Text(
                              "STRESS PREDICTION",
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.w800,
                                letterSpacing: 0.8,
                                color: Colors.grey,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: stressColor.withValues(alpha: 0.15),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Text(
                        "${(confidence * 100).toStringAsFixed(0)}% Conf",
                        style: TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.w700,
                          color: stressColor,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 14),
                FittedBox(
                  fit: BoxFit.scaleDown,
                  alignment: Alignment.centerLeft,
                  child: Text(
                    "$stressClass Stress Level".toUpperCase(),
                    style: TextStyle(
                      fontSize: 26,
                      fontWeight: FontWeight.w900,
                      color: stressColor,
                    ),
                  ),
                ),
                const SizedBox(height: 14),
                const Text(
                  "Probability Distribution (GroupKFold Model):",
                  style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: Colors.grey),
                ),
                const SizedBox(height: 8),
                ...probs.entries.map((entry) {
                  final pVal = entry.value.clamp(0.0, 1.0);
                  final barColor = AppColors.getRiskColor(entry.key);
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 8.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(
                              "${entry.key} Stress",
                              style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600),
                            ),
                            Text(
                              "${(pVal * 100).toStringAsFixed(1)}%",
                              style: TextStyle(
                                fontSize: 11,
                                fontWeight: FontWeight.w700,
                                color: barColor,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 4),
                        ClipRRect(
                          borderRadius: BorderRadius.circular(6),
                          child: LinearProgressIndicator(
                            value: pVal,
                            minHeight: 6,
                            backgroundColor: isDark ? Colors.grey[800] : Colors.grey[200],
                            valueColor: AlwaysStoppedAnimation<Color>(barColor),
                          ),
                        ),
                      ],
                    ),
                  );
                }),
              ],
            ),
          ),
          const SizedBox(height: 20),

          // Historical Physiological Readings
          const Text(
            "HISTORICAL PHYSIOLOGICAL SAMPLES",
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w800,
              letterSpacing: 1.1,
              color: Colors.grey,
            ),
          ),
          const SizedBox(height: 10),
          if (history.isEmpty)
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: isDark ? AppColors.darkCard : Colors.grey[100],
                borderRadius: BorderRadius.circular(16),
              ),
              child: const Text(
                "No historical vitals recorded yet. Stream ESP32 data to populate.",
                style: TextStyle(fontSize: 12, color: Colors.grey),
              ),
            )
          else
            ...history.take(8).map((record) {
              final hr = (record['heart_rate'] as num?)?.toDouble() ?? 0.0;
              final spo2 = (record['spo2'] as num?)?.toDouble();
              final temp = (record['temperature'] as num?)?.toDouble();
              final time = record['timestamp'] ?? "";
              final stress = record['stress_class'] ?? "Low";

              return Container(
                margin: const EdgeInsets.only(bottom: 8),
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                decoration: BoxDecoration(
                  color: isDark ? AppColors.darkCard : Colors.white,
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: Colors.grey.withValues(alpha: 0.15)),
                ),
                child: Row(
                  children: [
                    Text(
                      time,
                      style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: Colors.grey),
                    ),
                    const Spacer(),
                    FittedBox(
                      fit: BoxFit.scaleDown,
                      child: Row(
                        children: [
                          Text(
                            "${hr.toStringAsFixed(0)} BPM",
                            style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: Colors.redAccent),
                          ),
                          const SizedBox(width: 8),
                          Text(
                            spo2 != null ? "${spo2.toStringAsFixed(0)}%" : "--",
                            style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: Colors.blueAccent),
                          ),
                          const SizedBox(width: 8),
                          Text(
                            temp != null ? "${temp.toStringAsFixed(1)}°C" : "--",
                            style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: Colors.amber),
                          ),
                          const SizedBox(width: 8),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                            decoration: BoxDecoration(
                              color: AppColors.getRiskColor(stress).withValues(alpha: 0.15),
                              borderRadius: BorderRadius.circular(6),
                            ),
                            child: Text(
                              stress,
                              style: TextStyle(
                                fontSize: 9,
                                fontWeight: FontWeight.w700,
                                color: AppColors.getRiskColor(stress),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              );
            }),
          const SizedBox(height: 20),
        ],
      ),
    );
  }

  Widget _buildHardwareStatusChip({
    required IconData icon,
    required String label,
    required Color color,
    required bool isDark,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Column(
        children: [
          Icon(icon, size: 16, color: color),
          const SizedBox(height: 4),
          FittedBox(
            fit: BoxFit.scaleDown,
            child: Text(
              label,
              style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: color),
            ),
          ),
        ],
      ),
    );
  }
}
