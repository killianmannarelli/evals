#!/usr/bin/env python3
"""Re-fetch the 10 viewer-only L10 tasks once the Snowflake CDS view catches up.

The 2026-06-08 L10 run could only audit those 10 text-only: the CDS view
(SCALE_PROD.VIEW.CDS_CHAT_TASK_ATTEMPT_RESPONSES) had not yet materialised their
attempts, so the inline rubric + input images were unavailable (their factual/
visual golds stayed UNVERIFIABLE). This polls the view and, once an attempt has
landed, pulls the unwrapped inline RESPONSE so the task can be re-audited with
its real inputs.

    export REDASH_KEY=...        # never commit
    python3 scripts/refetch_l10_inputs.py            # check readiness
    python3 scripts/refetch_l10_inputs.py --out /tmp/l10  # + dump ready responses

Self-contained (only `requests`); does not depend on the qc-auditor package.
"""
import argparse, json, os, sys, time, requests

REDASH = "https://redash.scale.com"
DATA_SOURCE = 30  # _Snowflake (GenAI Ops)
PROJECT = "69f95a0f0992772af7907a03"  # mj_blue_shell
# The 10 net-new L10-pending task IDs from the 2026-06-08 run.
TASK_IDS = [
    "6a17cc59ea9a7319a6ca06d7", "6a17cc59ea9a7319a6ca06ec", "6a17cc59ea9a7319a6ca06ee",
    "6a17cc59ea9a7319a6ca06fb", "6a17cc59ea9a7319a6ca06fc", "6a0ffe25088789f616666871",
    "6a14c6a002f937bcb61ec0e5", "6a210a723e6e63649d93d61d", "6a1fbaebeae04350ba1af211",
    "6a1fbaebeae04350ba1af222",
]


def run_sql(key, sql):
    """POST an ad-hoc query, poll the job, return result rows."""
    h = {"Authorization": f"Key {key}"}
    r = requests.post(f"{REDASH}/api/query_results", headers=h,
                      json={"data_source_id": DATA_SOURCE, "query": sql, "max_age": 0}, timeout=60)
    r.raise_for_status()
    p = r.json()
    if "query_result" in p:
        return p["query_result"]["data"]["rows"]
    jid = (p.get("job") or {}).get("id")
    deadline = time.time() + 30 * 60
    while time.time() < deadline:
        time.sleep(2)
        j = requests.get(f"{REDASH}/api/jobs/{jid}", headers=h, timeout=30).json().get("job", {})
        if j.get("status") == 3:
            qr = requests.get(f"{REDASH}/api/query_results/{j['query_result_id']}", headers=h, timeout=60)
            return qr.json()["query_result"]["data"]["rows"]
        if j.get("status") in (4, 5):
            raise RuntimeError(f"Redash job failed: {j.get('error')}")
    raise TimeoutError("query did not complete in 30 min")


def latest_attempts(key):
    """task_id -> latest attempt_id for the 10 tasks (Scale bot excluded handled upstream)."""
    inlist = ",".join(f"'{t}'" for t in TASK_IDS)
    rows = run_sql(key, f"""
        WITH la AS (SELECT task, _id AS attempt,
                           ROW_NUMBER() OVER (PARTITION BY task ORDER BY attempted_at DESC) rn
                    FROM public_raw.taskattempts
                    WHERE project = '{PROJECT}' AND task IN ({inlist}))
        SELECT task::STRING task, attempt::STRING attempt FROM la WHERE rn = 1""")
    g = lambda r, k: r.get(k) or r.get(k.upper())
    return {g(r, "task"): g(r, "attempt") for r in rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--api-key", default=os.environ.get("REDASH_KEY"))
    ap.add_argument("--out", help="dir to dump unwrapped inline responses for ready tasks")
    a = ap.parse_args()
    if not a.api_key:
        print("error: REDASH_KEY unset", file=sys.stderr); return 2

    att = latest_attempts(a.api_key)
    inlist = ",".join(f"'{att[t]}'" for t in TASK_IDS if att.get(t))
    rows = run_sql(a.api_key, f"""
        SELECT TASK_ATTEMPT_ID::STRING id
        FROM SCALE_PROD.VIEW.CDS_CHAT_TASK_ATTEMPT_RESPONSES
        WHERE TASK_ATTEMPT_ID IN ({inlist})""")
    ready = {(r.get("id") or r.get("ID")) for r in rows}

    n_ready = 0
    for t in TASK_IDS:
        aid = att.get(t)
        ok = aid in ready
        n_ready += ok
        print(f"  {t[-4:]} {t}  attempt={aid}  CDS_view={'READY' if ok else 'pending'}")
    print(f"\n{n_ready}/{len(TASK_IDS)} ready in the CDS view.")

    if a.out and n_ready:
        os.makedirs(a.out, exist_ok=True)
        for t in TASK_IDS:
            if att.get(t) in ready:
                rows = run_sql(a.api_key, f"""
                    SELECT RESPSONSE::STRING r FROM SCALE_PROD.VIEW.CDS_CHAT_TASK_ATTEMPT_RESPONSES
                    WHERE TASK_ATTEMPT_ID = '{att[t]}'""")
                body = (rows[0].get("r") or rows[0].get("R")) if rows else None
                open(os.path.join(a.out, f"{t}.json"), "w").write(body or "{}")
        print(f"Dumped {n_ready} unwrapped responses to {a.out} — re-audit with fact_extractor_v3.")
    elif n_ready:
        print("Re-run with --out <dir> to dump the ready responses, then re-audit.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
