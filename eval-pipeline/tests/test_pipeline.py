"""Unit tests for the pipeline CORE LOGIC (previously untested): stage4 verdict rollup + dedupe +
redaction, resume harvest normalization + dimension→defect mapping, the attempt_id cache, the
recall/precision backtest, and the human-sheet row/confidence builder. Complements test_linters.py.
"""
import copy
import json

from src import common
from src import stage4_assemble as s4
from src import resume, cache, backtest
from src import stage5_human as s5

CFG = common.load_config()


# ── stage4: verdict rollup / dedupe / redaction / full rollup ───────────────────
def test_verdict_rule_tier_max():
    rule = CFG["taxonomy"]["verdict_rule"]
    def f(t): return {"tier": t}
    assert s4._verdict([f("action_required"), f("review_recommended")], rule) == "fail"
    assert s4._verdict([f("review_recommended")], rule) == "non-fail"
    assert s4._verdict([], rule) == "pass"


def test_dedupe_collapses_identical():
    a = {"defect_type": "X", "rubric_ids": [1], "test_names": [], "explanation": "same issue text here"}
    out = s4._dedupe([a, dict(a), {"defect_type": "Y", "rubric_ids": [2], "test_names": [], "explanation": "other"}])
    assert len(out) == 2


def test_redact_answer_key_field():
    r = s4._redact("look at why_rubric_is_correct for the gold")
    assert "why_rubric_is_correct" not in r and "rubric-justification" in r


def test_stage4_full_rollup(tmp_path):
    (tmp_path / "digest.json").write_text(json.dumps({
        "T1": {"attempt_id": "a1", "layer": 10, "category": "C", "subcategory": "S", "mm_input": "IMAGE", "reward": {"mean_reward": 0.2}},
        "T2": {"attempt_id": "a2", "layer": 10, "category": "C", "subcategory": "S", "mm_input": "TEXT", "reward": {"mean_reward": 0.9}},
    }))
    (tmp_path / "findings_linters.json").write_text(json.dumps({
        "T1": [{"check": "negweight_ratio", "defect_type": "RUBRIC_UNFAIR", "tier": "action_required",
                "rubric_ids": [], "test_names": [], "explanation": "zero negatives", "fix": "add penalties"}],
        "T2": [],
    }))
    (tmp_path / "findings_llm.json").write_text(json.dumps({
        "T2": [{"check": "cdq_static", "defect_type": "RUBRIC_AMBIGUOUS", "tier": "review_recommended",
                "rubric_ids": [], "test_names": [], "explanation": "vague", "fix": "clarify"}]}))
    rep = s4.main(CFG, tmp_path)
    v = {t["task_id"]: t["verdict"] for t in rep["tasks"]}
    assert v == {"T1": "fail", "T2": "non-fail"}
    assert rep["totals"]["fail"] == 1 and rep["totals"]["non_fail"] == 1
    assert rep["tasks"][0]["task_id"] == "T1"          # fail + low-reward sorts first
    assert rep["hygiene"]["clean"] is True


# ── resume: mapping + harvest normalization ─────────────────────────────────────
def test_dim2defect_exact_map():
    assert resume._dim2defect("Input Artifacts - Leak Prevention") == "ORACLE_LEAK"
    assert resume._dim2defect("Rubric Criteria - Rubric Structure") == "WEIGHT_MIX"
    assert resume._dim2defect("Tests - Correctness") == "GRADER_BROKEN"
    assert resume._dim2defect("Rubric Criteria - Rubric Spot Checks") == "RUBRIC_INACCURATE"


def test_flag2defect_reason_aware():
    d = "Rubric Criteria - Overall Rubric Quality - Major"
    assert resume._flag2defect(d, "the criterion is ambiguous, multiple readings") == "RUBRIC_AMBIGUOUS"
    assert resume._flag2defect(d, "contradicts the data in the CSV") == "RUBRIC_CONTRADICTION"
    assert resume._flag2defect(d, "demands an exact value; should be a range") == "RUBRIC_OVERSPEC"


def test_harvest_audit_and_cdq_from_outfile(tmp_path):
    ao = tmp_path / "aud.output"
    ao.write_text(json.dumps({"result": [{"task_id": "T1", "verdict": "Fail", "confidence": 80, "agreement": "1 grader",
        "why": "leaked", "flags": [{"dimension": "Input Artifacts - Leak Prevention", "category": "[Fail - Leak]",
        "severity": "Fail", "reason": "answer reachable", "fix": "remove", "spec_ref": "§"}]}]}))
    aud = resume.harvest_audit(str(ao), None)
    assert aud["T1"][0]["defect_type"] == "ORACLE_LEAK"
    assert aud["T1"][0]["tier"] == "action_required"
    assert aud["T1"][0]["flag_dimension"] == "Input Artifacts - Leak Prevention"

    co = tmp_path / "cdq.output"
    co.write_text(json.dumps({"result": [{"task_id": "T1", "findings": [{"tier": "review_recommended",
        "defect_type": "RUBRIC_AMBIGUOUS", "rubric_ids": [1], "test_names": [], "explanation": "x", "fix": "y"}]}]}))
    cdq = resume.harvest_cdq(str(co), None)
    assert cdq["T1"][0]["check"] == "cdq_static" and cdq["T1"][0]["defect_type"] == "RUBRIC_AMBIGUOUS"


