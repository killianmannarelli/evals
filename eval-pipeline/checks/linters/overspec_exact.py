"""overspec_exact — exact-value criteria that likely over-penalize valid alternatives.

The customer flagged rubrics demanding exact timestamps / long decimals where a range is
defensible (e.g. "R16 expects exact timestamp matches -> relax to ranges"). Pure text can't
prove over-specification, so we require TWO signals to keep precision high:
  (1) the criterion text demands an exact value (markers: exactly / exact / must equal / a
      timestamp mm:ss / a >=3-decimal number), AND
  (2) the criterion is empirically hard — both reference models pass it rarely
      (pass_rate <= pass_rate_ceiling), using per-criterion pass rate from the real grading
      (reward.crit_pass_rate) or the static pass_rate_gpt/opus fields.
review_recommended tier (needs human judgment on whether a range is acceptable).
"""
import re
from src.common import finding

_TS = re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\b")
_DECIMAL3 = re.compile(r"\b\d+\.\d{3,}\b")
# "must be <number/currency>" (e.g. "must be 42", "must be $84.87") — precise replacement for the
# dropped broad "must be " substring marker, so "must be polite" no longer counts as exact.
_MUSTBE_NUM = re.compile(r"must\s+be\s+(?:exactly\s+)?[-+$]?\d", re.I)


def _pass_rate(ctx, c):
    # prefer the real per-criterion pass rate from grading; else static model fields
    cpr = (ctx.get("reward") or {}).get("crit_pass_rate") or {}
    title = c.get("criteria") or c.get("title") or ""
    if title in cpr:
        return cpr[title]
    rates = [c.get("pass_rate_gpt"), c.get("pass_rate_opus")]
    rates = [r for r in rates if isinstance(r, (int, float))]
    return max(rates) if rates else None


def run(ctx, cfg):
    t = cfg["thresholds"]["overspec_exact"]
    markers = [m.lower() for m in t.get("exact_value_markers", [])]
    ceil = t.get("pass_rate_ceiling", 0.30)
    tier = t.get("tier", "review_recommended")
    out = []
    for i, c in enumerate(ctx.get("rubric") or []):
        if not isinstance(c, dict):
            continue
        text = c.get("criteria") or c.get("title") or ""
        low = text.lower()
        has_exact = (any(m in low for m in markers) or bool(_TS.search(text))
                     or bool(_DECIMAL3.search(text)) or bool(_MUSTBE_NUM.search(text)))
        if not has_exact:
            continue
        pr = _pass_rate(ctx, c)
        if pr is not None and pr <= ceil:
            out.append(finding(
                "overspec_exact", "RUBRIC_OVERSPEC", tier,
                f"Rubric R{i+1} demands an exact value and both reference models pass it rarely "
                f"(pass_rate={pr:.0%} <= {ceil:.0%}) — likely over-specified where a range is defensible.",
                fix="Accept a tolerance/range for this target (or move exact-match to an LLM-graded "
                    "criterion that can reason about acceptable variance).",
                rubric_ids=[i + 1], evidence=f"{text[:120]!r} pass_rate={pr}"))
    return out
