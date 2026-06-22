---
name: openclaw-qc
description: >-
  End-to-end rubric-QC for the OpenClaw MM Rubrics project (project_id
  69f95a0f0992772af7907a03, codename mj_blue_shell). Use when the user wants to
  audit a layer's queue (L-1/L0/L1/L10/L12), QC OpenClaw rubrics, check the
  platform drawer, or fill/refresh the OpenClaw QC Google Sheet. Triggers on
  "audit OpenClaw", "QC the L0/L10 queue", "run the rubric audit", "fill the QC
  sheet", "mj_blue_shell audit", "least-failing tasks". Runs three steps:
  (1) audit each rubric independently, grounded in the live prompt + viewed input
  images; (2) check the platform drawer and reconcile by verified union; (3) write
  the results to the Google Sheet as a new dated tab in Sheet1's exact format.
  NOT the Thoth swarm benchmark (that's the `fire` skill) — ignore swarm here.
---

# OpenClaw QC — audit yourself, check the drawer, fill the sheet

Project **mj_blue_shell** (`69f95a0f0992772af7907a03`). Audits the contributor-authored **rubric**
(is the rubric sound?), not the model's answer. Tests dims 8a-d are out of scope.

## Credentials (gitignored, never commit)
- `.creds/redash.env` → `export REDASH_KEY=...` for `redash.scale.com` (data source 30 = GenAI Ops Snowflake).
  Every API call sends a non-empty User-Agent (`requests` default is fine) — an empty UA gets a Cloudflare 1010.
- `.creds/sa.json` → the Google service-account JSON; the target Sheet must be shared with its `client_email` as Editor.
  Source the key with `set -a; source .creds/redash.env; set +a` before any fetch.

## The three evals (why the sheet has multiple verdict columns)
1. **Platform score** — the viewer's %: did the model's *response* satisfy the rubric.
2. **My audit** — is the *rubric* sound (the verdict; bands 6a/6b/6c on CB-authored criteria).
3. **Drawer** — the audit embedded in the viewer; high-recall, lower-precision cross-check, reconciled by verified
   union (see `references/calibration.md`). Not an oracle.

## Workflow

Set `WS=qc-runs/<layer>-<date>` (any scratch dir; gitignore it). Run scripts from `scripts/`.

**0. Spec (every run, never cache).**
```
python3 scripts/fetch_spec.py --project 69f95a0f0992772af7907a03 --api-key "$REDASH_KEY" --out "$WS/spec.md"
```

**1. Queue + scores.** Get the layer's pending tasks, then scrape the viewer for score + drawer:
```
python3 scripts/fetch_tasks.py --project 69f95a0f0992772af7907a03 --layer <L0|L10|...> --status pending \
        --api-key "$REDASH_KEY" --out "$WS/tasks/"
python3 scripts/fetch_platform_eval.py --workspace "$WS"          # writes platform_eval/<tid>.json (score + drawer)
```
Rank by `score.pct` to pick a slice (e.g. "least-failing" = highest scores; or all). The viewer carries the rubric
criteria + drawer even for tasks the Redash CDS view hasn't materialised yet.

**2. Rehydrate inline + extract bundles** (for the chosen task ids):
```
python3 scripts/fetch_openclaw_single.py --task-id <id,id,...> --api-key "$REDASH_KEY" --out "$WS/tasks/"
python3 scripts/fact_extractor_v3.py --task-dir "$WS/tasks/" --out-dir "$WS/sot/" --spec "$WS/spec.md"
```
`response_shape: inline` → fully auditable (prompt + rubric + downloaded images). `cds_pointer` → the CDS view
hasn't caught up; mark `audit_incomplete` and re-try later with `scripts/refetch_inputs.py` (it polls the view).
NEVER substitute `task_metadata` for the missing inline RESPONSE (Rule 10).

**2b. Surface the trajectory (every run).** Dump the agent's tool-RESULTS so auditors ground "connected-service"
golds in the real environment responses instead of dismissing them as unverifiable:
```
python3 scripts/dump_trajectory.py --task "$WS/tasks/<tid>.json" --out "$WS/sot/<tid>/trajectory.md"
```
This fixes the most common miss — a Pass built on golds the trajectory actually disproves. Tool-RESULTS are
admissible grounding; `desired_outcome` / Pass@K are not (dump_trajectory excludes them).

**2c. Surface the unit tests (every run).** Pull the task's `verifier.py` out of the rehydrated JSON so auditors can
grade **Tests-Correctness** (a test whose logic contradicts the prompt/inputs or is overly specific, wrongly failing a
correct response, is incorrect; ≥10% incorrect → Fail). No-op when the task has no tests.
```
python3 scripts/dump_tests.py --task "$WS/tasks/<tid>.json" --out "$WS/sot/<tid>/unit_tests.py"
```

**3. AUDIT YOURSELF (grounded).** Spawn one auditor per task (batch ~3/agent), prompt = `agents/grounded_auditor.md`
(fill `<WORKSPACE>` and `<TID>`). Each reads `sot/<tid>/` and **views the input images** to verify golds → writes
`$WS/validated/<tid>.json`.

**4. CHECK THE DRAWER (verified union).** After the auditors, spawn one master per task, prompt =
`agents/master_reconcile.md`. Each folds the drawer (`platform_eval/<tid>.json`) into my findings — adopting only
drawer flags that survive against the prompt + pixels, rejecting spot-check-exempt / out-of-band / unverifiable ones
→ writes `$WS/reconciled/<tid>.json` with the final verdict.

**5. FILL THE SHEET.** Author a contributor-facing feedback JSON from the reconciled verdicts + findings — plain,
present-tense, no internal jargon (see `references/sheet_format.md`). Then:
```
python3 scripts/push_audit_to_sheet.py --feedback "$WS/feedback.json" --tab "<Layer> <YYYY-MM-DD>"
```
This adds a NEW tab in `Sheet1`'s exact format (blank row 1, frozen bold header, 10 columns, WRAP on every cell,
full 24-char IDs, FAIL/Non-Fail/Pass casing, hyperlinked "Open the task"). It never overwrites — delete the old
tab first if replacing.

## Calibration
`references/calibration.md` is the condensed ruleset (bands, ruling #1 spot-check exemption, Rule 19c unverifiable,
sign-inversion, over-spec, out-of-scope dims, drawer reconciliation). `references/{auditor,master_auditor,
project_overrides}.md` are the full methodology the agents read.

## Files
- `scripts/` — `fetch_spec.py`, `fetch_tasks.py`, `fetch_openclaw_single.py` (CDS-view rehydration),
  `fact_extractor_v3.py`, `fetch_platform_eval.py` (drawer scrape), `refetch_inputs.py` (poll the CDS view),
  `push_audit_to_sheet.py` (Sheet1-format writer), `events.py` (helper).
- `agents/grounded_auditor.md`, `agents/master_reconcile.md` — the two spawn prompts.
- `references/` — calibration + sheet format + the full auditor/master/overrides methodology.
