"""visual_capacity — flag (nominally) MULTIMODAL tasks that need LOW visual capacity.

A task with images/video/audio-visual inputs whose rubric weight barely requires actually reading
those visuals could largely be solved blind — weak MM dependence (the OpenClaw "Prompt - MM
dependence" defect). Text-only tasks are EXEMPT: 0 visual capacity is expected there, not a defect.

Deterministic from the per-criterion `modality` tag. When the 5-bucket rubric tagger has run (its
label is attached to each criterion as `bucket`), the visual share is measured over the ACCURACY
criteria only — i.e. how much of the *correctness* actually depends on vision — which is the sharper
signal and robust to modality mistags being exactly what's under review.
"""
from src.common import finding


def _mm_is_visual(mm, text_vals):
    mm = str(mm or "").upper().strip()
    return bool(mm) and mm not in text_vals


def run(ctx, cfg):
    t = cfg["thresholds"]["visual_capacity"]
    rub = ctx.get("rubric") or []
    text_only = t.get("text_only_modality_value", "TEXT_ONLY")
    text_vals = {str(v).upper() for v in t.get("text_task_mm_values", ["TEXT_ONLY", "TEXT", "NONE", ""])}
    pos = [c for c in rub if isinstance(c.get("weight"), (int, float)) and c["weight"] > 0]
    total = sum(c["weight"] for c in pos)
    if total <= 0:
        return []

    def is_visual(c):
        return bool(c.get("modality")) and c["modality"] != text_only

    # Only a (nominally) multimodal task can be "low visual capacity"; a genuine text task isn't.
    task_visual = (_mm_is_visual(ctx.get("mm_input"), text_vals)
                   or bool(ctx.get("visual_rubrics"))
                   or any(is_visual(c) for c in pos))
    if not task_visual:
        return []

    # Measure the visual share of the relevant weight. If the rubric tagger ran, restrict to the
    # ACCURACY criteria (correctness that depends on vision); otherwise use all positive weight.
    scope, basis = pos, "all rubric weight"
    if t.get("use_tagger_accuracy", True) and any(c.get("bucket") for c in pos):
        acc = [c for c in pos if c.get("bucket") == "accuracy"]
        if acc:
            scope, basis = acc, "accuracy-criteria weight (rubric tagger)"
    denom = sum(c["weight"] for c in scope)
    if denom <= 0:
        return []
    vis_w = sum(c["weight"] for c in scope if is_visual(c))
    vc = vis_w / denom
    bar = t.get("min_visual_frac", 0.15)
    if vc >= bar:
        return []
    return [finding(
        "visual_capacity", "LOW_VISUAL_CAPACITY", t.get("tier", "review_recommended"),
        f"Multimodal task (mm_input={ctx.get('mm_input')!r}) but only {vc:.0%} of {basis} requires "
        f"visual understanding (bar {bar:.0%}) — the rubric can largely be satisfied without the "
        f"images/video (weak MM dependence). Often the visually-dependent criteria are mistagged TEXT_ONLY.",
        fix="Add or up-weight criteria that require reading the visual inputs, or re-tag the "
            "visually-dependent criteria (several may be mislabeled TEXT_ONLY).",
        evidence=f"visual_weight={vis_w}/{denom} ({basis}); mm_input={ctx.get('mm_input')}")]
