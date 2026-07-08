"""answer_key_data — rubric answer-key numbers that appear NOWHERE in the mock-API data.

The customer repeatedly caught "R2 claims $84.87 ... actual fintrack data is $78.40" — an
answer-key value contradicting (or absent from) the service data the agent reads. We extract
currency amounts (and salient standalone numbers) from each criterion's text and check whether
they occur in ANY mock-service data.json. A graded amount present nowhere in the data is a
strong RUBRIC_INACCURATE / DATA_SPARSE signal.

Conservative by design (avoid false positives): only currency-style amounts ($1,234.56) and
numbers with >= min_number_len digits; a criterion is flagged only when NONE of its extracted
amounts appear in the data blob. Requires ctx.service_data (raw text of the data files).
"""
import re
from src.common import finding

_MONEY = re.compile(r"\$\s?\d[\d,]*(?:\.\d{1,2})?")
_NUM = re.compile(r"\b\d[\d,]*\.\d+\b|\b\d{2,}\b")


def _norm_money(s):
    return s.replace("$", "").replace(",", "").replace(" ", "").rstrip(".0") or s.replace("$", "").replace(",", "").strip()


def run(ctx, cfg):
    blob = "\n".join((ctx.get("service_data") or {}).values())
    if not blob:
        return []          # no data files surfaced — skip (don't false-positive)
    t = cfg["thresholds"]["answer_key_data"]
    tier = t.get("tier", "review_recommended")
    aggregate = [m.lower() for m in t.get("aggregate_markers", [])]
    require_cents = t.get("require_cents", True)
    blob_norm = blob.replace(",", "")
    out = []
    for i, c in enumerate(ctx.get("rubric") or []):
        if not isinstance(c, dict):
            continue
        text = c.get("criteria") or c.get("title") or ""
        low = text.lower()
        if any(m in low for m in aggregate):
            continue                      # aggregates are computed, not looked up — skip
        moneys = _MONEY.findall(text)
        if require_cents:
            moneys = [m for m in moneys if "." in m]   # only cents-precision (likely direct lookups)
        if not moneys:
            continue                      # only adjudicate criteria that assert a direct currency amount
        present = []
        for m in moneys:
            num = m.replace("$", "").replace(",", "").strip()
            # match the numeric substring in the (comma-stripped) data blob
            if num and (num in blob_norm or num.rstrip("0").rstrip(".") in blob_norm):
                present.append(m)
        if not present and len(moneys) >= 1:
            out.append(finding(
                "answer_key_data", "RUBRIC_INACCURATE", tier,
                f"Rubric R{i+1} grades against currency value(s) {moneys} that appear nowhere in "
                f"the mock-API data the agent can read — the answer key is likely wrong or the "
                f"data is missing.",
                fix="Reconcile the rubric's expected amount with the actual service data "
                    "(fintrack/etc.), or add the supporting record so the value is derivable.",
                rubric_ids=[i + 1], evidence=f"amounts={moneys} not found in service data"))
    return out
