// CC-Multi alert archive (Google Apps Script, bound to the "CC-Multi Signal Log (live)" sheet)
// Every hour: reads the n8n alert log and appends any NEW rows to the "Archive" tab.
// The Archive tab is permanent - it survives n8n re-imports / resets.
// One-time setup: paste this file, then run setup() once and allow access.

const LOG_URL = 'https://vmi3437039.contaboserver.net/webhook/signals?csv=1';

function archive() {
  const res = UrlFetchApp.fetch(LOG_URL, { muteHttpExceptions: true });
  if (res.getResponseCode() !== 200) return;              // n8n unreachable -> try again next hour
  const rows = Utilities.parseCsv(res.getContentText());
  if (rows.length < 2) return;                             // header only, nothing new
  const ss = SpreadsheetApp.getActive();
  const sh = ss.getSheetByName('Archive') || ss.insertSheet('Archive');
  sh.getRange('A:L').setNumberFormat('@');                 // keep values exactly as sent (no auto date/number changes)
  if (sh.getLastRow() === 0) sh.appendRow(rows[0]);
  const key = r => [r[0], r[3], r[4], r[2]].join('|');    // received | ticker | action | time
  const n = sh.getLastRow() - 1;
  const have = new Set(n > 0 ? sh.getRange(2, 1, n, 12).getValues().map(r => key(r.map(String))) : []);
  const add = rows.slice(1).filter(r => r[0] && !have.has(key(r)));
  if (add.length) sh.getRange(sh.getLastRow() + 1, 1, add.length, rows[0].length).setValues(add);
}

function setup() {
  ScriptApp.getProjectTriggers().forEach(t => ScriptApp.deleteTrigger(t));   // no duplicate timers
  ScriptApp.newTrigger('archive').timeBased().everyHours(1).create();
  archive();
}
