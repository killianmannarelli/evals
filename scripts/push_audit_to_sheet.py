#!/usr/bin/env python3
"""Push an OpenClaw L10 audit run to the Google Sheet as a NEW TAB.

Each run adds its own dated worksheet (never overwrites a prior one), in the
same plain-English schema as the original `Sheet1`. Auth uses the service
account at .creds/sa.json (gitignored) — the sheet must be shared with the SA's
client_email.

    python3 scripts/push_audit_to_sheet.py            # creates tab "L10 2026-06-08"
    python3 scripts/push_audit_to_sheet.py --tab "L10 2026-06-09 rerun"

Reads this run's results from .openclaw_handoff/audit-2026-06-08/{validated_text,
platform_eval}/ for the 10 viewer-only tasks; the 3 inline tasks are embedded
(pixel/inline-verified). Adjust SHEET_ID / paths for future runs.
"""
import argparse, glob, json, os, sys, datetime
import gspread
from google.oauth2.service_account import Credentials

SHEET_ID = "1Ld547RXFeh91dd4c5eO1XKla2xlHkz0eMVphg1CNwx0"
SA = ".creds/sa.json"
WS = ".openclaw_handoff/audit-2026-06-08"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

HEADER = ["Task ID", "Universe / category", "What the agent had to do", "Verdict",
          "Why this verdict (plain English)", "What to fix",
          "Platform score", "Drawer (viewer 2nd opinion)", "Audit basis"]

# The 3 fully-auditable tasks (rehydrated inline + pixels) — rich plain-English.
INLINE = [
 ["6a0b6c51…753e", "Jamal — grocery cereal shelf (photos)",
  "List every cereal on the shelves with its average price into a spreadsheet.", "FAIL",
  "Penalizes listing 4 cereals (Golden Grahams, Krave, Cocoa Krispies, Fruity Pebbles) as absent, but the photos show all 4 present (pixel-confirmed). Rubric unchanged since 06-07 — not fixed; still stuck at L10.",
  "Remove the 4 present-product −5 decoys (C26–C29).", "4%", "Fail (agree)", "pixel · re-confirmed"],
 ["6a14c6a0…0eb", "Gabriela — source computer parts on Amazon",
  "Find each product (or a valid alternative), record link + price, update a savings sheet.", "FAIL",
  "Open prompt (exact item OR a valid alternative), but 10 criteria pin one fixed Amazon price/total — any valid alternative fails. Rubric unchanged since 06-07 — not fixed; still stuck at L10.",
  "Relax the 10 fixed-price criteria to internal-consistency checks (sum/derived totals, MEMORY matches CSV).",
  "36%", "Non-Fail (I'm stricter)", "inline · re-confirmed"],
 ["6a14c6a0…0f0", "Brandon — social-media SSOT audit",
  "Rebuild the social-media plan from the handwritten SSOT and email the mismatches.", "Non-Fail (was Fail)",
  "Contributor fixed the self-contradictory phone gold (C20), the filename extensions (C24 .png), the 'regular regular' typo, and removed C28. One Major remains: C26 fabricates a dashboard 'June 24 instead of July 1' mismatch — SSOT pixels show the dashboard IS June 24 and July 1 is the maintenance post. Major 1/27 = 3.7% → Non-Fail.",
  "Drop the dashboard/July-1 clause from C26; fix C14/C25 filename to the real 'final viasual.png'.",
  "40%", "Fail → reconciled Non-Fail", "pixel · re-audit (rubric changed)"],
]

def short(tid): return f"{tid[:8]}…{tid[-4:]}"

def text_rows():
    """Assemble the 10 viewer-only tasks from the validated_text + platform_eval JSON."""
    rows = []
    for f in sorted(glob.glob(f"{WS}/validated_text/*.json")):
        v = json.load(open(f)); tid = v["task_id"]
        pe = json.load(open(f"{WS}/platform_eval/{tid}.json"))
        cat = pe.get("category") or pe.get("universe") or ""
        crit0 = (pe.get("criteria") or [{}])[0].get("text", "").strip()
        score = pe.get("score") or {}
        pct = f"{score.get('pct')}%" if score.get("pct") is not None else ""
        drawer = (pe.get("embedded_audit") or {}).get("embedded_verdict") or "?"
        cf = v.get("confirmed_findings") or []
        nu = len(v.get("unverifiable") or [])
        verdict = v.get("verdict", "?")
        if verdict == "Pass":
            verdict = "Pass (text-structural)"
            fix = "None — but verify its visual/factual golds once inputs unlock."
        elif cf:
            fix = "Split: " + ", ".join(f"{x.get('criterion')}" for x in cf) + " (§9a fuse distinct concerns)."
        else:
            fix = "—"
        why = (v.get("summary") or "").strip()
        if nu:
            why += f" [{nu} factual/visual gold(s) UNVERIFIABLE — inputs CDS-locked.]"
        rows.append([short(tid), cat, (crit0[:140] + ("…" if len(crit0) > 140 else "")) or "(rubric only)",
                     verdict, why[:480], fix, pct, f"{drawer}", "text-only (viewer scrape)"])
    return rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tab", default=f"L10 {datetime.date.today().isoformat()}")
    ap.add_argument("--sheet-id", default=SHEET_ID)
    a = ap.parse_args()
    if not os.path.exists(SA):
        print(f"error: {SA} missing (service account)", file=sys.stderr); return 2

    gc = gspread.authorize(Credentials.from_service_account_file(SA, scopes=SCOPES))
    sh = gc.open_by_key(a.sheet_id)

    title = a.tab
    existing = {w.title for w in sh.worksheets()}
    n = 2
    while title in existing:           # never overwrite — uniquify
        title = f"{a.tab} ({n})"; n += 1

    data = INLINE + text_rows()
    # classify verdict case-insensitively: Fail=0, Non-Fail=1, Pass=2
    def cls(v):
        u = v.upper()
        if "NON-FAIL" in u: return 1
        if u.startswith("FAIL"): return 0
        if "PASS" in u: return 2
        return 1
    data.sort(key=lambda r: cls(r[3]))

    n_fail = sum(cls(r[3]) == 0 for r in data)
    n_nf = sum(cls(r[3]) == 1 for r in data)
    n_pass = sum(cls(r[3]) == 2 for r in data)
    banner = (f"OpenClaw L10 audit — {a.tab.replace('L10 ','')} · all 13 pending · "
              f"{n_fail} Fail / {n_nf} Non-Fail / {n_pass} Pass · "
              f"spec query 304995 unchanged · 3 pixel-audited, 10 text-only (inputs CDS-locked)")

    ws = sh.add_worksheet(title=title, rows=len(data) + 4, cols=len(HEADER))
    body = [[banner] + [""] * (len(HEADER) - 1), HEADER] + data
    ws.update(range_name="A1", values=body)
    ws.format("A2:I2", {"textFormat": {"bold": True}})
    ws.format("A1:I1", {"textFormat": {"bold": True, "italic": True}})
    print(f"Wrote tab {title!r} ({len(data)} rows) to {sh.title!r}")
    print(f"  {sh.url}#gid={ws.id}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
