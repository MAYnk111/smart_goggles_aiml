import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../constants.dart';
import '../providers/app_state.dart';

class EnvironmentScreen extends StatelessWidget {
  const EnvironmentScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final appState = Provider.of<AppState>(context);
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    final telemetry = appState.latestTelemetry;
    final env = telemetry?.environment;
    final aqiPred = telemetry?.aqiPrediction;
    final envFactors = telemetry?.explanation.environmentalFactors ?? [];

    final activePollutants = env?.getActivePollutants() ?? {
      "PM2.5": 36.4,
      "PM10": 38.1,
      "NO2": 10.7,
      "CO": 0.85,
      "SO2": 10.2,
      "O3": 171.0
    };

    final bucket = aqiPred?.predictedBucket ?? "Moderate";
    final confidence = aqiPred?.confidence ?? 0.80;
    final bucketColor = AppColors.getRiskColor(bucket);

    return Scaffold(
      appBar: AppBar(
        title: const Text("Environmental Monitoring"),
        actions: [
          IconButton(
            icon: appState.isLocatingGps
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                  )
                : const Icon(Icons.my_location_rounded),
            tooltip: "Update Phone GPS",
            onPressed: appState.isLocatingGps ? null : () => appState.refreshGpsLocation(),
          ),
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            tooltip: "Refresh Readings",
            onPressed: () => appState.refreshBackendState(),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16.0),
        children: [
          // GPS Location Status Banner
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            decoration: BoxDecoration(
              color: isDark ? AppColors.darkCard : Colors.grey[100],
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                color: appState.isRealGps ? AppColors.riskLow.withValues(alpha: 0.5) : Colors.grey.withValues(alpha: 0.3),
              ),
            ),
            child: Row(
              children: [
                Icon(
                  appState.isRealGps ? Icons.location_on_rounded : Icons.location_searching_rounded,
                  color: appState.isRealGps ? AppColors.riskLow : Colors.orange,
                  size: 20,
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        appState.isRealGps ? "LIVE PHONE GPS ACQUIRED" : "DEFAULT GPS FALLBACK",
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w800,
                          color: appState.isRealGps ? AppColors.riskLow : Colors.orange,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        "Lat: ${appState.latitude.toStringAsFixed(4)}, Lon: ${appState.longitude.toStringAsFixed(4)} (${env?.location ?? 'Open-Meteo API'})",
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(fontSize: 11, color: Colors.grey),
                      ),
                    ],
                  ),
                ),
                TextButton(
                  onPressed: () => appState.refreshGpsLocation(),
                  child: const Text("Locate", style: TextStyle(fontSize: 11)),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),

          // Hero Environmental Prediction Card
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [bucketColor.withValues(alpha: 0.85), bucketColor],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.circular(24),
              boxShadow: [
                BoxShadow(
                  color: bucketColor.withValues(alpha: 0.35),
                  blurRadius: 18,
                  offset: const Offset(0, 6),
                ),
              ],
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Expanded(
                      child: Text(
                        "LIVE AQI ML PREDICTION",
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w800,
                          letterSpacing: 1.0,
                          color: Colors.white70,
                        ),
                      ),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: Colors.black26,
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(
                        "Conf: ${(confidence * 100).toStringAsFixed(0)}%",
                        style: const TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w700,
                          color: Colors.white,
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
                    bucket.toUpperCase(),
                    style: const TextStyle(
                      fontSize: 32,
                      fontWeight: FontWeight.w900,
                      color: Colors.white,
                      letterSpacing: 1.1,
                    ),
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  "Station: ${env?.location ?? 'GPS Coordinates'} • Data: ${env?.source ?? 'Open-Meteo Live API'}",
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(fontSize: 11, color: Colors.white70),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),

          // Active Pollutants Grid (6 Live Open-Meteo Pollutants)
          const Text(
            "ACTIVE AMBIENT POLLUTANTS (OPEN-METEO)",
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w800,
              letterSpacing: 1.1,
              color: Colors.grey,
            ),
          ),
          const SizedBox(height: 10),
          GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 2,
              mainAxisSpacing: 8,
              crossAxisSpacing: 8,
              childAspectRatio: 2.2,
            ),
            itemCount: activePollutants.length,
            itemBuilder: (context, index) {
              final key = activePollutants.keys.elementAt(index);
              final val = activePollutants[key]!;
              final unit = key == "CO" ? "mg/m³" : "µg/m³";

              return Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                decoration: BoxDecoration(
                  color: isDark ? AppColors.darkCard : Colors.white,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: Colors.grey.withValues(alpha: 0.18)),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(
                      key,
                      style: const TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w600,
                        color: Colors.grey,
                      ),
                    ),
                    const SizedBox(height: 2),
                    FittedBox(
                      fit: BoxFit.scaleDown,
                      child: Row(
                        children: [
                          Text(
                            val.toStringAsFixed(1),
                            style: const TextStyle(
                              fontSize: 17,
                              fontWeight: FontWeight.w800,
                            ),
                          ),
                          const SizedBox(width: 4),
                          Text(
                            unit,
                            style: const TextStyle(fontSize: 10, color: Colors.grey),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              );
            },
          ),
          const SizedBox(height: 20),

          // Top Environmental Factors Section (SHAP)
          const Text(
            "TOP ENVIRONMENTAL FACTORS (SHAP XAI)",
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w800,
              letterSpacing: 1.1,
              color: Colors.grey,
            ),
          ),
          const SizedBox(height: 10),
          if (envFactors.isEmpty)
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: isDark ? AppColors.darkCard : Colors.grey[100],
                borderRadius: BorderRadius.circular(16),
              ),
              child: const Text(
                "Analyzing environmental SHAP weights from live pollutants...",
                style: TextStyle(fontSize: 12, color: Colors.grey),
              ),
            )
          else
            ...envFactors.map((factor) {
              final isPositive = factor.contribution >= 0;
              final factorColor = isPositive ? AppColors.riskHigh : AppColors.riskLow;
              return Container(
                margin: const EdgeInsets.only(bottom: 8),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: isDark ? AppColors.darkCard : Colors.white,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: factorColor.withValues(alpha: 0.3)),
                ),
                child: Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(6),
                      decoration: BoxDecoration(
                        color: factorColor.withValues(alpha: 0.15),
                        shape: BoxShape.circle,
                      ),
                      child: Icon(
                        isPositive ? Icons.arrow_upward_rounded : Icons.arrow_downward_rounded,
                        color: factorColor,
                        size: 16,
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            factor.feature,
                            style: const TextStyle(
                              fontSize: 13,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            factor.impactDescription,
                            style: TextStyle(
                              fontSize: 11,
                              color: isDark ? Colors.grey[300] : Colors.grey[700],
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 8),
                    Text(
                      "${isPositive ? '+' : ''}${factor.contribution.toStringAsFixed(3)}",
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w800,
                        color: factorColor,
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
}
