# سُعرة (Sura) — project status

_Last updated: 2026-09-30_

## Done ✅
- Flutter Android app built: Arabic RTL UI, 85+ Arab dish database, meal/snack/Ramadan logging,
  profile-based daily target, over-limit alert, weight + calorie charts, water tracker, streaks,
  sharing to Facebook/Instagram, paywall after a 365-day free year (Google Play subscriptions).
- Play Store icon, feature graphic, Arabic listing text, privacy policy (`store_listing/`).
- GitHub Actions builds on every push. The test APK is published as a direct download under
  **Releases** (e.g. https://github.com/rmazzawi/chart-commander-alerts/releases/tag/build-2).
- **The owner installed the test APK on their phone and it works.**

## Current limitations of the test build
- AI photo recognition is OFF: no Anthropic API key or proxy set up yet. Users pick dishes from the list.
- Subscriptions only work once installed from Google Play.

## Next steps (in order)
1. Owner: create an Anthropic API account (console.anthropic.com), add ~$5–10 credit, create an API key.
   Never paste the key in chat.
2. Owner: create a free Cloudflare account.
3. Deploy `backend/worker.js` with the key (see PUBLISHING.md §2), add the `AI_PROXY_URL` GitHub secret, rebuild.
4. Pending decision (proposed, awaiting owner's go-ahead): switch the photo model to Claude Haiku and cap
   photo scans at 3/day during the free year, to cut AI costs by roughly 70–90%.
5. Owner: create an empty private GitHub repo `sura-calorie-app`; then move the app there
   (a standalone copy with an adjusted workflow is prepared).
6. Owner: pay the $25 Google Play Console fee and get ID verification done; recruit 12+ testers for the
   required 14-day closed test.
7. Create an upload keystore + GitHub secrets, upload the .aab to internal testing, then publish.

## Decisions & notes
- Suggested prices: 14.99 SAR/month (~$4), 99.99 SAR/year (~$26.67). Set in Play Console.
- App ID: `com.sura.sura` (it can't be changed after the first upload).
- Estimated first-year cost beyond $25: mainly AI (~$0.01/photo, about $1,100 per 100 active users at
  3 photos/day); everything else is free or optional (domain ~$15–30).
