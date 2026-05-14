# polarity_tiles — task 69fec71276fb1b01f6ba0f26

## Status

- **Verdict**: PASS
- **Pattern used**: A
- **Initial audit**: `RESET_LOGGED+UNSOLVABLE[0..9]` (classifier: `UNKNOWN`)
- **Final audit**: clean (no UNSOLVABLE_SEEDS / SOLVER_TIMEOUT)
- **Replay**: 67/67 hash matches, final state `WIN`
- **End-to-end**: every probed seed plays through the engine to `GameState.WIN` — see `play.log`

## Files

| File | What it is |
|---|---|
| `polarity_tiles.zip` | The patched zip to upload to Outlier (use as-is) |
| `4.txt` | Grade marker (4 = trusted reviewer) |
| `verify.json` | Full `batch_verify.py` JSON output with `PV_BLOCK_SOLVABILITY=1` |
| `play.log` | Output of the game's own `verify.py` end-to-end playthrough |


## Reproduce the verification locally

Requires the puzzle-verify infrastructure at `/tmp/puzzle_verify/` (see
the top-level `INSTRUCTIONS.md`).

```bash
TASK=69fec71276fb1b01f6ba0f26
GAME=polarity_tiles
PV_BLOCK_SOLVABILITY=1 PV_SEED_NUM=10 PV_SEED_TIMEOUT=20 \
    /tmp/puzzle_verify/venv/bin/python /tmp/puzzle_verify/batch_verify.py \
    $GAME.zip $TASK
```

Expected: `"overall": "PASS"`, `"audit_issues": []` (`bellows_forge`
has the structural advisory `IPE_IS_ROOT`, which is non-blocking).
