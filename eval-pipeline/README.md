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

# Backtest recall against the customer feedback set (the "catch everything" proof):
python -m src.build_gold                                    # sheet -> gold/customer_findings.json (+ customer_tasks.txt)
python run.py --ids gold/customer_tasks.txt --backtest gold/customer_findings.json
python -m src.backtest --run-dir runs/<id>                 # or compare any run's report.json to gold
```

`run.py` orchestrates the stages; you can also run any stage standalone (`python -m src.stage1_pull ...`).

## Tune anywhere — everything lives in `config/`

| Want to change… | Edit |
|---|---|
| project / layer / status / which checks run | `config/pipeline.yaml` |
| **cost**: Sonnet vs Opus, reasoning effort, grader count, master skip-on-clean | `config/pipeline.yaml` `models` (`reviewer`, `reviewer_effort`, `audit_grader_roles`, `audit_master`) |
| **task selection**: exclude a list, reuse cached verdicts | `config/pipeline.yaml` (`selection.exclude_ids_file`, `cache`) or `--exclude PATH` / `--no-cache` |
| **audit quality**: adversarial refute of FAILs / low-confidence re-check | `config/pipeline.yaml` `audit_verify` (default off) |
| defect types, tiers, human labels, verdict rule | `config/taxonomy.yaml` |
| weight-mix bar, linter sensitivities/tiers, reward cutoffs, accuracy-type mapping | `config/thresholds.yaml` |
| a linter's logic | `checks/linters/<name>.py` (one small, unit-tested file each) |
| an LLM reviewer's prompt/schema | `checks/llm/<name>.py` (workflow-script generator) |

Add a new check: drop a module in `checks/linters/` exposing `run(task_ctx, cfg) -> [finding]`,
register it in `checks/registry.py`, and add its name to `enabled_checks`.

**Cost dial (biggest levers first):** `reviewer: sonnet` (~5× cheaper than opus) → `reviewer_effort`
(medium/low) → `audit_grader_roles` (fewer graders) → `audit_master: if_flagged|never` (skip the
verify pass) → the `cache` (skip unchanged tasks entirely) and `--exclude` (skip a known set).
Turn `audit_verify` on (Opus) only for high-stakes runs.

**Prove coverage:** `python -m src.build_gold` then `--backtest gold/customer_findings.json` reports
recall vs the customer's real findings (task-level + per-defect-type). Every run's human sheet also
ships an **Overview** tab (verdict split, cross-lens confidence, top defects, fails by category).

## How it works (stages)

1. **stage1_pull** — select tasks (queue or ids) → per-task foundation: attempt, metadata,
   `environment_docker_file`, category/modality, and **reward** (computed from
   `passAtKResults.runs[*]`).
2. **stage2_prepare** — download each bundle, extract every grading artifact
   (`tests/rubric.json`, optional `visual_rubrics.json`, `tests/test_outputs.py`,
   `tests/test_weights.json`, `task.toml`) + the agent-visible `environment/` tree.
3. **stage3_checks** — run every enabled check. Linters run inline (instant). LLM checks are
   emitted as background Workflow scripts (model + effort from `config/pipeline.yaml` — default
   **Sonnet / medium** for low cost; bump to Opus/high for a deeper run) whose transcripts persist
   in `~/.claude`. Audit cost is further tuned by `audit_grader_roles` and `audit_master`
   (`if_flagged` skips the verify pass on clean tasks).
4. **stage4_assemble** — merge + dedupe all findings, reward-prioritize, roll up a per-task
   verdict (worst-wins across linters ∪ CDQ ∪ DRAWER), run the leakage hygiene scan.
5. **stage5_human** — write ONE human-first tab: a color-coded global **PASS / NON-FAIL / FAIL**,
   a one-line headline, prioritized plain-English feedback + the recommended fix, reward, and
   evidence columns — sorted worst-first (never overwrites existing tabs).

## The linters (deterministic checks)

Eight pure-Python checks (`checks/linters/<name>.py`, `run(task_ctx, cfg) -> [finding]`) that
catch the *mechanical* defect classes an LLM pass is unreliable for. They run in milliseconds,
cost nothing, and are unit-tested. Each reads a specific grading artifact and emits the same
taxonomy tokens the LLM audit uses, so stage4 dedupes them together.

| Linter | What it catches (plain English) | Reads | Tier | Precision |
|---|---|---|---|---|
| `negweight_ratio` | Rubric has zero / too few negative-weight penalty criteria — §9g wants ~25% (cap 30%). This is the drawer's own deterministic Task-level flag. | `rubric.json` weights | **action_required** (zero) · review (off-band) | **Rock-solid** — arithmetic reproduction of §9g |
| `weight_mix` | Weight not concentrated on accuracy (≥60% of total), or vision under-weighted **on a visual task** (≥50% of the accuracy mix) — Karan's bar. | `rubric.json` type+modality+weight, `mm_input` | review | **Solid** math; vision bar now gated to visual tasks (no longer fires on text-only) |
| `pytest_hardcount` | Brittle exact-count asserts in the grader (`len(x)==6`, `test_..._is_six`) that fail a correct-but-differently-shaped output. | `test_outputs.py` | review → **action_required** when `mean_reward < 0.40` | Heuristic (regex); the reward gate raises precision |
| `visual_sign` | A criterion describing *undesired* behavior but scored **positive** (rewards the bad thing). | `visual_rubrics.json` / `rubric.json` | review | Heuristic (keyword markers) — raises a flag, LLM audit escalates |
| `visual_vs_text` | Same criterion in `visual_rubrics.json` and `rubric.json` graded with **opposite sign** (the two grading passes contradict). | both rubric files | review | Heuristic (fuzzy title match ≥0.85); low volume |
| `overspec_exact` | Criterion demands an **exact** value (timestamp / long decimal) a range would cover, *and* both reference models rarely pass it. | `rubric.json` + model pass-rates | review | Heuristic marker + empirical pass-rate gate |
| `answer_key_data` | Rubric grades against a currency amount that appears **nowhere** in the mock-API data (likely a wrong answer key). | mock `data.json` + `rubric.json` | review | Conservative (cents-only, aggregates skipped) |
| `visual_capacity` | **Low visual capacity needed**: a (nominally) multimodal task whose rubric weight barely requires visual understanding (weak MM dependence) — could largely be solved without the images/video. Text-only tasks exempt. | `rubric.json` modality+weight, `mm_input` (+ tagger accuracy buckets) | review | Deterministic on modality; sharper with tagger buckets |

**Design principle — only structural checks fail alone.** `negweight_ratio` (a faithful
reproduction of the §9g rule) can drive a task to **Fail** on its own. Every *heuristic* linter
emits `review_recommended` only; it becomes a Fail when the **LLM audit independently agrees**
(both emit the same token, so stage4 merges them) or, for `pytest_hardcount`, when low reward
corroborates. This keeps the linters a fast, free, reproducible pre-pass **without letting a
keyword false-positive hard-fail a correct task.** Tune every threshold in
`config/thresholds.yaml`; toggle any linter in `enabled_checks`.

## Rubric tagger (5-bucket accuracy classifier)

An LLM check (`rubric_tagger`, vendored from Scale's Rubric Tagging Guide) classifies **every
criterion by its text + task goal** into `accuracy / exist / formatting / process / safety` — a
*semantic* accuracy signal, independent of the authored `type` tag (which is frequently mislabeled,
e.g. a factual value-extraction tagged `task completion`). It runs tag → independent reviewer pass
on the config model. Its buckets are attached back to each criterion in `stage3`, so **`weight_mix`
and `visual_capacity` measure accuracy from the tagger's judgment** rather than the raw tag — falling
back to the authored `type` when the tagger hasn't run. This is what makes the "low visual capacity"
flag sharp: it measures the visual share of the *accuracy* weight (correctness that truly needs
vision), which is robust to the modality mistags being exactly what's under review.

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
