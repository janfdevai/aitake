import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/providers.dart';
import '../theme/app_theme.dart';

class WhatsAppVerificationScreen extends ConsumerStatefulWidget {
  final String businessId;
  final String phoneNumber;
  final String businessName;

  const WhatsAppVerificationScreen({
    super.key,
    required this.businessId,
    required this.phoneNumber,
    required this.businessName,
  });

  @override
  ConsumerState<WhatsAppVerificationScreen> createState() =>
      _WhatsAppVerificationScreenState();
}

class _WhatsAppVerificationScreenState
    extends ConsumerState<WhatsAppVerificationScreen> {
  final _otpController = TextEditingController();
  bool _isLoading = false;
  bool _codeSent = false;
  String? _phoneNumberId;

  @override
  void initState() {
    super.initState();
    // Auto-send code on load
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _sendCode();
    });
  }

  @override
  void dispose() {
    _otpController.dispose();
    super.dispose();
  }

  Future<void> _sendCode() async {
    setState(() {
      _isLoading = true;
    });

    try {
      final apiService = ref.read(apiServiceProvider);
      final pid = await apiService.registerWhatsApp(
        widget.phoneNumber,
        widget.businessName,
      );

      if (mounted) {
        setState(() {
          _phoneNumberId = pid;
          _codeSent = true;
          _isLoading = false;
        });
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Verification code sent!'),
            backgroundColor: AppTheme.successColor,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to send code: $e'),
            backgroundColor: AppTheme.errorColor,
          ),
        );
      }
    }
  }

  Future<void> _verifyCode() async {
    if (_otpController.text.isEmpty || _phoneNumberId == null) return;

    setState(() {
      _isLoading = true;
    });

    try {
      final apiService = ref.read(apiServiceProvider);
      await apiService.verifyWhatsApp(
        _phoneNumberId!,
        _otpController.text.trim(),
        widget.businessId,
      );

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('WhatsApp connected successfully!'),
            backgroundColor: AppTheme.successColor,
          ),
        );
        // Navigate to dashboard or login
        Navigator.of(context).popUntil((route) => route.isFirst);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Verification failed: $e'),
            backgroundColor: AppTheme.errorColor,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Verify WhatsApp')),
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              'Verify Your Phone',
              style: Theme.of(context).textTheme.headlineMedium,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            Text(
              'We sent a verification code to ${widget.phoneNumber}. Enter it below to connect your business.',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodyLarge,
            ),
            const SizedBox(height: 32),
            if (!_codeSent && _isLoading)
              const Center(child: CircularProgressIndicator())
            else ...[
              TextField(
                controller: _otpController,
                keyboardType: TextInputType.number,
                decoration: InputDecoration(
                  labelText: 'Verification Code',
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                  filled: true,
                ),
                textAlign: TextAlign.center,
                style: const TextStyle(fontSize: 24, letterSpacing: 8),
              ),
              const SizedBox(height: 24),
              ElevatedButton(
                onPressed: _isLoading ? null : _verifyCode,
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  backgroundColor: AppTheme.primaryColor,
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                child: _isLoading
                    ? const SizedBox(
                        height: 24,
                        width: 24,
                        child: CircularProgressIndicator(color: Colors.white),
                      )
                    : const Text(
                        'Verify & Connect',
                        style: TextStyle(fontSize: 18),
                      ),
              ),
              const SizedBox(height: 16),
              TextButton(
                onPressed: _isLoading ? null : _sendCode,
                child: const Text('Resend Code'),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
