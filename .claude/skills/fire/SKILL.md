---
name: fire
description: Run the full Thoth QC auditor pipeline end-to-end (L0 / L1 / L10 → InfoHub Evals tab) for Scale AI Project Lead Killian Mannarelli. Pulls pending tasks from Redash, spawns best-of-3 auditor sub-agents per task, runs a master validator, compiles CSV findings, pushes to the InfoHub sheet, and commits results. Trigger word "fire" (with or without args, e.g. "fire", "fire L1", "fire L0 L10", "fire run"). ALWAYS asks the user fresh for the Redash API key and the GCP service-account credential every run — never use cached values. Created by Marius Delahay.
---

# Fire — Thoth QC Auditor Pipeline

**Trigger word:** `fire` (any case, optionally followed by layer args like `fire L1`, `fire L0 L10`, `fire all`).

**Owner:** Killian Mannarelli (Scale AI Project Lead).
**Project ID:** `69bee012be45f06904292c9a` (Thoth multi-agent swarm benchmark).
**Working directory:** `/home/user/evals`.
**Results branch:** `claude/run-qc-auditor-CFRgs`.
**Target sheet:** InfoHub `1MOa-semWY_Z-uskBD9bwzGKrMHrHjXwERda9bv2_9QU`, tab `Evals`.

---

## STEP 0 — Attribution

Print exactly: `QC Auditor — created by Marius Delahay.`

## STEP 1 — ALWAYS prompt for credentials (every run, no caching)

Use `AskUserQuestion` to ask the user for two secrets before doing any other work.
Do NOT read `~/evals/.env` for the key. Do NOT use `~/evals/.creds/sa.json` silently.
The user rotates credentials regularly and expects to provide them fresh.

Question 1 — header `Redash key`:
- "Provide the Redash API key for this run."
- Options: `Paste fresh key` (recommended, user selects Other to enter), `Reuse last value (~/.evals/.env REDASH_KEY)`.

Question 2 — header `SA cred`:
- "Provide the GCP service-account JSON path or contents for the InfoHub push."
- Options: `Paste fresh contents`, `Use /home/user/evals/.creds/sa.json`.

Export results as `REDASH_KEY` and `GOOGLE_APPLICATION_CREDENTIALS` (write contents to `/home/user/evals/.creds/sa.json` if pasted). Do not echo the values back.

## STEP 2 — Parse layer arg

- `fire` alone → run `L0 L1 L10`.
- `fire L1` → just L1. `fire L0 L10` → those two. Any subset of `L0 L1 L10` is valid.
- Skip any layer with 0 pending tasks (normal "queue empty" state — not an error).

## STEP 3 — Per-layer pipeline

For each requested layer:

1. `TS=$(date -u +%Y%m%dT%H%M%SZ)`; workspace at `/home/user/evals/qc-auditor-workspace/69bee012be45f06904292c9a_<layer>_$TS/` (subdirs: `tasks/ findings/ validated/`).
2. On the **first** layer only, fetch the spec from Redash SPEC_GETTER (q304995):
   `python3 ~/.claude/skills/qc-auditor/scripts/fetch_spec.py --project 69bee012be45f06904292c9a --api-key $REDASH_KEY --out <ws>/spec.md`
   Copy that `spec.md` into the other layers' workspaces.
3. Fetch pending tasks:
   - **L0 / L1:** default
     `python3 ~/.claude/skills/qc-auditor/scripts/fetch_tasks.py --project 69bee012be45f06904292c9a --layer <layer> --api-key $REDASH_KEY --out <ws>/tasks/`
   - **L10:** prepend `EXCLUDE_ATTEMPTER_ID=""` so the Scale Bot's promoted attempts are INCLUDED — the bot's promotion IS the canonical state at L10.
     `EXCLUDE_ATTEMPTER_ID="" python3 ~/.claude/skills/qc-auditor/scripts/fetch_tasks.py ...`
