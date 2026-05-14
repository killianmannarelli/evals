# elemental_paths — task 69f95c5eca7b6125b7c668c1

## Status

- **Verdict**: PASS
- **Pattern used**: A
- **Initial audit**: `TEMPLATE_DIR+RESET_LOGGED+TIMEOUT` (classifier: `ALL_SEEDS_UNSOLVABLE`)
- **Final audit**: clean (no UNSOLVABLE_SEEDS / SOLVER_TIMEOUT)
- **Replay**: 1591/1591 hash matches, final state `WIN`
- **End-to-end**: every probed seed plays through the engine to `GameState.WIN` — see `play.log`

## Files

| File | What it is |
|---|---|
| `elemental_paths.zip` | The patched zip to upload to Outlier (use as-is) |
| `4.txt` | Grade marker (4 = trusted reviewer) |
| `verify.json` | Full `batch_verify.py` JSON output with `PV_BLOCK_SOLVABILITY=1` |
| `play.log` | Output of the game's own `verify.py` end-to-end playthrough |


## Reproduce the verification locally

Requires the puzzle-verify infrastructure at `/tmp/puzzle_verify/` (see
the top-level `INSTRUCTIONS.md`).

```bash
TASK=69f95c5eca7b6125b7c668c1
GAME=elemental_paths
PV_BLOCK_SOLVABILITY=1 PV_SEED_NUM=10 PV_SEED_TIMEOUT=20 \
    /tmp/puzzle_verify/venv/bin/python /tmp/puzzle_verify/batch_verify.py \
    $GAME.zip $TASK
```

Expected: `"overall": "PASS"`, `"audit_issues": []` (`bellows_forge`
has the structural advisory `IPE_IS_ROOT`, which is non-blocking).
