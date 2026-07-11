"""Check registry. A check is any module exposing `run(ctx, cfg) -> list[finding]`.

`ctx` (built by stage2) per task:
  task_id, attempt_id, layer, category, subcategory, mm_input, task_type,
  rubric        : list[{criteria, weight, type, modality, pass_rate_gpt, pass_rate_opus}]
  visual_rubrics: list[{title/criteria, is_positive, score, ...}] | None
  test_code     : str (tests/test_outputs.py) | None
  test_weights  : {test_name: weight}
  instruction   : str | None
  reward        : {mean_reward, weighted_score, n_runs, crit_pass_rate:{title:frac}}
  service_data  : {service_name: raw_text}   (mock-API data.json, for answer_key_data)
  task_dir      : path to environment/ tree

LLM checks (cdq_static, audit_hybrid31) are NOT here — they are emitted as Workflow scripts
by checks/llm/*.py and harvested via src/resume.py. This registry is the deterministic linters.
"""
from checks.linters import (
    weight_mix, pytest_hardcount, visual_sign, visual_vs_text, overspec_exact, answer_key_data,
    negweight_ratio, visual_capacity,
)

LINTERS = {
    "weight_mix": weight_mix.run,
    "pytest_hardcount": pytest_hardcount.run,
    "visual_sign": visual_sign.run,
    "visual_vs_text": visual_vs_text.run,
    "overspec_exact": overspec_exact.run,
    "answer_key_data": answer_key_data.run,
    "negweight_ratio": negweight_ratio.run,   # §9g — the drawer's negative-weight flag
    "visual_capacity": visual_capacity.run,   # weak MM dependence — low visual capacity needed
}

LLM_CHECKS = {"cdq_static", "audit_hybrid31", "rubric_tagger"}


def run_linters(ctx, cfg, enabled):
    """Run each enabled linter over one task ctx; return flat list of findings (check-tagged)."""
    out = []
    for name in enabled:
        fn = LINTERS.get(name)
        if not fn:
            continue
        try:
            out.extend(fn(ctx, cfg) or [])
        except Exception as e:  # a linter bug must never sink a run
            out.append({"check": name, "defect_type": "LINTER_ERROR", "tier": "review_recommended",
                        "rubric_ids": [], "test_names": [], "explanation": f"linter {name} errored: {e}",
                        "fix": "", "evidence": ""})
    return out
