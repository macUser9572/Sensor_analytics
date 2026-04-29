class Config {
  static const String baseUrl = String.fromEnvironment('FLUTTER_API_BASE_URL');
  static const String wsBaseUrl = String.fromEnvironment('FLUTTER_WS_URL');

  static void validate() {
    if (baseUrl.isEmpty || wsBaseUrl.isEmpty) {
      throw StateError(
        'FLUTTER_API_BASE_URL and FLUTTER_WS_URL must be provided with --dart-define.',
      );
    }
  }
}
