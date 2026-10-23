import 'sensor_data.dart';

class EnvironmentModel {
  final double? pm25;
  final double? pm10;
  final double? no;
  final double? no2;
  final double? nox;
  final double? nh3;
  final double? co;
  final double? so2;
  final double? o3;
  final double? benzene;
  final double? toluene;
  final double? xylene;
  final String source;
  final String location;

  EnvironmentModel({
    this.pm25,
    this.pm10,
    this.no,
    this.no2,
    this.nox,
    this.nh3,
    this.co,
    this.so2,
    this.o3,
    this.benzene,
    this.toluene,
    this.xylene,
    required this.source,
    required this.location,
  });

  factory EnvironmentModel.fromJson(Map<String, dynamic> json) {
    return EnvironmentModel(
      pm25: (json['pm25'] as num?)?.toDouble(),
      pm10: (json['pm10'] as num?)?.toDouble(),
      no: (json['no'] as num?)?.toDouble(),
      no2: (json['no2'] as num?)?.toDouble(),
      nox: (json['nox'] as num?)?.toDouble(),
      nh3: (json['nh3'] as num?)?.toDouble(),
      co: (json['co'] as num?)?.toDouble(),
      so2: (json['so2'] as num?)?.toDouble(),
      o3: (json['o3'] as num?)?.toDouble(),
      benzene: (json['benzene'] as num?)?.toDouble(),
      toluene: (json['toluene'] as num?)?.toDouble(),
      xylene: (json['xylene'] as num?)?.toDouble(),
      source: json['source'] ?? "Unknown",
      location: json['location'] ?? "Unknown",
    );
  }

  Map<String, double> getActivePollutants() {
    final map = <String, double>{};
    if (pm25 != null) map['PM2.5'] = pm25!;
    if (pm10 != null) map['PM10'] = pm10!;
    if (no2 != null) map['NO2'] = no2!;
    if (co != null) map['CO'] = co!;
    if (so2 != null) map['SO2'] = so2!;
    if (o3 != null) map['O3'] = o3!;
    if (nh3 != null) map['NH3'] = nh3!;
    if (benzene != null) map['Benzene'] = benzene!;
    return map;
  }
}

class AQIPredictionModel {
  final String predictedBucket;
  final double confidence;
  final Map<String, double> probabilities;

  AQIPredictionModel({
    required this.predictedBucket,
    required this.confidence,
    required this.probabilities,
  });

  factory AQIPredictionModel.fromJson(Map<String, dynamic> json) {
    final probs = <String, double>{};
    if (json['probabilities'] != null && json['probabilities'] is Map) {
      (json['probabilities'] as Map).forEach((k, v) {
        probs[k.toString()] = (v as num).toDouble();
      });
    }
    return AQIPredictionModel(
      predictedBucket: json['predicted_bucket'] ?? "Moderate",
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0.8,
      probabilities: probs,
    );
  }
}

class PhysiologicalPredictionModel {
  final String predictedStress;
  final double confidence;
  final Map<String, double> probabilities;

  PhysiologicalPredictionModel({
    required this.predictedStress,
    required this.confidence,
    required this.probabilities,
  });

  factory PhysiologicalPredictionModel.fromJson(Map<String, dynamic> json) {
    final probs = <String, double>{};
    if (json['probabilities'] != null && json['probabilities'] is Map) {
      (json['probabilities'] as Map).forEach((k, v) {
        probs[k.toString()] = (v as num).toDouble();
      });
    }
    return PhysiologicalPredictionModel(
      predictedStress: json['predicted_stress'] ?? "Low",
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0.85,
      probabilities: probs,
    );
  }
}

class RiskAssessmentModel {
  final double riskScore;
  final String riskLevel;
  final double environmentalComponent;
  final double physiologicalComponent;
  final Map<String, double> vitalModifiers;
  final String statusSummary;
  final String prototypeDisclaimer;

  RiskAssessmentModel({
    required this.riskScore,
    required this.riskLevel,
    required this.environmentalComponent,
    required this.physiologicalComponent,
    required this.vitalModifiers,
    required this.statusSummary,
    required this.prototypeDisclaimer,
  });

