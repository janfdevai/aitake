import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import '../services/api_service.dart';
import '../models/models.dart';

final apiServiceProvider = Provider((ref) => ApiService());

final businessesProvider = FutureProvider<List<Business>>((ref) async {
  final apiService = ref.watch(apiServiceProvider);
  return apiService.getBusinesses();
});

final selectedBusinessIdProvider = StateProvider<String?>((ref) => null);

final currentManagerProvider = StateNotifierProvider<ManagerNotifier, Manager?>(
  (ref) {
    return ManagerNotifier(ref);
  },
);

class ManagerNotifier extends StateNotifier<Manager?> {
  final Ref ref;
  ManagerNotifier(this.ref) : super(null) {
    _init();
  }

  void _init() {
    final supabase = ref.read(apiServiceProvider).supabase;

    // Listen to Auth state changes
    supabase.auth.onAuthStateChange.listen((data) async {
      final AuthChangeEvent event = data.event;
      final Session? session = data.session;

      if (event == AuthChangeEvent.signedIn && session != null) {
        final manager = await ref.read(apiServiceProvider).getCurrentManager();
        state = manager;
      } else if (event == AuthChangeEvent.signedOut) {
        state = null;
      }
    });

    // Check initial session
    final session = supabase.auth.currentSession;
    if (session != null) {
      ref.read(apiServiceProvider).getCurrentManager().then((manager) {
        state = manager;
      });
    }
  }
}

final managerBusinessesProvider = FutureProvider<List<Business>>((ref) async {
  final manager = ref.watch(currentManagerProvider);
  if (manager == null) return [];
  final apiService = ref.watch(apiServiceProvider);
  return apiService.getManagerBusinesses(manager.managerId);
});

final menuItemsProvider = FutureProvider.family<List<MenuItem>, String>((
  ref,
  businessId,
) async {
  final apiService = ref.watch(apiServiceProvider);
  return apiService.getMenuItems(businessId);
});

final ordersProvider = FutureProvider.family<List<Order>, String>((
  ref,
  businessId,
) async {
  // Auto-refresh every 10 seconds
  final timer = Timer(const Duration(seconds: 10), () {
    ref.invalidateSelf();
  });
  ref.onDispose(() => timer.cancel());

  final apiService = ref.watch(apiServiceProvider);
  return apiService.getOrders(businessId);
});

final orderStatusUpdateProvider =
    FutureProvider.family<void, ({String orderId, OrderStatus status})>((
      ref,
      args,
    ) async {
      final apiService = ref.read(apiServiceProvider);
      await apiService.updateOrderStatus(args.orderId, args.status);
    });

final conversationsProvider = FutureProvider.family<List<Conversation>, String>(
  (ref, businessId) async {
    // Auto-refresh every 10 seconds
    final timer = Timer(const Duration(seconds: 10), () {
      ref.invalidateSelf();
    });
    ref.onDispose(() => timer.cancel());

    final apiService = ref.watch(apiServiceProvider);
    return apiService.getConversations(businessId);
  },
);

final messagesProvider = FutureProvider.family<List<Message>, String>((
  ref,
  conversationId,
) async {
  // Auto-refresh every 5 seconds for messages (more frequent)
  final timer = Timer(const Duration(seconds: 5), () {
    ref.invalidateSelf();
  });
  ref.onDispose(() => timer.cancel());

  final apiService = ref.watch(apiServiceProvider);
  return apiService.getMessages(conversationId);
});
