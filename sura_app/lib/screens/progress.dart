import 'dart:io';
import 'dart:ui' as ui;

import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:intl/intl.dart';
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';

import '../store.dart';
import '../theme.dart';
import '../widgets/common.dart';

class ProgressScreen extends StatefulWidget {
  const ProgressScreen({super.key});
  @override
  State<ProgressScreen> createState() => _ProgressScreenState();
}

class _ProgressScreenState extends State<ProgressScreen> {
  final _shareKey = GlobalKey();

  Future<void> _share() async {
    final boundary = _shareKey.currentContext!.findRenderObject() as RenderRepaintBoundary;
    final img = await boundary.toImage(pixelRatio: 3);
    final bytes = await img.toByteData(format: ui.ImageByteFormat.png);
    final dir = await getTemporaryDirectory();
    final f = await File('${dir.path}/sura_progress.png').writeAsBytes(bytes!.buffer.asUint8List());
    await SharePlus.instance.share(ShareParams(
      files: [XFile(f.path)],
      text: 'تقدمي مع تطبيق سُعرة 💪🥗 — عدّاد السعرات للمطبخ العربي #سعرة #صحة',
    ));
  }

  Future<void> _logWeight() async {
    final s = AppScope.of(context);
    final c = TextEditingController(text: s.currentWeight.toString());
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('وزن اليوم ⚖️'),
        content: TextField(
            controller: c,
            autofocus: true,
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            decoration: const InputDecoration(suffixText: 'كغ')),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('إلغاء')),
          FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('حفظ')),
        ],
      ),
    );
    final v = double.tryParse(c.text);
    if (ok == true && v != null && v > 20 && v < 400) await s.logWeight(v);
  }

  @override
  Widget build(BuildContext context) {
    final s = AppScope.of(context);
    final p = s.profile!;
    final today = dayOf(DateTime.now());
    final days = List.generate(7, (i) => today.subtract(Duration(days: 6 - i)));
    final target = s.dailyTarget;
    final lost = p.startWeight - s.currentWeight;
    final toGo = (s.currentWeight - p.targetWeight).abs();
    final logged = days.where((d) => s.foodsOn(d).isNotEmpty).toList();
    final avg = logged.isEmpty ? 0 : logged.map(s.kcalOn).reduce((a, b) => a + b) ~/ logged.length;

    return Scaffold(
      appBar: AppBar(title: const Text('تقدمي'), actions: [
        IconButton(onPressed: _share, icon: const Icon(Icons.ios_share), tooltip: 'مشاركة على فيسبوك وإنستغرام'),
      ]),
      body: ListView(padding: const EdgeInsets.fromLTRB(16, 0, 16, 100), children: [
        RepaintBoundary(
          key: _shareKey,
          child: Glass(
            gradient: C.heroGradient,
            child: Column(children: [
              Text('رحلة ${p.name}', style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w800)),
              const SizedBox(height: 12),
              Row(mainAxisAlignment: MainAxisAlignment.spaceAround, children: [
                _Big(s.currentWeight.toStringAsFixed(1), 'الوزن الحالي'),
                _Big('${lost >= 0 ? '-' : '+'}${lost.abs().toStringAsFixed(1)}', 'منذ البداية'),
                _Big(toGo.toStringAsFixed(1), 'للهدف'),
              ]),
              const SizedBox(height: 12),
              Row(mainAxisAlignment: MainAxisAlignment.spaceAround, children: [
                _Big('🔥 ${s.streak}', 'أيام متتالية'),
                _Big('$avg', 'متوسط السعرات'),
                _Big(s.bmi.toStringAsFixed(1), 'مؤشر الكتلة'),
              ]),
              const SizedBox(height: 8),
              const Text('سُعرة 🥗', style: TextStyle(color: Colors.white54)),
            ]),
          ),
        ),
        const SizedBox(height: 16),
        Glass(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Text('السعرات — آخر 7 أيام', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
            const SizedBox(height: 16),
            SizedBox(
              height: 200,
              child: BarChart(BarChartData(
                maxY: [target * 1.3, ...days.map((d) => s.kcalOn(d) * 1.1)].reduce((a, b) => a > b ? a : b),
                gridData: const FlGridData(show: false),
                borderData: FlBorderData(show: false),
                extraLinesData: ExtraLinesData(horizontalLines: [
                  HorizontalLine(y: target.toDouble(), color: C.gold, strokeWidth: 2, dashArray: [6, 4]),
                ]),
                titlesData: FlTitlesData(
                  leftTitles: const AxisTitles(),
                  rightTitles: const AxisTitles(),
                  topTitles: const AxisTitles(),
                  bottomTitles: AxisTitles(
                    sideTitles: SideTitles(
                      showTitles: true,
                      getTitlesWidget: (v, _) =>
                          Text(DateFormat.E('ar').format(days[v.toInt()]), style: const TextStyle(fontSize: 11)),
                    ),
                  ),
                ),
                barGroups: [
                  for (var i = 0; i < 7; i++)
                    BarChartGroupData(x: i, barRods: [
                      BarChartRodData(
                        toY: s.kcalOn(days[i]).toDouble(),
                        width: 18,
                        borderRadius: BorderRadius.circular(8),
                        gradient: s.kcalOn(days[i]) > target
                            ? const LinearGradient(colors: [C.coral, Color(0xFFFFA07A)], begin: Alignment.bottomCenter, end: Alignment.topCenter)
                            : const LinearGradient(colors: [C.emeraldDark, C.emerald], begin: Alignment.bottomCenter, end: Alignment.topCenter),
                      ),
                    ]),
                ],
              )),
            ),
          ]),
        ),
        const SizedBox(height: 16),
        Glass(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [
              const Text('تطور الوزن', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
              const Spacer(),
              FilledButton.tonalIcon(onPressed: _logWeight, icon: const Icon(Icons.add), label: const Text('سجل وزنك')),
            ]),
            const SizedBox(height: 16),
            SizedBox(height: 200, child: _WeightChart(s)),
          ]),
        ),
      ]),
    );
  }
}

