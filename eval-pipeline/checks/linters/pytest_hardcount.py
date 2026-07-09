"""pytest_hardcount — flag brittle exact-count assertions in tests/test_outputs.py.

The customer flagged tasks like `test_field_corrections_count_is_six` /
`test_severity_matrix_has_three_scored_nail_rows` where a pytest asserts an EXACT count,
so a correct-but-different-shaped output fails. We detect:
  - `== <int>` / `!= <int>` comparisons on len(...) or a *count*/*rows*/*len* variable
  - test function names of the form `..._is_<number|word>` / `..._count_...`
Tier escalates to action_required when the task's mean_reward is low (brittle test likely
suppressing correct answers).
"""
import re
from src.common import finding

# Tightened 2026-07-09 to cut false positives:
#  - the count-word must be a token (leading underscore or bare "rows") so "account"/"discount"
#    no longer match; and the compared value must be >= 1 so `error_count == 0` ("no errors",
#    a valid assertion) no longer fires.
#  - the NAME regex is now "exactly"-only (high precision); number-word names are covered by
#    _WORD_NUM and the assertion itself by _LEN_EQ, so bare `_is_`/`_has_` (over-broad) are gone.
_LEN_EQ = re.compile(r"(len\s*\([^)]*\)|\b\w*_(?:count|counts|rows|len|num|items|entries)\b|\brows\b)\s*(==|!=)\s*([1-9]\d*)", re.I)
_NAME_NUM = re.compile(r"def\s+(test_\w*_exactly_\w*)\s*\(", re.I)
_WORD_NUM = re.compile(r"def\s+(test_\w*_(?:is|has|of)_(?:one|two|three|four|five|six|seven|eight|nine|ten)\b\w*)", re.I)


def run(ctx, cfg):
    code = ctx.get("test_code")
    if not code:
        return []
    t = cfg["thresholds"]["pytest_hardcount"]
    reward = (ctx.get("reward") or {}).get("mean_reward")
    low = reward is not None and reward < t.get("action_if_reward_below", 0.0)
    tier = "action_required" if low else t.get("count_assert_tier", "review_recommended")

    hits = []
    for m in _LEN_EQ.finditer(code):
        hits.append(f"`{m.group(0).strip()}`")
    names = set(m.group(1) for m in _NAME_NUM.finditer(code)) | set(m.group(1) for m in _WORD_NUM.finditer(code))
    if not hits and not names:
        return []
    detail = []
    if names:
        detail.append("exact-count test(s): " + ", ".join(sorted(names)[:6]))
    if hits:
        detail.append("hardcoded count assertion(s): " + "; ".join(hits[:6]))
    return [finding(
        "pytest_hardcount", "RUBRIC_OVERSPEC", tier,
        "tests/test_outputs.py contains exact-count assertions that fail a correct-but-"
        "different-shaped output. " + " | ".join(detail)
        + (f" Task mean_reward={reward:.2f} (low) — the brittle count may be suppressing correct answers." if low else ""),
        fix="Relax the exact-count assertion to a range / '>=' bound, or delete it if a rubric "
            "already covers the requirement.",
        test_names=sorted(names)[:8], evidence=" | ".join(detail))]
