import 'package:companion_app/models/models.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'screens/overview_screen.dart';
import 'services/notification_service.dart';
import 'services/websocket_service.dart';
import 'providers/providers.dart';
import 'config.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  Config.validate();
  await notificationService.init();

  // Begin WebSocket connections
  webSocketService.connectLive();
  webSocketService.connectAlerts();

  runApp(
    const ProviderScope(
      child: CompanionApp(),
    ),
  );
}

class CompanionApp extends ConsumerStatefulWidget {
  const CompanionApp({super.key});

  @override
  ConsumerState<CompanionApp> createState() => _CompanionAppState();
}

class _CompanionAppState extends ConsumerState<CompanionApp> {
  @override
  void initState() {
    super.initState();
    // Start listening to the alert event stream to show notifications globally
    ref.read(alertsStreamProvider.stream).listen((event) {
      if (event.type == AlertEventType.fired && event.alert != null) {
        if (event.alert!.type == 'critical') {
          notificationService.showAlertNotification(event.alert!);
        }
      }
    });
  }

  @override
  void dispose() {
    webSocketService.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Sensor Monitoring',
      theme: ThemeData.dark().copyWith(
        primaryColor: const Color(0xFF1E1E2E), // Dark aesthetic
        scaffoldBackgroundColor: const Color(0xFF11111B),
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFF1E1E2E),
          elevation: 0,
        ),
        cardColor: const Color(0xFF181825),
        colorScheme: const ColorScheme.dark().copyWith(
          secondary: const Color(0xFF89B4FA),
        ),
      ),
      home: const OverviewScreen(),
    );
  }
}
