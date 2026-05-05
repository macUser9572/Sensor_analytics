import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../config/app_config.dart';
import '../services/api_service.dart';
import '../services/websocket_service.dart';
import '../providers/providers.dart';

class SettingsScreen extends ConsumerStatefulWidget {
  const SettingsScreen({super.key});

  @override
  ConsumerState<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends ConsumerState<SettingsScreen> {
  late TextEditingController _apiController;
  late TextEditingController _wsController;
  bool _isTesting = false;

  @override
  void initState() {
    super.initState();
    _apiController = TextEditingController(text: AppConfig.apiBase);
    _wsController  = TextEditingController(text: AppConfig.wsBase);
  }

  @override
  void dispose() {
    _apiController.dispose();
    _wsController.dispose();
    super.dispose();
  }

  Future<void> _testConnection() async {
    setState(() => _isTesting = true);

    final originalApi = AppConfig.apiBase;
    await AppConfig.setApiBase(_apiController.text);

    final success = await apiService.testConnection();

    if (!success) {
      await AppConfig.setApiBase(originalApi);
    }

    setState(() => _isTesting = false);

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(success ? 'Connection OK ✓' : 'Connection Failed — check the IP and make sure the server is running'),
          backgroundColor: success ? Colors.green[800] : Colors.red[800],
          duration: Duration(seconds: success ? 2 : 4),
        ),
      );
    }
  }

  Future<void> _saveSettings() async {
    await AppConfig.setApiBase(_apiController.text);
    await AppConfig.setWsBase(_wsController.text);

    // Reconnect WebSocket with new URL
    webSocketService.reconnect();

    // Trigger a fresh data fetch now that the IP is configured
    ref.read(sensorsMapProvider.notifier).fetchInitialSensors();
    ref.read(activeAlertsProvider.notifier).fetchInitialAlerts();

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: const Text('Settings saved — connecting…'),
          backgroundColor: Colors.blue[800],
        ),
      );
      Navigator.pop(context);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Backend API URL',
                style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 4),
            const Text(
              'Use your server\'s local IP (e.g. http://192.168.1.X:8000).\nFor iOS simulator use http://127.0.0.1:8000.',
              style: TextStyle(fontSize: 12, color: Colors.grey),
            ),
            const SizedBox(height: 8),
            TextField(
              controller: _apiController,
              keyboardType: TextInputType.url,
              autocorrect: false,
              decoration: const InputDecoration(
                border: OutlineInputBorder(),
                hintText: 'http://192.168.1.X:8000',
              ),
            ),
            const SizedBox(height: 24),
            const Text('WebSocket URL',
                style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 4),
            const Text(
              'Same host as above, but with ws:// instead of http://',
              style: TextStyle(fontSize: 12, color: Colors.grey),
            ),
            const SizedBox(height: 8),
            TextField(
              controller: _wsController,
              keyboardType: TextInputType.url,
              autocorrect: false,
              decoration: const InputDecoration(
                border: OutlineInputBorder(),
                hintText: 'ws://192.168.1.X:8000',
              ),
            ),
            const SizedBox(height: 32),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                ElevatedButton.icon(
                  onPressed: _isTesting ? null : _testConnection,
                  icon: _isTesting
                      ? const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2))
                      : const Icon(Icons.network_check),
                  label: const Text('Test Connection'),
                  style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.grey[800]),
                ),
                ElevatedButton.icon(
                  onPressed: _saveSettings,
                  icon: const Icon(Icons.save),
                  label: const Text('Save'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.blueAccent,
                    foregroundColor: Colors.white,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
