"""stage4_assemble — merge all findings (linters + any LLM results), dedupe, roll up a
per-task verdict, reward-prioritize, and run the leakage hygiene scan.

Reads <run_dir>/findings_linters.json and (optional) findings_llm.json, plus digest.json for
reward. Writes <run_dir>/report.json = {generated, tasks:[per-task row], totals}.
"""
from __future__ import annotations
import json
from pathlib import Path
from src import common

LEAK_TERMS = ["/private/tmp", "claude-502", "/Users/killian", "REDASH_KEY", "serene-column",
              "deltaeval", "why_rubric_is_correct"]

# Answer-key field names to redact from sheet-bound text (they name where the gold answer lives).
# The graders reference these fields in their reasoning/fixes; neutralize the field name so no
# answer-key handle reaches the shared sheet, while keeping the finding readable.
REDACT = {"why_rubric_is_correct": "the rubric-justification field",
          "why_rubric_is_incorrect": "the rubric-justification field"}


def _redact(s):
    s = str(s or "")
    for k, v in REDACT.items():
        s = s.replace(k, v)
    return s


def _verdict(findings, rule):
    tiers = {f.get("tier") for f in findings}
    if rule["fail_if_any"] in tiers:
        return "fail"
    if rule["nonfail_if_any"] in tiers:
        return "non-fail"
    return "pass"


def _dedupe(findings):
    seen, out = set(), []
    for f in findings:
        key = (f.get("defect_type"), tuple(sorted(f.get("rubric_ids") or [])),
               tuple(sorted(f.get("test_names") or [])), (f.get("explanation") or "")[:60])
        if key in seen:
            continue
        seen.add(key); out.append(f)
    return out


def main(cfg, run_dir):
    run_dir = Path(run_dir)
    digest = json.load(open(run_dir / "digest.json"))
    lint = json.load(open(run_dir / "findings_linters.json")) if (run_dir / "findings_linters.json").exists() else {}
    llm = json.load(open(run_dir / "findings_llm.json")) if (run_dir / "findings_llm.json").exists() else {}
    rule = cfg["taxonomy"]["verdict_rule"]
    dim_of = cfg["taxonomy"]["dimension_of"]
    low = cfg["thresholds"]["reward"]["low_reward"]

    tasks = []
    for tid, d in digest.items():
        findings = _dedupe((lint.get(tid) or []) + (llm.get(tid) or []))
        for f in findings:                       # redact answer-key field names from sheet-bound text
            f["explanation"] = _redact(f.get("explanation"))
            f["fix"] = _redact(f.get("fix"))
        ar = [f for f in findings if f.get("tier") == "action_required"]
        rr = [f for f in findings if f.get("tier") == "review_recommended"]
        verdict = _verdict(findings, rule)
        reward = d.get("reward") or {}
        mr = reward.get("mean_reward")
        dims = sorted({dim_of.get(f.get("defect_type"), "other") for f in findings})
        flags = " | ".join(f"{f['defect_type']}[{f['tier'][:6]}]"
                            + (f" R{','.join(map(str,f['rubric_ids']))}" if f.get("rubric_ids") else "")
                            for f in findings)
        tasks.append({
            "task_id": tid, "attempt_id": d.get("attempt_id"), "layer": d.get("layer"),
            "category": d.get("category"), "subcategory": d.get("subcategory"),
            "mm_input": d.get("mm_input"), "mean_reward": mr, "weighted_score": reward.get("weighted_score"),
            "verdict": verdict, "n_action_required": len(ar), "n_review_recommended": len(rr),
            "defect_types": sorted({f["defect_type"] for f in findings}), "flagged_dimensions": dims,
            "flags": flags, "findings": findings,
            "summary": (ar or rr or [{"explanation": "No defects found."}])[0].get("explanation", "")[:200],
            "low_reward": (mr is not None and mr < low),
        })

    vrank = {"fail": 0, "non-fail": 1, "pass": 2}
    tasks.sort(key=lambda r: (vrank.get(r["verdict"], 3),
                              0 if r["low_reward"] else 1,
                              r["mean_reward"] if r["mean_reward"] is not None else 1.0,
                              r["task_id"]))
    report = {"tasks": tasks, "totals": {
        "n_tasks": len(tasks),
        "fail": sum(1 for t in tasks if t["verdict"] == "fail"),
        "non_fail": sum(1 for t in tasks if t["verdict"] == "non-fail"),
        "pass": sum(1 for t in tasks if t["verdict"] == "pass"),
        "flagged": sum(1 for t in tasks if t["verdict"] != "pass"),
        "total_findings": sum(len(t["findings"]) for t in tasks),
        "low_reward_tasks": sum(1 for t in tasks if t["low_reward"]),
    }}
    json.dump(report, open(run_dir / "report.json", "w"), indent=1)

    # hygiene scan on the text that will hit the sheet
    blob = json.dumps([{k: t[k] for k in ("summary", "flags", "findings")} for t in tasks])
    leaks = {term: blob.count(term) for term in LEAK_TERMS if blob.count(term)}
    report["hygiene"] = {"leaks": leaks, "clean": not leaks}
    json.dump(report, open(run_dir / "report.json", "w"), indent=1)
    print(f"stage4: {report['totals']}")
    print(f"stage4: hygiene {'CLEAN' if not leaks else 'LEAKS ' + str(leaks)}")
    return report


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("--run-dir", required=True)
    main(common.load_config(), ap.parse_args().run_dir)
