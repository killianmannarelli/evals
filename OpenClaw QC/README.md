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
  where the final verdict was adopted from the drawer).
- **`OpenClaw QC.base`** — native Obsidian **Bases** views: *All audits*, *Fails only*,
  *Eval divergences*.
- **`Dashboard.md`** — Dataview fallback (if Bases is unavailable) + build notes, field
  provenance, counts, and the 8-vs-9 divergence explainer.

## At a glance
- **16 tasks** · verdict split **4 Pass · 8 Non-Fail · 4 Fail** (both runs).
- **Current L10 queue (run2):** 4 `run: run2` notes + 2 `carryover: true` notes → **0 Pass · 3 Non-Fail · 3 Fail**.
- **Eval divergences** (final `verdict != drawer_verdict`) → 8 tasks: `…0eb, …06f8, …c0e2,
  …c0ed, …06da, …06ef, …06f3, …06f4`. See `Dashboard.md` for the `…0f0` edge case.

## How verdicts are decided
Bands on CB-authored criteria: **6a Fail** if Major > 10%; **6b** if Major+Moderate > 15%;
**6c** if any-severity > 20%. Below all three with ≥1 defect = **Non-Fail**; zero defects =
**Pass**. Tests dims 8a–d are out of scope.
