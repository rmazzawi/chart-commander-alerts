import 'package:flutter_test/flutter_test.dart';
import 'package:sura/data/arab_foods.dart';
import 'package:sura/models.dart';
import 'package:sura/services/ai_vision.dart';

void main() {
  test('daily target uses Mifflin-St Jeor and goal delta', () {
    final p = Profile(
      name: 'أحمد', age: 30, sex: Sex.male, heightCm: 175, startWeight: 80,
      targetWeight: 72, activity: Activity.sedentary, goal: Goal.lose, createdAt: DateTime(2026),
    );
    // BMR = 800 + 1093.75 - 150 + 5 = 1748.75; *1.2 = 2098.5; -500 = 1598.5
    expect(p.dailyTarget(80), 1599);
  });

  test('target never drops below safe minimum', () {
    final p = Profile(
      name: 'سارة', age: 60, sex: Sex.female, heightCm: 150, startWeight: 45,
      targetWeight: 42, activity: Activity.sedentary, goal: Goal.lose, createdAt: DateTime(2026),
    );
    expect(p.dailyTarget(45), 1200);
  });

  test('parses AI JSON wrapped in text', () {
    final d = AiVision.parse('هذه النتيجة: {"dishes":[{"name_ar":"منسف","portion":"صحن","kcal":850,"protein_g":45,"carbs_g":70,"fat_g":42}]}');
    expect(d.single.name, 'منسف');
    expect(d.single.kcal, 850);
  });

  test('Arab dish database is populated', () {
    expect(arabDishes.length, greaterThan(80));
    expect(arabDishes.any((d) => d.name == 'كبسة دجاج'), isTrue);
  });
}
