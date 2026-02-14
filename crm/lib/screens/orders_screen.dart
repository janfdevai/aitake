import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../providers/providers.dart';
import '../models/models.dart';
import '../theme/app_theme.dart';

class OrdersScreen extends ConsumerWidget {
  const OrdersScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final businessId = ref.watch(selectedBusinessIdProvider)!;
    final ordersAsync = ref.watch(ordersProvider(businessId));

    return Scaffold(
      appBar: AppBar(title: const Text('Orders')),
      body: ordersAsync.when(
        skipLoadingOnRefresh: true,
        data: (orders) => orders.isEmpty
            ? Center(
                child: Text(
                  'No orders found',
                  style: Theme.of(context).textTheme.bodyLarge,
                ),
              )
            : ListView.builder(
                itemCount: orders.length,
                padding: const EdgeInsets.symmetric(vertical: 8),
                itemBuilder: (context, index) {
                  final order = orders[index];
                  return _OrderCard(order: order);
                },
              ),
        error: (err, stack) => Center(child: Text('Error: $err')),
        loading: () => const Center(child: CircularProgressIndicator()),
      ),
    );
  }
}

class _OrderCard extends ConsumerWidget {
  final Order order;

  const _OrderCard({required this.order});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final currencyFormat = NumberFormat.currency(symbol: '\$');
    final dateFormat = DateFormat('MMM dd, hh:mm a');

    return Card(
      child: ExpansionTile(
        title: Row(
          children: [
            _StatusBadge(status: order.status),
            const SizedBox(width: 8),
            Text(
              order.orderId.substring(0, 8),
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
          ],
        ),
        subtitle: Text(
          'Total: ${currencyFormat.format(order.totalAmount)} • ${dateFormat.format(order.orderedAt)}',
        ),
        children: [
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Divider(),
                ...order.items.map(
                  (item) => Padding(
                    padding: const EdgeInsets.symmetric(vertical: 4),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          '${item.quantity}x ${item.nameSnapshot ?? "Unknown Item"}',
                        ),
                        Text(
                          currencyFormat.format(item.unitPrice * item.quantity),
                        ),
                      ],
                    ),
                  ),
                ),
                const Divider(),
                if (order.deliveryAddress != null) ...[
                  Text(
                    'Address: ${order.deliveryAddress}',
                    style: const TextStyle(fontWeight: FontWeight.w500),
                  ),
                  const SizedBox(height: 16),
                ],
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceAround,
                  children: [
                    if (order.status == OrderStatus.pending)
                      ElevatedButton(
                        onPressed: () => _updateStatus(
                          ref,
                          order.orderId,
                          OrderStatus.confirmed,
                        ),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.blue,
                          foregroundColor: Colors.white,
                        ),
                        child: const Text('Confirm'),
                      ),
                    if (order.status == OrderStatus.confirmed)
                      ElevatedButton(
                        onPressed: () => _updateStatus(
                          ref,
                          order.orderId,
                          OrderStatus.preparing,
                        ),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.orange,
                          foregroundColor: Colors.white,
                        ),
                        child: const Text('Prepare'),
                      ),
                    if (order.status == OrderStatus.preparing)
                      ElevatedButton(
                        onPressed: () => _updateStatus(
                          ref,
                          order.orderId,
                          OrderStatus.ready,
                        ),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.green,
                          foregroundColor: Colors.white,
                        ),
                        child: const Text('Ready'),
                      ),
                    if (order.status == OrderStatus.ready)
                      ElevatedButton(
                        onPressed: () => _updateStatus(
                          ref,
                          order.orderId,
                          OrderStatus.delivered,
                        ),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppTheme.successColor,
                          foregroundColor: Colors.white,
                        ),
                        child: const Text('Deliver'),
                      ),
                    ElevatedButton(
                      onPressed: () => _updateStatus(
                        ref,
                        order.orderId,
                        OrderStatus.cancelled,
                      ),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppTheme.errorColor,
                        foregroundColor: Colors.white,
                      ),
                      child: const Text('Cancel'),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  void _updateStatus(WidgetRef ref, String orderId, OrderStatus status) {
    final businessId = ref.read(selectedBusinessIdProvider)!;
    ref.read(apiServiceProvider).updateOrderStatus(orderId, status).then((_) {
      ref.invalidate(ordersProvider(businessId));
    });
  }
}

class _StatusBadge extends StatelessWidget {
  final OrderStatus status;

  const _StatusBadge({required this.status});

  @override
  Widget build(BuildContext context) {
    Color color;
    switch (status) {
      case OrderStatus.pending:
        color = Colors.grey;
        break;
      case OrderStatus.confirmed:
        color = Colors.blue;
        break;
      case OrderStatus.preparing:
        color = Colors.orange;
        break;
      case OrderStatus.ready:
        color = Colors.green;
        break;
      case OrderStatus.delivered:
        color = AppTheme.successColor;
        break;
      case OrderStatus.cancelled:
        color = AppTheme.errorColor;
        break;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withValues(alpha: 0.5)),
      ),
      child: Text(
        status.name.toUpperCase(),
        style: TextStyle(
          color: color,
          fontSize: 10,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }
}
