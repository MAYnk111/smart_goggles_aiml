class SensorData {
  final double heartRate; // maps to bpm or heart_rate
  final double? spo2; // nullable: ESP32 firmware currently does not calculate SpO2
  final double? temperature; // nullable
  final bool fall;
  final bool finger;
  final bool emergency;
  final String source; // 'REAL ESP32', 'SIMULATOR', or 'WAITING'
  final int packetsReceived;
  final DateTime? lastPacketTime;
  final String rawJson;
  final double? latitude;
  final double? longitude;

  SensorData({
    required this.heartRate,
    this.spo2,
    this.temperature,
    this.fall = false,
    this.finger = false,
    this.emergency = false,
    this.source = "WAITING",
    this.packetsReceived = 0,
    this.lastPacketTime,
    this.rawJson = "",
    this.latitude,
    this.longitude,
  });

  /// Parse payload from ESP32 BLE notification or Backend API
  /// ESP32 JSON schema: {"bpm": 80.5, "temperature": 36.4, "fall": false, "finger": true, "emergency": false}
  factory SensorData.fromJson(Map<String, dynamic> json, {String? defaultSource}) {
    final hrVal = (json['bpm'] ?? json['heart_rate'] ?? json['heartRate'] as num?)?.toDouble() ?? 0.0;
    final spo2Val = (json['spo2'] as num?)?.toDouble();
    final tempVal = (json['temperature'] as num?)?.toDouble();
    final fallVal = json['fall'] == true || json['fall'] == 1;
    final fingerVal = json['finger'] == true || json['finger'] == 1;
    final emergencyVal = json['emergency'] == true || json['emergency'] == 1;
    final src = (json['source'] as String?) ?? defaultSource ?? "REAL ESP32";

    return SensorData(
      heartRate: hrVal,
      spo2: spo2Val,
      temperature: tempVal,
      fall: fallVal,
      finger: fingerVal,
      emergency: emergencyVal,
      source: src,
      latitude: (json['latitude'] as num?)?.toDouble(),
      longitude: (json['longitude'] as num?)?.toDouble(),
      rawJson: json.toString(),
    );
  }

  Map<String, dynamic> toJson() {
    final map = <String, dynamic>{
      "bpm": heartRate,
      "heart_rate": heartRate,
      "fall": fall,
      "finger": finger,
      "emergency": emergency,
      "source": source,
    };
    if (spo2 != null) map["spo2"] = spo2;
    if (temperature != null) map["temperature"] = temperature;
    if (latitude != null) map["latitude"] = latitude;
    if (longitude != null) map["longitude"] = longitude;
    return map;
  }

  SensorData copyWith({
    double? heartRate,
    double? spo2,
    double? temperature,
    bool? fall,
    bool? finger,
    bool? emergency,
    String? source,
    int? packetsReceived,
    DateTime? lastPacketTime,
    String? rawJson,
    double? latitude,
    double? longitude,
  }) {
    return SensorData(
      heartRate: heartRate ?? this.heartRate,
      spo2: spo2 ?? this.spo2,
      temperature: temperature ?? this.temperature,
      fall: fall ?? this.fall,
      finger: finger ?? this.finger,
      emergency: emergency ?? this.emergency,
      source: source ?? this.source,
      packetsReceived: packetsReceived ?? this.packetsReceived,
      lastPacketTime: lastPacketTime ?? this.lastPacketTime,
      rawJson: rawJson ?? this.rawJson,
      latitude: latitude ?? this.latitude,
      longitude: longitude ?? this.longitude,
    );
  }

  String get displayHeartRate {
    if (!finger && source == "REAL ESP32") return "--";
    return heartRate > 0 ? heartRate.toStringAsFixed(0) : "--";
  }

  String get displaySpo2 {
    if (spo2 == null) return "--";
    return spo2!.toStringAsFixed(0);
  }

  String get displayTemperature {
    if (temperature == null) return "--";
    return temperature!.toStringAsFixed(1);
  }
}
