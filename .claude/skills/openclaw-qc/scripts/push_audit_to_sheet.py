#!/usr/bin/env python3
"""Publish an OpenClaw L10 review to the Google Sheet as a NEW TAB, in the exact
format of `Sheet1` (blank row 1, header on row 2, two frozen rows, 10 columns).

Contributor-facing, plain language. Each run adds its own dated worksheet (never
overwrites). Content comes from a feedback JSON (one object per task with keys:
task, scenario, did, verdict, why, fix, platform, viewer, agree, link).

    python3 scripts/push_audit_to_sheet.py \
        --feedback "OpenClaw QC/Audit-runs/2026-06-08-feedback.json" --tab "L10 2026-06-08"

Auth: service account at .creds/sa.json (gitignored); sheet shared with the SA.
"""
import argparse, json, os, sys, datetime
import gspread
from google.oauth2.service_account import Credentials

SHEET_ID = "1Ld547RXFeh91dd4c5eO1XKla2xlHkz0eMVphg1CNwx0"
SA = ".creds/sa.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
# Exact Sheet1 header (row 2).
HEADER = ["Task ID", "Scenario", "What the agent had to do", "Verdict",
          "Confidence /100 (ship as-is)",
          "Why this verdict (plain English)", "What to fix",
          "Platform score (model's auto-grade)", "Viewer 2nd opinion",
          "Do they agree?", "Open the task"]
FIELDS = ["task", "scenario", "did", "verdict", "confidence", "why", "fix", "platform", "viewer", "agree", "link"]


def rank(v):
    u = v.upper()
    if "NON-FAIL" in u: return 1
    if u.startswith("FAIL"): return 0
    if "PASS" in u: return 2
    if "PENDING" in u: return 3   # un-materialized tasks sort to the bottom
    return 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--feedback", required=True)
    ap.add_argument("--tab", default=f"L10 {datetime.date.today().isoformat()}")
    ap.add_argument("--sheet-id", default=SHEET_ID)
    a = ap.parse_args()
    if not os.path.exists(SA):
        print(f"error: {SA} missing", file=sys.stderr); return 2

    rows = json.load(open(a.feedback))
    rows.sort(key=lambda r: rank(r["verdict"]))
    table = [[r.get(k, "") for k in FIELDS] for r in rows]

    gc = gspread.authorize(Credentials.from_service_account_file(SA, scopes=SCOPES))
    sh = gc.open_by_key(a.sheet_id)
    title, existing, n = a.tab, {w.title for w in sh.worksheets()}, 2
    while title in existing:
        title = f"{a.tab} ({n})"; n += 1

    ws = sh.add_worksheet(title=title, rows=len(table) + 5, cols=len(HEADER))
    # Row 1 blank, header on row 2, data from row 3 — mirrors Sheet1.
    ws.update(range_name="A2", values=[HEADER] + table)
    ws.freeze(rows=2)
    ws.format(f"A1:K{len(table)+2}", {"wrapStrategy": "WRAP"})   # Sheet1 wraps every cell
    ws.format("A2:K2", {"textFormat": {"bold": True},
                        "backgroundColor": {"red": 0.847, "green": 0.867, "blue": 0.898}})  # header band #d8dde5
    ws.format("D3:D200", {"textFormat": {"bold": True}})
    # Confidence column (E): bold + centered for at-a-glance scanning.
    ws.format("E3:E200", {"textFormat": {"bold": True}, "horizontalAlignment": "CENTER"})
    # verdict-cell colors (Sheet1): FAIL #f4cccc, Non-Fail #fcedc6, Pass #d9ead3.
    # rows are sorted FAIL -> Non-Fail -> Pass, so colour contiguous D blocks.
    VBG = {"FAIL": {"red": 0.957, "green": 0.800, "blue": 0.800},
           "Non-Fail": {"red": 0.988, "green": 0.929, "blue": 0.776},
           "Pass": {"red": 0.851, "green": 0.918, "blue": 0.827},
           "Pending": {"red": 0.937, "green": 0.937, "blue": 0.937}}  # neutral grey for un-materialized
    _r = 3
    for _v in ("FAIL", "Non-Fail", "Pass", "Pending"):
        _n = sum(1 for t in table if t[3] == _v)
        if _n:
            ws.format(f"D{_r}:D{_r + _n - 1}", {"backgroundColor": VBG[_v]})
            _r += _n
    print(f"Wrote tab {title!r} ({len(table)} rows) to {sh.title!r}")
    print(f"  {sh.url}#gid={ws.id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
