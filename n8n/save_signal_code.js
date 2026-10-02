// Accepts ANY TradingView body. Never drops a signal: if it can't be parsed, the raw text is shown.
const KEY = 'change-me';
const ACT = {'1':'BUY CALLS','-1':'BUY PUTS','2':'SELL HALF CALLS','-2':'SELL HALF PUTS','3':'EXIT CALLS','-3':'EXIT PUTS'};
const STR = {'1':'S1 ORB 30m','2':'S2 SWEEP REVERSAL','3':'S3 VWAP','4':'S4 OPENING DRIVE'};
const store = $getWorkflowStaticData('global');
store.signals = store.signals || [];
for (const item of $input.all()) {
  let b = item.json.body;
  if ((b == null || (typeof b === 'object' && Object.keys(b).length === 0)) && item.binary && item.binary.data) {
    b = Buffer.from(item.binary.data.data, 'base64').toString('utf8');
  }
  if (b == null) continue;
  let raw = typeof b === 'string' ? b : JSON.stringify(b);
  if (typeof b === 'string') {
    const cleaned = b.replace(/\[\[[^\]]*\]\]/g, 'null').replace(/\{\{[^}]*\}\}/g, 'null').replace(/\bNaN\b/g, 'null');
    try { b = JSON.parse(cleaned); } catch (e) { b = { ticker: '?', action: 'RAW', note: raw.slice(0, 300) }; }
  }
  if (b.src === 'cc-ac') {
    b.action = b.code == null ? 'SIGNAL (see chart)' : (ACT[String(Math.round(b.code))] || ('code ' + b.code));
    b.strategy = b.strat == null ? '' : (STR[String(Math.round(b.strat))] || '');
    delete b.code; delete b.strat; delete b.src;
  } else if (b.key !== undefined && b.key !== KEY) {
    b.note = 'KEY MISMATCH - check Webhook key in CC-Multi settings';
  }
  if (typeof b.rvol === 'number') b.rvol = Math.round(b.rvol * 10) / 10;
  delete b.key;
  b.received = new Date().toISOString();
  store.signals.unshift(b);
}
store.signals = store.signals.slice(0, 500);
return [{ json: { ok: true, stored: store.signals.length } }];