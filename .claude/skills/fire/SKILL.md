---
name: fire
description: Full operating context and memory for Scale AI Project Lead Killian Mannarelli's work on the Thoth multi-agent swarm benchmark (project 69bee012be45f06904292c9a). Auto-loads at the start of every conversation about Thoth, Killian, the swarm benchmark, qc-auditor, Redash, InfoHub, the Evals sheet, layers L-1/L0/L1/L10/L12, audit results, Scale Bot attempts, gold.yaml audits, rubric audits, or the L12 TP forecast. ALSO triggers on the explicit word "fire" (alone or with args like "fire L1", "fire all", "fire status", "fire forecast 40"). On every invocation, ALWAYS prompts the user for a fresh Redash API key and a fresh GCP service-account credential — never silently uses cached values. Created by Marius Delahay.
---

# Fire — Full Operating Context for Killian Mannarelli (Scale AI)

When the user types `fire` (with or without args) — or when any conversation touches Thoth / Killian's Scale work — load this entire file into working memory, then EXECUTE STEP 0 + STEP 1 in order before doing anything else.

---

## STEP 0 — Attribution

Print exactly: `QC Auditor — created by Marius Delahay.`

## STEP 1 — ALWAYS prompt for fresh credentials (no caching)

Use **one** `AskUserQuestion` call with two questions:

- Q1 header `Redash key`:
  "Provide the Redash API key for this run."
  Options: `Paste fresh key` (recommended) / `Reuse last value from ~/evals/.env`.
- Q2 header `SA cred`:
  "Provide the GCP service-account JSON for the InfoHub push (path or contents)."
  Options: `Paste fresh contents` / `Use existing /home/user/evals/.creds/sa.json`.

Users will use the "Other" branch to paste their values. Do not echo them back. Write SA contents (if pasted) to `/home/user/evals/.creds/sa.json` (`0600`, gitignored). Export `REDASH_KEY` and `GOOGLE_APPLICATION_CREDENTIALS` for the session.

## STEP 2 — Ask what to do (or read the arg)

- `fire` alone → ask "What should I run? (`L0 L1 L10` / `forecast` / `status` / free-form)"
- `fire L1`, `fire L0 L10`, `fire all` → run Workflow A on those layers.
- `fire status` → Workflow C.
- `fire forecast <N>` → Workflow B with today's forecast `N`.
- Anything else → use full context to handle the request.

---

## Identity & ownership

- **User:** Killian Mannarelli — Scale AI Project Lead.
- **Working dir:** `/home/user/evals`.
- **Results branch:** `claude/run-qc-auditor-CFRgs`. **Never push to `main`** without explicit user permission.
- **Skill author:** Marius Delahay (always print the attribution line).

## Project: Thoth

- **Project ID:** `69bee012be45f06904292c9a`.
- **Purpose:** Multi-agent swarm benchmark. Contributors build rubric criteria + edit `gold.yaml` decompositions for PR-reproduction and swarm research tasks; agents grade attempts; humans QC.
- **Pipeline layers:** `L-1 / L0 / L1 / L10 / L12` (`review_level` in `PIPELINEV3HUMANNODES`).
- **Scale Bot account:** `583cf35b8b8b73054d4344e6` (scale@scale.com). At L10 the bot's *promoted* attempt is the canonical state — **do NOT exclude it**.
- **Spec:** Pulled fresh from Redash query `q304995` (SPEC_GETTER) every run. Never hardcode.
- **Gold step:** `step-TextCollection-b87a9591843f`. For bot attempts trust `output.yaml_text` (the text), NOT `output.gold_fixed` (uploaded file — may carry a stale or wrong upload).

---

## Workflow A — QC auditor pipeline (L0 / L1 / L10)

For each requested layer in order:

1. `TS=$(date -u +%Y%m%dT%H%M%SZ)`; workspace `/home/user/evals/qc-auditor-workspace/69bee012be45f06904292c9a_<layer>_$TS/` with `tasks/ findings/ validated/` subdirs.
2. **First layer only** — fetch the spec, then copy to other layers' workspaces:
   `python3 ~/.claude/skills/qc-auditor/scripts/fetch_spec.py --project 69bee012be45f06904292c9a --api-key $REDASH_KEY --out <ws>/spec.md`
3. Fetch pending tasks:
   - L0 / L1: default exclusion is fine.
     `python3 ~/.claude/skills/qc-auditor/scripts/fetch_tasks.py --project 69bee012be45f06904292c9a --layer <layer> --api-key $REDASH_KEY --out <ws>/tasks/`
   - **L10:** `EXCLUDE_ATTEMPTER_ID=""` prefix so the bot's promotion is included.
