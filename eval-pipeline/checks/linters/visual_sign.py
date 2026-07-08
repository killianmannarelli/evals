"""visual_sign — sign errors on rubric criteria (the customer flagged several).

A sign error = a criterion whose TEXT describes UNDESIRED behavior but is scored as if desired
(positive weight / is_positive=true), so the grader rewards the bad thing (or vice-versa).

Works on both shapes:
  - visual_rubrics.json criteria: {is_positive: bool, score: number, title/criteria}
  - tests/rubric.json criteria: signed `weight` (negative = penalty guard)

Heuristic: if the criterion text contains an "undesired" marker (should not / fails to /
hallucinat / incorrectly / must not / penaliz / without) then it SHOULD be scored negative
(is_positive=false or weight<0). If it's scored positive, flag it.
"""
from src.common import finding


def _is_undesired(text, markers):
    t = (text or "").lower()
    return any(m in t for m in markers)


def run(ctx, cfg):
    t = cfg["thresholds"]["visual_sign"]
    markers = [m.lower() for m in t.get("undesired_markers", [])]
    tier = t.get("tier", "action_required")
    out = []

    # visual_rubrics.json shape (is_positive + score)
    for i, c in enumerate(ctx.get("visual_rubrics") or []):
        if not isinstance(c, dict):
            continue
        text = c.get("criteria") or c.get("title") or c.get("description") or ""
        score = c.get("score")
        is_pos = c.get("is_positive")
        scored_positive = (is_pos is True) or (isinstance(score, (int, float)) and score > 0)
        if _is_undesired(text, markers) and scored_positive:
            out.append(finding(
                "visual_sign", "RUBRIC_UNFAIR", tier,
                f"Visual rubric R{i+1} describes undesired behavior but is scored positive "
                f"(is_positive={is_pos}, score={score}) — it rewards the bad behavior.",
                fix="Set is_positive=false with a negative score so the criterion penalizes the "
                    "undesired behavior instead of rewarding it.",
                rubric_ids=[i + 1], evidence=text[:160]))

    # tests/rubric.json shape (signed weight)
    for i, c in enumerate(ctx.get("rubric") or []):
        if not isinstance(c, dict):
            continue
        text = c.get("criteria") or c.get("title") or ""
        w = c.get("weight")
        if isinstance(w, (int, float)) and w > 0 and _is_undesired(text, markers):
            out.append(finding(
                "visual_sign", "RUBRIC_UNFAIR", tier,
                f"Rubric R{i+1} describes undesired behavior but carries a positive weight ({w}) — "
                f"it rewards the bad behavior instead of penalizing it.",
                fix="Give this criterion a negative weight (penalty guard) so incurring the bad "
                    "behavior subtracts points.",
                rubric_ids=[i + 1], evidence=text[:160]))
    return out
