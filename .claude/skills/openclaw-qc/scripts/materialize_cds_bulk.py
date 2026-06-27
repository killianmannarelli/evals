#!/usr/bin/env python3
"""Bulk-materialize cds_pointer tasks via the Snowflake CDS view in ONE batched
query per chunk.

Why this exists: per-task fetch_openclaw_single.py resolves a single attempt at a
time, and running many in parallel (xargs -P N) fires N concurrent CDS-view jobs
that overload Snowflake — most time out and the task is left stuck as cds_pointer
*even though the view holds perfectly good data*. Materialisation rate collapses
(observed ~19% on a 94-task L8 queue). Querying the view for many attempt_ids at
once (a single IN-list per chunk) sidesteps the contention entirely and resolves
the same tasks reliably.

Reads <ws>/tasks/*.json, finds those whose response_shape is not "inline", batches
their attempt_ids through SCALE_PROD.VIEW.CDS_CHAT_TASK_ATTEMPT_RESPONSES, unwraps
the RESPSONSE VARIANT (production typo — it is NOT `RESPONSE`), and rewrites each
task JSON in place. EVERY pre-existing field is preserved (task_metadata,
specializations, attempt_id, layer, review_*) — only response / response_shape /
inline_form_data are replaced. Tasks the view can't resolve are left untouched
(still cds_pointer) so the caller lists them Pending.

Usage:
    REDASH_KEY=... python3 materialize_cds_bulk.py --workspace <ws> [--chunk 10]
"""
import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_tasks import (  # noqa: E402
    run_adhoc_query,
    parse_response,
    extract_inline_form_data,
    html_unescape_deep,
)

DATA_SOURCE_ID = 30


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--chunk", type=int, default=10,
                    help="attempt_ids per batched view query (keep modest — each "
                         "RESPSONSE is a full OpenClaw object and payloads add up)")
    ap.add_argument("--api-key", default=os.environ.get("REDASH_KEY"))
    a = ap.parse_args()
    if not a.api_key:
        print("error: --api-key not provided and REDASH_KEY is unset", file=sys.stderr)
        return 2

    ws = a.workspace.rstrip("/")
    pending = {}  # attempt_id -> task file path
    for f in glob.glob(f"{ws}/tasks/*.json"):
        try:
            d = json.load(open(f))
        except Exception:
            continue
        if d.get("response_shape") != "inline" and d.get("attempt_id"):
            pending[d["attempt_id"]] = f
    aids = list(pending)
    print(f"{len(aids)} unmaterialized task(s) to resolve via CDS view "
          f"(chunk={a.chunk})", file=sys.stderr)
    if not aids:
        return 0

    done = unresolved = 0
    nchunks = (len(aids) + a.chunk - 1) // a.chunk
    for ci in range(nchunks):
        chunk = aids[ci * a.chunk:(ci + 1) * a.chunk]
        inlist = "','".join(chunk)
        q = f"""
        SELECT cds.TASK_ATTEMPT_ID AS aid, cds.RESPSONSE AS response_json
        FROM SCALE_PROD.VIEW.CDS_CHAT_TASK_ATTEMPT_RESPONSES cds
        WHERE cds.TASK_ATTEMPT_ID IN ('{inlist}')
        """
        try:
            res = run_adhoc_query(a.api_key, DATA_SOURCE_ID, q)
            rows = res["data"]["rows"]
        except Exception as e:
            print(f"  chunk {ci + 1}/{nchunks} query failed: {e}", file=sys.stderr)
            continue
        got = {r.get("AID"): r.get("RESPONSE_JSON") for r in rows}
        for aid in chunk:
            raw = got.get(aid)
            fp = pending[aid]
            if raw is None:
                unresolved += 1
                continue
            try:
                parsed = html_unescape_deep(parse_response(raw))
                if not isinstance(parsed, dict) or not any(
                    k in parsed for k in ("before", "after", "turns")
                ):
                    unresolved += 1
                    continue
                inline = extract_inline_form_data(parsed)
                rec = json.load(open(fp))
                rec["response"] = parsed
                rec["response_shape"] = inline.get("shape")
                rec["inline_form_data"] = inline if inline.get("shape") == "inline" else None
                json.dump(rec, open(fp, "w"), indent=2, default=str)
                if inline.get("shape") == "inline":
                    done += 1
                else:
                    unresolved += 1
            except Exception as e:
                print(f"  {aid} parse/write failed: {e}", file=sys.stderr)
                unresolved += 1
        print(f"  chunk {ci + 1}/{nchunks}: cumulative materialized={done} "
              f"unresolved={unresolved}", file=sys.stderr)

    print(f"DONE materialized={done} unresolved={unresolved}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
