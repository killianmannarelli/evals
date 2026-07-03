# CDQ (customer-data-quality-check) run — L10 2026-06-30 — RESUME

Static eval-design QA over the 137 L10 tasks (of the 143-task 2026-06-30 queue) that carry an
`environment_docker_file` bundle URL. Started in the remote session; **not finished** — preserved
here so it can be completed locally without redoing the expensive static pass.

## State at snapshot
- **Input:** `tasks.csv` — 137 tasks, columns `task_id, environment_docker_file, attempt_id`.
  (6 of the 143 lack a bundle URL and are out of scope: 1af226, 476d4b, b43f6c, cb4464, ee2e38, aeb434.)
- **Static review: 98/137 complete** and merged into `static_findings.json`
  (`{task_id: {findings:[{tier,defect_type,rubric_ids,test_names,explanation,fix}], dims:{…}}}`).
  Tally so far: 24 action_required + 39 review_recommended across 46 tasks.
  The remaining 39 were re-running when the container restarted (list: see below).
- **Verifier stage: NOT started.** **Decision CSV: not built.** **Sheet column: not added.**

## The 39 static tasks still to run
6a2252a7226df6fc69476d54,d55,d57 · b43f82 · 3056cd,d4,dc,de,e4,e9,ed · 352d22 · cb4461,cb4469 ·
ee2e2a,ee2e32 · 640092,640096,64009e,6400a7,6400a8,6400ab · 37316c,373174,373181 ·
9c09b4,b5,be,bf,c5,c7,cb,cf · aeb41f,aeb42d,aeb439,aeb43b,aeb43e,aeb440
(full task_ids are the rows of `tasks.csv` not present as keys in `static_findings.json`.)

## Resume locally (skill: `.claude/skills/customer-data-quality-check`)
1. `python3 prepare_inputs.py --csv tasks.csv --output-dir <OUT>` (re-downloads bundles; public https).
2. Finish static for the 39 above (skill stage 2, Sonnet) → merge into `static_findings.json`.
3. **Verifier stage (stage 3):** for each task, strip `tier` from its findings → feed the bare
   claims (`defect_type, rubric_ids, test_names, explanation`) to one neutral Sonnet verifier per
   task (blind — no prior tier), which re-derives each from the task files and emits a per-task
   decision `{verdict: pass|non-fail|fail, confidence, summary, flagged_dimensions, audit_md}`.
4. Render the decision CSV (`render_report_csv.py`) + run the hygiene check.
5. **Add the column** to Google Sheet tab **"L10 2026-06-30"** (sheet id
   `1Ld547RXFeh91dd4c5eO1XKla2xlHkz0eMVphg1CNwx0`): a new **"Data-quality QA"** column = verdict +
   confidence, keyed by `task_id`; the 6 no-bundle tasks get a blank cell.

## Notes
- Reviewers must run on **Sonnet** (skill requirement).
- Cross-validation seen so far: the static QA independently reproduced several openclaw audit Fails
  (5dfa non-existent HbA1c discrepancy, 06e5 FreshDirect user gap, 3f68 missing bookshelf photo,
  c0e8, d5b sign error) **and** surfaced environment-level defects openclaw can't see (leftover
  answer files copied into the workspace, misaligned crop images, a mock-API loading the wrong data
  file, an answer-key leak in conversation history, tests asserting against static seed data).
