import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/date_symbol_data_local.dart';

import 'screens/home_shell.dart';
import 'screens/onboarding.dart';
import 'screens/paywall.dart';
import 'services/subscription.dart';
import 'store.dart';
import 'theme.dart';
import 'widgets/common.dart';

late Subscription subscription;

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  SystemChrome.setSystemUIOverlayStyle(const SystemUiOverlayStyle(statusBarColor: Colors.transparent));
  await initializeDateFormatting('ar');
  final state = AppState();
  await state.load();
  subscription = Subscription(state);
  subscription.init(); // fire and forget; billing may be unavailable
  runApp(SuraApp(state: state));
}

class SuraApp extends StatelessWidget {
  final AppState state;
  const SuraApp({super.key, required this.state});

  @override
  Widget build(BuildContext context) {
    return AppScope(
      state: state,
      child: MaterialApp(
        title: 'سُعرة',
        debugShowCheckedModeBanner: false,
        theme: buildTheme(),
        locale: const Locale('ar'),
        supportedLocales: const [Locale('ar')],
        localizationsDelegates: GlobalMaterialLocalizations.delegates,
        home: const _Root(),
      ),
    );
  }
}

class _Root extends StatelessWidget {
  const _Root();
  @override
  Widget build(BuildContext context) {
    final s = AppScope.of(context);
    if (s.profile == null) return const OnboardingScreen();
    if (!s.hasAccess) return const PaywallScreen(locked: true);
    return const HomeShell();
  }
}
