"""src/build_gold.py — build gold/customer_findings.json from the customer feedback sheet
("Customer Feedback 2026-07-06"), for the recall backtest.

Reads the 'Findings (per flag)' tab (one row per flag): Task ID / Tier / Defect Type / Rubric
IDs. This is READ-ONLY on the customer sheet. Re-run whenever the sheet changes.

  python -m src.build_gold                      # default sheet -> gold/customer_findings.json
  python -m src.build_gold --sheet <id> --out gold/foo.json
"""
from __future__ import annotations
import argparse, collections, json
from pathlib import Path
from src import common

SHEET_DEFAULT = "1muNhEv7AdxtiC7KyayzvdbfCx1GLF85aOuY2Dec4cSg"
TAB = "Findings (per flag)"
TIER_MAP = {"ACTION REQUIRED": "action_required", "ACTION_REQUIRED": "action_required",
            "REVIEW": "review_recommended", "REVIEW RECOMMENDED": "review_recommended"}


def build(sheet_id=SHEET_DEFAULT, out="gold/customer_findings.json"):
    ss = common.sheets()
    rows = ss.values().get(spreadsheetId=sheet_id, range=f"'{TAB}'!A1:P400").execute().get("values", [])
    hdr = rows[0]
    idx = {h.strip(): i for i, h in enumerate(hdr)}

    def cell(r, name):
        i = idx.get(name)
        return (r[i].strip() if i is not None and i < len(r) else "")

    gold = collections.defaultdict(list)
    for r in rows[1:]:
        tid = cell(r, "Task ID")
        if not tid:
            continue
        rid = cell(r, "Rubric IDs")
        rubric_ids = [int(x) for x in rid.replace(";", ",").replace(" ", ",").split(",") if x.strip().isdigit()]
        gold[tid].append({
            "defect_type": cell(r, "Defect Type") or "UNKNOWN",
            "tier": TIER_MAP.get(cell(r, "Tier").upper(), "review_recommended"),
            "rubric_ids": rubric_ids,
        })
    obj = {"source": sheet_id, "tab": TAB, "n_tasks": len(gold),
           "n_findings": sum(len(v) for v in gold.values()), "tasks": dict(gold)}
    outp = common.PKG / out
    outp.parent.mkdir(parents=True, exist_ok=True)
    json.dump(obj, open(outp, "w"), indent=1)
    # also emit the task-id list so `run.py --ids gold/customer_tasks.txt --backtest ...` works
    (outp.parent / "customer_tasks.txt").write_text("\n".join(gold) + "\n")
    dtc = collections.Counter(f["defect_type"] for v in gold.values() for f in v)
    print(f"gold: {obj['n_tasks']} tasks / {obj['n_findings']} findings -> {outp}")
    print("  by defect_type:", dict(dtc.most_common()))
    return obj


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet", default=SHEET_DEFAULT)
    ap.add_argument("--out", default="gold/customer_findings.json")
    a = ap.parse_args()
    build(a.sheet, a.out)
