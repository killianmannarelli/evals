# Calibration rulings (apply in every audit)

The condensed rules. Full detail in `project_overrides.md` + `auditor.md` + `master_auditor.md`.

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
- **§9h** — internal contradiction, exact duplicate, or a complement-pair that double-scores one concern.
- **§9d** — wrong filename, but only if internally inconsistent or contradicted by inputs.

## Ruling #1 — spot-check ≠ atomicity (the most common over-flag)
A per-item / named-instance criterion that lists **one item's own fields**, or lists instances of the **same
concern** (e.g. "the 4 carousel images for this post", "captions missing for these 4 dates", "4 files removed"),
is the **endorsed spot-check → EXEMPT**. Only flag §9a when one criterion fuses genuinely DISTINCT concerns.
Reject drawer §9a flags of the exempt kind.

## Rule 19c — unverifiable never anchors a Fail
If confirming a gold needs an input you don't have (a connected-service value, an unrehydrated file), it is
**UNVERIFIABLE** — record it, but it cannot drive the verdict.

## Grounding (Rule 19a/g)
Ground only in: agent prompt + viewed inputs + active criteria + spec. **Never** `story.desired_outcome` or Pass@K.
Prompt-version drift (rubric grades content the live prompt doesn't ask for) = Incorrect Criteria, Major if material.

## Out of scope
Tests dims **8a-d** (no contributor verifier on the current pipeline). Process-targeting (`evaluation_target=
trajectory`) is advisory, never banded. Ratings-validity (dim 16) and Justification (dim 21) are separate
dimensions — not part of the 6a/6b/6c rubric-criteria band.

## The drawer (platform 2nd opinion)
High-recall, lower-precision cross-check — **not an oracle**. Reconcile by **verified union**: adopt every drawer
finding that survives a check against the real criterion + prompt + pixels; keep your own verified findings; never
defer blindly, never ignore it. Its hit-rate on divergent findings is ~⅓.
