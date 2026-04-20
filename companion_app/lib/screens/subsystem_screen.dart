import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fl_chart/fl_chart.dart';
import '../providers/providers.dart';
import '../models/models.dart';
import '../services/api_service.dart';

class SubsystemScreen extends ConsumerWidget {
  final String subsystem;

  const SubsystemScreen({super.key, required this.subsystem});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Watch the future provider for sensors. (Ideally we'd merge WS updates in here).
    final sensorsAsync = ref.watch(currentSensorsProvider(subsystem));

    return Scaffold(
      appBar: AppBar(
        title: Text(subsystem),
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
              return _buildSensorRow(context, sensor);
            },
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) => Center(child: Text('Error: $err')),
      ),
    );
  }

  Widget _buildSensorRow(BuildContext context, SensorReading sensor) {
    Color statusColor;
    switch (sensor.status) {
      case 'critical':
        statusColor = Colors.redAccent;
        break;
      case 'warning':
        statusColor = Colors.orangeAccent;
        break;
      default:
        statusColor = Colors.greenAccent;
    }

    return ListTile(
      title: Text(sensor.metric.toUpperCase()),
      subtitle: Text('ID: ${sensor.id}'),
      trailing: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            '${sensor.value.toStringAsFixed(2)} ${sensor.unit}',
            style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
          ),
          const SizedBox(width: 12),
          Container(
            width: 12,
            height: 12,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: statusColor,
            ),
          )
        ],
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
  int _tick = 0;

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
      final history = await apiService.fetchSensorHistory(widget.sensor.id, minutes: 10);
      
      final newSpots = <FlSpot>[];
      for (int i = 0; i < history.length; i++) {
        final double val = (history[i]['value'] as num).toDouble();
        _updateStats(val);
        newSpots.add(FlSpot(_tick.toDouble(), val));
        _tick++;
      }
      
      // If history is too long, trim it to recent 60 to mimic web app's 60s moving window
      if (newSpots.length > 60) {
        newSpots.removeRange(0, newSpots.length - 60);
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
    // Listen to real-time updates and move the plot
    ref.listen<AsyncValue<List<SensorReading>>>(currentSensorsProvider(widget.sensor.subsystem), (prev, next) {
      if (next.hasValue && next.value != null && !_isLoading) {
        try {
          final updatedSensor = next.value!.firstWhere((s) => s.id == widget.sensor.id);
          // Update the spots when a new tick is received
          setState(() {
            _currentValue = updatedSensor.value;
            _updateStats(_currentValue);
            _spots.add(FlSpot(_tick.toDouble(), _currentValue));
            _tick++;
            
            // Sliding window of 60 items
            if (_spots.length > 60) {
              _spots.removeAt(0);
            }
          });
        } catch (_) {
          // Sensor not updated in this tick
        }
      }
    });

    return Padding(
      padding: const EdgeInsets.all(24.0),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            widget.sensor.metric.toUpperCase(),
            style: const TextStyle(fontSize: 20, color: Colors.grey),
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
                  isCurved: true,
                  color: Colors.blueAccent,
                  barWidth: 3,
                  isStrokeCapRound: true,
                  dotData: FlDotData(show: false),
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

