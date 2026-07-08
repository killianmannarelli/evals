"""stage2_prepare — one download per task; build the per-task ctx the checks consume.

From each bundle zip we extract (single download):
  - grading artifacts (full tests/rubric.json, optional visual_rubrics.json, test_outputs.py,
    test_weights.json, instruction.md, task.toml)  -> ctx.rubric / visual_rubrics / test_code …
  - mock-API data (environment/server/**/data.json) -> ctx.service_data  (for answer_key_data)
  - if LLM checks enabled: the full environment/ tree -> task_dirs/<id>/environment (image view)
    + a reviewer batch record batch/<id>.json mirroring the skill's shape.

Writes <run_dir>/ctx/<task_id>.json for every task.
"""
from __future__ import annotations
import io, json, os, zipfile, concurrent.futures
from pathlib import Path
from src import common

MAX_DATA_CHARS = 400_000   # cap per-task service_data blob (answer_key_data grep)


def _extract_service_data(z, names, root):
    blobs = {}
    for n in names:
        if n.lower().endswith("data.json") and "/server/" in n and "/__pycache__/" not in n:
            try:
                txt = z.read(n).decode("utf-8", "replace")
            except Exception:
                continue
            key = n.split("/server/", 1)[1]
            blobs[key] = txt[:MAX_DATA_CHARS]
    return blobs


def _extract_env_tree(z, names, root, dest: Path):
    prefix = root + "environment/"
    for n in names:
        if not n.startswith(prefix) or n.endswith("/"):
            continue
        rel = n[len(root):]                      # environment/...
        out = dest / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        try:
            out.write_bytes(z.read(n))
        except Exception:
            pass


def _batch_record(task_id, parsed, task_dir):
    rub = parsed.get("rubric") or []
    rubrics = [{"id": i + 1, "criterion": (c.get("criteria") or c.get("title") or ""),
                "weight": c.get("weight")} for i, c in enumerate(rub)]
    rec = {"task_name": task_id, "prompt_text": parsed.get("instruction_raw") or "",
           "rubrics": rubrics, "task_dir": str(task_dir),
           "has_pytest_tests": bool(parsed.get("test_code_raw"))}
    if parsed.get("test_code_raw"):
        rec["tests"] = {"test_code": parsed["test_code_raw"], "test_weights": parsed.get("test_weights", {})}
    return rec


def _one(task_id, meta_row, digest_entry, run_dir: Path, want_env: bool):
    url = None
    if meta_row.get("metadata"):
        url = json.loads(meta_row["metadata"]).get("environment_docker_file")
    if not url:
        return (task_id, "no-bundle")
    data = common.download(url)
    z = zipfile.ZipFile(io.BytesIO(data))
    names = z.namelist()
    root = next((n[:-len("task.toml")] for n in names if n.endswith("task.toml")), "")
    parsed = common.parse_bundle(data)
    task_dir = run_dir / "task_dirs" / task_id / "environment"
    if want_env:
        _extract_env_tree(z, names, root, run_dir / "task_dirs" / task_id)
        json.dump([_batch_record(task_id, parsed, task_dir)],
                  open(_p(run_dir / "batch" , f"{task_id}.json"), "w"))
    ctx = {
        "task_id": task_id, "attempt_id": digest_entry.get("attempt_id"),
        "layer": digest_entry.get("layer"), "category": digest_entry.get("category"),
        "subcategory": digest_entry.get("subcategory"), "mm_input": digest_entry.get("mm_input"),
        "task_type": digest_entry.get("task_type"), "reward": digest_entry.get("reward") or {},
        "rubric": parsed.get("rubric") or [], "visual_rubrics": parsed.get("visual_rubrics"),
        "test_code": parsed.get("test_code_raw"), "test_weights": parsed.get("test_weights") or {},
        "instruction": parsed.get("instruction_raw"),
        "service_data": _extract_service_data(z, names, root),
        "task_dir": str(task_dir), "batch_file": str(run_dir / "batch" / f"{task_id}.json"),
        "has_visual_rubrics": bool(parsed.get("visual_rubrics")),
    }
    json.dump(ctx, open(_p(run_dir / "ctx", f"{task_id}.json"), "w"))
    return (task_id, "ok")


def _p(d: Path, name):
    d.mkdir(parents=True, exist_ok=True)
    return d / name


def main(cfg, run_dir, want_env=True, workers=8):
    run_dir = Path(run_dir)
    foundation = {r["task"]: r for r in json.load(open(run_dir / "foundation.json"))}
    digest = json.load(open(run_dir / "digest.json"))
    tasks = list(digest)
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(_one, t, foundation.get(t, {}), digest[t], run_dir, want_env): t for t in tasks}
        for f in concurrent.futures.as_completed(futs):
            try:
                results.append(f.result())
            except Exception as e:
                results.append((futs[f], "ERR:" + str(e)[:80]))
    ok = sum(1 for _, s in results if s == "ok")
    print(f"stage2: prepared {ok}/{len(tasks)} ctx (env_tree={'yes' if want_env else 'data-only'})")
    for tid, s in results:
        if s != "ok":
            print("  ", tid, s)
    return ok


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--data-only", action="store_true", help="skip full environment/ tree (linter-only runs)")
    a = ap.parse_args()
    main(common.load_config(), a.run_dir, want_env=not a.data_only)
