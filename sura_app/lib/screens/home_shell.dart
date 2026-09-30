import 'package:flutter/material.dart';

import '../theme.dart';
import 'add_food.dart';
import 'profile.dart';
import 'progress.dart';
import 'today.dart';

class HomeShell extends StatefulWidget {
  const HomeShell({super.key});
  @override
  State<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<HomeShell> {
  int _i = 0;
  static const _pages = [TodayScreen(), ProgressScreen(), ProfileScreen()];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(index: _i, children: _pages),
      floatingActionButtonLocation: FloatingActionButtonLocation.endFloat,
      floatingActionButton: Container(
        decoration: BoxDecoration(shape: BoxShape.circle, gradient: C.goldGradient, boxShadow: [
          BoxShadow(color: C.gold.withValues(alpha: .5), blurRadius: 18, offset: const Offset(0, 6)),
        ]),
        child: FloatingActionButton(
          heroTag: 'add',
          backgroundColor: Colors.transparent,
          elevation: 0,
          shape: const CircleBorder(),
          onPressed: () => showAddFoodSheet(context),
          child: const Icon(Icons.camera_alt_rounded, color: C.emeraldDark, size: 30),
        ),
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _i,
        onDestinationSelected: (i) => setState(() => _i = i),
        backgroundColor: Colors.white,
        indicatorColor: C.emerald.withValues(alpha: .15),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.today_outlined), selectedIcon: Icon(Icons.today), label: 'اليوم'),
          NavigationDestination(
              icon: Icon(Icons.insights_outlined), selectedIcon: Icon(Icons.insights), label: 'التقدم'),
          NavigationDestination(icon: Icon(Icons.person_outline), selectedIcon: Icon(Icons.person), label: 'حسابي'),
        ],
      ),
    );
  }
}
