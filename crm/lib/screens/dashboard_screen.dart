import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/models.dart';
import '../providers/providers.dart';
import '../theme/app_theme.dart';
import 'orders_screen.dart';
import 'menu_screen.dart';
import 'login_screen.dart';
import 'conversations_screen.dart';
import 'whatsapp_verification_screen.dart';
import 'package:image_picker/image_picker.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:flutter/foundation.dart';
import 'package:purchases_flutter/purchases_flutter.dart';

class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final businessId = ref.watch(selectedBusinessIdProvider);
    if (businessId == null) {
      return const Scaffold(body: Center(child: Text('No business selected')));
    }

    final ordersAsync = ref.watch(ordersProvider(businessId));
    final menuAsync = ref.watch(menuItemsProvider(businessId));

    return Scaffold(
      appBar: AppBar(
        title: const Text('Dashboard'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () {
              ref.invalidate(ordersProvider(businessId));
              ref.invalidate(menuItemsProvider(businessId));
            },
          ),
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
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Overview', style: Theme.of(context).textTheme.displayLarge),
            const SizedBox(height: 16),
            _SubscriptionCard(businessId: businessId),
            const SizedBox(height: 16),
            _BusinessProfileCard(businessId: businessId),
            const SizedBox(height: 24),
            Row(
              children: [
                Expanded(
                  child: _StatCard(
                    title: 'Active Orders',
                    value: ordersAsync.when(
                      skipLoadingOnRefresh: true,
                      data: (o) => o
                          .where(
                            (e) =>
                                e.status != OrderStatus.delivered &&
                                e.status != OrderStatus.cancelled,
                          )
                          .length
                          .toString(),
                      error: (_, __) => 'Error',
                      loading: () => '...',
                    ),
                    icon: Icons.shopping_bag,
                    color: AppTheme.primaryColor,
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: _StatCard(
                    title: 'Menu Items',
                    value: menuAsync.when(
                      data: (m) => m.length.toString(),
                      error: (_, __) => 'Error',
                      loading: () => '...',
                    ),
                    icon: Icons.restaurant_menu,
                    color: AppTheme.secondaryColor,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 32),
            Text(
              'Quick Actions',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 16),
            _QuickActionTile(
              title: 'Manage Orders',
              subtitle: 'Process and track customer orders',
              icon: Icons.list_alt,
              onTap: () => Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const OrdersScreen()),
              ),
            ),
            _QuickActionTile(
              title: 'Menu Management',
              subtitle: 'Edit prices and availability',
              icon: Icons.menu_book,
              onTap: () => Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const MenuScreen()),
              ),
            ),
            _QuickActionTile(
              title: 'Customer Insights',
              subtitle: 'View client interaction history',
              icon: Icons.people_outline,
              onTap: () => Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const ConversationsScreen()),
              ),
            ),
            _QuickActionTile(
              title: 'Provide Feedback',
              subtitle: 'Help us improve FastOrder',
              icon: Icons.feedback_outlined,
              onTap: () async {
                final Uri emailLaunchUri = Uri(
                  scheme: 'mailto',
                  path: 'hello@aitake.com',
                  queryParameters: {
                    'subject': 'FastOrder Early Access Feedback',
                  },
                );
                try {
                  await launchUrl(emailLaunchUri);
                } catch (e) {
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                        content: Text('Could not open email app.'),
                      ),
                    );
                  }
                }
              },
            ),
          ],
        ),
      ),
    );
  }
}

class _StatCard extends StatelessWidget {
  final String title;
  final String value;
  final IconData icon;
  final Color color;

  const _StatCard({
    required this.title,
    required this.value,
    required this.icon,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: color.withValues(alpha: 0.2)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: color, size: 32),
          const SizedBox(height: 16),
          Text(
            value,
            style: Theme.of(
              context,
            ).textTheme.displayLarge?.copyWith(color: color, fontSize: 36),
          ),
          Text(
            title,
            style: Theme.of(
              context,
            ).textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w600),
          ),
        ],
      ),
    );
  }
}

class _QuickActionTile extends StatelessWidget {
  final String title;
  final String subtitle;
  final IconData icon;
  final VoidCallback onTap;

