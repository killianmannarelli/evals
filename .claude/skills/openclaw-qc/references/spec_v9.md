# OpenClaw MM Rubrics — V9 spec ("Add missing notes") — authoritative dimension map

Source of truth: `references/spec_v9_rubric.csv` (the exact QC questionnaire; project `69f95a0f0992772af7907a03`).
The per-run `sot/<tid>/spec_catalog.md` is the same V9 spec pulled fresh from Redash 304995 (SPEC_GETTER).
This file is the readable digest + **our scope treatment** of each dimension.

Score legend: **2 = Fail**, **3 = Non-Fail**, **5 = Pass**. "Max Non-Fail" = the dimension can never score below 3.

## PROMPT
1. **MM dependence** — *Fail* if the prompt's explicit requests can be fully met **without** referencing any
   non-text input (no multimodal reasoning needed); *Pass* if it cannot be answered without the media.
2. **Output file(s) name** — *Fail* if the prompt asks for a file output but never specifies the filename;
   *Pass* if the filename is specified.
3. **Feasibility With Tools** — *Fail* if the **primary** request is impractical/impossible with the available
   tools; *Non-Fail* if one+ **secondary** requests are infeasible; *Pass* if fully actionable. (openclaw can run
   any python lib in a linux env, create venvs, etc.)

## INPUT ARTIFACTS
4. **Realism** — *Fail* if >20% of the multimodal inputs (**or** any 1+ xlsx/docx/pdf) are highly unrealistic /
   over-curated / "too perfect" with no reasonable explanation; *Non-Fail* if slightly unrealistic but plausible
   (or a stated reason exists); *Pass* if plausible & realistic.
5. **Artifact Verification** — *Fail* if, across **both** verifier types (tests **and** rubric criteria), **no**
   test/criterion depends on the **content** of a non-text file (existence-only checks do **not** count); *Pass*
   if ≥1 content-dependent verifier exists.
6. **Leak Prevention** — *Fail* if the solution is explicitly stated in a non-media field (filename like
   `overdue_balance_500.pdf`, contributor note that states the answer); *Non-Fail* if labeling gives heavy leading
   hints; *Pass* if identifiers are neutral/randomized and notes are process-only.

## VERIFIERS
7. **Safety** — *Fail* if any input artifact contains **real PII identifying a real, existing person** (not
   synthetic/mocked); *Pass* if no real PII.

## SILVER TRAJECTORY  (only graded when a silver trajectory is present)
8. **Category and Subcategory** — *Non-Fail* (max) if the trajectory is unrelated to / better fits a different
   category; *Pass* if clearly related. Subcategory misalignments are **not** flagged.
9. **Cross-Modal & Cross-Service Synthesis** — *Fail* (Disconnected/Simple Processing) if inputs are treated as
   isolated silos or there's no real cross-modal opportunity; *Non-Fail* (Trivial Integration) if combined
   superficially; *Pass* if a seamless cross-modal/service handoff with discrepancy-flagging.

## TRAJECTORY
10. **Architectural Depth & Friction Exposure** — *Fail* if no meaningful tool dependency; *Non-Fail* if depth is
    possible-but-not-required / shallow tool use; *Pass* if it forces modular multi-stage reasoning with real
    friction (conflicting data, missing fields, normalization, constraint negotiation). MEMORY.md must be required
    (explicitly or implicitly) in multi-turn tasks.

## RUBRIC CRITERIA  ← the core of our audit (denominator = CB-authored criteria; never double-count)
11. **Overall Rubric Quality — Major**  *(our 6a)* — *Fail* if **Major > 10%**; Non-Fail ≤10%; Pass none.
12. **Overall Rubric Quality — Major/Moderate**  *(our 6b)* — *Fail* if **Major+Moderate > 15%**; Non-Fail ≤15%
    with major <5%; Pass none.
13. **Overall Rubric Quality — Major/Moderate/Minor**  *(our 6c)* — *Fail* if **any-severity > 20%**; Non-Fail
    5–20% with major <5% & moderate <15%; Pass <5% minor only.
14. **Rubric Structure** — *Fail* if any weight is outside **{−5,−3,−1,+1,+3,+5}**; Pass if all valid. (Weights
    reflect the **difficulty** of what's tested, not its importance.)
15. **Rubric Spot Checks** — *Non-Fail* (max) if **>5** spot checks exist for any one outcome group; Pass if ≤5
    each. CBs are **expected** to provide up to 5 spot checks **plus a volume criterion** when there are
    sufficiently similar outcomes — so *missing* spot-checks within a ≤5 set is a real coverage gap (see calibration).

## TESTS  (only graded when unit tests are present)
16. **Correctness** — Fail ≥10% tests wrong/over-specific; Non-Fail <10%; Pass all correct.
17. **Underfitted Tests** — Fail >30% too-loose; Non-Fail ≤30%; Pass none.
18. **Coverage** — Fail >20% of expected tests missing (and not covered by any verifier); Non-Fail ≤20% missing or
    covered-by-rubric; Pass full. (PDF-type artifacts need only existence/structural checks; exact-schema requests
    need schema+content checks.)
19. **Redundancy** — Fail >1 pair of tests/criteria checking the identical behavior; Non-Fail exactly 1 pair / some
    overlap; Pass consolidated. (Same structure, different inputs ≠ redundant.)

## FAILED RUBRIC/UNIT TEST
20. **Justification** — *Non-Fail* (max): weak (too brief / no specific model-error pinpoint) **or** incorrect
    (defends an overly-specific/unrequested rubric) justification; *Pass* if all 3 justification questions are
    answered thoroughly for every Claude-failed verifier.

---

## OUR SCOPE — which dimensions set our verdict
**In-band (drive Pass / Non-Fail / Fail via the criteria count):** 11, 12, 13 (the 6a/6b/6c bands), 14 (invalid
weights → Major), 15 (>5 = Non-Fail; an under-filled ≤5 spot-check set → Major Missing-Criteria).

**In-scope verified non-criteria Fail drivers** — a VERIFIED finding here = **Fail** even if the bands are clean
(record `verdict=Fail`, name the driver; bands may stay 0/0/0; confidence floors to ~30). All seven (project-lead
decision 2026-06-18 — match the full V9 Fail set we can verify):
- **1 MM-dependence** — requests fully answerable without any non-text input.
- **2 Output filename** — prompt asks for a file but never names it.
- **3 Feasibility** — the **primary** request is impossible with the available tools (secondary-only = Non-Fail).
- **4 Realism** — >20% of MM inputs (or any 1+ xlsx/docx/pdf) highly contrived with no reasonable explanation.
- **5 Artifact Verification** — no rubric criterion (nor test) depends on the **content** of a non-text input.
- **6 Leak Prevention** — solution explicitly stated in a non-media field (filename / note).
- **7 Safety** — input contains real PII identifying a real, existing person (not synthetic).

**Out of scope** (advisory / conditional / capped at Non-Fail — never drive our Fail line): **8 Category**
(Non-Fail max, optional), **9 Cross-Modal Synthesis** & **10 Architectural Depth** (trajectory/task quality,
advisory/process-targeting), **16–19 Tests** (conditional on a verifier we don't have on this pipeline; benchmark
decision to exclude), **20 Justification** (Non-Fail max).
