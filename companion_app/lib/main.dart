import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'models/models.dart';
import 'services/notification_service.dart';
import 'services/websocket_service.dart';
import 'providers/providers.dart';
import 'config/app_config.dart';
import 'router.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  await AppConfig.init();
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
  void dispose() {
    webSocketService.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    // Listen to the alert event stream to show notifications globally
    ref.listen<AsyncValue<AlertEvent>>(alertsStreamProvider, (previous, next) {
      if (next.hasValue && next.value != null) {
        final event = next.value!;
        if (event.type == AlertEventType.fired && event.alert != null) {
          notificationService.showAlertNotification(event.alert!);
        }
      }
    });

    return MaterialApp.router(
      title: 'Sensor Monitoring',
      routerConfig: goRouter,
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
    );
  }
}
