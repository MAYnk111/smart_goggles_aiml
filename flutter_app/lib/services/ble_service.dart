import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:math';
import 'package:flutter/foundation.dart';
import 'package:flutter_blue_plus/flutter_blue_plus.dart';
export 'package:flutter_blue_plus/flutter_blue_plus.dart' show ScanResult;
import 'package:permission_handler/permission_handler.dart';
import '../constants.dart';
import '../models/sensor_data.dart';

enum BleConnectionState {
  disconnected,
  scanning,
  connecting,
  connectedNoData,
  connectedReceiving,
}

class BleService {
  final String targetDeviceName = AppConstants.bleDeviceName;
  final Guid serviceUuid = Guid(AppConstants.bleServiceUuid);
  final Guid characteristicUuid = Guid(AppConstants.bleCharacteristicUuid);

  BluetoothDevice? _connectedDevice;
  BluetoothCharacteristic? _notifyCharacteristic;
  BluetoothCharacteristic? get notifyCharacteristic => _notifyCharacteristic;
  StreamSubscription<List<int>>? _valueSubscription;
  StreamSubscription<BluetoothConnectionState>? _deviceStateSubscription;

  BleConnectionState _status = BleConnectionState.disconnected;
  BleConnectionState get status => _status;

  final _statusController = StreamController<BleConnectionState>.broadcast();
  Stream<BleConnectionState> get statusStream => _statusController.stream;

  final _sensorDataController = StreamController<SensorData>.broadcast();
  Stream<SensorData> get sensorDataStream => _sensorDataController.stream;

  final _rawJsonController = StreamController<String>.broadcast();
  Stream<String> get rawJsonStream => _rawJsonController.stream;

  final List<ScanResult> _scanResults = [];
  List<ScanResult> get scanResults => List.unmodifiable(_scanResults);

  // Packet Statistics
  int _packetCount = 0;
  int get packetCount => _packetCount;

  DateTime? _lastPacketTime;
  DateTime? get lastPacketTime => _lastPacketTime;

  String _lastRawJson = "";
  String get lastRawJson => _lastRawJson;

  String? _lastError;
  String? get lastError => _lastError;

  // Built-in ESP32 Hardware Simulator for testing/demo without physical hardware
  Timer? _simulationTimer;
  bool _isSimulating = false;
  bool get isSimulating => _isSimulating;

  BluetoothDevice? get connectedDevice => _connectedDevice;

  bool get isConnected =>
      _status == BleConnectionState.connectedNoData ||
      _status == BleConnectionState.connectedReceiving;

  String get gattNotificationStatus {
    if (_status == BleConnectionState.connectedReceiving) return "RECEIVING";
    if (_status == BleConnectionState.connectedNoData) return "WAITING";
    return "NOT SUBSCRIBED";
  }

  String get statusDisplayLabel {
    if (_isSimulating) return "Simulated Hardware Active";
    switch (_status) {
      case BleConnectionState.disconnected:
        return "DISCONNECTED";
      case BleConnectionState.scanning:
        return "SCANNING...";
      case BleConnectionState.connecting:
        return "CONNECTING...";
      case BleConnectionState.connectedNoData:
        return "Connected (Waiting for data...)";
      case BleConnectionState.connectedReceiving:
        return "Connected & Receiving";
    }
  }

  void _setStatus(BleConnectionState state) {
    _status = state;
    _statusController.add(state);
  }

  /// Request runtime permissions required for BLE on Android and iOS
  Future<bool> requestPermissions() async {
    if (kIsWeb) return true;

    if (Platform.isAndroid) {
      Map<Permission, PermissionStatus> statuses = await [
        Permission.bluetoothScan,
        Permission.bluetoothConnect,
        Permission.locationWhenInUse,
      ].request();

      bool granted = (statuses[Permission.bluetoothScan]?.isGranted ?? false) ||
          (statuses[Permission.locationWhenInUse]?.isGranted ?? false);
      return granted;
    } else if (Platform.isIOS) {
      PermissionStatus status = await Permission.bluetooth.request();
      return status.isGranted;
    }
    return true;
  }

  /// Check if Bluetooth is turned on
  Future<bool> isBluetoothAvailable() async {
    try {
      BluetoothAdapterState state = await FlutterBluePlus.adapterState.first;
      return state == BluetoothAdapterState.on;
    } catch (e) {
      debugPrint("BLE availability check: $e");
      return false;
    }
  }

