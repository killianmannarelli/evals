"""stage1_pull — select tasks (live queue or explicit ids) and pull per-task foundation
from Redash: latest attempt, metadata (bundle url, category/modality/passAtKResults), and the
computed reward. Writes <run_dir>/foundation.json, digest.json, tasks.csv.
"""
from __future__ import annotations
import csv, json, os, sys
from pathlib import Path
from src import common


def _task_ids(cfg, selection, ids_file):
    proj = cfg["pipeline"]["project"]["id"]
    if selection == "ids":
        return [l.strip() for l in open(ids_file) if l.strip()]
    q = cfg["pipeline"]["selection"]["queue"]
    sql = f"""
    WITH LA AS (SELECT *, ROW_NUMBER() OVER (PARTITION BY task ORDER BY attempted_at DESC) rn
      FROM public_raw.taskattempts WHERE project='{proj}')
    SELECT DISTINCT ta.task::STRING task
    FROM LA ta JOIN PUBLIC.PIPELINEV3HUMANNODES hn ON hn.task=ta.task
    LEFT JOIN public_raw.tasks t ON ta.task=t._id
    WHERE ta.rn=1 AND LOWER(t.status)='pending' AND LOWER(hn.status)='pending'
      AND hn.review_level={int(q['review_level'])}"""
    return [r["task"] for r in common.rows_of(common.redash_run(sql, cfg["pipeline"]["redash"]["data_source_id"]))]


def main(cfg, run_dir, selection="queue", ids_file=None):
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    proj = cfg["pipeline"]["project"]["id"]
    ids = _task_ids(cfg, selection, ids_file)
    if not ids:
        print("stage1: no tasks selected"); return []
    inlist = "','".join(ids)
    sql = f"""
    WITH LA AS (SELECT *, ROW_NUMBER() OVER (PARTITION BY task ORDER BY attempted_at DESC) rn
      FROM public_raw.taskattempts WHERE project='{proj}' AND task IN ('{inlist}'))
    SELECT ta.task::STRING task, ta._id::STRING attempt, MAX(hn.review_level) layer, t.metadata::STRING metadata
    FROM LA ta LEFT JOIN PUBLIC.PIPELINEV3HUMANNODES hn ON hn.task=ta.task
    LEFT JOIN public_raw.tasks t ON ta.task=t._id WHERE ta.rn=1 GROUP BY 1,2,4"""
    rows = common.rows_of(common.redash_run(sql, cfg["pipeline"]["redash"]["data_source_id"]))
    json.dump(rows, open(run_dir / "foundation.json", "w"))

    digest = {}
    with open(run_dir / "tasks.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["task_id", "environment_docker_file", "attempt_id", "layer"])
        w.writeheader()
        for r in rows:
            m = json.loads(r["metadata"]) if r.get("metadata") else {}
            w.writerow({"task_id": r["task"], "environment_docker_file": m.get("environment_docker_file"),
                        "attempt_id": r["attempt"], "layer": r["layer"]})
            digest[r["task"]] = {
                "attempt_id": r["attempt"], "layer": r["layer"],
                "category": m.get("category"), "subcategory": m.get("subcategory"),
                "task_type": m.get("task_type"), "mm_input": m.get("mm_input"),
                "reward": common.compute_reward(m.get("passAtKResults")),
                "env_docker": m.get("environment_docker_file"),
            }
    json.dump(digest, open(run_dir / "digest.json", "w"), indent=1)
    got = {r["task"] for r in rows}
    print(f"stage1: selected {len(ids)}, resolved {len(rows)}"
          + (f", MISSING {sorted(set(ids)-got)}" if set(ids) - got else ""))
    rw = [d["reward"].get("mean_reward") for d in digest.values() if d["reward"].get("mean_reward") is not None]
    if rw:
        print(f"stage1: reward mean_reward min/median/max = "
              f"{min(rw):.3f} / {sorted(rw)[len(rw)//2]:.3f} / {max(rw):.3f}; "
              f"< {cfg['thresholds']['reward']['low_reward']} : {sum(1 for x in rw if x < cfg['thresholds']['reward']['low_reward'])}")
    return list(digest)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--ids"); ap.add_argument("--queue", type=int)
    a = ap.parse_args()
    cfg = common.load_config()
    if a.queue is not None:
        cfg["pipeline"]["selection"]["queue"]["review_level"] = a.queue
    main(cfg, a.run_dir, "ids" if a.ids else "queue", a.ids)
