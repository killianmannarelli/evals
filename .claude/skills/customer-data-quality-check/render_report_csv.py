#!/usr/bin/env python3
"""Render the PRIMARY decision output of the static QA: one CSV row per task.

This is the deliverable the team actually acts on — drop it into a Google Sheet, sort by
`confidence`, and decide what ships (`pass`, high confidence → deliver blindly), what to
quick-audit (`non-fail`, borderline), and what to fix (`fail`). The Markdown report
(`render_report_md.py`) is an optional batch-level companion for eyeballing detail.

Driven by the SAME `report_data.json` the Markdown renderer uses, so nothing drifts.

    python3 render_report_csv.py --data report_data.json --output tasks.csv [--inputs-dir <OUTPUT_DIR>]

Columns (per task), ordered for fast human validation:
  task_name
  <carryover…>            passthrough columns from the input CSV (attempt_id, review_level, …)
  verdict                 pass | non-fail | fail
  needs_validation        yes for fail AND non-fail (both need a human); no for pass
  confidence              0–100, how confident the task is deliverable (clean). Sort by this.
  summary                 one-line headline of the worst issue (or "No defects found")
  action_required         count of confirmed action-required findings
  review_recommended      count of confirmed review-recommended findings
  flagged_dimensions      eval-guide dimensions implicated (semicolon-separated)
  flags                   compact per-finding flags: DEFECT_TYPE [tier] R-ids/tests
  audit_md                markdown summary of the task's findings (full detail for validation)

Each report_data task record may provide `verdict`, `confidence`, `summary`, `flagged_dimensions`,
and `audit_md` explicitly (from the verifier); when absent they are derived from `findings` so the
CSV is always complete.
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import re
from pathlib import Path
from typing import Any

# Map each defect_type token to the eval-guide quality dimension it implicates.
_DEFECT_DIMENSION = {
    "SP_UNCLEAR": "prompt_clarity",
    "RUBRIC_AMBIGUOUS": "rubric_accuracy",
    "RUBRIC_UNFAIR": "rubric_accuracy",
    "RUBRIC_CONTRADICTION": "rubric_accuracy",
    "ORACLE_LEAK": "rubric_accuracy",
    "RUBRIC_OVERSPEC": "test_correctness",
    "GRADER_BROKEN": "test_correctness",
    "DATA_SPARSE": "input_adequacy",
    "MEDIA_PATH": "input_adequacy",
    "MULTIMODAL_ARTIFACT": "input_adequacy",
    "CONTAINER_ENV": "environment_adequacy",
    "SKILL_LOADOUT": "environment_adequacy",
}

# Fallback confidence (0..100 = clean/deliverable) when the verifier didn't set one.
_FALLBACK_CONFIDENCE = {"pass": 92, "non-fail": 60, "fail": 25}

_TIER_SHORT = {"action_required": "action", "review_recommended": "review"}


def _strip_md_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", str(text or ""))
    return text.strip()


def _counts(findings: list[dict[str, Any]]) -> tuple[int, int]:
    ar = sum(1 for f in findings if f.get("tier") == "action_required")
    rr = sum(1 for f in findings if f.get("tier") == "review_recommended")
    return ar, rr


def _verdict(task: dict[str, Any], ar: int, rr: int) -> str:
    if task.get("verdict"):
        return str(task["verdict"])
    if ar:
        return "fail"
    if rr:
        return "non-fail"
    return "pass"


def _confidence(task: dict[str, Any], verdict: str) -> int:
    if task.get("confidence") is not None:
        try:
            return int(round(float(task["confidence"])))
        except (TypeError, ValueError):
            pass
    return _FALLBACK_CONFIDENCE.get(verdict, 50)


def _flagged_dimensions(task: dict[str, Any], findings: list[dict[str, Any]]) -> str:
    if task.get("flagged_dimensions"):
        dims = task["flagged_dimensions"]
        return "; ".join(dims) if isinstance(dims, list) else str(dims)
    seen: list[str] = []
    for f in findings:
        dim = _DEFECT_DIMENSION.get(str(f.get("defect_type", "")), "other")
        if dim not in seen:
            seen.append(dim)
    return "; ".join(seen)


def _ids(f: dict[str, Any]) -> str:
    ids = []
    if f.get("rubric_ids"):
        ids.append("R" + ",R".join(str(r).lstrip("R") for r in f["rubric_ids"]))
    if f.get("test_names"):
        ids.append(",".join(str(t) for t in f["test_names"]))
    return " ".join(ids)


def _flags(findings: list[dict[str, Any]]) -> str:
    parts = []
    for f in findings:
        tier = _TIER_SHORT.get(f.get("tier", ""), f.get("tier", ""))
        ids = _ids(f)
        parts.append(f"{f.get('defect_type', 'UNKNOWN')} [{tier}]" + (f" {ids}" if ids else ""))
    return " | ".join(parts)


def _summary(task: dict[str, Any], findings: list[dict[str, Any]]) -> str:
    if task.get("summary"):
        return _strip_md_html(task["summary"])
    if not findings:
        return "No defects found."
    worst = sorted(findings, key=lambda f: 0 if f.get("tier") == "action_required" else 1)[0]
    expl = _strip_md_html(worst.get("explanation", ""))
    if len(expl) > 140:
        expl = expl[:137].rstrip() + "…"
    return f"{worst.get('defect_type', 'UNKNOWN')}: {expl}".strip().rstrip(":")


def _audit_md(task: dict[str, Any], findings: list[dict[str, Any]]) -> str:
    if task.get("audit_md"):
        return str(task["audit_md"])
    if not findings:
        return "No defects found."
    ranked = sorted(findings, key=lambda f: 0 if f.get("tier") == "action_required" else 1)
    lines = []
    for f in ranked:
        tier = _TIER_SHORT.get(f.get("tier", ""), f.get("tier", "")).upper()
        ids = _ids(f)
        head = f"- **[{tier}] {f.get('defect_type', 'UNKNOWN')}**"
        if ids:
            head += f" ({ids})"
        head += f": {_strip_md_html(f.get('explanation', ''))}"
        lines.append(head)
        if f.get("fix"):
            lines.append(f"  - Fix: {_strip_md_html(f['fix'])}")
    return "\n".join(lines)


def _verdict_rank(v: str) -> int:
    return {"fail": 0, "non-fail": 1, "pass": 2}.get(v, 3)


def build_rows(data: dict[str, Any], carryover_by_task: dict[str, dict[str, Any]]):
    tasks = data.get("tasks", [])
    # Union of carryover column names, preserving first-seen order.
    carry_cols: list[str] = []
    for t in tasks:
        merged = {**(carryover_by_task.get(t.get("task_name", ""), {})), **(t.get("carryover") or {})}
        for k in merged:
            if k not in carry_cols:
                carry_cols.append(k)

    rows = []
    for t in tasks:
        findings = t.get("findings") or []
        ar, rr = _counts(findings)
        verdict = _verdict(t, ar, rr)
        conf = _confidence(t, verdict)
        merged_carry = {**(carryover_by_task.get(t.get("task_name", ""), {})), **(t.get("carryover") or {})}
        row = {
            "task_name": t.get("task_name", ""),
            "verdict": verdict,
            "needs_validation": "no" if verdict == "pass" else "yes",
            "confidence": conf,
            "summary": _summary(t, findings),
            "action_required": ar,
            "review_recommended": rr,
            "flagged_dimensions": _flagged_dimensions(t, findings),
            "flags": _flags(findings),
            "audit_md": _audit_md(t, findings),
        }
        for c in carry_cols:
            row[c] = merged_carry.get(c, "")
        rows.append(row)

    # Worst first: fail → non-fail → pass, then lowest confidence first.
    rows.sort(key=lambda r: (_verdict_rank(r["verdict"]), r["confidence"], r["task_name"]))
    header = (["task_name"] + carry_cols +
              ["verdict", "needs_validation", "confidence", "summary",
               "action_required", "review_recommended",
               "flagged_dimensions", "flags", "audit_md"])
    return header, rows


def _load_carryover_from_inputs(inputs_dir: Path) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for b in sorted(glob.glob(str(inputs_dir / "batch_*.json"))):
        try:
            rec = json.load(open(b))[0]
        except (json.JSONDecodeError, IndexError, OSError):
            continue
        if rec.get("carryover"):
            out[rec.get("task_name", "")] = rec["carryover"]
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--data", required=True, help="Path to report_data.json")
    ap.add_argument("--output", required=True, help="Path to write the decision CSV")
    ap.add_argument("--inputs-dir", default=None,
                    help="Optional <OUTPUT_DIR> from prepare_inputs.py; merges carryover columns")
    args = ap.parse_args(argv)

    data = json.loads(Path(args.data).read_text(encoding="utf-8"))
    carryover = _load_carryover_from_inputs(Path(args.inputs_dir)) if args.inputs_dir else {}
    header, rows = build_rows(data, carryover)

    with open(args.output, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=header)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"Wrote {args.output} ({len(rows)} tasks, {len(header)} columns)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
