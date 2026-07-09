"""src/backtest.py — measure the pipeline's RECALL against a gold finding set (the customer's
143 findings by default). This is the "catch everything" proof: it compares our run's findings
(report.json) to gold on the OVERLAP of tasks and reports what we caught vs missed.

  python -m src.backtest --run-dir runs/<id>                       # vs gold/customer_findings.json
  python -m src.backtest --run-dir runs/<id> --gold gold/other.json
  (also invoked automatically by run.py --backtest gold/customer_findings.json)

Two recall numbers:
  - task-level  : of overlapping gold-flagged tasks, how many did we flag at all (any finding)?
  - defect-type : of gold findings, how many did we match by (task_id, defect_type)?
Task-level is the fair headline (our DRAWER tokens are mapped from spec dimensions, so exact
defect-type match understates true agreement).
"""
from __future__ import annotations
import argparse, collections, json
from pathlib import Path
from src import common


def _ours(report):
    out = {}
    for t in report["tasks"]:
        dts = collections.Counter(f.get("defect_type") for f in t.get("findings", []))
        out[t["task_id"]] = {"defect_types": set(dts),
                             "verdict": t.get("verdict"),
                             "n_findings": sum(dts.values())}
    return out


def run(gold_path, report_path):
    gold = json.load(open(gold_path))
    gtasks = gold["tasks"]
    ours = _ours(json.load(open(report_path)))
    overlap = sorted(t for t in gtasks if t in ours)

    print(f"backtest vs {Path(gold_path).name}  (gold: {gold['n_tasks']} tasks / {gold['n_findings']} findings)")
    if not overlap:
        print("  no overlapping tasks in this run — run the pipeline on the gold task set to measure recall.")
        print(f"  (gold task_ids e.g. {list(gtasks)[:3]})")
        return {"overlap": 0}

    task_hit = sum(1 for t in overlap if ours[t]["n_findings"] > 0)
    gf = df = 0
    by_dt = collections.defaultdict(lambda: [0, 0])
    missed = []
    for t in overlap:
        our_dts = ours[t]["defect_types"]
        for f in gtasks[t]:
            dt = f.get("defect_type", "UNKNOWN")
            gf += 1
            by_dt[dt][1] += 1
            if dt in our_dts:
                df += 1
                by_dt[dt][0] += 1
            else:
                missed.append(f"{t[:10]}:{dt}({f.get('tier','')[:6]})")

    # set-level precision / recall / F1 on defect_types per task (dedup our verbose findings to a
    # set first). Extras (types we raised, gold didn't) are NOT necessarily false positives — we may
    # catch real issues the customer's spot-check missed — so they're reported separately, not as errors.
    tp = ourtot = goldtot = 0
    extras = []
    for t in overlap:
        g = {f.get("defect_type") for f in gtasks[t]}
        o = ours[t]["defect_types"]
        tp += len(o & g); ourtot += len(o); goldtot += len(g)
        extras += [f"{t[:10]}:{dt}" for dt in sorted(o - g)]
    prec = tp / ourtot if ourtot else 0.0
    rec = tp / goldtot if goldtot else 0.0
    f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) else 0.0

    print(f"  overlap tasks: {len(overlap)} / {gold['n_tasks']}")
    print(f"  TASK-level recall : {task_hit}/{len(overlap)} flagged ({task_hit/len(overlap):.0%})")
    print(f"  DEFECT-type recall (per gold finding): {df}/{gf} ({(df/gf if gf else 0):.0%})")
    print(f"  DEFECT-type set  : precision={prec:.0%} recall={rec:.0%} F1={f1:.0%}  (TP={tp}, ours={ourtot}, gold={goldtot})")
    for dt, (c, n) in sorted(by_dt.items(), key=lambda x: -x[1][1]):
        print(f"     {dt}: {c}/{n} ({(c/n if n else 0):.0%})")
    if missed:
        print(f"  MISSED gold findings ({len(missed)}): {missed[:15]}{'…' if len(missed) > 15 else ''}")
    if extras:
        print(f"  EXTRA types we raised (not in gold; may be real or noise): {extras[:15]}{'…' if len(extras) > 15 else ''}")
    return {"overlap": len(overlap), "task_recall": task_hit / len(overlap),
            "defect_recall": (df / gf if gf else 0), "precision": prec, "f1": f1,
            "by_defect": {k: v for k, v in by_dt.items()}, "missed": missed, "extras": extras}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--gold", default=str(common.PKG / "gold" / "customer_findings.json"))
    a = ap.parse_args()
    run(a.gold, str(Path(a.run_dir) / "report.json"))
