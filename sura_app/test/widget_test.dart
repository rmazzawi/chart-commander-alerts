import 'package:flutter_test/flutter_test.dart';
import 'package:sura/data/arab_foods.dart';
import 'package:sura/models.dart';
import 'package:sura/nutrition.dart';
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

  test('serving grams parsed from text or fallback table', () {
    final kabsa = arabDishes.firstWhere((d) => d.name == 'كبسة دجاج');
    expect(kabsa.grams, 350);
    final bread = arabDishes.firstWhere((d) => d.name == 'خبز عربي');
    expect(bread.grams, 60);
  });

  test('every dish has full nutrients and sugar never exceeds carbs', () {
    for (final d in arabDishes) {
      final n = d.nutrients;
      for (final k in allNutrients) {
        expect(n.containsKey(k.key), isTrue, reason: '${d.name} missing ${k.key}');
      }
      expect(n['sugar']!, lessThanOrEqualTo(d.carbs), reason: d.name);
    }
  });

  test('food entry keeps grams and nutrients; old entries still load', () {
    final e = FoodEntry(
      id: '1', name: 'تمر', kcal: 200, meal: MealType.snack, time: DateTime(2026),
      grams: 72, nutrients: {'sugar': 48, 'iron': 0.7},
    );
    final back = FoodEntry.fromJson(e.toJson());
    expect(back.grams, 72);
    expect(back.nutrients['sugar'], 48);
    final old = Map<String, dynamic>.from(e.toJson())..remove('g')..remove('n');
    expect(FoodEntry.fromJson(old).nutrients, isEmpty);
  });

  test('AI result parses grams and nutrients', () {
    final d = AiVision.parse('{"dishes":[{"name_ar":"كنافة","grams":150,"kcal":520,"protein_g":11,"carbs_g":55,"fat_g":29,"nutrients":{"sugar":30,"calcium":200}}]}');
    expect(d.single.grams, 150);
    expect(d.single.nutrients['sugar'], 30);
  });

  test('scaling nutrients by portion', () {
    expect(scaleNutrients({'iron': 2}, 1.5)['iron'], 3);
  });
}
