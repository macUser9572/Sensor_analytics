import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../providers/providers.dart';
import '../models/models.dart';
import '../services/websocket_service.dart';
import '../config/app_config.dart';

// Actual subsystem keys sent by the backend (lowercase)
const _kSubsystems = [
  'turbine',
  'boiler',
  'generator',
  'cooling',
  'transformer',
  'auxiliary',
];

// Display labels shown to the user
const _kSubsystemLabels = {
  'turbine':     'Turbine',
  'boiler':      'Boiler',
  'generator':   'Generator',
  'cooling':     'Cooling',
  'transformer': 'Transformer',
  'auxiliary':   'Auxiliary',
};

class OverviewScreen extends ConsumerStatefulWidget {
  const OverviewScreen({super.key});

  @override
  ConsumerState<OverviewScreen> createState() => _OverviewScreenState();
}

class _OverviewScreenState extends ConsumerState<OverviewScreen>
    with SingleTickerProviderStateMixin {
  late AnimationController _pulseController;
  late Animation<double> _pulseAnimation;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 1),
    )..repeat(reverse: true);
    _pulseAnimation = Tween<double>(begin: 1.0, end: 0.4).animate(_pulseController);
  }

  @override
  void dispose() {
    _pulseController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final subsystemsAsync  = ref.watch(subsystemsProvider);
    final activeAlertsAsync = ref.watch(activeAlertsProvider);
    final wsState          = ref.watch(wsConnectionProvider).value
        ?? webSocketService.connectionState;
    final sensorsAsync     = ref.watch(sensorsMapProvider);
    final selectedSensors  = ref.watch(selectedSensorsProvider);
    final sensorsMap       = sensorsAsync.value ?? {};

    final Map<String, SubsystemStatus> subsystems = subsystemsAsync.value ?? {};
    final int alertCount = activeAlertsAsync.value?.length ?? 0;

    int selectedSubsystemsCount = 0;
    if (selectedSensors.isNotEmpty) {
      final subs = <String>{};
      for (final id in selectedSensors) {
        if (sensorsMap.containsKey(id)) {
          subs.add(sensorsMap[id]!.subsystem);
        }
      }
      selectedSubsystemsCount = subs.length;
    }

    // Derive a human-readable connection status for the header dot
    final Color dotColor = wsState == WsConnectionState.connected
        ? Colors.greenAccent
        : wsState == WsConnectionState.connecting
            ? Colors.amberAccent
            : Colors.redAccent;
    final String dotTooltip = wsState == WsConnectionState.connected
        ? 'Live'
        : wsState == WsConnectionState.connecting
            ? 'Connecting…'
            : 'Disconnected';

    // API error banner (shown below AppBar when HTTP fetch failed)
    final String? apiError = sensorsAsync.hasError
        ? _friendlyError(sensorsAsync.error)
        : null;

    // Detect unconfigured default IP so we can prompt the user to set it
    final bool isDefaultIp = AppConfig.apiBase.contains('192.168.1.102');

    return Scaffold(
      appBar: AppBar(
        title: const Text('BHEL Unit 5 — Live Monitoring',
            style: TextStyle(fontSize: 18)),
        actions: [
          if (selectedSensors.length >= 2)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 8.0),
              child: ElevatedButton(
                onPressed: () => context.push('/compare'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Theme.of(context).colorScheme.secondary,
                  foregroundColor: Colors.white,
                ),
                child: Text(
                    'COMPARE (${selectedSensors.length}) · $selectedSubsystemsCount subs'),
              ),
            ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 6.0),
            child: Tooltip(
              message: dotTooltip,
              child: Center(
                child: Container(
                  width: 12,
                  height: 12,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: dotColor,
                  ),
                ),
              ),
            ),
          ),
          // Connection state label next to dot
          Padding(
            padding: const EdgeInsets.only(right: 8.0),
            child: Center(
              child: Text(
                dotTooltip,
                style: TextStyle(
                  fontSize: 11,
                  color: dotColor,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
          ),
          IconButton(
            icon: const Icon(Icons.settings),
            onPressed: () => context.push('/settings'),
          ),
        ],
      ),
      body: Column(
        children: [
          // First-launch setup prompt — shown when the placeholder IP is still set
          if (isDefaultIp)
            _buildErrorBanner(
              icon: Icons.settings_ethernet,
              color: Colors.blueAccent,
              message:
                  'Server IP not configured. Tap Settings and enter your server\'s IP address.',
              onRetry: () => context.push('/settings'),
              retryLabel: 'Open Settings',
            ),
          // API error banner
          if (apiError != null && !isDefaultIp)
            _buildErrorBanner(
              icon: Icons.cloud_off,
              color: Colors.orangeAccent,
              message: 'API: $apiError',
              onRetry: () => ref.read(sensorsMapProvider.notifier).fetchInitialSensors(),
            ),
          // WebSocket disconnected banner
          if (wsState == WsConnectionState.disconnected && !isDefaultIp)
            _buildErrorBanner(
              icon: Icons.wifi_off,
              color: Colors.redAccent,
              message: 'Live stream disconnected — retrying…',
            ),
          // WebSocket connecting banner
          if (wsState == WsConnectionState.connecting && !isDefaultIp)
            _buildErrorBanner(
              icon: Icons.wifi_tethering,
              color: Colors.amberAccent,
              message: 'Connecting to live stream…',
            ),
          Expanded(
            child: GridView.builder(
              padding: const EdgeInsets.all(16),
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 2,
                crossAxisSpacing: 16,
                mainAxisSpacing: 16,
                childAspectRatio: 0.85,
              ),
              itemCount: _kSubsystems.length,
              itemBuilder: (context, index) {
                final key    = _kSubsystems[index];
                final label  = _kSubsystemLabels[key]!;
                final status = subsystems[key];
                return _buildSubsystemCard(
                  context,
                  key: key,
                  label: label,
                  status: status,
                  wsState: wsState,
                  apiError: sensorsAsync.hasError,
                );
              },
            ),
          ),
          _buildAlertsBanner(context, alertCount),
        ],
      ),
    );
  }

  Widget _buildErrorBanner({
    required IconData icon,
    required Color color,
    required String message,
    VoidCallback? onRetry,
    String retryLabel = 'Retry',
  }) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      color: color.withValues(alpha:0.12),
      child: Row(
        children: [
          Icon(icon, color: color, size: 16),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              message,
              style: TextStyle(color: color, fontSize: 12),
            ),
          ),
          if (onRetry != null)
            TextButton(
              onPressed: onRetry,
              style: TextButton.styleFrom(
                padding: EdgeInsets.zero,
                minimumSize: const Size(40, 24),
              ),
              child: Text(retryLabel, style: TextStyle(color: color, fontSize: 12)),
            ),
        ],
      ),
    );
  }

  Widget _buildSubsystemCard(
    BuildContext context, {
    required String key,
    required String label,
    required SubsystemStatus? status,
    required WsConnectionState wsState,
    required bool apiError,
  }) {
    Color borderColor;
    String worst = 'normal';
    Widget bottomContent;

    if (status != null) {
      // We have live data — normal card
      worst = status.worstStatus;
      switch (worst) {
        case 'fault':
          borderColor = Colors.grey;
          break;
        case 'critical':
          borderColor = Colors.redAccent;
          break;
        case 'warning':
          borderColor = Colors.orangeAccent;
          break;
        default:
          borderColor = Colors.greenAccent.withValues(alpha:0.5);
      }
      bottomContent = Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '${status.totalSensors} Sensors',
            style: TextStyle(color: Colors.grey[400], fontSize: 12),
          ),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              _buildStatusChip(status.normalCount,   Colors.greenAccent),
              _buildStatusChip(status.warningCount,  Colors.orangeAccent),
              _buildStatusChip(status.criticalCount, Colors.redAccent),
              if (status.faultCount + status.missingCount > 0)
                _buildStatusChip(
                    status.faultCount + status.missingCount, Colors.grey),
            ],
          ),
        ],
      );
    } else {
      // No data yet — show a helpful state message
      borderColor = Colors.grey.withValues(alpha:0.2);
      final String stateMsg;
      final Color stateColor;
      final IconData stateIcon;

      if (apiError) {
        stateMsg   = 'Cannot reach API server.\nCheck Settings.';
        stateColor = Colors.orangeAccent;
        stateIcon  = Icons.cloud_off;
      } else if (wsState == WsConnectionState.disconnected) {
        stateMsg   = 'Live stream disconnected.\nRetrying…';
        stateColor = Colors.redAccent;
        stateIcon  = Icons.wifi_off;
      } else if (wsState == WsConnectionState.connecting) {
        stateMsg   = 'Connecting to server…';
        stateColor = Colors.amberAccent;
        stateIcon  = Icons.wifi_tethering;
      } else {
        // Connected but this subsystem hasn't reported yet
        stateMsg   = 'No data from subsystem yet';
        stateColor = Colors.grey;
        stateIcon  = Icons.hourglass_empty;
      }

      bottomContent = Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(stateIcon, size: 14, color: stateColor),
          const SizedBox(width: 6),
          Expanded(
            child: Text(
              stateMsg,
              style: TextStyle(color: stateColor, fontSize: 11),
            ),
          ),
        ],
      );
    }

    Widget cardContent = Container(
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
            color: borderColor, width: worst == 'critical' ? 3 : 2),
        boxShadow: worst == 'normal' || status == null
            ? []
            : [
                BoxShadow(
                  color: borderColor.withValues(alpha:0.3),
                  blurRadius: 8,
                  spreadRadius: 2,
                ),
              ],
      ),
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Icon(
                worst == 'fault'
                    ? Icons.sensors_off
                    : Icons.dashboard_customize_outlined,
                color: worst == 'fault' ? Colors.grey : Colors.grey[400],
                size: 32,
              ),
              if (worst == 'fault')
                const Icon(Icons.close, color: Colors.grey),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            label,
            style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
          const Spacer(),
          bottomContent,
        ],
      ),
    );

    if (worst == 'critical') {
      cardContent = AnimatedBuilder(
        animation: _pulseAnimation,
        builder: (context, child) =>
            Opacity(opacity: _pulseAnimation.value, child: child),
        child: cardContent,
      );
    }

    return InkWell(
      onTap: () => context.push('/subsystem/$key'),
      child: cardContent,
    );
  }

  Widget _buildStatusChip(int count, Color color) {
    if (count == 0) return const SizedBox.shrink();
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: color.withValues(alpha:0.15),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withValues(alpha:0.5)),
      ),
      child: Text(
        count.toString(),
        style: TextStyle(
            color: color, fontWeight: FontWeight.bold, fontSize: 12),
      ),
    );
  }

  Widget _buildAlertsBanner(BuildContext context, int count) {
    return InkWell(
      onTap: () => context.push('/alerts'),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: count > 0
              ? Colors.redAccent.withValues(alpha:0.2)
              : Colors.greenAccent.withValues(alpha:0.1),
          border: Border(
            top: BorderSide(
                color: count > 0 ? Colors.redAccent : Colors.greenAccent),
          ),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Row(
              children: [
                Icon(
                  count > 0
                      ? Icons.warning_amber_rounded
                      : Icons.check_circle_outline,
                  color: count > 0 ? Colors.redAccent : Colors.greenAccent,
                ),
                const SizedBox(width: 8),
                Text(
                  'Active Alerts',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                    color:
                        count > 0 ? Colors.redAccent : Colors.greenAccent,
                  ),
                ),
              ],
            ),
            Container(
              padding:
                  const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                color: count > 0 ? Colors.redAccent : Colors.greenAccent,
                borderRadius: BorderRadius.circular(16),
              ),
              child: Text(
                count.toString(),
                style: const TextStyle(
                    fontWeight: FontWeight.bold, color: Colors.white),
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _friendlyError(Object? error) {
    if (error == null) return 'Unknown error';
    final msg = error.toString();
    if (msg.contains('SocketException') || msg.contains('Connection refused')) {
      return 'Cannot reach server — check IP in Settings';
    }
    if (msg.contains('TimeoutException') || msg.contains('timed out')) {
      return 'Request timed out — server may be down';
    }
    if (msg.contains('401') || msg.contains('403')) {
      return 'Authentication error';
    }
    if (msg.contains('404')) {
      return 'API endpoint not found';
    }
    // Trim the "Exception: Network error:" prefix that ApiService wraps
    return msg
        .replaceFirst('Exception: Network error: ', '')
        .replaceFirst('Exception: ', '')
        .split('\n')
        .first;
  }
}
