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

def _pct(band, denominator):
    """Defect rate in PERCENTAGE POINTS (e.g. 10.5), robust to agents that stored
    `pct` as a fraction (0.105). Prefer count/denominator when available — counts
    are unambiguous; only fall back to the stored pct (fraction-guarded) otherwise."""
    c = float(band.get("count", 0) or 0)
    if denominator:
        return 100.0 * c / float(denominator)
    p = float(band.get("pct", 0) or 0)
    return p * 100.0 if (0 < p <= 1.0 and c > 0) else p   # 0.105 -> 10.5


def compute_confidence(bands, denominator=None, n_unverifiable=0, is_fail=False):
    M  = _pct(bands["6a"], denominator)   # Major %
    MM = _pct(bands["6b"], denominator)   # Major+Moderate %
    A  = _pct(bands["6c"], denominator)   # any-severity %
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
