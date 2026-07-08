# L10_opus run — Opus MAX + real V10 spec + drawer Task-level-flags eval

83 L10 tasks (same set as L10_full). Deterministic pass done: 376 findings, sheet 'eval L10_opus' (gid=893254108).

## LLM workflows (Opus MAX, effort max)
| check | Workflow task | run id | transcript dir | output file |
|---|---|---|---|---|
| cdq_static (83) | wvrjvndp1 | wf_70e1427c-9a3 | subagents/workflows/wf_70e1427c-9a3 | tasks/wvrjvndp1.output |
| audit drawer-flags (~415) | wd9by988a | wf_c39eb3c9-4ab | subagents/workflows/wf_c39eb3c9-4ab | tasks/wd9by988a.output |

## Finish / recover
```
cd eval-pipeline; export REDASH_KEY=... GOOGLE_SA_JSON=.../creds/sa.json
SUB=/Users/killian.mannarelli/.claude/projects/-Users-killian-mannarelli/cf1c8afd-39d4-4017-8a8d-964da247826e/subagents/workflows
TASKS=/Users/killian.mannarelli/.claude/projects/-Users-killian-mannarelli/cf1c8afd-39d4-4017-8a8d-964da247826e/tasks
python -m src.resume --run-dir runs/L10_opus --cdq-out $TASKS/wvrjvndp1.output --cdq-tdir $SUB/wf_70e1427c-9a3 --audit-out $TASKS/wd9by988a.output --audit-tdir $SUB/wf_c39eb3c9-4ab
python -m src.stage4_assemble --run-dir runs/L10_opus
python -m src.stage5_sheet --run-dir runs/L10_opus --tab "eval L10_opus COMBINED"
```
Interrupted workflow -> relaunch Workflow({scriptPath: workflows/<name>.js, resumeFromRunId: <run id>}) then re-harvest.

## NOTE (2026-07-08): audit relaunched flags-only
First audit run (wf_bdf0484f-058) hit StructuredOutput retry wall (all-21-grades schema too big for Opus MAX); stopped. Grader now returns flags-only. New run: wd9by988a / wf_c39eb3c9-4ab. CDQ already harvested into findings_llm.json.

## NOTE 2: audit reduced to 2 graders (gen1+rubric) + master for time (~3-4h vs 7-11h). Run: wd9by988a / wf_c39eb3c9-4ab.

## DONE 2026-07-09: audit complete (wd9by988a, 81/83; 2 retry-cap fails: 6a271a812033c9fde3b43f63, 6a31a2f7424da28b8ccb4459). Combined tab 'eval L10_opus COMBINED' gid=387981138 written. 60 fail / 23 non-fail / 761 findings.
