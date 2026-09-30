import 'package:flutter/material.dart';
import 'package:in_app_purchase/in_app_purchase.dart';

import '../main.dart' show subscription;
import '../services/subscription.dart';
import '../theme.dart';
import '../widgets/common.dart';

class PaywallScreen extends StatelessWidget {
  /// True when the free year is over and the app is locked.
  final bool locked;
  const PaywallScreen({super.key, this.locked = false});

  @override
  Widget build(BuildContext context) {
    final s = AppScope.of(context);
    final products = [...subscription.products]
      ..sort((a, b) => a.id == Subscription.yearlyId ? -1 : 1);
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(gradient: C.heroGradient),
        child: SafeArea(
          child: ListView(padding: const EdgeInsets.all(24), children: [
            if (!locked)
              Align(
                alignment: AlignmentDirectional.centerStart,
                child: IconButton(
                    onPressed: () => Navigator.pop(context),
                    icon: const Icon(Icons.close, color: Colors.white)),
              ),
            const SizedBox(height: 10),
            const Center(child: Text('👑', style: TextStyle(fontSize: 70))),
            const Text('سُعرة بريميوم',
                textAlign: TextAlign.center,
                style: TextStyle(color: Colors.white, fontSize: 32, fontWeight: FontWeight.w800)),
            const SizedBox(height: 6),
            Text(
              locked
                  ? 'انتهت سنتك المجانية 🎉 شكراً لثقتك! اشترك لمواصلة رحلتك.'
                  : s.premium
                      ? 'أنت مشترك في بريميوم ✅'
                      : 'متبقٍ ${s.trialDaysLeft} يوماً من سنتك المجانية',
              textAlign: TextAlign.center,
              style: const TextStyle(color: Colors.white70, fontSize: 16),
            ),
            const SizedBox(height: 26),
            for (final f in const [
              '📸 تحليل غير محدود لصور الأطباق بالذكاء الاصطناعي',
              '🍛 أكبر قاعدة بيانات للأطباق العربية',
              '📊 تقارير أسبوعية وشهرية للتقدم والوزن',
              '🌙 وضع رمضان: سحور وإفطار',
              '🔔 تنبيهات تجاوز السعرات والماء',
            ])
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 6),
                child: Text(f, style: const TextStyle(color: Colors.white, fontSize: 16)),
              ),
            const SizedBox(height: 24),
            if (products.isEmpty)
              const Text('خيارات الاشتراك غير متاحة حالياً. تأكد من تثبيت التطبيق من متجر Google Play.',
                  textAlign: TextAlign.center, style: TextStyle(color: Colors.white70)),
            for (final p in products) _PlanTile(p),
            const SizedBox(height: 10),
            TextButton(
              onPressed: subscription.restore,
              child: const Text('استعادة المشتريات', style: TextStyle(color: Colors.white)),
            ),
            const Text('يتجدد الاشتراك تلقائياً ويمكن إلغاؤه في أي وقت من Google Play.',
                textAlign: TextAlign.center, style: TextStyle(color: Colors.white54, fontSize: 12)),
          ]),
        ),
      ),
    );
  }
}

class _PlanTile extends StatelessWidget {
  final ProductDetails p;
  const _PlanTile(this.p);
  @override
  Widget build(BuildContext context) {
    final yearly = p.id == Subscription.yearlyId;
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        borderRadius: BorderRadius.circular(20),
        onTap: () => subscription.buy(p),
        child: Container(
          padding: const EdgeInsets.all(18),
          decoration: BoxDecoration(
            gradient: yearly ? C.goldGradient : null,
            color: yearly ? null : Colors.white24,
            borderRadius: BorderRadius.circular(20),
          ),
          child: Row(children: [
            Expanded(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(yearly ? 'سنوي — الأفضل قيمة' : 'شهري',
                    style: TextStyle(
                        fontWeight: FontWeight.w800, fontSize: 17, color: yearly ? C.emeraldDark : Colors.white)),
                if (yearly)
                  const Text('وفّر أكثر من 40٪', style: TextStyle(color: C.emeraldDark)),
              ]),
            ),
            Text(p.price,
                style: TextStyle(
                    fontWeight: FontWeight.w800, fontSize: 18, color: yearly ? C.emeraldDark : Colors.white)),
          ]),
        ),
      ),
    );
  }
}
