# Publishing سُعرة on Google Play — step by step

## 1. One-time accounts (≈ $25)
1. Create a Google Play Console developer account: https://play.google.com/console ($25 one-time fee; identity verification takes 1–3 days).
2. Create a **payments profile** (Console → Settings → Payments profile) so you can sell subscriptions.
3. Pick an **Anthropic API account** for the AI photo analysis: https://console.anthropic.com

## 2. Deploy the AI proxy (keeps your API key secret)
```bash
cd sura_app
npx wrangler login
npx wrangler secret put ANTHROPIC_API_KEY   # paste your key
npx wrangler deploy backend/worker.js --name sura-ai
```
Note the URL, e.g. `https://sura-ai.<you>.workers.dev`.

## 3. Create your upload key (run once, keep it forever)
```bash
keytool -genkey -v -keystore upload-keystore.jks -keyalg RSA -keysize 2048 -validity 10000 -alias upload
```
**Back this file and its passwords up.** Losing it means you can't publish updates.

## 4. Build the release (two options)
**A. GitHub Actions (no Android Studio needed).** In the repo, go to Settings → Secrets → Actions and add:
| Secret | Value |
|---|---|
| `KEYSTORE_BASE64` | `base64 -w0 upload-keystore.jks` |
| `KEYSTORE_PASSWORD` / `KEY_PASSWORD` | your passwords |
| `KEY_ALIAS` | `upload` |
| `AI_PROXY_URL` | the URL from step 2 |

Then run **Actions → Sura Android build → Run workflow** and download `app-release.aab` (plus an APK for testing on your phone).

**B. Locally:** create `android/key.properties`:
```
storePassword=...
keyPassword=...
keyAlias=upload
storeFile=/absolute/path/upload-keystore.jks
```
Then run: `flutter build appbundle --release --dart-define=AI_PROXY_URL=https://sura-ai.<you>.workers.dev`

## 5. Create the app in Play Console
1. **Create app**: name `سُعرة - حاسبة السعرات بالتصوير`, default language **Arabic (ar)**, App, Free.
2. **Store listing**: copy text from `store_listing/listing_ar.md`. Upload `store_listing/icon_512.png`, `store_listing/feature_graphic_1024x500.png`, and at least 2 phone screenshots (take them in the app).
3. **App content**:
   - Privacy policy URL: host `store_listing/privacy_policy_ar.md` (GitHub Pages or Google Sites) and paste the link.
   - Data safety: photos are sent to the AI service for analysis and not stored; health data (weight, meals) stays on the device; nothing is sold.
   - Target audience: 18+ (avoids the Families policy requirements).
   - Health apps declaration: "Nutrition and weight management". The app is **not** a medical device.
   - Content rating questionnaire: fill it in (expect "Everyone").
4. **Countries**: select all Arab countries first (Saudi Arabia, UAE, Egypt, Jordan, Kuwait, Qatar, Bahrain, Oman, Morocco, Iraq, …), then expand.

## 6. Subscriptions (charging after year one)
Console → Monetize → Products → **Subscriptions** → create:
| Product ID (must match code) | Suggested price |
|---|---|
| `sura_premium_monthly` | 14.99 SAR / month |
| `sura_premium_yearly`  | 99.99 SAR / year |

Activate both. The app counts **365 days from first launch** and then shows the paywall. For stronger protection later, verify purchases on a server (TODO in `lib/services/subscription.dart`).

## 7. Testing, then production
1. Upload the `.aab` to **Testing → Internal testing** and add your own email as a tester.
2. **New personal developer accounts must run a closed test with at least 12 testers for 14 days** before production access is granted. Recruit friends and family.
3. Promote to **Production** → Send for review (usually 1–7 days).

## 8. Updates
Bump `version:` in `pubspec.yaml` (e.g. `1.0.1+2`; the number after `+` must always increase), rebuild, and upload a new release.
