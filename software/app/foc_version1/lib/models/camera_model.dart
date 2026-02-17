import 'dart:ui';

class Camera {
  final String cameraId;
  final String name;
  final String source;
  final String type;
  final String userId;
  final String addedDate;
  final String lastActive;
  final String lastModified;
  final bool detectionEnabled;
  final bool autoStart;
  final bool streamEnabled;
  final bool peopleDetectionEnabled;
  final bool fireSmokeDetectionEnabled;
  final bool recordingEnabled;
  final String status;

  Camera({
    required this.cameraId,
    required this.name,
    required this.source,
    required this.type,
    required this.userId,
    required this.addedDate,
    required this.lastActive,
    required this.lastModified,
    required this.detectionEnabled,
    required this.autoStart,
    required this.streamEnabled,
    required this.peopleDetectionEnabled,
    required this.fireSmokeDetectionEnabled,
    required this.recordingEnabled,
    required this.status,
  });

  factory Camera.fromJson(Map<String, dynamic> json) {
    return Camera(
      cameraId: json['camera_id'] ?? '',
      name: json['name'] ?? '',
      source: json['source'] ?? '',
      type: json['type'] ?? 'ip',
      userId: json['user_id'] ?? '',
      addedDate: json['added_date'] ?? '',
      lastActive: json['last_active'] ?? '',
      lastModified: json['last_modified'] ?? '',
      detectionEnabled: json['detection_enabled'] ?? false,
      autoStart: json['auto_start'] ?? true,
      streamEnabled: json['stream_enabled'] ?? true,
      peopleDetectionEnabled: json['people_detection_enabled'] ?? false,
      fireSmokeDetectionEnabled: json['fire_smoke_detection_enabled'] ?? false,
      recordingEnabled: json['recording_enabled'] ?? false,
      status: json['status'] ?? 'inactive',
    );
  }

  bool get isActive => status == 'active';
  bool get isOnline => status == 'active' || status == 'streaming';
  
  Color get statusColor {
    switch (status.toLowerCase()) {
      case 'active':
        return const Color(0xFF4CAF50);
      case 'inactive':
        return const Color(0xFF9E9E9E);
      case 'error':
        return const Color(0xFFF44336);
      case 'streaming':
        return const Color(0xFF2196F3);
      default:
        return const Color(0xFF9E9E9E);
    }
  }
}