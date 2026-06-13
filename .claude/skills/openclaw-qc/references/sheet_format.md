# Output sheet format — match `Sheet1` EXACTLY

The Google Sheet (`1Ld547RXFeh91dd4c5eO1XKla2xlHkz0eMVphg1CNwx0`) holds one tab per run. Every new tab must
replicate `Sheet1` exactly. `scripts/push_audit_to_sheet.py` already encodes all of this — don't hand-roll it.

## Structure
- **Row 1: blank.** **Row 2: header.** Data from row 3.
- **Freeze 2 rows.** Header row **bold**. Verdict column (D) **bold**. **Every cell `wrapStrategy: WRAP`.**
- **Colours:** header band `#d8dde5`; verdict cell (D) by verdict — **FAIL `#f4cccc`** (red), **Non-Fail `#fcedc6`**
  (cream), **Pass `#d9ead3`** (green). All other cells white. (`push_audit_to_sheet.py` applies these.)
- **11 columns, header text verbatim:**
  1. `Task ID` — the **full 24-char** task id (never the `…` short form).
  2. `Scenario` — one short human line (persona + what the task is).
  3. `What the agent had to do` — one plain sentence.
  4. `Verdict` — `FAIL` (caps) / `Non-Fail` / `Pass`.
  5. `Confidence /100 (ship as-is)` — bold, centered. How deliverable the rubric is *without fixes*: 100 = spotless,
     ~50 = a non-fail sitting on a Fail line, ~38 = a fail one fix from passing, ~5 = catastrophic. Computed by
     `scripts/confidence.py` from the verdict bands (+ a small discount for unverifiable golds) — never hand-set.
     Leave blank for `Pending` rows (no bands).
  6. `Why this verdict (plain English)`
  7. `What to fix`
  8. `Platform score (model's auto-grade)` — e.g. `36%`.
  9. `Viewer 2nd opinion` — the drawer's verdict: `Fail` / `Non-Fail`.
  10. `Do they agree?` — human one-liner (e.g. "Yes — both agree it fails", "No — I'm stricter; the viewer missed it").
  11. `Open the task` — the viewer URL (auto-links as a hyperlink).
- Sort rows: FAIL → Non-Fail → Pass.

## Voice (columns 2,3,6,7,10) — contributor-facing
- **Plain and human.** No rule names (§9a, Rule 19c, 6a/6b), no internal jargon (drawer/band/denominator/CDS/
  text-only/unverifiable/spot-check), no "CB". Criterion numbers (C26, C12) are fine — they help locate the fix.
- **Present tense, no history.** Don't reference prior runs ("unchanged since…", "was Fail", "still stuck").
- **Pass** = "No issues found — the checks are clear and supported." **Fix** for a pass = "None — looks good."

## Feedback JSON (what the writer consumes)
A list of objects, one per task:
`{task (full id), scenario, did, verdict, confidence, why, fix, platform, viewer, agree, link}`
(`confidence` = int 0-100 or "" for Pending; compute with `confidence.confidence_for(reconciled_dict, n_unverifiable)`)
Then: `python3 scripts/push_audit_to_sheet.py --feedback <file>.json --tab "<Layer> <YYYY-MM-DD>"`
The writer never overwrites an existing tab name (it appends "(2)") — delete the old tab first if replacing.
