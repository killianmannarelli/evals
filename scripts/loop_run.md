# Loop run: Thoth QC auditor — L0 / L1 / L10 → InfoHub

Per-iteration runbook invoked by `/loop 4h` for the Thoth project (`69bee012be45f06904292c9a`).
Designed to be **fully autonomous** — never asks the user a question.

## 1. Setup

- Working dir: `/home/user/evals`
- Print attribution: `QC Auditor — created by Marius Delahay.`
- Load env: `set -a && . /home/user/evals/.env && set +a`
  - `REDASH_KEY` — for spec + tasks fetcher
- Creds:
  - `GOOGLE_APPLICATION_CREDENTIALS=/home/user/evals/.creds/sa.json` — InfoHub push
- Project ID: `69bee012be45f06904292c9a`
- Layers: `L0 L1 L10` — skip any layer with 0 pending tasks
- Spec: fresh from Redash SPEC_GETTER (q304995) every run
- Artifacts: `FETCH_ARTIFACTS=true`

## 2. Per-layer pipeline

For each layer in `L0 L1 L10`:

1. `TS=$(date -u +%Y%m%dT%H%M%SZ)` and create workspace at
   `/home/user/evals/qc-auditor-workspace/69bee012be45f06904292c9a_<layer>_$TS/`
2. Run `~/.claude/skills/qc-auditor/scripts/fetch_spec.py --project 69bee012be45f06904292c9a --api-key $REDASH_KEY --out <workspace>/spec.md`
   (only on the first layer; copy the resulting `spec.md` to the other layers' workspaces)
3. Run `~/.claude/skills/qc-auditor/scripts/fetch_tasks.py --project 69bee012be45f06904292c9a --layer <layer> --api-key $REDASH_KEY --out <workspace>/tasks/`
4. If task count is 0, skip to next layer.
5. **Linter pre-pass** (Thoth-specific; runs in parallel with step 6):
   `GOLD_CHECKER_PATH=~/swarmImprove/gold_checker_vercel python3 ~/.claude/skills/qc-auditor/scripts/run_linter.py --workspace <workspace> --api-key $REDASH_KEY`
   If the package isn't present, the script exits 0 silently and the linter columns in the CSV stay empty — log it and continue.
6. For every task, spawn 3 auditor sub-agents in parallel (`general-purpose`), batching ~30 per turn. Each sub-agent reads `~/.claude/skills/qc-auditor/agents/auditor.md` and gets `TASK_PATH / SPEC_PATH / PROJECT_OVERRIDES_PATH / USER_NOTES (empty) / OUTPUT_PATH=findings/<tid>/auditor_<N>.json / FETCH_ARTIFACTS=true`.
7. After all auditors finish, spawn one master per task using `~/.claude/skills/qc-auditor/agents/master_auditor.md` with `RETRY_ROUND=0`.
8. For every task whose validated file has `status == "needs_reaudit"`, run a single re-audit round (3 fresh auditors → 1 round-1 master). Cap at one re-audit per task.
9. `~/.claude/skills/qc-auditor/scripts/compile_csv.py <workspace>/validated/ <workspace>/audit_results.csv`
   (compile_csv joins the linter outputs into the CSV when `<workspace>/linter/` exists)
10. Copy `audit_results.csv` and `run_summary.json` to `/home/user/evals/results/<layer>_audit_results.csv` and `<layer>_run_summary.json` (overwrite per layer).

## 3. Push to InfoHub

After all non-empty layers are done:

- `GOOGLE_APPLICATION_CREDENTIALS=/home/user/evals/.creds/sa.json python3 /home/user/evals/scripts/push_to_infohub.py results/L0_audit_results.csv results/L1_audit_results.csv results/L10_audit_results.csv`
  (skip any path that doesn't exist for layers with 0 tasks)
- The script appends to the Evals tab and prints the updated range.

## 4. Git commit

- `git add results/` and commit with a message including the UTC timestamp + per-layer task counts + the appended sheet range. Then `git push origin claude/run-qc-auditor-CFRgs`.
- If the push fails for network reasons, retry with exponential backoff (2s, 4s, 8s, 16s).

## 5. Constraints

- **Never ask the user a question.** If something is missing, log it and continue / abort the iteration; do not block waiting on input.
- Don't rerun a layer if it returned 0 tasks — that's the normal "queue empty" state.
- If Redash returns 401/403, stop the iteration and log; don't retry indefinitely.
- If the InfoHub push 404s, stop the iteration and log; don't retry.
- Don't commit secrets. `.env` and `.creds/` are gitignored.
- Token-wise this is an expensive run; do not add extra "let me double-check" passes that aren't in this spec.
