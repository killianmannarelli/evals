# Review agents: static analysis + neutral FP verification

Two review-agent roles, both writing the same finding schema. Stage 2 runs the **static** agent per
task; stage 3 runs a single **neutral verifier** (one per task) that adjudicates all of that task's
findings from the claims alone. Each role is an LLM agent (a subagent / parallel worker) given the
inputs noted below and the prompt for that role. **There is no trajectory/runtime agent** — this
pipeline never sees model rollouts.

**Finding schema** (every agent emits a list of these):
```json
{"tier": "action_required | review_recommended", "defect_type": "<TAXONOMY>", "rubric_ids": [3],
 "test_names": ["test_appendix_word_count"], "explanation": "2–4 sentences, cite files/rubrics/tests", "fix": "..."}
```

**Defect taxonomy** (exact tokens — the report parser depends on them):
`MEDIA_PATH`, `GRADER_BROKEN`, `SKILL_LOADOUT`, `ORACLE_LEAK`, `RUBRIC_OVERSPEC`,
`RUBRIC_AMBIGUOUS`, `RUBRIC_UNFAIR`, `RUBRIC_CONTRADICTION`, `SP_UNCLEAR`, `CONTAINER_ENV`,
`MULTIMODAL_ARTIFACT`, `DATA_SPARSE`.

**Two tiers — rate each finding by how critical it is and how sure you are:**
- **action_required** — a defect you are *highly confident* is real and that makes the task's score
  untrustworthy until fixed: a required service/tool/media path missing from the environment
  (`CONTAINER_ENV`/`MEDIA_PATH`/`SKILL_LOADOUT`), a test that can never pass as written or
  missing/malformed test weights or a judge-vs-test contradiction (`GRADER_BROKEN`; a grader/judge
  *crash* is infra, not a defect — exclude it), a visible reference answer reachable by the agent
  (`ORACLE_LEAK`), or a rubric that contradicts the prompt/data or another rubric
  (`RUBRIC_CONTRADICTION`). Reserve this tier for issues you would stake the report's credibility on.
- **review_recommended** — a likely issue you have good but not certain confidence in, or one that
  distorts the score without breaking the eval: hidden format requirements, ambiguous IDs/dates,
  prompt/rubric mismatch, sparse data (`DATA_SPARSE`), over-specified/tautological tests
  (`RUBRIC_OVERSPEC`), brittle wording, a trivially-loose criterion (`RUBRIC_UNFAIR`).
- **Drop anything weaker.** If you are not confident a finding is real, omit it — a missed issue is
  cheaper than a false one.

## Dispatch

**Run every reviewer subagent on Claude Sonnet — required.** Both roles (static, verifier) must run
on Claude Sonnet: pass the Sonnet model id on each subagent call. These checks are read-heavy and
the prompts and tiering here are calibrated for Sonnet, so it is the required model for the
reviewers — do not substitute a different model. Keep only the orchestrator on your strongest model.
(The wave batching below is mechanics you can adapt to your agent runner; the Sonnet requirement is
not.)

**Never fire all tasks at once — always batch into waves.** Spawning one agent per task in a single
shot overloads the API (rate limits, dropped calls) and floods the orchestrator context with
returns. Run in **waves of ~15** parallel agents instead:

- Launch the agents of a wave as parallel calls, then **wait for the entire wave to return before
  launching the next**. After each wave, check which output files were written, note any
  missing/failed indices, and **retry them in a final wave** at the end. Do not start wave N+1 while
  wave N is in flight.
- For **large task sets (>100 tasks)**, shard the work across multiple background runs (round-robin
  task indices into a handful of shards); each shard runs its own wave loop over its subset and
  writes a `*_done.json` marker. Poll for all markers, then advance to the report stage. Note that
  in many runners a spawned agent cannot itself spawn further agents, so the top-level driver must
  fan out the shards.
- Write each role's prompt to `<OUTPUT_DIR>/<role>_prompt_template.txt` with a `<TASK>` placeholder,
  and substitute the task name per task.

---

## Static agent (data / rubric / harness defects)

Receives: `<OUTPUT_DIR>/batch_NNN.json` (prompt, rubrics, tests, `task_dir`, `has_pytest_tests`) and
the eval guide.

