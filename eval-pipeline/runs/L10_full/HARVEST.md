# L10_full run — harvest / resume info

First production run of eval-pipeline on the live L10 queue (83 tasks), 2026-07-08.

## Stages done (deterministic, committed)
- stage1/2/3/4/5 complete. Linters: 297 findings. Sheet tab **`eval L10_full`** (gid=154607718)
  written with linter + reward columns. report.json + findings_linters.json committed here.

## LLM workflows in flight
| check | Workflow task | run id (resume) | transcript dir | output file |
|---|---|---|---|---|
| cdq_static (83) | w6kjk2lev | wf_8aafea39-6fd | subagents/workflows/wf_8aafea39-6fd | tasks/w6kjk2lev.output |
| audit_hybrid31 (~415) | wfktnjc38 | wf_03cb7096-339 | subagents/workflows/wf_03cb7096-339 | tasks/wfktnjc38.output |

(paths under /Users/killian.mannarelli/.claude/projects/-Users-killian-mannarelli/cf1c8afd-39d4-4017-8a8d-964da247826e/ and .../tasks/)

## To finish after the workflows complete (or to recover after a wipe)
```
cd eval-pipeline
export REDASH_KEY=... GOOGLE_SA_JSON=.../creds/sa.json
SUB=/Users/killian.mannarelli/.claude/projects/-Users-killian-mannarelli/cf1c8afd-39d4-4017-8a8d-964da247826e/subagents/workflows
TASKS=/Users/killian.mannarelli/.claude/projects/-Users-killian-mannarelli/cf1c8afd-39d4-4017-8a8d-964da247826e/tasks
python -m src.resume --run-dir runs/L10_full \
  --cdq-out $TASKS/w6kjk2lev.output   --cdq-tdir $SUB/wf_8aafea39-6fd \
  --audit-out $TASKS/wfktnjc38.output --audit-tdir $SUB/wf_03cb7096-339
python -m src.stage4_assemble --run-dir runs/L10_full
python -m src.stage5_sheet    --run-dir runs/L10_full --tab "eval L10_full COMBINED"
```
If a workflow was interrupted: relaunch it with Workflow({scriptPath: workflows/<name>.js,
resumeFromRunId: <run id>}) — completed agents return cached — then re-run the harvest.
