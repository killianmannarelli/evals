#!/usr/bin/env python3
"""
fetch_spec.py — Pull the latest *approved* audit rubric for a Scale AI project
straight from Redash (query SPEC_GETTER, id 304995) and render it as the
canonical spec.md the auditor sub-agents read.

Usage:
    python fetch_spec.py --project <id> --api-key $REDASH_KEY --out <path>

Why this exists:
- Manually exporting a spec from the rubric editor and feeding it as CSV/PDF is
  a friction step that loses information (formatting, ordering, the Pass / Fail
  / Score band each option carries).
- The audit rubric is already structured in Snowflake; query 304995 emits one
  row per (dimension × answer option). This script re-groups by dimension so
  the canonical spec.md reads dimension-by-dimension with all options listed
  inline — the same shape the auditor prompt was designed for.
- Whenever the user hands us a static doc instead, the orchestrator falls back
  to parse_spec.py. The Redash path is the default for projects that have an
  approved rubric in the auditrubrics table.

Query: https://redash.scale.com/queries/304995 — parameter `project_id`.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import OrderedDict
from pathlib import Path

import requests

try:
    from events import emit
except ImportError:
    # Allow running from the scripts/ directory directly without PYTHONPATH magic.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from events import emit  # type: ignore  # noqa: E402

REDASH_BASE = "https://redash.scale.com"
DEFAULT_QUERY_ID = 304995  # SPEC_GETTER


def run_query(api_key: str, query_id: int, params: dict) -> dict:
    """Run a saved Redash query with parameters and return the query_result blob."""
    headers = {"Authorization": f"Key {api_key}"}
    r = requests.post(
        f"{REDASH_BASE}/api/queries/{query_id}/results",
        headers=headers,
        json={"parameters": params, "max_age": 0},
        timeout=60,
    )
    r.raise_for_status()
    p = r.json()
    if "query_result" in p:
        return p["query_result"]
    job_id = (p.get("job") or {}).get("id")
    if not job_id:
        raise RuntimeError(f"Unexpected Redash response: {p}")
    deadline = time.time() + 60 * 30
    while time.time() < deadline:
        time.sleep(2)
        rj = requests.get(f"{REDASH_BASE}/api/jobs/{job_id}", headers=headers, timeout=30)
        rj.raise_for_status()
        j = rj.json().get("job", {})
        s = j.get("status")
        if s == 3:
            qr_id = j.get("query_result_id")
            r2 = requests.get(
                f"{REDASH_BASE}/api/query_results/{qr_id}",
                headers=headers,
                timeout=60,
            )
            r2.raise_for_status()
            return r2.json()["query_result"]
        if s in (4, 5):
            raise RuntimeError(f"Redash job failed/canceled: {j.get('error', '<no error>')}")
    raise TimeoutError("Redash SPEC_GETTER did not complete within 30 minutes")


def _get(row: dict, *keys: str) -> str:
    """Tolerate column-name casing differences from Snowflake/Redash."""
    for k in keys:
        for variant in (k, k.upper(), k.lower()):
            if variant in row and row[variant] is not None:
                return row[variant]
    return ""


def render_markdown(rows: list[dict]) -> str:
    """Group rows by dimension and emit one section per dimension, with all
    options listed inline under it. This matches the structure the auditor
    prompt expects (dimension → options with Pass/Non-Fail/Fail score bands)."""
    if not rows:
        return ""

    grouped: OrderedDict[str, list[dict]] = OrderedDict()
    for row in rows:
        title = str(_get(row, "DIMENSION_TITLE") or "<unknown dimension>").strip()
        grouped.setdefault(title, []).append(row)

    rubric_name = str(_get(rows[0], "RUBRIC_NAME")).strip()

    out: list[str] = []
    if rubric_name:
        out.append(f"# {rubric_name}")
        out.append("")

    for title, opts in grouped.items():
        out.append(f"## {title}")
        first = opts[0]
        bucket = str(_get(first, "BUCKET")).strip()
        question = str(_get(first, "QUESTION_TEXT")).strip()
        description = str(_get(first, "QUESTION_DESCRIPTION")).strip()
        categories = str(_get(first, "ERROR_CATEGORIES")).strip()

        if bucket:
            out.append(f"**Bucket:** {bucket}")
        if question:
            out.append(f"**Question:** {question}")
        if description:
            out.append(f"**Description:** {description}")
        if categories:
            out.append(f"**Error categories:** {categories}")
        out.append("")
        out.append("**Options:**")
        out.append("")
        # Sort options by score descending so Pass surfaces first, then
        # Non-Fail, then Fail. Stable on input order within the same score.
        def _score_key(item):
            idx, opt = item
            try:
                s = int(_get(opt, "OPTION_SCORE") or 0)
            except (TypeError, ValueError):
                s = 0
            return (-s, idx)
        for _, opt in sorted(enumerate(opts), key=_score_key):
            score = _get(opt, "OPTION_SCORE")
            verdict = str(_get(opt, "OPTION_VERDICT")).strip()
            text = str(_get(opt, "OPTION_TEXT")).strip()
            req = _get(opt, "OPTION_REQUIRES_JUSTIFICATION")
            req_str = " (justification required)" if req in (True, "true", "TRUE", 1, "1") else ""
            out.append(f"- **Score {score} — {verdict}**{req_str}")
            if text:
                for line in text.splitlines():
                    out.append(f"  {line}")
            out.append("")
        out.append("---")
        out.append("")
    while out and out[-1] in ("", "---"):
        out.pop()
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--project", required=True, help="Project ID (24-char ObjectId) — passed to SPEC_GETTER as project_id")
    parser.add_argument(
        "--api-key",
        default=os.environ.get("REDASH_KEY") or os.environ.get("REDASH_API_KEY"),
        help="Redash API key (or REDASH_KEY env var; REDASH_API_KEY accepted as fallback)",
    )
    parser.add_argument("--out", required=True, help="Output path for the canonical spec.md")
    parser.add_argument("--query-id", type=int, default=DEFAULT_QUERY_ID, help=f"Redash query ID (default: {DEFAULT_QUERY_ID} = SPEC_GETTER)")
    args = parser.parse_args()

    if not args.api_key:
        print("error: --api-key not provided and REDASH_KEY is unset", file=sys.stderr)
        return 2

    print("QC Auditor — created by Marius Delahay.", file=sys.stderr)
    print(f"Running SPEC_GETTER (query {args.query_id}) for project={args.project}...", file=sys.stderr)
    emit("spec_fetch_started", project=args.project, query_id=args.query_id)
    res = run_query(args.api_key, args.query_id, {"project_id": args.project})
    rows = res.get("data", {}).get("rows", [])
    if not rows:
        print(
            f"error: SPEC_GETTER returned 0 rows for project {args.project}. Either the project has no approved rubric in public.auditrubrics, or the project ID is wrong.",
            file=sys.stderr,
        )
        emit("spec_fetch_failed", project=args.project, reason="zero_rows")
        return 3
    print(f"Got {len(rows)} option rows across the rubric", file=sys.stderr)

    md = render_markdown(rows)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    header = f"<!-- pulled from Redash query {args.query_id} (SPEC_GETTER) for project {args.project} -->\n\n"
    out_path.write_text(header + md)
    print(f"Wrote {out_path} ({len(md)} chars, {len(md.splitlines())} lines)", file=sys.stderr)
    # Count distinct dimensions so the UI can show a quick "rubric sanity" tile.
    dim_count = sum(1 for line in md.splitlines() if line.startswith("## "))
    emit("spec_fetched", project=args.project, query_id=args.query_id, option_rows=len(rows), dimensions=dim_count, path=str(out_path))

    # Same sanity checks parse_spec.py uses, so a malformed rubric stops the
    # run before 50 auditors burn tokens on a useless spec.
    nonempty = [l for l in md.splitlines() if l.strip()]
    if len(nonempty) < 10:
        print(f"warning: spec output is suspiciously short ({len(nonempty)} non-empty lines)", file=sys.stderr)
        return 3
    if not any(m in md for m in ("Pass", "Fail", "Score")):
        print("warning: spec output contains none of the expected markers (Pass/Fail/Score)", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