> Read the eval guide at `<SKILL_DIR>/references/agentic_quality_eval_guide.md` (the orchestrator
> substitutes the skill's absolute path), then `<OUTPUT_DIR>/batch_NNN.json`. You are auditing
> **eval-design quality** for `<TASK>` from the task files alone — what a careful reader flags
> before any model runs.
>
> **Explore** `ls -R {task_dir}`. Only the `environment/` tree is what the agent sees at runtime.
> Check the task's runtime files directory for images/PDFs/spreadsheets (often nested). **Read to
> verify, don't guess:** mock-API data/schema files in full, CSV rows backing rubric claims, any
> skill/tool definition files, message/notes fixtures, task config, the environment/container
> definition, and **view referenced images/PDFs** to check visual claims.
>
> **Visual claims are error-prone** — when a finding depends on reading an image/PDF/chart
> (counting objects/people, colors, positions, text-in-image), view the file directly, count
> carefully, and mark the finding as **lower-confidence** in its explanation (your VLM read can be
> wrong). Don't assert "the image shows N" as fact; phrase it as your reading so the verifier knows
> to re-check it.
>
> Evaluate the guide's dimensions and emit findings (schema above) for: inaccurate rubrics (claim
> vs data) → `RUBRIC_*`; sign errors and tautological/contradictory/over-specified tests →
> `RUBRIC_OVERSPEC` / `RUBRIC_CONTRADICTION` / `GRADER_BROKEN`; unclear prompt → `SP_UNCLEAR`;
> coverage gaps; missing input data → `DATA_SPARSE` / `MEDIA_PATH`; missing tools/env →
> `CONTAINER_ENV` / `SKILL_LOADOUT`; not self-contained. Also flag **weak design** that a model
> passes for the wrong reason: a trivially-satisfiable criterion that any output meets →
> `RUBRIC_UNFAIR`; the reference answer reachable in the prompt/data/tools → `ORACLE_LEAK`. If the
> task has no pytest tests, set `test_names: []` and evaluate coverage on rubrics alone.
>
> Also return the dimension scores used internally: `prompt_clarity` (1–5), `criteria_completeness`
> (1–5), `input_adequacy` (1–5), `environment_adequacy` (1–5), `is_self_contained` (yes/no),
> `missing_data`, `missing_tools`. (These are not rendered in the shared report.)

### Optional: single-trace runtime scan (low-power, best-effort)

Each bundle ships **one** sample trajectory (`conversation_history/*.json`, extracted by
`prepare_inputs.py` to `sample_traces` in the batch JSON). It is a single rollout, not the K
runs, so it cannot do cross-K reasoning — treat it as a cheap bonus net, not a real trajectory
check. If `sample_traces` is present, one lightweight pass may scan that trace for **blatant**
runtime defects only: an HTTP 500 / stack trace from a mock API (`TOOL_FAILURE`/`CONTAINER_ENV`),
the reference answer visible in a tool output (`ORACLE_LEAK`), or a clear judge-vs-test
contradiction on that trace (`GRADER_BROKEN`). Emit findings in the same schema; skip if nothing is
obvious. These findings merge with the static findings and go through the same verifier below (which
may open the trace to confirm). Do not flag model behavior, and do not infer anything from a single
sample beyond what is plainly visible.

---

## Stage 3 — Objective FP verification

Take each task's static findings and **first** apply the deterministic filter, **then** run one
objective verifier per task.

**Deterministic sign-aware filter** (no LLM): drop any finding whose **all** flagged `rubric_ids`
are negative-point (penalty) rubrics AND the criterion penalizes behavior the prompt does not
request — a correctly-signed penalty guard is not a defect. (With no rollouts there are no pass
rates to consult; rely on the sign + criterion intent.)

**Objectivity is the whole point.** The static findings are LLM-written hypotheses; a verifier that
sees the candidate's own reasoning, tier, or confidence anchors on it and rubber-stamps false
positives — the dominant failure mode is confirming "missing data" claims that are really present.
So the verifier runs **blind to all prior judgment**:
- Hand it only the **claims** — `defect_type`, `rubric_ids`, `test_names`, and the plain
  `explanation`. **Strip the prior `tier`, any confidence wording, and which reviewer wrote it.**
- Frame every claim as an unproven hypothesis from an unknown source that may well be wrong. It must
  seek evidence **both for and against** each one and reach its own verdict from primary evidence —
  never lean toward confirming.
- It assigns the tier itself, from its own evidence — there is no tier to inherit.

**Objective verifier agent** — one per task, adjudicating all of that task's merged claims together
(they share files, so one pass saves compute). Receives the stripped claims + the task's files:

