#!/usr/bin/env python3
"""Compile EVERY committed audit into one living master tab — ONE row per task
(latest real audit wins), refreshed on every run.

Reads all of `OpenClaw QC/Audit-runs/*.json` (the per-run feedback records),
dedupes by task_id keeping the most recent NON-Pending audit (falling back to
Pending only if a task was never materialised), and rewrites a single Sheet tab
(default "ALL AUDITS (latest per task)"). Idempotent — safe to re-run after every
audit; it always reflects the full history deduped to current state.

  python3 build_master_sheet.py [--tab "ALL AUDITS (latest per task)"]

Auth: service account at .creds/sa.json (gitignored), same Sheet as the dated tabs.
"""
import argparse, json, glob, os, re, sys
import gspread
from google.oauth2.service_account import Credentials

SHEET_ID = "1Ld547RXFeh91dd4c5eO1XKla2xlHkz0eMVphg1CNwx0"
SA = ".creds/sa.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
RUNS_DIR = "OpenClaw QC/Audit-runs"

HEADER = ["Task ID", "Attempt ID", "Specialization", "Layer", "Last audited", "Verdict",
          "Confidence /100", "Scenario", "What the agent had to do",
          "Why this verdict (plain English)", "What to fix",
          "Platform score (model's auto-grade)", "Viewer 2nd opinion",
          "Do they agree?", "Open the task"]
FIELDS = ["task", "attempt", "specialization", "layer", "last_audited", "verdict", "confidence",
          "scenario", "did", "why", "fix", "platform", "viewer", "agree", "link"]

SUFFIX_RANK = {"": 0, "REAUDIT": 1, "a": 1, "b": 2, "c": 3, "d": 4, "e": 5,
               "f": 6, "g": 7, "h": 8, "i": 9, "j": 10}


def norm(v):
    u = str(v).strip().upper()
    if u.startswith("FAIL"):
        return "FAIL"
    if "NON" in u:
        return "Non-Fail"
    if "PASS" in u:
        return "Pass"
    if "PEND" in u:
        return "Pending"
    return v or ""


def parse_run(fn):
    """(date, suffix_rank, layer, label) from a feedback filename."""
    base = re.sub(r"-(feedback|flagged-attempts)\.json$", "", fn)
    base = re.sub(r"\.json$", "", base)
    date = base[:10]
    tail = base[10:]
    sfx = ""
    if tail[:1].isalpha():            # date-attached suffix, e.g. 2026-06-22e
        sfx = tail[0]
        tail = tail[1:]
    layer, special = "", ""
    for p in [p for p in tail.split("-") if p]:
        m = re.match(r"(L-?\d+)([a-z]?)$", p)
        if m:
            layer = m.group(1)
            if m.group(2):
                sfx = m.group(2)       # layer-attached suffix, e.g. L0b
        elif p.upper() == "REAUDIT":
            special = "REAUDIT"
    rank = SUFFIX_RANK.get(special or sfx, 0)
    label = date + (f" ({sfx})" if sfx else "") + (" re-audit" if special else "")
    return date, rank, (layer or "L10"), label


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tab", default="ALL AUDITS (latest per task)")
    ap.add_argument("--runs-dir", default=RUNS_DIR)
    ap.add_argument("--sheet-id", default=SHEET_ID)
    a = ap.parse_args()
    if not os.path.exists(SA):
        print(f"error: {SA} missing", file=sys.stderr)
        return 2

    best = {}  # task -> (sortkey, row_dict)
    for f in glob.glob(f"{a.runs_dir}/*.json"):
        date, rank, layer, label = parse_run(os.path.basename(f))
        mtime = os.path.getmtime(f)
        try:
            rows = json.load(open(f))
        except Exception:
            continue
        for r in rows:
            t = r.get("task")
            if not t:
                continue
            v = norm(r.get("verdict"))
            is_real = 0 if v == "Pending" else 1
            # run_date (the ACTUAL day the audit ran) overrides the filename's anchor
            # date for recency. The tab/record date is a cosmetic series anchor and can
            # be older than another layer's anchor even when this run is more recent
            # (e.g. an L10 run anchored 06-22 that actually ran 06-29 must still win over
            # an L8 record anchored 06-26 for tasks queued at both layers).
            eff_date = r.get("run_date") or date
            eff_label = label
            if r.get("run_date") and r["run_date"] != date:
                eff_label = f'{label} · run {r["run_date"]}'
            sk = (is_real, eff_date, rank, mtime)
            if t not in best or sk > best[t][0]:
                row = {
                    "task": t, "attempt": r.get("attempt", "") or "",
                    "specialization": r.get("specialization", "") or "",
                    "layer": layer, "last_audited": eff_label, "verdict": v,
                    "confidence": r.get("confidence", ""),
                    "scenario": r.get("scenario", ""), "did": r.get("did", ""),
                    "why": r.get("why", ""), "fix": r.get("fix", ""),
                    "platform": r.get("platform", ""), "viewer": r.get("viewer", ""),
                    "agree": r.get("agree", ""), "link": r.get("link", ""),
                }
                best[t] = (sk, row)

    rank_v = {"FAIL": 0, "Non-Fail": 1, "Pass": 2, "Pending": 3}
    rows = [b[1] for b in best.values()]
    rows.sort(key=lambda r: (rank_v.get(r["verdict"], 1), r["layer"], r["task"]))
    table = [[r.get(k, "") for k in FIELDS] for r in rows]

    gc = gspread.authorize(Credentials.from_service_account_file(SA, scopes=SCOPES))
    sh = gc.open_by_key(a.sheet_id)
    # Replace the master tab each run (idempotent latest-per-task snapshot).
    try:
        sh.del_worksheet(sh.worksheet(a.tab))
    except gspread.WorksheetNotFound:
        pass
    ws = sh.add_worksheet(title=a.tab, rows=len(table) + 5, cols=len(HEADER))
    ws.update(range_name="A2", values=[HEADER] + table)
    ws.freeze(rows=2)
    last = chr(ord("A") + len(HEADER) - 1)
    vcol = chr(ord("A") + FIELDS.index("verdict"))
    ccol = chr(ord("A") + FIELDS.index("confidence"))
    vi = FIELDS.index("verdict")
    ws.format(f"A1:{last}{len(table)+2}", {"wrapStrategy": "WRAP"})
    ws.format(f"A2:{last}2", {"textFormat": {"bold": True},
                              "backgroundColor": {"red": 0.847, "green": 0.867, "blue": 0.898}})
    ws.format(f"{vcol}3:{vcol}2000", {"textFormat": {"bold": True}})
    ws.format(f"{ccol}3:{ccol}2000", {"textFormat": {"bold": True}, "horizontalAlignment": "CENTER"})
    VBG = {"FAIL": {"red": 0.957, "green": 0.800, "blue": 0.800},
           "Non-Fail": {"red": 0.988, "green": 0.929, "blue": 0.776},
           "Pass": {"red": 0.851, "green": 0.918, "blue": 0.827},
           "Pending": {"red": 0.937, "green": 0.937, "blue": 0.937}}
    _r = 3
    for _v in ("FAIL", "Non-Fail", "Pass", "Pending"):
        _n = sum(1 for t in table if t[vi] == _v)
        if _n:
            ws.format(f"{vcol}{_r}:{vcol}{_r + _n - 1}", {"backgroundColor": VBG[_v]})
            _r += _n
    from collections import Counter
    print(f"Wrote tab {a.tab!r}: {len(table)} unique tasks | "
          f"{dict(Counter(t[vi] for t in table))}")
    print(f"  {sh.url}#gid={ws.id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
