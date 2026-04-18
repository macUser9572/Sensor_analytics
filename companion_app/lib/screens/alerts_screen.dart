import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../providers/providers.dart';
import '../models/models.dart';

class AlertsScreen extends ConsumerWidget {
  const AlertsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final alertsState = ref.watch(activeAlertsProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Active Alerts'),
      ),
      body: RefreshIndicator(
        onRefresh: () async {
          await ref.read(activeAlertsProvider.notifier).fetchInitialAlerts();
        },
        child: _buildBody(context, ref, alertsState),
      ),
    );
  }

  Widget _buildBody(BuildContext context, WidgetRef ref, AsyncValue<List<Alert>> state) {
    return state.when(
      data: (alerts) {
        if (alerts.isEmpty) {
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.check_circle, color: Colors.greenAccent[400], size: 80),
                const SizedBox(height: 16),
                const Text(
                  'All systems normal',
                  style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 8),
                const Text('No active alerts at this time.', style: TextStyle(color: Colors.grey)),
              ],
            ),
          );
        }

        return ListView.builder(
          padding: const EdgeInsets.symmetric(vertical: 8),
          itemCount: alerts.length,
          itemBuilder: (context, index) {
            final alert = alerts[index];
            return _buildAlertCard(context, ref, alert);
          },
        );
      },
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (err, stack) => Center(
        child: Text('Error loading alerts: $err', style: const TextStyle(color: Colors.redAccent)),
      ),
    );
  }

  Widget _buildAlertCard(BuildContext context, WidgetRef ref, Alert alert) {
    final isCritical = alert.type == 'critical';
    final color = isCritical ? Colors.redAccent : Colors.orangeAccent;
    final Duration duration = DateTime.now().difference(alert.firedAt);
    
    String timeAgo;
    if (duration.inMinutes < 60) {
      timeAgo = '${duration.inMinutes}m ago';
    } else {
      timeAgo = '${duration.inHours}h ${duration.inMinutes % 60}m ago';
    }

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: color.withOpacity(0.5), width: 1),
      ),
      elevation: 4,
      child: Container(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(12),
          border: Border(left: BorderSide(color: color, width: 6)),
        ),
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  children: [
                    Icon(
                      isCritical ? Icons.cancel : Icons.warning,
                      color: color,
                      size: 20,
                    ),
                    const SizedBox(width: 8),
                    Text(
                      alert.type.toUpperCase(),
                      style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 12),
                    ),
                  ],
                ),
                Text(timeAgo, style: const TextStyle(color: Colors.grey, fontSize: 12)),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              alert.metric.toUpperCase(),
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 4),
            Text('${alert.subsystem} • Sensor ID: ${alert.sensorId}', style: const TextStyle(color: Colors.grey)),
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.black12,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('Current Value', style: TextStyle(color: Colors.grey, fontSize: 12)),
                      Text(
                        alert.currentValue.toStringAsFixed(2),
                        style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 16),
                      ),
                    ],
                  ),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      const Text('Threshold', style: TextStyle(color: Colors.grey, fontSize: 12)),
                      Text(
                        alert.threshold.toStringAsFixed(2),
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: color.withOpacity(0.1),
                  foregroundColor: color,
                  side: BorderSide(color: color),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                ),
                onPressed: () async {
                  final success = await ref.read(activeAlertsProvider.notifier).acknowledge(alert.id);
                  if (success && context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: const Text('Alert acknowledged'),
                        behavior: SnackBarBehavior.floating,
                        backgroundColor: Colors.green[800],
                      ),
                    );
                  }
                },
                child: const Text('ACKNOWLEDGE'),
              ),
            )
          ],
        ),
      ),
    );
  }
}
