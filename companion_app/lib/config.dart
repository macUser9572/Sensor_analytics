class Config {
  // Use 10.0.2.2 for Android emulator default localhost mapping.
  // Use 127.0.0.1 for iOS / Web / Desktop.
  // For the moment we will default to 127.0.0.1 as per standard.
  static const String host = '127.0.0.1';
  static const String port = '8000'; // Assuming FastAPI default port is 8000
  
  static const String baseUrl = 'http://$host:$port';
  static const String wsBaseUrl = 'ws://$host:$port';
}
