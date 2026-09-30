import 'dart:io';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:path_provider/path_provider.dart';

import '../data/arab_foods.dart';
import '../models.dart';
import '../services/ai_vision.dart';
import '../theme.dart';
import '../widgets/common.dart';

MealType guessMeal(bool ramadan) {
  final h = DateTime.now().hour;
  if (ramadan) return h < 6 ? MealType.suhoor : (h >= 17 ? MealType.iftar : MealType.snack);
  if (h >= 5 && h < 11) return MealType.breakfast;
  if (h >= 12 && h < 17) return MealType.lunch;
  if (h >= 19 && h < 23) return MealType.dinner;
  return MealType.snack;
}

void showAddFoodSheet(BuildContext context) {
  showModalBottomSheet(
    context: context,
    backgroundColor: Colors.white,
    shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(28))),
    builder: (ctx) => SafeArea(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          const Text('أضف وجبة', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800)),
          const SizedBox(height: 16),
          _Option('📸', 'صوّر طبقك', 'الذكاء الاصطناعي يحسب السعرات', () {
            Navigator.pop(ctx);
            _pick(context, ImageSource.camera);
          }),
          _Option('🖼️', 'اختر من المعرض', 'صورة محفوظة لطبق', () {
            Navigator.pop(ctx);
            _pick(context, ImageSource.gallery);
          }),
          _Option('🔍', 'ابحث في الأطباق العربية', '${arabDishes.length}+ طبق من كل الدول العربية', () {
            Navigator.pop(ctx);
            Navigator.push(context, MaterialPageRoute(builder: (_) => const DishSearchScreen()));
          }),
        ]),
      ),
    ),
  );
}

Future<void> _pick(BuildContext context, ImageSource src) async {
  final x = await ImagePicker().pickImage(source: src, maxWidth: 1280, imageQuality: 80);
  if (x == null || !context.mounted) return;
  // Copy into app storage so the thumbnail survives cache clears.
  final dir = await getApplicationDocumentsDirectory();
  final saved = await File(x.path).copy('${dir.path}/meal_${DateTime.now().millisecondsSinceEpoch}.jpg');
  if (!context.mounted) return;
  Navigator.push(context, MaterialPageRoute(builder: (_) => AnalyzeScreen(photo: saved)));
}

class _Option extends StatelessWidget {
  final String emoji, title, sub;
  final VoidCallback onTap;
  const _Option(this.emoji, this.title, this.sub, this.onTap);
  @override
  Widget build(BuildContext context) => Card(
        elevation: 0,
        color: C.bg,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
        child: ListTile(
          onTap: onTap,
          leading: Text(emoji, style: const TextStyle(fontSize: 30)),
          title: Text(title, style: const TextStyle(fontWeight: FontWeight.w800)),
          subtitle: Text(sub),
          trailing: const Icon(Icons.chevron_left),
        ),
      );
}

/// Shows the photo, runs AI detection, lets the user adjust, then saves.
class AnalyzeScreen extends StatefulWidget {
  final File photo;
  const AnalyzeScreen({super.key, required this.photo});
  @override
  State<AnalyzeScreen> createState() => _AnalyzeScreenState();
}

class _AnalyzeScreenState extends State<AnalyzeScreen> {
  List<DetectedDish>? _dishes;
  String? _error;

  @override
  void initState() {
    super.initState();
    _run();
  }

