"""stage5_sheet — write ONE combined tab from report.json (never overwrites an existing tab).

Columns: identity + context, reward (mean_reward / weighted_score), verdict, finding counts,
defect types, per-finding flags, one-line summary, viewer link. Refuses to write if the
hygiene scan found leaks.
"""
from __future__ import annotations
import json
from pathlib import Path
from src import common

HEADER = ["Task ID", "Attempt ID", "Layer", "Category", "Subcategory", "Modality",
          "mean_reward", "weighted_score", "Verdict", "#action_required", "#review_recommended",
          "Defect types", "Flagged dims", "Flags (per finding)", "Summary (worst)", "Open the task"]


def main(cfg, run_dir, tab_name=None):
    run_dir = Path(run_dir)
    report = json.load(open(run_dir / "report.json"))
    if report.get("hygiene") and not report["hygiene"]["clean"]:
        raise SystemExit(f"stage5: REFUSING to write — hygiene leaks {report['hygiene']['leaks']}")
    sc = cfg["pipeline"]["sheets"]
    viewer = sc["viewer_base"]
    rows = []
    for t in report["tasks"]:
        rows.append([
            t["task_id"], t.get("attempt_id", ""), f"L{t.get('layer','')}", t.get("category", ""),
            t.get("subcategory", ""), t.get("mm_input", ""),
            "" if t.get("mean_reward") is None else round(t["mean_reward"], 3),
            "" if t.get("weighted_score") is None else round(t["weighted_score"], 3),
            t["verdict"], t["n_action_required"], t["n_review_recommended"],
            ", ".join(t.get("defect_types", [])), "; ".join(t.get("flagged_dimensions", [])),
            t.get("flags", ""), t.get("summary", ""), viewer + (t.get("attempt_id") or ""),
        ])
    tab_base = tab_name or f"{sc['tab_prefix']} {run_dir.name}"
    tab, gid = common.write_new_tab(sc["spreadsheet_id"], tab_base, HEADER, rows)
    print(f"stage5: wrote tab {tab!r} (gid={gid}) — {len(rows)} tasks")
    json.dump({"tab": tab, "gid": gid}, open(run_dir / "sheet.json", "w"))
    return tab, gid


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("--run-dir", required=True); ap.add_argument("--tab")
    a = ap.parse_args()
    main(common.load_config(), a.run_dir, a.tab)
