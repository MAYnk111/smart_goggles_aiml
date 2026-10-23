import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:fl_chart/fl_chart.dart';
import '../constants.dart';
import '../providers/app_state.dart';

class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  int _selectedChartIndex = 0; // 0: Risk, 1: HR, 2: Temp, 3: AQI

  @override
  Widget build(BuildContext context) {
    final appState = Provider.of<AppState>(context);
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    final history = appState.history;

    return Scaffold(
      appBar: AppBar(
        title: const Text("Historical Telemetry"),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            tooltip: "Refresh History",
            onPressed: () => appState.refreshBackendState(),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16.0),
        children: [
          // Chart Selector Chips
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Row(
              children: [
                _buildFilterChip("Risk Score", 0, Icons.shield_outlined, AppColors.riskHigh),
                const SizedBox(width: 8),
                _buildFilterChip("Heart Rate", 1, Icons.favorite_rounded, Colors.redAccent),
                const SizedBox(width: 8),
                _buildFilterChip("Skin Temp", 2, Icons.thermostat_rounded, Colors.amber),
                const SizedBox(width: 8),
                _buildFilterChip("Air Quality", 3, Icons.air_rounded, AppColors.secondary),
              ],
            ),
          ),
          const SizedBox(height: 14),

          // Main Interactive fl_chart Card
          Container(
            height: 250,
            padding: const EdgeInsets.fromLTRB(14, 18, 18, 14),
            decoration: BoxDecoration(
              color: isDark ? const Color(0xFF1E293B) : Colors.white,
              borderRadius: BorderRadius.circular(22),
              border: Border.all(color: Colors.grey.withValues(alpha: 0.15)),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.04),
                  blurRadius: 10,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: history.isEmpty
                ? const Center(
                    child: Text(
                      "No historical samples recorded yet.\nConnect BLE or Start Simulator to collect data.",
                      textAlign: TextAlign.center,
                      style: TextStyle(color: Colors.grey, fontSize: 12),
                    ),
                  )
                : _buildLineChart(history, isDark),
          ),
          const SizedBox(height: 20),

          // Table / List of Readings
          const Text(
            "RECORDED SAMPLES",
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w800,
              letterSpacing: 1.1,
              color: Colors.grey,
            ),
          ),
          const SizedBox(height: 10),
          if (history.isEmpty)
            const Text("No data in buffer.", style: TextStyle(color: Colors.grey, fontSize: 12))
          else
            ...history.map((item) {
              final hr = (item['heart_rate'] as num?)?.toDouble() ?? 0.0;
              final temp = (item['temperature'] as num?)?.toDouble();
              final risk = (item['risk_score'] as num?)?.toDouble() ?? 0.0;
              final level = item['risk_level'] ?? "Low";
              final aqi = item['aqi_bucket'] ?? "Moderate";
              final time = item['timestamp'] ?? "";

              return Container(
                margin: const EdgeInsets.only(bottom: 8),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: isDark ? AppColors.darkCard : Colors.white,
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: Colors.grey.withValues(alpha: 0.15)),
                ),
                child: Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            time,
                            style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: Colors.grey),
                          ),
                          const SizedBox(height: 4),
                          FittedBox(
                            fit: BoxFit.scaleDown,
                            alignment: Alignment.centerLeft,
                            child: Row(
                              children: [
                                Text(
                                  "${hr.toStringAsFixed(0)} BPM",
                                  style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: Colors.redAccent),
                                ),
                                const SizedBox(width: 8),
                                Text(
                                  temp != null ? "${temp.toStringAsFixed(1)}°C" : "--",
                                  style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: Colors.amber),
                                ),
                                const SizedBox(width: 8),
                                Text(
                                  "AQI: $aqi",
                                  style: const TextStyle(fontSize: 11, color: Colors.grey),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: AppColors.getRiskColor(level).withValues(alpha: 0.15),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        "Risk: ${risk.toStringAsFixed(0)}",
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w800,
                          color: AppColors.getRiskColor(level),
                        ),
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

  Widget _buildFilterChip(String label, int index, IconData icon, Color color) {
    final isSelected = _selectedChartIndex == index;
    return ChoiceChip(
      avatar: Icon(icon, size: 14, color: isSelected ? Colors.white : color),
      label: Text(label),
      selected: isSelected,
      onSelected: (_) => setState(() => _selectedChartIndex = index),
      selectedColor: color,
      labelStyle: TextStyle(
        color: isSelected ? Colors.white : null,
        fontWeight: isSelected ? FontWeight.w700 : FontWeight.w500,
        fontSize: 11,
      ),
    );
  }

  Widget _buildLineChart(List<Map<String, dynamic>> data, bool isDark) {
    final displayData = data.reversed.toList();
    List<FlSpot> spots = [];

    Color chartColor = AppColors.riskHigh;
    double minY = 0.0;
    double maxY = 100.0;

    for (int i = 0; i < displayData.length; i++) {
      final item = displayData[i];
      double val = 0.0;
      if (_selectedChartIndex == 0) {
        // Risk
        val = (item['risk_score'] as num?)?.toDouble() ?? 25.0;
        chartColor = AppColors.riskHigh;
        minY = 0;
        maxY = 100;
      } else if (_selectedChartIndex == 1) {
        // HR
        val = (item['heart_rate'] as num?)?.toDouble() ?? 75.0;
        chartColor = Colors.redAccent;
        minY = 40;
        maxY = 140;
      } else if (_selectedChartIndex == 2) {
        // Temp
        val = (item['temperature'] as num?)?.toDouble() ?? 36.5;
        chartColor = Colors.amber;
        minY = 32;
        maxY = 42;
      } else {
        // AQI indicator
        final b = item['aqi_bucket']?.toString().toLowerCase() ?? "moderate";
        if (b.contains("good")) {
          val = 20;
        } else if (b.contains("satisfactory")) {
          val = 40;
        } else if (b.contains("moderate")) {
          val = 60;
        } else if (b.contains("poor")) {
          val = 80;
        } else {
          val = 100;
        }
        chartColor = AppColors.secondary;
        minY = 0;
        maxY = 100;
      }
      spots.add(FlSpot(i.toDouble(), val));
    }

    return LineChart(
      LineChartData(
        minX: 0,
        maxX: (displayData.length - 1).toDouble().clamp(1.0, 50.0),
        minY: minY,
        maxY: maxY,
        gridData: FlGridData(
          show: true,
          drawVerticalLine: false,
          getDrawingHorizontalLine: (value) => FlLine(
            color: Colors.grey.withValues(alpha: 0.15),
            strokeWidth: 1,
          ),
        ),
        titlesData: FlTitlesData(
          topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          leftTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              reservedSize: 34,
              getTitlesWidget: (val, meta) => Text(
                val.toInt().toString(),
                style: const TextStyle(fontSize: 10, color: Colors.grey),
              ),
            ),
          ),
          bottomTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
        ),
        borderData: FlBorderData(show: false),
        lineBarsData: [
          LineChartBarData(
            spots: spots,
            isCurved: true,
            color: chartColor,
            barWidth: 2.5,
            isStrokeCapRound: true,
            dotData: const FlDotData(show: false),
            belowBarData: BarAreaData(
              show: true,
              color: chartColor.withValues(alpha: 0.15),
            ),
          ),
        ],
      ),
    );
  }
}
