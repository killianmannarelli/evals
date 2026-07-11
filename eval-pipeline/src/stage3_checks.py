"""stage3_checks — run the enabled DETERMINISTIC linters over every task ctx.

LLM checks (cdq_static, audit_hybrid31) are emitted as background Workflow scripts by
checks/llm/*.py and harvested by src/resume.py — they are NOT run here. This stage produces
<run_dir>/findings_linters.json = {task_id: [finding, ...]}.
"""
from __future__ import annotations
import glob, json
from pathlib import Path
from src import common
from checks import registry


def main(cfg, run_dir):
    run_dir = Path(run_dir)
    enabled = [c for c in cfg["pipeline"]["enabled_checks"] if c in registry.LINTERS]
    # rubric-tagger buckets (if the tagger has run) — attach the semantic accuracy/exist/formatting/
    # process/safety label to each criterion so weight_mix + visual_capacity use it over the authored type.
    tags = json.load(open(run_dir / "rubric_tags.json")) if (run_dir / "rubric_tags.json").exists() else {}
    out = {}
    n_find = 0
    for p in sorted(glob.glob(str(run_dir / "ctx" / "*.json"))):
        ctx = json.load(open(p))
        tb = tags.get(ctx["task_id"]) or {}
        if tb:
            for i, c in enumerate(ctx.get("rubric") or [], 1):
                if isinstance(c, dict) and str(i) in tb:
                    c["bucket"] = tb[str(i)]
        fs = registry.run_linters(ctx, cfg, enabled)
        out[ctx["task_id"]] = fs
        n_find += len(fs)
    json.dump(out, open(run_dir / "findings_linters.json", "w"), indent=1)
    import collections
    by_check = collections.Counter(f["check"] for fs in out.values() for f in fs)
    print(f"stage3: ran linters {enabled} over {len(out)} tasks -> {n_find} findings")
    for c, n in by_check.most_common():
        print(f"   {c}: {n}")
    return out


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("--run-dir", required=True)
    main(common.load_config(), ap.parse_args().run_dir)
