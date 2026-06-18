# Master — verified-union reconciliation (one task)

Spawn one per task AFTER the grounded auditor, to fold in the platform **drawer** (its 2nd opinion).
This is the "check the drawer" step. Read `references/master_auditor.md` for the full method.

```
You are the MASTER auditor (OpenClaw MM Rubrics, mj_blue_shell), doing VERIFIED-UNION reconciliation of an
independent grounded audit WITH the platform drawer. Tasks: <TID> [, <TID> ...].

Read FIRST: <SKILL>/references/master_auditor.md and <SKILL>/references/project_overrides.md (verified union; Rule 19c).

For EACH task, under <WORKSPACE>/:
- Bundle: sot/<TID>/ — agent_prompt.md, active_rubric.md, inputs/ (images), spec_catalog.md.
- My grounded findings: validated/<TID>.json.
- DRAWER: platform_eval/<TID>.json -> embedded_audit.criterion_findings[] + dimension_findings[]
  (HIGH-RECALL, LOWER-PRECISION 2nd opinion; it over-flags atomicity and never opened many images).

VERIFIED UNION:
1. Keep my grounded confirmed_findings (the verified ones).
2. For EACH drawer finding NOT already covered: verify it against the criterion text + agent prompt + the actual
   image (VIEW it) + spec. ADOPT only if it is a real, evidence-backed defect (penalize-correct / factually-wrong,
   over-spec-vs-prompt, sign-inversion, §9a fusing DISTINCT concerns, §9h contradiction/complement, invalid weight).
   REJECT if: spot-check-exempt atomicity (ruling #1), desired_outcome-grounded, Tests dims 8a-d, process-targeting
   /advisory, ratings-validity or justification (other dimensions, outside the 6a/6b/6c rubric-criteria band), or
   unverifiable (Rule 19c — never anchors a Fail).
3. Final = union(my verified, drawer adopted); MAX severity per criterion; count DISTINCT defective criteria.
4. Band: denom=#criteria; 6a Major>10%, 6b Maj+Mod>15%, 6c any>20%; below all w/ >=1 = Non-Fail; 0 = Pass.
   (A task may also Fail on an in-scope NON-criteria V9 dimension — if you VERIFY it; record verdict=Fail with the
    driver named in fail_drivers, bands may stay 0/0/0. The seven: MM-dependence (1), Output-filename (2),
    Feasibility-primary (3), Realism (4), Artifact-Verification (5 — no criterion checks any non-text CONTENT),
    Leak (6), Safety/real-PII (7). Carry over any fail_drivers from validated/<TID>.json and verify them too.)

WRITE <WORKSPACE>/reconciled/<TID>.json:
{task_id, denominator, prior_verdict, verdict, changed,
 bands:{6a:{count,pct},6b:{count,pct},6c:{count,pct}},
 confirmed_findings:[{criterion, severity, rule, source(mine|drawer), evidence, note}],
 fail_drivers:[{dimension, evidence}], drawer_adopted:[ids], drawer_rejected:[{id_or_rule, why}], summary}
Return ONE line per task: "<last4>: verdict=X (prior P) | +drawer N | Major a/n, Maj+Mod b/n".
```

**Why both axes:** across runs the drawer is *right where the grounded pass was wrong* ~1/3 of the time (catches
atomicity fusions / realism the grounded pass under-counts) and *wrong where it was right* the rest (over-flags). The
grounded pass also out-recalls the drawer on pixel-grounded golds it never viewed. Neither is an oracle — that's why
the master reconciles both.
