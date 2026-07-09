"""src/cache.py — reuse prior LLM verdicts across runs, keyed on attempt_id.

The expensive part of a run is the LLM audit (CDQ + DRAWER). If a task's latest attempt_id
hasn't changed since we last audited it, its verdict is still valid — so we SKIP the LLM for it
and reuse the cached result. Deterministic linters still re-run for every task (instant + free,
so they always reflect the latest linter improvements).

Flow (wired in run.py):
  - after stage3:  seed()  -> pre-fill findings_llm.json + drawer.json with cached records for
                             skippable tasks, and write skip_llm.json so emit._tasks() skips them.
  - after a completed run:  update()  -> store each task's attempt_id + verdict + drawer + llm
                             findings for future reuse.

Cache lives at cache/audited.json (config: pipeline.cache.{enabled,file}). Enabled by default;
an empty cache simply skips nothing (safe on a first run). Toggle with --no-cache on run.py.
"""
from __future__ import annotations
import argparse, json
from datetime import datetime, timezone
from pathlib import Path
from src import common

DEFAULT_FILE = "cache/audited.json"


def _cfgc(cfg):
    return cfg["pipeline"].get("cache", {}) or {}


def enabled(cfg):
    return bool(_cfgc(cfg).get("enabled", True))


def _path(cfg):
    return common.PKG / _cfgc(cfg).get("file", DEFAULT_FILE)


def load(cfg):
    p = _path(cfg)
    return json.load(open(p)) if p.exists() else {}


def _read(run_dir, name, default):
    p = Path(run_dir) / name
    return json.load(open(p)) if p.exists() else default


def cached_ids(cfg, digest):
    """task_ids whose latest attempt_id matches a cached verdict (safe to skip the LLM)."""
    if not enabled(cfg):
        return set()
    c = load(cfg)
    return {tid for tid, d in digest.items()
            if tid in c and c[tid].get("attempt_id") and c[tid]["attempt_id"] == d.get("attempt_id")}


def seed(cfg, run_dir):
    """Pre-seed findings_llm.json + drawer.json with cached records for skippable tasks and write
    skip_llm.json (consumed by emit._tasks). Returns the set of skipped task_ids."""
    run_dir = Path(run_dir)
    digest = _read(run_dir, "digest.json", {})
    ids = cached_ids(cfg, digest)
    if not ids:
        (run_dir / "skip_llm.json").write_text("[]")
        return set()
    c = load(cfg)
    fll = _read(run_dir, "findings_llm.json", {})
    draw = _read(run_dir, "drawer.json", {})
    for tid in ids:
        rec = c[tid]
        fll[tid] = rec.get("findings_llm", [])
        if rec.get("drawer") is not None:
            draw[tid] = rec["drawer"]
    json.dump(fll, open(run_dir / "findings_llm.json", "w"), indent=1)
    json.dump(draw, open(run_dir / "drawer.json", "w"), indent=1)
    (run_dir / "skip_llm.json").write_text(json.dumps(sorted(ids)))
    print(f"cache: reusing {len(ids)} cached LLM verdict(s); LLM will run on the rest.")
    return ids


def update(cfg, run_dir):
    """Store attempt_id + verdict + drawer + llm findings for every task that got an LLM result,
    so a future run with the same attempt_id can skip it."""
    if not enabled(cfg):
        return 0
    run_dir = Path(run_dir)
    digest = _read(run_dir, "digest.json", {})
    fll = _read(run_dir, "findings_llm.json", {})
    draw = _read(run_dir, "drawer.json", {})
    verd = {t["task_id"]: t.get("verdict") for t in _read(run_dir, "report.json", {"tasks": []})["tasks"]}
    c = load(cfg)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    n = 0
    for tid, d in digest.items():
        aid = d.get("attempt_id")
        if not aid or (tid not in draw and tid not in fll):
            continue                      # only cache tasks that actually got an LLM audit
        c[tid] = {"attempt_id": aid, "verdict": verd.get(tid), "drawer": draw.get(tid),
                  "findings_llm": fll.get(tid, []), "stamp": stamp}
        n += 1
    p = _path(cfg)
    p.parent.mkdir(parents=True, exist_ok=True)
    json.dump(c, open(p, "w"), indent=1)
    try:
        shown = p.relative_to(common.PKG)
    except ValueError:
        shown = p
    print(f"cache: stored/updated {n} task verdict(s) -> {shown}")
    return n


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--update", action="store_true", help="store this run's verdicts into the cache")
    ap.add_argument("--seed", action="store_true", help="seed cached verdicts into this run")
    a = ap.parse_args()
    cfg = common.load_config()
    if a.update:
        update(cfg, a.run_dir)
    if a.seed or not a.update:
        seed(cfg, a.run_dir)
