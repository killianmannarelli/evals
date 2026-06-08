# Project overrides — QC Auditor fine-tuning

This file is the single place to put **project-specific guidance** for the QC Auditor. The skill itself is project-agnostic; everything project-specific lives here.

The orchestrator passes this file's path to every auditor and master sub-agent as `PROJECT_OVERRIDES_PATH`. Sub-agents read it after the spec, and treat it as **supplementary guidance that refines how to apply the spec** — never as a replacement for the spec.

**This file ships empty on purpose.** The skill works without any overrides — sub-agents handle a missing or empty file gracefully and rely on the spec alone. Edit this file (or use the editor at `http://127.0.0.1:7860/overrides` while the web UI is running) to add tuning for your project. See the README's "Customising for your project" section for the suggested structure and what each section is for.

---

## Thoth (Multi-Agent Swarm Benchmark) — `69bee012be45f06904292c9a`

When auditing the Thoth project, the optional **mechanical linter pre-pass** (`scripts/run_linter.py`, see SKILL.md Step 2.5) is available and recommended. It runs the `gold_checker_vercel` package (`~/swarmImprove/gold_checker_vercel`) and adds three columns to the CSV:

- `linter_verdict` — `PASS`, `PASS WITH MINOR`, or `FAIL` from the 12 mechanical checks
- `linter_fail_checks` — names of checks at FAIL severity (e.g., `numeric_claims`, `rubric_coverage`, `rubric_anchoring`, `gold_size_drift`)
- `linter_minor_checks` — names of checks at MINOR severity

How to read these columns alongside the V15 audit:

1. **Both flag the same task** → high-confidence reject. Linter caught a mechanical defect (e.g., wrong file count) AND auditors found at least one V15 Fail. These tasks belong at the top of the fix queue.
2. **Linter FAIL but V15 clean** → mechanical defect exists but the auditors didn't trip a Fail-band trigger. Often "imprecise but not contradictory" — e.g., gold says "12 files" actually 13, but the V15 Correctness band needs 2+ incorrect claims. Worth a manual look.
3. **V15 Fail but linter PASS** → the LLM auditors caught something the rules-based checks can't (subjective phrasing, atomicity, classification). Trust the audit; the linter is a recall device, not the verdict.
4. **Both clean** → ship-it candidate.

Auditor sub-agents do **not** read the linter output — that would couple the two passes. They make independent calls; the master can spot-check linter findings against its own confirmed findings as a coherence check, but the linter never grants new findings (the spec is the only source of truth for what counts as a violation).

---

## OpenClaw MM Rubrics / `mj_blue_shell` — `69f95a0f0992772af7907a03`

### 📋 Current canonical spec — V3 (2026-05-22)

The active QC audit rubric for this project is **V3**, with **22 dimensions** (was 11 in V1/V2). The full per-dimension map — spec UUIDs, scoring bands `{2 Fail, 3 Non-Fail, 5 Pass}`, error categories, and inline-RESPONSE evidence paths — lives in:

- [`~/.claude/skills/qc-auditor-openclaw/references/openclaw_dimensions.md`](../qc-auditor-openclaw/references/openclaw_dimensions.md) — navigation map
- [`~/.claude/skills/qc-auditor-openclaw/references/V3_spec_rubric.csv`](../qc-auditor-openclaw/references/V3_spec_rubric.csv) — raw V3 rubric (source of truth for spec UUIDs and error category strings)
- [`~/.claude/skills/qc-auditor-openclaw/references/quality_skill.md`](../qc-auditor-openclaw/references/quality_skill.md) — **the deeper authoritative quality reference** (1,380 lines, 22 sections). Consolidates the customer's MM spec, pilot-delivery review feedback, internal verifier guidelines, failure-mode taxonomy (M1–M11), difficulty levers (L1–L5 HEART, S1–S4 Safety), the customer's Taxonomy SPs (Pre-Production Advisor, Coherence Evaluator, Story-Script Trajectory Validator, Rubric Architect), the verbatim Reviewer Checklist (§21), and the customer's QC grading workflow (1–5 scale, fail/non-fail thresholds, Major/Moderate/Minor classification). When this overrides file and `quality_skill.md` disagree on a borderline call, `quality_skill.md` wins — it carries the rationale (the *why* sections) and is the customer's authoritative source.

Group structure of V3:

| Group | Sub-dims | Notes |
|---|---|---|
| 1. Prompt | 1a MM Dependence, 1b Output File(s) Name, 1c Feasibility With Tools | 1b is back (was "Coming Soon" in earlier batches; now active) |
| 2. Input Artifacts | 2a Realism, 2b Artifact Verification, 2c Tagging Accuracy, 2d Leak Prevention | 2c is back (was "Coming Soon" in earlier batches; now active) |
| 3. Verifiers | 3 Safety | V3 narrowed Verifiers to just the Safety/Harmful-Inputs check |
| 4. Silver Trajectory | 4a Category and Subcategory, 4b Cross-Modal & Cross-Service Synthesis | Subcategory misalignments are NOT flagged in 4a (only category-level mismatches) |
| 5. Trajectory | 5 Architectural Depth & Friction Exposure | MEMORY.md usage required in multi-turn tasks (03/10 rule) |
| 6. Rubric Criteria ⭐ | 6a Major, 6b Major/Moderate, 6c Major/Moderate/Minor, 6d Rubric Structure, 6e Rubric Spot Checks | Three Overall-Quality dims share denominator (= criteria the CB wrote); do not double-count criteria with multiple issues; **Missing-Criteria coverage gaps are advisory, excluded from the band — Rule 19(f)** |
| 7. Ratings | 7 Validity | Counted across all trajectories |
| 8. Tests ⭐ | 8a Correctness, 8b Underfitted, 8c Coverage, 8d Redundancy | V3 (05/04): tests covered by rubric → `Non-Fail - Incorrectly Covered by Rubric`, not Coverage Fail |
| 9. Failed Rubric/Unit Test | 9 Justification | Three justification questions per failed rubric/test |

**Earlier "Coming Soon" exemptions are retired.** Output File(s) Name (1b) and Tagging Accuracy (2c) — previously flagged Coming Soon for the 5/14 batch — are now active. The "no Coming Soon carve-outs" note further down in this file remains the canonical policy.

### ⚠️ Source-of-truth principle (2026-05-17) — read first

**Grading inputs come from exactly two places:**

1. **The spec** (freshly fetched every run from Redash query 304995 `SPEC_GETTER`; static fallback at `~/Downloads/openclaw_mm_rubrics_spec.md` only when Redash returns 0 rows). The spec defines the dimensions, the failure categories, and the score bands. **Use the spec to decide what to grade.**
2. **The contributor's inline RESPONSE** (`response.before[*]` per Rule 8) plus **files linked from it** (`code_container_attachments`, `oracle_solution_files`, the `s3Url` fields inside any step's output). **Use the inline RESPONSE to decide what the contributor actually submitted.**

**`task_metadata.*` is NOT authoritative for grading.** It is the customer's pre-attempt configuration blob (initial category assignment, customer-supplied `test_weights`, customer-staged input artifacts, platform-auto-generated `validationOutputs` and `passAtKResults` from pre-validation runs). It does **not** represent what the contributor authored, and grading against it has produced wrong verdicts on this project (see Rule 9 incident — task `69faacb4258ee33d6821fa61`). Treat the entire `task_metadata` blob as **customer-side reference data** at best. See Rule 10 for the full inventory.

Hard consequence: if the inline RESPONSE is unavailable (CDS-pointer shape) AND the dimension's evidence lives inside the contributor's authored content, mark the dimension `audit_incomplete` rather than falling back to `task_metadata`. Failing closed beats grading the wrong artifact.

The static spec (`openclaw_mm_rubrics_spec.md`) lives outside Redash because `PUBLIC.AUDITRUBRICS` has no approved rubric for this project yet. Use the parsed copy at `~/Downloads/openclaw_mm_rubrics_spec.md` as the canonical reference. **Fetch the freshest spec at the top of every audit run — never reuse `spec.md` from a prior workspace.**

### Project facts every auditor must know

