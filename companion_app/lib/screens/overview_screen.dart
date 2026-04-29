import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../providers/providers.dart';
import '../models/models.dart';

class OverviewScreen extends ConsumerStatefulWidget {
  const OverviewScreen({super.key});

  @override
  ConsumerState<OverviewScreen> createState() => _OverviewScreenState();
}

class _OverviewScreenState extends ConsumerState<OverviewScreen> with SingleTickerProviderStateMixin {
  late AnimationController _pulseController;
  late Animation<double> _pulseAnimation;

  final List<String> _fixedSubsystems = [
    'Turbine',
    'Boiler',
    'Generator',
    'Condenser',
    'Feed Water',
    'BFP'
  ];

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
    final subsystemsAsync = ref.watch(subsystemsProvider);
    final activeAlertsAsync = ref.watch(activeAlertsProvider);
    final selectedSensors = ref.watch(selectedSensorsProvider);
    final sensorsMap = ref.watch(sensorsMapProvider).value ?? {};
    
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

    return Scaffold(
      appBar: AppBar(
        title: const Text('BHEL Unit 5 — Live Monitoring', style: TextStyle(fontSize: 18)),
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
                child: Text('COMPARE (${selectedSensors.length}) · $selectedSubsystemsCount subs'),
              ),
            ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16.0),
            child: Center(
              child: Container(
                width: 12,
                height: 12,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: subsystemsAsync.hasValue ? Colors.greenAccent : Colors.redAccent,
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
          Expanded(
            child: GridView.builder(
              padding: const EdgeInsets.all(16),
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 2,
                crossAxisSpacing: 16,
                mainAxisSpacing: 16,
                childAspectRatio: 0.85,
              ),
              itemCount: _fixedSubsystems.length,
              itemBuilder: (context, index) {
                final subName = _fixedSubsystems[index];
                final status = subsystems[subName];
                return _buildSubsystemCard(context, subName, status);
              },
            ),
          ),
          _buildAlertsBanner(context, alertCount),
        ],
      ),
    );
  }

  Widget _buildSubsystemCard(BuildContext context, String subName, SubsystemStatus? status) {
    Color borderColor = Colors.greenAccent.withOpacity(0.3);
    String worst = 'normal';
    
    if (status != null) {
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
          borderColor = Colors.greenAccent.withOpacity(0.5);
      }
    } else {
      borderColor = Colors.grey.withOpacity(0.2); // No data yet
    }

    Widget cardContent = Container(
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: borderColor, width: worst == 'critical' ? 3 : 2),
        boxShadow: worst == 'normal' || status == null ? [] : [
          BoxShadow(
            color: borderColor.withOpacity(0.3),
            blurRadius: 8,
            spreadRadius: 2,
          )
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
                worst == 'fault' ? Icons.sensors_off : Icons.dashboard_customize_outlined, 
                color: worst == 'fault' ? Colors.grey : Colors.grey[400], 
                size: 32
              ),
              if (worst == 'fault')
                const Icon(Icons.close, color: Colors.grey),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            subName,
            style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
          const Spacer(),
          Text(
            status != null ? '${status.totalSensors} Sensors' : 'Waiting for data...', 
            style: TextStyle(color: Colors.grey[400], fontSize: 12)
          ),
          const SizedBox(height: 8),
          if (status != null)
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                _buildStatusChip(status.normalCount, Colors.greenAccent),
                _buildStatusChip(status.warningCount, Colors.orangeAccent),
                _buildStatusChip(status.criticalCount, Colors.redAccent),
                if (status.faultCount > 0 || status.missingCount > 0)
                  _buildStatusChip(status.faultCount + status.missingCount, Colors.grey),
              ],
            )
        ],
      ),
    );

    if (worst == 'critical') {
      cardContent = AnimatedBuilder(
        animation: _pulseAnimation,
        builder: (context, child) {
          return Opacity(
            opacity: _pulseAnimation.value,
            child: child,
          );
        },
        child: cardContent,
      );
    }

    return InkWell(
      onTap: () {
        context.push('/subsystem/$subName');
      },
      child: cardContent,
    );
  }

  Widget _buildStatusChip(int count, Color color) {
    if (count == 0) return const SizedBox.shrink();
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
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
      onTap: () => context.push('/alerts'),
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
