# eval-pipeline

A durable, config-driven QA pipeline for OpenClaw MM-Rubrics tasks. It runs **both** eval
lenses — the customer static eval-design QA (**CDQ**) and our **Hybrid 3+1 rubric-quality
audit** vs the V10 spec — plus a set of **deterministic linters** that catch the mechanical
defect classes an LLM pass is unreliable for, and it is **reward-aware** (mean_reward /
weighted_score from pass@K). Output is one combined Google-Sheet tab, sorted worst-first.

Built after the customer's own eval-design QA (128 tasks / 143 findings, "Customer Feedback
2026-07-06") showed our ad-hoc process was missing defect classes, reward signal, and the
weight-mix bar — and because the ad-hoc scratchpad scripts kept getting wiped. This is the
"catch everything, tune anywhere" replacement.

## Quick start

```bash
export REDASH_KEY=...                       # Redash API key
export GOOGLE_SA_JSON=/path/to/sa.json      # Sheets service-account (default: ../creds/sa.json)

# Run on the live L10 queue (both evals + all linters):
python run.py --queue L10

# Run on a specific task list:
python run.py --ids mytasks.txt

# Run only the fast deterministic linters (no LLM cost):
python run.py --ids mytasks.txt --only-linters

# Backtest recall against the customer feedback set:
python run.py --ids runs/customer_feedback_128.txt --backtest gold/customer_findings.json
```

`run.py` orchestrates the stages; you can also run any stage standalone (`python -m src.stage1_pull ...`).

## Tune anywhere — everything lives in `config/`

| Want to change… | Edit |
|---|---|
| project / layer / status / models / which checks run | `config/pipeline.yaml` |
| defect types, tiers, defect→dimension map, verdict rule | `config/taxonomy.yaml` |
| weight-mix bar, linter sensitivities, reward cutoffs, accuracy-type mapping | `config/thresholds.yaml` |
| a linter's logic | `checks/linters/<name>.py` (one small, unit-tested file each) |
| an LLM reviewer's prompt/schema | `checks/llm/<name>.py` (workflow-script generator) |

Add a new check: drop a module in `checks/linters/` exposing `run(task_ctx, cfg) -> [finding]`,
register it in `checks/registry.py`, and add its name to `enabled_checks`.

## How it works (stages)

1. **stage1_pull** — select tasks (queue or ids) → per-task foundation: attempt, metadata,
   `environment_docker_file`, category/modality, and **reward** (computed from
   `passAtKResults.runs[*]`).
2. **stage2_prepare** — download each bundle, extract every grading artifact
   (`tests/rubric.json`, optional `visual_rubrics.json`, `tests/test_outputs.py`,
   `tests/test_weights.json`, `task.toml`) + the agent-visible `environment/` tree.
3. **stage3_checks** — run every enabled check. Linters run inline (instant). LLM checks are
   emitted as background Workflow scripts (Sonnet) whose transcripts persist in `~/.claude`.
4. **stage4_assemble** — merge + dedupe all findings, reward-prioritize, roll up a per-task
   verdict, run the leakage hygiene scan.
5. **stage5_sheet** — write ONE new combined tab (never overwrites existing tabs).

## Resilience

LLM checks run as background Workflows; `src/resume.py` harvests their results from the
persisted transcripts, schema-validates them, and lists any tasks still missing so they can be
re-run. Deterministic linters are instant and idempotent. Per-run outputs are committed under
`runs/<run_id>/`, so a wiped scratchpad never loses results — re-clone the branch and continue.

## Layout

```
config/     pipeline.yaml · taxonomy.yaml · thresholds.yaml
src/        common.py · stage1_pull.py … stage5_sheet.py · resume.py
checks/     registry.py · linters/*.py · llm/*.py
tests/      pytest for the linters (fixtures from real rubric.json)
runs/       durable per-run outputs
gold/       customer-feedback backtest set
run.py      CLI orchestrator
```
