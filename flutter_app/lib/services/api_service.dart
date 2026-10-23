import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import '../models/sensor_data.dart';
import '../models/telemetry_model.dart';
import '../config/app_config.dart';

class ApiService {
  String _baseUrl = AppConfig.apiBaseUrl;

  String _healthStatus = "DISCONNECTED";
  String get healthStatus => _healthStatus;

  String _lastTestedUrl = "";
  String get lastTestedUrl => _lastTestedUrl.isNotEmpty ? _lastTestedUrl : "$_baseUrl/api/health";

  String? _lastError;
  String? get lastError => _lastError;

  DateTime? _lastUploadTime;
  DateTime? get lastUploadTime => _lastUploadTime;

  ApiService() {
    _baseUrl = AppConfig.apiBaseUrl;
    _lastTestedUrl = "$_baseUrl/api/health";
  }

  void setCustomUrl(String url) {
    _baseUrl = url.trim();
    _lastTestedUrl = "$_baseUrl/api/health";
    AppConfig.setCustomBaseUrl(_baseUrl);
  }

  String get baseUrl => _baseUrl;

  /// Check backend health against specified or active URL
  Future<bool> checkHealth([String? urlToTest]) async {
    final base = (urlToTest != null && urlToTest.trim().isNotEmpty) ? urlToTest.trim() : _baseUrl;
    _lastTestedUrl = "$base/api/health";
    try {
      final uri = Uri.parse(_lastTestedUrl);
      final response = await http.get(uri).timeout(const Duration(seconds: 3));
      if (response.statusCode == 200) {
        _healthStatus = "CONNECTED";
        _lastError = null;
        if (urlToTest != null && urlToTest.trim().isNotEmpty) {
          _baseUrl = urlToTest.trim();
          AppConfig.setCustomBaseUrl(_baseUrl);
        }
        return true;
      } else {
        _healthStatus = "DISCONNECTED";
        _lastError = "HTTP ${response.statusCode}: ${response.reasonPhrase ?? 'Service Error'}";
        return false;
      }
    } catch (e) {
      _healthStatus = "DISCONNECTED";
      _lastError = "FastAPI unreachable at $_lastTestedUrl ($e)";
      return false;
    }
  }

  /// Post physiological sensor readings received from ESP32 BLE
  Future<TelemetryResponse?> sendSensorData(SensorData data) async {
    final uri = Uri.parse("$_baseUrl/api/sensor");
    try {
      final response = await http
          .post(
            uri,
            headers: {"Content-Type": "application/json"},
            body: jsonEncode(data.toJson()),
          )
          .timeout(const Duration(seconds: 4));

      if (response.statusCode == 200) {
        _lastUploadTime = DateTime.now();
        _healthStatus = "CONNECTED";
        _lastError = null;
        final decoded = jsonDecode(response.body);
        return TelemetryResponse.fromJson(decoded);
      } else {
        _lastError = "API Error ${response.statusCode}: ${response.body}";
        debugPrint("API Error ${response.statusCode}: ${response.body}");
      }
    } catch (e) {
      _healthStatus = "DISCONNECTED";
      _lastError = "FastAPI unreachable at $uri ($e)";
      debugPrint("API Network exception sending sensor data to $uri: $e");
    }
    return null;
  }

  /// Fetch live environmental pollutants for dynamic GPS coordinates
  Future<EnvironmentModel?> fetchEnvironment({double? latitude, double? longitude}) async {
    String url = "$_baseUrl/api/environment";
    if (latitude != null && longitude != null) {
      url += "?lat=$latitude&lon=$longitude";
    }
    final uri = Uri.parse(url);
    try {
      final response = await http.get(uri).timeout(const Duration(seconds: 5));
      if (response.statusCode == 200) {
        final decoded = jsonDecode(response.body);
        return EnvironmentModel.fromJson(decoded);
      }
    } catch (e) {
      debugPrint("API exception fetching environment: $e");
    }
    return null;
  }

  /// Get verified ML evaluation results
  Future<Map<String, dynamic>?> fetchMlResults() async {
    final uri = Uri.parse("$_baseUrl/api/ml/results");
    try {
      final response = await http.get(uri).timeout(const Duration(seconds: 4));
      if (response.statusCode == 200) {
        return jsonDecode(response.body) as Map<String, dynamic>;
      }
    } catch (e) {
      debugPrint("API exception fetching ML results: $e");
    }
    return null;
  }

  /// Get live ML diagnostics and latest real-time inferences
  Future<Map<String, dynamic>?> fetchMlLive() async {
    final uri = Uri.parse("$_baseUrl/api/ml/live");
    try {
      final response = await http.get(uri).timeout(const Duration(seconds: 4));
      if (response.statusCode == 200) {
        return jsonDecode(response.body) as Map<String, dynamic>;
      }
    } catch (e) {
      debugPrint("API exception fetching live ML diagnostics: $e");
    }
    return null;
  }

  /// Get latest telemetry snapshot
  Future<TelemetryResponse?> getLatest() async {
    final uri = Uri.parse("$_baseUrl/api/latest");
    try {
      final response = await http.get(uri).timeout(const Duration(seconds: 4));
      if (response.statusCode == 200) {
        return TelemetryResponse.fromJson(jsonDecode(response.body));
      }
    } catch (e) {
      debugPrint("API Network exception fetching latest: $e");
    }
    return null;
  }

  /// Fetch history records for charts
  Future<List<Map<String, dynamic>>> getHistory({int limit = 30}) async {
    final uri = Uri.parse("$_baseUrl/api/history?limit=$limit");
    try {
      final response = await http.get(uri).timeout(const Duration(seconds: 4));
      if (response.statusCode == 200) {
        final List list = jsonDecode(response.body);
        return list.cast<Map<String, dynamic>>();
      }
    } catch (e) {
      debugPrint("API Network exception fetching history: $e");
    }
    return [];
  }
}

final apiService = ApiService();
