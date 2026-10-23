import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Network Configuration for Smart Goggle Backend Connectivity
/// Supports Physical Android Devices over WiFi/Hotspot, Emulator, Desktop, and Web.
class AppConfig {
  static const String keyCustomApiUrl = "custom_api_base_url";

  // Standard environment network endpoints:
  // 1. Physical Android Device on Laptop Wi-Fi:
  static const String defaultWifiUrl = "http://10.146.195.65:8000";

  // 2. Physical Android Device on Laptop Hotspot:
  static const String hotspotUrl = "http://192.168.137.1:8000";

  // 3. Android Emulator (maps host localhost to 10.0.2.2):
  static const String emulatorBaseUrl = "http://10.0.2.2:8000";

  // 4. Desktop / iOS Simulator / Web: localhost / 127.0.0.1:
  static const String localBaseUrl = "http://127.0.0.1:8000";

  static const List<Map<String, String>> presets = [
    {"label": "Wi-Fi (Laptop)", "url": defaultWifiUrl},
    {"label": "Hotspot", "url": hotspotUrl},
    {"label": "Android Emulator", "url": emulatorBaseUrl},
    {"label": "Localhost (PC)", "url": localBaseUrl},
  ];

  static String _activeBaseUrl = _getDefaultUrl();

  static String get apiBaseUrl => _activeBaseUrl;

  static String _getDefaultUrl() {
    if (kIsWeb) return localBaseUrl;
    if (Platform.isAndroid) {
      // Default to laptop Wi-Fi IP for real device testing
      return defaultWifiUrl;
    }
    return localBaseUrl;
  }

  /// Initialize and restore user-saved custom endpoint if any
  static Future<void> init() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final savedUrl = prefs.getString(keyCustomApiUrl);
      if (savedUrl != null && savedUrl.trim().isNotEmpty) {
        _activeBaseUrl = savedUrl.trim();
      }
    } catch (_) {}
  }

  /// Set and persist custom backend address
  static Future<void> setCustomBaseUrl(String url) async {
    _activeBaseUrl = url.trim();
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(keyCustomApiUrl, _activeBaseUrl);
    } catch (_) {}
  }
}
