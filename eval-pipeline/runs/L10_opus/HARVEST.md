# L10_opus run — Opus MAX + real V10 spec + drawer Task-level-flags eval

83 L10 tasks (same set as L10_full). Deterministic pass done: 376 findings, sheet 'eval L10_opus' (gid=893254108).

## LLM workflows (Opus MAX, effort max)
| check | Workflow task | run id | transcript dir | output file |
|---|---|---|---|---|
| cdq_static (83) | wvrjvndp1 | wf_70e1427c-9a3 | subagents/workflows/wf_70e1427c-9a3 | tasks/wvrjvndp1.output |
| audit drawer-flags (~415) | wq747a1vw | wf_bdf0484f-058 | subagents/workflows/wf_bdf0484f-058 | tasks/wq747a1vw.output |

## Finish / recover
```
cd eval-pipeline; export REDASH_KEY=... GOOGLE_SA_JSON=.../creds/sa.json
SUB=/Users/killian.mannarelli/.claude/projects/-Users-killian-mannarelli/cf1c8afd-39d4-4017-8a8d-964da247826e/subagents/workflows
TASKS=/Users/killian.mannarelli/.claude/projects/-Users-killian-mannarelli/cf1c8afd-39d4-4017-8a8d-964da247826e/tasks
python -m src.resume --run-dir runs/L10_opus --cdq-out $TASKS/wvrjvndp1.output --cdq-tdir $SUB/wf_70e1427c-9a3 --audit-out $TASKS/wq747a1vw.output --audit-tdir $SUB/wf_bdf0484f-058
python -m src.stage4_assemble --run-dir runs/L10_opus
python -m src.stage5_sheet --run-dir runs/L10_opus --tab "eval L10_opus COMBINED"
```
Interrupted workflow -> relaunch Workflow({scriptPath: workflows/<name>.js, resumeFromRunId: <run id>}) then re-harvest.
