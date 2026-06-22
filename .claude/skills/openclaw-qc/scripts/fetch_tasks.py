#!/usr/bin/env python3
"""
fetch_tasks.py — Pull the latest attempt for every task at a given pipeline
layer of a Scale AI project, via Redash, and write one JSON file per task.

Usage:
    python fetch_tasks.py \\
        --project aaaaaaaaaaaaaaaaaaaaaaaa \\
        --layer L0 \\
        --api-key $REDASH_KEY \\
        --out qc-auditor-workspace/<run>/tasks/

Layers: L-1, L0, L1, L10, L12.

The script creates an ad-hoc Redash query against the Snowflake data source,
polls until execution completes, downloads the result JSON, and writes one
task file per row. The query is the standard latest-attempt pattern:

    WITH latest AS (
        SELECT
            ta.task,
            ta.response,
            ta.attempted_by,
            ta.attempted_at,
            hn.review_level,
            ROW_NUMBER() OVER (PARTITION BY ta.task ORDER BY ta.attempted_at DESC) rn
        FROM PUBLIC.TASKATTEMPTS ta
        JOIN PUBLIC.PIPELINEV3HUMANNODES hn ON hn.task = ta.task
        WHERE ta.project = :project
          AND hn.review_level = :review_level
          AND ta.attempted_by != :exclude_attempter
    )
    SELECT task, response, attempted_by, attempted_at
    FROM latest WHERE rn = 1

The attempter to exclude (typically the Scale bot user) is read from the
EXCLUDE_ATTEMPTER_ID env var, falling back to the well-known Scale bot ID
if unset. The Redash API key is read from REDASH_KEY (or --api-key).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests

try:
    from events import emit
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from events import emit  # type: ignore  # noqa: E402

REDASH_BASE = "https://redash.scale.com"
# Default to the GenAI Ops Snowflake data source, which is what every project
# managed out of the GenAI Ops org sits on (Thoth, RLHF, safety, etc.).
# Override with --data-source-id if you're auditing a project on a different
# org's warehouse. Run `GET /api/data_sources` against your Redash instance
# to list IDs; common ones at scale.com are 22 (GenAI Ops FTEs), 29 (GenAI
# Eng), 30 (GenAI Ops), 47 (GenAI Ops Leads).
SNOWFLAKE_DATA_SOURCE_ID_DEFAULT = 30
# The attempter to exclude from the latest-attempt selection. Defaults to the
# well-known Scale bot user (`583cf35b…`), since automated transitions can
# otherwise be picked up as if they were human attempts. Override with the
# EXCLUDE_ATTEMPTER_ID env var (or by editing the default below) when auditing
# a project on a non-standard pipeline.
SCALE_BOT_USER_ID_FALLBACK = "583cf35b8b8b73054d4344e6"
EXCLUDE_ATTEMPTER_ID = os.environ.get("EXCLUDE_ATTEMPTER_ID", SCALE_BOT_USER_ID_FALLBACK)

# review_level is stored as a STRING in PIPELINEV3HUMANNODES (verified
# 2026-04-30 against the live schema), so all comparisons must quote the value.
LAYER_TO_REVIEW_LEVEL = {
    "L-1": "-1",
    "L0": "0",
    "L1": "1",
    "L10": "10",
    "L11": "11",
    "L12": "12",
}

# "Active" tasks are the ones currently sitting at the layer waiting for a
# reviewer. completed / canceled / paused tasks share the same review_level
# row but aren't pending action, so we filter to status='pending' by default.
DEFAULT_STATUS = "pending"


def build_query(project_id: str, review_level: str, status: str) -> str:
    # The LEFT JOIN to PUBLIC.TASKS pulls the task's `metadata` blob, which is
    # the universal home for prompt text, instruction URLs, and external
    # artefact pointers across every Scale project. Auditors that grade against
    # "the prompt" or "ground truth" need this — without it they're grading
    # GOLD/rubric content against itself.
    # The LEFT JOIN to PUBLIC.USERS resolves the attempter's email so it can
    # be surfaced as a CSV column without a follow-up lookup. We keep it as a
    # LEFT JOIN (not INNER) so a missing user row never silently drops a task.
    return f"""
