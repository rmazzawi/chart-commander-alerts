# CC-Multi — Project Handoff (read this first)

Last updated: 2026-10-08 (end of session 2). Repo: `rmazzawi/chart-commander-alerts`. **All latest work is on branch `claude/admiring-knuth-f7lory`** (built on `claude/gifted-noether-f72n1r`; `claude/sleepy-ramanujan-kb3jjq` = user's original branch, untouched). Start a new session by checking out that branch and reading this file.

**Quick links:** dashboard `https://vmi3437039.contaboserver.net/webhook/signals` · TradingView webhook URL `https://vmi3437039.contaboserver.net/webhook/tv-signal` · live log CSV `…/webhook/signals?csv=1` · Google Sheet id `1u5jCqGPcLcWedliNCqbfPM5y9JDgT6OlfAhEl9lnJ60` (tab Archive; readable with the Google Drive connector → export xlsx).

---

## 1. Who / what
- User trades **0DTE options (calls/puts)** from a TradingView Pine indicator **"CC-Multi"** on **2-minute charts, extended hours ON**. ~58 tickers on charts.
- Alerts go **TradingView → n8n webhook → dashboard page + log → Google Sheet**.
- User is not a programmer: always give **plain-English explanations**, step-by-step click instructions, and **full ready-to-paste files** (never "edit line X").

## 2. User's working rules (follow these)
1. Change **one thing at a time**.
2. **Explain in plain English and get a yes BEFORE changing anything** (user often says "tell me first", "don't change anything yet").
3. New rules: originally "OFF by default" — **but the user later asked for rules to be always ON** (lunch block, 2-loss stop, profit protection, info alerts). Ask when unsure.
4. **Always send the full .pine file + its line count.**
5. **Test every change in Python on all tickers first; show before/after tables** (both periods: Jul 27–Sep 3 = "good month", Sep 4–Oct 2 = "bad month") before sending a script.
6. Chart shows **boxes only**; details go to n8n alerts.
7. Be honest about weak results; the user values that.

## 3. Current live versions
| Piece | File | Notes |
|---|---|---|
| **Pine (latest)** | **`CC-Multi_v8.pine`** (= `cc_multi_strategy.pine`), **925 lines**. **User calls it "CC-Multi V8" (same name in TradingView)** — always refer to it by that name | = v4 + PIN BAR info alert (looser rule: any drop into the day low, slow or fast). Not compiled by Claude — user verifies in TradingView |
| Previous live Pine | `CC-Multi_v4.pine`, 901 lines | |
| Approved baseline (never modify) | `cc_multi_BASELINE.pine`, 684 lines | |
| Older versions | `CC-Multi_v2_LUNCH.pine` (699), `CC-Multi_v3.pine` (735), `CC-Multi_S2-400SMA.pine`, `CC-Multi_TEST400.pine` | history |
| **n8n workflow (latest)** | `n8n/tv_signals_workflow.json` → page shows **"dashboard v8"** | v8 = PIN BAR rows teal + own bell/chime sound (other honk events unchanged). v7 was confirmed running 2026-10-06; v8 sent for install |
| Google Apps Script | `n8n/archive_apps_script.gs` | hourly archive into sheet tab "Archive" |

### What v4 contains (on top of the 684-line baseline)
Baseline strategies (unchanged): **S1** 30m ORB + 20 EMA retest, **S2** liquidity sweep/exhaustion reversal, **S3** VWAP reclaim/loss, **S4** opening drive (PM high/low break), **S5** trend pullback into 34/50 or 72/89 cloud, **S6** TLP patience candle. Filters: cloud rule, chop block after 11:30, 1st-hour S2 needs 2nd test, 5m confirmation, 10m/30m trend filters. Exits: initial stop, trail on 5m candles, T1 sell half (stop→BE), T2 sell more, 3:45 flat.

Added (all tested, user approved):
1. **S2 only with the 400 SMA trend** (calls above SMA400, puts below) — setting `s2Trend`, default **ON**.
2. **Lunch block 12:30–14:00 ET, always on**: no new entries / no POSSIBLE alerts; open trades still managed; alerts "LUNCH BREAK - STOP NEW TRADES" / "LUNCH OVER - TRADING RESUMES".
3. **Stop after 2 losing trades per ticker per day** (always on) → "DONE FOR TODAY - 2 LOSSES".
4. **Profit protection**: at 80% of the way to T1 → stop moves to lock 50% of the move → "PROTECT PROFIT CALLS/PUTS - move stop to X"; exit text "profit lock hit".
5. **Information-only trend-day alerts (no trade effect)**, all tickers:
   - 9:46 "TREND DAY POSSIBLE UP/DOWN (likely - yesterday choppy)" / "TREND DAY UNLIKELY" (first 15m candle closes in top/bottom 20% vs middle).
   - 10:30 "TREND DAY LIKELY … (angle N deg, still pushing)" if open→tip triangle angle ≥30° and tip in last 15 min; 20–30° = "POSSIBLE"; steep but tip early = "EARLY SPIKE - not a trend".
     Angle = arccos(adj/hyp), adj = bars × avg 2m candle (prev 5 days), opp = |tip − open| (zoom-independent, user's requested method).
   - "EXHAUSTION RISK … at <level>": strong move (angle ≥20) makes new extreme within max(2×unit, 0.15%) of prior-day H/L, PM H/L, SMA200/400, 5-day H/L, with 6-bar avg volume ≥75% of first-30-min avg. Once/ticker/day.
   - 11:00–12:00 "TREND PAUSING" (60-min regression angle <20° on the half-day-range-per-hour scale) after a likely/possible trend day.
   - "VWAP BREAK after one-sided morning - likely fake-out" (10m EMA5/9 stayed one side of VWAP 9:30–10:20, later 10m close through VWAP). Once/ticker/day.

### What CC-Multi V8 adds (info only, no trade effect)
- **PIN BAR AT DAY LOW - watch CALLS above X** / **PIN BAR AT DAY HIGH - watch PUTS below X**: 2m candle >= 0.5 x RTH ATR(14), tail >= 60%, body <= 35%, price moved into it over last 3 bars (slow or fast; looser rule chosen 10/6 - same ~60% wins, 2x alerts), tail within 0.15 ATR of the earlier day low/high and closed back inside. 9:36-15:00, not lunch, max 1 per 5 bars per side. Tested (analysis/pinbar_tf.py): ~57-62% wins at 1R, both periods. Today's GOOGL 9:56 pin would NOT fire (slow drift in, fails the 1-ATR rule) - told user.

## 4. Infrastructure
- **TradingView alert** per chart: Condition **CC-Multi → "Any alert() function call"**, webhook `https://vmi3437039.contaboserver.net/webhook/tv-signal`. Must be **recreated after every script update** (alerts keep the old version). Each ticker needs its own alert.
- **Dashboard**: `https://vmi3437039.contaboserver.net/webhook/signals` (user must click the sound button after each page load; STOP HONK button + Esc).
  - Honks on: LUNCH, DONE FOR TODAY, PROTECT PROFIT, TREND DAY LIKELY, EXHAUSTION. (User declined making every alert honk.)
  - Resets daily (ET). Version label "dashboard vN" next to title — bump it on every change so the user can verify the import.
- **Log**: n8n keeps a permanent log in workflow static data, served as CSV at `…/webhook/signals?csv=1`. **Re-importing the workflow wipes it** → before any re-import tell the user to run `archive` once in Apps Script.
- **Google Sheet** "CC-Multi Signal Log (live)" in reda.mazzawi@gmail.com Drive: id `1u5jCqGPcLcWedliNCqbfPM5y9JDgT6OlfAhEl9lnJ60`. Tab **Archive** = permanent history (Apps Script hourly). Readable via the Google Drive connector (export as xlsx to get all tabs). Old unused sheet "CC-Multi Signal Log" (`1xedRPnVAbRXyINZ0vMlpBvMLzmh6wwlGsiW09QZa-OI`).
- Claude's sandbox **cannot reach the contabo server** (proxy 403) — can't test the live URL.
- Webhook key in Pine/n8n: `change-me` (default; both sides match).
- n8n gotchas learned: a Google Sheets node without credentials can block activation → v6 removed it; duplicate active workflows fight over the same paths.

## 5. Data
- `data/*.csv.gz` — TradingView exports, 2-minute, extended hours, with CC-Multi **baseline** columns (ActionCode, StrategyCode, RVOL…): AAPL AMD AMZN GLD IWM META MSFT NVDA QQQ SPX SPY TSLA (~Jul 27/Aug 3 → Oct 2; SPX from May 11). `AMEX_SPY_2_S2rule_ON` = SPY with the 400-SMA rule ON (matched Python exactly).
- ActionCode: 1 BUY CALLS, −1 BUY PUTS, ±2 T1/T2, ±3 exit. StrategyCode 1–6 = S1–S6.
- User's broker executions (personal, NOT committed): ask user to re-upload if needed.
- **Setup:** `pip install pandas openpyxl && mkdir work && cd work && python ../analysis/prepare.py` → builds `D_<TK>.pkl` (bars + ATR + date), `T_<TK>.pkl`, `ALL.pkl`; reproduces SPY baseline 84 trades / 35%. Other scripts in `analysis/` chain from these (e.g. `feat.py` → `F.pkl`, `day.py`/`rt.py` → `S2day2.pkl`, `sim.py` → `SIM.pkl`, `doc_tests.py` → `DOC.pkl`, `tdall.py` → `TDALL.pkl`).
- R = points / initial risk; win = points > 0; T1 counted as half at T1 + half at exit.

## 6. Key findings so far (so you don't redo them)
- Baseline SPY Sep 4–Oct 2: 84 trades 35%; S2 64 @ 28% was the main loser. Across 12 tickers S2 was +65R Jul–Sep 3 but −63R Sep 4–Oct 2 (regime).
- **Worked (both periods):** S2 400-SMA rule; lunch block 12:30–14:00; stop after 2 losses/ticker/day; profit protection 80%→lock 50%. #1+#5 together turned the bad month −14.9R → +6.1R.
- **Didn't work:** per-ticker strategy selection (picks didn't persist, 42% same-sign); quicker exits (current exits best); trend/chop router; 1H alignment; 15m ORB (+0.05R/trade); Fib pullbacks (high win% 55–59% but ~0R on every TF 2/5/10/15m); weekly options + holding losers (high win%, big $ losses); 10m EMA5/9-vs-VWAP reversal/bounce setups (≈50/50 both with premarket on/off).
- **User's own trading** (Mar 2025–Sep 2026, 2,130 option round trips): −$19,683 incl. $4,146 fees. 306 trades held to ~zero = −$26,497 (everything else +$6.8k). After a loss trades: −$17.9k. Holding >60 min: −$27k. Exiting at −40% would have made ≈ +$8.2k. Trades matching a script signal: +$8.5/trade. Advice given: 1 contract, hard stop −40%/script stop, 2 losses = done, script signals only.
- **Trend days**: ~2–4/month per ticker (TSLA 4.3), mostly NOT the same days as SPX (18%). Not explained by CPI/jobs/FOMC (3 of 13). First 15m candle closing at an extreme caught 34/50 stock trend days; direction matched 88% on stocks (~66–83% SPX). Tip-to-tip angle ≥30° **and still pushing at 10:30** → 71% trend days (24 cases); steep-but-early-peak → ~10%. 45° (on this scale) happened only twice → 30° is the threshold.
- **Reversals/exhaustion**: tip at a key level (PDH/PDL, PMH/PML, SMA200/400, 5-day H/L) → 45% reversed vs 20%; + heavy volume → 61%. Pivots, HTF trend, gap direction: no effect. Flattening around 11–12 is usually a pause, not the end.
- Live log 2026-10-05: 27 closed trades, 56% wins, +6.0R; S6 best; afternoon (after 2 PM) weak; median stop 0.16% / T1 0.20% of price → moves are tiny vs option spreads (main concern). 189 POSSIBLE alerts = noise.

- **Session 2 tests (2026-10-06):** minimum move size (T1>=0.2-0.4% / stop>=0.15-0.3%): no consistent gain, not added (analysis/minmove.py). Pin bars at key levels on 2/5/10/15/20/30/60/65-min: 15m+ no edge, few trades; 2m ~55% wins ~+0.1R/trade; 10m 58-65% but only 4/12 tickers positive in bad month (analysis/pinbar.py, pinbar_tf.py). By type (2m): day low/high retest 63-64% wins = best; broken-level retest from the other side (SPY 10/6 PM-high type) 51% = coin flip.
- Why 10/6 alerts didn't fire: SPY PM-high retest from above isn't an S2 level; GOOGL blocked by S2 400-SMA rule + first-hour "higher low" rule; IWM rounded bottom at no level, below SMA400, weak volume.
- Old TradingView webhook errors (500 Sep 25-29, 404 Sep 30-Oct 1) are history; since Oct 2 all delivered. User's plain price alerts ("X Crossing ...") also hit the webhook -> RAW rows; told user to uncheck Webhook on those.

- Lunch exception test (10/6, market-wide lunch selloff, user asked): lunch trades in trend direction still lose (bad month 36% wins -12R; strong-trend-day only -13R). Keep lunch block. NVDA 10/6 12:06 doji = continuation pause under VWAP at EMA20 (S5 family), not a reversal; future test idea: 'small rejection candle at EMA20 below VWAP in downtrend -> puts' (and mirror).

- 'Breakdown with no pullback' test (10/6, IWM 11:52 drop; analysis/vwap_nopb.py): close beyond VWAP + 10-bar range, 3 candles no reclaim -> enter. Loses: all 44-50% wins, bad month -43R at 1R; after chop 38-47%, negative. Confirms waiting for a retest. Not added.

- User idea 10/7 (analysis/orb_ema9.py): 30m opening-range break -> retest of 9 EMA on 2m AND 5m -> entry when trend agrees. Loses: with trend filter good month 50% wins ~-2R, bad month 36% -20R (1R exits); 1/12 tickers positive both months. Not added.

- 10/7 quiet grind-up day (AMZN/GOOGL/QQQ/SPY +3-6 from morning low, RVOL ~0.8): script took morning puts, few calls. S5 pullbacks rejected by volume rule. Test A (analysis/s5_quiet.py) S5 without volume rule: the extra low-volume trades lose in both months (41%/-7R, 40%/-12R; 0/12 tickers positive). Volume rule stays. Next candidate: test B = block counter-trend trades once day is clearly trending.

- Test B (analysis/testB_counter.py): block trades against an established day trend (after 10:30, >=80% of last hour on one VWAP side + beyond day open). Blocked trades are almost all S2 reversals: good month +24.8R (they WIN), bad month -5.3R. Net: good month 66->51R, bad -1->+1R. Not added. 10/7 charts: morning puts were WITH the trend at the time (premarket+open downtrend, V-turn ~10:45); not counter-trend.

- **10/9 key finding (analysis/stops_exits.py):** user's complaint "right direction, but the move came later" is confirmed: ~1 in 4 losers later went 2R+ our way; typical best move comes 30-36 min after entry; median stop only 0.15% of price. Wider stops / 10m trailing (same $ risk) barely change R before costs (good month 55R -> 25-44R, bad -12R -> -3..-7R). BUT with option costs (round trip 0.02% of stock price ~ liquid 0DTE) EVERY version loses: NOW -24R / -73R; stop x2 + 10m trail -9R / -37R; stop x3 -2R / -29R. Tight stops make costs eat ~0.13R per trade. => the 2m edge (~+0.1R/trade) is smaller than costs. Next agreed step: build/test 10m and 30m versions (bigger stops -> costs smaller) before any script change. 5m exact test needs 5m exports from user.

## 7. Open items / next steps
0. **Status at handoff (10/8):** user was installing CC-Multi V8 (looser pin rule) + dashboard v8 and recreating alerts (webhook on, toast pop-ups off). Confirm it's running ("dashboard v8" title, teal PIN BAR rows with bell). Plan: let V8 run 3–4 weeks, then review the Archive tab live results (incl. PIN BAR alerts: did price break the level, 1R vs stop) before letting anything affect trades.
   - Live 10/7 (to 14:30): 38 closed trades, 53% wins, −1.6R; S5 0/3; S6 61%. Only S1 alert was F puts with a 1-cent stop → candidate test: minimum STOP size (e.g. ≥0.10% of price) — not yet tested.
   - Open idea backlog (test in Python first, one at a time): minimum stop size; dedicated "quiet low-volume trend day" setup (needs more example days); NVDA-type small rejection at EMA20 under VWAP (continuation); 20 EMA / VWAP retest instead of 9 EMA for the ORB idea.
   - User shares charts + 2m CSV exports of interesting days: put uploads in their own folder, read with `python3 -I`; today's file covers only ~1–2 days, so ATR/levels come from the CSV itself.
1. After 3–4 weeks of live alerts: export the sheet's **Archive** tab (Drive connector xlsx export works) + user's broker executions → evaluate every alert type (incl. trend-day info alerts) on live data before letting any affect trades.
2. Candidate tunings to test then (one at a time): minimum move size (T1 ≥0.3–0.4% / min stop), shorter ticker list (liquid 0DTE names), no new entries after 2:30–3:00, minimum entry RVOL (~0.5), hide POSSIBLE rows from the dashboard (keep in log) — user hasn't decided.
3. User was offered: dashboard sound for BUY/SELL alerts (declined for now).
4. Trend-day research could improve with more history (3–6 months).
