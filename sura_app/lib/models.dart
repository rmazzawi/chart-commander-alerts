import 'dart:convert';

enum Sex { male, female }

enum MealType { breakfast, lunch, dinner, snack, suhoor, iftar }

extension MealTypeX on MealType {
  String get ar => const {
        MealType.breakfast: 'الفطور',
        MealType.lunch: 'الغداء',
        MealType.dinner: 'العشاء',
        MealType.snack: 'وجبة خفيفة',
        MealType.suhoor: 'السحور',
        MealType.iftar: 'الإفطار (رمضان)',
      }[this]!;
  String get emoji => const {
        MealType.breakfast: '🌅',
        MealType.lunch: '☀️',
        MealType.dinner: '🌙',
        MealType.snack: '🍎',
        MealType.suhoor: '🌌',
        MealType.iftar: '🏮',
      }[this]!;
}

enum Activity { sedentary, light, moderate, active, veryActive }

extension ActivityX on Activity {
  double get factor => const [1.2, 1.375, 1.55, 1.725, 1.9][index];
  String get ar => const ['قليل الحركة', 'نشاط خفيف', 'نشاط متوسط', 'نشيط', 'نشيط جداً'][index];
}

enum Goal { lose, maintain, gain }

extension GoalX on Goal {
  String get ar => const ['خسارة الوزن', 'الحفاظ على الوزن', 'زيادة الوزن'][index];
  int get delta => const [-500, 0, 400][index];
}

class Profile {
  String name;
  int age;
  Sex sex;
  double heightCm;
  double startWeight;
  double targetWeight;
  Activity activity;
  Goal goal;
  DateTime createdAt;

  Profile({
    required this.name,
    required this.age,
    required this.sex,
    required this.heightCm,
    required this.startWeight,
    required this.targetWeight,
    required this.activity,
    required this.goal,
    required this.createdAt,
  });

  /// Mifflin-St Jeor BMR.
  double bmr(double weight) =>
      10 * weight + 6.25 * heightCm - 5 * age + (sex == Sex.male ? 5 : -161);

  int dailyTarget(double weight) {
    final t = bmr(weight) * activity.factor + goal.delta;
    final floor = sex == Sex.male ? 1500 : 1200; // safe minimum
    return t.round().clamp(floor, 5000);
  }

  Map<String, dynamic> toJson() => {
        'name': name,
        'age': age,
        'sex': sex.index,
        'height': heightCm,
        'startWeight': startWeight,
        'targetWeight': targetWeight,
        'activity': activity.index,
        'goal': goal.index,
        'createdAt': createdAt.toIso8601String(),
      };

  factory Profile.fromJson(Map<String, dynamic> j) => Profile(
        name: j['name'],
        age: j['age'],
        sex: Sex.values[j['sex']],
        heightCm: (j['height'] as num).toDouble(),
        startWeight: (j['startWeight'] as num).toDouble(),
        targetWeight: (j['targetWeight'] as num).toDouble(),
        activity: Activity.values[j['activity']],
        goal: Goal.values[j['goal']],
        createdAt: DateTime.parse(j['createdAt']),
      );
}

class FoodEntry {
  final String id;
  final String name;
  final int kcal;
  final double protein, carbs, fat;
  final MealType meal;
  final DateTime time;
  final String? photoPath;

  FoodEntry({
    required this.id,
    required this.name,
    required this.kcal,
    this.protein = 0,
    this.carbs = 0,
    this.fat = 0,
    required this.meal,
    required this.time,
    this.photoPath,
  });

  Map<String, dynamic> toJson() => {
        'id': id,
        'name': name,
        'kcal': kcal,
        'p': protein,
        'c': carbs,
        'f': fat,
        'meal': meal.index,
        'time': time.toIso8601String(),
        'photo': photoPath,
      };

  factory FoodEntry.fromJson(Map<String, dynamic> j) => FoodEntry(
        id: j['id'],
        name: j['name'],
        kcal: j['kcal'],
        protein: (j['p'] as num).toDouble(),
        carbs: (j['c'] as num).toDouble(),
        fat: (j['f'] as num).toDouble(),
        meal: MealType.values[j['meal']],
        time: DateTime.parse(j['time']),
        photoPath: j['photo'],
      );
}

class WeightEntry {
  final DateTime date;
  final double kg;
  WeightEntry(this.date, this.kg);
  Map<String, dynamic> toJson() => {'d': date.toIso8601String(), 'kg': kg};
  factory WeightEntry.fromJson(Map<String, dynamic> j) =>
      WeightEntry(DateTime.parse(j['d']), (j['kg'] as num).toDouble());
}

String encodeList(List<dynamic> l) => jsonEncode(l.map((e) => e.toJson()).toList());
