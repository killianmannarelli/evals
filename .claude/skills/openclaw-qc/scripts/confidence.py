#!/usr/bin/env python3
"""Confidence (0-100) that a rubric can be DELIVERED AS-IS without failing.

Driven by the objective signal already produced by the audit — how far each
defect rate sits from its Fail threshold (Major>10%, Maj+Mod>15%, any>20%) —
plus a small discount for golds that couldn't be verified (they carry residual
flip-risk: if the unseen connected-service value differs, the task could fail).

  100  = spotless, every gold verified -> ships clean
  ~50  = a non-fail sitting right on a Fail line (one defect from failing)
  ~38  = a fail just over a line (one fix from passing)
  ~5   = a catastrophic fail (e.g. whole-rubric prompt drift)
"""

def compute_confidence(bands, denominator=None, n_unverifiable=0, is_fail=False):
    M  = float(bands["6a"]["pct"])   # Major %
    MM = float(bands["6b"]["pct"])   # Major+Moderate %
    A  = float(bands["6c"]["pct"])   # any-severity %
    # ratio to each Fail line; >=1 means it fails on that constraint
    worst = max(M / 10.0, MM / 15.0, A / 20.0)
    # A task can FAIL on a verified non-criteria dimension (Input-Realism / Leak /
    # MM-dependence) while its criteria bands stay clean. It still can't ship as-is,
    # so floor it into the fail range rather than trusting the (clean) bands.
    if is_fail and worst <= 1.0:
        return 30
    if worst <= 1.0:                              # Pass / Non-Fail
        score = 100.0 - 50.0 * worst
        if denominator and n_unverifiable:        # residual flip-risk discount
            score -= 12.0 * min(n_unverifiable / denominator, 1.0)
    else:                                         # Fail (band-driven)
        score = 40.0 - 35.0 * min(worst - 1.0, 1.0)
    return max(3, min(100, round(score)))


# "Pending" rows (un-materialized) have no bands -> no meaningful confidence.
def confidence_for(rec, n_unverifiable=0):
    """rec = a reconciled dict (has bands + verdict + denominator) or None. Returns int or ''."""
    if not rec or not rec.get("bands"):
        return ""
    is_fail = str(rec.get("verdict", "")).strip().upper().startswith("FAIL")
    return compute_confidence(rec["bands"], rec.get("denominator"), n_unverifiable, is_fail)
