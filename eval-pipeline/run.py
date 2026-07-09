#!/usr/bin/env python3
"""eval-pipeline CLI orchestrator.

  python run.py --queue L10                 # both evals on the live L10 queue
  python run.py --ids tasks.txt             # explicit task list
  python run.py --ids tasks.txt --only-linters   # fast deterministic pass, no LLM cost
  python run.py --run-id my_run --no-sheet       # custom run dir, skip the sheet write

The deterministic linters + prep + assemble + sheet run fully in Python here. The LLM checks
(cdq_static, audit_hybrid31) are compute-heavy Opus Workflows: when enabled, this emits their
runnable workflow scripts into <run_dir>/workflows/ and prints launch instructions — Claude
launches them, then `python -m src.resume` harvests results and re-runs stage4/5.
"""
from __future__ import annotations
import argparse, sys, datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from src import common, stage1_pull, stage2_prepare, stage3_checks, stage4_assemble, stage5_human, cache
from checks import registry


def run_id_for(sel):
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%d_%H%M")
    return f"{sel}_{ts}"


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--queue", type=int, help="review_level of the live pending queue (e.g. 10)")
    g.add_argument("--ids", help="path to newline-separated task_ids")
    ap.add_argument("--only-linters", action="store_true", help="skip LLM checks (fast, no cost)")
    ap.add_argument("--no-sheet", action="store_true")
    ap.add_argument("--run-id")
    ap.add_argument("--tab")
    ap.add_argument("--exclude", help="path to newline-separated task_ids to EXCLUDE from the run")
    ap.add_argument("--backtest", help="gold findings json to measure recall against after assembly")
    ap.add_argument("--no-cache", action="store_true", help="re-audit every task (ignore cached verdicts)")
    a = ap.parse_args()

    cfg = common.load_config()
    if a.queue is not None:
        cfg["pipeline"]["selection"]["queue"]["review_level"] = a.queue
    sel = "ids" if a.ids else f"L{cfg['pipeline']['selection']['queue']['review_level']}"
    run_dir = common.RUNS / (a.run_id or run_id_for(sel))
    run_dir.mkdir(parents=True, exist_ok=True)
    print(f"=== eval-pipeline run: {run_dir.name} ===")

    llm_enabled = [c for c in cfg["pipeline"]["enabled_checks"]
                   if c in registry.LLM_CHECKS] and not a.only_linters

    stage1_pull.main(cfg, run_dir, "ids" if a.ids else "queue", a.ids, a.exclude)
    stage2_prepare.main(cfg, run_dir, want_env=bool(llm_enabled))
    stage3_checks.main(cfg, run_dir)
    if not a.no_cache:
        cache.seed(cfg, run_dir)          # reuse cached LLM verdicts (attempt_id unchanged)

    if llm_enabled:
        try:
            from checks.llm import emit as llm_emit
            paths = llm_emit.emit_all(cfg, run_dir)
            print(f"\n>>> LLM checks enabled ({llm_enabled}). Emitted workflow scripts:")
            for p in paths:
                print("     ", p)
            print(">>> Launch each via the Workflow tool, then run: "
                  f"python -m src.resume --run-dir {run_dir} && "
                  f"python -m src.stage4_assemble --run-dir {run_dir} && "
                  f"python -m src.cache --update --run-dir {run_dir} && "
                  f"python -m src.stage5_human --run-dir {run_dir}\n")
        except Exception as e:
            print(f"[warn] LLM emit unavailable ({e}); continuing with linter findings only")

    report = stage4_assemble.main(cfg, run_dir)
    if not a.no_cache:
        cache.update(cfg, run_dir)
    if a.backtest:
        from src import backtest
        backtest.run(a.backtest, str(run_dir / "report.json"))
    if not a.no_sheet:
        stage5_human.main(cfg, run_dir, a.tab)
    print(f"=== done: {run_dir}/report.json ===")


if __name__ == "__main__":
    main()
