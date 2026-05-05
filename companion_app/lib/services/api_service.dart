import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config/app_config.dart';
import '../models/models.dart';

// Default timeout for all API calls — avoids the 60-second OS ETIMEDOUT hang
const _kTimeout = Duration(seconds: 10);

class ApiService {
  Future<bool> testConnection() async {
    try {
      final response = await http
          .get(Uri.parse('${AppConfig.apiBase}/health'))
          .timeout(const Duration(seconds: 5));
      if (response.statusCode == 200) {
        final decoded = jsonDecode(response.body);
        return decoded['status'] == 'ok' || decoded['status'] == 'degraded';
      }
      return false;
    } catch (_) {
      return false;
    }
  }

  Future<Map<String, SensorReading>> fetchCurrentSensors() async {
    try {
      final response = await http
          .get(Uri.parse('${AppConfig.apiBase}/data/sensors/current'))
          .timeout(_kTimeout);
      if (response.statusCode == 200) {
        final dynamic decoded = jsonDecode(response.body);
        final Map<String, SensorReading> result = {};

        if (decoded is List) {
          for (final item in decoded) {
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
        throw Exception('Server returned ${response.statusCode}');
      }
    } on Exception {
      rethrow;
    } catch (e) {
      throw Exception('Network error: $e');
    }
  }

  Future<List<Map<String, dynamic>>> fetchSensorHistory(
      String sensorId, {int minutes = 10}) async {
    try {
      final response = await http
          .get(Uri.parse(
              '${AppConfig.apiBase}/data/sensors/$sensorId/history?minutes=$minutes'))
          .timeout(_kTimeout);
      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body);
        return List<Map<String, dynamic>>.from(data);
      } else {
        throw Exception('Server returned ${response.statusCode}');
      }
    } on Exception {
      rethrow;
    } catch (e) {
      throw Exception('Network error: $e');
    }
  }

  Future<Map<String, List<Map<String, dynamic>>>> fetchSensorCompare(
      List<String> ids, {int minutes = 60}) async {
    try {
      final idsParam = ids.join(',');
      final response = await http
          .get(Uri.parse(
              '${AppConfig.apiBase}/data/sensors/compare?ids=$idsParam&minutes=$minutes'))
          .timeout(_kTimeout);
      if (response.statusCode == 200) {
        final Map<String, dynamic> data = jsonDecode(response.body);
        final Map<String, List<Map<String, dynamic>>> result = {};
        data.forEach((key, value) {
          if (value is List) {
            result[key] = List<Map<String, dynamic>>.from(value);
          }
        });
        return result;
      } else {
        throw Exception('Server returned ${response.statusCode}');
      }
    } on Exception {
      rethrow;
    } catch (e) {
      throw Exception('Network error: $e');
    }
  }

  Future<List<Alert>> fetchActiveAlerts() async {
    try {
      final response = await http
          .get(Uri.parse('${AppConfig.apiBase}/api/v1/alerts/active'))
          .timeout(_kTimeout);
      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body);
        return data.map((item) => Alert.fromJson(item)).toList();
      } else {
        throw Exception('Server returned ${response.statusCode}');
      }
    } on Exception {
      rethrow;
    } catch (e) {
      throw Exception('Network error: $e');
    }
  }

  Future<bool> acknowledgeAlert(String alertId) async {
    try {
      final response = await http
          .post(Uri.parse(
              '${AppConfig.apiBase}/api/v1/alerts/$alertId/acknowledge'))
          .timeout(_kTimeout);
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return data['status'] == 'success';
      }
      return false;
    } catch (_) {
      return false;
    }
  }
}

final apiService = ApiService();