class _Big extends StatelessWidget {
  final String v, l;
  const _Big(this.v, this.l);
  @override
  Widget build(BuildContext context) => Column(children: [
        Text(v, style: const TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.w800)),
        Text(l, style: const TextStyle(color: Colors.white70, fontSize: 12)),
      ]);
}

class _WeightChart extends StatelessWidget {
  final AppState s;
  const _WeightChart(this.s);
  @override
  Widget build(BuildContext context) {
    final w = s.weights;
    if (w.length < 2) {
      return const Center(child: Text('سجّل وزنك يومياً لترى الرسم البياني 📈', style: TextStyle(color: Colors.black45)));
    }
    final t0 = w.first.date;
    final spots = w.map((e) => FlSpot(e.date.difference(t0).inDays.toDouble(), e.kg)).toList();
    final ys = [...w.map((e) => e.kg), s.profile!.targetWeight];
    final minY = ys.reduce((a, b) => a < b ? a : b) - 2;
    final maxY = ys.reduce((a, b) => a > b ? a : b) + 2;
    return LineChart(LineChartData(
      minY: minY,
      maxY: maxY,
      gridData: const FlGridData(show: false),
      borderData: FlBorderData(show: false),
      titlesData: const FlTitlesData(
        topTitles: AxisTitles(),
        rightTitles: AxisTitles(),
        bottomTitles: AxisTitles(),
        leftTitles: AxisTitles(sideTitles: SideTitles(showTitles: true, reservedSize: 36)),
      ),
      extraLinesData: ExtraLinesData(horizontalLines: [
        HorizontalLine(
          y: s.profile!.targetWeight,
          color: C.gold,
          dashArray: [6, 4],
          label: HorizontalLineLabel(show: true, labelResolver: (_) => 'الهدف'),
        ),
      ]),
      lineBarsData: [
        LineChartBarData(
          spots: spots,
          isCurved: true,
          barWidth: 4,
          color: C.emerald,
          dotData: const FlDotData(show: true),
          belowBarData: BarAreaData(
            show: true,
            gradient: LinearGradient(
              colors: [C.emerald.withValues(alpha: .35), C.emerald.withValues(alpha: 0)],
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
            ),
          ),
        ),
      ],
    ));
  }
}
