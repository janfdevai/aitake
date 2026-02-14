import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import '../models/models.dart';

class ApiService {
  final String baseUrl;

  ApiService({String? baseUrl})
    : baseUrl =
          baseUrl ??
          (kIsWeb
              ? 'http://127.0.0.1:8000'
              : Platform.isAndroid
              ? 'http://10.0.2.2:8000'
              : 'http://127.0.0.1:8000');

  Future<Manager> login(String email) async {
    final response = await http.get(
      Uri.parse('$baseUrl/managers/login?email=$email'),
    );
    if (response.statusCode == 200) {
      return Manager.fromJson(json.decode(response.body));
    } else {
      throw Exception('Failed to login: ${response.statusCode}');
    }
  }

  Future<List<Business>> getManagerBusinesses(String managerId) async {
    final response = await http.get(
      Uri.parse('$baseUrl/managers/$managerId/businesses'),
    );
    if (response.statusCode == 200) {
      List data = json.decode(response.body);
      return data.map((item) => Business.fromJson(item)).toList();
    } else {
      throw Exception('Failed to load manager businesses');
    }
  }

  Future<Manager> createManager(Map<String, dynamic> data) async {
    final response = await http.post(
      Uri.parse('$baseUrl/managers'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode(data),
    );
    if (response.statusCode == 200 || response.statusCode == 201) {
      return Manager.fromJson(json.decode(response.body));
    } else {
      throw Exception('Failed to create manager: ${response.body}');
    }
  }

  Future<List<Business>> getBusinesses() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/businesses'));
      if (response.statusCode == 200) {
        List data = json.decode(response.body);
        return data.map((item) => Business.fromJson(item)).toList();
      } else {
        throw Exception('Failed to load businesses: ${response.statusCode}');
      }
    } catch (e) {
      print('Error fetching businesses: $e');
      rethrow;
    }
  }

  Future<List<MenuItem>> getMenuItems(String businessId) async {
    final response = await http.get(
      Uri.parse('$baseUrl/businesses/$businessId/menu'),
    );
    if (response.statusCode == 200) {
      List data = json.decode(response.body);
      return data.map((item) => MenuItem.fromJson(item)).toList();
    } else {
      throw Exception('Failed to load menu items');
    }
  }

  Future<List<Order>> getOrders(
    String businessId, {
    OrderStatus? status,
  }) async {
    String url = '$baseUrl/businesses/$businessId/orders';
    if (status != null) {
      url += '?status=${status.name}';
    }
    final response = await http.get(Uri.parse(url));
    if (response.statusCode == 200) {
      List data = json.decode(response.body);
      return data.map((item) => Order.fromJson(item)).toList();
    } else {
      throw Exception('Failed to load orders');
    }
  }

  Future<Order> updateOrderStatus(String orderId, OrderStatus status) async {
    final response = await http.patch(
      Uri.parse('$baseUrl/orders/$orderId/status?status=${status.name}'),
    );
    if (response.statusCode == 200) {
      return Order.fromJson(json.decode(response.body));
    } else {
      throw Exception('Failed to update order status');
    }
  }

  Future<MenuItem> createMenuItem(
    String businessId,
    Map<String, dynamic> itemData,
  ) async {
    final response = await http.post(
      Uri.parse('$baseUrl/businesses/$businessId/menu'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode(itemData),
    );
    if (response.statusCode == 200 || response.statusCode == 201) {
      return MenuItem.fromJson(json.decode(response.body));
    } else {
      throw Exception('Failed to create menu item: ${response.body}');
    }
  }

  Future<MenuItem> updateMenuItem(
    String itemId,
    Map<String, dynamic> updates,
  ) async {
    final response = await http.patch(
      Uri.parse('$baseUrl/menu/$itemId'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode(updates),
    );
    if (response.statusCode == 200) {
      return MenuItem.fromJson(json.decode(response.body));
    } else {
      throw Exception('Failed to update menu item');
    }
  }

  Future<Business> createBusiness(
    Map<String, dynamic> data, {
    String? managerId,
  }) async {
    String url = '$baseUrl/businesses';
    if (managerId != null) {
      url += '?manager_id=$managerId';
    }
    final response = await http.post(
      Uri.parse(url),
      headers: {'Content-Type': 'application/json'},
      body: json.encode(data),
    );
    if (response.statusCode == 200 || response.statusCode == 201) {
      return Business.fromJson(json.decode(response.body));
    } else {
      throw Exception('Failed to create business: ${response.body}');
    }
  }

  // --- CONVERSATIONS ---
  Future<List<Conversation>> getConversations(String businessId) async {
    final response = await http.get(
      Uri.parse('$baseUrl/businesses/$businessId/conversations'),
    );
    if (response.statusCode == 200) {
      List data = json.decode(response.body);
      return data.map((item) => Conversation.fromJson(item)).toList();
    } else {
      throw Exception('Failed to load conversations');
    }
  }

  Future<List<Message>> getMessages(String conversationId) async {
    final response = await http.get(
      Uri.parse('$baseUrl/conversations/$conversationId/messages'),
    );
    if (response.statusCode == 200) {
      List data = json.decode(response.body);
      return data.map((item) => Message.fromJson(item)).toList();
    } else {
      throw Exception('Failed to load messages');
    }
  }

  Future<Message> sendMessage(
    String conversationId,
    String content,
    SenderType senderType,
  ) async {
    final response = await http.post(
      Uri.parse('$baseUrl/conversations/$conversationId/messages'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({'content': content, 'sender_type': senderType.name}),
    );
    if (response.statusCode == 200 || response.statusCode == 201) {
      return Message.fromJson(json.decode(response.body));
    } else {
      throw Exception('Failed to send message: ${response.body}');
    }
  }
}
