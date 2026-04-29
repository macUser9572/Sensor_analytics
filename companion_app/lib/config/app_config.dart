import 'package:shared_preferences/shared_preferences.dart';

class AppConfig {
  static late SharedPreferences _prefs;

  static Future<void> init() async {
    _prefs = await SharedPreferences.getInstance();
  }

  static String get apiBase => _prefs.getString('api_base_url') ?? 'http://192.168.1.102:8000';
  static String get wsBase => _prefs.getString('ws_base_url') ?? 'ws://192.168.1.102:8000';

  static Future<void> setApiBase(String url) async {
    await _prefs.setString('api_base_url', url);
  }

  static Future<void> setWsBase(String url) async {
    await _prefs.setString('ws_base_url', url);
  }
}
