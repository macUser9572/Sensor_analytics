import 'dart:async';
import 'dart:convert';
import 'dart:math';
import 'package:flutter/foundation.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import '../models/models.dart';
import '../config/app_config.dart';

enum WsConnectionState { connecting, connected, disconnected }

class WebSocketService {
  WebSocketChannel? _liveChannel;
  WebSocketChannel? _alertsChannel;

  final Map<String, SubsystemStatus> _currentStatus = {};
  final _subsystemsController      = StreamController<Map<String, SubsystemStatus>>.broadcast();
  final _alertEventController      = StreamController<AlertEvent>.broadcast();
  final _liveReadingsController    = StreamController<List<SensorReading>>.broadcast();
  final _connectionStateController = StreamController<WsConnectionState>.broadcast();

  WsConnectionState _connectionState = WsConnectionState.connecting;

  Stream<Map<String, SubsystemStatus>> get subsystemStatusStream  => _subsystemsController.stream;
  Stream<List<SensorReading>>          get liveReadingsStream     => _liveReadingsController.stream;
  Stream<AlertEvent>                   get alertEventStream       => _alertEventController.stream;
  Stream<WsConnectionState>            get connectionStateStream  => _connectionStateController.stream;
  WsConnectionState                    get connectionState        => _connectionState;

  Timer? _liveReconnectTimer;
  Timer? _alertsReconnectTimer;
  Timer? _pingTimer;

  int _liveRetryCount   = 0;
  int _alertsRetryCount = 0;
  final int maxRetrySeconds = 30;

  void _emitState(WsConnectionState s) {
    _connectionState = s;
    _connectionStateController.add(s);
  }

  // ──────────────────────────────────────────────
  // LIVE SENSOR STREAM  (ws/live)
  // ──────────────────────────────────────────────
  void connectLive() {
    _emitState(WsConnectionState.connecting);
    try {
      final uri = Uri.parse('${AppConfig.wsBase}/ws/live');
      _liveChannel = WebSocketChannel.connect(uri);
      _liveChannel!.ready.catchError((_) {
        _emitState(WsConnectionState.disconnected);
        _scheduleLiveReconnect();
      });

      _startPingTimer();

      _liveChannel!.stream.listen(
        (data) {
          _liveRetryCount = 0;
          try {
            if (data == 'pong') return;
            final parsedData = jsonDecode(data as String) as Map<String, dynamic>;

            if (parsedData['subsystem'] != null && parsedData['readings'] != null) {
              _emitState(WsConnectionState.connected);

              final String subName = parsedData['subsystem'] as String;
              final List<dynamic> readings = parsedData['readings'] as List<dynamic>;

              int normal = 0, warning = 0, critical = 0, fault = 0;
              final List<SensorReading> parsedReadings = [];

              for (final r in readings) {
                final s = r['status'] as String? ?? 'normal';
                if (s == 'normal') {
                  normal++;
                } else if (s == 'warning') {
                  warning++;
                } else if (s == 'critical') {
                  critical++;
                } else {
                  fault++;
                }

                try {
                  r['subsystem'] ??= subName;
                  parsedReadings.add(SensorReading.fromJson(r as Map<String, dynamic>));
                } catch (e) {
                  debugPrint('Error parsing sensor reading: $e');
                }
              }

              _currentStatus[subName] = SubsystemStatus(
                name: subName,
                totalSensors: readings.length,
                normalCount: normal,
                warningCount: warning,
                criticalCount: critical,
                faultCount: fault,
              );

              _subsystemsController.add(Map.from(_currentStatus));
              _liveReadingsController.add(parsedReadings);
            }
          } catch (e) {
            debugPrint('Error parsing live data: $e');
          }
        },
        onDone: () {
          _emitState(WsConnectionState.disconnected);
          _scheduleLiveReconnect();
        },
        onError: (_) {
          _emitState(WsConnectionState.disconnected);
          _scheduleLiveReconnect();
        },
      );
    } catch (_) {
      _emitState(WsConnectionState.disconnected);
      _scheduleLiveReconnect();
    }
  }

  void _startPingTimer() {
    _pingTimer?.cancel();
    _pingTimer = Timer.periodic(const Duration(seconds: 30), (_) {
      try {
        _liveChannel?.sink.add('ping');
      } catch (_) {}
    });
  }

  // ──────────────────────────────────────────────
  // ALERTS STREAM  (ws/alerts)
  // ──────────────────────────────────────────────
  void connectAlerts() {
    try {
      final uri = Uri.parse('${AppConfig.wsBase}/ws/alerts');
      _alertsChannel = WebSocketChannel.connect(uri);
      _alertsChannel!.ready.catchError((_) => _scheduleAlertsReconnect());

      _alertsChannel!.stream.listen(
        (data) {
          _alertsRetryCount = 0;
          try {
            final parsedData = jsonDecode(data as String) as Map<String, dynamic>;

            // Initial dump of active alerts on connect
            if (parsedData['type'] == 'active_alerts') return;

            final event = parsedData['event'] as String? ?? '';
            if (event == 'alert_fired' && parsedData['alert'] != null) {
              final alert = Alert.fromJson(parsedData['alert'] as Map<String, dynamic>);
              _alertEventController.add(AlertEvent.fired(alert));
            } else if (event == 'alert_resolved') {
              final sensorId = parsedData['sensor_id'] as String?;
              if (sensorId != null) {
                _alertEventController.add(AlertEvent.resolved(sensorId));
              }
            }
          } catch (e) {
            debugPrint('Error parsing alert data: $e');
          }
        },
        onDone:  () => _scheduleAlertsReconnect(),
        onError: (_) => _scheduleAlertsReconnect(),
      );
    } catch (_) {
      _scheduleAlertsReconnect();
    }
  }

  // ──────────────────────────────────────────────
  // RECONNECTION
  // ──────────────────────────────────────────────
  void reconnect() {
    _liveChannel?.sink.close();
    _alertsChannel?.sink.close();
    _liveReconnectTimer?.cancel();
    _alertsReconnectTimer?.cancel();
    _liveRetryCount = 0;
    _alertsRetryCount = 0;
    connectLive();
    connectAlerts();
  }

  void _scheduleLiveReconnect() {
    if (_liveReconnectTimer?.isActive ?? false) return;
    final delay = _backoff(_liveRetryCount++);
    _liveReconnectTimer = Timer(Duration(seconds: delay), connectLive);
  }

  void _scheduleAlertsReconnect() {
    if (_alertsReconnectTimer?.isActive ?? false) return;
    final delay = _backoff(_alertsRetryCount++);
    _alertsReconnectTimer = Timer(Duration(seconds: delay), connectAlerts);
  }

  int _backoff(int count) => min(pow(2, count).toInt(), maxRetrySeconds);

  void dispose() {
    _pingTimer?.cancel();
    _liveReconnectTimer?.cancel();
    _alertsReconnectTimer?.cancel();
    _liveChannel?.sink.close();
    _alertsChannel?.sink.close();
    _subsystemsController.close();
    _alertEventController.close();
    _liveReadingsController.close();
    _connectionStateController.close();
  }
}

final webSocketService = WebSocketService();