  Future<void> _run() async {
    setState(() => _error = null);
    try {
      final r = await AiVision.analyze(widget.photo);
      if (mounted) setState(() => _dishes = r);
    } catch (e) {
      if (mounted) setState(() => _error = e.toString().replaceFirst('Exception: ', ''));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      extendBodyBehindAppBar: true,
      appBar: AppBar(foregroundColor: Colors.white),
      body: Column(children: [
        Stack(children: [
          Image.file(widget.photo, height: 320, width: double.infinity, fit: BoxFit.cover),
          Container(
            height: 320,
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [Colors.black54, Colors.transparent, Colors.black26]),
            ),
          ),
        ]),
        Expanded(child: _body()),
      ]),
    );
  }

  Widget _body() {
    if (_error != null) {
      return Padding(
        padding: const EdgeInsets.all(24),
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          const Text('😕', textAlign: TextAlign.center, style: TextStyle(fontSize: 48)),
          Text(_error!, textAlign: TextAlign.center),
          const SizedBox(height: 16),
          if (AiVision.configured) OutlinedButton(onPressed: _run, child: const Text('إعادة المحاولة')),
          const SizedBox(height: 8),
          FilledButton(
            onPressed: () => Navigator.pushReplacement(context,
                MaterialPageRoute(builder: (_) => DishSearchScreen(photoPath: widget.photo.path))),
            child: const Text('اختر الطبق يدوياً'),
          ),
        ]),
      );
    }
    if (_dishes == null) {
      return const Center(
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          CircularProgressIndicator(color: C.emerald),
          SizedBox(height: 16),
          Text('جارٍ تحليل طبقك… 🍽️', style: TextStyle(fontWeight: FontWeight.w700)),
        ]),
      );
    }
    if (_dishes!.isEmpty) {
      _error = 'لم نتعرف على طعام في الصورة';
      return _body();
    }
    return ListView(padding: const EdgeInsets.all(16), children: [
      const Text('وجدنا في طبقك:', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
      for (final d in _dishes!)
        Card(
          elevation: 0,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
          child: ListTile(
            title: Text(d.name, style: const TextStyle(fontWeight: FontWeight.w800)),
            subtitle: Text(d.portion),
            trailing: Text('${d.kcal} سعرة', style: const TextStyle(color: C.emerald, fontWeight: FontWeight.w800)),
            onTap: () => _confirm(d.name, d.kcal, d.protein, d.carbs, d.fat),
          ),
        ),
      const SizedBox(height: 12),
      FilledButton(
        onPressed: () {
          final t = _dishes!;
          _confirm(
            t.map((d) => d.name).join(' + '),
            t.fold(0, (a, d) => a + d.kcal),
            t.fold(0.0, (a, d) => a + d.protein),
            t.fold(0.0, (a, d) => a + d.carbs),
            t.fold(0.0, (a, d) => a + d.fat),
          );
        },
        child: Text('أضف الكل (${_dishes!.fold<int>(0, (a, d) => a + d.kcal)} سعرة)'),
      ),
    ]);
  }

  void _confirm(String name, int kcal, double p, double c, double f) =>
      confirmAndSave(context, name: name, kcal: kcal, p: p, c: c, f: f, photoPath: widget.photo.path, popCount: 1);
}

/// Bottom sheet to choose portion + meal, then saves and alerts if over.
Future<void> confirmAndSave(BuildContext context,
    {required String name,
    required int kcal,
    required double p,
    required double c,
    required double f,
    String? photoPath,
    int popCount = 1}) async {
  final s = AppScope.of(context);
  final nav = Navigator.of(context);
  var meal = guessMeal(s.ramadanMode);
  var mult = 1.0;
  final ok = await showModalBottomSheet<bool>(
    context: context,
    isScrollControlled: true,
    shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(28))),
    builder: (ctx) => StatefulBuilder(
      builder: (ctx, set) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            Text(name, textAlign: TextAlign.center, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800)),
            Text('${(kcal * mult).round()} سعرة',
                textAlign: TextAlign.center, style: const TextStyle(fontSize: 34, fontWeight: FontWeight.w800, color: C.emerald)),
            const SizedBox(height: 8),
            const Text('حجم الحصة', textAlign: TextAlign.center),
            Wrap(
              alignment: WrapAlignment.center,
              spacing: 8,
              children: [0.5, 0.75, 1.0, 1.5, 2.0]
                  .map((m) => ChoiceChip(
                        label: Text(m == 1 ? 'عادية' : '×$m'),
                        selected: mult == m,
                        onSelected: (_) => set(() => mult = m),
                      ))
                  .toList(),
            ),
            const SizedBox(height: 12),
            const Text('نوع الوجبة', textAlign: TextAlign.center),
            Wrap(
              alignment: WrapAlignment.center,
              spacing: 8,
              children: (s.ramadanMode
                      ? [MealType.suhoor, MealType.iftar, MealType.snack]
                      : [MealType.breakfast, MealType.lunch, MealType.dinner, MealType.snack])
                  .map((m) => ChoiceChip(
                        label: Text('${m.emoji} ${m.ar}'),
                        selected: meal == m,
                        onSelected: (_) => set(() => meal = m),
                      ))
                  .toList(),
            ),
            const SizedBox(height: 20),
            FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('حفظ ✅')),
          ]),
        ),
      ),
    ),
  );
  if (ok != true || !context.mounted) return;
  final entry = FoodEntry(
    id: DateTime.now().microsecondsSinceEpoch.toString(),
    name: name,
    kcal: (kcal * mult).round(),
    protein: p * mult,
    carbs: c * mult,
    fat: f * mult,
    meal: meal,
    time: DateTime.now(),
    photoPath: photoPath,
  );
  final over = await s.addFood(entry);
  if (!nav.mounted) return;
  for (var i = 0; i < popCount; i++) {
    nav.pop();
  }
  if (over) {
    await showOverLimitAlert(nav.context, s.kcalOn(DateTime.now()), s.dailyTarget);
  }
}

