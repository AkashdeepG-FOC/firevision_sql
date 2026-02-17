class User {
  final String username;
  final String email;
  final String role;
  final String createdDate;
  final String lastLogin;
  final bool isActive;

  User({
    required this.username,
    required this.email,
    required this.role,
    required this.createdDate,
    required this.lastLogin,
    required this.isActive,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      username: json['username'] ?? '',
      email: json['email'] ?? '',
      role: json['role'] ?? 'user',
      createdDate: json['created_date'] ?? '',
      lastLogin: json['last_login'] ?? '',
      isActive: json['is_active'] ?? true,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'username': username,
      'email': email,
      'role': role,
      'created_date': createdDate,
      'last_login': lastLogin,
      'is_active': isActive,
    };
  }
}