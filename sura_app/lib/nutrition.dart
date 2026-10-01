/// Nutrient definitions, daily values and per-dish estimates.
class Nutrient {
  final String key, ar, unit;
  final double dailyValue; // adult reference daily value
  final bool limit; // true = lower is better (sugar, sodium, ...)
  const Nutrient(this.key, this.ar, this.unit, this.dailyValue, {this.limit = false});
}

const macroNutrients = [
  Nutrient('sugar', 'السكريات', 'غ', 50, limit: true),
  Nutrient('fiber', 'الألياف', 'غ', 28),
  Nutrient('satFat', 'دهون مشبعة', 'غ', 20, limit: true),
  Nutrient('cholesterol', 'الكوليسترول', 'ملغ', 300, limit: true),
  Nutrient('sodium', 'الصوديوم (ملح)', 'ملغ', 2300, limit: true),
];

const minerals = [
  Nutrient('potassium', 'البوتاسيوم', 'ملغ', 4700),
  Nutrient('calcium', 'الكالسيوم', 'ملغ', 1300),
  Nutrient('iron', 'الحديد', 'ملغ', 18),
  Nutrient('magnesium', 'المغنيسيوم', 'ملغ', 420),
  Nutrient('zinc', 'الزنك', 'ملغ', 11),
];

const vitamins = [
  Nutrient('vitA', 'فيتامين A', 'مكغ', 900),
  Nutrient('vitC', 'فيتامين C', 'ملغ', 90),
  Nutrient('vitD', 'فيتامين D', 'مكغ', 20),
  Nutrient('vitB12', 'فيتامين B12', 'مكغ', 2.4),
  Nutrient('folate', 'حمض الفوليك', 'مكغ', 400),
];

const allNutrients = [...macroNutrients, ...minerals, ...vitamins];

Map<String, double> scaleNutrients(Map<String, double> n, double f) =>
    n.map((k, v) => MapEntry(k, v * f));

Map<String, double> sumNutrients(Iterable<Map<String, double>> list) {
  final out = <String, double>{};
  for (final m in list) {
    m.forEach((k, v) => out[k] = (out[k] ?? 0) + v);
  }
  return out;
}

// Approximate per-100g profiles by dish category, in the order:
// sugar, fiber, satFat, cholesterol, sodium, potassium, calcium, iron,
// magnesium, zinc, vitA, vitC, vitD, vitB12, folate
const _keys = [
  'sugar', 'fiber', 'satFat', 'cholesterol', 'sodium', 'potassium', 'calcium', 'iron',
  'magnesium', 'zinc', 'vitA', 'vitC', 'vitD', 'vitB12', 'folate'
];
const _profiles = <String, List<double>>{
  'أطباق رئيسية': [1.5, 1.2, 2, 30, 380, 220, 25, 1.2, 22, 1.5, 30, 4, 0.1, 0.4, 15],
  'مشاوي': [0.5, 0.3, 4, 85, 450, 330, 15, 2, 25, 4, 15, 2, 0.2, 1.5, 8],
  'وجبات سريعة': [3, 2.5, 3.5, 35, 520, 250, 50, 1.8, 30, 1.6, 25, 5, 0.1, 0.5, 35],
  'مخبوزات': [3, 2.5, 4, 15, 500, 140, 80, 2.2, 25, 1, 40, 1, 0.1, 0.2, 60],
  'أطباق جانبية': [0.1, 0.4, 0.1, 0, 2, 35, 10, 1.2, 12, 0.5, 0, 0, 0, 0, 58],
  'فطور': [2, 4, 3, 60, 400, 280, 70, 2, 35, 1.2, 60, 5, 0.5, 0.4, 50],
  'سلطات': [3, 2.5, 1, 0, 250, 250, 30, 1, 15, 0.3, 120, 20, 0, 0, 40],
  'شوربات': [1.5, 2.5, 0.5, 3, 350, 220, 20, 1.5, 20, 0.7, 60, 3, 0, 0.05, 40],
  'حلويات': [28, 1, 7, 25, 150, 120, 50, 1, 20, 0.5, 50, 0, 0.2, 0.2, 15],
  'وجبات خفيفة': [20, 5, 1.5, 0, 5, 450, 40, 1, 60, 1, 5, 4, 0, 0, 20],
  'مشروبات': [9, 0.2, 0.3, 2, 15, 120, 30, 0.2, 8, 0.1, 5, 5, 0.1, 0.1, 5],
};

