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
      floatingActionButton: FloatingActionButton(
        onPressed: () => _showAddBusinessDialog(context, ref),
        child: const Icon(Icons.add),
      ),
    );
  }

  Future<void> _showAddBusinessDialog(
    BuildContext context,
    WidgetRef ref,
  ) async {
    final nameController = TextEditingController();
    final addressController = TextEditingController();
    bool isLoading = false;

    await showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) {
          return AlertDialog(
            title: const Text('Add New Business'),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: nameController,
                  decoration: const InputDecoration(
                    labelText: 'Business Name',
                    prefixIcon: Icon(Icons.business),
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: addressController,
                  decoration: const InputDecoration(
                    labelText: 'Address',
                    prefixIcon: Icon(Icons.location_on),
                    border: OutlineInputBorder(),
                  ),
                ),
              ],
            ),
            actions: [
              TextButton(
                onPressed: isLoading ? null : () => Navigator.of(context).pop(),
                child: const Text('Cancel'),
              ),
              ElevatedButton(
                onPressed: isLoading
                    ? null
                    : () async {
                        if (nameController.text.trim().isEmpty ||
                            addressController.text.trim().isEmpty) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(
                              content: Text('Please fill all fields'),
                              backgroundColor: Colors.red,
                            ),
                          );
                          return;
                        }

                        setState(() => isLoading = true);

                        try {
                          final apiService = ref.read(apiServiceProvider);
                          final manager = await apiService.getCurrentManager();
                          if (manager == null) {
                            throw Exception('Manager not found');
                          }

                          await apiService.createBusiness({
                            'name': nameController.text.trim(),
                            'address': addressController.text.trim(),
                            'whatsapp_phone_number': null,
                          }, managerId: manager.managerId);

                          ref.invalidate(managerBusinessesProvider);
                          if (context.mounted) {
                            Navigator.of(context).pop();
                          }
                        } catch (e) {
                          setState(() => isLoading = false);
                          if (context.mounted) {
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(
                                content: Text('Error: $e'),
                                backgroundColor: Colors.red,
                              ),
                            );
                          }
                        }
                      },
                child: isLoading
                    ? const SizedBox(
                        height: 20,
                        width: 20,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Text('Create'),
              ),
            ],
          );
        },
      ),
    );
  }
}