WITH latest AS (
    SELECT
        ta.task,
        ta.response,
        ta.attempted_by,
        ta.attempted_at,
        t.metadata AS task_metadata,
        t.SPECIALIZATIONS AS specializations,
        hn.review_level,
        hn.status AS hn_status,
        ROW_NUMBER() OVER (PARTITION BY ta.task ORDER BY ta.attempted_at DESC) AS rn
    FROM PUBLIC.TASKATTEMPTS ta
    JOIN PUBLIC.PIPELINEV3HUMANNODES hn ON hn.task = ta.task
    LEFT JOIN PUBLIC.TASKS t ON t._ID = ta.task
    WHERE ta.project = '{project_id}'
      AND hn.review_level = '{review_level}'
      AND hn.status = '{status}'
      AND ta.attempted_by != '{EXCLUDE_ATTEMPTER_ID}'
)
SELECT latest.task, latest.response, latest.attempted_by, latest.attempted_at,
       latest.task_metadata, latest.specializations, u.email AS attempter_email
FROM latest
LEFT JOIN PUBLIC.USERS u ON u._ID = latest.attempted_by
WHERE latest.rn = 1
""".strip()


def run_adhoc_query(api_key: str, data_source_id: int, query: str) -> dict:
    """POST to /api/query_results, poll the job, return the result rows."""
    headers = {"Authorization": f"Key {api_key}"}
    resp = requests.post(
        f"{REDASH_BASE}/api/query_results",
        headers=headers,
        json={"data_source_id": data_source_id, "query": query, "max_age": 0},
        timeout=60,
    )
    resp.raise_for_status()
    payload = resp.json()

    if "query_result" in payload:
        return payload["query_result"]

    job = payload.get("job") or {}
    job_id = job.get("id")
    if not job_id:
        raise RuntimeError(f"Unexpected Redash response: {payload}")

    deadline = time.time() + 60 * 30
    while time.time() < deadline:
        time.sleep(2)
        r = requests.get(f"{REDASH_BASE}/api/jobs/{job_id}", headers=headers, timeout=30)
        r.raise_for_status()
        j = r.json().get("job", {})
        status = j.get("status")
        if status == 3:
            qr_id = j.get("query_result_id")
            r2 = requests.get(
                f"{REDASH_BASE}/api/query_results/{qr_id}",
                headers=headers,
                timeout=60,
            )
            r2.raise_for_status()
            return r2.json()["query_result"]
        if status == 4:
            raise RuntimeError(f"Redash job failed: {j.get('error', '<no error>')}")

    raise TimeoutError("Redash query did not complete within 30 minutes")


def parse_response(raw: object) -> object:
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw
    return raw


def extract_inline_form_data(response: object) -> dict:
    if not isinstance(response, dict):
        return {"shape": "unknown"}

    keys = set(response.keys())
    if keys == {"type", "url"}:
        return {"shape": "cds_pointer", "url": response.get("url"), "type": response.get("type")}

    before = response.get("before")
    if not isinstance(before, dict):
        return {"shape": "unknown", "top_keys": sorted(keys)}

    out = {
        "shape": "inline",
        "step_inventory": sorted(before.keys()),
        "rubrics": [],
        "eval": None,
        "prompt": None,
        "story": None,
        "per_run_responses": [],
        "code_container_attachments": [],
        "oracle_solution": None,
        "contributor_verifier_py": None,
    }

    for step_id, step in before.items():
        if not isinstance(step, dict):
            continue
        step_out = step.get("output")
        if not isinstance(step_out, dict):
            continue

        if step_id.startswith("step-RubricCriteriaBuilder-"):
            crits_raw = step_out.get("criteria")
            if not isinstance(crits_raw, list):
                continue
            criteria = []
            kind = None
            for c in crits_raw:
                if not isinstance(c, dict):
                    continue
                ann = c.get("annotations") or {}
                if "failure_1_category" in ann:
                    kind = kind or "failure_modes"
                    criteria.append({
                        "id": c.get("id"),
                        "title": c.get("title"),
                        "failure_1_category": ann.get("failure_1_category"),
                        "failure_1_step": ann.get("failure_1_step"),
                    })
                else:
                    kind = kind or "anti_overfit"
                    criteria.append({
                        "id": c.get("id"),
                        "title": c.get("title"),
                        "weight": c.get("weight"),
                        "correct_answer_justification_rubric": ann.get("correct_answer_justification_rubric"),
                        "incorrect_rubric_justification": ann.get("incorrect_rubric_justification"),
                        "model_mistake_justification_rubric": ann.get("model_mistake_justification_rubric"),
                    })
            out["rubrics"].append({"step_id": step_id, "kind": kind or "unknown", "criteria": criteria})

        elif step_id.startswith("step-RubricEvaluationViewer-"):
            ev = step_out.get("evaluations") or {}
            model_a = ev.get("model_a_metrics") or {}
            score = model_a.get("score") or {}
            out["eval"] = {
                "step_id": step_id,
                "rank": model_a.get("rank"),
                "total_score": score.get("totalScore"),
                "max_score": score.get("maxScore"),
                "percentage": score.get("percentage"),
            }

        elif step_id.startswith("step-PromptTextCollection-"):
            out["prompt"] = {
                "step_id": step_id,
                "main_request_summary": step_out.get("main_request_summary"),
                "safety_tier_annotation": step_out.get("safety_tier_annotation"),
                "tier_justification": step_out.get("tier_justification"),
            }

        elif step_id.startswith("step-ResponseTextCollection-"):
            out["per_run_responses"].append({"step_id": step_id, "output": step_out})

        elif step_id.startswith("step-") and step_id[5:].split("-")[0].isdigit() and out["story"] is None:
            out["story"] = {
                "step_id": step_id,
                "agent_objective": step_out.get("agent_objective"),
                "assigned_universe": step_out.get("assigned_universe"),
                "core_functionalities": step_out.get("core_functionalities"),
                "desired_outcome": step_out.get("desired_outcome"),
                "retrieved_date": step_out.get("retrieved_date"),
                "source_platform": step_out.get("source_platform"),
                "source_url": step_out.get("source_url"),
                "target_domain": step_out.get("target_domain"),
                # Per Rule 10: surface contributor-attached input artifacts so
                # auditors can grade dims 1a (MM Dependence) and 2a-c (Input
                # Artifacts) directly from the inline RESPONSE without falling
                # back to task_metadata.zip_url_artifacts.
                "source_screenshot": step_out.get("source_screenshot") or [],
                "zip_folder": step_out.get("zip_folder") or [],
            }

        # Per Rule 9: surface contributor-submitted artifacts (verifier.py, workspace
        # tarball, oracle solution) wherever they appear. These can show up in any
        # step's output (commonly step-TextCollection-*), not at a fixed step_id.
        ccas = step_out.get("code_container_attachments")
        if isinstance(ccas, list):
            for a in ccas:
                if not isinstance(a, dict):
                    continue
                entry = {
                    "step_id": step_id,
                    "name": a.get("name"),
                    "mimeType": a.get("mimeType"),
                    "fileSizeInBytes": a.get("fileSizeInBytes"),
                    "cdsUrl": a.get("cdsUrl") or a.get("url"),
                    "s3Url": a.get("s3Url"),
                }
                out["code_container_attachments"].append(entry)
                if (entry["name"] or "").lower() == "verifier.py" and out["contributor_verifier_py"] is None:
                    out["contributor_verifier_py"] = entry

        if "oracle_solution_text" in step_out or "oracle_solution_files" in step_out:
            files = step_out.get("oracle_solution_files") or []
            if isinstance(files, dict):
                files = [files]
            out["oracle_solution"] = {
                "step_id": step_id,
                "text": step_out.get("oracle_solution_text"),
                "files": files if isinstance(files, list) else [],
            }

    return out


def html_unescape_deep(obj: object) -> object:
    """Recursively HTML-unescape every string inside a nested dict/list.

    Why this exists: Scale's response serialization layer sometimes encodes
    YAML markers as HTML entities — `>` becomes `&gt;`, `<` becomes `&lt;`,
    quotes become `&quot;`. When a contributor's edited GOLD.yaml contains
    a YAML block-scalar marker (`description: >`), it lands in the task JSON
    as `description: &gt;`, which then looks like the contributor wrote a
    broken YAML file when in fact they didn't. Decoding once here means the
    auditor sub-agents see canonical YAML and don't waste cycles flagging
    rendering artefacts as edits. Non-string nodes pass through untouched.
    """
    import html

    if isinstance(obj, str):
        return html.unescape(obj)
    if isinstance(obj, list):
        return [html_unescape_deep(x) for x in obj]
    if isinstance(obj, dict):
        return {k: html_unescape_deep(v) for k, v in obj.items()}
    return obj


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project", required=True, help="Project ID (24-char ObjectId)")
    parser.add_argument("--layer", required=True, choices=list(LAYER_TO_REVIEW_LEVEL), help="Pipeline layer to audit")
    parser.add_argument("--api-key", default=os.environ.get("REDASH_KEY") or os.environ.get("REDASH_API_KEY"), help="Redash API key (or REDASH_KEY env var; REDASH_API_KEY accepted as fallback)")
    parser.add_argument("--out", required=True, help="Output directory for per-task JSON files")
    parser.add_argument("--data-source-id", type=int, default=SNOWFLAKE_DATA_SOURCE_ID_DEFAULT, help="Redash Snowflake data source ID (default: 30 = GenAI Ops)")
    parser.add_argument("--status", default=DEFAULT_STATUS, help="PIPELINEV3HUMANNODES.status to filter on. Default 'pending' = currently active. Use 'completed' to audit finished tasks, or 'any' to disable the filter.")
    args = parser.parse_args()

    if not args.api_key:
        print("error: --api-key not provided and REDASH_KEY is unset", file=sys.stderr)
        return 2

    print("QC Auditor — created by Marius Delahay.", file=sys.stderr)

    review_level = LAYER_TO_REVIEW_LEVEL[args.layer]
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.status == "any":
        # Drop the status filter entirely — useful when the user explicitly
        # wants every task ever queued at this layer.
        query = build_query(args.project, review_level, status="").replace("AND hn.status = ''", "")
    else:
        query = build_query(args.project, review_level, args.status)
    print(f"Running Redash query for project={args.project} layer={args.layer} (review_level='{review_level}', status={args.status})...", file=sys.stderr)
    emit("tasks_fetch_started", project=args.project, layer=args.layer)
    result = run_adhoc_query(args.api_key, args.data_source_id, query)

    rows = result.get("data", {}).get("rows", [])
    print(f"Got {len(rows)} tasks", file=sys.stderr)

    written = 0
    artifact_url_count = 0
    for row in rows:
        task_id = row.get("task") or row.get("TASK")
        if not task_id:
            continue
        # HTML-decode response and metadata before writing — see html_unescape_deep
        # for the rationale (rendering-layer entity escaping otherwise leaks into
        # the auditor's view of contributor content and produces phantom YAML
        # malformation findings).
        task_metadata = html_unescape_deep(parse_response(row.get("task_metadata") or row.get("TASK_METADATA")))
        response = html_unescape_deep(parse_response(row.get("response") or row.get("RESPONSE")))
        inline_form_data = extract_inline_form_data(response)
        # PUBLIC.TASKS.SPECIALIZATIONS — a JSON-array column (often empty []); store
        # a flat display string for the QC sheet's Specialization column.
        _spec_raw = row.get("specializations") or row.get("SPECIALIZATIONS")
        try:
            _spec = json.loads(_spec_raw) if isinstance(_spec_raw, str) and _spec_raw.strip().startswith("[") else _spec_raw
        except Exception:
            _spec = _spec_raw
        specializations = ", ".join(str(x) for x in _spec) if isinstance(_spec, list) else (_spec or "")
        record = {
            "task_id": task_id,
            "project": args.project,
            "layer": args.layer,
            "attempted_by": row.get("attempted_by") or row.get("ATTEMPTED_BY"),
            "attempter_email": row.get("attempter_email") or row.get("ATTEMPTER_EMAIL") or "",
            "attempted_at": row.get("attempted_at") or row.get("ATTEMPTED_AT"),
            "response": response,
            "response_shape": inline_form_data.get("shape"),
            "inline_form_data": inline_form_data if inline_form_data.get("shape") == "inline" else None,
            "task_metadata": task_metadata,
            "specializations": specializations,
        }
        # Count URL-shaped values inside task_metadata so the orchestrator can
        # decide whether artifact-fetching is worth enabling without re-parsing.
        if isinstance(task_metadata, dict):
            for v in task_metadata.values():
                if isinstance(v, str) and v.startswith(("http://", "https://")):
                    artifact_url_count += 1
        out_path = out_dir / f"{task_id}.json"
        out_path.write_text(json.dumps(record, indent=2, default=str))
        written += 1

    print(f"Wrote {written} task files to {out_dir}", file=sys.stderr)
    if artifact_url_count:
        print(f"Detected {artifact_url_count} URL-shaped artefact references across task_metadata blobs.", file=sys.stderr)
        print("If you want auditors to fetch and audit those artefacts, pass FETCH_ARTIFACTS=true to each spawned auditor.", file=sys.stderr)
    emit(
        "tasks_fetched",
        project=args.project,
        layer=args.layer,
        tasks=written,
        artifact_urls=artifact_url_count,
        out_dir=str(out_dir),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
