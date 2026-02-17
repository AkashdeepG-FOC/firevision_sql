class Alert {
  final String title;
  final String body;
  final String? thumbnailUrl;
  final DateTime timestamp;

  Alert({required this.title, required this.body, this.thumbnailUrl, required this.timestamp});

  factory Alert.fromMap(Map<String, dynamic> map) {
    return Alert(
      title: map['title'] ?? '',
      body: map['body'] ?? '',
      thumbnailUrl: map['thumbnailUrl'],
      timestamp: DateTime.now(),
    );
  }
} 