# ── cache: skip / seed / update round-trip ──────────────────────────────────────
def test_cache_update_seed_skip(tmp_path):
    cfg = copy.deepcopy(CFG)
    cfg["pipeline"]["cache"] = {"enabled": True, "file": str(tmp_path / "cache.json")}
    rd = tmp_path / "run1"; rd.mkdir()
    (rd / "digest.json").write_text(json.dumps({"T1": {"attempt_id": "a1"}, "T2": {"attempt_id": "a2"}}))
    (rd / "findings_llm.json").write_text(json.dumps({"T1": [{"check": "cdq_static", "defect_type": "X",
        "tier": "review_recommended", "explanation": "e", "fix": ""}]}))
    (rd / "drawer.json").write_text(json.dumps({"T1": {"task_id": "T1", "verdict": "Non-Fail", "confidence": 70,
        "flags": [], "why": "w", "agreement": "a"}}))
    (rd / "report.json").write_text(json.dumps({"tasks": [{"task_id": "T1", "verdict": "non-fail"},
        {"task_id": "T2", "verdict": "pass"}]}))
    assert cache.update(cfg, rd) == 1                    # only T1 got an LLM result
    assert "T1" in cache.load(cfg) and "T2" not in cache.load(cfg)

    rd2 = tmp_path / "run2"; rd2.mkdir()
    (rd2 / "digest.json").write_text(json.dumps({"T1": {"attempt_id": "a1"}, "T2": {"attempt_id": "CHANGED"}}))
    assert cache.cached_ids(cfg, json.loads((rd2 / "digest.json").read_text())) == {"T1"}
    assert cache.seed(cfg, rd2) == {"T1"}
    assert json.loads((rd2 / "skip_llm.json").read_text()) == ["T1"]
    assert "T1" in json.loads((rd2 / "findings_llm.json").read_text())


# ── backtest: recall / precision / F1 ───────────────────────────────────────────
def test_backtest_recall_precision(tmp_path):
    gold = {"n_tasks": 2, "n_findings": 3, "tasks": {
        "T1": [{"defect_type": "RUBRIC_CONTRADICTION", "tier": "action_required", "rubric_ids": [1]},
               {"defect_type": "RUBRIC_AMBIGUOUS", "tier": "review_recommended", "rubric_ids": [2]}],
        "T2": [{"defect_type": "DATA_SPARSE", "tier": "review_recommended", "rubric_ids": []}]}}
    (tmp_path / "gold.json").write_text(json.dumps(gold))
    (tmp_path / "report.json").write_text(json.dumps({"tasks": [
        {"task_id": "T1", "verdict": "fail", "findings": [{"defect_type": "RUBRIC_CONTRADICTION"}, {"defect_type": "WEIGHT_MIX"}]},
        {"task_id": "T3", "verdict": "pass", "findings": []}]}))
    res = backtest.run(str(tmp_path / "gold.json"), str(tmp_path / "report.json"))
    assert res["overlap"] == 1 and res["task_recall"] == 1.0
    assert res["defect_recall"] == 0.5                  # CONTRADICTION matched, AMBIGUOUS missed
    assert abs(res["precision"] - 0.5) < 1e-9           # TP=1 of ours=2 (CONTRADICTION, WEIGHT_MIX)


# ── stage5_human: row + cross-lens confidence ───────────────────────────────────
def test_stage5_row_confidence_and_normalize():
    human = CFG["taxonomy"].get("human_label", {})
    t = {"task_id": "T1", "attempt_id": "att", "verdict": "fail", "category": "C", "subcategory": "S",
         "mm_input": "IMAGE", "mean_reward": 0.2, "low_reward": True, "findings": [
             {"check": "negweight_ratio", "defect_type": "RUBRIC_UNFAIR", "tier": "action_required", "explanation": "zero neg.", "fix": "add"},
             {"check": "cdq_static", "defect_type": "RUBRIC_AMBIGUOUS", "tier": "review_recommended", "explanation": "vague.", "fix": "clarify"}]}
    drawer = {"T1": {"verdict": "Fail", "confidence": 80, "agreement": "a", "why": "bad",
                     "flags": [{"category": "[Fail - x]", "dimension": "D"}]}}
    row, lenses = s5._row(t, drawer, human, "http://v/")
    assert row[0] == "FAIL"                             # verdict normalized to upper
    assert lenses == 3 and row[1].startswith("High")    # linter + cdq + drawer all flagged
    assert row[2] == "T1" and row[-1] == "http://v/att"


def test_stage5_first_sentence_and_label():
    assert s5._first_sentence("First one. Second one.") == "First one."
    assert s5._label({"flag_dimension": "Rubric Criteria - X"}, {}) == "Rubric Criteria - X"
    assert s5._label({"defect_type": "RUBRIC_AMBIGUOUS"}, {"RUBRIC_AMBIGUOUS": "Ambiguous"}) == "Ambiguous"
