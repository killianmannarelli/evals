"""weight_mix — Karan Sikka's rubric weight-distribution bar (chat 2026-07-04).

Requirement:
  - accuracy rubrics must be >= accuracy_min_frac_of_total of total (positive) rubric weight
  - vision (visual-modality) rubrics must be >= vision_min_frac_of_accuracy of the accuracy mix
    (equivalently >= vision_min_frac_of_total of total)

"accuracy" = rubric criteria whose `type` is in thresholds.weight_mix.accuracy_types
(default ["factuality and hallucination"], optionally + ["task completion"]).
"vision"   = criteria whose `modality` != text_only_modality_value.

Deterministic: sums signed weights from tests/rubric.json (positive weights only for shares).
Emits WEIGHT_MIX findings for whichever bar(s) are missed, with the exact percentages.

The VISION bar only applies to tasks that actually involve vision (see _is_visual_task): a
genuinely text-only task has no vision requirement, so applying the vision bar there was a
false positive on *every* text-only task. Gate off via thresholds.weight_mix.require_visual_task.
"""
from src.common import finding


def _acc_types(t):
    types = list(t.get("accuracy_types", []))
    if t.get("count_optional_as_accuracy"):
        types += list(t.get("accuracy_types_optional", []))
    return set(types)


def _is_visual_task(ctx, t, text_only):
    """True if the task involves vision: it declares a visual input modality (ctx.mm_input),
    ships a visual_rubrics.json, or tags any criterion with a non-text modality. Used to gate
    the vision bar so it doesn't fire on genuinely text-only tasks."""
    mm = str(ctx.get("mm_input") or "").upper().strip()
    text_vals = {str(v).upper() for v in t.get("text_task_mm_values", ["TEXT_ONLY", "TEXT", "NONE", ""])}
    if mm and mm not in text_vals:
        return True
    if ctx.get("visual_rubrics"):
        return True
    return any(c.get("modality") and c["modality"] != text_only for c in (ctx.get("rubric") or []))


def run(ctx, cfg):
    t = cfg["thresholds"]["weight_mix"]
    rub = ctx.get("rubric") or []
    if not rub:
        return []
    acc_types = _acc_types(t)
    text_only = t.get("text_only_modality_value", "TEXT_ONLY")
    pos = [c for c in rub if isinstance(c.get("weight"), (int, float)) and c["weight"] > 0]
    total_w = sum(c["weight"] for c in pos)
    if total_w <= 0:
        return []
    # Prefer the rubric tagger's semantic "accuracy" bucket (judged from criterion text) when it has
    # run; otherwise fall back to the authored `type` tag. This fixes accuracy% on tasks whose factual
    # criteria were mistagged (e.g. a value-extraction tagged "task completion").
    use_bucket = any(c.get("bucket") for c in pos)

    def _is_acc(c):
        return (c.get("bucket") == "accuracy") if use_bucket else (c.get("type") in acc_types)

    acc_w = sum(c["weight"] for c in pos if _is_acc(c))
    vis_w = sum(c["weight"] for c in pos if c.get("modality") and c["modality"] != text_only)
    vis_acc_w = sum(c["weight"] for c in pos
                    if _is_acc(c) and c.get("modality") and c["modality"] != text_only)

    acc_frac = acc_w / total_w
    vis_frac = vis_w / total_w
    vis_of_acc = (vis_acc_w / acc_w) if acc_w > 0 else 0.0

    tier = t.get("tier", "review_recommended")
    out = []
    ev = (f"accuracy={acc_frac:.0%} of total (w={acc_w}/{total_w}); "
          f"vision={vis_frac:.0%} of total; vision-of-accuracy={vis_of_acc:.0%}; "
          f"accuracy_source={'tagger-bucket' if use_bucket else 'type:' + str(sorted(acc_types))}")

    if acc_frac < t["accuracy_min_frac_of_total"]:
        out.append(finding(
            "weight_mix", "WEIGHT_MIX", tier,
            f"Accuracy rubrics are {acc_frac:.0%} of total rubric weight, below the "
            f"{t['accuracy_min_frac_of_total']:.0%} bar. Non-accuracy criteria are over-weighted.",
            fix=f"Downweight non-accuracy criteria (or add accuracy criteria) until accuracy "
                f">= {t['accuracy_min_frac_of_total']:.0%} of total weight.",
            evidence=ev))

    vis_ok = (vis_of_acc >= t["vision_min_frac_of_accuracy"]) and (vis_frac >= t["vision_min_frac_of_total"])
    apply_vision_bar = _is_visual_task(ctx, t, text_only) if t.get("require_visual_task", True) else True
    if apply_vision_bar and not vis_ok:
        out.append(finding(
            "weight_mix", "WEIGHT_MIX", tier,
            f"Vision rubrics are {vis_of_acc:.0%} of the accuracy mix ({vis_frac:.0%} of total), "
            f"below the {t['vision_min_frac_of_accuracy']:.0%}-of-accuracy "
            f"(>= {t['vision_min_frac_of_total']:.0%} of total) bar. "
            f"{'No criteria are tagged vision-dependent — check for modality mistagging.' if vis_w == 0 else ''}",
            fix="Add or up-weight vision-dependent accuracy criteria (and verify criteria that "
                "require reading an image aren't mistagged TEXT_ONLY).",
            evidence=ev))
    return out
