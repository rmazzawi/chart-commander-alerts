import 'package:flutter/material.dart';

import '../models.dart';
import '../theme.dart';
import '../widgets/common.dart';

/// Profile form. Used for first launch and for editing later.
class OnboardingScreen extends StatefulWidget {
  final Profile? edit;
  const OnboardingScreen({super.key, this.edit});
  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  final _form = GlobalKey<FormState>();
  late final _name = TextEditingController(text: widget.edit?.name);
  late final _age = TextEditingController(text: widget.edit?.age.toString());
  late final _height = TextEditingController(text: widget.edit?.heightCm.round().toString());
  late final _weight = TextEditingController(text: widget.edit?.startWeight.toString());
  late final _target = TextEditingController(text: widget.edit?.targetWeight.toString());
  late Sex _sex = widget.edit?.sex ?? Sex.male;
  late Activity _activity = widget.edit?.activity ?? Activity.light;
  late Goal _goal = widget.edit?.goal ?? Goal.lose;

  String? _num(String? v, double min, double max) {
    final n = double.tryParse(v ?? '');
    if (n == null) return 'أدخل رقماً';
    if (n < min || n > max) return 'القيمة بين ${min.round()} و ${max.round()}';
    return null;
  }

  Future<void> _save() async {
    if (!_form.currentState!.validate()) return;
    final s = AppScope.of(context);
    final weight = double.parse(_weight.text);
    await s.saveProfile(Profile(
      name: _name.text.trim(),
      age: int.parse(_age.text),
      sex: _sex,
      heightCm: double.parse(_height.text),
      startWeight: widget.edit?.startWeight ?? weight,
      targetWeight: double.parse(_target.text),
      activity: _activity,
      goal: _goal,
      createdAt: widget.edit?.createdAt ?? DateTime.now(),
    ));
    if (widget.edit != null && mounted) Navigator.pop(context);
  }

  @override
  Widget build(BuildContext context) {
    final editing = widget.edit != null;
    return Scaffold(
      body: CustomScrollView(slivers: [
        SliverToBoxAdapter(
          child: Container(
            padding: const EdgeInsets.fromLTRB(24, 70, 24, 36),
            decoration: const BoxDecoration(
              gradient: C.heroGradient,
              borderRadius: BorderRadius.vertical(bottom: Radius.circular(36)),
            ),
            child: Column(children: [
              const Text('🥗', style: TextStyle(fontSize: 60)),
              Text(editing ? 'تعديل الملف الشخصي' : 'أهلاً بك في سُعرة',
                  style: const TextStyle(color: Colors.white, fontSize: 28, fontWeight: FontWeight.w800)),
              const SizedBox(height: 6),
              const Text('صوّر طبقك… واعرف سعراته فوراً.\nمصمم للمطبخ العربي 🇸🇦🇪🇬🇯🇴🇲🇦🇮🇶',
                  textAlign: TextAlign.center, style: TextStyle(color: Colors.white70, fontSize: 15)),
              if (!editing) ...[
                const SizedBox(height: 14),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                  decoration: BoxDecoration(gradient: C.goldGradient, borderRadius: BorderRadius.circular(30)),
                  child: const Text('🎁 مجاني بالكامل للسنة الأولى',
                      style: TextStyle(fontWeight: FontWeight.w800, color: C.emeraldDark)),
                ),
              ],
            ]),
          ),
        ),
        SliverPadding(
          padding: const EdgeInsets.all(20),
          sliver: SliverToBoxAdapter(
            child: Form(
              key: _form,
              child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                TextFormField(
                  controller: _name,
                  decoration: const InputDecoration(labelText: 'الاسم', prefixIcon: Icon(Icons.person_outline)),
                  validator: (v) => (v ?? '').trim().isEmpty ? 'أدخل اسمك' : null,
                ),
                const SizedBox(height: 14),
                SegmentedButton<Sex>(
                  segments: const [
                    ButtonSegment(value: Sex.male, label: Text('ذكر'), icon: Icon(Icons.male)),
                    ButtonSegment(value: Sex.female, label: Text('أنثى'), icon: Icon(Icons.female)),
                  ],
                  selected: {_sex},
                  onSelectionChanged: (v) => setState(() => _sex = v.first),
                ),
                const SizedBox(height: 14),
                Row(children: [
                  Expanded(
                      child: TextFormField(
                          controller: _age,
                          keyboardType: TextInputType.number,
                          decoration: const InputDecoration(labelText: 'العمر'),
                          validator: (v) => _num(v, 12, 100))),
                  const SizedBox(width: 12),
                  Expanded(
                      child: TextFormField(
                          controller: _height,
                          keyboardType: TextInputType.number,
                          decoration: const InputDecoration(labelText: 'الطول (سم)'),
                          validator: (v) => _num(v, 120, 230))),
                ]),
                const SizedBox(height: 14),
                Row(children: [
                  Expanded(
                      child: TextFormField(
                          controller: _weight,
                          enabled: !editing,
                          keyboardType: const TextInputType.numberWithOptions(decimal: true),
                          decoration: const InputDecoration(labelText: 'الوزن اليوم (كغ)'),
                          validator: (v) => _num(v, 30, 300))),
                  const SizedBox(width: 12),
                  Expanded(
                      child: TextFormField(
                          controller: _target,
                          keyboardType: const TextInputType.numberWithOptions(decimal: true),
                          decoration: const InputDecoration(labelText: 'الوزن المستهدف'),
                          validator: (v) => _num(v, 30, 300))),
                ]),
                const SizedBox(height: 20),
                const Text('مستوى النشاط', style: TextStyle(fontWeight: FontWeight.w700)),
                Wrap(
                  spacing: 8,
                  children: Activity.values
                      .map((a) => ChoiceChip(
                            label: Text(a.ar),
                            selected: _activity == a,
                            onSelected: (_) => setState(() => _activity = a),
                          ))
                      .toList(),
                ),
                const SizedBox(height: 14),
                const Text('هدفك', style: TextStyle(fontWeight: FontWeight.w700)),
                Wrap(
                  spacing: 8,
                  children: Goal.values
                      .map((g) => ChoiceChip(
                            label: Text(g.ar),
                            selected: _goal == g,
                            onSelected: (_) => setState(() => _goal = g),
                          ))
                      .toList(),
                ),
                const SizedBox(height: 28),
                FilledButton(onPressed: _save, child: Text(editing ? 'حفظ' : 'ابدأ رحلتك 🚀')),
                const SizedBox(height: 12),
                const Text(
                  'تنبيه: التطبيق للإرشاد العام ولا يغني عن استشارة الطبيب أو أخصائي التغذية.',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 12, color: Colors.black45),
                ),
              ]),
            ),
          ),
        ),
      ]),
    );
  }
}
