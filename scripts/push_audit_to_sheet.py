#!/usr/bin/env python3
"""Publish an OpenClaw L10 review to the Google Sheet as a NEW TAB.

Contributor-facing: plain-language verdict + reason + fix per task. Each run adds
its own dated worksheet (never overwrites). Content comes from a feedback JSON
(list of {task, scenario, did, verdict, why, fix}); author one per run.

    python3 scripts/push_audit_to_sheet.py \
        --feedback "OpenClaw QC/Audit-runs/2026-06-08-feedback.json" --tab "L10 2026-06-08"

Auth: service account at .creds/sa.json (gitignored); the sheet must be shared
with the SA's client_email as Editor.
"""
import argparse, json, os, sys, datetime
import gspread
from google.oauth2.service_account import Credentials

SHEET_ID = "1Ld547RXFeh91dd4c5eO1XKla2xlHkz0eMVphg1CNwx0"
SA = ".creds/sa.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
HEADER = ["Task ID", "Scenario", "What the agent had to do",
          "Verdict", "Why this verdict", "What to fix"]


def rank(v):
    u = v.upper()
    if "NON-FAIL" in u: return 1
    if u.startswith("FAIL"): return 0
    if "PASS" in u: return 2
    return 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--feedback", required=True, help="path to the run's feedback JSON")
    ap.add_argument("--tab", default=f"L10 {datetime.date.today().isoformat()}")
    ap.add_argument("--sheet-id", default=SHEET_ID)
    a = ap.parse_args()
    if not os.path.exists(SA):
        print(f"error: {SA} missing (service account)", file=sys.stderr); return 2

    rows = json.load(open(a.feedback))
    rows.sort(key=lambda r: rank(r["verdict"]))
    table = [[r["task"], r["scenario"], r["did"], r["verdict"], r["why"], r["fix"]] for r in rows]

    n_fix = sum(rank(r["verdict"]) == 0 for r in rows)
    n_min = sum(rank(r["verdict"]) == 1 for r in rows)
    n_ok = sum(rank(r["verdict"]) == 2 for r in rows)
    banner = (f"OpenClaw L10 — rubric review · {len(rows)} tasks · "
              f"{n_fix} need fixes · {n_min} minor tweaks · {n_ok} look good")

    gc = gspread.authorize(Credentials.from_service_account_file(SA, scopes=SCOPES))
    sh = gc.open_by_key(a.sheet_id)
    title, existing, n = a.tab, {w.title for w in sh.worksheets()}, 2
    while title in existing:
        title = f"{a.tab} ({n})"; n += 1

    ws = sh.add_worksheet(title=title, rows=len(table) + 4, cols=len(HEADER))
    ws.update(range_name="A1", values=[[banner] + [""] * (len(HEADER) - 1), HEADER] + table)
    ws.format("A1:F1", {"textFormat": {"bold": True, "italic": True}})
    ws.format("A2:F2", {"textFormat": {"bold": True}})
    ws.format("D3:D100", {"textFormat": {"bold": True}})
    print(f"Wrote tab {title!r} ({len(table)} rows) to {sh.title!r}")
    print(f"  {sh.url}#gid={ws.id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
