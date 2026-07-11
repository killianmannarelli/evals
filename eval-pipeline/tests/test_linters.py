"""Unit tests for the deterministic linters. Fixtures mirror the real rubric.json /
visual_rubrics.json / test_outputs.py shapes seen in OpenClaw bundles.

Each linter is tested for a POSITIVE (should flag) and NEGATIVE (should stay silent) case,
so tuning a threshold that breaks intent fails here.
"""
from src.common import load_config
from checks.linters import (weight_mix, pytest_hardcount, visual_sign, visual_vs_text,
                            overspec_exact, answer_key_data, negweight_ratio, visual_capacity)

CFG = load_config()


def ctx(**kw):
    base = dict(task_id="t", rubric=[], visual_rubrics=None, test_code=None, test_weights={},
                instruction="", reward={"mean_reward": None, "crit_pass_rate": {}}, service_data={})
    base.update(kw)
    return base


# ── weight_mix ────────────────────────────────────────────────────────────────
def test_weight_mix_flags_low_accuracy_and_zero_vision_on_visual_task():
    # IMAGE task with zero vision-tagged criteria => the vision bar legitimately fires (mistag).
    rub = [{"criteria": "did X", "weight": 5, "type": "task completion", "modality": "TEXT_ONLY"},
           {"criteria": "did Y", "weight": 5, "type": "instruction following", "modality": "TEXT_ONLY"},
           {"criteria": "value is 42", "weight": 2, "type": "factuality and hallucination", "modality": "TEXT_ONLY"}]
    out = weight_mix.run(ctx(rubric=rub, mm_input="IMAGE"), CFG)
    assert any("Accuracy" in f["explanation"] for f in out)   # 2/12 = 17% < 60%
    assert any("Vision" in f["explanation"] for f in out)     # 0% vision on a visual task
    assert all(f["defect_type"] == "WEIGHT_MIX" for f in out)


def test_weight_mix_text_only_task_skips_vision_bar():
    # Genuinely text-only task (no visual input, no visual criteria) => vision bar must NOT fire.
    rub = [{"criteria": "value is 42", "weight": 7, "type": "factuality and hallucination", "modality": "TEXT_ONLY"},
           {"criteria": "did X", "weight": 3, "type": "task completion", "modality": "TEXT_ONLY"}]
    out = weight_mix.run(ctx(rubric=rub, mm_input="TEXT_ONLY"), CFG)
    assert not any("Vision" in f["explanation"] for f in out)  # gated off on text-only tasks
    assert out == []                                           # accuracy is 70% >= 60% => fully silent


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
    assert out[0]["tier"] == "review_recommended"   # heuristic: raises a review flag, not a lone Fail


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
    assert out[0]["tier"] == "review_recommended"   # heuristic: raises a review flag, not a lone Fail


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


# ── negweight_ratio (§9g) ─────────────────────────────────────────────────────
def test_negweight_flags_zero_negatives():
    rub = [{"criteria": "a", "weight": 5}, {"criteria": "b", "weight": 3}, {"criteria": "c", "weight": 1}]
    out = negweight_ratio.run(ctx(rubric=rub), CFG)
    assert out and out[0]["tier"] == "action_required" and "ZERO" in out[0]["explanation"]


def test_negweight_silent_when_in_band():
    # 1 of 4 = 25% negative -> in [25%,30%] band -> clean
    rub = [{"criteria": "a", "weight": 5}, {"criteria": "b", "weight": 3},
           {"criteria": "c", "weight": 1}, {"criteria": "d", "weight": -3}]
    assert negweight_ratio.run(ctx(rubric=rub), CFG) == []


# ── false-positive guards (heuristic tightening, 2026-07-09) ─────────────────────
def test_visual_sign_silent_on_valid_positive_constraints():
    # "must not contain PII" / "without errors" are valid POSITIVE criteria, not sign errors.
    rub = [{"criteria": "The response must not contain PII", "weight": 3},
           {"criteria": "Agent completes the task without errors", "weight": 4}]
    assert visual_sign.run(ctx(rubric=rub), CFG) == []


def test_pytest_hardcount_silent_on_zero_and_non_count():
    # `== 0` ("no errors") is a valid assertion; `account`/`_is_correct` are not counts.
    code = "def test_result_is_correct():\n    assert error_count == 0\n    assert account == 5\n"
    assert pytest_hardcount.run(ctx(test_code=code), CFG) == []


def test_overspec_silent_on_colon_and_mustbe_word():
    # A colon or "must be <word>" is not an exact-value overspec, even when empirically hard.
    rub = [{"criteria": "Agent must be polite: greets the user by name", "weight": 3,
            "pass_rate_gpt": 0.1, "pass_rate_opus": 0.2}]
    assert overspec_exact.run(ctx(rubric=rub), CFG) == []


def test_overspec_flags_mustbe_number_when_hard():
    # but "must be <number>" that both models rarely pass IS overspec
    rub = [{"criteria": "The total must be 42 units", "weight": 3, "pass_rate_gpt": 0.0, "pass_rate_opus": 0.1}]
    out = overspec_exact.run(ctx(rubric=rub), CFG)
    assert out and out[0]["defect_type"] == "RUBRIC_OVERSPEC"


# ── visual_capacity (weak MM dependence — low visual capacity needed) ────────────
def test_visual_capacity_flags_multimodal_task_with_text_only_rubric():
    # a video/audio task where every criterion is TEXT_ONLY -> 0% visual -> weak MM dependence
    rub = [{"criteria": "identifies the student as Emma", "weight": 5, "modality": "TEXT_ONLY"},
           {"criteria": "uses the requested output format", "weight": 5, "modality": "TEXT_ONLY"}]
    out = visual_capacity.run(ctx(rubric=rub, mm_input="video, audio"), CFG)
    assert out and out[0]["defect_type"] == "LOW_VISUAL_CAPACITY"


def test_visual_capacity_silent_when_visuals_carry_weight():
    rub = [{"criteria": "reads the value shown in the chart", "weight": 7, "modality": "REQUIRE_VISUAL_UNDERSTANDING"},
           {"criteria": "uses the requested output format", "weight": 3, "modality": "TEXT_ONLY"}]
    assert visual_capacity.run(ctx(rubric=rub, mm_input="IMAGE"), CFG) == []


def test_visual_capacity_exempts_text_only_task():
    # a genuine text-only task legitimately needs no visual capacity -> NOT a defect
    rub = [{"criteria": "the value is 42", "weight": 5, "modality": "TEXT_ONLY"}]
    assert visual_capacity.run(ctx(rubric=rub, mm_input="TEXT_ONLY"), CFG) == []


def test_visual_capacity_uses_tagger_accuracy_scope():
    # tagger buckets present -> measure the visual share of the ACCURACY criteria. Accuracy is
    # TEXT_ONLY while the visual weight sits on a formatting criterion -> accuracy is 0% visual -> flag.
    rub = [{"criteria": "states the correct submission date", "weight": 5, "modality": "TEXT_ONLY", "bucket": "accuracy"},
           {"criteria": "thumbnail is a valid PNG", "weight": 5, "modality": "REQUIRE_VISUAL_UNDERSTANDING", "bucket": "formatting"}]
    out = visual_capacity.run(ctx(rubric=rub, mm_input="IMAGE"), CFG)
    assert out and out[0]["defect_type"] == "LOW_VISUAL_CAPACITY"
    assert "accuracy-criteria weight" in out[0]["evidence"]
