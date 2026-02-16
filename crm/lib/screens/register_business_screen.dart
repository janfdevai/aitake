import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/providers.dart';
import '../theme/app_theme.dart';

class RegisterBusinessScreen extends ConsumerStatefulWidget {
  const RegisterBusinessScreen({super.key});

  @override
  ConsumerState<RegisterBusinessScreen> createState() =>
      _RegisterBusinessScreenState();
}

class _RegisterBusinessScreenState
    extends ConsumerState<RegisterBusinessScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _managerNameController = TextEditingController();
  final _emailController = TextEditingController();
  final _addressController = TextEditingController();
  final _phoneController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _isLoading = false;
  bool _obscurePassword = true;

  @override
  void dispose() {
    _nameController.dispose();
    _managerNameController.dispose();
    _emailController.dispose();
    _addressController.dispose();
    _phoneController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Register Business')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Create Your Business Profile',
                style: Theme.of(
                  context,
                ).textTheme.displayLarge?.copyWith(fontSize: 28),
              ),
              const SizedBox(height: 8),
              Text(
                'Join the FastOrder platform and start taking orders.',
                style: Theme.of(context).textTheme.bodyMedium,
              ),
              const SizedBox(height: 32),
              _sectionHeader('Manager Information'),
              const SizedBox(height: 16),
              _buildTextField(
                'Your Full Name',
                Icons.person_outline,
                _managerNameController,
                validator: (v) => v!.isEmpty ? 'Name is required' : null,
              ),
              const SizedBox(height: 16),
              _buildTextField(
                'Email Address',
                Icons.email_outlined,
                _emailController,
                keyboardType: TextInputType.emailAddress,
                validator: (v) => v!.isEmpty || !v.contains('@')
                    ? 'Valid email required'
                    : null,
              ),
              const SizedBox(height: 16),
              _buildTextField(
                'Create Password',
                Icons.lock_outline,
                _passwordController,
                obscureText: _obscurePassword,
                suffixIcon: IconButton(
                  icon: Icon(
                    _obscurePassword ? Icons.visibility_off : Icons.visibility,
                  ),
                  onPressed: () {
                    setState(() {
                      _obscurePassword = !_obscurePassword;
                    });
                  },
                ),
                validator: (v) =>
                    v!.isEmpty || v.length < 6 ? 'Min 6 characters' : null,
              ),
              const SizedBox(height: 32),
              _sectionHeader('Business Information'),
              const SizedBox(height: 16),
              _buildTextField(
                'Business Name',
                Icons.business,
                _nameController,
                validator: (v) =>
                    v!.isEmpty ? 'Business name is required' : null,
              ),
              const SizedBox(height: 16),
              _buildTextField(
                'Address',
                Icons.location_on_outlined,
                _addressController,
                validator: (v) => v!.isEmpty ? 'Address is required' : null,
              ),
              const SizedBox(height: 16),
              _buildTextField(
                'WhatsApp Phone',
                Icons.phone_android,
                _phoneController,
                keyboardType: TextInputType.phone,
                validator: (v) => v!.isEmpty ? 'Phone is required' : null,
              ),
              const SizedBox(height: 40),
              SizedBox(
                width: double.infinity,
                height: 56,
                child: ElevatedButton(
                  onPressed: _isLoading ? null : _handleRegister,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppTheme.primaryColor,
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(16),
                    ),
                  ),
                  child: _isLoading
                      ? const SizedBox(
                          height: 24,
                          width: 24,
                          child: CircularProgressIndicator(
                            color: Colors.white,
                            strokeWidth: 2,
                          ),
                        )
                      : const Text(
                          'Register & Continue',
                          style: TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _sectionHeader(String title) {
    return Text(
      title,
      style: Theme.of(context).textTheme.titleMedium?.copyWith(
        color: AppTheme.primaryColor,
        fontWeight: FontWeight.bold,
      ),
    );
  }

  Widget _buildTextField(
    String label,
    IconData icon,
    TextEditingController controller, {
    String? Function(String?)? validator,
    TextInputType? keyboardType,
    bool obscureText = false,
    Widget? suffixIcon,
  }) {
    return TextFormField(
      controller: controller,
      validator: validator,
      keyboardType: keyboardType,
      obscureText: obscureText,
      decoration: InputDecoration(
        labelText: label,
        prefixIcon: Icon(icon),
        suffixIcon: suffixIcon,
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(16)),
        filled: true,
        fillColor: Colors.white,
      ),
    );
  }

  void _handleRegister() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _isLoading = true;
    });

    try {
      final apiService = ref.read(apiServiceProvider);

      final email = _emailController.text.trim();
      final password = _passwordController.text.trim();

      // 1. Register in Supabase Auth
      final authResponse = await apiService.register(email, password);
      final user = authResponse.user;

      if (user == null) throw Exception('Auth registration failed');

      // 2. Create Manager in Database
      final managerData = {
        'full_name': _managerNameController.text.trim(),
        'email': email,
        'auth_user_id': user.id,
      };

      final manager = await apiService.createManager(managerData);

      // 2. Create Business linked to manager
      final businessData = {
        'name': _nameController.text.trim(),
        'address': _addressController.text.trim(),
        'whatsapp_phone_number': _phoneController.text.trim(),
      };

      await apiService.createBusiness(
        businessData,
        managerId: manager.managerId,
      );

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Registration successful! Please login.'),
            backgroundColor: AppTheme.successColor,
          ),
        );
        Navigator.pop(context);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Registration failed: $e'),
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
}