4. If task count is 0, skip to next layer.
5. **Optional linter pre-pass** (Thoth-specific; runs in parallel with auditors):
   `GOLD_CHECKER_PATH=~/swarmImprove/gold_checker_vercel python3 ~/.claude/skills/qc-auditor/scripts/run_linter.py --workspace <ws> --api-key $REDASH_KEY`
   Package may not be installed — exits 0 silently in that case. Log and continue.
6. For every task, spawn **3 auditors in parallel** (`general-purpose` subagent), batching ~30 per turn. Each gets:
   - `TASK_PATH: <ws>/tasks/<tid>.json`
   - `SPEC_PATH: <ws>/spec.md`
   - `PROJECT_OVERRIDES_PATH: /root/.claude/skills/qc-auditor/project_overrides.md`
   - `USER_NOTES: (empty)`
   - `OUTPUT_PATH: <ws>/findings/<tid>/auditor_<N>.json`
   - `FETCH_ARTIFACTS: true`
   - Prompt body must say "Auditor. Follow /root/.claude/skills/qc-auditor/agents/auditor.md EXACTLY."
7. After all 3 auditors land for a task, spawn one **master** per task (`general-purpose`), prompt body: "Master Auditor. Follow /root/.claude/skills/qc-auditor/agents/master_auditor.md EXACTLY." with:
   - `AUDITOR_FINDINGS_DIR: <ws>/findings/<tid>/`
   - `OUTPUT_PATH: <ws>/validated/<tid>.json`
   - `RETRY_ROUND: 0`
8. Re-audit pass: for any validated file where `status == "needs_reaudit"`, run ONE more round — 3 fresh auditors → 1 round-1 master with `RETRY_ROUND: 1`. Cap at one re-audit per task.
9. Compile CSV:
   `python3 ~/.claude/skills/qc-auditor/scripts/compile_csv.py <ws>/validated/ <ws>/audit_results.csv`
10. Copy results into the repo:
    `cp <ws>/audit_results.csv /home/user/evals/results/<layer>_audit_results.csv` (overwrite per layer).
    Same for `run_summary.json` if present.

## STEP 4 — Push to InfoHub

After all non-empty layers finish:

```
GOOGLE_APPLICATION_CREDENTIALS=/home/user/evals/.creds/sa.json \
  python3 /home/user/evals/scripts/push_to_infohub.py \
    results/L0_audit_results.csv \
    results/L1_audit_results.csv \
    results/L10_audit_results.csv
```

Skip any CSV path that doesn't exist (layer had 0 tasks). The script appends to the `Evals` tab and prints the updated A1-notation range. Retry once after ~10s on 503/DNS errors.

## STEP 5 — Compute "movable" count

For each layer, count tasks whose validated file has **zero `Fail - ...` entries** in `confirmed_findings` — those are movable directly (no blocking violations). Tasks with `Fail - *` are blocked.

```python
import json, glob
for f in glob.glob("<ws>/validated/*.json"):
    fails = [c for c in json.load(open(f)).get("confirmed_findings", [])
             if (c.get("failure_category") or "").lower().startswith("fail")]
```

Report per-layer movable / total counts and the blocked task IDs with their Fail categories.

## STEP 6 — Commit + push

```
cd /home/user/evals
git add results/
git commit -m "qc-auditor: <layers> run <UTC ts>  (counts + InfoHub range)"
git push -u origin claude/run-qc-auditor-CFRgs
```

If push fails on a network error, retry up to 4× with exponential backoff (2s, 4s, 8s, 16s).

## STEP 7 — Final report to user

In one short reply:
- Per-layer task counts.
- Per-layer movable / blocked split (L10 especially — name blocked task IDs and Fail categories).
- InfoHub appended range.
- Commit SHA.

---

## Hard constraints

