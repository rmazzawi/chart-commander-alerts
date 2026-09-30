import 'package:flutter/material.dart';

class C {
  static const emerald = Color(0xFF0F9D7A);
  static const emeraldDark = Color(0xFF064E3B);
  static const gold = Color(0xFFE8B04B);
  static const coral = Color(0xFFFF6B6B);
  static const bg = Color(0xFFF4F7F5);
  static const ink = Color(0xFF12241F);
  static const protein = Color(0xFF5B8DEF);
  static const carbs = Color(0xFFE8B04B);
  static const fat = Color(0xFFEF6C9B);

  static const heroGradient = LinearGradient(
    colors: [Color(0xFF064E3B), Color(0xFF0F9D7A), Color(0xFF34D399)],
    begin: Alignment.topRight,
    end: Alignment.bottomLeft,
  );
  static const goldGradient = LinearGradient(
    colors: [Color(0xFFF6D365), Color(0xFFE8B04B), Color(0xFFC98A1E)],
  );
}

ThemeData buildTheme() {
  final base = ThemeData(
    useMaterial3: true,
    fontFamily: 'Cairo',
    colorScheme: ColorScheme.fromSeed(seedColor: C.emerald, surface: Colors.white),
    scaffoldBackgroundColor: C.bg,
  );
  return base.copyWith(
    textTheme: base.textTheme.apply(bodyColor: C.ink, displayColor: C.ink),
    appBarTheme: AppBarTheme(
      backgroundColor: Colors.transparent,
      elevation: 0,
      centerTitle: true,
      foregroundColor: C.ink,
      titleTextStyle: const TextStyle(fontFamily: 'Cairo', fontSize: 20, fontWeight: FontWeight.w700, color: C.ink),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: Colors.white,
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(16), borderSide: BorderSide.none),
      contentPadding: const EdgeInsets.symmetric(horizontal: 18, vertical: 16),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: C.emerald,
        minimumSize: const Size(64, 54),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
        textStyle: const TextStyle(fontFamily: 'Cairo', fontSize: 17, fontWeight: FontWeight.w700),
      ),
    ),
  );
}