  /// Start scanning for ESP32 devices
  Future<void> startScan({Duration timeout = const Duration(seconds: 10)}) async {
    await requestPermissions();
    _scanResults.clear();
    _lastError = null;
    _setStatus(BleConnectionState.scanning);

    try {
      FlutterBluePlus.scanResults.listen((results) {
        _scanResults.clear();
        _scanResults.addAll(results);
      });

      await FlutterBluePlus.startScan(timeout: timeout);
      await FlutterBluePlus.isScanning.where((scanning) => !scanning).first;
      if (_status == BleConnectionState.scanning) {
        _setStatus(BleConnectionState.disconnected);
      }
    } catch (e) {
      _lastError = "BLE scan error: $e";
      debugPrint(_lastError);
      _setStatus(BleConnectionState.disconnected);
    }
  }

  /// Stop scanning
  Future<void> stopScan() async {
    try {
      await FlutterBluePlus.stopScan();
      if (_status == BleConnectionState.scanning) {
        _setStatus(BleConnectionState.disconnected);
      }
    } catch (e) {
      debugPrint("Error stopping BLE scan: $e");
    }
  }

  /// Connect to ESP32 device
  Future<bool> connect(BluetoothDevice device) async {
    stopSimulation();
    await stopScan();
    _lastError = null;
    _packetCount = 0;
    _lastPacketTime = null;
    _lastRawJson = "";
    _setStatus(BleConnectionState.connecting);

    try {
      await device.connect(
        license: License.nonprofit,
        timeout: const Duration(seconds: 15),
      );
      _connectedDevice = device;

      // Listen for unexpected disconnection
      _deviceStateSubscription?.cancel();
      _deviceStateSubscription = device.connectionState.listen((state) {
        if (state == BluetoothConnectionState.disconnected) {
          debugPrint("BLE Device disconnected by peripheral or link loss.");
          disconnect();
        }
      });

      // Discover GATT services and subscribe to telemetry characteristic
      return await _discoverGattServices(device);
    } catch (e) {
      _lastError = "BLE connection error: $e";
      debugPrint(_lastError);
      disconnect();
      return false;
    }
  }

  /// Discover Services & Characteristics and subscribe to notifications
  Future<bool> _discoverGattServices(BluetoothDevice device) async {
    try {
      debugPrint("Discovering GATT services on ${device.platformName} (${device.remoteId})...");
      List<BluetoothService> services = await device.discoverServices();
      BluetoothCharacteristic? targetChar;

      final targetCharUuidStr = AppConstants.bleCharacteristicUuid.toLowerCase();
      final targetServiceUuidStr = AppConstants.bleServiceUuid.toLowerCase();

      for (var service in services) {
        final currentServiceUuid = service.uuid.toString().toLowerCase();
        debugPrint("Discovered Service: $currentServiceUuid");

        for (var char in service.characteristics) {
          final currentCharUuid = char.uuid.toString().toLowerCase();
          debugPrint(
            "  -> Characteristic: $currentCharUuid (notify: ${char.properties.notify}, read: ${char.properties.read}, write: ${char.properties.write})",
          );

          if (currentCharUuid == targetCharUuidStr) {
            targetChar = char;
            break;
          }
          if (currentServiceUuid == targetServiceUuidStr && char.properties.notify) {
            targetChar = char;
            break;
          }
        }
        if (targetChar != null) break;
      }

      if (targetChar == null) {
        _lastError = "BLE characteristic not found (${AppConstants.bleCharacteristicUuid})";
        debugPrint(_lastError);
        // Retain connection state for diagnostics, but note error
        _setStatus(BleConnectionState.connectedNoData);
        return false;
      }

      if (!targetChar.properties.notify && !targetChar.properties.indicate) {
        _lastError = "ERROR: Characteristic does not support notifications";
        debugPrint(_lastError);
        _setStatus(BleConnectionState.connectedNoData);
        return false;
      }

      _notifyCharacteristic = targetChar;
      return await _subscribeToCharacteristic(targetChar);
    } catch (e) {
      _lastError = "GATT discovery error: $e";
      debugPrint(_lastError);
      _setStatus(BleConnectionState.disconnected);
      return false;
    }
  }

  /// Subscribe to incoming BLE notifications containing ESP32 JSON payload
  Future<bool> _subscribeToCharacteristic(BluetoothCharacteristic characteristic) async {
    try {
      debugPrint("Subscribing to notifications on ${characteristic.uuid}...");
      await characteristic.setNotifyValue(true);
      _valueSubscription?.cancel();
      _valueSubscription = characteristic.onValueReceived.listen((data) {
        _handleIncomingPacket(data);
      });

      // Connected and subscribed, but waiting for first actual sensor packet
      _setStatus(BleConnectionState.connectedNoData);
      debugPrint("GATT subscribed successfully. Waiting for ESP32 BLE stream...");
      return true;
    } catch (e) {
      _lastError = "BLE notification subscription failed: $e";
      debugPrint(_lastError);
      _setStatus(BleConnectionState.connectedNoData);
      return false;
    }
  }

