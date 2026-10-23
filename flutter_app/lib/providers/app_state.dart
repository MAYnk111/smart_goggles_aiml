import 'dart:async';
import 'package:flutter/material.dart';
import '../models/sensor_data.dart';
import '../models/telemetry_model.dart';
import '../services/ble_service.dart';
import '../services/api_service.dart';
import '../services/gps_service.dart';

class AppState extends ChangeNotifier {
  SensorData _currentVitals = SensorData(
    heartRate: 0.0,
    spo2: null,
    temperature: null,
    fall: false,
    finger: false,
    emergency: false,
    source: "WAITING",
  );
  TelemetryResponse? _latestTelemetry;
  List<Map<String, dynamic>> _history = [];
  bool _isBackendConnected = false;
  String _lastUpdatedTime = "--:--:--";
  String _lastRawBleJson = "Waiting for ESP32 BLE stream (JATAYU_BAND)...";
  bool _isDarkMode = true;
  bool _isLocatingGps = false;

  Map<String, dynamic>? _mlResults;
  Map<String, dynamic>? _mlLiveDiagnostics;
  bool _isLoadingMlResults = false;

  StreamSubscription<SensorData>? _bleDataSub;
  StreamSubscription<BleConnectionState>? _bleStateSub;
  StreamSubscription<String>? _bleRawSub;

  AppState() {
    _initListeners();
    _initGpsAndBackend();
  }

  SensorData get currentVitals => _currentVitals;
  TelemetryResponse? get latestTelemetry => _latestTelemetry;
  List<Map<String, dynamic>> get history => _history;
  bool get isBackendConnected => _isBackendConnected;
  String get lastUpdatedTime => _lastUpdatedTime;
  String get lastRawBleJson => _lastRawBleJson;
  bool get isDarkMode => _isDarkMode;
  bool get isLocatingGps => _isLocatingGps;

  Map<String, dynamic>? get mlResults => _mlResults;
  Map<String, dynamic>? get mlLiveDiagnostics => _mlLiveDiagnostics;
  bool get isLoadingMlResults => _isLoadingMlResults;

  String get physiologicalMlStatus =>
      _mlLiveDiagnostics?['status']?['physiological_ml'] ?? (_isBackendConnected ? "WAITING" : "OFFLINE");
  String get environmentalMlStatus =>
      _mlLiveDiagnostics?['status']?['environmental_ml'] ?? (_isBackendConnected ? "WAITING" : "OFFLINE");
  String get lastMlPredictionTime =>
      _mlLiveDiagnostics?['status']?['last_prediction'] ?? "--:--:--";

  // Backend Diagnostics Getters
  String get backendUrl => apiService.baseUrl;
  String get backendHealthStatus => apiService.healthStatus;
  String get backendTestedUrl => apiService.lastTestedUrl;
  String? get backendLastError => apiService.lastError;
  DateTime? get lastBackendUploadTime => apiService.lastUploadTime;

  // GPS Getters
  double get latitude => gpsService.latitude;
  double get longitude => gpsService.longitude;
  bool get isRealGps => gpsService.isRealGps;
  String get gpsStatusMessage => gpsService.statusMessage;

  void toggleTheme() {
    _isDarkMode = !_isDarkMode;
    notifyListeners();
  }

  void _initListeners() {
    // 1. Listen for parsed SensorData from BLE
    _bleDataSub = bleService.sensorDataStream.listen((data) {
      _currentVitals = data;
      _lastUpdatedTime = DateTime.now().toIso8601String().substring(11, 19);
      notifyListeners();

      // Forward to FastAPI Backend with GPS coordinates
      _forwardSensorToBackend(data);
    });

    // 2. Listen for BLE connection state
    _bleStateSub = bleService.statusStream.listen((state) {
      notifyListeners();
    });

    // 3. Listen for raw BLE JSON string
    _bleRawSub = bleService.rawJsonStream.listen((raw) {
      _lastRawBleJson = raw;
      notifyListeners();
    });
  }

  Future<void> _initGpsAndBackend() async {
    await refreshGpsLocation();
    await refreshBackendState();
    await loadMlResults();
  }

  /// Request phone GPS coordinates
  Future<void> refreshGpsLocation() async {
    _isLocatingGps = true;
    notifyListeners();
    try {
      await gpsService.getCurrentLocation();
    } catch (_) {}
    _isLocatingGps = false;
    notifyListeners();
  }

  Future<void> _forwardSensorToBackend(SensorData data) async {
    // Enrich with current GPS coordinates
    final enrichedData = data.copyWith(
      latitude: gpsService.latitude,
      longitude: gpsService.longitude,
    );

    final response = await apiService.sendSensorData(enrichedData);
    if (response != null) {
      _latestTelemetry = response;
      _isBackendConnected = true;
      _appendToLocalHistory(response);
      notifyListeners();
    } else {
      _isBackendConnected = false;
      notifyListeners();
    }
  }

  void _appendToLocalHistory(TelemetryResponse resp) {
    _history.insert(0, {
      "timestamp": resp.timestamp,
      "heart_rate": resp.sensorData.heartRate,
      "spo2": resp.sensorData.spo2,
      "temperature": resp.sensorData.temperature,
      "aqi_bucket": resp.aqiPrediction.predictedBucket,
      "stress_class": resp.physiologicalPrediction.predictedStress,
      "risk_score": resp.personalizedRisk.riskScore,
      "risk_level": resp.personalizedRisk.riskLevel,
      "fall": resp.sensorData.fall,
      "finger": resp.sensorData.finger,
      "emergency": resp.sensorData.emergency,
    });
    if (_history.length > 50) {
      _history.removeLast();
    }
  }

  /// Initial or manual refresh from backend
  Future<void> refreshBackendState() async {
    _isBackendConnected = await apiService.checkHealth();
    if (_isBackendConnected) {
      final latest = await apiService.getLatest();
      if (latest != null) {
        _latestTelemetry = latest;
        _currentVitals = latest.sensorData;
        _lastUpdatedTime = latest.timestamp;
      }
      final hist = await apiService.getHistory(limit: 30);
      if (hist.isNotEmpty) {
        _history = hist;
      }
      await refreshMlLive();
    }
    notifyListeners();
  }

  /// Change and test custom backend URL with instant feedback
  Future<bool> updateBackendUrl(String newUrl) async {
    final success = await apiService.checkHealth(newUrl);
    _isBackendConnected = success;
    if (success) {
      await refreshBackendState();
    } else {
      notifyListeners();
    }
    return success;
  }

  /// Load authentic ML training & evaluation results
  Future<void> loadMlResults() async {
    _isLoadingMlResults = true;
    notifyListeners();
    try {
      _mlResults = await apiService.fetchMlResults();
      _mlLiveDiagnostics = await apiService.fetchMlLive();
    } catch (_) {}
    _isLoadingMlResults = false;
    notifyListeners();
  }

  /// Refresh live ML execution status and latest predictions
  Future<void> refreshMlLive() async {
    try {
      final live = await apiService.fetchMlLive();
      if (live != null) {
        _mlLiveDiagnostics = live;
        notifyListeners();
      }
    } catch (_) {}
  }

  @override
  void dispose() {
    _bleDataSub?.cancel();
    _bleStateSub?.cancel();
    _bleRawSub?.cancel();
    super.dispose();
  }
}
