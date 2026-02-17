import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';
import '../models/user_model.dart';
import 'api_service.dart';

class AuthService {
  static const String _tokenKey = 'auth_token';
  static const String _userKey = 'user_data';

  static Future<Map<String, dynamic>> login(String username, String password) async {
    try {
      final result = await ApiService.login(username, password);
      
      if (result['success'] == true) {
        // Save login data locally
        await _saveLoginData(result['token'], result['user']);
      }
      
      return result;
    } catch (e) {
      return {
        'success': false,
        'message': 'Login failed: ${e.toString()}',
      };
    }
  }

  static Future<void> logout() async {
    await ApiService.logout();
    await _clearLoginData();
  }

  static Future<bool> isLoggedIn() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString(_tokenKey);
    final userData = prefs.getString(_userKey);
    
    if (token != null && userData != null) {
      // Restore user session
      try {
        final userMap = json.decode(userData);
        // You might want to validate the token with the server here
        return true;
      } catch (e) {
        await _clearLoginData();
        return false;
      }
    }
    
    return false;
  }

  static Future<User?> getCurrentUser() async {
    final prefs = await SharedPreferences.getInstance();
    final userData = prefs.getString(_userKey);
    
    if (userData != null) {
      try {
        final userMap = json.decode(userData);
        return User.fromJson(userMap);
      } catch (e) {
        return null;
      }
    }
    
    return null;
  }

  static Future<void> _saveLoginData(String token, Map<String, dynamic> userData) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_tokenKey, token);
    await prefs.setString(_userKey, json.encode(userData));
  }

  static Future<void> _clearLoginData() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_tokenKey);
    await prefs.remove(_userKey);
  }
}