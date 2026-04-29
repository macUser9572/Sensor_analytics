enum SensorHealthState { live, stale, uncertain, fault }

class SensorReading {
  final String id;
  final String subsystem;
  final String metric;
  final double value;
  final String unit;
  final String status; // normal, warning, critical
  final DateTime timestamp;

  SensorHealthState get healthState {
    if (status == 'fault' || status == 'missing') return SensorHealthState.fault;
    final age = DateTime.now().difference(timestamp).inSeconds;
    if (age > 60) return SensorHealthState.uncertain;
    if (age > 15 || status == 'warning' || status == 'stale') return SensorHealthState.stale;
    return SensorHealthState.live;
  }

  SensorReading({
    required this.id,
    required this.subsystem,
    required this.metric,
    required this.value,
    required this.unit,
    required this.status,
    required this.timestamp,
  });

  factory SensorReading.fromJson(Map<String, dynamic> json) {
    return SensorReading(
      id: json['id'] ?? json['sensor_id'] ?? '',
      subsystem: json['subsystem'] ?? '',
      metric: json['name'] ?? json['metric'] ?? '',
      value: (json['value'] ?? 0.0).toDouble(),
      unit: json['unit'] ?? '',
      status: json['status'] ?? 'normal',
      timestamp: json['timestamp'] != null 
          ? DateTime.parse(json['timestamp']) 
          : DateTime.now(),
    );
  }
}

class SubsystemStatus {
  final String name;
  final int totalSensors;
  final int normalCount;
  final int warningCount;
  final int criticalCount;
  final int faultCount;
  final int missingCount;
  
  SubsystemStatus({
    required this.name,
    required this.totalSensors,
    required this.normalCount,
    required this.warningCount,
    required this.criticalCount,
    this.faultCount = 0,
    this.missingCount = 0,
  });

  String get worstStatus {
    if (faultCount > 0 || missingCount > 0) return 'fault';
    if (criticalCount > 0) return 'critical';
    if (warningCount > 0) return 'warning';
    return 'normal';
  }

  factory SubsystemStatus.fromJson(String name, Map<String, dynamic> json) {
    return SubsystemStatus(
      name: name,
      totalSensors: json['total'] ?? 0,
      normalCount: json['normal'] ?? 0,
      warningCount: json['warning'] ?? 0,
      criticalCount: json['critical'] ?? 0,
      faultCount: json['fault'] ?? 0,
      missingCount: json['missing'] ?? 0,
    );
  }
}

class Alert {
  final String id;
  final String sensorId;
  final String subsystem;
  final String metric;
  final String type; // warning, critical
  final double threshold;
  final double currentValue;
  final String unit;
  final DateTime firedAt;

  Alert({
    required this.id,
    required this.sensorId,
    required this.subsystem,
    required this.metric,
    required this.type,
    required this.threshold,
    required this.currentValue,
    required this.unit,
    required this.firedAt,
  });

  factory Alert.fromJson(Map<String, dynamic> json) {
    return Alert(
      id: json['id'] ?? '',
      sensorId: json['sensor_id'] ?? '',
      subsystem: json['subsystem'] ?? '',
      metric: json['sensor_name'] ?? json['metric'] ?? '',
      type: json['severity'] ?? json['type'] ?? 'warning',
      threshold: (json['threshold'] ?? 0.0).toDouble(),
      currentValue: (json['value'] ?? json['current_value'] ?? 0.0).toDouble(),
      unit: json['unit'] ?? '',
      firedAt: json['fired_at'] != null
          ? DateTime.parse(json['fired_at']).toLocal()
          : DateTime.now(),
    );
  }
}

// ── Alert event wrapper so WS can signal both "fired" and "resolved" ──────────
enum AlertEventType { fired, resolved }

class AlertEvent {
  final AlertEventType type;
  final Alert? alert;       // non-null when type == fired
  final String? sensorId;   // non-null when type == resolved

  const AlertEvent._({required this.type, this.alert, this.sensorId});

  factory AlertEvent.fired(Alert alert) =>
      AlertEvent._(type: AlertEventType.fired, alert: alert);

  factory AlertEvent.resolved(String sensorId) =>
      AlertEvent._(type: AlertEventType.resolved, sensorId: sensorId);
}
