import 'package:flutter/material.dart';

/// Configurable BLE UUIDs and Service Constants
/// Matches ESP32 firmware (final_bpm_and_mpu.ino) exactly.
class AppConstants {
  // ESP32 BLE Device Name from firmware
  static const String bleDeviceName = "JATAYU_BAND";

  // Standard ESP32 BLE Service and Characteristic UUIDs from firmware
  static const String bleServiceUuid = "4fafc201-1fb5-459e-8fcc-c5c9c331914b";
  static const String bleCharacteristicUuid = "beb5483e-36e1-4688-b7f5-ea07361b26a8";

  // Backend FastAPI URL
  // Use 10.0.2.2 for Android Emulator, localhost/127.0.0.1 for Desktop/Web/iOS, or custom IP
  static const String defaultBackendUrl = "http://127.0.0.1:8000";
  static const String androidEmulatorBackendUrl = "http://10.0.2.2:8000";

  // College Prototype Disclaimer
  static const String prototypeDisclaimer =
      "COLLEGE PROTOTYPE / RESEARCH DEMONSTRATION ONLY. "
      "Not a medical diagnostic device. Risk indices are experimental indicators.";
}

class AppColors {
  static const Color primary = Color(0xFF0F766E); // Deep Teal
  static const Color primaryLight = Color(0xFF14B8A6);
  static const Color secondary = Color(0xFF0284C7); // Cyan / Blue
  static const Color accent = Color(0xFFF59E0B); // Amber

  // Risk Palette
  static const Color riskLow = Color(0xFF10B981); // Green
  static const Color riskMild = Color(0xFF84CC16); // Lime
  static const Color riskModerate = Color(0xFFF59E0B); // Amber
  static const Color riskHigh = Color(0xFFF97316); // Orange
  static const Color riskVeryHigh = Color(0xFFEF4444); // Red

  // Dark Theme Neutral
  static const Color darkBackground = Color(0xFF0F172A);
  static const Color darkSurface = Color(0xFF1E293B);
  static const Color darkCard = Color(0xFF334155);

  static Color getRiskColor(String level) {
    switch (level.toLowerCase()) {
      case 'low':
        return riskLow;
      case 'mild':
        return riskMild;
      case 'moderate':
        return riskModerate;
      case 'high':
        return riskHigh;
      case 'very high':
      case 'severe':
        return riskVeryHigh;
      default:
        return primary;
    }
  }
}