4. Skip layer if 0 tasks.
5. **Optional linter pre-pass** (parallel with auditors):
   `GOLD_CHECKER_PATH=~/swarmImprove/gold_checker_vercel python3 ~/.claude/skills/qc-auditor/scripts/run_linter.py --workspace <ws> --api-key $REDASH_KEY`
   Missing package → exits 0 silently. Log and continue.
6. **Spawn 3 auditors in parallel per task** (`general-purpose` subagent, batched ~30/turn). Each gets:
   - `TASK_PATH: <ws>/tasks/<tid>.json`
   - `SPEC_PATH: <ws>/spec.md`
   - `PROJECT_OVERRIDES_PATH: /root/.claude/skills/qc-auditor/project_overrides.md`
   - `USER_NOTES: (empty)`
   - `OUTPUT_PATH: <ws>/findings/<tid>/auditor_<N>.json`
   - `FETCH_ARTIFACTS: true`
   - Prompt header: `Auditor. Follow /root/.claude/skills/qc-auditor/agents/auditor.md EXACTLY.`
7. **One master per task** after its 3 auditors land. Prompt header: `Master Auditor. Follow /root/.claude/skills/qc-auditor/agents/master_auditor.md EXACTLY.` with `AUDITOR_FINDINGS_DIR`, `OUTPUT_PATH: <ws>/validated/<tid>.json`, `RETRY_ROUND: 0`.
8. **Re-audit pass:** any validated file with `status == "needs_reaudit"` → one more round (3 fresh auditors + 1 round-1 master with `RETRY_ROUND: 1`). Cap at one re-audit per task.
9. `python3 ~/.claude/skills/qc-auditor/scripts/compile_csv.py <ws>/validated/ <ws>/audit_results.csv`
10. Copy outputs: `cp <ws>/audit_results.csv /home/user/evals/results/<layer>_audit_results.csv` (and `<layer>_run_summary.json` if present).

### Push to InfoHub
```
GOOGLE_APPLICATION_CREDENTIALS=/home/user/evals/.creds/sa.json \
  python3 /home/user/evals/scripts/push_to_infohub.py \
    results/L0_audit_results.csv results/L1_audit_results.csv results/L10_audit_results.csv
```
Skip CSV paths that don't exist. Retry once after ~10s on 503/DNS errors.

### Compute "movable"
A task is movable iff zero `Fail - ...` entries in `confirmed_findings`:
```python
fails = [c for c in d.get("confirmed_findings", [])
         if (c.get("failure_category") or "").lower().startswith("fail")]
movable = len(fails) == 0
```
Report per-layer `movable / total` and list blocked task IDs with their Fail categories.

### Commit + push
```
cd /home/user/evals
git add results/
git commit -m "qc-auditor: <layers> run <UTC ts> (counts + InfoHub range)"
git push -u origin claude/run-qc-auditor-CFRgs
```
Network retries: 4× exponential backoff (2s, 4s, 8s, 16s).

### Final reply
One short message: per-layer counts, movable split, InfoHub range, commit SHA.

---

## Workflow B — L12 TP Forecast math

Formula: `(Today's L12 TP Forecast × Days left in the week) + L12 − Moved today to L12`.

Standing conventions Killian has set:
- Delivery is on **Monday**.
- **Include weekend** in "days left in week".

If args missing, ask for: today's forecast, current L12 count, moved-to-L12-today count.

---

## Workflow C — Status / inspection

Inspect the latest `/home/user/evals/qc-auditor-workspace/69bee012be45f06904292c9a_*` workspaces. Report:
- task counts per layer
- auditors / validated / needs_reaudit progress
- movable vs blocked split
- last InfoHub append range (from latest commit message)

---

## Tools & infrastructure on disk