/// Serving weight in grams for dishes whose serving text has no grams.
const servingGrams = <String, double>{
  'محشي ورق عنب': 250, 'محشي كوسا': 400, 'كبة مقلية': 180, 'كفتة مشوية': 200,
  'دجاج مشوي (نصف)': 350, 'شاورما دجاج (ساندويش)': 250, 'شاورما لحم (ساندويش)': 250,
  'فلافل (ساندويش)': 230, 'فطيرة جبنة': 100, 'فطيرة سبانخ': 100, 'منقوشة زعتر': 120,
  'منقوشة جبنة': 150, 'صفيحة لحم': 150, 'سمبوسة لحم': 120, 'خبز عربي': 60,
  'خبز صاج': 65, 'رز أبيض': 160, 'لبنة بزيت الزيتون': 75, 'شكشوكة': 250,
  'بيض مقلي': 100, 'طعمية': 100, 'بلاليط': 250, 'زيت وزعتر': 25, 'جبنة بيضاء': 50,
  'زيتون': 40, 'سلطة خضراء': 200, 'شوربة عدس': 300, 'شوربة فريكة': 300, 'حريرة': 300,
  'بقلاوة': 75, 'قطايف': 120, 'بسبوسة / هريسة': 90, 'لقيمات': 90, 'معمول تمر': 70,
  'أم علي': 200, 'مهلبية': 200, 'عصيدة': 250, 'تمر': 72, 'فاكهة (تفاحة/برتقالة)': 180,
  'قهوة عربية': 100, 'شاي بالسكر': 250, 'كرك': 250, 'لبن عيران': 250, 'جلاب': 250,
  'قمر الدين': 250, 'تمر هندي': 250, 'عصير برتقال طبيعي': 250, 'مشروب غازي': 330,
};

/// Per-serving overrides where the category profile is a poor fit.
const _overrides = <String, Map<String, double>>{
  'تمر': {'sugar': 48, 'fiber': 5, 'potassium': 480},
  'مكسرات مشكلة': {'sugar': 1.3, 'fiber': 2.5, 'satFat': 2, 'sodium': 60, 'magnesium': 70},
  'بزر (لب)': {'sugar': 0.5, 'fiber': 2.5, 'magnesium': 100, 'zinc': 1.5},
  'فاكهة (تفاحة/برتقالة)': {'sugar': 15, 'fiber': 4, 'vitC': 50, 'potassium': 250},
  'قهوة عربية': {'sugar': 0, 'potassium': 90},
  'شاي بالسكر': {'sugar': 10},
  'كرك': {'sugar': 20, 'calcium': 150, 'satFat': 3},
  'لبن عيران': {'sugar': 9, 'calcium': 280, 'vitB12': 1, 'satFat': 3},
  'جلاب': {'sugar': 42},
  'قمر الدين': {'sugar': 38, 'vitA': 150},
  'تمر هندي': {'sugar': 34},
  'عصير برتقال طبيعي': {'sugar': 21, 'vitC': 120, 'potassium': 450, 'folate': 75},
  'مشروب غازي': {'sugar': 39, 'calcium': 10, 'potassium': 10},
  'مهلبية': {'sugar': 25, 'calcium': 220},
  'جبنة بيضاء': {'sugar': 0.5, 'calcium': 250, 'sodium': 560, 'satFat': 6},
  'زيتون': {'sugar': 0, 'sodium': 620},
};

double gramsFor(String name, String serving) {
  final m = RegExp(r'(\d+)غ').firstMatch(serving);
  if (m != null) return double.parse(m.group(1)!);
  return servingGrams[name] ?? 200;
}

Map<String, double> estimateNutrients(String name, String category, double grams, double carbs) {
  final p = _profiles[category] ?? _profiles['أطباق رئيسية']!;
  final out = <String, double>{
    for (var i = 0; i < _keys.length; i++) _keys[i]: p[i] * grams / 100,
  };
  out.addAll(_overrides[name] ?? const {});
  // Sugar can never exceed total carbohydrates.
  out['sugar'] = (out['sugar']!).clamp(0, carbs);
  return out;
}
