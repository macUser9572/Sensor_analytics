import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:go_router/go_router.dart';
import '../providers/providers.dart';
import '../models/models.dart';
import '../services/api_service.dart';

class SubsystemScreen extends ConsumerWidget {
  final String subsystem;

  const SubsystemScreen({super.key, required this.subsystem});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final sensorsAsync = ref.watch(currentSensorsProvider(subsystem));
    final selectedSensors = ref.watch(selectedSensorsProvider);

    return Scaffold(
      appBar: AppBar(
        title: Text(subsystem),
        actions: [
          if (selectedSensors.isNotEmpty)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 8.0),
              child: ElevatedButton(
                onPressed: () => context.push('/compare'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Theme.of(context).colorScheme.secondary,
                  foregroundColor: Colors.white,
                ),
                child: Text('COMPARE (${selectedSensors.length})'),
              ),
            ),
        ],
      ),
      body: sensorsAsync.when(
        data: (sensors) {
          if (sensors.isEmpty) {
            return const Center(child: Text("No sensors found."));
          }
          return ListView.builder(
            itemCount: sensors.length,
            itemBuilder: (context, index) {
              final sensor = sensors[index];
              final isSelected = selectedSensors.contains(sensor.id);
              return _buildSensorRow(context, ref, sensor, isSelected);
            },
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) => Center(child: Text('Error: $err')),
      ),
    );
  }

  Widget _buildSensorRow(BuildContext context, WidgetRef ref, SensorReading sensor, bool isSelected) {
    Color statusColor;
    switch (sensor.healthState) {
      case SensorHealthState.fault:
        statusColor = Colors.grey;
        break;
      case SensorHealthState.stale:
        statusColor = Colors.orangeAccent;
        break;
      case SensorHealthState.uncertain:
        statusColor = Colors.yellow;
        break;
      case SensorHealthState.live:
      default:
        statusColor = Colors.greenAccent;
    }

    // Override with status if critical/warning
    if (sensor.status == 'critical') {
      statusColor = Colors.redAccent;
    } else if (sensor.status == 'warning' && statusColor == Colors.greenAccent) {
      statusColor = Colors.orangeAccent;
    } else if (sensor.status == 'fault' || sensor.status == 'missing') {
      statusColor = Colors.grey;
    }

    final duration = DateTime.now().difference(sensor.timestamp);
    String timeAgo;
    if (duration.inSeconds < 60) {
      timeAgo = '${duration.inSeconds}s ago';
    } else if (duration.inMinutes < 60) {
      timeAgo = '${duration.inMinutes}m ago';
    } else {
      timeAgo = '${duration.inHours}h ago';
    }

    return ListTile(
      leading: Checkbox(
        value: isSelected,
        onChanged: (val) {
          ref.read(selectedSensorsProvider.notifier).toggleSelection(sensor.id);
        },
      ),
      title: Row(
        children: [
          Container(
            width: 10,
            height: 10,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: statusColor,
            ),
          ),
          const SizedBox(width: 8),
          Expanded(child: Text(sensor.metric.toUpperCase())),
        ],
      ),
      subtitle: Text('ID: ${sensor.id} • Last seen: $timeAgo'),
      trailing: Text(
        '${sensor.value.toStringAsFixed(2)} ${sensor.unit}',
        style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
      ),
      onTap: () {
        _showSparklineBottomSheet(context, sensor);
      },
    );
  }

  void _showSparklineBottomSheet(BuildContext context, SensorReading sensor) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: const Color(0xFF1E1E2E), // Dark theme modal
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) {
        return _SensorBottomSheet(sensor: sensor);
      },
    );
  }
}

class _SensorBottomSheet extends ConsumerStatefulWidget {
  final SensorReading sensor;
  const _SensorBottomSheet({required this.sensor});

  @override
  ConsumerState<_SensorBottomSheet> createState() => _SensorBottomSheetState();
}

class _SensorBottomSheetState extends ConsumerState<_SensorBottomSheet> {
  bool _isLoading = true;
  String? _error;
  List<FlSpot> _spots = [];
  double _currentValue = 0.0;
  double _lastStreamedValue = double.nan;

  static const int _historyMinutes = 60;

  double _minVal = double.maxFinite;
  double _maxVal = double.minPositive;
  double _sumVal = 0.0;
  int _totalCount = 0;

  @override
  void initState() {
    super.initState();
    _currentValue = widget.sensor.value;
    _loadHistory();
  }