  factory RiskAssessmentModel.fromJson(Map<String, dynamic> json) {
    final mods = <String, double>{};
    if (json['vital_modifiers'] != null && json['vital_modifiers'] is Map) {
      (json['vital_modifiers'] as Map).forEach((k, v) {
        mods[k.toString()] = (v as num).toDouble();
      });
    }
    return RiskAssessmentModel(
      riskScore: (json['risk_score'] as num?)?.toDouble() ?? 25.0,
      riskLevel: json['risk_level'] ?? "Low",
      environmentalComponent: (json['environmental_component'] as num?)?.toDouble() ?? 12.0,
      physiologicalComponent: (json['physiological_component'] as num?)?.toDouble() ?? 13.0,
      vitalModifiers: mods,
      statusSummary: json['status_summary'] ?? "Stable condition.",
      prototypeDisclaimer: json['prototype_disclaimer'] ?? "Prototype risk indicator.",
    );
  }
}

class SHAPFactorModel {
  final String feature;
  final double contribution;
  final String impactDescription;

  SHAPFactorModel({
    required this.feature,
    required this.contribution,
    required this.impactDescription,
  });

  factory SHAPFactorModel.fromJson(Map<String, dynamic> json) {
    return SHAPFactorModel(
      feature: json['feature'] ?? "",
      contribution: (json['contribution'] as num?)?.toDouble() ?? 0.0,
      impactDescription: json['impact_description'] ?? "",
    );
  }
}

class ExplanationDetailModel {
  final List<SHAPFactorModel> environmentalFactors;
  final List<SHAPFactorModel> physiologicalFactors;
  final String modelContributionNote;

  ExplanationDetailModel({
    required this.environmentalFactors,
    required this.physiologicalFactors,
    required this.modelContributionNote,
  });

  factory ExplanationDetailModel.fromJson(Map<String, dynamic> json) {
    var envList = <SHAPFactorModel>[];
    if (json['environmental_factors'] != null) {
      envList = (json['environmental_factors'] as List)
          .map((i) => SHAPFactorModel.fromJson(i))
          .toList();
    }
    var physList = <SHAPFactorModel>[];
    if (json['physiological_factors'] != null) {
      physList = (json['physiological_factors'] as List)
          .map((i) => SHAPFactorModel.fromJson(i))
          .toList();
    }
    return ExplanationDetailModel(
      environmentalFactors: envList,
      physiologicalFactors: physList,
      modelContributionNote: json['model_contribution_note'] ?? "",
    );
  }
}

class TelemetryResponse {
  final bool success;
  final String timestamp;
  final SensorData sensorData;
  final EnvironmentModel environment;
  final AQIPredictionModel aqiPrediction;
  final PhysiologicalPredictionModel physiologicalPrediction;
  final RiskAssessmentModel personalizedRisk;
  final ExplanationDetailModel explanation;

  TelemetryResponse({
    required this.success,
    required this.timestamp,
    required this.sensorData,
    required this.environment,
    required this.aqiPrediction,
    required this.physiologicalPrediction,
    required this.personalizedRisk,
    required this.explanation,
  });

  factory TelemetryResponse.fromJson(Map<String, dynamic> json) {
    return TelemetryResponse(
      success: json['success'] ?? true,
      timestamp: json['timestamp'] ?? "",
      sensorData: SensorData.fromJson(json['sensor_data'] ?? {}),
      environment: EnvironmentModel.fromJson(json['environment'] ?? {}),
      aqiPrediction: AQIPredictionModel.fromJson(json['aqi_prediction'] ?? {}),
      physiologicalPrediction:
          PhysiologicalPredictionModel.fromJson(json['physiological_prediction'] ?? {}),
      personalizedRisk: RiskAssessmentModel.fromJson(json['personalized_risk'] ?? {}),
      explanation: ExplanationDetailModel.fromJson(json['explanation'] ?? {}),
    );
  }
}
