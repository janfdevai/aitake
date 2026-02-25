import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'theme/app_theme.dart';
import 'screens/login_screen.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:flutter/foundation.dart';
import 'dart:io';
import 'package:purchases_flutter/purchases_flutter.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  await dotenv.load(fileName: "assets/env");

  await Supabase.initialize(
    url: dotenv.env['SUPABASE_URL'] ?? '',
    anonKey: dotenv.env['SUPABASE_ANON_KEY'] ?? '',
  );

  if (!kIsWeb) {
    await Purchases.setLogLevel(LogLevel.debug);
    PurchasesConfiguration? configuration;

    if (Platform.isAndroid) {
      configuration = PurchasesConfiguration(
        dotenv.env['REVENUECAT_ANDROID_KEY'] ??
            dotenv.env['REVENUECAT_API_KEY'] ??
            'mock_key',
      );
    } else if (Platform.isIOS) {
      configuration = PurchasesConfiguration(
        dotenv.env['REVENUECAT_IOS_KEY'] ??
            dotenv.env['REVENUECAT_API_KEY'] ??
            'mock_key',
      );
    }

    if (configuration != null) {
      await Purchases.configure(configuration);
    }
  }

  runApp(const ProviderScope(child: MainApp()));
}

class MainApp extends StatelessWidget {
  const MainApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'AIOTake CRM',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      home: const LoginScreen(),
    );
  }
}
