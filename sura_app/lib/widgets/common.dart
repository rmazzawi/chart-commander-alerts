import 'dart:math';

import 'package:flutter/material.dart';

import '../store.dart';
import '../theme.dart';

/// Provides [AppState] to the widget tree.
class AppScope extends InheritedNotifier<AppState> {
  const AppScope({super.key, required AppState state, required super.child})
      : super(notifier: state);
  static AppState of(BuildContext c) =>
      c.dependOnInheritedWidgetOfExactType<AppScope>()!.notifier!;
}

class Glass extends StatelessWidget {
  final Widget child;
  final EdgeInsets padding;
  final Gradient? gradient;
  const Glass({super.key, required this.child, this.padding = const EdgeInsets.all(18), this.gradient});
  @override
  Widget build(BuildContext context) => Container(
        padding: padding,
        decoration: BoxDecoration(
          color: gradient == null ? Colors.white : null,
          gradient: gradient,
          borderRadius: BorderRadius.circular(24),
          boxShadow: [
            BoxShadow(color: C.emeraldDark.withValues(alpha: .07), blurRadius: 24, offset: const Offset(0, 10)),
          ],
        ),
        child: child,
      );
}

/// Animated calorie ring. Turns coral when over target.
class CalorieRing extends StatelessWidget {
  final int eaten, target;
  final double size;
  const CalorieRing({super.key, required this.eaten, required this.target, this.size = 190});
  @override
  Widget build(BuildContext context) {
    final over = eaten > target;
    final left = (target - eaten).abs();
    return TweenAnimationBuilder<double>(
      tween: Tween(begin: 0, end: target == 0 ? 0 : eaten / target),
      duration: const Duration(milliseconds: 1100),
      curve: Curves.easeOutCubic,
      builder: (_, v, _) => SizedBox(
        width: size,
        height: size,
        child: CustomPaint(
          painter: _RingPainter(v, over),
          child: Center(
            child: Column(mainAxisSize: MainAxisSize.min, children: [
              Text('$left',
                  style: TextStyle(fontSize: size * .2, fontWeight: FontWeight.w800, color: Colors.white, height: 1.1)),
              Text(over ? 'سعرة زيادة ⚠️' : 'سعرة متبقية',
                  style: const TextStyle(color: Colors.white70, fontSize: 14)),
            ]),
          ),
        ),
      ),
    );
  }
}

class _RingPainter extends CustomPainter {
  final double v;
  final bool over;
  _RingPainter(this.v, this.over);
  @override
  void paint(Canvas canvas, Size s) {
    final c = s.center(Offset.zero);
    final r = s.width / 2 - 10;
    final bg = Paint()
      ..color = Colors.white24
      ..style = PaintingStyle.stroke
      ..strokeWidth = 16;
    canvas.drawCircle(c, r, bg);
    final rect = Rect.fromCircle(center: c, radius: r);
    final fg = Paint()
      ..shader = SweepGradient(
        startAngle: -pi / 2,
        endAngle: 3 * pi / 2,
        colors: over ? const [C.coral, Color(0xFFFFA07A), C.coral] : const [C.gold, Colors.white, C.gold],
      ).createShader(rect)
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round
      ..strokeWidth = 16;
    canvas.drawArc(rect, -pi / 2, 2 * pi * v.clamp(0, 1), false, fg);
  }

  @override
  bool shouldRepaint(_RingPainter o) => o.v != v || o.over != over;
}

class MacroBar extends StatelessWidget {
  final String label;
  final double grams, goal;
  final Color color;
  const MacroBar(this.label, this.grams, this.goal, this.color, {super.key});
  @override
  Widget build(BuildContext context) => Expanded(
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(label, style: const TextStyle(color: Colors.white70, fontSize: 12)),
          const SizedBox(height: 4),
          ClipRRect(
            borderRadius: BorderRadius.circular(8),
            child: LinearProgressIndicator(
              value: goal == 0 ? 0 : (grams / goal).clamp(0, 1),
              minHeight: 7,
              color: color,
              backgroundColor: Colors.white24,
            ),
          ),
          const SizedBox(height: 2),
          Text('${grams.round()} / ${goal.round()}غ',
              style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.w700)),
        ]),
      );
}

/// Full-screen alert shown when the user exceeds the daily target.
Future<void> showOverLimitAlert(BuildContext context, int eaten, int target) {
  return showGeneralDialog(
    context: context,
    barrierDismissible: true,
    barrierLabel: 'alert',
    barrierColor: Colors.black54,
    transitionDuration: const Duration(milliseconds: 350),
    pageBuilder: (_, _, _) => const SizedBox(),
    transitionBuilder: (ctx, a, _, _) => Transform.scale(
      scale: Curves.elasticOut.transform(a.value).clamp(0.0, 1.2),
      child: AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(28)),
        icon: const Text('⚠️', style: TextStyle(fontSize: 54)),
        title: const Text('تجاوزت احتياجك اليومي!', textAlign: TextAlign.center),
        content: Text(
          'تناولت $eaten سعرة من أصل $target.\nزيادة ${eaten - target} سعرة اليوم.\n\n'
          'نصيحة: امشِ ${((eaten - target) / 4).round()} دقيقة أو اختر وجبة خفيفة في المرة القادمة 💪',
          textAlign: TextAlign.center,
        ),
        actions: [
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: C.coral),
            onPressed: () => Navigator.pop(ctx),
            child: const Text('فهمت'),
          ),
        ],
      ),
    ),
  );
}
