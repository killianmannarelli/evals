#!/usr/bin/env python3

"""Render a markdown version of the static eval-design QA report.

Optional batch-summary companion to the decision CSV (`render_report_csv.py`). Both
render from the SAME structured payload (`report_data.json`) so they never drift:
write `report_data.json` once, then run either renderer against it.

This is a STATIC QA (loader-A only) — there are no reward / pass@K / rollout
columns; tasks are ranked purely by their flagged-rubric counts.

Stdlib only — run it directly:

    python3 render_report_md.py --data report_data.json --output report.md

`report_data.json` schema (all keys optional unless noted; the renderer
tolerates missing optional fields):

    {
      "title": "Eval data-quality QA report",         # required
      "subtitle": "30 tasks · static review · generated 2026_06_02",
      "methodology": "One paragraph … ends with the mandatory FP caveat.",
      # Two tier-split recurring-theme sections (concise category descriptions + count pointers).
      "action_required_summary":   ["**Category** — one-sentence what-it-is <em>(N findings · M tasks)</em>", ...],
      "review_recommended_summary": ["**Category** — one-sentence what-it-is <em>(N findings · M tasks)</em>", ...],
      # (legacy: a single flat "recurring_issues" list is still rendered if present.)
      "tasks": [
        {
          "task_name": "course-proposal-slides",     # required
          "task_id": "abc123…",                       # optional (drop for the shared report)
          "has_tests": true,                           # optional "+ tests" chip
          "flagged_rubrics": {"action_required": 1, "review_recommended": 6},  # unique rubric ids by tier
          # --- decision fields consumed by render_report_csv.py (the PRIMARY output) ---
          "verdict": "fail",                           # pass | non-fail | fail (else derived from findings)
          "confidence": 25,                            # 0..100 = how confident the task is deliverable/clean
          "summary": "ORACLE_LEAK: answer key sits in an agent-readable file",  # one-line headline (else derived)
          "flagged_dimensions": ["environment_adequacy"],  # eval-guide dimensions implicated (else derived)
          "audit_md": "- **[ACTION] …**",             # per-task markdown audit (else derived from findings)
          "carryover": {"attempt_id": "…", "review_level": "11"},  # echoed passthrough, ignored by eval
          # NOTE: per-task static "quality" dimension scores are dropped for the shared report.
          "findings": [
            {
              "tier": "action_required", "defect_type": "CONTAINER_ENV",
              "rubric_ids": [3], "test_names": ["test_appendix_word_count"],
              "explanation": "…", "fix": "…"
            }
          ]
        }
      ]
    }
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

# Two tiers, most urgent first, with their human-readable labels.
_TIERS = [
    ("action_required", "action required"),
    ("review_recommended", "review recommended"),
]


def _html_to_md(text: str) -> str:
    """Convert the light inline HTML used in the payload to markdown."""
    if not text:
        return ""
    text = re.sub(r"<code>(.*?)</code>", r"`\1`", text, flags=re.S)
    text = re.sub(r"<(?:strong|b)>(.*?)</(?:strong|b)>", r"**\1**", text, flags=re.S)
    text = re.sub(r"<(?:em|i)>(.*?)</(?:em|i)>", r"*\1*", text, flags=re.S)
    text = re.sub(r"<[^>]+>", "", text)  # strip any remaining tags
    return text.strip()


def _fmt_flagged(flagged: dict[str, Any] | None) -> str:
    """Render flagged-rubric counts like `1 action required · 6 review recommended`."""
    if not flagged:
        return "—"
    parts = [
        f"{int(flagged[key])} {label}" for key, label in _TIERS if flagged.get(key)
    ]
    return " · ".join(parts) if parts else "—"


def _sort_key(task: dict[str, Any]) -> tuple[int, int, str]:
    """Most urgent tasks first: by flagged action-required then review-recommended desc,
    then task name."""
    flagged = task.get("flagged_rubrics") or {}
    return (
        -int(flagged.get("action_required", 0)),
        -int(flagged.get("review_recommended", 0)),
        str(task.get("task_name", "")),
    )


def _header_lines(data: dict[str, Any]) -> list[str]:
    """Title, subtitle, methodology, and the two tier-split issue-summary sections."""
    lines = [f"# {data.get('title', 'Eval data-quality QA report')}"]
    if data.get("subtitle"):
        lines += ["", f"*{data['subtitle']}*"]

    # Two concise, tier-split issue-summary sections (action required / review recommended).
    # Each item may be a plain string, or a dict {"text", "example_task"} where the example task
    # is rendered as an anchor link into that task's per-task findings section.
    def _summary_bullet(item):
        if isinstance(item, dict):
            text = _html_to_md(str(item.get("text", "")))
            ex = item.get("example_task")
            if ex:
                return f"- {text} — example: [`{ex}`](#{ex})"
            return f"- {text}"
        return f"- {_html_to_md(str(item))}"

    for key, heading in (
        ("action_required_summary", "## Action required"),
        ("review_recommended_summary", "## Review recommended"),
    ):
        items = data.get(key) or []
        if items:
            lines += ["", heading, ""]
            lines += [_summary_bullet(i) for i in items]
    # Back-compat: a single flat `recurring_issues` list is still rendered if present.
    legacy = data.get("recurring_issues") or []
    if legacy:
        lines += ["", "## Key recurring issues", ""]
        lines += [f"- {_html_to_md(str(issue))}" for issue in legacy]
    if data.get("methodology"):
        lines += ["", "## Methodology", "", _html_to_md(data["methodology"])]
    return lines


def _summary_lines(tasks: list[dict[str, Any]]) -> list[str]:
    """The per-task summary markdown table (worst-first)."""
    header = ["Task", "Flagged rubrics", "Defects"]
    lines = ["", "## Summary", ""]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("|" + "|".join(["---"] * len(header)) + "|")
    for task in tasks:
        name = str(task.get("task_name", "?"))
        if task.get("has_tests"):
            name += " `+tests`"
        if task.get("task_id"):
            name += f"<br>`{task['task_id']}`"
        row = [
            name,
            _fmt_flagged(task.get("flagged_rubrics")),
            str(len(task.get("findings") or [])),
        ]
        lines.append("| " + " | ".join(row) + " |")
    return lines


def _finding_line(f: dict[str, Any]) -> list[str]:
    """One finding rendered as a bullet (+ optional fix sub-bullet)."""
    ids = []
    if f.get("rubric_ids"):
        ids.append("R" + ", R".join(str(r) for r in f["rubric_ids"]))
    if f.get("test_names"):
        ids.append(", ".join(str(t) for t in f["test_names"]))
    id_str = f" ({'; '.join(ids)})" if ids else ""
    tier = f.get("tier", "review_recommended")
    label = {"action_required": "ACTION REQUIRED", "review_recommended": "REVIEW"}.get(
        tier, tier.upper()
    )
    dtype = f.get("defect_type", "UNKNOWN")
    out = [
        f"- **[{label}] {dtype}**{id_str}: {_html_to_md(str(f.get('explanation', '')))}"
    ]
    if f.get("fix"):
        out.append(f"  - *Fix:* {_html_to_md(str(f['fix']))}")
    return out


def _defects_lines(tasks: list[dict[str, Any]]) -> list[str]:
    """Findings grouped by task (anchored by task_name for the summary links)."""
    lines = ["", "## Findings by task", ""]
    any_defect = False
    for task in tasks:
        findings = task.get("findings") or []
        if not findings:
            continue
        any_defect = True
        heading = str(task.get("task_name", "?"))
        if task.get("task_id"):
            heading += f" (`{task['task_id']}`)"
        lines += [f"### {heading}", ""]
        ranked = sorted(
            findings, key=lambda f: 0 if f.get("tier") == "action_required" else 1
        )
        for f in ranked:
            lines += _finding_line(f)
        lines.append("")
    if not any_defect:
        lines.append("_No defects found._")
    return lines


def render_markdown(data: dict[str, Any]) -> str:
    """Render the full report markdown from a `report_data.json` payload."""
    tasks = sorted(data.get("tasks", []), key=_sort_key)
    lines = _header_lines(data)
    lines += _summary_lines(tasks)
    lines += _defects_lines(tasks)
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--data", required=True, help="Path to report_data.json")
    ap.add_argument("--output", required=True, help="Path to write the .md report")
    args = ap.parse_args(argv)

    data = json.loads(Path(args.data).read_text(encoding="utf-8"))
    Path(args.output).write_text(render_markdown(data), encoding="utf-8")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
