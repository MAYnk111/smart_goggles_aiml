import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../constants.dart';
import '../providers/app_state.dart';
import '../services/ble_service.dart';
import '../widgets/vital_card.dart';
import '../widgets/risk_gauge_card.dart';
import 'ml_results_screen.dart';

class DashboardScreen extends StatelessWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final appState = Provider.of<AppState>(context);
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    final vitals = appState.currentVitals;
    final telemetry = appState.latestTelemetry;

    final aqiBucket = telemetry?.aqiPrediction.predictedBucket ?? "Moderate";
    final aqiVal = telemetry?.environment.pm25 != null
        ? (telemetry!.environment.pm25! * 1.5).toStringAsFixed(0)
        : "72";

    final stressVal = telemetry?.physiologicalPrediction.predictedStress ?? "Low";
    final riskScore = telemetry?.personalizedRisk.riskScore ?? 32.0;
    final riskLevel = telemetry?.personalizedRisk.riskLevel ?? "Low";
    final envComp = telemetry?.personalizedRisk.environmentalComponent ?? 16.0;
    final physComp = telemetry?.personalizedRisk.physiologicalComponent ?? 16.0;
    final statusSumm = telemetry?.personalizedRisk.statusSummary ??
        "Normal baseline vitals and moderate environmental exposure.";

    // Source Label and Color
    String sourceBadge;
    Color sourceColor;
    if (vitals.source == "REAL ESP32") {
      sourceBadge = "SOURCE: REAL ESP32 (${vitals.packetsReceived} pkts)";
      sourceColor = AppColors.riskLow;
    } else if (bleService.isSimulating || vitals.source == "SIMULATOR") {
      sourceBadge = "SOURCE: SIMULATOR (${vitals.packetsReceived} pkts)";
      sourceColor = Colors.amber;
    } else {
      sourceBadge = "SOURCE: WAITING FOR ESP32";
      sourceColor = Colors.grey;
    }

    return Scaffold(
      appBar: AppBar(
        title: const Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              "SMART GOGGLE",
              style: TextStyle(fontWeight: FontWeight.w900, fontSize: 18, letterSpacing: 1.2),
            ),
            Text(
              "Personal Health & Environment System",
              style: TextStyle(fontSize: 11, color: Colors.grey),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.analytics_rounded),
            tooltip: "ML Metrics & XAI",
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const MlResultsScreen()),
              );
            },
          ),
          IconButton(
            icon: Icon(appState.isDarkMode ? Icons.light_mode : Icons.dark_mode),
            tooltip: "Toggle Theme",
            onPressed: () => appState.toggleTheme(),
          ),
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            tooltip: "Refresh Backend",
            onPressed: () => appState.refreshBackendState(),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () async {
          await appState.refreshGpsLocation();
          await appState.refreshBackendState();
        },
        child: ListView(
          padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 12.0),
          children: [
            // Alert Banners (Fall / Emergency)
            if (vitals.fall || vitals.emergency) ...[
              Container(
                margin: const EdgeInsets.only(bottom: 12),
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: Colors.red.withValues(alpha: 0.2),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: Colors.red, width: 2),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.warning_rounded, color: Colors.red, size: 28),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            vitals.emergency ? "EMERGENCY ALERT TRIGGERED" : "FALL DETECTED",
                            style: const TextStyle(
                              color: Colors.red,
                              fontWeight: FontWeight.w900,
                              fontSize: 14,
                            ),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            vitals.emergency
                                ? "Emergency switch pressed on Smart Goggle hardware."
                                : "MPU6050 accelerometer detected high-G sudden impact / fall event.",
                            style: const TextStyle(color: Colors.redAccent, fontSize: 11),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ],

            // Top Status Bar: Source Badge + Time + GPS
            Row(
              children: [
                Expanded(
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                    decoration: BoxDecoration(
                      color: sourceColor.withValues(alpha: 0.15),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: sourceColor.withValues(alpha: 0.4)),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Container(
                          width: 8,
                          height: 8,
                          decoration: BoxDecoration(shape: BoxShape.circle, color: sourceColor),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            sourceBadge,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.w800,
                              color: sourceColor,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                  decoration: BoxDecoration(
                    color: isDark ? AppColors.darkCard : Colors.grey[200],
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.access_time_rounded, size: 13, color: Colors.grey),
                      const SizedBox(width: 4),
                      Text(
                        appState.lastUpdatedTime,
                        style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: Colors.grey),
                      ),
                    ],
                  ),
                ),
              ],
            ),

            // Live ML Execution Status Bar (Section 54)
            const SizedBox(height: 8),
            InkWell(
              borderRadius: BorderRadius.circular(12),
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (_) => const MlResultsScreen()),
                );
              },
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                decoration: BoxDecoration(
                  color: isDark ? AppColors.darkCard : Colors.grey[100],
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.grey.withValues(alpha: 0.15)),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.bolt_rounded, size: 14, color: AppColors.primaryLight),
                    const SizedBox(width: 6),
                    Expanded(
                      child: Text(
                        "Physiological ML: ${appState.physiologicalMlStatus} • Env ML: ${appState.environmentalMlStatus}",
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w700),
                      ),
                    ),
                    const Icon(Icons.chevron_right_rounded, size: 14, color: Colors.grey),
                  ],
                ),
              ),
            ),

            if (bleService.isSimulating) ...[
              const SizedBox(height: 10),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                decoration: BoxDecoration(
                  color: Colors.amber.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.amber, width: 1.2),
                ),
                child: const Row(
                  children: [
                    Icon(Icons.science_rounded, color: Colors.amber, size: 16),
                    SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        "DEMO SIMULATION: Real ESP32 BLE packet will immediately override simulator.",
                        style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: Colors.amber),
                      ),
                    ),
                  ],
                ),
              ),
            ],

            const SizedBox(height: 14),

            // Personalized Risk Hero Card
            RiskGaugeCard(
              score: riskScore,
              level: riskLevel,
              envComponent: envComp,
              physComponent: physComp,
              summary: statusSumm,
            ),
            const SizedBox(height: 18),

            // Live Physiological Vitals Title & Finger Status
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  "PHYSIOLOGICAL VITALS (ESP32)",
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w800,
                    letterSpacing: 1.1,
                    color: Colors.grey,
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: vitals.finger
                        ? AppColors.riskLow.withValues(alpha: 0.15)
                        : Colors.orange.withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Row(
                    children: [
                      Icon(
                        vitals.finger ? Icons.touch_app_rounded : Icons.fingerprint_rounded,
                        size: 12,
                        color: vitals.finger ? AppColors.riskLow : Colors.orange,
                      ),
                      const SizedBox(width: 4),
                      Text(
                        vitals.finger ? "Finger Detected" : "Place Finger",
                        style: TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.w700,
                          color: vitals.finger ? AppColors.riskLow : Colors.orange,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),

            // 3 Physiological Vital Cards using LayoutBuilder to never overflow
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
                            ? (vitals.heartRate > 100 ? "Elevated" : "Normal")
                            : "Sensor ready",
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
                        subtitle: vitals.spo2 != null ? "Optimal" : "No FW Calc",
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: VitalCard(
                        title: "Temp",
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
            const SizedBox(height: 18),

            // Environment & Stress AI Predictions Row
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  "AI PREDICTIONS (SHAP / ML)",
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w800,
                    letterSpacing: 1.1,
                    color: Colors.grey,
                  ),
                ),
                TextButton(
                  onPressed: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(builder: (_) => const MlResultsScreen()),
                    );
                  },
                  child: const Text("View ML Proof", style: TextStyle(fontSize: 11)),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  child: VitalCard(
                    title: "Air Quality (AQI)",
                    value: aqiVal,
                    unit: "AQI",
                    icon: Icons.air_rounded,
                    color: AppColors.getRiskColor(aqiBucket),
                    subtitle: "Bucket: $aqiBucket",
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: VitalCard(
                    title: "Stress Classifier",
                    value: stressVal,
                    unit: "",
                    icon: Icons.psychology_rounded,
                    color: AppColors.getRiskColor(stressVal),
                    subtitle: "Random Forest ML",
                  ),
                ),
              ],
            ),
            const SizedBox(height: 20),

            // Prototype Disclaimer Notice
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: isDark ? AppColors.darkCard.withValues(alpha: 0.5) : Colors.grey[100],
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: Colors.grey.withValues(alpha: 0.2)),
              ),
              child: const Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(Icons.info_outline_rounded, size: 16, color: Colors.grey),
                  SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      AppConstants.prototypeDisclaimer,
                      style: TextStyle(fontSize: 11, color: Colors.grey, height: 1.3),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),
          ],
        ),
      ),
    );
  }
}
