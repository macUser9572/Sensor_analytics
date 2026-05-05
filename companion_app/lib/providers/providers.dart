import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/models.dart';
import '../services/api_service.dart';
import '../services/websocket_service.dart';
import '../config/app_config.dart';
export '../services/websocket_service.dart' show WsConnectionState;
import 'dart:async';

// Tracks WebSocket live connection state
final wsConnectionProvider = StreamProvider<WsConnectionState>((ref) {
  return webSocketService.connectionStateStream;
});

// Provides the stream of SubsystemStatus real-time data
final subsystemsProvider = StreamProvider<Map<String, SubsystemStatus>>((ref) {
  return webSocketService.subsystemStatusStream;
});

// Provides the stream of newly fired alerts
final alertsStreamProvider = StreamProvider<AlertEvent>((ref) {
  return webSocketService.alertEventStream;
});

// A provider that maintains the current list of active alerts by blending API and WS data
final activeAlertsProvider =
    StateNotifierProvider<ActiveAlertsNotifier, AsyncValue<List<Alert>>>((ref) {
  final notifier = ActiveAlertsNotifier(ref);
  notifier.fetchInitialAlerts();

  ref.listen<AsyncValue<AlertEvent>>(alertsStreamProvider, (previous, next) {
    if (next.hasValue && next.value != null) {
      final event = next.value!;
      if (event.type == AlertEventType.fired) {
        notifier.addOrUpdateAlert(event.alert!);
      } else if (event.type == AlertEventType.resolved) {
        notifier.removeAlertBySensorId(event.sensorId!);
      }
    }
  });

  return notifier;
});

class ActiveAlertsNotifier extends StateNotifier<AsyncValue<List<Alert>>> {
  final Ref ref;
  Timer? _refreshTimer;

  ActiveAlertsNotifier(this.ref) : super(const AsyncLoading()) {
    _refreshTimer = Timer.periodic(const Duration(seconds: 10), (_) {
      _silentRefresh();
    });
  }

  @override
  void dispose() {
    _refreshTimer?.cancel();
    super.dispose();
  }

  Future<void> fetchInitialAlerts() async {
    if (AppConfig.isUnconfigured) {
      state = const AsyncData([]);
      return;
    }
    try {
      state = const AsyncLoading();
      final alerts = await apiService.fetchActiveAlerts();
      state = AsyncData(alerts);
    } catch (e, stack) {
      state = AsyncError(e, stack);
    }
  }

  Future<void> _silentRefresh() async {
    if (AppConfig.isUnconfigured) return;
    try {
      final alerts = await apiService.fetchActiveAlerts();
      state = AsyncData(alerts);
    } catch (_) {
      // Keep existing state on network hiccup
    }
  }

  void addOrUpdateAlert(Alert newAlert) {
    if (state.hasValue && state.value != null) {
      final currentAlerts = List<Alert>.from(state.value!);
      final index = currentAlerts.indexWhere((a) => a.id == newAlert.id);
      if (index >= 0) {
        currentAlerts[index] = newAlert;
      } else {
        currentAlerts.insert(0, newAlert);
      }
      state = AsyncData(currentAlerts);
    }
  }

  void removeAlertBySensorId(String sensorId) {
    if (state.hasValue && state.value != null) {
      final updated =
          state.value!.where((a) => a.sensorId != sensorId).toList();
      state = AsyncData(updated);
    }
  }

  Future<bool> acknowledge(String alertId) async {
    final success = await apiService.acknowledgeAlert(alertId);
    if (success && state.hasValue) {
      final currentAlerts =
          state.value!.where((a) => a.id != alertId).toList();
      state = AsyncData(currentAlerts);
    }
    return success;
  }
}

// A provider that exposes the live readings stream
final liveReadingsStreamProvider = StreamProvider<List<SensorReading>>((ref) {
  return webSocketService.liveReadingsStream;
});

// Global sensors map provider
final sensorsMapProvider =
    StateNotifierProvider<SensorsMapNotifier, AsyncValue<Map<String, SensorReading>>>(
        (ref) {
  final notifier = SensorsMapNotifier();
  notifier.fetchInitialSensors();

  ref.listen<AsyncValue<List<SensorReading>>>(liveReadingsStreamProvider,
      (previous, next) {
    if (next.hasValue && next.value != null) {
      notifier.updateFromLive(next.value!);
    }
  });

  return notifier;
});

class SensorsMapNotifier
    extends StateNotifier<AsyncValue<Map<String, SensorReading>>> {
  SensorsMapNotifier() : super(const AsyncLoading());

  Future<void> fetchInitialSensors() async {
    if (AppConfig.isUnconfigured) {
      // Don't throw network errors when no IP is configured yet
      state = const AsyncData({});
      return;
    }
    try {
      state = const AsyncLoading();
      final allSensors = await apiService.fetchCurrentSensors();
      state = AsyncData(allSensors);
    } catch (e, stack) {
      state = AsyncError(e, stack);
    }
  }

  void updateFromLive(List<SensorReading> liveReadings) {
    if (state.hasValue && state.value != null) {
      final currentMap = Map<String, SensorReading>.from(state.value!);
      for (final r in liveReadings) {
        currentMap[r.id] = r;
      }
      state = AsyncData(currentMap);
    }
  }
}

// Current Sensors State for a specific subsystem
final currentSensorsProvider =
    Provider.family<AsyncValue<List<SensorReading>>, String>((ref, subsystem) {
  final sensorsMap = ref.watch(sensorsMapProvider);
  return sensorsMap.whenData((map) {
    final lower = subsystem.toLowerCase();
    return map.values.where((s) => s.subsystem.toLowerCase() == lower).toList();
  });
});

// Selected sensors for comparison feature
final selectedSensorsProvider =
    StateNotifierProvider<SelectedSensorsNotifier, List<String>>((ref) {
  return SelectedSensorsNotifier();
});

class SelectedSensorsNotifier extends StateNotifier<List<String>> {
  SelectedSensorsNotifier() : super([]);

  void toggleSelection(String id) {
    if (state.contains(id)) {
      state = state.where((s) => s != id).toList();
    } else {
      state = [...state, id];
    }
  }

  void clearSelection() {
    state = [];
  }
}
