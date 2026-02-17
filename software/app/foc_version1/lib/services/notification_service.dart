import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter/material.dart';

class NotificationService {
  static final NotificationService _instance = NotificationService._internal();
  factory NotificationService() => _instance;
  NotificationService._internal();

  final FlutterLocalNotificationsPlugin flutterLocalNotificationsPlugin = FlutterLocalNotificationsPlugin();

  Future<void> init() async {
    // Android settings
    const AndroidInitializationSettings initializationSettingsAndroid = AndroidInitializationSettings('@mipmap/ic_launcher');
    // iOS settings
    final DarwinInitializationSettings initializationSettingsIOS = DarwinInitializationSettings();
    // Init
    final InitializationSettings initializationSettings = InitializationSettings(
      android: initializationSettingsAndroid,
      iOS: initializationSettingsIOS,
    );
    await flutterLocalNotificationsPlugin.initialize(initializationSettings);

    // Request permissions
    await FirebaseMessaging.instance.requestPermission();

    // Foreground message handler
    FirebaseMessaging.onMessage.listen((RemoteMessage message) {
      _showNotification(message);
    });
  }

  Future<void> _showNotification(RemoteMessage message) async {
    final notification = message.notification;
    final imageUrl = notification?.android?.imageUrl ?? notification?.apple?.imageUrl ?? message.data['thumbnailUrl'];

    final styleInformation = imageUrl != null
        ? BigPictureStyleInformation(
            FilePathAndroidBitmap(imageUrl),
            contentTitle: notification?.title,
            summaryText: notification?.body,
          )
        : null;

    final androidDetails = AndroidNotificationDetails(
      'dispatch_alerts',
      'Dispatch Alerts',
      channelDescription: 'Channel for dispatch alerts',
      importance: Importance.max,
      priority: Priority.high,
      styleInformation: styleInformation,
    );

    final details = NotificationDetails(android: androidDetails);

    await flutterLocalNotificationsPlugin.show(
      0,
      notification?.title ?? message.data['title'],
      notification?.body ?? message.data['body'],
      details,
      payload: imageUrl,
    );
  }
} 