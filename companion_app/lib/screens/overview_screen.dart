import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/providers.dart';
import '../models/models.dart';
import 'subsystem_screen.dart';
import 'alerts_screen.dart';

class OverviewScreen extends ConsumerWidget {
  const OverviewScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final subsystemsAsync = ref.watch(subsystemsProvider);
    final activeAlertsAsync = ref.watch(activeAlertsProvider);
    
    // Fallback UI structures if data is missing or loading
    final Map<String, SubsystemStatus> subsystems = subsystemsAsync.value ?? {};
    final int alertCount = activeAlertsAsync.value?.length ?? 0;

    return Scaffold(
      appBar: AppBar(
        title: const Text('BHEL Unit 5 — Live Monitoring'),
        actions: [
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: Container(
              width: 12,
              height: 12,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: subsystemsAsync.hasValue ? Colors.greenAccent : Colors.redAccent,
              ),
            ),
          )
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: subsystems.isEmpty 
                ? const Center(child: CircularProgressIndicator())
                : GridView.builder(
                    padding: const EdgeInsets.all(16),
                    gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                      crossAxisCount: 2,
                      crossAxisSpacing: 16,
                      mainAxisSpacing: 16,
                      childAspectRatio: 0.85,
                    ),
                    itemCount: subsystems.length,
                    itemBuilder: (context, index) {
                      final key = subsystems.keys.elementAt(index);
                      final status = subsystems[key]!;
                      return _buildSubsystemCard(context, status);
                    },
                  ),
          ),
          _buildAlertsBanner(context, alertCount),
        ],
      ),
    );
  }

  Widget _buildSubsystemCard(BuildContext context, SubsystemStatus status) {
    Color borderColor;
    switch (status.worstStatus) {
      case 'critical':
        borderColor = Colors.redAccent;
        break;
      case 'warning':
        borderColor = Colors.orangeAccent;
        break;
      default:
        borderColor = Colors.greenAccent;
    }

    return InkWell(
      onTap: () {
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (_) => SubsystemScreen(subsystem: status.name),
          ),
        );
      },
      child: Container(
        decoration: BoxDecoration(
          color: Theme.of(context).cardColor,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: borderColor, width: 2),
          boxShadow: [
            BoxShadow(
              color: borderColor.withOpacity(0.2),
              blurRadius: 8,
              spreadRadius: 2,
            )
          ],
        ),
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(Icons.dashboard_customize_outlined, color: Colors.grey[400], size: 32),
            const SizedBox(height: 12),
            Text(
              status.name,
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
            const Spacer(),
            Text('${status.totalSensors} Sensors', style: TextStyle(color: Colors.grey[400])),
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                _buildStatusChip(status.normalCount, Colors.greenAccent),
                _buildStatusChip(status.warningCount, Colors.orangeAccent),
                _buildStatusChip(status.criticalCount, Colors.redAccent),
              ],
            )
          ],
        ),
      ),
    );
  }

  Widget _buildStatusChip(int count, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.15),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withOpacity(0.5)),
      ),
      child: Text(
        count.toString(),
        style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 12),
      ),
    );
  }

  Widget _buildAlertsBanner(BuildContext context, int count) {
    return InkWell(
      onTap: () {
        Navigator.push(
          context,
          MaterialPageRoute(builder: (_) => const AlertsScreen()),
        );
      },
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: count > 0 ? Colors.redAccent.withOpacity(0.2) : Colors.greenAccent.withOpacity(0.1),
          border: Border(
            top: BorderSide(
              color: count > 0 ? Colors.redAccent : Colors.greenAccent,
            ),
          ),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Row(
              children: [
                Icon(
                  count > 0 ? Icons.warning_amber_rounded : Icons.check_circle_outline,
                  color: count > 0 ? Colors.redAccent : Colors.greenAccent,
                ),
                const SizedBox(width: 8),
                Text(
                  'Active Alerts',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                    color: count > 0 ? Colors.redAccent : Colors.greenAccent,
                  ),
                ),
              ],
            ),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                color: count > 0 ? Colors.redAccent : Colors.greenAccent,
                borderRadius: BorderRadius.circular(16),
              ),
              child: Text(
                count.toString(),
                style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.white),
              ),
            )
          ],
        ),
      ),
    );
  }
}
