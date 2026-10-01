import 'dart:io';

import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';

import '../models.dart';
import '../nutrition.dart';
import '../theme.dart';
import '../widgets/common.dart';

/// Full nutrition breakdown for one food entry or a whole day.
class NutritionScreen extends StatelessWidget {
  final String title;
  final String? subtitle;
  final String? photoPath;
  final int kcal;
  final double protein, carbs, fat;
  final Map<String, double> nutrients;
  final bool isDay;

  const NutritionScreen._(this.title, this.subtitle, this.photoPath, this.kcal, this.protein, this.carbs,
      this.fat, this.nutrients, this.isDay);

  factory NutritionScreen.entry(FoodEntry e) => NutritionScreen._(
      e.name,
      '${e.meal.emoji} ${e.meal.ar}${e.grams > 0 ? ' · ${e.grams.round()}غ' : ''}',
      e.photoPath,
      e.kcal,
      e.protein,
      e.carbs,
      e.fat,
      e.nutrients,
      false);

  factory NutritionScreen.day(List<FoodEntry> items) => NutritionScreen._(
      'تحليل اليوم',
      '${items.length} أصناف',
      null,
      items.fold(0, (a, e) => a + e.kcal),
      items.fold(0.0, (a, e) => a + e.protein),
      items.fold(0.0, (a, e) => a + e.carbs),
      items.fold(0.0, (a, e) => a + e.fat),
      sumNutrients(items.map((e) => e.nutrients)),
      true);

  List<String> _insights() {
    final out = <String>[];
    double pct(String k) =>
        (nutrients[k] ?? 0) / allNutrients.firstWhere((n) => n.key == k).dailyValue * 100;
    final scale = isDay ? 1.0 : 3.0; // a single meal ≈ a third of the day
    if (pct('sodium') * scale > 100) out.add('🧂 الملح مرتفع — اشرب ماءً أكثر وقلّل المخللات والمرق الجاهز.');
    if (pct('sugar') * scale > 100) out.add('🍬 السكريات مرتفعة — جرّب تقليل الحلويات والعصائر المحلّاة.');
    if (pct('satFat') * scale > 100) out.add('🧈 الدهون المشبعة مرتفعة — اختر المشوي بدل المقلي.');
    if (kcal > 0 && protein * 4 / kcal >= .25) out.add('💪 ممتاز! نسبة بروتين عالية تساعد على الشبع وبناء العضلات.');
    if (pct('fiber') * scale >= 100) out.add('🥦 رائع! ألياف جيدة لصحة الهضم.');
    if (isDay && pct('vitC') < 50) out.add('🍊 فيتامين C منخفض اليوم — أضف فاكهة أو سلطة.');
    if (isDay && pct('calcium') < 50) out.add('🥛 الكالسيوم منخفض — أضف لبناً أو لبنة أو جبنة.');
    return out;
  }

