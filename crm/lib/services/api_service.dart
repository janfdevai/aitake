import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:supabase_flutter/supabase_flutter.dart';
import '../models/models.dart';

class ApiService {
  final supabase = Supabase.instance.client;
  // TODO: Move to environment config
  static const String channelsApiUrl = String.fromEnvironment(
    'CHANNELS_API_URL',
    defaultValue: 'http://localhost:8002',
  );

  // --- AUTH & MANAGER ---
  Future<void> login(String email, String password) async {
    await supabase.auth.signInWithPassword(email: email, password: password);
  }

  Future<AuthResponse> register(String email, String password) async {
    return await supabase.auth.signUp(email: email, password: password);
  }

  Future<Manager?> getCurrentManager() async {
    final user = supabase.auth.currentUser;
    if (user == null) return null;

    final response = await supabase
        .from('managers')
        .select()
        .eq('email', user.email!)
        .maybeSingle();

    if (response == null) return null;

    final manager = Manager.fromJson(response);

    // Link Supabase Auth ID if not already linked
    if (manager.authUserId == null) {
      await supabase
          .from('managers')
          .update({'auth_user_id': user.id})
          .eq('manager_id', manager.managerId);
    }

    return manager;
  }

  Future<List<Business>> getManagerBusinesses(String managerId) async {
    final response = await supabase
        .from('business_managers')
        .select('''
          businesses (*)
        ''')
        .eq('manager_id', managerId);

    return (response as List)
        .map((item) => Business.fromJson(item['businesses']))
        .toList();
  }

  Future<Manager> createManager(Map<String, dynamic> data) async {
    final response = await supabase
        .from('managers')
        .insert(data)
        .select()
        .single();
    return Manager.fromJson(response);
  }

  // --- BUSINESS ---
  Future<List<Business>> getBusinesses() async {
    final response = await supabase.from('businesses').select();
    return (response as List).map((item) => Business.fromJson(item)).toList();
  }

  Future<Business> createBusiness(
    Map<String, dynamic> data, {
    String? managerId,
  }) async {
    final businessResponse = await supabase
        .from('businesses')
        .insert(data)
        .select()
        .single();
    final business = Business.fromJson(businessResponse);

    if (managerId != null) {
      await supabase.from('business_managers').insert({
        'business_id': business.id,
        'manager_id': managerId,
      });
    }

    return business;
  }

  // --- MENU ---
  Future<List<MenuItem>> getMenuItems(String businessId) async {
    final response = await supabase
        .from('menu_items')
        .select()
        .eq('business_id', businessId);
    return (response as List).map((item) => MenuItem.fromJson(item)).toList();
  }

  Future<MenuItem> createMenuItem(
    String businessId,
    Map<String, dynamic> itemData,
  ) async {
    final response = await supabase
        .from('menu_items')
        .insert({...itemData, 'business_id': businessId})
        .select()
        .single();
    return MenuItem.fromJson(response);
  }

  Future<MenuItem> updateMenuItem(
    String itemId,
    Map<String, dynamic> updates,
  ) async {
    final response = await supabase
        .from('menu_items')
        .update(updates)
        .eq('item_id', itemId)
        .select()
        .single();
    return MenuItem.fromJson(response);
  }

  // --- ORDERS ---
  Future<List<Order>> getOrders(
    String businessId, {
    OrderStatus? status,
  }) async {
    var query = supabase
        .from('orders')
        .select('*, items:order_items(*)')
        .eq('business_id', businessId);

    if (status != null) {
      query = query.eq('status', status.name);
    }

    final response = await query.order('ordered_at', ascending: false);
    return (response as List).map((item) => Order.fromJson(item)).toList();
  }

  Future<Order> updateOrderStatus(String orderId, OrderStatus status) async {
    final response = await supabase
        .from('orders')
        .update({'status': status.name})
        .eq('order_id', orderId)
        .select('*, items:order_items(*)')
        .single();
    return Order.fromJson(response);
  }

  // --- CONVERSATIONS & MESSAGES ---
  Future<List<Conversation>> getConversations(String businessId) async {
    final response = await supabase
        .from('conversations')
        .select('*, client:clients(*)')
        .eq('business_id', businessId)
        .order('updated_at', ascending: false);

    return (response as List).map((item) {
      final conv = Conversation.fromJson(item);
      // Map extra fields from client for list view
      return conv.copyWith(
        clientName: item['client']['full_name'],
        clientWaId: item['client']['wa_id'],
      );
    }).toList();
  }

  Future<List<Message>> getMessages(String conversationId) async {
    final response = await supabase
        .from('messages')
        .select()
        .eq('conversation_id', conversationId)
        .order('created_at', ascending: true);
    return (response as List).map((item) => Message.fromJson(item)).toList();
  }

  Future<Message> sendMessage(
    String conversationId,
    String content,
    SenderType senderType, {
    String? phoneNumber,
  }) async {
    // 1. Insert into Supabase
    final response = await supabase
        .from('messages')
        .insert({
          'conversation_id': conversationId,
          'content': content,
          'sender_type': senderType.name,
        })
        .select()
        .single();

    // 2. Trigger External API (WhatsApp) if sender is business
    if (senderType == SenderType.business && phoneNumber != null) {
      try {
        final uri = Uri.parse('$channelsApiUrl/send-message');
        final apiResponse = await http.post(
          uri,
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({'phone_number': phoneNumber, 'content': content}),
        );

        if (apiResponse.statusCode != 200) {
          print('Failed to send message via Channels API: ${apiResponse.body}');
          // Optionally throw or handle error, but we might not want to block the UI since DB insert succeeded
        }
      } catch (e) {
        print('Error calling Channels API: $e');
      }
    }

    return Message.fromJson(response);
  }

  // --- REALTIME ---
  Stream<List<Order>> subscribeToOrders(String businessId) {
    return supabase
        .from('orders')
        .stream(primaryKey: ['order_id'])
        .eq('business_id', businessId)
        .order('ordered_at', ascending: false)
        .map((data) => data.map((item) => Order.fromJson(item)).toList());
  }

  Stream<List<Message>> subscribeToMessages(String conversationId) {
    return supabase
        .from('messages')
        .stream(primaryKey: ['message_id'])
        .eq('conversation_id', conversationId)
        .order('created_at', ascending: true)
        .map((data) => data.map((item) => Message.fromJson(item)).toList());
  }

  // --- WHATSAPP ONBOARDING ---
  Future<String> registerWhatsApp(
    String phoneNumber,
    String displayName,
  ) async {
    final uri = Uri.parse('$channelsApiUrl/whatsapp/onboard/start');
    final response = await http.post(
      uri,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'phone_number': phoneNumber,
        'display_name': displayName,
      }),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return data['phone_number_id'];
    } else {
      throw Exception('Failed to start onboarding: ${response.body}');
    }
  }

  Future<void> verifyWhatsApp(
    String phoneNumberId,
    String code,
    String businessId,
  ) async {
    // 1. Verify with Channels API
    final uri = Uri.parse('$channelsApiUrl/whatsapp/onboard/verify');
    final response = await http.post(
      uri,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'phone_number_id': phoneNumberId, 'code': code}),
    );

    if (response.statusCode != 200) {
      throw Exception('Failed to verify code: ${response.body}');
    }

    // 2. Update Business in Supabase
    await supabase
        .from('businesses')
        .update({'whatsapp_phone_number_id': phoneNumberId})
        .eq('business_id', businessId);
  }
}
