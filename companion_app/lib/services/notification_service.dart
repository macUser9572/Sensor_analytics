import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import '../models/models.dart';

class NotificationService {
  static final NotificationService _instance = NotificationService._internal();
  factory NotificationService() => _instance;
  NotificationService._internal();

  final FlutterLocalNotificationsPlugin _flutterLocalNotificationsPlugin = 
      FlutterLocalNotificationsPlugin();

  Future<void> init() async {
    const AndroidInitializationSettings initializationSettingsAndroid =
        AndroidInitializationSettings('@mipmap/ic_launcher');
        
    const DarwinInitializationSettings initializationSettingsIOS =
        DarwinInitializationSettings(
      requestAlertPermission: true,
      requestBadgePermission: true,
      requestSoundPermission: true,
    );
    
    const InitializationSettings initializationSettings = InitializationSettings(
      android: initializationSettingsAndroid,
      iOS: initializationSettingsIOS,
    );

    await _flutterLocalNotificationsPlugin.initialize(
      initializationSettings,
      onDidReceiveNotificationResponse: (NotificationResponse response) {
        // Here we could handle UI routing based on notification payload interaction
      },
    );
  }

  Future<void> showAlertNotification(Alert alert) async {
    if (alert.type != 'critical') return;

    const AndroidNotificationDetails androidPlatformChannelSpecifics =
        AndroidNotificationDetails(
      'alerts_channel', 
      'Critical Alerts',
      channelDescription: 'Notifications for critical sensor alerts',
      importance: Importance.max,
      priority: Priority.high,
      ticker: 'ticker',
    );
    
    const NotificationDetails platformChannelSpecifics = 
        NotificationDetails(android: androidPlatformChannelSpecifics);
        
    await _flutterLocalNotificationsPlugin.show(
      alert.id.hashCode,
      'CRITICAL: ${alert.subsystem}',
      '${alert.metric} breached threshold! Value: ${alert.currentValue.toStringAsFixed(1)}',
      platformChannelSpecifics,
      payload: 'alert_${alert.id}',
    );
  }
}

final notificationService = NotificationService();