  Future<void> _loadHistory() async {
    try {
      final history = await apiService.fetchSensorHistory(widget.sensor.id, minutes: _historyMinutes);

      final newSpots = <FlSpot>[];
      for (final entry in history) {
        final double val = (entry['value'] as num).toDouble();
        final rawTime = entry['time'] ?? entry['timestamp'];
        final ts = rawTime != null
            ? DateTime.parse(rawTime as String).millisecondsSinceEpoch.toDouble()
            : DateTime.now().millisecondsSinceEpoch.toDouble();
        _updateStats(val);
        newSpots.add(FlSpot(ts, val));
      }

      setState(() {
        _spots = newSpots;
        _isLoading = false;
      });
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = e.toString();
          _isLoading = false;
        });
      }
    }
  }

  void _updateStats(double val) {
    if (val < _minVal) _minVal = val;
    if (val > _maxVal) _maxVal = val;
    _sumVal += val;
    _totalCount++;
  }

  @override
  Widget build(BuildContext context) {
    ref.listen<AsyncValue<List<SensorReading>>>(currentSensorsProvider(widget.sensor.subsystem), (prev, next) {
      if (next.hasValue && next.value != null && !_isLoading) {
        try {
          final updatedSensor = next.value!.firstWhere((s) => s.id == widget.sensor.id);
          final val = updatedSensor.value;
          if (val == _lastStreamedValue) return;
          final cutoffMs = DateTime.now().millisecondsSinceEpoch - _historyMinutes * 60 * 1000;
          final ts = updatedSensor.timestamp.millisecondsSinceEpoch.toDouble();
          setState(() {
            _lastStreamedValue = val;
            _currentValue = val;
            _updateStats(val);
            _spots.add(FlSpot(ts, val));
            _spots.removeWhere((s) => s.x < cutoffMs);
          });
        } catch (_) {}
      }
    });

    return Padding(
      padding: const EdgeInsets.all(24.0),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                widget.sensor.metric.toUpperCase(),
                style: const TextStyle(fontSize: 20, color: Colors.grey),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: widget.sensor.status == 'normal' 
                      ? Colors.green.withOpacity(0.2) 
                      : widget.sensor.status == 'warning' 
                          ? Colors.orange.withOpacity(0.2) 
                          : Colors.red.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                    color: widget.sensor.status == 'normal' 
                        ? Colors.green 
                        : widget.sensor.status == 'warning' 
                            ? Colors.orange 
                            : Colors.red,
                  )
                ),
                child: Text(
                  widget.sensor.status.toUpperCase(),
                  style: TextStyle(
                    color: widget.sensor.status == 'normal' 
                        ? Colors.greenAccent 
                        : widget.sensor.status == 'warning' 
                            ? Colors.orangeAccent 
                            : Colors.redAccent,
                    fontSize: 12,
                    fontWeight: FontWeight.bold
                  ),
                ),
              )
            ],
          ),
          const SizedBox(height: 8),
          Text(
            '${_currentValue.toStringAsFixed(2)} ${widget.sensor.unit}',
            style: const TextStyle(fontSize: 36, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 24),
          SizedBox(
            height: 200,
            child: _isLoading 
              ? const Center(child: CircularProgressIndicator())
              : _error != null 
                ? Center(child: Text("Error: $_error"))
                : _spots.isEmpty 
                  ? const Center(child: Text("No history data available."))
                  : _buildChart(),
          ),
        ],
      ),
    );
  }

  Widget _buildChart() {
    double range = _maxVal - _minVal;
    if (range == 0) range = 1;

    return Column(
      children: [
        Expanded(
          child: LineChart(
            LineChartData(
              gridData: FlGridData(show: false),
              titlesData: FlTitlesData(show: false),
              borderData: FlBorderData(show: false),
              minY: _minVal - (range * 0.1),
              maxY: _maxVal + (range * 0.1),
              minX: _spots.first.x,
              maxX: _spots.last.x,
              lineBarsData: [
                LineChartBarData(
                  spots: _spots,
                  isCurved: false,
                  color: Colors.blueAccent,
                  barWidth: 2,
                  isStrokeCapRound: true,
                  dotData: FlDotData(
                    show: true,
                    getDotPainter: (spot, percent, barData, index) => FlDotCirclePainter(
                      radius: 2.0,
                      color: Colors.blueAccent,
                      strokeWidth: 0,
                      strokeColor: Colors.transparent,
                    ),
                  ),
                  belowBarData: BarAreaData(
                    show: true,
                    color: Colors.blueAccent.withOpacity(0.2),
                  ),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 16),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
          children: [
            _buildStatLabel('Min', _minVal),
            _buildStatLabel('Max', _maxVal),
            _buildStatLabel('Mean', _totalCount > 0 ? _sumVal / _totalCount : 0),
          ],
        )
      ],
    );
  }

  Widget _buildStatLabel(String label, double value) {
    return Column(
      children: [
        Text(label, style: const TextStyle(color: Colors.grey, fontSize: 12)),
        const SizedBox(height: 4),
        Text(value.toStringAsFixed(2), style: const TextStyle(fontWeight: FontWeight.bold)),
      ],
    );
  }
}
