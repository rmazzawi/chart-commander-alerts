# chart-commander-alerts

Stores the latest stock chart-pattern alert for the "Chart Commander" workflow.

## Files
- `latest_alert.txt` — one plain-text line with the current alerts, e.g.
  "TSLA has a bull flag on the 15min chart. NVDA shows a hammer candle on the 30min chart."
  Each alert = ticker + pattern + timeframe. Overwrite it with each new alert.

## Working rules (save tokens)
- This repo is tiny: don't re-explore it, this file is the overview.
- Keep answers short and plain; the owner is not a developer, so give step-by-step instructions.
- For large files (price data, CSVs, logs), use the Headroom plugin / `/peek` if enabled:
  outline first, read only the relevant parts.
- Don't install third-party tools in cloud sessions without asking; they don't persist.