  const _QuickActionTile({
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: Colors.grey.withValues(alpha: 0.1)),
          ),
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: const BoxDecoration(
                  color: AppTheme.backgroundColor,
                  shape: BoxShape.circle,
                ),
                child: Icon(icon, color: AppTheme.textColorPrimary),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    Text(
                      subtitle,
                      style: Theme.of(context).textTheme.bodyMedium,
                    ),
                  ],
                ),
              ),
              const Icon(
                Icons.chevron_right,
                color: AppTheme.textColorSecondary,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _BusinessProfileCard extends ConsumerWidget {
  final String businessId;
  const _BusinessProfileCard({required this.businessId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final profileAsync = ref.watch(whatsappProfileProvider(businessId));

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: Colors.grey.withValues(alpha: 0.1)),
      ),
      child: profileAsync.when(
        data: (profile) {
          if (profile == null) {
            return Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Text(
                  'WhatsApp not connected',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  'Connect your WhatsApp Business number to receive messages and orders.',
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
                const SizedBox(height: 16),
                ElevatedButton(
                  onPressed: () async {
                    final businesses = await ref.read(
                      managerBusinessesProvider.future,
                    );
                    final business = businesses.firstWhere(
                      (b) => b.id == businessId,
                    );
                    if (context.mounted) {
                      final phoneController = TextEditingController(
                        text: business.whatsappPhoneNumber ?? '',
                      );
                      final result = await showDialog<String>(
                        context: context,
                        builder: (context) => AlertDialog(
                          title: const Text('Connect WhatsApp'),
                          content: Column(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              const Text(
                                'Enter the WhatsApp Business phone number to connect.',
                              ),
                              const SizedBox(height: 16),
                              TextField(
                                controller: phoneController,
                                keyboardType: TextInputType.phone,
                                decoration: const InputDecoration(
                                  labelText: 'Phone Number',
                                  prefixIcon: Icon(Icons.phone_android),
                                  border: OutlineInputBorder(),
                                  filled: true,
                                ),
                              ),
                            ],
                          ),
                          actions: [
                            TextButton(
                              onPressed: () => Navigator.of(context).pop(),
                              child: const Text('Cancel'),
                            ),
                            ElevatedButton(
                              onPressed: () {
                                if (phoneController.text.trim().isNotEmpty) {
                                  Navigator.of(
                                    context,
                                  ).pop(phoneController.text.trim());
                                }
                              },
                              style: ElevatedButton.styleFrom(
                                backgroundColor: AppTheme.primaryColor,
                                foregroundColor: Colors.white,
                              ),
                              child: const Text('Continue'),
                            ),
                          ],
                        ),
                      );

                      if (result != null &&
                          result.isNotEmpty &&
                          context.mounted) {
                        Navigator.of(context).push(
                          MaterialPageRoute(
                            builder: (context) => WhatsAppVerificationScreen(
                              businessId: business.id,
                              phoneNumber: result,
                              businessName: business.name,
                            ),
                          ),
                        );
                      }
                    }
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppTheme.primaryColor,
                    foregroundColor: Colors.white,
                  ),
                  child: const Text('Connect WhatsApp'),
                ),
              ],
            );
          }
          final String? photoUrl = profile['profile_picture_url'];

          return Row(
            children: [
              CircleAvatar(
                radius: 30,
                backgroundImage: photoUrl != null
                    ? NetworkImage(photoUrl)
                    : null,
                child: photoUrl == null ? const Icon(Icons.business) : null,
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'WhatsApp Business Profile',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    Text(
                      profile['about'] ?? 'No description',
                      style: Theme.of(context).textTheme.bodyMedium,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),
              IconButton(
                icon: const Icon(Icons.edit),
                onPressed: () async {
                  final ImagePicker picker = ImagePicker();
                  final XFile? image = await picker.pickImage(
                    source: ImageSource.gallery,
                  );

                  if (image != null) {
                    try {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('Uploading photo...')),
                      );
                      final bytes = await image.readAsBytes();

                      final businesses = await ref.read(
                        managerBusinessesProvider.future,
                      );
                      final business = businesses.firstWhere(
                        (b) => b.id == businessId,
                      );
                      if (business.whatsappPhoneNumberId != null) {
                        await ref
                            .read(apiServiceProvider)
                            .updateWhatsAppProfilePhoto(
                              business.whatsappPhoneNumberId!,
                              bytes.toList(),
                              image.name,
                            );
                        ref.invalidate(whatsappProfileProvider(businessId));
                        if (context.mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(
                              content: Text('Photo updated successfully!'),
                            ),
                          );
                        }
                      }
                    } catch (e) {
                      if (context.mounted) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(content: Text('Error updating photo: $e')),
                        );
                      }
                    }
                  }
                },
              ),
            ],
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, st) => Text('Error: $e'),
      ),
    );
  }
}

