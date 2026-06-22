#!/usr/bin/env python3
"""Assemble the contributor-facing feedback.json for ONE audit run — NO REUSE.

Every row is built from THIS run's own reconciled/ + prose/ + platform_eval/.
We NEVER carry a verdict, prose, or finding over from a prior run's feedback
record: each run re-audits the WHOLE pending queue from scratch (that is the
project rule — a stale verdict is worse than no verdict, and rubrics/specs are
revised continuously). Prior committed records under "OpenClaw QC/Audit-runs/"
are historical reference ONLY and are never read here.

Inputs in <workspace>/:
  reconciled/<tid>.json    — final verdict + bands + findings (master output)
  prose/<tid>.json         — {scenario, did, why, fix} contributor text
  validated/<tid>.json     — grounded findings (for the unverifiable count -> confidence)
  platform_eval/<tid>.json — live platform score + drawer 2nd opinion + viewer_url
  plan.json (optional)     — {"incomplete": [tids]} cds-pending tasks to list as Pending

Usage: python3 assemble.py --workspace <ws>            # writes <ws>/feedback.json
"""
import argparse, json, glob, os, sys


def J(p):
    return json.load(open(p))


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
    return v


def drawer_v(pe):
    ea = pe.get("embedded_audit") or {}
    v = ea.get("embedded_verdict") or pe.get("embedded_verdict")
    if isinstance(v, dict):
        v = v.get("verdict") or v.get("label")
    if not v:
        return ""
    s = str(v).lower()
    return "Fail" if ("fail" in s and "non" not in s) else "Non-Fail"


def live(ws, t):
    p = f"{ws}/platform_eval/{t}.json"
    if not os.path.exists(p):
        return {}
    pe = J(p)
    o = {}
    if (pe.get("score") or {}).get("pct") is not None:
        o["platform"] = f"{pe['score']['pct']}%"
    o["viewer"] = drawer_v(pe)
    if pe.get("viewer_url"):
        o["link"] = pe["viewer_url"]
    return o


def agree(mine, drawer):
    if not drawer:
        return "No second opinion recorded for this one."
    mf, df = mine == "FAIL", drawer == "Fail"
    if mf and df:
        return "Yes — both flag it as failing."
    if not mf and not df:
        return "Yes — both agree it holds up."
    if mf:
        return "No — I'm stricter here; the second opinion lets it pass."
    return "No — the second opinion flags it, but on a closer look the concern doesn't hold up."


def nunver(ws, t):
    try:
        return len(J(f"{ws}/validated/{t}.json").get("unverifiable") or [])
    except Exception:
        return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--skill", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    a = ap.parse_args()
    ws = a.workspace.rstrip("/")
    sys.path.insert(0, os.path.join(a.skill, "scripts"))
    from confidence import confidence_for

    plan = J(f"{ws}/plan.json") if os.path.exists(f"{ws}/plan.json") else {}
    incomplete = list(plan.get("incomplete") or [])

    rows, miss = [], []
    # one row per reconciled task — THIS RUN ONLY, never a prior record
    for rp in sorted(glob.glob(f"{ws}/reconciled/*.json")):
        t = os.path.basename(rp)[:-5]
        pp = f"{ws}/prose/{t}.json"
        if not os.path.exists(pp):
            miss.append(t[-4:])
            continue
        rec, pr = J(rp), J(pp)
        mine = norm(rec["verdict"])
        row = {"task": t, **{k: pr.get(k, "") for k in ("scenario", "did", "why", "fix")}, "verdict": mine}
        row["confidence"] = confidence_for(rec, nunver(ws, t))
        row.update(live(ws, t))
        for k in ("platform", "viewer", "link"):
            row.setdefault(k, "")
        row["agree"] = agree(mine, row.get("viewer", ""))
        rows.append(row)

    # pending = cds-unmaterialised tasks (no reconciled produced this run)
    done = {r["task"] for r in rows}
    for t in incomplete:
        if t in done:
            continue
        row = {"task": t, "scenario": "(run not captured yet)", "did": "—", "verdict": "Pending", "confidence": "",
               "why": "A new version of this task is in flight and its run hasn't been captured yet, so the checks "
                      "can't be reviewed this round.",
               "fix": "Queued for a re-check once the run lands.", "agree": "Pending — nothing to compare yet."}
        row.update(live(ws, t))
        for k in ("platform", "viewer", "link"):
            row.setdefault(k, "")
        rows.append(row)

    json.dump(rows, open(f"{ws}/feedback.json", "w"), indent=1, ensure_ascii=False)
    from collections import Counter
    print("rows:", len(rows), "| verdicts:", dict(Counter(r["verdict"] for r in rows)), "| missing prose:", miss)


if __name__ == "__main__":
    main()
