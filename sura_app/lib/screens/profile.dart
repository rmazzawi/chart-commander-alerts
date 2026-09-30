import 'package:flutter/material.dart';
import 'package:share_plus/share_plus.dart';

import '../models.dart';
import '../theme.dart';
import '../widgets/common.dart';
import 'onboarding.dart';
import 'paywall.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final s = AppScope.of(context);
    final p = s.profile!;
    return Scaffold(
      appBar: AppBar(title: const Text('حسابي')),
      body: ListView(padding: const EdgeInsets.fromLTRB(16, 0, 16, 100), children: [
        Glass(
          child: Row(children: [
            CircleAvatar(
              radius: 32,
              backgroundColor: C.emerald,
              child: Text(p.name.characters.first,
                  style: const TextStyle(fontSize: 28, color: Colors.white, fontWeight: FontWeight.w800)),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(p.name, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800)),
                Text('${p.sex == Sex.male ? 'ذكر' : 'أنثى'} · ${p.age} سنة · ${p.heightCm.round()} سم'),
                Text('${p.goal.ar} · ${s.dailyTarget} سعرة/يوم', style: const TextStyle(color: C.emerald)),
              ]),
            ),
            IconButton(
              icon: const Icon(Icons.edit_outlined),
              onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => OnboardingScreen(edit: p))),
            ),
          ]),
        ),
        const SizedBox(height: 16),
        InkWell(
          borderRadius: BorderRadius.circular(24),
          onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const PaywallScreen())),
          child: Glass(
            gradient: C.goldGradient,
            child: Row(children: [
              const Text('👑', style: TextStyle(fontSize: 32)),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  s.premium ? 'مشترك في بريميوم' : 'السنة المجانية: باقي ${s.trialDaysLeft} يوماً',
                  style: const TextStyle(fontWeight: FontWeight.w800, color: C.emeraldDark, fontSize: 16),
                ),
              ),
              const Icon(Icons.chevron_left, color: C.emeraldDark),
            ]),
          ),
        ),
        const SizedBox(height: 16),
        Glass(
          padding: const EdgeInsets.symmetric(vertical: 6),
          child: Column(children: [
            SwitchListTile(
              value: s.ramadanMode,
              onChanged: s.setRamadan,
              secondary: const Text('🌙', style: TextStyle(fontSize: 24)),
              title: const Text('وضع رمضان'),
              subtitle: const Text('وجبات السحور والإفطار'),
            ),
            ListTile(
              leading: const Text('📣', style: TextStyle(fontSize: 24)),
              title: const Text('ادعُ أصدقاءك'),
              subtitle: const Text('شارك التطبيق على فيسبوك وإنستغرام وواتساب'),
              onTap: () => SharePlus.instance.share(ShareParams(
                text: 'جرّب تطبيق سُعرة 🥗 صوّر طبقك واعرف سعراته — مصمم للأكل العربي ومجاني لسنة كاملة!\n'
                    'https://play.google.com/store/apps/details?id=com.sura.sura',
              )),
            ),
            ListTile(
              leading: const Text('🗑️', style: TextStyle(fontSize: 24)),
              title: const Text('حذف كل البيانات'),
              onTap: () async {
                final ok = await showDialog<bool>(
                  context: context,
                  builder: (ctx) => AlertDialog(
                    title: const Text('هل أنت متأكد؟'),
                    content: const Text('سيتم حذف ملفك وكل سجلاتك نهائياً.'),
                    actions: [
                      TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('إلغاء')),
                      FilledButton(
                        style: FilledButton.styleFrom(backgroundColor: C.coral),
                        onPressed: () => Navigator.pop(ctx, true),
                        child: const Text('حذف'),
                      ),
                    ],
                  ),
                );
                if (ok == true) await s.resetAll();
              },
            ),
          ]),
        ),
        const SizedBox(height: 16),
        const Text('القيم تقديرية وللإرشاد فقط ولا تغني عن استشارة مختص.',
            textAlign: TextAlign.center, style: TextStyle(color: Colors.black38, fontSize: 12)),
      ]),
    );
  }
}