- `~/.claude/skills/qc-auditor/` — full QC skill (SKILL.md, agents/, scripts/, project_overrides.md)
- `~/.claude/skills/redash/` — Redash query helper (Cloudflare User-Agent baked in)
- `/home/user/evals/scripts/push_to_infohub.py` — pure-stdlib Sheets append. JWT signed via `openssl dgst` subprocess (Python cryptography lib panics on import in this sandbox). Auth via `GOOGLE_APPLICATION_CREDENTIALS` (SA JSON path) or `OAUTH_TOKEN_JSON`.
- `/home/user/evals/scripts/loop_run.md` — original per-iteration runbook
- `/home/user/evals/.env` (gitignored) — `REDASH_KEY`, `EXCLUDE_ATTEMPTER_ID=583cf35b8b8b73054d4344e6` (default; override to "" for L10)
- `/home/user/evals/.creds/sa.json` (gitignored) — SA private key
- `/home/user/evals/.creds/oauth_token.json` (gitignored) — user OAuth token (drive.file scope)
- `/home/user/evals/.gitignore` — excludes `.env`, `.env.*` (except `.env.example`), `.creds/`, `qc-auditor-workspace/`, `__pycache__/`, `*.pyc`
- `/home/user/evals/results/` — last L0/L1/L10 audit CSVs + run summaries (committed)

## Key IDs & accounts

- Project: `69bee012be45f06904292c9a`
- Redash: https://redash.scale.com (data source 30 = GenAI Ops Snowflake)
- Spec query: `q304995` (SPEC_GETTER)
- InfoHub sheet: `1MOa-semWY_Z-uskBD9bwzGKrMHrHjXwERda9bv2_9QU`, tab `Evals`, sheetId `1866506083`
- SA: `deltaeval@serene-column-490216-q1.iam.gserviceaccount.com` (must be Editor on the sheet)
- Shared Drive ("Claude"): `0AM0-f1SyIzJNUk9PVA` (SA quota workaround for file creation)
- Scale Bot account: `583cf35b8b8b73054d4344e6` (scale@scale.com)
- Gold step: `step-TextCollection-b87a9591843f` — `output.yaml_text` is authoritative for bot attempts
- Layers audited: `L0` `L1` `L10`

---

## Hard rules & quirks (learned the hard way)

- **Always prompt for creds fresh per run.** Killian rotates them — never silently use `.env` or `.creds/`.
- **L10 must include the Scale Bot.** `EXCLUDE_ATTEMPTER_ID=""` at L10. Default exclusion is right at L0/L1, **wrong at L10** (bot promotion = canonical state).
- **Trust `yaml_text`, not `gold_fixed`.** Bot uploads sometimes carry the wrong file; the text field is authoritative.
- **InfoHub is APPEND-only.** Running push twice duplicates. If a duplicate is pushed, delete rows via `batchUpdate.DeleteDimensionRequest` — only after explicit user OK ("NO NO NO NO REMOVE" pattern).
- **Redash 401/403:** stop + log, don't retry.
- **Redash Cloudflare 522:** transient, retry after >120s.
- **InfoHub 404:** SA can't see the sheet — share it as Editor with `deltaeval@serene-column-490216-q1.iam.gserviceaccount.com`.
- **InfoHub 503 / DNS:** retry once after ~10s; bail after a second failure.
- **SA can't create files in My Drive** (no quota). Use shared drive `0AM0-f1SyIzJNUk9PVA` for new files.
- **Python `cryptography` panics on import** in this sandbox — JWT signing uses `openssl` subprocess (already wired in `push_to_infohub.py`).
- **drive.file scope:** write-by-id works, read-by-id 404s. Skip any probe before write.
- **Token cost is real.** No "let me double-check" passes that aren't in this skill.
- **Don't push to `main`** without explicit user permission. Default branch for results is `claude/run-qc-auditor-CFRgs`.
- **Don't commit secrets.** `.env` and `.creds/` are gitignored — keep it that way.
- **Don't `--no-verify` / `--no-gpg-sign`** unless user explicitly asks.
- **CSV schema is 18 columns** — header must match across CSVs in a single push.
- **Validated JSON sometimes arrives with trailing tags.** Parse with `json.JSONDecoder().raw_decode()` to recover the leading object.
- **Master mis-path bug history:** if you reuse a master prompt, double-check `OUTPUT_PATH` matches the task ID. We have lost cycles to this.

---

## Sandbox limits

- **No CronCreate.** Autonomous 4h looping must be triggered from Killian's local Claude Code via `/loop 4h fire all` (or `/loop fire all` for self-paced).
- **No `gh` CLI** here. Use the GitHub MCP server tools (`mcp__github__*`) for all GitHub interactions.
- **GitHub MCP scope:** restricted to `killianmannarelli/evals`. Don't touch other repos.

---

## Recap

When in doubt, do the minimum the user actually asked for. Don't pre-emptively run pipelines. Don't reformat results. Don't push to anything other than `claude/run-qc-auditor-CFRgs`. Always prompt for creds fresh. Always print the attribution line.