  @override
  Widget build(BuildContext context) {
    final macroKcal = protein * 4 + carbs * 4 + fat * 9;
    final insights = _insights();
    return Scaffold(
      appBar: AppBar(title: Text(title)),
      body: ListView(padding: const EdgeInsets.fromLTRB(16, 0, 16, 32), children: [
        if (photoPath != null && File(photoPath!).existsSync())
          Padding(
            padding: const EdgeInsets.only(bottom: 16),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(24),
              child: Image.file(File(photoPath!), height: 200, fit: BoxFit.cover),
            ),
          ),
        Glass(
          gradient: C.heroGradient,
          child: Row(children: [
            SizedBox(
              width: 130,
              height: 130,
              child: Stack(alignment: Alignment.center, children: [
                PieChart(PieChartData(
                  sectionsSpace: 3,
                  centerSpaceRadius: 42,
                  sections: macroKcal == 0
                      ? [PieChartSectionData(value: 1, color: Colors.white24, radius: 16, showTitle: false)]
                      : [
                          PieChartSectionData(value: protein * 4, color: C.protein, radius: 16, showTitle: false),
                          PieChartSectionData(value: carbs * 4, color: C.carbs, radius: 16, showTitle: false),
                          PieChartSectionData(value: fat * 9, color: C.fat, radius: 16, showTitle: false),
                        ],
                )),
                Column(mainAxisSize: MainAxisSize.min, children: [
                  Text('$kcal', style: const TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.w800)),
                  const Text('سعرة', style: TextStyle(color: Colors.white70, fontSize: 12)),
                ]),
              ]),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                if (subtitle != null) Text(subtitle!, style: const TextStyle(color: Colors.white70)),
                const SizedBox(height: 8),
                for (final (l, v, col) in [
                  ('بروتين', protein, C.protein),
                  ('كربوهيدرات', carbs, C.carbs),
                  ('دهون', fat, C.fat),
                ])
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 3),
                    child: Row(children: [
                      Container(width: 10, height: 10, decoration: BoxDecoration(color: col, shape: BoxShape.circle)),
                      const SizedBox(width: 8),
                      Expanded(child: Text(l, style: const TextStyle(color: Colors.white))),
                      Text('${v.toStringAsFixed(1)}غ',
                          style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w800)),
                      const SizedBox(width: 6),
                      Text(
                          macroKcal == 0
                              ? ''
                              : '${((l == 'دهون' ? v * 9 : v * 4) / macroKcal * 100).round()}٪',
                          style: const TextStyle(color: Colors.white70, fontSize: 12)),
                    ]),
                  ),
              ]),
            ),
          ]),
        ),
        if (insights.isNotEmpty) ...[
          const SizedBox(height: 16),
          Glass(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              const Text('💡 ملاحظات', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
              const SizedBox(height: 6),
              for (final t in insights)
                Padding(padding: const EdgeInsets.symmetric(vertical: 4), child: Text(t)),
            ]),
          ),
        ],
        if (nutrients.isEmpty)
          const Padding(
            padding: EdgeInsets.all(24),
            child: Text('لا توجد تفاصيل إضافية لهذا الصنف.', textAlign: TextAlign.center),
          )
        else ...[
          _Section('السكر والدهون والملح', macroNutrients, nutrients),
          _Section('المعادن', minerals, nutrients),
          _Section('الفيتامينات', vitamins, nutrients),
          const SizedBox(height: 12),
          const Text(
            'النسب من الاحتياج اليومي لشخص بالغ. القيم تقديرية للإرشاد فقط.',
            textAlign: TextAlign.center,
            style: TextStyle(color: Colors.black45, fontSize: 12),
          ),
        ],
      ]),
    );
  }
}

class _Section extends StatelessWidget {
  final String title;
  final List<Nutrient> list;
  final Map<String, double> values;
  const _Section(this.title, this.list, this.values);

  String _fmt(double v) => v >= 100 ? v.round().toString() : v.toStringAsFixed(v >= 10 ? 0 : 1);

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(top: 16),
        child: Glass(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(title, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
            const SizedBox(height: 8),
            for (final n in list) ...[
              Builder(builder: (_) {
                final v = values[n.key] ?? 0;
                final pct = v / n.dailyValue;
                final color = n.limit
                    ? (pct > .5 ? C.coral : pct > .25 ? C.gold : C.emerald)
                    : (pct >= .2 ? C.emerald : const Color(0xFF7DD3B8));
                return Padding(
                  padding: const EdgeInsets.symmetric(vertical: 6),
                  child: Column(children: [
                    Row(children: [
                      Expanded(child: Text(n.ar)),
                      Text('${_fmt(v)} ${n.unit}', style: const TextStyle(fontWeight: FontWeight.w700)),
                      SizedBox(
                        width: 52,
                        child: Text('${(pct * 100).round()}٪',
                            textAlign: TextAlign.end, style: TextStyle(color: color, fontWeight: FontWeight.w800)),
                      ),
                    ]),
                    const SizedBox(height: 4),
                    ClipRRect(
                      borderRadius: BorderRadius.circular(6),
                      child: LinearProgressIndicator(
                        value: pct.clamp(0, 1).toDouble(),
                        minHeight: 6,
                        color: color,
                        backgroundColor: C.bg,
                      ),
                    ),
                  ]),
                );
              }),
            ],
          ]),
        ),
      );
}
