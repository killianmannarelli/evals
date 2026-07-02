---
name: customer-data-quality-check
description: >
  Static eval-design QA for a set of agentic-benchmark tasks. Given a CSV of (task_id,
  environment_docker_file), it prepares per-task inputs, runs a static review of each task's
  files (prompt, rubrics, tests, inputs, environment), then a single neutral verifier re-derives
  each finding from primary evidence (blind to the prior verdict) so only high-confidence issues
  survive, and a per-task decision CSV (verdict / confidence / flags, for a Google Sheet) is
  produced, plus an optional Markdown batch summary. The QA target is the EVAL
  data/rubrics/tests/tools/environment, NOT the model — never flag model behavior, and this skill
  does NOT use model rollouts, trajectories, or pass@K stats at all.
---

# customer-data-quality-check

QA the **eval design** of a set of agentic-benchmark tasks, reading only the **static task files**
(no model rollouts, no trajectories, no pass@K). This is a **loader-A-only** pipeline: everything
needed comes from each task's `environment_docker_file` bundle.

Per task:

1. **Static check** — defects a careful reader finds in the task files before any model runs
   (inaccurate rubrics, contradictory/over-specified/tautological tests, unclear prompt, sign
   errors, coverage gaps, missing input data, unreachable oracle/answer leak, missing tools/env).
2. **Objective FP verification** — a fresh reviewer re-derives every static finding from primary
   evidence (the task files/images), seeing only the *claims* (never a prior verdict, tier, or
   confidence) so it cannot anchor. It seeks evidence both for and against, keeps only what
   concrete evidence supports, and assigns the tier from its own read. It drops anything ambiguous.

Output: a per-task **decision CSV** (the deliverable the team acts on — `verdict` ∈
pass/non-fail/fail, `confidence` /100, flagged dimensions, flags, and a short markdown audit per
task), plus an optional **Markdown** batch summary. Both render from a shared `report_data.json` so
they never drift.

## Input

**A single CSV** with two columns per task: a stable **`task_id`** and the **`environment_docker_file`**
URL. Nothing else is required — the delivery JSONL, pass@K stats, and rollouts are NOT used. Any
**extra columns** (e.g. `attempt_id`, `review_level`) are treated as **passthrough**: ignored by
every reviewer, but echoed verbatim into the output CSV so you can carry them across.

Each `environment_docker_file` is a zip that contains the whole static task:
`instruction.md` / `instructions.jsonl` (prompt), `task.toml` (id + goal), `tests/rubric.json`
(rubric criteria + weights), `tests/test_outputs.py` + `tests/test.sh` + `tests/test_weights.json`
(the tests), and the agent-visible `environment/` tree (Dockerfile, mock-API `server/`, `skills/`,
and `artifacts/inputs/…` data/images).

`prepare_inputs.py` (shipped with this skill) downloads each bundle and emits the per-task records
the static reviewer reads. See [references/inputs-and-parsing.md](references/inputs-and-parsing.md).

## Pipeline

1. **Prepare inputs** — `python3 prepare_inputs.py --csv <tasks.csv> --output-dir <OUTPUT_DIR>`
   writes one `<OUTPUT_DIR>/batch_NNN.json` per task (prompt, rubrics, tests, `task_dir`,
   `has_pytest_tests`) + `<OUTPUT_DIR>/manifest.json`, and extracts each task's `environment/` tree
   to `<OUTPUT_DIR>/task_dirs/<task_id>/environment`.
   → [references/inputs-and-parsing.md](references/inputs-and-parsing.md)
2. **Per-task static analysis** — for each task spawn one static review agent (Claude Sonnet,
   batched in waves). *Optional:* a low-power single-trace runtime scan of the one delivered sample
   trajectory for blatant runtime defects. → [references/subagents.md](references/subagents.md)
3. **Objective FP verification** — one neutral verifier agent per task adjudicates that task's
   findings from claims alone (no prior verdict/tier), confirms or drops each from the task files,
   and assigns its tier from primary evidence. → [references/subagents.md](references/subagents.md)
4. **Build + ship report** — write `report_data.json`, render the decision **CSV** (primary; +
   optional Markdown summary), run the hygiene check. → [references/report.md](references/report.md)

## Additional Notes

- **Eval defects only** — never flag model behavior. This skill never sees a model rollout; it
  audits the task definition itself.
- **A grader/judge crash is infra, not a data defect** — reserve `GRADER_BROKEN` for genuine
  authoring defects a vendor can fix: a test that can never pass as written, missing/malformed test
  weights, or a judge-vs-test contradiction.
- **"Missing data" usually means the model would need to look** — the dominant false positive is "a
  graded fact appears nowhere" when it is actually provided. Before flagging it, open the source in
  its native format (view images, OCR receipts, parse spreadsheets/PDFs — naive text extraction
  misses inline-string sheets and image-only PDFs) and confirm the fact is present in the task's
  agent-visible `environment/` tree.
- **Precision is the key; rate findings by confidence** — every reported finding must survive
  verification with cited evidence, and carries one of two tiers: **action required** for critical
  defects you are highly confident in, **review recommended** for likely issues you are reasonably
  but not fully sure of. Drop anything weaker — a missed issue is cheaper than a false one.
- **Findings are model-produced hypotheses, not ground truth** — the static check and the verifier
  are both LLM/VLM reviewers; neither is a source of truth. The verifier re-derives every finding
  from scratch. **Visual claims get extra scrutiny:** a reviewer can miscount or misread an image
  from a capability gap (e.g. flags "rubric assumes 6 people, image has 5" when the reviewer itself
  miscounted) — view the image directly before shipping.
- **No leakage** — strip internal job names, dataset slugs, raw filesystem mounts, usernames, and
  any customer/PII identifiers from the shared report; the hygiene check (references/report.md) must
  return all-zero before sharing. Note in particular that `tests/rubric.json` carries answer-key
  fields (`why_rubric_is_correct`, expected ids/values) — these feed the reviewer as rubric text but
  must never be placed into the agent-visible `task_dir`.
