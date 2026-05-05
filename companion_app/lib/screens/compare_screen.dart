import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:go_router/go_router.dart';
import '../providers/providers.dart';
import '../models/models.dart';
import '../services/api_service.dart';

class CompareScreen extends ConsumerStatefulWidget {
  const CompareScreen({super.key});

  @override
  ConsumerState<CompareScreen> createState() => _CompareScreenState();
}

class _CompareScreenState extends ConsumerState<CompareScreen> {
  int _minutes = 60;
  bool _isLoading = true;
  String? _error;

  // sensorId -> list of spots (x = ms since epoch as double)
  Map<String, List<FlSpot>> _chartData = {};
  // last streamed value per sensor for dedup
  final Map<String, double> _lastStreamedValues = {};
  // current display value per sensor (updated by live stream)
  Map<String, double> _currentValues = {};

  final List<Color> _palette = [
    Colors.blueAccent,
    Colors.pinkAccent,
    Colors.greenAccent,
    Colors.orangeAccent,
    Colors.purpleAccent,
    Colors.cyanAccent,
  ];

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _fetchData();
    });
  }

  Future<void> _fetchData() async {
    setState(() {
      _isLoading = true;
      _error = null;
      _lastStreamedValues.clear();
    });

    final selectedIds = ref.read(selectedSensorsProvider);
    if (selectedIds.isEmpty) {
      setState(() {
        _isLoading = false;
        _chartData = {};
      });
      return;
    }

    try {
      final data = await apiService.fetchSensorCompare(selectedIds, minutes: _minutes);

      final Map<String, List<FlSpot>> newChartData = {};
      final Map<String, double> newCurrentValues = {};

      data.forEach((sensorId, history) {
        final spots = <FlSpot>[];
        double lastVal = 0;

        for (final entry in history) {
          final val = (entry['value'] as num).toDouble();
          final rawTime = entry['time'] ?? entry['timestamp'];
          final ts = rawTime != null
              ? DateTime.parse(rawTime as String).millisecondsSinceEpoch.toDouble()
              : DateTime.now().millisecondsSinceEpoch.toDouble();
          spots.add(FlSpot(ts, val));
          lastVal = val;
        }

        newChartData[sensorId] = spots;
        newCurrentValues[sensorId] = lastVal;
      });

      if (mounted) {
        setState(() {
          _chartData = newChartData;
          _currentValues = newCurrentValues;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = e.toString();
          _isLoading = false;
        });
      }
    }
  }

  void _clearSelection() {
    ref.read(selectedSensorsProvider.notifier).clearSelection();
    context.go('/');
  }

  @override
  Widget build(BuildContext context) {
    final selectedIds = ref.watch(selectedSensorsProvider);
    final sensorsMap = ref.watch(sensorsMapProvider).value ?? {};

    // Stream live ticks into chart data
    ref.listen<AsyncValue<Map<String, SensorReading>>>(sensorsMapProvider, (prev, next) {
      if (!next.hasValue || _isLoading) return;
      final map = next.value!;
      final cutoffMs = DateTime.now().millisecondsSinceEpoch - _minutes * 60 * 1000;
      bool changed = false;

      for (final id in selectedIds) {
        final reading = map[id];
        if (reading == null) continue;
        final val = reading.value;
        if (val == _lastStreamedValues[id]) continue;
        _lastStreamedValues[id] = val;

        final ts = reading.timestamp.millisecondsSinceEpoch.toDouble();
        final spots = _chartData[id] ?? [];
        spots.add(FlSpot(ts, val));

        // Trim points outside the time window
        spots.removeWhere((s) => s.x < cutoffMs);

        _chartData[id] = spots;
        _currentValues[id] = val;
        changed = true;
      }

      if (changed && mounted) setState(() {});
    });

    return Scaffold(
      appBar: AppBar(
        title: const Text('Compare Sensors'),
        actions: [
          TextButton(
            onPressed: _clearSelection,
            child: const Text('Clear Selection', style: TextStyle(color: Colors.redAccent)),
          )
        ],
      ),
      body: selectedIds.isEmpty
          ? const Center(child: Text("No sensors selected for comparison."))
          : Column(
              children: [
                _buildTimeFilters(),
                Expanded(
                  child: _isLoading
                      ? const Center(child: CircularProgressIndicator())
                      : _error != null
                          ? Center(child: Text("Error: $_error"))
                          : Padding(
                              padding: const EdgeInsets.all(24.0),
                              child: _buildChart(selectedIds, sensorsMap),
                            ),
                ),
                if (!_isLoading && _error == null)
                  _buildLegend(selectedIds, sensorsMap),
              ],
            ),
    );
  }

  Widget _buildTimeFilters() {
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          _timeButton('15m', 15),
          const SizedBox(width: 16),
          _timeButton('1h', 60),
          const SizedBox(width: 16),
          _timeButton('6h', 360),
        ],
      ),
    );
  }

  Widget _timeButton(String label, int minutes) {
    final isSelected = _minutes == minutes;
    return ChoiceChip(
      label: Text(label),
      selected: isSelected,
      onSelected: (selected) {
        if (selected && !isSelected) {
          setState(() => _minutes = minutes);
          _fetchData();
        }
      },
    );
  }

  Widget _buildChart(List<String> selectedIds, Map<String, SensorReading> sensorsMap) {
    if (_chartData.isEmpty) return const Center(child: Text("No data"));

    final lineBars = <LineChartBarData>[];
    double globalMinY = double.maxFinite;
    double globalMaxY = double.minPositive;
    double minX = double.maxFinite;
    double maxX = double.minPositive;

    int colorIndex = 0;

    final Set<String> units = {};
    for (final id in selectedIds) {
      if (sensorsMap.containsKey(id)) units.add(sensorsMap[id]!.unit);
    }
    final isDualAxis = units.length > 1;

    for (final id in selectedIds) {
      final spots = _chartData[id];
      if (spots == null || spots.isEmpty) continue;

      final color = _palette[colorIndex % _palette.length];

      for (final spot in spots) {
        if (spot.y < globalMinY) globalMinY = spot.y;
        if (spot.y > globalMaxY) globalMaxY = spot.y;
        if (spot.x < minX) minX = spot.x;
        if (spot.x > maxX) maxX = spot.x;
      }

      lineBars.add(
        LineChartBarData(
          spots: spots,
          isCurved: false,
          color: color,
          barWidth: 1.5,
          isStrokeCapRound: true,
          dotData: FlDotData(
            show: true,
            getDotPainter: (spot, percent, barData, index) => FlDotCirclePainter(
              radius: 2.0,
              color: barData.color ?? Colors.white,
              strokeWidth: 0,
              strokeColor: Colors.transparent,
            ),
          ),
        ),
      );
      colorIndex++;
    }

    if (globalMinY == double.maxFinite) return const SizedBox.shrink();

    double range = globalMaxY - globalMinY;
    if (range == 0) range = 1;

    return LineChart(
      LineChartData(
        gridData: FlGridData(
          show: true,
          drawVerticalLine: false,
          getDrawingHorizontalLine: (value) => FlLine(
            color: Colors.grey.withOpacity(0.2),
            strokeWidth: 1,
          ),
        ),
        titlesData: FlTitlesData(
          bottomTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              reservedSize: 28,
              interval: (maxX - minX) / 4,
              getTitlesWidget: (val, meta) {
                final dt = DateTime.fromMillisecondsSinceEpoch(val.toInt());
                return Text(
                  '${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}',
                  style: const TextStyle(fontSize: 9, color: Colors.grey),
                );
              },
            ),
          ),
          topTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
          leftTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              reservedSize: 40,
              getTitlesWidget: (val, meta) => Text(
                val.toStringAsFixed(0),
                style: const TextStyle(fontSize: 10, color: Colors.grey),
              ),
            ),
          ),
          rightTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: isDualAxis,
              reservedSize: 40,
              getTitlesWidget: (val, meta) => Text(
                val.toStringAsFixed(0),
                style: const TextStyle(fontSize: 10, color: Colors.grey),
              ),
            ),
          ),
        ),
        borderData: FlBorderData(show: false),
        minY: globalMinY - (range * 0.1),
        maxY: globalMaxY + (range * 0.1),
        minX: minX,
        maxX: maxX,
        lineBarsData: lineBars,
      ),
    );
  }

  Widget _buildLegend(List<String> selectedIds, Map<String, SensorReading> sensorsMap) {
    return Container(
      padding: const EdgeInsets.all(16),
      color: Theme.of(context).cardColor,
      child: SafeArea(
        top: false,
        child: Wrap(
          spacing: 16,
          runSpacing: 8,
          alignment: WrapAlignment.center,
          children: List.generate(selectedIds.length, (index) {
            final id = selectedIds[index];
            final sensor = sensorsMap[id];
            final name = sensor?.metric ?? id;
            final val = _currentValues[id] ?? 0.0;
            final unit = sensor?.unit ?? '';
            final color = _palette[index % _palette.length];

            return Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  width: 12,
                  height: 12,
                  decoration: BoxDecoration(shape: BoxShape.circle, color: color),
                ),
                const SizedBox(width: 8),
                Text(
                  '$name: ${val.toStringAsFixed(1)} $unit',
                  style: const TextStyle(fontWeight: FontWeight.bold),
                ),
              ],
            );
          }),
        ),
      ),
    );
  }
}
