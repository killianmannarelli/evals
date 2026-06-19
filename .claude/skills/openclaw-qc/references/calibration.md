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
  (verify against the prompt + pixels). Major.
- **Over-specification** — demands content / method / exact values / filenames / schemas / sections the **live
  prompt** never asks for. Major if material, else Moderate (Overfitting).
- **§9a Not-Atomic** — ONE criterion fuses **distinct** concerns/columns. Moderate (Major if it fuses many
  unrelated assertions).
- **Sign-inversion / invalid weight** — a weight outside {−5,−3,−1,+1,+3,+5}; or a negative weight on a *good*
  behavior (a correct response eats the penalty). Major.
- **§9h** — internal contradiction, exact duplicate, or a complement-pair that double-scores one concern. **Also
  flag internal IRRECONCILABILITY**: when one criterion *requires* a value that another criterion *penalizes*
  (e.g. C22/C23 demand a recalculated total of 2894.50 while C14–C19 each −3 the very per-purchase numbers that sum
  to it) — no response can satisfy both sets, so the rubric is self-defeating. Major. Detectable with NO external data.
- **§9d** — wrong filename, but only if internally inconsistent or contradicted by inputs.
- **Missing criteria — IS bandable (not merely advisory):** (a) **Missing spot-checks** — a set of ≤5 similar
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

**Out of scope (advisory / conditional / capped at Non-Fail — never our Fail line):** **Tests** (V9 dims 16–19;
"only if unit tests present" — no contributor verifier on this pipeline + benchmark decision). **Justification**
(dim 20, Non-Fail max). **Silver-Trajectory Category** (dim 8, Non-Fail max, optional). **Cross-Modal Synthesis**
(dim 9) & **Architectural Depth** (dim 10) — trajectory/task quality, advisory. Process-targeting
(`evaluation_target=trajectory`) is advisory, never banded. (V9 has **no** Ratings-Validity dimension — dropped.)

## The drawer (platform 2nd opinion)
High-recall, lower-precision cross-check — **not an oracle**. Reconcile by **verified union**: adopt every drawer
finding that survives a check against the real criterion + prompt + pixels; keep your own verified findings; never
defer blindly, never ignore it. Its hit-rate on divergent findings is ~⅓.