  /// Process raw incoming packet from ESP32 BLE
  void _handleIncomingPacket(List<int> data) {
    if (data.isEmpty) return;

    // REAL ESP32 DATA ARRIVED - strictly overrides and terminates any active simulator
    if (_isSimulating) {
      stopSimulation();
    }

    String rawString;
    try {
      rawString = utf8.decode(data);
    } catch (_) {
      rawString = String.fromCharCodes(data);
    }

    _packetCount++;
    _lastPacketTime = DateTime.now();
    _lastRawJson = rawString;
    _lastError = null;

    // State transitions to CONNECTED_RECEIVING only after receiving valid data
    if (_status != BleConnectionState.connectedReceiving) {
      _setStatus(BleConnectionState.connectedReceiving);
    }

    _rawJsonController.add(rawString);
    _parseAndEmitJson(rawString, isRealEsp32: true);
  }

  /// Parse the ESP32 JSON schema:
  /// {"bpm": 80.5, "temperature": 36.4, "fall": false, "finger": true, "emergency": false}
  void _parseAndEmitJson(String jsonString, {required bool isRealEsp32}) {
    try {
      final Map<String, dynamic> parsed = jsonDecode(jsonString.trim());
      final sensorData = SensorData.fromJson(
        parsed,
        defaultSource: isRealEsp32 ? "REAL ESP32" : "SIMULATOR",
      ).copyWith(
        source: isRealEsp32 ? "REAL ESP32" : "SIMULATOR",
        packetsReceived: _packetCount,
        lastPacketTime: _lastPacketTime ?? DateTime.now(),
        rawJson: jsonString,
      );
      _sensorDataController.add(sensorData);
    } catch (e) {
      _lastError = "JSON decode error: $e";
      debugPrint("JSON parsing error from BLE payload '$jsonString': $e");
    }
  }

  /// Disconnect device safely
  Future<void> disconnect() async {
    _valueSubscription?.cancel();
    _valueSubscription = null;
    _deviceStateSubscription?.cancel();
    _deviceStateSubscription = null;
    if (_connectedDevice != null) {
      try {
        await _connectedDevice!.disconnect();
      } catch (_) {}
      _connectedDevice = null;
    }
    _notifyCharacteristic = null;
    _setStatus(BleConnectionState.disconnected);
  }

  /// Hardware Simulation Mode:
  /// Realistic ESP32 sensor packets for testing/demo without physical hardware.
  /// Automatically disabled the moment any real ESP32 BLE packet is received.
  void startSimulation() {
    disconnect();
    _isSimulating = true;
    _packetCount = 0;
    _lastError = null;
    _setStatus(BleConnectionState.connectedReceiving);

    final random = Random();
    _simulationTimer?.cancel();
    _simulationTimer = Timer.periodic(const Duration(seconds: 2), (timer) {
      if (!_isSimulating) {
        timer.cancel();
        return;
      }

      _packetCount++;
      _lastPacketTime = DateTime.now();

      // Realistic random-walk physiological vitals
      double hr = 72.0 + random.nextInt(18) + (random.nextInt(10) / 10.0);
      double temp = 36.3 + (random.nextInt(8) / 10.0);
      bool fingerDetected = true;
      bool fallDetected = false;
      bool emergencyTriggered = false;

      // Schema strictly matches ESP32 firmware
      Map<String, dynamic> payload = {
        "bpm": double.parse(hr.toStringAsFixed(1)),
        "temperature": double.parse(temp.toStringAsFixed(1)),
        "fall": fallDetected,
        "finger": fingerDetected,
        "emergency": emergencyTriggered,
      };

      String jsonString = jsonEncode(payload);
      _lastRawJson = jsonString;
      _rawJsonController.add(jsonString);

      final sensorData = SensorData.fromJson(
        payload,
        defaultSource: "SIMULATOR",
      ).copyWith(
        source: "SIMULATOR",
        packetsReceived: _packetCount,
        lastPacketTime: _lastPacketTime,
        rawJson: jsonString,
      );
      _sensorDataController.add(sensorData);
    });
  }

  void stopSimulation() {
    _isSimulating = false;
    _simulationTimer?.cancel();
    _simulationTimer = null;
    if (_connectedDevice == null) {
      _setStatus(BleConnectionState.disconnected);
    }
  }

  void dispose() {
    _valueSubscription?.cancel();
    _deviceStateSubscription?.cancel();
    _simulationTimer?.cancel();
    _statusController.close();
    _sensorDataController.close();
    _rawJsonController.close();
  }
}

final bleService = BleService();