- **Single-model project**: only `anthropic/claude-opus-4.6` (Model A) runs in the OpenClaw environment. There is no Model F / foil. The two verifier-chain variants per task carry positive-case and refusal-case gradings of the *same* model — do not interpret them as model A/B comparison.
- **Contributors author the rubric** (not the answers). The audit grades whether the contributor's `verifier.py` + rubric criteria pair correctly captures what the prompt asks for — not whether Model A solved the task correctly.
- **Two-tier verification**: every task ships a `verifier.py` (pytest, mechanical) AND a weighted rubric (PASS/FAIL, LLM-judged). The spec's `Tests — Coverage` dimension explicitly notes the rubric is the *other half* of the verification suite, so a missing rubric criterion is forgivable if a unit test already covers it (see the cookie-recipe example in Major Issues → Missing Criteria — Critical Requirements).
- **Desired Outcome is EXCLUDED ENTIRELY (v3, 2026-06-01).** Never read `story.desired_outcome`, never ground a requirement / coverage / gold check in it, never cite it. It is the contributor's answer key; grounding the audit in it is circular and hides over-specification. The **agent-facing prompt** (`response.before["step-PromptInput-*"].output.content`) is the sole grounding source. (See Rule 19.)
- **Read-only persona universes**: when `inline_form_data.story.assigned_universe` is a person name (e.g., `matthew_smith`, `daniel_park`, `meriton`, the 19 others), the prompt must request read-only operations only. Write/edit/modify requests are an instruction-following Fail. (Read from the inline RESPONSE per Rule 10; the customer's `task_metadata.universe_id` is initial assignment only and may disagree with what the contributor selected.)

### All spec dimensions are graded — no Coming Soon carve-outs (as of 2026-05-20)

Every dimension that appears in the freshly-fetched spec MUST be graded. There is **no** "Coming Soon" / "ignore for this batch" exception. Earlier versions of this file carried a list of dimensions to skip; that list has been retired — the customer's spec is now the single source of truth for what counts.

If the spec itself marks a dimension as "Coming Soon" in its own header / preamble, follow the spec literally — but do not invent skip-rules in the overrides. The overrides file is for refinement, not exclusion.

### Rule 14 — Try the signed CDS URL before flagging audit_incomplete (added 2026-05-23)

Snowflake queries against `PUBLIC.TASKATTEMPTS` return a `response.url::string` that is **a CloudFront-signed URL** for the private CDS bucket. The signature itself is the authentication — anyone holding the URL can fetch the JSON until the `Expires` timestamp passes. Many such URLs in our CSVs are valid for 30+ days.

**Procedure when fetcher sees a CDS-pointer response:**

1. Extract the signed URL from `response.url` (Snowflake row) OR `response.cds_url` (CSV column).
2. Try `curl -s -o <path> "<signed_url>"`. If it returns HTTP 200 and >1KB JSON, parse as inline RESPONSE.
3. Only mark the task `audit_incomplete` if (a) the URL is missing entirely, (b) `curl` returns 4xx/5xx, or (c) the JSON is unparseable.

**Failure mode this prevents** (2026-05-22): T22 of the 25-task audit was flagged `audit_incomplete` because the response shape was `cds_pointer` and the bucket was `scale-cds-private-us-west-2`. The signed URL in the CSV was valid for 60+ more days. A `curl` against it returned the full 9MB inline RESPONSE. Wasted audit slot due to a false "this is inaccessible" assumption.

The fetch script `qc-auditor-openclaw/scripts/fetch_openclaw_single.py` honors `--signed-url` flag to short-circuit straight to the signed-URL path; the batch `fetch_tasks.py` checks `response.url` automatically.

### Rule 13 — Mandatory pre-audit deterministic gates (added 2026-05-23; v3 reframed 2026-06-01 → see Rule 19)

Before any sub-agent grades the task, the orchestrator MUST run `scripts/preaudit_checks.py` (in `qc-auditor-openclaw/scripts/`). It produces a `gates_report.json` per task that:

1. **Identifies the active rubric step** (Rule 12 algorithm, executed deterministically by matching `RubricCriteriaRating.responseRatings` keys against each candidate builder's criterion IDs).
2. **Inspects `step-AgentExecution-*.trajectory`** for tool-call count, file writes, workflow execution. Emits forced FAIL findings on dims 5, 7 when trajectory shows ≤2 tool calls or 0 file writes.
3. **Counts rubric atomicity violations** quantitatively and applies the 10% / 15% / 20% thresholds on dims 6a / 6b / 6c.
4. **Cross-checks the claimed `category_subcategory` against subcategory anchor terms** in the rubric/prompt content. ZERO anchor hits → FAIL 1a / 4a.
5. **Cross-checks required-output filenames** from the **agent-facing prompt** (`step-PromptInput-*`) against active-rubric criterion titles. Any unscored required artifact → Coverage finding (must cite the prompt sentence + the spec Coverage category).
6. **Scans universe data for contributor-note leaks** (working-notes phrases like *"give me the original prompt"*, *"trying to cause an failure"*, *"≥50% threshold"*). Any hit → FAIL 9 (Overall Quality).

**v3 (2026-06-01) — superseded by Rule 19.** The deterministic pre-pass is now `scripts/fact_extractor_v3.py`, which emits **FACTS** (authoritative), **ROUTES** (work-orders), and **HINTS** (ignorable) into a `sot/<task_id>/` bundle — it does **not** emit forced judgment findings. Sub-agents treat FACTS as authoritative and may not contradict them; every JUDGMENT finding (D1–D5) is EARNED, must cite the spec + one grounding-evidence kind, and is never inherited from a gate. There is no `gate_override_justification` machinery any more. (Legacy `forced` behavior remains reachable only via the `gate_authority: forced` knob for one release.)

Run the gates batch:

```
python3 ~/.claude/skills/qc-auditor-openclaw/scripts/preaudit_checks.py \
    --task-dir <workspace>/tasks/ \
    --out-dir <workspace>/gates/
```

Each `<workspace>/gates/<task_id>.gates.json` then feeds into each sub-agent spawn as `GATES_REPORT_PATH`.

### Rule 12 — Identify the ACTIVE rubric step before grading rubric dimensions (added 2026-05-20, deterministic implementation 2026-05-23)

**Implementation (deterministic — runs as Gate 1 of Rule 13):**

```python
# Pseudocode — full impl in scripts/preaudit_checks.py gate1_active_rubric_step()
candidates = [step for step in before
              if (step matches "RubricCriteriaBuilder-*" OR "step-<13-digit-ts>-*")
              and step.output.criteria is a non-empty list]

rated_ids = set()
for step in before where step.output.responseRatings exists:
    for candidate, ratings in responseRatings.items():
        rated_ids.update(ratings.keys())

for c in candidates:
    c.match_ratio = len(c.criterion_ids & rated_ids) / max(len(c.criterion_ids), 1)

full_matches = [c for c in candidates if c.match_ratio >= 0.99]

if len(full_matches) == 1:
    active = full_matches[0]
elif len(full_matches) > 1:
    # Multiple full-matches with same IDs — use latest timestamp
    timestamped = [c for c in full_matches if c.is_timestamped]
    active = max(timestamped, key=lambda c: c.id) if timestamped else full_matches[0]
elif high_matches := [c for c in candidates if c.match_ratio >= 0.5]:
    active = max(high_matches, key=lambda c: c.match_ratio)
elif not rated_ids:
    # No rating step — fall back to latest timestamped
    timestamped = [c for c in candidates if c.is_timestamped]
    active = max(timestamped, key=lambda c: c.id) if timestamped else candidates[0]
else:
    return audit_incomplete  # no match found
```

**Critical insight learned 2026-05-23**: When two builder steps both share the same criterion IDs (e.g., a `step-RubricCriteriaBuilder-<hex>` template alongside a `step-<timestamp>-<suffix>` contributor edit), the timestamped step is ALWAYS the active one. The hex-suffixed `RubricCriteriaBuilder-*` step is the customer template — it gets superseded by contributor edits. Defaulting to the named-pattern step (because the name "looks canonical") is the exact failure mode Rule 12 was written to prevent.



OpenClaw responses commonly carry **multiple `RubricCriteriaBuilder` steps in `.before`** — early drafts, the actively-rated rubric, failure-mode-justification steps, and sometimes a customer-template stub. Grading the wrong one produces phantom Fail findings (the classic case: a deprecated draft has a criterion with no `weight` field, which jq's `.weight == null` flags as broken; the active rubric — different step ID — has the same criterion properly weighted).

**Step-ID naming convention** (what you'll see in `.before` keys):

| Pattern | What it usually is |
|---|---|
| `step-<UnixMillisecondsTimestamp>-<6char>` (e.g. `step-1772171628343-3n5s2m`) | **Active** — contributor's most recent edit. Timestamp tells you when the contributor created/saved it. |
| `step-RubricCriteriaBuilder-<8-hex>` (e.g. `step-RubricCriteriaBuilder-7ba171f3e6b7`) | **Customer template** — the initial step the customer set up when defining the task. Often superseded by the contributor's timestamped edits. May or may not still match the active rubric. |
| `step-RubricCriteriaBuilder-fa33ac18d6a7` (with single `all-passed` entry) | **Stub** — placeholder slot the contributor never filled. Ignore. |

**Procedure to identify the actively-rated rubric** (do this BEFORE grading any rubric-related dimension):

1. Look at `step-RubricCriteriaRating-*` (or `step-<ts>-<suffix>` of type `RubricCriteriaRating`) — usually paired in time with the active rubric (millisecond-adjacent timestamps). Pull `output.responseRatings.<candidate>` and list the criterion IDs it scored.
2. Compare those IDs against the criteria IDs of each `RubricCriteriaBuilder` step in `.before`. The builder whose criteria IDs **fully match** the rating step's keys is the active rubric.
3. If multiple builder steps share the same criteria IDs (overlapping versions), take the one with the **latest timestamp** in its step ID. Hash-suffix steps are older than any timestamped step.
4. **All grading for Rubric Quality (7a), Rubric Structure (7b), Rubric Spot Checks (7c), Ratings Validity (8), Coverage (9c against rubric)** must use the active rubric. Citing a deprecated step's criteria as evidence of a defect is a Rule 12 violation; the master will reject any finding whose citation path points at a non-active rubric step.

**Failure-modes step is separate.** A step typed `RubricCriteriaBuilder` whose entries have IDs like `all-passed`, or whose titles look like verifier test names (`test_h3_format`, `test_h4_format`), is the **Failed-Rubric/Unit-Test Justification** holder (Dim 10), not the main rubric. `weight` may be absent from those entries by design — they're justification holders, not weighted criteria. Do not flag missing weights on this step as a Rubric Structure defect.

**Quick sanity check before flagging null/missing weights**: If you're about to flag "criterion X has no weight", first confirm (a) the step you're reading IS the active rubric (matches the rating step's keys), and (b) the criterion's ID also appears in `step-RubricCriteriaRating-*`. If either check fails, the criterion is in a deprecated or non-grading step — drop the finding.

### Source-of-truth precedence inside the task JSON

When the task category/subcategory in the original task assignment disagrees with the L0 reviewer's selection, **the L0 selection wins** (the `Reviewer Verification - Task Category and Subcategory` field is the Source of Truth per step 2 of the audit workflow).

### Artifact-routing table (where to find each grading input)

Per the source-of-truth principle above, every grading input has a **canonical inline-RESPONSE path** (the contributor's authored content). `task_metadata.*` paths are listed only for **non-grading uses** (sanity checks, telemetry, eval-scoreboard context) — never to drive a finding.

**Canonical (inline RESPONSE — use these for grading):**

| Artifact | Inline-RESPONSE path |
|---|---|
| Agent-facing prompt (the ONLY grounding source) | `response.before["step-PromptInput-*"].output.content` (the real prompt; `inline_form_data.prompt` is often null). Fallback `step-PromptTextCollection-*.output.main_request_summary`. **NEVER `story.desired_outcome`.** |
| Agent universe / persona | `inline_form_data.story.assigned_universe` |
| Source URL / retrieval date / platform | `inline_form_data.story.source_url`, `story.retrieved_date`, `story.source_platform` |
| Input images / zips (contributor-staged) | `inline_form_data.story.source_screenshot[*]`, `story.zip_folder[*]` (each carries the `cdsUrl` / `s3Url` of the file the contributor attached) |
| Docker env definition (contributor-authored) | `inline_form_data.before["step-OpenClawEnvironment-*"].output.*` |
| `verifier.py` (contributor-authored) | `inline_form_data.contributor_verifier_py.s3Url` (top-level convenience field; full list at `inline_form_data.code_container_attachments[*]` where `name == "verifier.py"`) |
| Workspace tarballs (contributor-authored) | `inline_form_data.code_container_attachments[*]` where `name` ends in `.tar` / `.tar.gz` / `.zip` |
| Snapshots (contributor-authored) | `inline_form_data.code_container_attachments[*]` where `name` ends in `.json` (e.g., `snapshots.json`) |
| Oracle solution (contributor-authored) | `inline_form_data.oracle_solution.text` + `inline_form_data.oracle_solution.files[*]` |
| Rubric criteria (anti-overfit + failure-mode) | `inline_form_data.rubrics[*].criteria[*]` |
| Per-run model responses (contributor-rated) | `inline_form_data.per_run_responses[*]` |
| Eval scoreboard (platform's verdict — context only) | `inline_form_data.eval` |
| Contributor justifications (Failed-Rubric Justification dim) | `inline_form_data.rubrics[*].criteria[*].annotations.{correct_answer_justification_rubric, incorrect_rubric_justification, model_mistake_justification_rubric}` |

`scale-cds://…#s3/scale-cds-public-us-west-2` URLs rewrite to `https://scale-cds-public-us-west-2.s3.amazonaws.com/<workspace_id>/<file_id>` — publicly fetchable. Private CDS URLs (`…#s3/scale-cds-private-us-west-2`) are not.

**Non-authoritative (`task_metadata.*` — DO NOT use to drive a finding):**

| Field | What it actually is | Why not authoritative |
|---|---|---|
| `task_metadata.passAtKResults` | Platform's auto-grader runs vs. rubric | Tells you platform's verdict, not what contributor submitted. Read `inline_form_data.eval` for the same signal, scoped correctly. |
| `task_metadata.test_weights` | Customer-supplied weighted test list | Routinely misaligned with the contributor's actual `verifier.py` (this is what Rule 4 detects). Compare verifier.py to inline rubric coverage, not to this. |
| `task_metadata.validationOutputs.chains[*]` | Platform-auto-generated validation drafts | Rule 9 — these are NOT the contributor's submission. |
| `task_metadata.zip_url_artifacts` / `…environment_docker_file` / `…trajectories_url` / `…system_prompt` | Customer-staged or pre-attempt URLs | The contributor's references to these live in the inline RESPONSE (see canonical table above); if inline RESPONSE is missing, the dimension is `audit_incomplete`, not "fall back to metadata". |
| `task_metadata.category` / `task_metadata.subcategory` | Customer's pre-attempt category assignment | The spec says L0 reviewer's selection wins; that selection is in the L0 reviewer's RESPONSE, not `task_metadata`. Use `task_metadata.category` only as the customer's initial assignment for context, never as a grading anchor. |

If a dimension's grading input has no inline-RESPONSE path (i.e., the RESPONSE is a CDS pointer wrapper and the contributor's form blob is in private CDS), mark that dimension `audit_incomplete` per Rules 5, 9, and 10. Do not substitute `task_metadata.*`.

### Experimental tasks (no `verifier.py`)

Per step 9 of the audit workflow (NOTE 05/01): experimental tasks ship without a `verifier.py`. For those tasks, auditors must **skip the Tests dimensions** (Correctness, Underfitted Tests, Coverage, Redundancy) entirely — these are not gradable when the artifact doesn't exist. The master should emit `status: "audit_incomplete"` with `incomplete_reason: "experimental task — no verifier.py to grade Tests dimensions"` for the missing dimensions, but continue scoring the remaining dimensions normally.

### Scoring conversion (1–5 task-level score from per-dimension findings)

The spec's General Grading Instructions translate per-dimension findings into a single 1–5:

1. Any **1-2 Fail** finding on any dimension → task is Fail (1 or 2).
2. Else if any **3-4 Non-Fail** finding on any dimension → task is 3-4.
3. Else (all dimensions clean) → task is 5.
4. 1 vs 2: 1 if attempter put little/no effort.
5. 3 vs 4: judgment call on severity.

The audit CSV should retain the per-dimension finding so QMs can re-derive this if needed; the master should not collapse findings into a single score (that's QM's call).

### Recall-improvement rules (added 2026-05-16 after first L12 audit)

These rules were added after a sanity-check comparison of the qc-auditor's L12 output against a QM-graded ground-truth audit of task `69fb9655277dce0e70070e35`. The QM's verdict was FAIL on Rubric Quality and Failed-Rubric Justification; my first pass landed at Non-Fail because of three systematic gaps. Each rule below targets one of those gaps.

#### Rule 1 — Overfitting vs Tests-Redundancy collision

When a rubric criterion is both **(a) overly specific about the model's response phrasing** AND **(b) covered by a unit test on the underlying fact**, the criterion is **Overfitting** (Rubric Quality dimension), not just Tests-Redundancy.

The defect is that the criterion would reject valid model implementations: a model that produces a correct artifact (e.g., `purchase_order.json` with the right SKU) but doesn't verbally narrate "the response states that purchase_order.json contains the SKU" would fail the criterion despite producing a valid result. The unit test is satisfied; the rubric criterion is not. That gap is what the spec's Overfitting definition penalizes.

**Master rule**: when an auditor flags this pattern, do **not** reject the finding on the grounds that "duplicate test/criterion coverage belongs in Tests-Redundancy." Both framings can be true; if the criterion would reject a valid model output that satisfies the unit test, Overfitting is the load-bearing classification — keep it.

**Example trigger phrase to recognise**: a criterion that starts with *"The response states that…"* and names a specific file / variable / value that already has a deterministic unit test. The "states that" verb is the smoking gun — it overconstrains the model's surface language while the test already verifies the underlying truth.

#### Rule 2 — Mandatory prompt→rubric coverage walk

Before scoring `Rubric Criteria — Overall Rubric Quality`, every auditor must perform an explicit **prompt→rubric coverage walk**:

1. Read the **actual agent-facing prompt**: `response.before["step-PromptInput-*"].output.content` (fallback `step-PromptTextCollection-*.output.main_request_summary`). This is the ONLY grounding source for "required by the prompt." **Never** read `story.desired_outcome` (answer key → circular) or `task_metadata.passAtKResults.input.message` (customer pre-attempt blob). If the prompt step is absent, mark the dimension `audit_incomplete` — never substitute desired_outcome.
2. Enumerate each **explicit imperative** in the prompt — every "must", "should", "check", "include", "send", "create", "identify", "verify", etc. that points at a specific action or output.
3. For each enumerated imperative, search the **active rubric** criteria (the Rule-12 active step, e.g. `step-1772171628343-3n5s2m` — NOT `inline_form_data.rubrics`, which is the customer template) for a criterion that grades it. If no criterion grades it (and no unit test in the contributor's `verifier.py` — per Rule 9 — covers the same behaviour mechanically), flag a **Missing Criteria — Critical Requirements** finding citing the prompt sentence verbatim. Tag it `bucket: "missing_criteria"`, `counts_toward_band: false` — advisory, excluded from the 6a/6b/6c band per Rule 19(f).

If the RESPONSE is a CDS pointer wrapper (no inline form data accessible), the prompt is in private CDS and this walk cannot run — mark `Rubric Criteria — Overall Rubric Quality` `audit_incomplete` with reason "prompt in private CDS, prompt→rubric walk cannot run". Do not substitute the customer's pre-attempt message from `task_metadata`.

This walk is what catches issues like *"check their prices in our records"* in the Vans-pricing example: the prompt explicitly requests price identification across multiple matches, but the rubric only graded a single SKU's price — three valid Vans models (Authentic, Era, Old Skool, Sk8-Hi) were left ungraded. Without the walk, this defect is invisible to the rubric-first reading.

The walk should run *in parallel* to dimension-by-dimension scoring, not as a sub-step of any one dimension. Its output feeds the Rubric Quality dimension's Missing-Criteria-Critical bucket.

#### Rule 3 — Per-criterion self-containment isolation check

Before scoring Rubric Quality clean (or low-severity), every auditor must run a **self-containment isolation check** against each rubric criterion:

> *"If I gave a human evaluator ONLY the model's response (no access to the prompt, no other criteria, no contributor submission), could they decide PASS/FAIL on this criterion?"*

If the criterion mentions deictic references to **the generated PO number, the selected shoe model, the logic, the bug, the prior turn**, etc. — terms the evaluator would need outside material to resolve — flag a **Criteria Not Self Contained** (Major) finding per the spec's Appendix.

The fix template from the spec: change *"Criterion #8: …generated PO number…"* → *"Criterion #8: …generated PO number, which is the same as the one in purchase_order.json…"*. Auditors don't need to write the fix; they just need to flag the defect.

##### Rule 3b — Strict self-containment: sibling criteria do NOT anchor (added 2026-05-28)

**Strict rule.** A criterion is self-contained **only when its labels are anchored in the prompt, the inputs, or the model's response under evaluation** — *nothing else*. Other criteria in the same rubric, the `desired_outcome` (gold), and `task_metadata` do **not** count as anchors.

**Why strict.** A grader is meant to be able to read one criterion and check it against the artifact, not run a within-rubric scavenger hunt to figure out what a label means. If "Meal 4" appears bare in a criterion and the only place "Meal 4 = Stouffer's lasagna" is established is another criterion in the same rubric, the dependent criterion fails self-containment — the sibling does not save it.

**Trigger pattern (general).** A criterion references a short positional/numeric label of the form `<noun> <id>` — e.g. `Meal 4`, `Row 7`, `Item 3`, `Step 2`, `Photo 1`, `Order 5`, `Receipt 2`, `Line 4`, `Entry B`, `Record 12`, `Product 3` — and the descriptor for that label is **not** established in the prompt or the inputs. Flag the dependent criterion regardless of whether some sibling criterion names the descriptor.

**Severity.** This is a **Criteria Not Self Contained** finding under the spec's Appendix — same dimension as Rule 3. Default to **Major** (dim 6a) unless the spec appendix explicitly demotes the pattern (which the loaded spec doesn't enumerate today).

**Fix template.** Restate the descriptor inline in each dependent criterion. Example: *"flags ultra-processed food violation for Meal 4"* → *"flags ultra-processed food violation for Meal 4 (Stouffer's lasagna)"*. Auditors only need to flag; the contributor writes the fix.

**Detection heuristic for auditors.** Walk every criterion title. For each, extract tokens matching `\b<NounWord>\s+(?:#\s*)?(?:\d+|[A-Z]\d?)\b`. For every such token, check whether the **prompt** or the **inputs** (image filenames, attached docs, agent_objective, user instructions) establish the descriptor. If they don't, the criterion fails strict self-containment regardless of what sibling criteria say.

#### Rule 4 — `verifier.py` artifact-routing mismatch → `audit_incomplete`

**Updated 2026-05-17 (per Rule 9):** The canonical contributor-authored `verifier.py` lives at `inline_form_data.contributor_verifier_py.s3Url` (extracted by `fetch_tasks.py` from `response.before["step-TextCollection-*"].output.code_container_attachments[*]`). That is the file Rule 4's routing-mismatch check runs against. Never substitute `task_metadata.validationOutputs.chains[*].outputFileUrls["verifier.py"]` — those are platform-auto-generated drafts and routinely contain tests for an entirely different scenario than the contributor's actual submission.

**Updated 2026-05-17 (per Rule 10):** The routing-mismatch heuristic compares the contributor's `verifier.py` against the **contributor's inline rubric criteria + the prompt's enumerated imperatives** (both from the inline RESPONSE), not against `task_metadata.test_weights`. `test_weights` is a customer-supplied weighted test list that routinely disagrees with what the contributor actually submitted — using it as the comparison anchor reproduces the same trust-the-metadata bug Rule 9 fixed.

**Auditor heuristic to detect the mismatch:**

1. Enumerate test function names from the contributor's `verifier.py` (the file at `inline_form_data.contributor_verifier_py.s3Url`).
2. Build the "expected coverage set" from the inline RESPONSE: (a) the criterion titles in `inline_form_data.rubrics[*].criteria[*].title`, (b) the prompt imperatives enumerated by the Rule 2 walk.
3. Score each test against the expected coverage set: does the test (by name AND body) target a rubric criterion or a prompt imperative? Count the matches.
4. If fewer than 50% of the tests match anything in the expected coverage set, declare a routing mismatch and emit `audit_incomplete` on the Tests-* dimensions with `incomplete_reason: "contributor verifier.py targets behaviour outside the prompt+rubric coverage set — <50% test-coverage overlap"`.

**Master rule**: when an auditor reports this mismatch, the master must emit `audit_incomplete` for all four Tests-* dimensions (Correctness, Underfitted, Coverage, Redundancy) with the reason above. Do **not** let those dimensions silently pass when the artifact-routing is broken.

**If `inline_form_data.contributor_verifier_py` is null** (no `verifier.py` attached in the inline RESPONSE), emit `audit_incomplete` for all four Tests-* dimensions with `incomplete_reason: "contributor verifier.py not present in inline RESPONSE — cannot audit Tests-* against platform drafts"`. Do not fall back to chain URLs or to `task_metadata.test_weights`.

**Legacy note:** Prior to 2026-05-17 this rule (a) pointed at `task_metadata.validationOutputs.chains[*]` for the file itself and (b) used `task_metadata.test_weights` as the comparison anchor. Both leans on `task_metadata` were retired on task `69faacb4258ee33d6821fa61` after a QM-feedback investigation. Rules 9 and 10 are the source of truth.

#### Rule 5 — Failed-Rubric Justification dimension: view-first, then `audit_incomplete`

Per-criterion 3-question contributor justifications live in the private CDS submission (`response.url` → `scale-cds-private-us-west-2`). They are **not in the public task JSON** and **not in `passAtKResults.runs[*].rubric_results.criteria[*].reason`** (those are auto-grader explanations, not contributor justifications — never grade Failed-Rubric Justification against those).

**Updated 2026-05-24** — `SCALE_PROD.VIEW.CDS_CHAT_TASK_ATTEMPT_RESPONSES` resolves the CDS pointer in-Snowflake for most post-migration attempts (~6 of 7 in spot-check). The orchestrator-side `fetch_openclaw_single.py` (Rule 14a) tries the view first; if it succeeds, the unwrapped form data lands in `inline_form_data` exactly as it would for a pre-migration inline attempt.

**Master rule** — branch on `inline_form_data.shape`:

- **`shape == "inline"`** (either originally inline, OR fetched via the CDS view, OR fetched via Rule 14 signed URL): the Failed-Rubric Justification dimension is **gradable**. Read each criterion's `incorrect_rubric_justification` / `model_mistake_justification_rubric` / `correct_answer_justification_rubric` from `inline_form_data` and grade per spec. Do NOT auto-emit `audit_incomplete`.

- **`shape == "cds_pointer"` or `"unknown"`** AND the view returned NULL/array-shape AND Rule 14 signed-URL also failed: emit `audit_incomplete` for the Failed-Rubric Justification dimension. The auditor's `unmapped_dimensions` list correctly captures this; the master should promote it to `audit_incomplete` so the CSV row makes the limitation visible to the QM.

The same branching applies to Ratings Validity (dim 7) and any other dim whose evidence lives in `inline_form_data` — gradable when the form data was successfully fetched (via any of: inline-original, CDS view, signed URL), `audit_incomplete` only when all three failed.

**Updated 2026-05-28 — annotations-stripped sub-case**: when `inline_form_data.shape == "inline"` BUT every criterion in the active rubric step has `annotations` reduced to `{criteria_category, evaluation_target}` only (i.e., all 3 justification fields are `null` across the rubric), do NOT emit a Fail on dim 9. This is a form/workflow artifact (the OpenClaw atomic-split rebuild strips justification fields), not a contributor knowledge issue. Treat as `audit_incomplete` for dim 9 with a note: "annotations stripped on active step — form/workflow issue, not gradable as Fail." Auditor sub-agents should still emit this as a finding, but the master must downgrade it from Fail (score 2) to `audit_incomplete`. Only grade dim 9 as Fail when SOME criteria have justification fields filled AND they defend overly-specific/unrequested rubrics (Rule 1 cross-check).

#### Rule 18 — Process-targeting = Major (STRICT stance, 2026-05-31 project-lead directive)

**Stance:** Count **process-targeting** criteria as **Major** rubric defects that drive the 6a band and can force a Fail. A process-targeting criterion grades *how* the agent worked (the trajectory/process) rather than the output:

- `annotations.evaluation_target` is (or contains) **`trajectory`** — the authoritative signal.
- Phrasings: "**Before** composing/writing X, the trajectory …", "the agent **uses/consults/inspects/extracts** <tool/source> to …", "**after** <gerund> …".

⚠️ **v3 (2026-06-01): process-targeting is an advisory HINT, never a forced gate finding.** It surfaces in `hints.json`. A swarm may still grade it Major under the strict stance, but only as an EARNED judgment finding that cites the spec — it is never auto-forced onto the verdict. (This diverges from the customer's V6 spec, which demotes process-targeting; the strict stance stays available via the `gate_authority` knob but is off the forced path.)

**Mechanics:**
- Each process-targeting criterion = one Major finding (dim 6a), counted in the total-criteria denominator. Do not double-count a criterion that is also an atomicity defect.
- Band: (process-targeting majors ∪ other Major criteria) / total > 10% → **6a Fail**.
- **Do NOT** re-import `gate_3`'s recall-tuned moderate/minor atomicity flags into this band — those are the spot-check false positives that v2.2 (Spot-Check Rubric Pattern) clears. The strict lever is **process-targeting only**, on top of adjudicated majors.

**Deterministic pre-pass:** `gate_3b` in `preaudit_checks_v2.py` (v2.4), constant `PROCESS_TARGETING_MAJOR=True`, emits these as forced majors + a `process_targeting_strict_band_breach`. **Reversibility:** set `PROCESS_TARGETING_MAJOR=False` to restore the spec-literal grade (process-targeting = advisory). On the 2026-05-31 L0 batch this stance moves the fail rate **26% → 61%**.

#### Rule 19 — v3 source resolution, spec-cited failures, and the evidence model (2026-06-01)

**Governing rule for v3.** Supersedes the "forced gates" model (Rule 13) and removes desired_outcome from grounding (Rule 2).

**(a) Three source layers — resolve and separate before grading.** `scripts/fact_extractor_v3.py` writes a `sot/<task_id>/` bundle; grade ONLY from it:
- `agent_prompt.md` — the real agent-facing prompt (`step-PromptInput-*`). Sole grounding source for "required by the prompt."
- `inputs/` — downloaded input artifacts (images kept as files to VIEW; policy sheets, PDFs, text). Sole grounding source for factual / visual / policy golds.
- `active_rubric.md` — the Rule-12 active rubric (the criteria under audit).
- `story.desired_outcome` is NOT a layer and is never read, cited, or used.

**(b) Every FAILURE must cite the spec.** A failure is invalid unless it names the V6 spec dimension + failure category it triggers (e.g. "Rubric Criteria — Overall Rubric Quality — Major: Incorrect Criteria, >10%"). The fresh spec catalog is `sot/spec_catalog.md`. The master drops any failure lacking a spec citation (D6 spec-grounding check). **Pass@K / platform-grader signals are NEVER a basis for a finding.**

**(c) Grounding evidence — exactly one kind per failure:**
- `prompt_quote` — criterion not required by / contradicts the agent prompt (over/under-specification).
- `viewed_image` — a gold is factually wrong about the actual pixels (the verifier VIEWED the image).
- `policy_quote` — criterion violates a provided policy input (e.g. a coach guidelines sheet).
- `criterion_quote` — structural defect (atomicity §9a / §17 subjective / §9h redundancy) per the spec appendix.
A finding groundable only in desired_outcome is reframed as over-specification (not required by the prompt) or dropped.

**(d) FACTS / ROUTES / HINTS (replaces forced gates):**
- FACTS (`sot/facts.json`) — authoritative, ~zero-FP (active step, trajectory, weight-set validity, leaks, phantom filenames, platform score). A finding contradicting a FACT is rejected.
- ROUTES (`sot/routes.json`) — work-orders (vision queue, safety candidate, category candidate); no verdict, they say where to look.
- HINTS (`sot/hints.json`) — old recall-tuned heuristics (atomicity, process-targeting, prompt-walk, ratings-sanity, self-containment). IGNORABLE; a swarm adopts one only by earning it (spec + evidence).

**(e) Inverse test + `fix_plan` (v3.1, 2026-06-01).** Two additions on top of (a)-(d), motivated by the e04 audit (the v3.0 swarm reached the right verdict but missed criteria that penalize a correct response):

- **The inverse test — run on EVERY criterion.** (a)-(d) above catch over-specification ("is this criterion *required* by the prompt?"). The higher-value inverse is: **"Would a correct, prompt-following response FAIL this criterion?"** If yes, flag it (ground in a `prompt_quote` — the prompt passage or another criterion's schema a correct response satisfies while still failing this one; never `desired_outcome`) and **route by WHY it fails (appendix line-60 NOTE — prefer the most specific category): over-specific / too-rigid that rejects a subset of valid implementations → `Overfitting` (Moderate); demands the wrong artifact or field, contradicts another criterion, lists a source set that flags a prompt-provided source as hallucination, is factually wrong, or otherwise penalizes the correct response → `Incorrect Criteria` (Major).** Three sub-patterns to check by name on every criterion:
  - **Wrong-location gold** — the criterion demands content in artifact/field X, but the prompt (or another criterion's schema) puts it in Y (e.g. C25: reviewer name required in the ranking CSV when the prompt + that CSV's `C4` header put the reviewer in the review doc).
  - **Overly-narrow source list** — a negative / anti-hallucination criterion lists some valid sources but omits others the prompt provides (e.g. C33: lists the 5 media files, omits Calendar/Contacts the prompt feeds), so correct cross-source facts read as hallucination.
  - **Cross-criterion contradiction** — the criterion's required output is impossible-or-penalized under another criterion's stated schema/constraint (e.g. C25 vs C4's fixed CSV header).
  - **Polarity / sign mismatch (two outcomes — split by SCORING EFFECT, per the appendix).** Check sign-vs-valence on EVERY weighted criterion as arithmetic. **(i) Scoring inversion → Incorrect Criteria, Major:** a `−N` on good-behavior-stated-affirmatively (correct response eats the penalty) or a `+N` on a bad event (a worse response is rewarded) — implementing it makes the response worse. *(0e6 C8: −5 on "the agent grounds … and refrains from fabricating" — a correct response eats the −5. Stays Major.)* **(ii) Double Negative → Moderate:** a `−N` that penalizes the ABSENCE of a good thing ("−3: response does **not** do ABC") where the scoring still resolves correctly — just negative-absence framing instead of a `+N` reward-of-presence (appendix "Double Negative"). Separator: does a CORRECT response fail? Yes → (i) Major; no → (ii) Moderate.
- **Complement-pair §9h redundancy.** A **negative** criterion that is the logical complement of a **positive** one (e.g. a `-5` "ranks IMG_4021 above DSC_1187" ↔ a positive "DSC_1187 ranked #1") adds no independent signal → one **§9h redundancy** finding with a **REMOVE** `fix_plan` on the redundant negative; do not also flag the correct positive. (Master reconciliation §9h — `agents/master_auditor.md` Step 2.7.)
- **Every finding carries a `fix_plan` with the exact edit.** On top of the one-line `fix`, every confirmed finding must carry a structured `fix_plan` = `{action: ADD|REMOVE|MODIFY, criterion_id (null for ADD), current, proposed, weight, annotations:{criteria_category, evaluation_target}, rationale}`, where `proposed` (ADD/MODIFY) is the **EXACT** new/edited criterion text — reusing the criterion schema from `qc-auditor-openclaw/agents/auto_attempter.md`. The sub-auditors emit it; the master authors/completes it when thin (`master_auditor.md` Step 2.8). `compile_report.py` renders it as the report's "How to fix this rubric" section; it is the human-readable twin of the auto-attempter's 3-JSON bundle and shares its schema.

**(f) Coverage gaps are advisory — EXCLUDED from the 6a/6b/6c band (Ruling 2026-06-01, "Separate, advisory").** A `Missing Criteria — Critical Requirements` finding (the Rule-2 coverage walk: a required output the rubric forgot to grade) is *not* a defect in "a criterion the CB wrote," so it cannot be a numerator unit in the 6a/6b/6c percentage — the denominator is the count of criteria the CB authored, and a missing criterion is not one of them. Track it in its own bucket (`bucket: "missing_criteria"`, `counts_toward_band: false`), surface it with an `action: ADD` `fix_plan` + the report's "Missing criteria (advisory)" section, but it is **never a standalone Fail driver.** The band % counts only `counts_toward_band: true` written-criteria defects (Incorrect Criteria, atomicity §9a, §17, §9h, invalid weights, and process-targeting under the strict stance). A rubric whose only issues are sub-threshold Major findings + coverage gaps is **Non-Fail.** *(This supersedes the brandon_lewis `871` precedent, which folded a MEMORY.md coverage gap into a 6a Fail; under this ruling a critical coverage gap alone does not Fail a task.)* The band math lives in `master_auditor.md` "Verdict mapping"; `compile_openclaw_csv.py` reads `task_verdict` as authoritative (no longer "any score-2 → Fail").

**(g) The agent prompt = the LIVE conversation the model received, NOT `step-PromptInput` (Leak #5, 2026-06-01).** Ground "required by the prompt" in `response.before["step-AgentExecution-*"].output.conversationHistory` (the first `role:"user"` turn) — the actual model input. `step-PromptInput-*.output.content` is only a FALLBACK and can be **STALE**: a contributor can edit the prompt after the run is generated, so PromptInput and the live conversation diverge. `fact_extractor_v3.py` now grounds `agent_prompt.md` in the live conversation and emits a **`prompt_version_drift`** FACT (+ a ⚠️ banner in `agent_prompt.md`) when they differ. **A criterion that matches the stale PromptInput but NOT the live prompt is `Incorrect Criteria` (Major)** — it grades a section/requirement the model was never asked for and penalizes the correct output. *(Discovered on task `6a17cc59ea9a7319a6ca06d9`: C2/C5 demanded a "Label Copy and Claim Consistency" section, but the live prompt required "Competitor / Reference Comparison" — a 16.7% Major FAIL the v3.1 swarm missed while grounded in the stale PromptInput. The platform grader's own notes corroborated.)*

#### Rule 20 — Calibration guards from customer feedback + reconciliation (v3.3–v3.4, 2026-06-05)

Customer feedback ("Openclaw MM Feedback") names 13 defect buckets; 11 map onto findings the v3.1 swarm already earns. Two need a sharper line so the auditor catches the real defect without flipping to a false positive. Both are EARNED findings (spec + evidence), never forced.

**(a) Over-specification precision guard (customer #8 "Rubric Overspecification").** Over-spec is the highest-FREQUENCY defect, but the catcher must not eat the endorsed Spot-Check Pattern. Before confirming an over-spec / Overfitting finding, BOTH must hold: (i) the **agent prompt left the choice genuinely open** (multiple valid values/formats/paths — if the prompt or the input *determines* the value, it is a correctness check, not over-spec); AND (ii) it is **not** a representative spot-check of a closed, prompt-defined set (representative-row / per-unit / named-instance / schema / global-count consolidation is sanctioned — see [[Spot-Check Rubric Pattern]]). Only flag when the criterion narrows an open choice to one arbitrary option (a mandated filename, one reasoning path, one accepted phrasing). *Regression: gabriela 0eb per-item exact prices = over-spec (prompt allowed "an alternative" -> open) -> FLAG; cereal 753e per-product shelf checks over the closed set = spot-check -> EXEMPT.* The master rejects an over-spec finding that fails either guard with reason `endorsed spot-check / prompt-determined value - not over-specification`.

**(b) Input-perception gradability (customer #6 "Input Perception Rubrics", P0).** A criterion that grades the model's *interpretation of an input artifact* (image/video/doc/whiteboard) rather than the deliverable, where the grader cannot verify the perceived value, is now an EARNED finding (it was an advisory process-targeting hint pre-v3.3). Gate: (1) does grading require what the model PERCEIVED, not what it PRODUCED? (2) if yes, is the value present in the deliverable AND confirmable against the media by the vision verifier? **YES -> VALID, keep (the guard — vision-checkable perception facts are correctness criteria, D2).** NO -> flag, routed by why: `evaluation_target=trajectory` -> process-targeting (Rule 18); fact never surfaces in the deliverable -> §17 unverifiable criterion (Moderate, MODIFY to grade the output / REMOVE); grading it fails a correct deliverable -> Incorrect Criteria (Major, the D3.1 inverse test). Distinguish from Rule 19c UNVERIFIABLE-gold ("we can't tell if the gold is right") — this is "the *criterion* can't be graded by the judge regardless of the gold". Full method in `auditor.md` D3.2; master enforces the guard in Check 4b.

**(c) Band-counting — defective criteria, not root causes (0eb lesson, 2026-06-05).** The 6a/6b/6c numerator counts **distinct CRITERIA that carry a defect**, not distinct root causes. The "do not double-count" rule only prevents counting ONE criterion twice when it has two issues; it does **NOT** license folding several distinct criteria that share one underlying defect (e.g. the same over-specified price pinned in a CSV row, a MEMORY row, and a derived total) into a single count. Each defective criterion counts once. *Regression: the 0eb dispute reached Non-Fail by folding 10 over-specified criteria into "3 root over-specs" → that was wrong; honest count is 6–10/21 Moderate → 6b FAIL. Do not add a "fold repeated over-spec" rule — it under-counts.*

**(d) Full image sweep before clearing a negative/decoy criterion (v3.4, 753e lesson).** A −5 / anti-hallucination / "product X is absent" criterion is a penalize-correct Major if X appears in ANY input image — so it is cleared only after viewing EVERY image, never a spot-crop sample. The vision verifier reports `present_in:<image> | absent_all_images | unswept` per decoy; the master confirms a Major on any `present_in` and marks `unswept` decoys `audit_incomplete` (master Check 4c). *Regression: 753e penalized Krave (C27), Cocoa Krispies (C28), Fruity Pebbles (C29) as "should not list" — all three are physically on the shelves → 3 penalize-correct Majors = 10.3% → 6a Fail. A spot-crop pass missed two. The over-spec shelf-read criteria stay EXEMPT (Rule 20a) — the Fail is from the decoys, a different axis.*

#### Rule 6 — When reading `verifier.py`, read assertion bodies, not function names

Test correctness defects often live inside the assertion body, not in the test name:

- Regex bug: `re.search(r"sign.?off", text)` should be `re.search(r"sign-?off", text)` — the test name (`test_discord_message_content`) gives no hint.
- Hardcoded literal: `assert price == 75` for a Vans entry that has 4 valid SKU choices (Authentic / Era / Old Skool / Sk8-Hi) at different prices.
- Overly-wide search window: `_tokens_near(..., window=250)` accepts brand-name matches from a previous unrelated audit-log entry.

When `FETCH_ARTIFACTS=true` and the auditor fetches a `verifier.py`, they must read each weighted test's function body (the lines between `def test_X(...):` and the next `def`) — not just the function name — before scoring the Tests-Correctness or Tests-Underfitted dimension clean. Reading only names is recall-blind to assertion-body defects.

This rule is moot when the `verifier.py` is unfetchable (Rule 4 above) — but when it is fetchable, the auditor must do the body-read.

#### Rule 7 — Cross-run pass-rate is the Overfitting fingerprint

When the contributor's recorded per-run model responses show a rubric criterion failing in (say) **15/16 runs**, treat that as quantitative evidence of Overfitting on that specific criterion — even if the criterion's text reads plausibly in isolation.

**Why:** A criterion that consistently fails across diverse model runs is either (a) measuring surface phrasing the prompt doesn't actually require, (b) including hard-coded values the prompt doesn't supply, or (c) demanding output the agent can't produce from the inputs given. All three are the Overfitting / "Criteria Not Required by Prompt" failure mode. A single failure run is noise; a near-100% failure rate across runs is signal.

**How to apply (per Rule 10 — read from inline RESPONSE, not `task_metadata`):**

Compute pass-rate-per-criterion from the **inline RESPONSE's per-run data**:
- `inline_form_data.per_run_responses[*]` — each run carries the contributor's per-criterion rating for that run.
- `inline_form_data.eval.evaluations.model_a_metrics` — also surfaces per-criterion aggregate counts when present.

If `pass_rate < 0.20` AND the criterion isn't a known difficulty-anchored stretch criterion, emit `Fail - Rubric Quality - Overfitting` and cite the per-run breakdown in the justification. Conversely, criteria that pass in ≥80% of runs are calibration anchors — don't flag them for Overfitting without strong text evidence.

**Do NOT use `task_metadata.passAtKResults`** — that's the platform's pre-attempt auto-grader run, not the contributor's recorded ratings, and per Rule 10 it's customer-side reference data, not authoritative. If the inline RESPONSE doesn't carry per-run data (CDS-pointer shape), skip the cross-run signal for this task and rely on text-only Overfitting heuristics (Rule 1).

#### Rule 8 — Inline RESPONSE schema (when Snowflake has the form data)

`PUBLIC.TASKATTEMPTS.RESPONSE` has two distinct shapes on this project:

1. **CDS pointer wrapper** (47 of 52 attempts as of 2026-05-15, all post-migration):
   `{"type": "ResponseObject", "url": "scale-cds://...scale-cds-private-us-west-2"}` — `LENGTH(RESPONSE::STRING) ≈ 117` chars. Form data is unreachable without Scale customer-org auth; emit `audit_incomplete` for any dimension whose evidence lives only here.

2. **Inline VARIANT** (5 of 52, all pre-2026-05-11):
   `{"before": {...by step_id...}, "after": {...}, "completions": [...], "dataSourceResults": [...], "metrics": {...}, "turns": []}` — `LENGTH(RESPONSE::STRING)` is 3.5M–9M chars. Full contributor form data is queryable from Snowflake directly.

**Detection query (in fetch_tasks.py or auditor):**
```sql
SELECT
  CASE WHEN OBJECT_KEYS(RESPONSE) = ARRAY_CONSTRUCT('type','url')
       THEN 'cds_pointer' ELSE 'inline' END AS shape
FROM PUBLIC.TASKATTEMPTS WHERE _ID = '<attempt_id>'
```

**When inline, parse these step paths:**

| Step type | Path | Content |
|---|---|---|
| Story / agent definition | `RESPONSE:before['step-1771366239685'].output.*` | `agent_objective`, `assigned_universe`, `core_functionalities`, `desired_outcome` (⚠ v3: present in the schema but EXCLUDED — never a grounding source), `retrieved_date`, `source_platform`, `source_screenshot`, `source_url`, `target_domain`, `zip_folder` |
| Prompt | `RESPONSE:before['step-PromptTextCollection-*'].output.*` | `main_request_summary`, `safety_tier_annotation`, `tier_justification` |
| Rubric A (anti-overfit) criteria | `RESPONSE:before['step-RubricCriteriaBuilder-7ba171f3e6b7'].output.criteria[*]` | Per-criterion: `id`, `title`, `weight` (typically 3), `annotations.correct_answer_justification_rubric`, `annotations.incorrect_rubric_justification`, `annotations.model_mistake_justification_rubric` |
| Rubric B (failure-mode) criteria | `RESPONSE:before['step-RubricCriteriaBuilder-ad24316a75bb'].output.criteria[*]` | Per-criterion: `id`, `title`, `annotations.failure_1_category` (taxonomy code: `f1_scope_creep`, `f1_assumption`, `f3_privacy_leak_exposure`, `f6_misrepresentation`, etc.), `annotations.failure_1_step` |
| Rubric eval scoreboard | `RESPONSE:before['step-RubricEvaluationViewer-*'].output.evaluations.model_a_metrics.score` | `{totalScore, maxScore, percentage}` — overall task-level score |
| Per-run model responses | `RESPONSE:before['step-ResponseTextCollection-*'].output.*` | Each of the K runs' selected outputs |
| Per-run model selector | `RESPONSE:before['step-ModelResponsePreview-*'].output` / `step-ModelResponseSelector-*` | Which model variant was selected per run |
| Environment | `RESPONSE:before['step-OpenClawEnvironment-*'].output` | env_id, docker_file, snapshots |

The step IDs after the type prefix (e.g., `7ba171f3e6b7`) are stable per task batch — they're the form-builder UUIDs the project's task-template assigns. They differ across tasks but follow the same naming scheme.

**Why this matters:** When inline data is available, auditors should prefer it over fetching CDS public URLs. It carries the contributor's own justifications (the `_rubric` annotation fields) — which is what auditors need to grade Failed-Rubric Justification, Self-Containment, and Overfitting properly. Public CDS files only carry verifier.py + snapshots, which give you tests and environment state but NOT contributor reasoning.

#### Access-tier note (2026-05-16)

Exhaustive probing established the following data-access boundary for this user's Redash key + Scale API key:

- **Public REST (`api.scale.com/v1` and `/v2`)**: 403 / 404. Key scope is bound to the user's workspace, not OpenClaw's customer org (`68a7f8dc133a30ee7f7494de`). `GET /v2/projects` returns `{"projects":[]}`. No path forward without customer-admin credentials.
- **Snowflake `PUBLIC` / `PUBLIC_RAW` / `FULL` / `PUBLIC_W_DELETED` / `PUBLIC_W_DELETED_RAW`**: All carry identical CDS-pointer wrappers for post-migration attempts. `__UNTYPED` is null. No hidden Mongo blob to extract.
- **`PUBLIC_WRITABLE.MULTIMANGO_AUDIT_HISTORYV4`** (18,939 rows): zero OpenClaw entries. It's the labeling-vertical audit table — image/video/transcription projects. OpenClaw audits live on different infra (likely the customer's own dashboards).
- **Public CDS (`scale-cds-public-us-west-2`)**: fully fetchable. Carries `verifier.py`, `snapshots.json`, `system_prompt`, `environment_docker_file`, `zip_url_artifacts`, per-run `rubric_results` blob. Use for Tests-* dimension auditing.
- **Private CDS (`scale-cds-private-us-west-2`)**: requires Cognito → STS → signed-S3 chain that only the Outlier SPA has. Carries the contributor's L12 form blob + the 3-question Failed-Rubric Justification answers. Programmatically inaccessible at this access tier.
- **Snowflake `TASKATTEMPTS.TASK_FEEDBACK`**: the L0 reviewer's full grade form is inline (rating fields, review_decision, free-text feedback). This is the closest QM-ground-truth signal you can pull from Snowflake — use it to filter "QM-already-graded" vs "QM-pending" tasks during batch audits.

**Default behavior for auditor sub-agents on this project (per Rule 10):**
- If RESPONSE is inline (Rule 8 shape), use it directly. Tests-*, Rubric Quality, Justification, Safety, Prompt, Input Artifacts dimensions are all auditable from `inline_form_data.*`.
- If RESPONSE is CDS-only, mark every contributor-content-dependent dimension `audit_incomplete` (Tests-*, Rubric Quality, Failed-Rubric Justification, Ratings-Validity, Prompt, Input Artifacts, Source Documentation, Silver Trajectory). Do **not** substitute `task_metadata.*` paths — per Rule 10, those are customer-side/platform-generated reference data, not contributor submissions. Failing closed beats grading the wrong artifact.


#### Rule 9 — Contributor-submitted artifacts only; `task_metadata.validationOutputs.chains` is NOT authoritative

The contributor's submitted `verifier.py` (and other authored files) lives **inside the inline RESPONSE**, not in `task_metadata.validationOutputs.chains[*]`. The chain URLs are platform-auto-generated validation drafts that do not represent what the contributor actually submitted, and grading them in place of the canonical artifact produces wrong audit findings.

**Why:** Discovered 2026-05-17 on task `69faacb4258ee33d6821fa61` (attempt `6a0645adde4b154e0b849ade`). The 4 verifier.py URLs in `task_metadata.validationOutputs.chains[0..3]` were platform-generated alternates that all tested for write actions. The contributor's actual submitted verifier.py was a strictly-read-only test suite (every test asserted absence of artifacts/state changes) that contradicted the prompt's write instructions. Auditing the chain URLs instead of the contributor's file led to the wrong verdict ("verifier is fine") when the correct verdict was "verifier is fundamentally misaligned with the prompt".

**How to apply:**

For OpenClaw MM Rubrics audits, the canonical location for the contributor's submitted artifacts is:

- **`verifier.py`** → `RESPONSE.before["step-TextCollection-*"].output.code_container_attachments[*]` where `name == "verifier.py"`. Use the `cdsUrl` / `s3Url` field to fetch the actual file content. Confirm by `name == "verifier.py"` and `mimeType == "text/x-python-script"`.
- **`workspace.tar` / agent workspace output** → same step's `code_container_attachments` where `name` ends in `.tar` or `.zip`.
- **`oracle_solution_files`** → `RESPONSE.before["step-TextCollection-*"].output.oracle_solution_files` when present.

For tests-specialist audits specifically:

1. Walk `RESPONSE.before[*].output.code_container_attachments[*]` and pick out the entry whose `name == "verifier.py"`.
2. Fetch that file (it's at `scale-cds-public-us-west-2`, anyone-fetchable via the `s3Url` field).
3. Read assertion bodies per Rule 6.
4. Apply Rules 4 (routing-mismatch) and 6 (body-reading) against THIS file, never against `task_metadata.validationOutputs.chains[*].outputFileUrls["verifier.py"]`.

**No-fallback policy (updated 2026-05-17 per Rule 10):** If the contributor's submitted verifier.py is not present in any `code_container_attachments` slot, mark all four Tests-* dimensions `audit_incomplete` with reason "contributor verifier.py absent from inline RESPONSE — contributor-side defect (missing upload)". **Do NOT fall back to `task_metadata.validationOutputs.chains`** — those are platform-auto-generated drafts (see Rule 9's `69faacb4258ee33d6821fa61` incident) and grading them produces wrong findings.

The inline-RESPONSE parser (`extract_inline_form_data` in `scripts/fetch_tasks.py`) surfaces `code_container_attachments`, `oracle_solution`, and the convenience field `contributor_verifier_py` as top-level keys in `inline_form_data` (implemented 2026-05-17). Auditors should read these directly rather than walking `response.before` manually.

---

#### Rule 10 — Spec + inline RESPONSE only; `task_metadata` is not authoritative for grading

**The general principle behind Rule 9, applied to the entire `task_metadata` blob.** Grading inputs come from exactly two places:

1. **The spec** (defines what to grade — dimensions, failure categories, score bands).
2. **The contributor's inline RESPONSE + files linked from it** (defines what the contributor actually submitted).

`task_metadata.*` is the customer's pre-attempt configuration blob plus the platform's auto-generated validation results. It is **customer-side / platform-side reference data**, not the contributor's submission. Treating it as authoritative produces wrong audit findings.

**Why:** The chain-URLs incident (Rule 9, task `69faacb4258ee33d6821fa61` on 2026-05-17) revealed a class of failure that extends beyond `validationOutputs`:

- `task_metadata.passAtKResults` — platform-auto-generated grader runs, not contributor ratings (the contributor's ratings live in `inline_form_data.per_run_responses[*]` and `inline_form_data.rubrics[*].criteria[*].annotations.*`)
- `task_metadata.test_weights` — customer-supplied weighted test list, routinely misaligned with the contributor's actual `verifier.py` (this misalignment is what Rule 4 detects, but Rule 4 should not USE `test_weights` as the comparison anchor — see updated Rule 4)
- `task_metadata.passAtKResults.input.message` — customer's pre-attempt prompt staging; not the contributor's authored prompt (the authored prompt lives in `inline_form_data.prompt.*` + `inline_form_data.story.*`)
- `task_metadata.zip_url_artifacts` / `task_metadata.environment_docker_file` / `task_metadata.trajectories_url` / `task_metadata.system_prompt` — customer-staged input URLs; the contributor's references to these are in `inline_form_data.story.*` and `inline_form_data.before["step-OpenClawEnvironment-*"]`
- `task_metadata.category` / `task_metadata.subcategory` — customer's initial assignment; the L0 reviewer's category selection (which the spec says wins) lives in the L0 reviewer's RESPONSE, not here

**How to apply:**

For every dimension, before scoring, ask: "What evidence do I need? Is it contributor-authored?" If yes, the evidence path **must** start with `inline_form_data.*`. If the inline RESPONSE doesn't carry that evidence (CDS-pointer shape, or contributor didn't fill that field), mark the dimension `audit_incomplete` — do not substitute the equivalent `task_metadata.*` path.

The dimensions/paths whose answers came (incorrectly) from `task_metadata.*` in prior runs and now must come from inline RESPONSE:

| Dimension / use | OLD (do not use) | NEW (canonical) |
|---|---|---|
| Prompt→rubric coverage walk (Rule 2) | `task_metadata.passAtKResults.input.message` AND `story.desired_outcome` | `response.before["step-PromptInput-*"].output.content` (agent-facing prompt) |
| Verifier-routing comparison (Rule 4) | `task_metadata.test_weights` (test names) | `inline_form_data.rubrics[*].criteria[*].title` (criterion titles) + prompt imperatives from inline story |
| Cross-run pass-rate Overfitting (Rule 7) | `task_metadata.passAtKResults[*].rubric_results[*]` | `inline_form_data.per_run_responses[*]` + `inline_form_data.eval` |
| Verifier.py source (Rule 9) | `task_metadata.validationOutputs.chains[*].outputFileUrls["verifier.py"]` | `inline_form_data.contributor_verifier_py.s3Url` |
| Workspace tarballs / snapshots | `task_metadata.validationOutputs[...].outputFileUrls["workspace_*.tar.gz" / "snapshot_*.json"]` | `inline_form_data.code_container_attachments[*]` (filter by `name` suffix) |
| Input images / zips (sub-dim 1a, 2a-c) | `task_metadata.zip_url_artifacts` | `inline_form_data.story.source_screenshot[*]` + `inline_form_data.story.zip_folder[*]` (each carries its own `cdsUrl` / `s3Url`) |
| Docker env (sub-dim 1b) | `task_metadata.environment_docker_file` | `inline_form_data.before["step-OpenClawEnvironment-*"].output.*` |
| Source URL / retrieved date / platform (Source Documentation) | n/a (already inline) | `inline_form_data.story.{source_url, retrieved_date, source_platform}` |
| Universe / persona (read-only enforcement) | `task_metadata.universe_id` | `inline_form_data.story.assigned_universe` |
| Eval scoreboard for context | `task_metadata.passAtKResults.success_rate` | `inline_form_data.eval` (display-only, never grading anchor) |

**Permitted non-grading uses of `task_metadata`:**

- **Sanity checks:** compare `task_metadata.category` against `inline_form_data.story.target_domain` to detect customer/contributor disagreement (flag as a finding only if the spec says one of them is wrong).
- **Eval-scoreboard context:** mention the platform's verdict in the audit summary so QMs can see "platform PASS, audit FAIL" cases (e.g., task `e38`). The audit verdict is independent of the platform's.
- **Telemetry / filtering:** use `task_metadata.subcategory` to slice the audit batch by category in the output CSV. Never as a grading input.

**Master rule:** if a finding cites a `task_metadata.*` path as its evidence anchor, the master must reject the finding with `rejection_reason: "Rule 10 violation — finding cited task_metadata.* which is customer-side reference data, not authoritative for grading. Re-cite from inline_form_data.* or mark the dimension audit_incomplete."` Auditors that surface `task_metadata.*` evidence by accident should re-audit against the canonical inline path before the master accepts the finding.

**Spec freshness:** Every audit run must fetch the spec fresh from Redash query 304995 (`SPEC_GETTER`) or, when Redash returns 0 rows, the static fallback at `~/Downloads/openclaw_mm_rubrics_spec.md`. Never reuse a `spec.md` from a prior workspace — QMs revise the rubric continuously, and an audit against a stale spec is worse than no audit. The spec is the second non-negotiable source-of-truth alongside the inline RESPONSE.
