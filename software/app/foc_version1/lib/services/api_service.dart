import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/user_model.dart';
import '../models/camera_model.dart';

class ApiService {
  static const String baseUrl = 'http://localhost:5000/api'; // Change to your server URL
  static String? _authToken;
  static User? _currentUser;

  static Map<String, String> get _headers => {
    'Content-Type': 'application/json',
    if (_authToken != null) 'Authorization': 'Bearer $_authToken',
  };

  // Authentication
  static Future<Map<String, dynamic>> login(String username, String password) async {
    try {
      // Since your server doesn't have a login endpoint, we'll simulate it
      // by checking if the user exists in the users collection
      final response = await http.get(
        Uri.parse('$baseUrl/config/users'),
        headers: _headers,
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        if (data['success'] == true) {
          final users = data['data'] as List;
          final user = users.firstWhere(
            (u) => u['username'] == username,
            orElse: () => null,
          );

          if (user != null) {
            _currentUser = User.fromJson(user);
            _authToken = 'dummy_token_${username}_${DateTime.now().millisecondsSinceEpoch}';
            
            return {
              'success': true,
              'message': 'Login successful',
              'user': _currentUser!.toJson(),
              'token': _authToken,
            };
          } else {
            return {
              'success': false,
              'message': 'Invalid username or password',
            };
          }
        }
      }

      return {
        'success': false,
        'message': 'Login failed. Please try again.',
      };
    } catch (e) {
      return {
        'success': false,
        'message': 'Network error: ${e.toString()}',
      };
    }
  }

  static Future<void> logout() async {
    _authToken = null;
    _currentUser = null;
  }

  static User? get currentUser => _currentUser;
  static bool get isLoggedIn => _authToken != null && _currentUser != null;

  // Get user cameras
  static Future<List<Camera>> getUserCameras(String userId) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/config/cameras/user/$userId'),
        headers: _headers,
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        if (data['success'] == true) {
          final camerasData = data['data'] as List;
          return camerasData.map((camera) => Camera.fromJson(camera)).toList();
        }
      }

      throw Exception('Failed to load cameras');
    } catch (e) {
      throw Exception('Error fetching cameras: ${e.toString()}');
    }
  }

  // Get all cameras
  static Future<List<Camera>> getAllCameras() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/config/cameras'),
        headers: _headers,
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        if (data['success'] == true) {
          final camerasData = data['data'] as List;
          return camerasData.map((camera) => Camera.fromJson(camera)).toList();
        }
      }

      throw Exception('Failed to load cameras');
    } catch (e) {
      throw Exception('Error fetching cameras: ${e.toString()}');
    }
  }

  // Get camera statistics
  static Future<Map<String, dynamic>> getCameraStats(String userId) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/config/cameras/stats/user/$userId'),
        headers: _headers,
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        if (data['success'] == true) {
          return data['data'];
        }
      }

      throw Exception('Failed to load camera statistics');
    } catch (e) {
      throw Exception('Error fetching camera stats: ${e.toString()}');
    }
  }

  // Get system health
  static Future<Map<String, dynamic>> getSystemHealth() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/health'),
        headers: _headers,
      );

      if (response.statusCode == 200) {
        return json.decode(response.body);
      }

      throw Exception('Failed to get system health');
    } catch (e) {
      throw Exception('Error fetching system health: ${e.toString()}');
    }
  }

  // Get active streams
  static Future<List<Map<String, dynamic>>> getActiveStreams() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/config/active_streams'),
        headers: _headers,
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        if (data['success'] == true) {
          return List<Map<String, dynamic>>.from(data['data']);
        }
      }

      throw Exception('Failed to load active streams');
    } catch (e) {
      throw Exception('Error fetching active streams: ${e.toString()}');
    }
  }
}