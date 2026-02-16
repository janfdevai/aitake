import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/providers.dart';
import 'dashboard_screen.dart';
import 'login_screen.dart';

class BusinessListScreen extends ConsumerWidget {
  const BusinessListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final businessesAsync = ref.watch(managerBusinessesProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Select Business'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () {
              ref.read(apiServiceProvider).supabase.auth.signOut();
              ref.read(selectedBusinessIdProvider.notifier).state = null;
              Navigator.pushAndRemoveUntil(
                context,
                MaterialPageRoute(builder: (_) => const LoginScreen()),
                (route) => false,
              );
            },
          ),
        ],
      ),
      body: businessesAsync.when(
        data: (businesses) => ListView.builder(
          itemCount: businesses.length,
          padding: const EdgeInsets.all(16),
          itemBuilder: (context, index) {
            final business = businesses[index];
            return Card(
              child: ListTile(
                leading: business.logoUrl != null
                    ? CircleAvatar(
                        backgroundImage: NetworkImage(business.logoUrl!),
                      )
                    : const CircleAvatar(child: Icon(Icons.business)),
                title: Text(
                  business.name,
                  style: Theme.of(context).textTheme.titleLarge,
                ),
                subtitle: Text(business.address ?? 'No address provided'),
                trailing: const Icon(Icons.chevron_right),
                onTap: () {
                  ref.read(selectedBusinessIdProvider.notifier).state =
                      business.businessId;
                  Navigator.of(context).push(
                    MaterialPageRoute(builder: (_) => const DashboardScreen()),
                  );
                },
              ),
            );
          },
        ),
        error: (err, stack) => Center(child: Text('Error: $err')),
        loading: () => const Center(child: CircularProgressIndicator()),
      ),
    );
  }
}
