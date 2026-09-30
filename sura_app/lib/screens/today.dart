import 'dart:io';

import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../models.dart';
import '../theme.dart';
import '../widgets/common.dart';
import 'paywall.dart';

class TodayScreen extends StatelessWidget {
  const TodayScreen({super.key});

  String _greeting() {
    final h = DateTime.now().hour;
    if (h < 12) return 'صباح الخير';
    if (h < 18) return 'مساء الخير';
    return 'مساء النور';
  }

  @override
  Widget build(BuildContext context) {
    final s = AppScope.of(context);
    final now = DateTime.now();
    final items = s.foodsOn(now);
    final eaten = s.kcalOn(now);
    final target = s.dailyTarget;
    final p = items.fold<double>(0, (a, f) => a + f.protein);
    final c = items.fold<double>(0, (a, f) => a + f.carbs);
    final f = items.fold<double>(0, (a, f) => a + f.fat);
    final over = eaten > target;
    final meals = s.ramadanMode
        ? [MealType.suhoor, MealType.iftar, MealType.snack]
        : [MealType.breakfast, MealType.lunch, MealType.dinner, MealType.snack];

    return ListView(padding: EdgeInsets.zero, children: [
      Container(
        padding: const EdgeInsets.fromLTRB(20, 56, 20, 26),
        decoration: const BoxDecoration(
          gradient: C.heroGradient,
          borderRadius: BorderRadius.vertical(bottom: Radius.circular(36)),
        ),
        child: Column(children: [
          Row(children: [
            Expanded(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text('${_greeting()}، ${s.profile!.name} 👋',
                    style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.w800)),
                Text(DateFormat('EEEE d MMMM', 'ar').format(now), style: const TextStyle(color: Colors.white70)),
              ]),
            ),
            if (s.streak > 0)
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(color: Colors.white24, borderRadius: BorderRadius.circular(20)),
                child: Text('🔥 ${s.streak}', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w800)),
              ),
          ]),
          const SizedBox(height: 18),
          Row(mainAxisAlignment: MainAxisAlignment.spaceEvenly, children: [
            _Stat('المستهدف', '$target'),
            CalorieRing(eaten: eaten, target: target, size: 170),
            _Stat('تناولت', '$eaten'),
          ]),
          const SizedBox(height: 18),
          Row(children: [
            MacroBar('بروتين', p, target * .25 / 4, C.protein),
            const SizedBox(width: 12),
            MacroBar('كربوهيدرات', c, target * .5 / 4, C.carbs),
            const SizedBox(width: 12),
            MacroBar('دهون', f, target * .25 / 9, C.fat),
          ]),
        ]),
      ),
      if (over)
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 0),
          child: Glass(
            gradient: const LinearGradient(colors: [C.coral, Color(0xFFFF8E72)]),
            child: Row(children: [
              const Text('⚠️', style: TextStyle(fontSize: 30)),
              const SizedBox(width: 12),
              Expanded(
                child: Text('تجاوزت احتياجك اليومي بـ ${eaten - target} سعرة. حاول المشي أو اختيار وجبات أخف.',
                    style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700)),
              ),
            ]),
          ),
        ),
      if (!s.premium && s.trialDaysLeft <= 30)
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 0),
          child: InkWell(
            onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const PaywallScreen())),
            child: Glass(
              gradient: C.goldGradient,
              child: Text('👑 باقي ${s.trialDaysLeft} يوماً من السنة المجانية — اشترك الآن بخصم',
                  style: const TextStyle(fontWeight: FontWeight.w800, color: C.emeraldDark)),
            ),
          ),
        ),
      Padding(padding: const EdgeInsets.fromLTRB(16, 16, 16, 0), child: _WaterCard()),
      for (final m in meals) _MealSection(m, items.where((e) => e.meal == m).toList()),
      const SizedBox(height: 100),
    ]);
  }
}

class _Stat extends StatelessWidget {
  final String label, value;
  const _Stat(this.label, this.value);
  @override
  Widget build(BuildContext context) => Column(children: [
        Text(value, style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.w800)),
        Text(label, style: const TextStyle(color: Colors.white70, fontSize: 12)),
      ]);
}

class _WaterCard extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final s = AppScope.of(context);
    final n = s.waterOn(DateTime.now());
    return Glass(
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          const Text('💧 الماء', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
          const Spacer(),
          Text('$n / 8 أكواب', style: const TextStyle(color: Colors.black54)),
        ]),
        const SizedBox(height: 8),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: List.generate(
            8,
            (i) => GestureDetector(
              onTap: () => s.setWater(DateTime.now(), i < n ? i : i + 1),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 300),
                width: 30,
                height: 40,
                decoration: BoxDecoration(
                  color: i < n ? const Color(0xFF38BDF8) : const Color(0xFFE0F2FE),
                  borderRadius: const BorderRadius.vertical(bottom: Radius.circular(10), top: Radius.circular(4)),
                ),
              ),
            ),
          ),
        ),
      ]),
    );
  }
}

class _MealSection extends StatelessWidget {
  final MealType meal;
  final List<FoodEntry> items;
  const _MealSection(this.meal, this.items);

  @override
  Widget build(BuildContext context) {
    final s = AppScope.of(context);
    final total = items.fold<int>(0, (a, e) => a + e.kcal);
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 0),
      child: Glass(
        padding: const EdgeInsets.fromLTRB(18, 14, 18, 8),
        child: Column(children: [
          Row(children: [
            Text('${meal.emoji}  ${meal.ar}', style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
            const Spacer(),
            Text('$total سعرة', style: const TextStyle(color: C.emerald, fontWeight: FontWeight.w700)),
          ]),
          if (items.isEmpty)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 10),
              child: Text('لم تسجل شيئاً بعد', style: TextStyle(color: Colors.black38)),
            ),
          for (final e in items)
            Dismissible(
              key: ValueKey(e.id),
              direction: DismissDirection.endToStart,
              background: Container(
                alignment: AlignmentDirectional.centerEnd,
                padding: const EdgeInsets.symmetric(horizontal: 16),
                color: C.coral.withValues(alpha: .15),
                child: const Icon(Icons.delete_outline, color: C.coral),
              ),
              onDismissed: (_) => s.removeFood(e.id),
              child: ListTile(
                contentPadding: EdgeInsets.zero,
                leading: ClipRRect(
                  borderRadius: BorderRadius.circular(12),
                  child: e.photoPath != null && File(e.photoPath!).existsSync()
                      ? Image.file(File(e.photoPath!), width: 46, height: 46, fit: BoxFit.cover)
                      : Container(
                          width: 46,
                          height: 46,
                          color: C.bg,
                          alignment: Alignment.center,
                          child: const Text('🍽️', style: TextStyle(fontSize: 22))),
                ),
                title: Text(e.name, style: const TextStyle(fontWeight: FontWeight.w700)),
                subtitle: Text(
                    'ب ${e.protein.round()}غ · ك ${e.carbs.round()}غ · د ${e.fat.round()}غ · ${DateFormat.jm('ar').format(e.time)}'),
                trailing: Text('${e.kcal}', style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
              ),
            ),
        ]),
      ),
    );
  }
}
