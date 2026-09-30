# سُعرة (Sura) — Arabic photo calorie counter for Android

Snap a photo of your plate and get calories for **Arab dishes** — kabsa, mansaf, koshari, maqluba, couscous, and more.

## Features
- 🇸🇦 Fully Arabic, right-to-left UI with the bundled Cairo font
- 📸 **AI photo analysis** (Claude vision) tuned for Gulf, Levantine, Egyptian, Maghrebi, Iraqi and Yemeni cuisine
- 🍛 Offline database of 85+ Arab dishes, plus custom entries
- 🍽️ Logs breakfast, lunch, dinner and snacks, with a **Ramadan mode** for suhoor and iftar
- 🎯 Personal daily target (Mifflin–St Jeor × activity level ± goal) from name, age, sex, height and weight
- ⚠️ **On-screen alert** plus a red banner when you eat more than your target
- ⚖️ Daily weight log with a trend chart, BMI and progress toward your goal weight
- 📊 7-day calorie chart, macros (protein/carbs/fat), water tracker, streaks 🔥
- 📣 Share a progress card to **Facebook / Instagram** / WhatsApp, and invite friends
- 👑 **Free for the first year**, then a Google Play subscription (monthly or yearly)

## Project layout
```
lib/
  main.dart               app entry, routes to onboarding / paywall / home
  models.dart, store.dart profile, entries, persistence, trial logic
  data/arab_foods.dart    Arab dish database
  services/ai_vision.dart photo → dishes (Claude vision)
  services/subscription.dart Google Play Billing
  screens/                today, add food, progress, profile, paywall, onboarding
backend/worker.js         API-key proxy for the AI (Cloudflare Worker)
store_listing/            Play Store icon, feature graphic, listing text, privacy policy
```

## Run
```bash
flutter pub get
flutter run --dart-define=AI_PROXY_URL=https://your-proxy.workers.dev
```
Without `AI_PROXY_URL`, the photo still gets saved and the user picks the dish from the database.

See **PUBLISHING.md** for Google Play release steps.
