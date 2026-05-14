# Puzzle solvability-gate batch — handoff to local Claude

6 task folders, one per puzzle, plus this top-level instructions file. Each
folder is self-contained — drop it into your local Outlier workflow and
the zip is ready to upload.

## Folder layout

```
results/puzzle_solvability_gate_20260514/
├── INSTRUCTIONS.md                          ← you are here
├── SUMMARY.md                               ← cross-task summary table
├── deep_verify_results.json                 ← per-seed worker output (all 60 cells)
├── 69f95c5eca7b6125b7c668c1_elemental_paths/
│   ├── README.md           ← per-task instructions
│   ├── elemental_paths.zip ← the zip to submit
│   ├── 4.txt               ← grade marker
│   ├── verify.json         ← batch_verify.py JSON with PV_BLOCK_SOLVABILITY=1
│   └── play.log            ← engine-level play-through output
├── 69fec71276fb1b01f6ba0f07_phase_echo/
│   ├── …
│   ├── play.log
│   └── per_seed_play.log   ← extra per-seed BFS replay log (phase_echo only)
├── 69fec71276fb1b01f6ba0f26_polarity_tiles/
├── 69fec71276fb1b01f6ba0f31_bellows_forge/
├── 69fec71276fb1b01f6ba0f43_merge_blocks/
└── 69fec71276fb1b01f6ba0f44_signal_cascade/
```

Folder names follow `<24-hex task_id>_<game_name>`. The zip inside is named
`<game_name>.zip` — Outlier expects the game-name form, not the task-id form.

## Local Claude prompt

Paste this verbatim into a fresh local Claude session in the directory that
contains the 6 task folders (e.g. after cloning this repo and `cd
results/puzzle_solvability_gate_20260514/`):

> I have 6 puzzle task folders, each containing a fixed `<game>.zip`, a
> `4.txt` grade marker, a `verify.json`, a `play.log`, and a `README.md`. I
> need to (1) re-verify each zip locally with the v3.2 solvability gate,
> (2) keep the zip exactly as committed (no re-zipping unless verification
> fails), and (3) submit each task to Outlier via the submit-task skill.
>
> For each folder `<task_id>_<game>/`:
> 1. Read `README.md`.
> 2. Run `PV_BLOCK_SOLVABILITY=1 /tmp/puzzle_verify/venv/bin/python
>    /tmp/puzzle_verify/batch_verify.py <game>.zip <task_id>`. Confirm
>    `overall: PASS` and audit clean (bellows_forge is allowed `IPE_IS_ROOT`).
> 3. Submit `<game>.zip` to task `<task_id>` via the submit-task / Playwright
>    flow and the grade in `4.txt`.
>
> Stop if any verify fails — don't auto-rebuild the zip.

## If you need to rebuild a zip (don't, unless you must)

Each `<game>.zip` was rebuilt from a clean `unpacked/` tree via
`cd unpacked && zip -qr <game>.zip .` (with old zip deleted first) — see
the per-task README. The unpacked source is **not** included here (to keep
the bundle small); if you need it back, extract the committed zip into a
fresh directory and modify there. Re-zipping rules:

```bash
rm -f <game>.zip                         # ALWAYS delete first
find unpacked -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
find unpacked -name '*.pyc' -delete
find unpacked -name '.DS_Store' -delete
cd unpacked && zip -qr ../<game>.zip .
```

## Verifier infrastructure

The verifier expects `/tmp/puzzle_verify/` with:
- `venv/bin/python` (with pydantic, numpy, Pillow, flask, httpx, dotenv,
  openpyxl, requests)
- `batch_verify.py`, `auto_patch.py`, `log_recorder.py`, `solve_helpers.py`,
  `_canonical_ipe/mixins.py`

If your local machine doesn't have it, recreate it from the `verify-task`
skill in the bundle: copy `verify-task/*.py` into `/tmp/puzzle_verify/`,
make the venv, install the deps. The first task you verify will populate
the canonical-ipe directory from its own `ipe/` if needed.

## What was changed in each zip (one-line per task)

| Game | Change |
|---|---|
| signal_cascade  | Added Pattern A monkey-patch + regenerated play log (106 actions, fresh WIN) |
| merge_blocks    | Added Pattern A monkey-patch; play log unchanged; stripped .DS_Store |
| phase_echo      | Pattern A + Pattern C seed remap (raw seeds 3,9 → 11,12); stripped __pycache__/.DS_Store |
| bellows_forge   | Pattern A routes BFSSolver.verify_and_report through the existing solve_spec() planner |
| elemental_paths | Pattern A using the puzzle's stored \_solution_path; play log regenerated; removed game_template/ |
| polarity_tiles  | Pattern A greedy solver; stripped leading RESET from play log |

All Pattern A monkey-patches are installed at module load
(`_install_domain_solver()` at the top of `games/<game>/<game>.py`) so they
persist across the verifier's per-seed subprocess workers.

## End-to-end proof (480 cells)

| Game | Seeds × Levels | Reached WIN |
|---|---:|---:|
| signal_cascade  | 10 × 4  | 40/40   |
| merge_blocks    | 10 × 4  | 40/40   |
| phase_echo      | 10 × 4  | 40/40   |
| bellows_forge   | 20 × 4  | 80/80   |
| elemental_paths | 20 × 4  | 80/80   |
| polarity_tiles  | 50 × 4  | 200/200 |
| **Total**       |         | **480/480** |
