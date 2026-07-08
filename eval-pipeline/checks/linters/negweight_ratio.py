"""negweight_ratio — §9g of the spec: rubrics must have ~25% negative-weight criteria (cap 30%).

This is the exact rule the viewer's Task-level-flags drawer fired on (elizabeth_miller task:
"zero negative-weight criteria; §9g requires ~25% (cap 30%)"). Fully deterministic from the
rubric weights, so we reproduce that flag with certainty.

Bands (thresholds tunable in config):
  - 0 negative-weight criteria           -> Fail  (category "[Fail - 15%+ Moderate Rubric Errors]"-adjacent; a structural miss)
  - 0 < frac < target (0.25)             -> Non-Fail (below target)
  - frac > cap (0.30)                     -> Non-Fail (over cap)
"""
from src.common import finding


def run(ctx, cfg):
    t = cfg["thresholds"]["negweight_ratio"]
    rub = ctx.get("rubric") or []
    weighted = [c for c in rub if isinstance(c.get("weight"), (int, float))]
    n = len(weighted)
    if n == 0:
        return []
    neg = sum(1 for c in weighted if c["weight"] < 0)
    frac = neg / n
    target, cap = t["target_frac"], t["cap_frac"]
    ev = f"{neg}/{n} = {frac:.0%} negative-weight (§9g target {target:.0%}, cap {cap:.0%})"
    if neg == 0:
        return [finding("negweight_ratio", "RUBRIC_UNFAIR", t["tier_zero"],
            f"Rubric has ZERO negative-weight criteria. §9g requires ~{target:.0%} (cap {cap:.0%}) "
            f"negative-weight criteria to cover failure modes (cross-modal hallucination, prohibitions). {ev}.",
            fix=f"Add negative-weight criteria (~{target:.0%} of the set) that AWARD points when a "
                f"failure mode IS present (affirmative phrasing of the bad behavior).",
            evidence=ev)]
    if frac < target:
        return [finding("negweight_ratio", "RUBRIC_UNFAIR", t["tier_below"],
            f"Negative-weight criteria are {frac:.0%}, below the §9g ~{target:.0%} target. {ev}.",
            fix=f"Add negative-weight criteria until ~{target:.0%} of the set is negative.", evidence=ev)]
    if frac > cap:
        return [finding("negweight_ratio", "RUBRIC_UNFAIR", t["tier_below"],
            f"Negative-weight criteria are {frac:.0%}, above the §9g {cap:.0%} cap. {ev}.",
            fix=f"Reduce negative-weight criteria below the {cap:.0%} cap.", evidence=ev)]
    return []
