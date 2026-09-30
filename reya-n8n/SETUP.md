# Reya Office on n8n: setup (one time, about 15 minutes)

Once set up, this runs on its own in n8n. Claude is not involved in the daily run.

## 1. Load the fixed sheet into the SAME Google Sheet
1. Open `Reya_B2B_Master_Sheet` in Google Sheets (reyacandles@gmail.com).
2. **File → Import → Upload** → `Reya_B2B_Master_Sheet_FIXED.xlsx`.
3. Choose **Replace current sheet**. This keeps the same file, so n8n still finds it.
4. Make sure the tab is still called **Sheet1**.

What changed in the sheet:
- 6 candle makers are marked `مستبعد - صانع شموع` and will never be contacted.
- The 20 contacts added today were wrongly labelled "wedding planners". They are now `ح — home décor & concept stores` with IDs `AMM-D-0001` to `AMM-D-0020`, and their drafts were reset.
- 21 drafts that were stuck (never approved, because the Telegram step was crashing) were reset, so they'll be redrafted and sent to Telegram again.
- A reminder stuck since 27 Sep (AMM-W-0004) is closed.
- New column `approval_deadline`.
- `(cite index=…)` junk removed from the notes.

## 2. Import the two workflows
In n8n: **Workflows → ⋯ → Import from file**, one at a time:
- `workflows/Reya_Office_1_Daily_Run.json`
- `workflows/Reya_Office_2_Telegram_Approvals.json`

Open every node with a ⚠️ and re-select its credential if asked: *Reya Google Sheets*, *Reya B2B bot*, *Anthropic API*, *Reya Gmail*.

## 3. Turn the old ones OFF, then delete them
Deactivate and delete: *B2B - 1 Researcher*, *2 Writer drafts*, *3 Approvals (Telegram buttons)*, *4 Reminders*, and *Reya Birthday - 0 Setup*.
**Important:** only ONE workflow may listen to the Telegram bot. If the old Approvals workflow stays active, the buttons will break.

## 4. Activate the new ones
Switch both to **Active**. You can put them in one n8n folder or project called "Reya Office".

## 5. Test
Open *Daily Run* and click **Execute workflow**. That's the "▶ Start the day" button. Within a few minutes:
- 🔎 a research summary arrives on Telegram,
- draft cards arrive, each showing "⏰ Approve before …",
- 📝 manager notes arrive if any draft was fixed or blocked.
Tap a button to check the reply. If you don't tap a card, it gets denied automatically after 6 hours and you receive a ⏰ notice.

## Changing settings
In each code step, near the top: `APPROVAL_HOURS=6`, `LIMIT=20`, `APPROVERS=[…]`, `MODEL`.
Better: edit `reya-n8n/build.py`, run `python3 reya-n8n/build.py`, and re-import.
