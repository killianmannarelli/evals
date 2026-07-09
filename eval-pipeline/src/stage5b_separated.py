"""stage5b_separated — the SIDE-BY-SIDE combined tab: DRAWER (Task-level flags) and CDQ and
linters as their OWN labeled columns, so each eval is visible on its own (not merged into one
verdict). This is the view Killian wants.

Reads: runs/<id>/drawer.json (rich master verdict+flags+why), findings_llm.json (cdq_static),
findings_linters.json, digest.json. Writes a NEW tab (never overwrites).
"""
from __future__ import annotations
import json, os, sys, collections
from pathlib import Path
from src import common
from src.stage4_assemble import _redact   # reuse answer-key redaction

HEADER = ["Task ID", "Attempt ID", "Layer", "Category", "Subcategory", "Modality",
          "Platform pass@k", "mean_reward",
          "DRAWER verdict", "DRAWER flags (spec bands)", "DRAWER why",
          "CDQ verdict", "CDQ top findings",
          "Linter flags", "Open the task"]
VIEWER = "https://openclaw-viewer-mm.vercel.app/attempt/"


def _cdq_verdict(fs):
    ar = [f for f in fs if f.get("tier") == "action_required"]
    rr = [f for f in fs if f.get("tier") == "review_recommended"]
    if ar: return "fail", ar
    if rr: return "non-fail", rr
    return "pass", []


def main(cfg, run_dir, tab="eval L10_opus (drawer+CDQ+linters)"):
    run_dir = Path(run_dir)
    def load(n, d):
        p = run_dir / n
        return json.load(open(p)) if p.exists() else d
    drawer = load("drawer.json", {})
    llm = load("findings_llm.json", {})
    lint = load("findings_linters.json", {})
    digest = load("digest.json", {})
    order = list(digest)

    rows = []
    for tid in order:
        d = digest.get(tid, {})
        rs = d.get("reward") or {}
        # reward: pass@k from crit_pass_rate mean is not stored; use mean_reward
        mr = rs.get("mean_reward")
        pak = "" if mr is None else f"{round(mr*100)}%"
        # DRAWER
        dm = drawer.get(tid)
        if dm:
            dv = dm.get("verdict", "")
            dflags = " | ".join(f"{f.get('category','')} ({f.get('dimension','')})" for f in dm.get("flags", []))
            dwhy = _redact(dm.get("why", ""))          # FULL — wrap handles length; truncation reads as "cut off"
        else:
            dv, dflags, dwhy = "— (audit failed)", "", ""
        # CDQ — full text, one bullet per finding on its own line (wrap + auto row height show it all)
        cfs = [f for f in llm.get(tid, []) if f.get("check") == "cdq_static"]
        cv, ctop = _cdq_verdict(cfs)
        if not cfs:
            cv = "pass"
        ctxt = _redact("\n".join(f"• {f['defect_type']}: {f.get('explanation','')}" for f in ctop))
        # linters
        lfs = lint.get(tid, [])
        lflags = " | ".join(f"{f['check']}:{f['defect_type']}" for f in lfs)
        rows.append([
            tid, d.get("attempt_id", ""), f"L{d.get('layer','')}", d.get("category", ""),
            d.get("subcategory", ""), d.get("mm_input", ""), pak, "" if mr is None else round(mr, 3),
            dv, _redact(dflags), dwhy, cv, ctxt, lflags, VIEWER + (d.get("attempt_id") or ""),
        ])
    dr = {"Fail": 0, "Non-Fail": 1, "Pass": 2, "— (audit failed)": 3, "": 4}
    cr = {"fail": 0, "non-fail": 1, "pass": 2}
    rows.sort(key=lambda r: (dr.get(r[8], 5), cr.get(r[11], 3), r[0]))
    # hygiene on sheet-bound text
    blob = json.dumps(rows)
    leaks = [t for t in ("why_rubric_is_correct", "/private/tmp", "REDASH_KEY") if t in blob]
    if leaks:
        raise SystemExit(f"stage5b: REFUSING — leaks {leaks}")
    sc = cfg["pipeline"]["sheets"]
    t, gid = common.write_new_tab(sc["spreadsheet_id"], tab, HEADER, rows)
    common.format_tab(sc["spreadsheet_id"], gid, len(HEADER),
                      widths=[190,190,42,120,150,80,72,82,90,300,470,82,520,240,230], nrows=len(rows))
    dv = collections.Counter(r[8] for r in rows); cvc = collections.Counter(r[11] for r in rows)
    print(f"stage5b: wrote {t!r} (gid={gid}) — {len(rows)} tasks")
    print(f"  DRAWER: {dict(dv)}")
    print(f"  CDQ:    {dict(cvc)}")
    return t, gid


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("--run-dir", required=True); ap.add_argument("--tab")
    a = ap.parse_args()
    main(common.load_config(), a.run_dir, a.tab or "eval L10_opus (drawer+CDQ+linters)")
