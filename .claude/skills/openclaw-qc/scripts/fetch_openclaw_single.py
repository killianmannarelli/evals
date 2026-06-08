#!/usr/bin/env python3
"""Fetch a single OpenClaw task (by task_id) with the inline-RESPONSE parser.

This is the single-task variant of the parent qc-auditor's fetch_tasks.py.
Use when the user provides an explicit task ID rather than running a layer-wide batch.

Usage:
    REDASH_KEY=... python3 fetch_openclaw_single.py \\
        --task-id 69fb9655277dce0e70070e38 \\
        --out /path/to/workspace/tasks/

    REDASH_KEY=... python3 fetch_openclaw_single.py \\
        --task-id 6a04c2de0b4f42487f8e5dfc,69fb9655277dce0e70070e35 \\
        --out /path/to/workspace/tasks/
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Optional

import requests

# Reuse the parent skill's inline-RESPONSE parser + html unescape helpers.
sys.path.insert(0, str(Path.home() / ".claude" / "skills" / "qc-auditor" / "scripts"))
from fetch_tasks import extract_inline_form_data, parse_response, html_unescape_deep  # noqa: E402

BASE = "https://redash.scale.com"
DATA_SOURCE_ID = 30
OPENCLAW_PROJECT = "69f95a0f0992772af7907a03"


def run_query(query: str, api_key: str) -> dict:
    headers = {"Authorization": f"Key {api_key}"}
    r = requests.post(
        f"{BASE}/api/query_results",
        headers=headers,
        json={"data_source_id": DATA_SOURCE_ID, "query": query, "max_age": 0},
        timeout=300,
    )
    r.raise_for_status()
    j = r.json()
    if "query_result" in j:
        return j["query_result"]["data"]
    jid = j["job"]["id"]
    for _ in range(150):
        time.sleep(2)
        jr = requests.get(f"{BASE}/api/jobs/{jid}", headers=headers, timeout=30).json()["job"]
        if jr["status"] == 3:
            return requests.get(
                f"{BASE}/api/query_results/{jr['query_result_id']}",
                headers=headers,
                timeout=300,
            ).json()["query_result"]["data"]
        if jr["status"] == 4:
            raise RuntimeError(jr.get("error"))
    raise TimeoutError("Snowflake job did not complete within 300s")


def fetch_via_cds_view(attempt_id: str, api_key: str) -> Optional[dict]:
    """Resolve a CDS-pointer attempt via SCALE_PROD.VIEW.CDS_CHAT_TASK_ATTEMPT_RESPONSES.

    The view returns the unwrapped CDS content as a Snowflake VARIANT in column
    `RESPSONSE` (note the production typo — it is NOT `RESPONSE`).

    Returns:
        - dict: the unwrapped OpenClaw-shaped object (`{before, after, turns, ...}`)
                — caller can hand this straight to `extract_inline_form_data`.
        - None: view returned no row, RESPSONSE was NULL, OR RESPSONSE was an
                array-shape variant (cross-project form-field definitions, not the
                expected OpenClaw object). Falls through to Rule 14 signed-URL.

    Schema confirmed 2026-05-24 against data source 30 (GenAI Ops Snowflake).
    Coverage caveat: 7-attempt spot-check showed ~14% NULL rate; one attempt
    returned an array-shape variant — both fall through cleanly via None.
    """
    query = f"""
    SELECT cds.RESPSONSE AS response_json
    FROM SCALE_PROD.VIEW.CDS_CHAT_TASK_ATTEMPT_RESPONSES cds
    WHERE cds.TASK_ATTEMPT_ID = '{attempt_id}'
    LIMIT 1
    """
    try:
        data = run_query(query, api_key)
        rows = data.get("rows", [])
        if not rows:
            return None
        raw = rows[0].get("RESPONSE_JSON")
        if raw is None:
            return None
        parsed = parse_response(raw)
        # Shape guard: reject array-shape variants (form-field definitions from
        # cross-project rows). Expect a dict with at least one of the known
        # OpenClaw top-level keys.
        if not isinstance(parsed, dict):
            return None
        if not any(k in parsed for k in ("before", "after", "turns")):
            return None
        return html_unescape_deep(parsed)
    except Exception as e:
        print(f"  CDS view fetch failed for attempt {attempt_id}: {e}", file=sys.stderr)
        return None


def fetch_task(task_id: str, api_key: str, out_dir: Path, attempt_id: Optional[str] = None) -> dict:
    if attempt_id:
        where_clause = f"ta._ID = '{attempt_id}'"
    else:
        where_clause = f"ta.task = '{task_id}'"
    query = f"""
    WITH latest AS (
      SELECT ta._ID AS attempt_id, ta.task, ta.RESPONSE, ta.ATTEMPTED_AT, ta.ATTEMPTED_BY,
             ta.REVIEW_LEVEL, ta.REVIEW_STATUS, ta.REVIEW_OUTCOME, ta.TASK_FEEDBACK,
             ROW_NUMBER() OVER (PARTITION BY ta.task ORDER BY ta.ATTEMPTED_AT DESC) AS rn
      FROM PUBLIC.TASKATTEMPTS ta
      WHERE {where_clause}
    )
    SELECT l.attempt_id, l.task, l.RESPONSE, l.ATTEMPTED_AT, l.ATTEMPTED_BY,
           l.REVIEW_LEVEL, l.REVIEW_STATUS, l.REVIEW_OUTCOME, l.TASK_FEEDBACK,
           t.metadata AS task_metadata, t.project, t.status AS task_status,
           u.email AS attempter_email
    FROM latest l
    LEFT JOIN PUBLIC.TASKS t ON t._ID = l.task
    LEFT JOIN PUBLIC.USERS u ON u._ID = l.ATTEMPTED_BY
    WHERE l.rn = 1
    """
    data = run_query(query, api_key)
    rows = data.get("rows", [])
    if not rows:
        raise ValueError(f"No attempts found for task {task_id} (attempt_id={attempt_id})")

    row = rows[0]
    if row.get("PROJECT") != OPENCLAW_PROJECT:
        print(
            f"WARNING: task {task_id} project = {row.get('PROJECT')}, "
            f"expected {OPENCLAW_PROJECT}. Continuing anyway.",
            file=sys.stderr,
        )

    response = html_unescape_deep(parse_response(row["RESPONSE"]))
    task_metadata = html_unescape_deep(parse_response(row["TASK_METADATA"]))
    inline = extract_inline_form_data(response)

    # Rule 14a (2026-05-24): when shape is cds_pointer/unknown, try
    # SCALE_PROD.VIEW.CDS_CHAT_TASK_ATTEMPT_RESPONSES FIRST. The view resolves
    # CDS pointers in-Snowflake and avoids the signed-URL round-trip entirely.
    # Falls through to Rule 14 signed-URL fetch when the view returns NULL or
    # a shape-variant (array of form-field definitions instead of OpenClaw obj).
    if inline.get("shape") in ("cds_pointer", "unknown"):
        view_attempt_id = row.get("ATTEMPT_ID")
        if view_attempt_id:
            view_unwrapped = fetch_via_cds_view(view_attempt_id, api_key)
            if view_unwrapped is not None:
                response = view_unwrapped
                inline = extract_inline_form_data(response)
                print(
                    f"  Rule 14a: fetched via CDS view "
                    f"(shape={inline.get('shape')}) for {task_id}",
                    file=sys.stderr,
                )

    # Rule 14 (2026-05-23): if the response is a CDS pointer wrapper and a
    # signed URL is present (response.url), try fetching it directly before
    # giving up. The signature itself authenticates — anyone holding the URL
    # can read the JSON until Expires. Many such URLs live for 30+ days.
    if (
        inline.get("shape") in ("cds_pointer", "unknown")
        and isinstance(response, dict)
        and isinstance(response.get("url"), str)
        and response["url"].startswith("https://")
    ):
        try:
            import urllib.request
            req = urllib.request.Request(
                response["url"],
                headers={"User-Agent": "qc-auditor-openclaw/1.0"},
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                if resp.status == 200:
                    raw = resp.read()
                    if len(raw) > 1024:
                        unwrapped = html_unescape_deep(json.loads(raw))
                        # Replace the response wrapper with the unwrapped form
                        response = unwrapped
                        inline = extract_inline_form_data(response)
                        print(
                            f"  Rule 14: fetched signed-URL inline RESPONSE "
                            f"({len(raw)} bytes) for {task_id}",
                            file=sys.stderr,
                        )
        except Exception as e:
            print(f"  Rule 14: signed-URL fetch failed for {task_id}: {e}", file=sys.stderr)

    record = {
        "task_id": task_id,
        "attempt_id": row.get("ATTEMPT_ID"),
        "project": row.get("PROJECT"),
        "layer": f"L{row.get('REVIEW_LEVEL')}" if row.get("REVIEW_LEVEL") is not None else None,
        "review_level": row.get("REVIEW_LEVEL"),
        "review_status": row.get("REVIEW_STATUS"),
        "review_outcome": row.get("REVIEW_OUTCOME"),
        "task_status": row.get("TASK_STATUS"),
        "attempted_by": row.get("ATTEMPTED_BY"),
        "attempter_email": row.get("ATTEMPTER_EMAIL"),
        "attempted_at": str(row.get("ATTEMPTED_AT")),
        "response": response,
        "response_shape": inline.get("shape"),
        "inline_form_data": inline if inline.get("shape") == "inline" else None,
        "task_metadata": task_metadata,
        "task_feedback": parse_response(row.get("TASK_FEEDBACK")),
    }

    out_path = out_dir / f"{task_id}.json"
    out_path.write_text(json.dumps(record, indent=2, default=str))
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-id", required=True, help="Single task ID or comma-separated list")
    parser.add_argument(
        "--attempt-id",
        help="Optional: pin to a specific attempt ID (use for retrospective audits of pre-CDS-migration inline attempts). Only valid with a single --task-id.",
    )
    parser.add_argument("--out", required=True, help="Output directory for per-task JSON files")
    parser.add_argument(
        "--api-key",
        default=os.environ.get("REDASH_KEY"),
        help="Redash API key (or REDASH_KEY env var)",
    )
    args = parser.parse_args()

    if not args.api_key:
        print("error: --api-key not provided and REDASH_KEY is unset", file=sys.stderr)
        return 2

    print("QC Auditor (OpenClaw) — created by Killian Mannarelli.", file=sys.stderr)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    ids = [tid.strip() for tid in args.task_id.split(",") if tid.strip()]
    if args.attempt_id and len(ids) != 1:
        print("error: --attempt-id requires exactly one --task-id", file=sys.stderr)
        return 2
    print(f"Fetching {len(ids)} task(s) ...", file=sys.stderr)

    inline_count = 0
    cds_count = 0
    for tid in ids:
        try:
            record = fetch_task(tid, args.api_key, out_dir, attempt_id=args.attempt_id)
            shape = record.get("response_shape")
            if shape == "inline":
                inline_count += 1
            elif shape == "cds_pointer":
                cds_count += 1
            print(
                f"  {tid} -> {out_dir}/{tid}.json "
                f"(shape={shape}, layer={record.get('layer')}, "
                f"review_status={record.get('review_status')})",
                file=sys.stderr,
            )
        except Exception as exc:
            print(f"  {tid} -> ERROR: {exc}", file=sys.stderr)

    print(
        f"\nDone. inline={inline_count}, cds_pointer={cds_count}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
