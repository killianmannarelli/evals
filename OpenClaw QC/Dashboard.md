---
title: OpenClaw QC — Dashboard
type: dashboard
project: openclaw-mm-rubrics
tags: [openclaw, qc, l10]
---

# OpenClaw QC — Dashboard

Built from the section-4 table of `HANDOFF — OpenClaw MM Rubrics QC (L10) · 2026-06-07`
(project **mj_blue_shell**, `69f95a0f0992772af7907a03`). One note per audited task in
`Tasks/`. Use **`OpenClaw QC.base`** for the native Bases views; this Dashboard is the
Dataview fallback plus the build notes.

## Dataview fallback (if Bases isn't available)

```dataview
TABLE persona, task_type, verdict, drawer_verdict, platform_pct AS "plat%", denominator AS n, divergence
FROM "OpenClaw QC/Tasks"
SORT verdict ASC, platform_pct ASC
```

```dataview
TABLE persona, task_type, platform_pct AS "plat%", divergence
FROM "OpenClaw QC/Tasks"
WHERE verdict = "Fail"
SORT platform_pct ASC
```

## What the database contains

- **16 task notes** (run1's 12-task sweep + run2's 4 new tasks). Verdict split across both
  runs: **4 Pass · 8 Non-Fail · 4 Fail**.
- De-duplicated to the *current* state: run1 = **4 Pass / 5 Non-Fail / 3 Fail** (12), plus the
  new-in-run2 tasks (`06db`, `06df`, `06ed` Non-Fail + `06f8` Fail).
- **Current L10-pending queue (run2, 6 tasks)** = the 4 notes with `run: run2` **+** the 2 with
  `carryover: true` (`…753e`, `…0eb`, both Fail). Verdict split: **0 Pass / 3 Non-Fail / 3 Fail**.

### The three evals (why there are multiple verdict columns)
1. **platform_pct** — the viewer's score: did the model's *response* satisfy the rubric.
2. **verdict** — my QC audit: is the *rubric itself* sound (the final, post-reconciliation call).
3. **drawer_verdict** — the audit embedded in the viewer drawer; a high-recall cross-check,
   reconciled by **verified union** (adopt what survives a check against the real criterion /
   prompt / pixels). Not an oracle.

## Field provenance
- `verdict`, `drawer_verdict`, `platform_pct`, `persona`, `task_type`, `divergence` — from the
  HANDOFF section-4 table (the declared source of truth).
- `band_6a`, `band_6b`, `denominator` — the section-4 table abbreviated several of these; they
  are completed here from each task's authoritative `validated/<task>.json` band math (and the
  `reconciled/<task>.json` math for the two reconciliation flips). They never contradict the
  table where it stated a value.
- `viewer` — the exact `viewer_url` scraped into `platform_eval/<task>.json`.
- `run` = the task's origin sweep; `carryover: true` marks the two run1 Fails that recur in the
  live run2 queue.

## Eval divergences — read this (8 vs 9)
The **"Eval divergences"** Bases view filters `verdict != drawer_verdict`, so it lists the **8**
tasks whose *final* verdict tier differs from the drawer:
`…0eb, …06f8, …c0e2, …c0ed, …06da, …06ef, …06f3, …06f4`.

The HANDOFF's verification prose lists **9** (those 8 **+ `…0f0`**). `0f0` is the edge case: the
drawer said **Fail** and my *final* verdict is also **Fail**, so the final tiers **agree** — but
they agree only because reconciliation **adopted** the drawer's filename Majors (my independent
prior was **Non-Fail**). The note bodies for the two such tasks carry an explicit
**Reconciliation flip** callout:

- `…0f0` — prior **Non-Fail** → final **Fail** (drawer Fail).
- `…06e9` — prior **Pass** → final **Non-Fail** (drawer Non-Fail).

So `0f0` is a *pre-reconciliation* divergence, not a final-tier one. The strict, machine-checkable
view follows the final verdict (8 rows). If you instead want the prose's 9, count `0f0` as a
reconciliation flip rather than relaxing its `drawer_verdict` (the drawer genuinely was Fail).

## Open items (from the HANDOFF)
- 3 live Fails to fix or dispute: **753e** (remove 4 present-product −5 decoys), **0eb** (relax
  10 fixed-price criteria to consistency checks), **f8** (remove pool/landline criteria absent
  from the photos).
- Bake the drawer's recurring catches into the auditor: filename/path-existence, §9a two-count
  conjunctions, method/structure over-spec.
- Eng escalation: a run-environment defect (missing `sharp`/`openpyxl`, image-model timeouts)
  invalidated the platform score on tasks **0e2** + **e9** — measurement-invalidating on a
  multimodal benchmark.
