import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

/// A dish detected in a photo.
class DetectedDish {
  final String name;
  final String portion;
  final int kcal;
  final double protein, carbs, fat, grams;
  final Map<String, double> nutrients;
  DetectedDish(this.name, this.portion, this.kcal, this.protein, this.carbs, this.fat,
      [this.grams = 0, this.nutrients = const {}]);

  factory DetectedDish.fromJson(Map<String, dynamic> j) => DetectedDish(
        j['name_ar'] ?? j['name'] ?? 'طبق',
        j['portion'] ?? '',
        (j['kcal'] as num).round(),
        (j['protein_g'] as num? ?? 0).toDouble(),
        (j['carbs_g'] as num? ?? 0).toDouble(),
        (j['fat_g'] as num? ?? 0).toDouble(),
        (j['grams'] as num? ?? 0).toDouble(),
        (j['nutrients'] as Map? ?? {}).map((k, v) => MapEntry(k as String, (v as num).toDouble())),
      );
}

/// Food photo analysis using Claude vision.
///
/// Production: set AI_PROXY_URL to your own backend that forwards the request
/// to the Anthropic API (keeps the API key off the device).
/// Development only: ANTHROPIC_API_KEY may be passed with --dart-define.
class AiVision {
  static const _proxy = String.fromEnvironment('AI_PROXY_URL');
  static const _key = String.fromEnvironment('ANTHROPIC_API_KEY');
  static const model = 'claude-sonnet-5-5';

  static bool get configured => _proxy.isNotEmpty || _key.isNotEmpty;

  static const _prompt = '''
أنت خبير تغذية متخصص في المطبخ العربي (الخليجي، الشامي، المصري، المغاربي، العراقي، اليمني).
حلّل صورة الطعام وحدد كل طبق ظاهر وقدّر حجم الحصة من خلال الصحن وأدوات المائدة.
أعد JSON فقط بدون أي نص آخر، بالشكل (القيم للحصة الظاهرة كاملة):
{"dishes":[{"name_ar":"كبسة دجاج","portion":"صحن متوسط","grams":350,"kcal":620,"protein_g":35,"carbs_g":72,"fat_g":20,
"nutrients":{"sugar":4,"fiber":3,"satFat":6,"cholesterol":95,"sodium":1100,"potassium":650,"calcium":70,"iron":3,
"magnesium":70,"zinc":4,"vitA":90,"vitC":12,"vitD":0.3,"vitB12":0.8,"folate":45}}]}
الوحدات: sugar/fiber/satFat بالغرام، vitA/vitD/vitB12/folate بالميكروغرام، والباقي بالملليغرام.
إذا لم تكن الصورة طعاماً أعد {"dishes":[]}.''';

  static Future<List<DetectedDish>> analyze(File image) async {
    if (!configured) {
      throw Exception('خدمة التعرف على الصور غير مفعّلة');
    }
    final bytes = await image.readAsBytes();
    final body = jsonEncode({
      'model': model,
      'max_tokens': 2048,
      'messages': [
        {
          'role': 'user',
          'content': [
            {
              'type': 'image',
              'source': {
                'type': 'base64',
                'media_type': 'image/jpeg',
                'data': base64Encode(bytes),
              }
            },
            {'type': 'text', 'text': _prompt},
          ]
        }
      ]
    });
    final uri = Uri.parse(_proxy.isNotEmpty ? _proxy : 'https://api.anthropic.com/v1/messages');
    final headers = {
      'content-type': 'application/json',
      if (_proxy.isEmpty) 'x-api-key': _key,
      if (_proxy.isEmpty) 'anthropic-version': '2023-06-01',
    };
    final res = await http
        .post(uri, headers: headers, body: body)
        .timeout(const Duration(seconds: 60));
    if (res.statusCode != 200) {
      throw Exception('فشل التحليل (${res.statusCode})');
    }
    final data = jsonDecode(utf8.decode(res.bodyBytes));
    final text = (data['content'] as List)
        .where((c) => c['type'] == 'text')
        .map((c) => c['text'] as String)
        .join();
    return parse(text);
  }

  static List<DetectedDish> parse(String text) {
    final start = text.indexOf('{');
    final end = text.lastIndexOf('}');
    if (start < 0 || end <= start) return [];
    final j = jsonDecode(text.substring(start, end + 1));
    return (j['dishes'] as List? ?? [])
        .map((d) => DetectedDish.fromJson(d))
        .toList();
  }
}
