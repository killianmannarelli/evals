# Inputs & parsing

This is a **static-only** QA. The single input is a **CSV** with one row per task and two columns:

- `task_id` — a stable id used as `task_name` throughout the pipeline and the report.
- `environment_docker_file` — a URL to that task's bundle zip.

No rollouts, trajectories, pass@K stats, or delivery JSONL are used or needed.

## What the bundle contains

Each `environment_docker_file` zip holds the entire static task. The files the QA needs:

| Purpose | Path inside the bundle |
|---|---|
| Prompt (single-turn) | `instruction.md` |
| Prompt (multi-turn) | `instructions.jsonl` (only one of the two is present) |
| Task id + goal | `task.toml` |
| Rubrics (criteria + weights) | `tests/rubric.json` (a JSON list of `{criteria, weight, …}`) |
| Test code | `tests/test_outputs.py` |
| Test runner | `tests/test.sh` |
| Test weights | `tests/test_weights.json` (`{"tests": [{"test_name", "weight"}, …]}`) |
| Agent-visible environment | `environment/` (Dockerfile, mock-API `server/`, `skills/`, `artifacts/inputs/…`) |

`tests/` is a **grading-harness** directory — it is NOT visible to the agent at runtime, only the
`environment/` tree is. `tests/rubric.json` also carries answer-key fields
(`why_rubric_is_correct`, expected ids/values); those are fine to feed the reviewer as rubric text
but must never be copied into the agent-visible `task_dir`.

## Prepare the inputs (portable — ships with the skill)

Run the bundled script:

```bash
python3 prepare_inputs.py --csv <tasks.csv> --output-dir <OUTPUT_DIR>
```

It downloads each bundle, extracts the `environment/` tree to
`<OUTPUT_DIR>/task_dirs/<task_id>/environment`, and writes one record per task to
`<OUTPUT_DIR>/batch_NNN.json` (a JSON list with a single object) plus `<OUTPUT_DIR>/manifest.json`
with the task count. The record shape the static reviewer reads:

```json
{
  "task_name": "6a271a812033c9fde3b43f64",
  "prompt_text": "<contents of instruction.md (or joined instructions.jsonl)>",
  "rubrics": [
    {"id": 1, "criterion": "<rubric.json[i].criteria>", "weight": 5}
  ],
  "tests": {                       // omitted entirely for rubric-only tasks
    "test_code": "<contents of tests/test_outputs.py>",
    "test_sh": "<contents of tests/test.sh>",
    "test_weights": {"test_name": 3}
  },
  "task_dir": "/abs/path/to/<OUTPUT_DIR>/task_dirs/<task_id>/environment",
  "has_pytest_tests": true
}
```

Parsing rules the script applies (keep these if you re-implement):

- **Rubric `id`** — `rubric.json` has no id field; assign positional `1..N` in file order (that is
  how the grader aligns them to verdicts).
- **Rubric `weight` sign** — keep as-is. A negative weight is a **penalty** rubric ("agent should
  NOT do X"); the sign matters for coverage/sign-error checks.
- **`test_weights`** — flatten `tests/test_weights.json` `tests[]` into `{test_name: weight}`.
- **`has_pytest_tests`** — true when `tests/test_outputs.py` exists. Rubric-only tasks omit the
  whole `tests` block and skip the test dimension.
- **Prompt** — prefer `instruction.md`; if only `instructions.jsonl` is present, join its turns
  into readable `[role] content` text.

The bundle layout may be flat at the zip root or nested under a `<task_id>/` prefix — the script
detects the root by locating `task.toml` and resolves the other members relative to it.

### `scale-cds://` URLs

The script downloads plain `https` URLs directly. If a `environment_docker_file` is a
`scale-cds://` URL it must be signed via the dashboard `transform_obj_s3_url` endpoint first; the
script stops with a clear message rather than guessing. Resolve such URLs to signed `https` before
running (or extend `download()` with your signing session).

## Validate before proceeding

Never run the audit on empty data (the agents will flag everything). The script prints `[ok]` /
`[THIN]` per task; you can also re-check:

```bash
python3 -c "
import json, glob
for b in sorted(glob.glob('<OUTPUT_DIR>/batch_*.json')):
    d = json.load(open(b))[0]
    print('OK' if d.get('prompt_text','').strip() and d.get('rubrics') else 'EMPTY', b)
"
```

If batches are `EMPTY`, the bundle didn't resolve or the layout differs — fix before continuing.
Detect rubric-only datasets the same way (`tests` block absent across a sample) and tell the static
agent to skip test analysis.
