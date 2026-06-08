---
title: V6/V7 audit spec (query 304995)
type: reference
project: openclaw-mm-rubrics
source: redash.scale.com query 304995 (SPEC_GETTER)
pulled: 2026-06-08
tags: [openclaw, qc, spec]
---

# V7 - synthetic artifact/justif updates — V6/V7 audit spec

Pulled **live** from Redash query **304995** (`SPEC_GETTER`) for project `69f95a0f0992772af7907a03` on 2026-06-08: **54 option rows across 20 dimensions**. The rendered body is **byte-identical** (sha `e557113fe9ab`) to the 2026-06-07 snapshot — the customer rubric is unchanged.

## Dimensions (20)

| # | Dimension | Bucket | Scores | In audit scope |
|---|---|---|---|---|
| 1 | Prompt - MM dependence | Other | 5,2 | — |
| 2 | Prompt - Output file(s) name | Other | 5,2 | — |
| 3 | Prompt - Feasibility With Tools | Other | 5,3,2 | — |
| 4 | Input Artifacts - Realism | Other | 5,3,2 | input-artifact dims |
| 5 | Input Artifacts - Artifact Verification | Other | 5,2 | input-artifact dims |
| 6 | Input Artifacts - Leak Prevention | Other | 5,3,2 | input-artifact dims |
| 7 | Verifiers - Safety | Other | 5,2 | — |
| 8 | Silver Trajectory - Category and Subcategory | Other | 5,3 | — |
| 9 | Silver Trajectory - Cross-Modal & Cross-Service Synthesis | Other | 5,3,2 | — |
| 10 | Trajectory - Architectural Depth & Friction Exposure | Other | 5,3,2 | — |
| 11 | Tests - Correctness | Other | 5,3,2 | OUT (tests 8a–d) |
| 12 | Tests - Underfitted Tests | Other | 5,3,2 | OUT (tests 8a–d) |
| 13 | Tests - Coverage | Other | 5,3,2 | OUT (tests 8a–d) |
| 14 | Tests - Redundancy | Other | 5,3,2 | OUT (tests 8a–d) |
| 15 | Failed Rubric/Unit Test - Justification | Other | 5,3 | — |
| 16 | Rubric Criteria - Overall Rubric Quality - Major | Rubric Criteria | 5,3,2 | **6a** band (Major > 10% → Fail) |
| 17 | Rubric Criteria - Overall Rubric Quality - Major/Moderate | Rubric Criteria | 5,3,2 | **6b** band (Major+Moderate > 15% → Fail) |
| 18 | Rubric Criteria - Overall Rubric Quality - Major/Moderate/Minor | Rubric Criteria | 5,3,2 | **6c** band (any severity > 20% → Fail) |
| 19 | Rubric Criteria - Rubric Structure | Rubric Criteria | 5,2 | structure / atomicity |
| 20 | Rubric Criteria - Rubric Spot Checks | Rubric Criteria | 5,3 | spot-check ruling |

## How this maps to verdicts
- The three **Overall Rubric Quality** dims are the banded ones: **6a** (Major), **6b** (Major+Moderate), **6c** (any severity), denominator = CB-authored criteria. Fail thresholds 10 / 15 / 20 %.
- The four **Tests -** dims (Correctness, Underfitted, Coverage, Redundancy) are **out of scope** for this L10 sweep (the 8a–d tests dims).
- **Rubric Spot Checks** underwrites the spot-check-exempt ruling; **Rubric Structure** covers atomicity.
- Every option carries a Pass(5) / Non-Fail(3) / Fail(2) score band; score 2 options require justification.

_Full dimension-by-dimension text (508 lines) lives in the FULL package at `redash/spec_V6V7_query304995.md`; re-pull with `fetch_spec.py --query-id 304995`._
