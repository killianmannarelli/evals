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
"""
from src.common import finding


def _acc_types(t):
    types = list(t.get("accuracy_types", []))
    if t.get("count_optional_as_accuracy"):
        types += list(t.get("accuracy_types_optional", []))
    return set(types)


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
    acc_w = sum(c["weight"] for c in pos if c.get("type") in acc_types)
    vis_w = sum(c["weight"] for c in pos if c.get("modality") and c["modality"] != text_only)
    vis_acc_w = sum(c["weight"] for c in pos
                    if c.get("type") in acc_types and c.get("modality") and c["modality"] != text_only)

    acc_frac = acc_w / total_w
    vis_frac = vis_w / total_w
    vis_of_acc = (vis_acc_w / acc_w) if acc_w > 0 else 0.0

    tier = t.get("tier", "review_recommended")
    out = []
    ev = (f"accuracy={acc_frac:.0%} of total (w={acc_w}/{total_w}); "
          f"vision={vis_frac:.0%} of total; vision-of-accuracy={vis_of_acc:.0%}; "
          f"accuracy_types={sorted(acc_types)}")

    if acc_frac < t["accuracy_min_frac_of_total"]:
        out.append(finding(
            "weight_mix", "WEIGHT_MIX", tier,
            f"Accuracy rubrics are {acc_frac:.0%} of total rubric weight, below the "
            f"{t['accuracy_min_frac_of_total']:.0%} bar. Non-accuracy criteria are over-weighted.",
            fix=f"Downweight non-accuracy criteria (or add accuracy criteria) until accuracy "
                f">= {t['accuracy_min_frac_of_total']:.0%} of total weight.",
            evidence=ev))

    vis_ok = (vis_of_acc >= t["vision_min_frac_of_accuracy"]) and (vis_frac >= t["vision_min_frac_of_total"])
    if not vis_ok:
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