> You are an independent, objective reviewer of one eval task, `<TASK>`. Below are N claims that the
> task has eval-design defects, written by unknown reviewers — each is an **unproven hypothesis that
> may well be wrong**. For EACH claim, decide from primary evidence whether it is TRUE: actively
> look for evidence **both for AND against** it, and do **not** assume any claim is correct or
> incorrect — reach your own verdict. You are one LLM/VLM reviewer too, so re-derive everything
> yourself rather than trust a claim's wording. Keep a finding **only** if concrete evidence in the
> actual task files supports it; when evidence is ambiguous, **drop it** (we want high precision,
> not high recall).
>
> Explore the task's files/images once, then adjudicate every claim with these principles:
> - **Visual claims get extra scrutiny — view the image yourself.** Any finding that hinges on
>   reading an image/PDF/chart/slide (counts, colors, positions, text-in-image) may be wrong because
>   a *reviewer* hit a capability gap, not because the rubric is broken. Example: a claim "rubric
>   assumes 6 people but the image shows 5" can just as easily mean the auditor miscounted as that
>   the rubric is wrong — the rubric's claim and the auditor's claim are **both** hypotheses. Open
>   the actual file and re-count/re-read carefully. Beware your own capability gap too; **drop the
>   claim when still ambiguous.**
> - **Confirm true absence before keeping a "missing data" claim.** The single most common false
>   positive is "a graded fact appears nowhere" when it is actually present. Before keeping
>   `DATA_SPARSE` / `MEDIA_PATH` / a missing-oracle `GRADER_BROKEN`: open the source in its **native
>   format** — view images, OCR receipts, parse spreadsheets/PDFs properly (inline-string sheets and
>   image-only PDFs defeat naive text/grep extraction) — and check the fact is actually **provided
>   to the agent by the `environment/` tree**. If the fact is present and reachable, drop it. Only
>   confirm when the data is genuinely absent, or genuinely unreadable by the agent as configured.
> - **A broken test is the test's fault** — but a **grader/judge crash** (grading harness erroring,
>   judge timeout, test-runner setup failure) is infra, not a task-data defect — REFUTE any
>   `GRADER_BROKEN` claim that is really a crash. Only confirm `GRADER_BROKEN` for a test that can
>   never pass as written, missing weights/per-test records, or a judge-vs-test contradiction.
> - **A rubric being easy to pass is not evidence it is good, and being hard is not evidence it is
>   broken.** For `ORACLE_LEAK` / weak-rubric flags, verify the criterion actually discriminates
>   good answers from bad; for a "too hard / unsolvable" flag, confirm from the files that the
>   rubric/test/environment is actually broken, not merely demanding.
> - Merge duplicates: when two claims describe the same issue, keep one verdict citing both.
>
> Claims: `[{defect_type, rubric_ids, test_names, explanation}, ...]`. Write one verdict per claim:
> `[{claim_idx, verdict: CONFIRMED|REFUTED|UNCERTAIN, tier: action_required|review_recommended,
> confidence, reasoning, key_evidence}, ...]`, each citing the exact files/images/rubrics you
> checked. Set `tier` only on CONFIRMED claims, from your own evidence: `action_required` for a
> critical defect you are highly confident in, `review_recommended` when reasonably but not fully
> sure.
>
> Then, from the surviving (CONFIRMED + downgraded-UNCERTAIN) findings, emit a **task-level
> decision** the CSV output consumes:
> `{"verdict": "pass|non-fail|fail", "confidence": <0-100>, "summary": "<one line>",
> "flagged_dimensions": [...], "audit_md": "<2-6 line markdown summary a human can validate in 15s>"}`.
> - `verdict`: **fail** if any surviving finding is `action_required`; **non-fail** if only
>   `review_recommended` survive; **pass** if none survive. **Both `fail` and `non-fail` are meant
>   to be human-validated** — only `pass` is deliver-blindly.
> - `confidence` (0–100): how confident you are the task is **deliverable / clean** — high (deliver
>   blindly) when you found nothing real, low when a blocking defect is well-evidenced. This is the
>   column the team sorts on to triage.
> - `summary`: a single-line headline of the worst issue (or "No defects found") for at-a-glance
>   scanning in the sheet.
> - `flagged_dimensions`: the eval-guide dimensions implicated (`prompt_clarity`, `rubric_accuracy`,
>   `test_correctness`, `coverage_and_balance`, `input_adequacy`, `environment_adequacy`).
> - `audit_md`: a terse, plain-language summary of what's wrong and why — written so a human can
>   quickly agree or disagree.

Disposition (per claim): keep `CONFIRMED` at the verifier's own tier; **drop `REFUTED`** (false
positive); downgrade `UNCERTAIN` to `review_recommended`. Record the verdicts so the methodology can
report "N confirmed, M removed".

The surviving findings + the task-level decision (`verdict`, `confidence`, `flagged_dimensions`,
`audit_md`) feed the report in [report.md](report.md). If the verifier omits any decision field, the
CSV renderer derives it deterministically from the findings (fail/non-fail/pass by tier, a fallback
confidence, and a findings-based audit) — but the verifier's own `confidence` and `audit_md` are far
more useful for human triage, so emit them.