class DishSearchScreen extends StatefulWidget {
  final String? photoPath;
  const DishSearchScreen({super.key, this.photoPath});
  @override
  State<DishSearchScreen> createState() => _DishSearchScreenState();
}

class _DishSearchScreenState extends State<DishSearchScreen> {
  String _q = '';
  String? _cat;

  @override
  Widget build(BuildContext context) {
    final list = arabDishes
        .where((d) => (_cat == null || d.category == _cat) && (_q.isEmpty || d.name.contains(_q) || d.region.contains(_q)))
        .toList();
    return Scaffold(
      appBar: AppBar(title: const Text('الأطباق العربية')),
      body: Column(children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: TextField(
            decoration: const InputDecoration(hintText: 'ابحث: كبسة، منسف، كشري…', prefixIcon: Icon(Icons.search)),
            onChanged: (v) => setState(() => _q = v.trim()),
          ),
        ),
        SizedBox(
          height: 56,
          child: ListView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            children: [
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 4),
                child: ChoiceChip(label: const Text('الكل'), selected: _cat == null, onSelected: (_) => setState(() => _cat = null)),
              ),
              for (final c in dishCategories)
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 4),
                  child: ChoiceChip(label: Text(c), selected: _cat == c, onSelected: (_) => setState(() => _cat = c)),
                ),
            ],
          ),
        ),
        Expanded(
          child: ListView.builder(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 24),
            itemCount: list.length + 1,
            itemBuilder: (_, i) {
              if (i == list.length) {
                return TextButton.icon(
                  onPressed: _custom,
                  icon: const Icon(Icons.add),
                  label: const Text('طبق غير موجود؟ أضفه يدوياً'),
                );
              }
              final d = list[i];
              return Card(
                elevation: 0,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
                child: ListTile(
                  title: Text(d.name, style: const TextStyle(fontWeight: FontWeight.w700)),
                  subtitle: Text('${d.region} · ${d.serving}'),
                  trailing: Text('${d.kcal}', style: const TextStyle(color: C.emerald, fontWeight: FontWeight.w800, fontSize: 16)),
                  onTap: () => confirmAndSave(context,
                      name: d.name, kcal: d.kcal, p: d.protein, c: d.carbs, f: d.fat, photoPath: widget.photoPath),
                ),
              );
            },
          ),
        ),
      ]),
    );
  }

  Future<void> _custom() async {
    final name = TextEditingController();
    final kcal = TextEditingController();
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('طبق مخصص'),
        content: Column(mainAxisSize: MainAxisSize.min, children: [
          TextField(controller: name, decoration: const InputDecoration(labelText: 'اسم الطبق')),
          const SizedBox(height: 10),
          TextField(controller: kcal, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'السعرات')),
        ]),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('إلغاء')),
          FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('متابعة')),
        ],
      ),
    );
    final k = int.tryParse(kcal.text);
    if (ok == true && k != null && name.text.trim().isNotEmpty && mounted) {
      await confirmAndSave(context, name: name.text.trim(), kcal: k, p: 0, c: 0, f: 0, photoPath: widget.photoPath);
    }
  }
}
