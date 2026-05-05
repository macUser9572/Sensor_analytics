import 'package:shared_preferences/shared_preferences.dart';

const _kDefaultApiBase = 'http://192.168.1.102:8000';
const _kDefaultWsBase  = 'ws://192.168.1.102:8000';

class AppConfig {
  static late SharedPreferences _prefs;

  static Future<void> init() async {
    _prefs = await SharedPreferences.getInstance();
  }

  static String get apiBase => _prefs.getString('api_base_url') ?? _kDefaultApiBase;
  static String get wsBase  => _prefs.getString('ws_base_url')  ?? _kDefaultWsBase;

  /// True when the user has never configured a server IP.
  /// All network calls should be skipped while this is true.
  static bool get isUnconfigured =>
      apiBase == _kDefaultApiBase || wsBase == _kDefaultWsBase;

  static Future<void> setApiBase(String url) async {
    await _prefs.setString('api_base_url', url);
  }

  static Future<void> setWsBase(String url) async {
    await _prefs.setString('ws_base_url', url);
  }
}
