import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config.dart';
import '../models/models.dart';

class ApiService {
  Future<Map<String, SensorReading>> fetchCurrentSensors() async {
    try {
      final response = await http.get(Uri.parse('${Config.baseUrl}/data/sensors/current'));
      if (response.statusCode == 200) {
        final dynamic decoded = jsonDecode(response.body);
        final Map<String, SensorReading> result = {};
        
        if (decoded is List) {
          for (var item in decoded) {
            if (item is Map<String, dynamic>) {
              final reading = SensorReading.fromJson(item);
              result[reading.id] = reading;
            }
          }
        } else if (decoded is Map<String, dynamic>) {
          decoded.forEach((key, value) {
            if (value is Map<String, dynamic>) {
              result[key] = SensorReading.fromJson(value);
            }
          });
        }
        
        return result;
      } else {
        throw Exception('Failed to fetch current sensors: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Network error: $e');
    }
  }

  Future<List<Map<String, dynamic>>> fetchSensorHistory(String sensorId, {int minutes = 10}) async {
    try {
      final response = await http.get(
        Uri.parse('${Config.baseUrl}/data/sensors/$sensorId/history?minutes=$minutes'),
      );
      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body);
        return List<Map<String, dynamic>>.from(data);
      } else {
        throw Exception('Failed to fetch sensor history: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Network error: $e');
    }
  }

  Future<List<Alert>> fetchActiveAlerts() async {
    try {
      final response = await http.get(Uri.parse('${Config.baseUrl}/api/v1/alerts/active'));
      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body);
        return data.map((item) => Alert.fromJson(item)).toList();
      } else {
        throw Exception('Failed to fetch active alerts: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Network error: $e');
    }
  }

  Future<bool> acknowledgeAlert(String alertId) async {
    try {
      final response = await http.post(Uri.parse('${Config.baseUrl}/api/v1/alerts/$alertId/acknowledge'));
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return data['status'] == 'success';
      }
      return false;
    } catch (e) {
      return false;
    }
  }
}

final apiService = ApiService();
