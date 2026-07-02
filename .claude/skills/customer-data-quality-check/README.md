# customer-data-quality-check — end-to-end runbook

Static **eval-design QA** for a set of agentic-benchmark tasks. You give it a **CSV** of
`(task_id, environment_docker_file)`; it produces a **per-task decision CSV** (verdict ∈
pass/non-fail/fail, confidence /100, flagged dimensions, flags, and a short markdown audit) — the
thing you drop into a Google Sheet to decide what to ship, quick-audit, or fix — plus an optional
**Markdown** batch summary. It flags eval-design defects (bad rubrics, unfair/broken tests,
missing data/tools, oracle leaks, unclear prompts), audits the **task definition** (never the
model), and uses **no rollouts, trajectories, or pass@K stats** (loader-A only).

## For an agent handed this directory

If a user points you at this directory and says *"using this CSV as input, run the eval"*, do the
following, in order. `SKILL.md` + the files under `references/` are the source of truth; this README
is the operational sequence.

### 0. Prereqs
- Python 3 (stdlib only for all scripts here).
- Network access to download each `environment_docker_file` URL.
- A subagent runner that can dispatch **Claude Sonnet** workers (required for the reviewers).

### 1. Prepare inputs (one command)
```bash
python3 prepare_inputs.py --csv <TASKS.csv> --output-dir <OUTPUT_DIR>
```
This downloads each bundle and writes, under `<OUTPUT_DIR>`:
- `batch_NNN.json` — one per task: `task_name`, `prompt_text`, `rubrics[]`, `tests`, `task_dir`,
  `has_pytest_tests`.
- `manifest.json` — `{"task_count": N}`.
- `task_dirs/<task_id>/environment/` — the extracted, agent-visible environment tree.

Column names auto-detect; override with `--id-col` / `--url-col`. If the CSV has `scale-cds://`
URLs, sign them to `https` first (see `references/inputs-and-parsing.md`).

**Validate** (never audit empty data):
```bash
python3 -c "
import json, glob
for b in sorted(glob.glob('<OUTPUT_DIR>/batch_*.json')):
    d = json.load(open(b))[0]
    print('OK' if d.get('prompt_text','').strip() and d.get('rubrics') else 'EMPTY', b)
"
```
Every task should print `OK`. Investigate any `EMPTY` before continuing.

### 2. Static review — one Sonnet subagent per task, in waves of ~15
Read `references/subagents.md` → "Static agent". Write its prompt (with a `<TASK>` placeholder) to
`<OUTPUT_DIR>/static_prompt_template.txt`, substitute the task name per task, and dispatch. Each
agent reads its `batch_NNN.json` + `task_dir` + `references/agentic_quality_eval_guide.md` and writes
its findings JSON (schema in `references/subagents.md`) to a per-task output file. **Wait for a whole
wave to finish before starting the next; retry missing indices in a final wave.**

*(Optional)* If a batch record has `sample_traces`, one lightweight pass may scan that single
delivered trajectory for **blatant** runtime defects only (HTTP 500 from a mock, oracle in a tool
output, judge-vs-test contradiction). It's a bonus net, not a real trajectory check — see
`references/subagents.md` → "single-trace runtime scan". Its findings merge with the static ones.

### 3. Objective FP verification — one Sonnet verifier per task
Read `references/subagents.md` → "Stage 3". First apply the deterministic sign-aware filter, then
dispatch one verifier per task with the **claims only** (strip tier/confidence/author). Keep
`CONFIRMED` (at the verifier's tier), drop `REFUTED`, downgrade `UNCERTAIN` →
`review_recommended`. Track "N confirmed, M removed".

### 4. Build the report — CSV is the deliverable
Assemble the surviving findings + each task's decision fields (`verdict`, `confidence`,
`flagged_dimensions`, `audit_md`) into `<OUTPUT_DIR>/report_data.json` (schema in the docstring of
`render_report_md.py` and in `references/report.md`). Then render the **CSV** (primary) and,
optionally, the Markdown batch summary — both from that one file:
```bash
# PRIMARY: per-task decision CSV for the sheet (carryover columns merged via --inputs-dir)
python3 render_report_csv.py --data <OUTPUT_DIR>/report_data.json --inputs-dir <OUTPUT_DIR> --output /tmp/<eval>_qa_<YYYY_MM_DD>.csv
# OPTIONAL batch summary
python3 render_report_md.py  --data <OUTPUT_DIR>/report_data.json --output /tmp/<eval>_qa_<YYYY_MM_DD>.md
```
The CSV is sorted worst-first and includes `needs_validation` (yes for `fail` **and** `non-fail`)
and a one-line `summary`. Triage: `pass` → deliver blindly; filter `needs_validation = yes` → skim
`summary`/`audit_md`, agree or disagree, fix what's real.

### 5. Hygiene check (must be all-zero before sharing)
Run the leakage check from `references/report.md` on **both** outputs (internal ids, mount paths,
usernames, PII, and rubric answer-key text like `why_rubric_is_correct`). Every count must be 0.
Then hand off the `.csv` (+ the `.md` summary if useful).

## Files in this directory

| File | Role |
|---|---|
| `SKILL.md` | What the skill is + the 4-stage pipeline (start here) |
| `prepare_inputs.py` | Stage 1 — CSV → `batch_NNN.json` + `manifest.json` + `task_dirs/` |
| `references/inputs-and-parsing.md` | Input contract, bundle layout, parsing rules |
| `references/subagents.md` | Static agent + neutral verifier prompts, dispatch/waves |
| `references/agentic_quality_eval_guide.md` | The detailed rubric/test/coverage judging standard |
| `references/report.md` | Report IA, payload schema, render commands, hygiene check |
| `render_report_csv.py` | **Primary** — per-task decision CSV renderer (stdlib) |
| `render_report_md.py` | Optional Markdown batch-summary renderer (stdlib) |

## What it does NOT do
- No model rollouts / trajectories / pass@K (that was "loader B" — removed).
- No model-behavior flags, no infra/crash flags — eval-design defects only.
- No network calls at build time beyond downloading the bundles in stage 1.
