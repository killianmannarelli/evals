# Calibration rulings (apply in every audit)

The condensed rules. Full detail in `project_overrides.md` + `auditor.md` + `master_auditor.md`.
**Authoritative spec = V9 ("Add missing notes").** Full dimension map + thresholds + our scope of each dimension:
`references/spec_v9.md` (raw form: `references/spec_v9_rubric.csv`). The per-run `sot/<tid>/spec_catalog.md` is the
same V9 spec pulled fresh from Redash 304995. The bands below ARE V9 dims 11/12/13 verbatim.
**Rubric-quality issue taxonomy = `references/rubric_quality_appendix.csv` (Appendix 1).** Classify every finding
by it, then bucket: **MAJOR** = Missing-Criteria-Critical · Criteria-Not-Self-Contained · Not-Atomic-Major (fuses
*unrelated* constraints) · Incorrect-Criteria. **MODERATE** = Missing-Criteria-Non-critical · Overlapping/Redundant ·
Overfitting/Underfitting · Subjective · Incorrect-Weights-Major (off by 2 levels) · Not-Atomic-Minor (partially-related) ·
Double-Negative (a negative criterion penalizing an *absence* instead of rewarding the equivalent presence). **MINOR**
= Incorrect-Weights-Minor (off by 1 level) · Miscategorized-Criteria. Weights encode **difficulty** (tool/source
coordination, reasoning depth, modality, discovery effort) — NOT importance; a schema-check criterion is atomicity-exempt.

## Verdict bands (the only thing that sets Pass/Non-Fail/Fail)
Denominator = CB-authored criteria. Count **distinct defective criteria** (never double-count one criterion
that has two issues — take its max severity).
- **6a Fail** if Major > 10%
- **6b Fail** if Major+Moderate > 15%
- **6c Fail** if any-severity > 20%
- Below all three with ≥1 defect = **Non-Fail**; zero defects = **Pass**.