class _SubscriptionCard extends ConsumerWidget {
  final String businessId;
  const _SubscriptionCard({required this.businessId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final businessesAsync = ref.watch(managerBusinessesProvider);

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppTheme.primaryColor.withValues(alpha: 0.05),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: AppTheme.primaryColor.withValues(alpha: 0.2)),
      ),
      child: businessesAsync.when(
        data: (businesses) {
          final business = businesses.firstWhere((b) => b.id == businessId);
          final isFree = business.subscriptionTier == 'free';
          final messageCount = business.aiMessageCount;
          final maxMessages = 1000;
          final isNearLimit = isFree && messageCount >= (maxMessages * 0.8);

          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    'Plan: ${business.subscriptionTier.toUpperCase()}',
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: AppTheme.primaryColor,
                    ),
                  ),
                  if (isFree)
                    ElevatedButton.icon(
                      onPressed: () async {
                        if (!kIsWeb) {
                          try {
                            await Purchases.logIn(business.id);
                            final offerings = await Purchases.getOfferings();
                            if (offerings.current != null &&
                                offerings
                                    .current!
                                    .availablePackages
                                    .isNotEmpty) {
                              final package =
                                  offerings.current!.availablePackages.first;
                              final customerInfo =
                                  await Purchases.purchasePackage(package);
                              if (customerInfo
                                      .entitlements
                                      .all['pro']
                                      ?.isActive ==
                                  true) {
                                if (context.mounted) {
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    const SnackBar(
                                      content: Text(
                                        'Successfully upgraded to Pro!',
                                      ),
                                    ),
                                  );
                                }
                              }
                            } else {
                              if (context.mounted) {
                                ScaffoldMessenger.of(context).showSnackBar(
                                  const SnackBar(
                                    content: Text(
                                      'No subscriptions available.',
                                    ),
                                  ),
                                );
                              }
                            }
                          } on Exception catch (e) {
                            if (context.mounted) {
                              ScaffoldMessenger.of(context).showSnackBar(
                                const SnackBar(
                                  content: Text('Purchase failed.'),
                                ),
                              );
                            }
                          }
                        } else {
                          try {
                            if (context.mounted) {
                              ScaffoldMessenger.of(context).showSnackBar(
                                const SnackBar(
                                  content: Text('Preparing secure checkout...'),
                                ),
                              );
                            }
                            final response = await ref
                                .read(apiServiceProvider)
                                .supabase
                                .functions
                                .invoke(
                                  'create_stripe_checkout',
                                  body: {'business_id': business.id},
                                );
                            final url = response.data['url'] as String?;
                            if (url != null) {
                              await launchUrl(
                                Uri.parse(url),
                                webOnlyWindowName: '_self',
                              );
                            } else {
                              throw Exception('No URL returned');
                            }
                          } catch (e) {
                            if (context.mounted) {
                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(
                                  content: Text('Could not start checkout: $e'),
                                ),
                              );
                            }
                          }
                        }
                      },
                      icon: const Icon(Icons.star, size: 18),
                      label: const Text('Upgrade to Pro'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppTheme.secondaryColor,
                        foregroundColor: Colors.white,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                      ),
                    ),
                ],
              ),
              const SizedBox(height: 16),
              if (isFree) ...[
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      'AI Messages Used',
                      style: Theme.of(context).textTheme.bodyMedium,
                    ),
                    Text(
                      '$messageCount / $maxMessages',
                      style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                        fontWeight: FontWeight.bold,
                        color: isNearLimit
                            ? AppTheme.errorColor
                            : AppTheme.textColorPrimary,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                LinearProgressIndicator(
                  value: (messageCount / maxMessages).clamp(0.0, 1.0),
                  backgroundColor: Colors.grey.withValues(alpha: 0.2),
                  valueColor: AlwaysStoppedAnimation<Color>(
                    isNearLimit ? AppTheme.errorColor : AppTheme.primaryColor,
                  ),
                  borderRadius: BorderRadius.circular(8),
                  minHeight: 8,
                ),
              ] else ...[
                Text(
                  'Unlimited AI Messages',
                  style: Theme.of(
                    context,
                  ).textTheme.bodyLarge?.copyWith(fontWeight: FontWeight.bold),
                ),
              ],
            ],
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, st) => Text('Error loading subscription'),
      ),
    );
  }
}
