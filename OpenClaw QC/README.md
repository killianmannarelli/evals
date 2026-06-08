---
title: OpenClaw QC — vault folder
type: index
project: openclaw-mm-rubrics
tags: [openclaw, qc, l10]
---

# OpenClaw QC

A queryable Obsidian database of the **L10 rubric-QC audits** for project **mj_blue_shell**
(OpenClaw MM Rubrics, `69f95a0f0992772af7907a03`), built from the 2026-06-07 HANDOFF.

## Layout
- **`Tasks/<task_id>.md`** — one note per audited task (16 total). YAML frontmatter holds the
  verdict, drawer verdict, platform %, band math, denominator, divergence, run, carryover flag,
  and the live viewer URL; the body has a one-line driver (plus a reconciliation-flip callout
  where the final verdict was adopted from the drawer), an **Inputs** inventory (images/video/docs
  now available from the FULL package), and **pixel-verification** notes on the image-grounded
  Fails (f8, 753e).
- **`OpenClaw QC.base`** — native Obsidian **Bases** views: *All audits*, *Fails only*,
  *Eval divergences*.
- **`Dashboard.md`** — Dataview fallback (if Bases is unavailable) + build notes, field
  provenance, counts, and the 8-vs-9 divergence explainer.
- **`Spec-V6V7.md`** — digest of the customer audit rubric (Redash query 304995, 20 dimensions),
  pulled **live** 2026-06-08 and confirmed unchanged vs. the snapshot; maps the dimensions to the
  6a/6b/6c bands and the out-of-scope tests dims.
- **`Live-checks/2026-06-08.md`** — a live Redash pull: spec unchanged + the current L10-pending
  queue (6 → 13) with the diff vs. the audit snapshot.
- **`Audit-runs/2026-06-08-L10.md`** — the 2026-06-08 L10 re-audit: 3 auditable (753e/0eb still
  Fail, 0f0 improved Fail → Non-Fail) + 10 `audit_incomplete` (CDS view not yet populated). The
  three auditable verdicts also append a **Re-audit (2026-06-08)** section to their task notes.

## At a glance
- **16 tasks** · verdict split **4 Pass · 8 Non-Fail · 4 Fail** (both runs).
- **Current L10 queue (run2):** 4 `run: run2` notes + 2 `carryover: true` notes → **0 Pass · 3 Non-Fail · 3 Fail**.
- **Eval divergences** (final `verdict != drawer_verdict`) → 8 tasks: `…0eb, …06f8, …c0e2,
  …c0ed, …06da, …06ef, …06f3, …06f4`. See `Dashboard.md` for the `…0f0` edge case.
- **Live check 2026-06-08:** V6/V7 spec unchanged; L10 queue turned over 6 → 13. The two carryover
  Fails (`…753e`, `…0eb`) are **still stuck** at L10 (Jun 1 / Jun 3 attempts); `…0f0` re-entered the
  queue; 10 net-new tasks await audit. See `Live-checks/2026-06-08.md`.

## How verdicts are decided
Bands on CB-authored criteria: **6a Fail** if Major > 10%; **6b** if Major+Moderate > 15%;
**6c** if any-severity > 20%. Below all three with ≥1 defect = **Non-Fail**; zero defects =
**Pass**. Tests dims 8a–d are out of scope.
