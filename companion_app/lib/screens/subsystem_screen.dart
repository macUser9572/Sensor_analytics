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

class _SensorBottomSheet extends StatefulWidget {
  final SensorReading sensor;
  const _SensorBottomSheet({required this.sensor});

  @override
  State<_SensorBottomSheet> createState() => _SensorBottomSheetState();
}

class _SensorBottomSheetState extends State<_SensorBottomSheet> {
  late Future<List<Map<String, dynamic>>> _historyFuture;

  @override
  void initState() {
    super.initState();
    _historyFuture = apiService.fetchSensorHistory(widget.sensor.id, minutes: 10);
  }

  @override
  Widget build(BuildContext context) {
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
            '${widget.sensor.value.toStringAsFixed(2)} ${widget.sensor.unit}',
            style: const TextStyle(fontSize: 36, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 24),
          SizedBox(
            height: 200,
            child: FutureBuilder<List<Map<String, dynamic>>>(
              future: _historyFuture,
              builder: (context, snapshot) {
                if (snapshot.connectionState == ConnectionState.waiting) {
                  return const Center(child: CircularProgressIndicator());
                } else if (snapshot.hasError) {
                  return Center(child: Text("Error fetching history: ${snapshot.error}"));
                } else if (!snapshot.hasData || snapshot.data!.isEmpty) {
                  return const Center(child: Text("No history data available."));
                }

                // Data mapping for FLChart
                final history = snapshot.data!;
                double minVal = double.maxFinite;
                double maxVal = double.minPositive;
                double sumVal = 0.0;
                
                final spots = <FlSpot>[];
                
                for (int i = 0; i < history.length; i++) {
                  final double val = (history[i]['value'] as num).toDouble();
                  if (val < minVal) minVal = val;
                  if (val > maxVal) maxVal = val;
                  sumVal += val;
                  spots.add(FlSpot(i.toDouble(), val));
                }
                
                // Adjusting axes bounds slightly for padding
                double range = maxVal - minVal;
                if (range == 0) range = 1;
                
                return Column(
                  children: [
                    Expanded(
                      child: LineChart(
                        LineChartData(
                          gridData: FlGridData(show: false),
                          titlesData: FlTitlesData(show: false),
                          borderData: FlBorderData(show: false),
                          minY: minVal - (range * 0.1),
                          maxY: maxVal + (range * 0.1),
                          lineBarsData: [
                            LineChartBarData(
                              spots: spots,
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
                        _buildStatLabel('Min', minVal),
                        _buildStatLabel('Max', maxVal),
                        _buildStatLabel('Mean', sumVal / history.length),
                      ],
                    )
                  ],
                );
              },
            ),
          ),
        ],
      ),
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