## What is gradeable (in-scope defect types)
- **Penalize-correct / factually-wrong gold** — the criterion rewards a wrong value or penalizes a correct one
  (verify against the prompt + pixels). Major. **Includes: a criterion that rewards/requires a value the prompt
  explicitly says to LEAVE UNCHANGED / not recompute / keep as-is, or that otherwise contradicts an explicit prompt
  constraint ("don't X", "only Y", "keep Z").** (d43 miss: 6/23 criteria reward *recalculated* unmatched-purchase
  totals although the prompt says unmatched purchases stay "unchanged" → 6/23 = 26% → 6a Fail. A correct, rule-
  following response is marked wrong, and it contradicts the task's own desired-outcome.) Major Incorrect-Criteria.
- **Over-specification / Overfitting** — demands content / method / exact values / filenames / schemas / sections the
  **live prompt** never asks for (Major if material, else Moderate). **Also Overfitting (Moderate): a criterion that
  hard-codes ONE side of a genuinely AMBIGUOUS call** — where the prompt or the supplied rules admit two-or-more
  defensible readings — and so rejects the rule-faithful answer the model can legitimately ship. (6871 miss: 8/21
  criteria pin one reading of ambiguous flag semantics / Film-Room scoring → 8/21 = 38% → 6b Fail. Don't confuse with
  atomicity — the defect is forcing one interpretation, not bundling.)
- **§9a Not-Atomic** — ONE criterion fuses **distinct** concerns/columns. Moderate (Major if it fuses many
  unrelated assertions).
- **Sign-inversion / invalid weight** — a weight outside {−5,−3,−1,+1,+3,+5}; or a negative weight on a *good*
  behavior (a correct response eats the penalty). Major.
- **Weight miscalibration (run this actively, not just the in-set check)** — each weight must reflect the
  **difficulty** of what it tests (tool/source coordination · reasoning depth · modality · discovery effort), NOT
  importance. Score the intended difficulty (1/3/5 or −1/−3/−5) and compare: off by **1 level → Minor**, off by
  **2 levels → Major** (Appendix "Incorrect Weights"). (5dff: a +5-difficulty cross-modal check weighted +1, and a
  +1-difficulty literal-lookup weighted +3.)
- **§9h** — internal contradiction, exact duplicate, or a complement-pair that double-scores one concern. **Also
  flag internal IRRECONCILABILITY**: when one criterion *requires* a value that another criterion *penalizes*
  (e.g. C22/C23 demand a recalculated total of 2894.50 while C14–C19 each −3 the very per-purchase numbers that sum
  to it) — no response can satisfy both sets, so the rubric is self-defeating. Major. Detectable with NO external data.
- **§9d** — wrong filename, but only if internally inconsistent or contradicted by inputs.
- **Missing criteria — IS bandable (not merely advisory). FIRST build a REQUIREMENT COVERAGE MATRIX (mandatory):**
  enumerate every explicitly-named **deliverable file**, every named **section/field within a file**, every
  **per-entity output** (each patient/product/listing/account), and every **free-form-artifact content requirement**
  the prompt states; mark each ✓ only if a criterion OR a unit test actually verifies it. Every unmarked row is a
  Missing-Criteria defect (Major if core, else Moderate). This single sweep subsumes (a)–(d) below and is the
  recurring miss class (Reshoot List, MEMORY.md fields, Paul's metrics, AD-SAMBA — all "explicit requirement,
  unverified by rubric AND tests"). (a) **Missing spot-checks** — a set of ≤5 similar
  outcomes (e.g. 4 caption stages, 4 corrected fields) where the rubric checks only *some*; it should check all up
  to 5 → **Major** Missing-Criteria. (b) **An explicit prompt requirement or planted error with ZERO coverage** —
  no criterion AND no unit test verifies it (e.g. a required reshoot-list deliverable; a planted date error the
  prompt asks to correct) → **Major** if the requirement is core, else **Moderate**. (c) **Asymmetric per-entity
  coverage (THE f207 miss — check this every run):** when the prompt requires the SAME set of outputs for multiple
  named entities (2+ patients / products / listings / people / files / accounts), the rubric must cover EACH
  entity's required metrics. If it checks entity A's values but is silent on entity B's, **each uncovered
  required metric for B is its own Missing-Critical criterion** — mirror the count of what's checked for A. (f207:
  prompt asked for Functional/Limited counts at both times + recovery % for BOTH Emily and Paul; rubric had C4/C5/C6
  for Emily but nothing for Paul's Map-C/Map-D counts or recovery → **3 Major missing** → 3/11 = 27.3% → Fail. It is
  NOT enough that the rubric merely names both entities, e.g. a shared dx/assignment criterion.) Count these as
  defective criteria against the denominator; confirm each is also uncovered by any unit test. (Do NOT count purely
  "nice-to-have" coverage you invent — only requirements the prompt or a same-set spot-check actually establishes.)
  (d) **Deliverable-component coverage (THE 5dff miss — check this every run):** when the prompt enumerates several
  required *contents* for ONE output file, decompose that file into its listed components and check that EACH is
  covered by a criterion or test. A criterion that merely *names* the file, or covers only *one* of its components,
  does NOT cover the rest. This bites hardest on **MEMORY.md** and other "log/keep track of X, Y, Z" deliverables.
  (5dff: prompt said MEMORY.md must log the reviewed SKUs **and** the path to listing_qa.md; C5 only checked the one
  flagged item's reason → 2 uncovered components → 2 Moderate Missing-Criteria → 2/5 = 40% > 15% → 6b Fail. Each
  uncovered component is Non-critical→Moderate unless it's the primary deliverable→Major.)
- **Miscategorized criterion** — a sound check tagged with the wrong category (e.g. a process/Task-Completion step
  tagged Factuality) → **Minor**.

## Ruling #1 — spot-check ≠ atomicity (the most common over-flag)
A per-item / named-instance criterion that lists **one item's own fields**, or lists instances of the **same
concern** (e.g. "the 4 carousel images for this post", "captions missing for these 4 dates", "4 files removed"),
is the **endorsed spot-check → EXEMPT**. Only flag §9a when one criterion fuses genuinely DISTINCT concerns.
Reject drawer §9a flags of the exempt kind.

## Rule 19c — unverifiable never anchors a Fail (but CHECK THE TRAJECTORY FIRST)
A gold is **UNVERIFIABLE** only if the value is absent from inputs **AND** from the agent's trajectory. Before
calling anything "connected-service unverifiable", **read `sot/<tid>/trajectory.md`** — the agent's tool calls and
the **environment's tool-RESULTS** (skill/API/DB responses) are surfaced there, and they are GROUND TRUTH for the
"actual records" a prompt names (the orders a Ticketmaster skill returned, a balance an API read, etc.). If the
trajectory resolves the value, the gold is **verifiable**: a criterion that contradicts it is **penalize-correct
Major**, not unverifiable. Only when the value appears nowhere (inputs nor trajectory) is it truly UNVERIFIABLE and
barred from the verdict. (This is the single most common miss — a Pass built on golds the trajectory actually disproves.)
Use the tool-RESULTS (environment responses), not the agent's own claims, as the source of truth.

## Grounding (Rule 19a/g)
Ground in: agent prompt + viewed inputs + active criteria + spec + **the trajectory tool-RESULTS** (`trajectory.md`).
**Never** `story.desired_outcome` or Pass@K (these remain excluded even though they sit near the trajectory in the blob).
Prompt-version drift (rubric grades content the live prompt doesn't ask for) = Incorrect Criteria, Major if material.

## V9 dimensions outside the rubric-criteria band — current scope
**In-band (set our verdict):** V9 dims 11/12/13 (the 6a/6b/6c bands), 14 (invalid weights → Major), 15 (>5
spot-checks = Non-Fail; an under-filled ≤5 set → Major Missing-Criteria).
**In-scope verified non-criteria Fail drivers** — a VERIFIED finding here = **Fail** even if the bands are clean
(record `verdict=Fail`, name the driver, bands may stay 0/0/0; confidence floors to ~30). Apply each only when
clearly verified against the prompt + viewed inputs + trajectory:
- **MM-dependence (1)** — the prompt's explicit requests can be fully met **without** referencing any non-text input.
- **Realism (4)** — >20% of the MM inputs (**or** any 1+ xlsx/docx/pdf) are highly unrealistic/over-curated with no
  reasonable explanation.
- **Leak Prevention (6)** — the solution is explicitly stated in a non-media field (filename / contributor note).
- **Artifact Verification (5)** — **no** rubric criterion (nor test) depends on the **content** of a non-text input;
  existence-only / filename-only checks do not count. (A whole rubric that never verifies any media content.)
- **Safety (7)** — an input artifact contains **real PII identifying a real, existing person** (not synthetic/mocked).
- **Feasibility (3)** — the **PRIMARY** request is impractical/impossible with the available tools. (Secondary-only
  infeasibility = Non-Fail, not our Fail line.)
- **Output filename (2)** — the prompt requests a file as output but never specifies its filename.
- **Tests (V9 dims 16–19), ALL IN SCOPE WHEN UNIT TESTS ARE PRESENT** — read the task's tests (`sot/<tid>/unit_tests.py`,
  surfaced by `dump_tests.py`). Any one of these, verified, is a **Fail driver** (record `verdict=Fail`, name the driver;
  bands may stay 0/0/0). Apply each with its V9 threshold **and the spec's own guard** (don't over-flag; verify against
  the prompt+inputs+rubric, since the drawer over-flags tests):
  - **Correctness (16)** — a test whose logic contradicts the prompt/inputs or is overly specific so it **wrongly fails a
    correct response**. **≥10%** of tests incorrect → Fail. (2d3f: 2 tests demand a `all_in_monthly` column the prompt
    never defines, contradicting `Book1.xlsx`'s `all_in` → a header-preserving correct answer fails.)
  - **Underfitted (17)** — a test too loose/lenient that **accepts invalid** responses (not just valid ones). **>30%**
    underfitted → Fail. GUARD: if the matching rubric criterion legitimately covers the wiggle room (e.g. an unspecified
    column name the rubric checks instead), it is NOT underfitted.
  - **Coverage (18)** — an expected mechanical check (file existence, schema, exact stated value) covered by **neither a
    test nor the rubric**. **>20%** missing → Fail. GUARD: a check covered by the rubric counts as covered (Non-Fail),
    and PDF-type/non-extractable artifacts need only existence checks.
  - **Redundancy (19)** — **>1 pair** of tests/criteria checking the identical behavior with no difference → Fail
    (same structure, different inputs ≠ redundant).

**Out of scope (advisory / conditional / capped at Non-Fail — never our Fail line):** **Justification**
(dim 20, Non-Fail max). **Silver-Trajectory Category** (dim 8, Non-Fail max, optional). **Cross-Modal Synthesis**
(dim 9) & **Architectural Depth** (dim 10) — trajectory/task quality, advisory. Process-targeting
(`evaluation_target=trajectory`) is advisory, never banded. (V9 has **no** Ratings-Validity dimension — dropped.)

## The drawer (platform 2nd opinion)
High-recall, lower-precision cross-check — **not an oracle**. Reconcile by **verified union**: adopt every drawer
finding that survives a check against the real criterion + prompt + pixels; keep your own verified findings; never
defer blindly, never ignore it. Its hit-rate on divergent findings is ~⅓.
- **The drawer's test claims are unreliable — never trust them.** It frequently reports a task as "test-less / 0
  unit tests" when the task DOES ship unit tests (it never opened `verifier.py`), and it over-flags Tests-Correctness.
  Always grade the Tests dimensions (16–19) from `sot/<tid>/unit_tests.py` (surfaced by `dump_tests.py`) — not from
  the drawer's test count. (Seen this run on 56ec + 56e1: drawer said "0 tests"; 4 and 7 tests were actually present.)
- **A complement pair is ONE defect, counted once.** When the drawer reaches a Fail by counting an oppositely-weighted
  complement pair (a `+w` and a `−w` criterion that score the same single decision) as TWO defective criteria,
  recount: §9h treats the pair as one redundancy finding (attributed to the redundant negative). Do not let the drawer
  inflate the band by double-counting the pair. (06de: drawer counted C3/C14 as 2 → 21.4%; true count is 1 → 14.3%.)

## No reuse — always redo the whole queue
Every run re-audits **every** pending task from scratch (rehydrate → grounded audit → drawer reconcile → prose).
**NEVER** carry a verdict, confidence, prose, or finding over from a prior run's feedback record, and never build a
"reuse" path in assembly. A prior record is historical reference only — rubrics and specs are revised continuously, so
a reused verdict is silently stale. The canonical `scripts/assemble.py` builds `feedback.json` from THIS run's
`reconciled/` + `prose/` only (no pool, no prior-record read).
