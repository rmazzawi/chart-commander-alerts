import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'models.dart';

DateTime dayOf(DateTime d) => DateTime(d.year, d.month, d.day);

/// Central app state, persisted locally on the device.
class AppState extends ChangeNotifier {
  late SharedPreferences _p;
  Profile? profile;
  List<FoodEntry> foods = [];
  List<WeightEntry> weights = [];
  Map<String, int> water = {}; // yyyy-mm-dd -> glasses
  DateTime firstLaunch = DateTime.now();
  bool premium = false;
  bool ramadanMode = false;

  static const freeDays = 365;

  Future<void> load() async {
    _p = await SharedPreferences.getInstance();
    final fl = _p.getString('firstLaunch');
    if (fl == null) {
      await _p.setString('firstLaunch', firstLaunch.toIso8601String());
    } else {
      firstLaunch = DateTime.parse(fl);
    }
    final pj = _p.getString('profile');
    if (pj != null) profile = Profile.fromJson(jsonDecode(pj));
    foods = (jsonDecode(_p.getString('foods') ?? '[]') as List)
        .map((e) => FoodEntry.fromJson(e))
        .toList();
    weights = (jsonDecode(_p.getString('weights') ?? '[]') as List)
        .map((e) => WeightEntry.fromJson(e))
        .toList();
    water = Map<String, int>.from(jsonDecode(_p.getString('water') ?? '{}'));
    premium = _p.getBool('premium') ?? false;
    ramadanMode = _p.getBool('ramadan') ?? false;
  }

  // ---------- subscription ----------
  DateTime get trialEnds => firstLaunch.add(const Duration(days: freeDays));
  int get trialDaysLeft =>
      trialEnds.difference(DateTime.now()).inDays.clamp(0, freeDays);
  bool get hasAccess => premium || DateTime.now().isBefore(trialEnds);

  Future<void> setPremium(bool v) async {
    premium = v;
    await _p.setBool('premium', v);
    notifyListeners();
  }

  Future<void> setRamadan(bool v) async {
    ramadanMode = v;
    await _p.setBool('ramadan', v);
    notifyListeners();
  }

  // ---------- profile & weight ----------
  Future<void> saveProfile(Profile p) async {
    final isNew = profile == null;
    profile = p;
    await _p.setString('profile', jsonEncode(p.toJson()));
    if (isNew) await logWeight(p.startWeight);
    notifyListeners();
  }

  double get currentWeight =>
      weights.isEmpty ? (profile?.startWeight ?? 70) : weights.last.kg;

  int get dailyTarget => profile?.dailyTarget(currentWeight) ?? 2000;

  Future<void> logWeight(double kg, [DateTime? when]) async {
    final d = dayOf(when ?? DateTime.now());
    weights.removeWhere((w) => dayOf(w.date) == d);
    weights.add(WeightEntry(d, kg));
    weights.sort((a, b) => a.date.compareTo(b.date));
    await _p.setString('weights', encodeList(weights));
    notifyListeners();
  }

  double get bmi {
    final h = (profile?.heightCm ?? 170) / 100;
    return currentWeight / (h * h);
  }

  // ---------- food ----------
  List<FoodEntry> foodsOn(DateTime d) =>
      foods.where((f) => dayOf(f.time) == dayOf(d)).toList();

  int kcalOn(DateTime d) => foodsOn(d).fold(0, (s, f) => s + f.kcal);

  /// Adds food. Returns true if this addition crossed the daily target.
  Future<bool> addFood(FoodEntry e) async {
    final before = kcalOn(e.time);
    foods.add(e);
    await _p.setString('foods', encodeList(foods));
    notifyListeners();
    return before + e.kcal > dailyTarget;
  }

  Future<void> removeFood(String id) async {
    foods.removeWhere((f) => f.id == id);
    await _p.setString('foods', encodeList(foods));
    notifyListeners();
  }

  // ---------- water ----------
  String _k(DateTime d) => dayOf(d).toIso8601String().substring(0, 10);
  int waterOn(DateTime d) => water[_k(d)] ?? 0;
  Future<void> setWater(DateTime d, int glasses) async {
    water[_k(d)] = glasses.clamp(0, 20);
    await _p.setString('water', jsonEncode(water));
    notifyListeners();
  }

  /// Consecutive days (ending today or yesterday) with logs within target.
  int get streak {
    var d = dayOf(DateTime.now());
    if (foodsOn(d).isEmpty) d = d.subtract(const Duration(days: 1));
    var n = 0;
    while (foodsOn(d).isNotEmpty && kcalOn(d) <= dailyTarget) {
      n++;
      d = d.subtract(const Duration(days: 1));
    }
    return n;
  }

  Future<void> resetAll() async {
    await _p.clear();
    await _p.setString('firstLaunch', firstLaunch.toIso8601String());
    profile = null;
    foods = [];
    weights = [];
    water = {};
    notifyListeners();
  }
}