- **Always ask for the Redash key and SA cred fresh.** Do not silently use `.env` / `.creds/`. User rotates them per run.
- **L10 must include the Scale Bot** — fetch with `EXCLUDE_ATTEMPTER_ID=""`. Bot ID `583cf35b8b8b73054d4344e6` is otherwise excluded by default; at L10 that's wrong because the bot's promoted attempt is the canonical state.
- **Bot attempts:** when an auditor needs the "gold", use `output.yaml_text` of step `step-TextCollection-b87a9591843f` (the text). The `output.gold_fixed` uploaded file may carry the wrong upload — text is authoritative.
- **Never commit secrets.** `.env` and `.creds/` are gitignored.
- **Never push to `main`** without explicit user permission. Default branch for results is `claude/run-qc-auditor-CFRgs`.
- **Never `--no-verify`.**
- **Don't re-push CSV rows** already in InfoHub — the script appends; running twice duplicates. If a duplicate is pushed, delete via `batchUpdate` `DeleteDimensionRequest` only after explicit user confirmation.
- **Redash 401/403:** stop and log. Don't retry.
- **InfoHub 404:** stop and log. Don't retry. 404 means the SA can't see the sheet — share it as Editor.
- **InfoHub 503 / transient DNS:** retry once after ~10s. After two failures, stop and log.
- **Token-wise this run is expensive.** Don't add extra "let me double-check" passes that aren't in this skill.

---

## Reference files (already on disk)

- `~/.claude/skills/qc-auditor/SKILL.md` — full skill description
- `~/.claude/skills/qc-auditor/scripts/fetch_spec.py` — Redash SPEC_GETTER (q304995)
- `~/.claude/skills/qc-auditor/scripts/fetch_tasks.py` — pending tasks at layer (respects `EXCLUDE_ATTEMPTER_ID`)
- `~/.claude/skills/qc-auditor/scripts/compile_csv.py` — validated/ → CSV
- `~/.claude/skills/qc-auditor/scripts/run_linter.py` — Thoth gold-checker pre-pass
- `~/.claude/skills/qc-auditor/agents/auditor.md` — auditor sub-agent contract
- `~/.claude/skills/qc-auditor/agents/master_auditor.md` — master/best-of-3 contract
- `~/.claude/skills/qc-auditor/project_overrides.md` — Thoth project-specific notes
- `/home/user/evals/scripts/push_to_infohub.py` — Sheets append (stdlib + openssl JWT, SA or OAuth)
- `/home/user/evals/scripts/loop_run.md` — original per-iteration runbook
- `/home/user/evals/.env` (gitignored) — `REDASH_KEY=`, `EXCLUDE_ATTEMPTER_ID=583cf35b8b8b73054d4344e6` (default — override to "" for L10)
- `/home/user/evals/.creds/sa.json` (gitignored) — SA private key (`deltaeval@serene-column-490216-q1.iam.gserviceaccount.com`)

---

## Key IDs and accounts

- **Project:** `69bee012be45f06904292c9a` (Thoth)
- **Redash:** https://redash.scale.com (data source 30 = GenAI Ops Snowflake)
- **Spec query:** q304995 (SPEC_GETTER) — pull every run, never hardcode
- **InfoHub sheet:** `1MOa-semWY_Z-uskBD9bwzGKrMHrHjXwERda9bv2_9QU`, tab `Evals`, sheetId 1866506083
- **Scale Bot account:** `583cf35b8b8b73054d4344e6` (scale@scale.com)
- **SA:** `deltaeval@serene-column-490216-q1.iam.gserviceaccount.com` (must be Editor on the sheet)
- **Shared Drive (SA quota workaround):** `0AM0-f1SyIzJNUk9PVA` ("Claude")
- **Gold step:** `step-TextCollection-b87a9591843f` — `output.yaml_text` is authoritative for bot attempts
- **Layers we audit:** `L0` `L1` `L10` (review_level 0 / 1 / 10 in PIPELINEV3HUMANNODES)
