"""visual_vs_text — the same criterion appearing in BOTH visual_rubrics.json and
tests/rubric.json with a diverging sign/target (the customer flagged "align visual_rubrics.json
Rn to match the text rubric Rn").

Match criteria across the two files by normalized-title similarity; if a matched pair disagrees
on sign (one rewards, one penalizes) flag it. No-op when a task has no visual_rubrics.json.
"""
import difflib, re
from src.common import finding


def _norm(s):
    return re.sub(r"[^a-z0-9 ]", "", (s or "").lower()).strip()


def _sign(c):
    if "is_positive" in c or "score" in c:
        sc = c.get("score")
        if c.get("is_positive") is True or (isinstance(sc, (int, float)) and sc > 0):
            return 1
        if c.get("is_positive") is False or (isinstance(sc, (int, float)) and sc < 0):
            return -1
    w = c.get("weight")
    if isinstance(w, (int, float)):
        return 1 if w > 0 else (-1 if w < 0 else 0)
    return 0


def run(ctx, cfg):
    vis = ctx.get("visual_rubrics")
    txt = ctx.get("rubric") or []
    if not vis or not txt:
        return []
    t = cfg["thresholds"]["visual_vs_text"]
    thr = t.get("title_match_min", 0.85)
    tier = t.get("tier", "action_required")
    txt_titles = [(_norm(c.get("criteria") or c.get("title") or ""), c) for c in txt]
    out = []
    for i, vc in enumerate(vis):
        if not isinstance(vc, dict):
            continue
        vt = _norm(vc.get("criteria") or vc.get("title") or vc.get("description") or "")
        if not vt:
            continue
        best, bestc = 0.0, None
        for nt, tc in txt_titles:
            r = difflib.SequenceMatcher(None, vt, nt).ratio()
            if r > best:
                best, bestc = r, tc
        if best >= thr and bestc is not None:
            if _sign(vc) and _sign(bestc) and _sign(vc) != _sign(bestc):
                out.append(finding(
                    "visual_vs_text", "RUBRIC_CONTRADICTION", tier,
                    f"Visual rubric R{i+1} and its matching text rubric grade the same criterion "
                    f"with opposite sign (visual sign={_sign(vc)}, text sign={_sign(bestc)}). "
                    "The two grading passes contradict each other.",
                    fix="Align visual_rubrics.json and tests/rubric.json to the same sign/target "
                        "for this criterion (or remove the duplicate).",
                    rubric_ids=[i + 1], evidence=f"visual: {vt[:80]!r} ~ text: {best:.2f}"))
    return out
