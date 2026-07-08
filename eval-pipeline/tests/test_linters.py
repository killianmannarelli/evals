"""Unit tests for the deterministic linters. Fixtures mirror the real rubric.json /
visual_rubrics.json / test_outputs.py shapes seen in OpenClaw bundles.

Each linter is tested for a POSITIVE (should flag) and NEGATIVE (should stay silent) case,
so tuning a threshold that breaks intent fails here.
"""
from src.common import load_config
from checks.linters import (weight_mix, pytest_hardcount, visual_sign, visual_vs_text,
                            overspec_exact, answer_key_data)

CFG = load_config()


def ctx(**kw):
    base = dict(task_id="t", rubric=[], visual_rubrics=None, test_code=None, test_weights={},
                instruction="", reward={"mean_reward": None, "crit_pass_rate": {}}, service_data={})
    base.update(kw)
    return base


# ── weight_mix ────────────────────────────────────────────────────────────────
def test_weight_mix_flags_low_accuracy_and_zero_vision():
    rub = [{"criteria": "did X", "weight": 5, "type": "task completion", "modality": "TEXT_ONLY"},
           {"criteria": "did Y", "weight": 5, "type": "instruction following", "modality": "TEXT_ONLY"},
           {"criteria": "value is 42", "weight": 2, "type": "factuality and hallucination", "modality": "TEXT_ONLY"}]
    out = weight_mix.run(ctx(rubric=rub), CFG)
    kinds = {f["explanation"].split()[0] for f in out}
    assert any("Accuracy" in f["explanation"] for f in out)   # 2/12 = 17% < 60%
    assert any("Vision" in f["explanation"] for f in out)     # 0% vision
    assert all(f["defect_type"] == "WEIGHT_MIX" for f in out)


def test_weight_mix_silent_when_compliant():
    rub = [{"criteria": "img value", "weight": 7, "type": "factuality and hallucination", "modality": "REQUIRE_VISUAL_UNDERSTANDING"},
           {"criteria": "other", "weight": 3, "type": "task completion", "modality": "TEXT_ONLY"}]
    # accuracy 7/10=70% >=60%; vision-of-accuracy 7/7=100%; vision-of-total 70% -> compliant
    assert weight_mix.run(ctx(rubric=rub), CFG) == []


# ── pytest_hardcount ──────────────────────────────────────────────────────────
def test_pytest_hardcount_flags_exact_count():
    code = "def test_field_corrections_count_is_six():\n    assert len(rows) == 6\n"
    out = pytest_hardcount.run(ctx(test_code=code, reward={"mean_reward": 0.2, "crit_pass_rate": {}}), CFG)
    assert out and out[0]["defect_type"] == "RUBRIC_OVERSPEC"
    assert out[0]["tier"] == "action_required"    # low reward escalates


def test_pytest_hardcount_silent_on_clean_tests():
    code = "def test_output_exists():\n    assert path.exists()\n    assert len(rows) >= 1\n"
    assert pytest_hardcount.run(ctx(test_code=code), CFG) == []


# ── visual_sign ───────────────────────────────────────────────────────────────
def test_visual_sign_flags_positive_on_undesired():
    vr = [{"title": "Agent incorrectly hallucinated a price", "is_positive": True, "score": 3}]
    out = visual_sign.run(ctx(visual_rubrics=vr), CFG)
    assert out and out[0]["rubric_ids"] == [1]


def test_visual_sign_flags_positive_weight_penalty_text():
    rub = [{"criteria": "The report should not include fabricated data", "weight": 4}]
    out = visual_sign.run(ctx(rubric=rub), CFG)
    assert out and "positive weight" in out[0]["explanation"]


def test_visual_sign_silent_on_correct_signs():
    vr = [{"title": "Agent correctly listed all items", "is_positive": True, "score": 3}]
    rub = [{"criteria": "The report should not fabricate data", "weight": -3}]
    assert visual_sign.run(ctx(visual_rubrics=vr, rubric=rub), CFG) == []


# ── visual_vs_text ────────────────────────────────────────────────────────────
def test_visual_vs_text_flags_opposite_sign():
    vr = [{"title": "Thumbnail shows the final chisel frame", "is_positive": True, "score": 3}]
    rub = [{"criteria": "Thumbnail shows the final chisel frame", "weight": -3}]
    out = visual_vs_text.run(ctx(visual_rubrics=vr, rubric=rub), CFG)
    assert out and out[0]["defect_type"] == "RUBRIC_CONTRADICTION"


def test_visual_vs_text_noop_without_visual():
    assert visual_vs_text.run(ctx(rubric=[{"criteria": "x", "weight": 3}]), CFG) == []


# ── overspec_exact ────────────────────────────────────────────────────────────
def test_overspec_flags_exact_and_hard():
    rub = [{"criteria": "Reading 2's time is logged as exactly 2:50", "weight": 3,
            "pass_rate_gpt": 0.0, "pass_rate_opus": 0.1}]
    out = overspec_exact.run(ctx(rubric=rub), CFG)
    assert out and out[0]["defect_type"] == "RUBRIC_OVERSPEC"


def test_overspec_silent_when_models_pass():
    rub = [{"criteria": "time is exactly 2:50", "weight": 3, "pass_rate_gpt": 0.9, "pass_rate_opus": 0.8}]
    assert overspec_exact.run(ctx(rubric=rub), CFG) == []


# ── answer_key_data ───────────────────────────────────────────────────────────
def test_answer_key_flags_missing_amount():
    rub = [{"criteria": "North Haven Gardens purchase for $84.87", "weight": 3}]
    data = {"fintrack": '{"amount": -78.40, "merchant": "North Haven Gardens"}'}
    out = answer_key_data.run(ctx(rubric=rub, service_data=data), CFG)
    assert out and out[0]["defect_type"] == "RUBRIC_INACCURATE"


def test_answer_key_silent_when_amount_present():
    rub = [{"criteria": "purchase for $78.40", "weight": 3}]
    data = {"fintrack": '{"amount": -78.40}'}
    assert answer_key_data.run(ctx(rubric=rub, service_data=data), CFG) == []
