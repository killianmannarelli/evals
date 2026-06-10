#!/usr/bin/env python3
"""
QC AUDITOR BULLETPROOF GATES — v2 BETA (2026-05-23)
====================================================

⚠️  BETA — runs alongside v1 (preaudit_checks.py). Same CLI surface; richer
output schema. Designed after the 2026-05-23 audit retro where the v1 gates
missed real defects on 3 of 6 tasks (T2 ratings inversion, T4 Wikimedia
clinical photo, T6 hidden 'so' conjunction) and made false-PASS calls.

Design choices (locked in with the user 2026-05-23):

  1. **Recall-tuned**: gates fire on softer signals with an explicit
     `confidence` field (`high` | `medium` | `low`). Master/swarm down-grade
     low-confidence findings rather than missing them entirely.

  2. **Score grounding**: pulls the platform's auto-score (eval scoreboard
     or step-QualityMeasurement) and computes the delta against the gate's
     audit verdict band. If audit says PASS but score is <30%, that's an
     audit miss; if audit says FAIL and score >80%, that's likely a
     rubric-not-contributor defect (rubric over-graded a real failure).

  3. **Per-criterion attribution**: each criterion's defects become first-
     class findings carrying `criterion_id`, `severity`, `rule_anchor`
     (§9a-Rule-C / §14f / §17 / etc.), `evidence_snippet`, `confidence`.
     The previous rollup-only output is preserved as `per_dim_summary` for
     backward compatibility.

New gates added in v2 (vs v1's 7):

  Gate 1  — Active rubric step (unchanged)
  Gate 2  — Trajectory inspection (unchanged; parser already fixed in v1)
  Gate 3  — Atomicity per-criterion attribution (RECALL-TUNED, per-criterion findings)
  Gate 5  — Category mismatch (unchanged)
  Gate 6  — Coverage cross-check (unchanged with markdown-link normalization)
  Gate 7  — Contributor-note leak detection (expanded patterns)

  Gate 8  — REMOVED 2026-05-23 — Tests dims 8a-d out of scope on this skill,
            verifier.py presence is no longer relevant. See openclaw_dimensions.md §8.

  Gate 9  — NEW: Hidden-conjunction atomicity — catches 'so'/'hence'/
            'therefore'/'thus'/'thereby' joining independent assertions

  Gate 10 — NEW: Semantic ratings sanity heuristic — detects suspicious
            ratings patterns (all-Present with empty/templated justifications,
            cross-wired justification text, rating contradicts justification)

  Gate 11 — NEW: Safety artifact heuristic — scans `zip_folder` / `source_screenshot`
            filenames + descriptions for medical / PII / Wikimedia / Commons /
            clinical indicators that suggest real-PII risk

  Gate 12 — NEW: Score grounding — pulls auto-score from eval scoreboard,
            computes delta_class (matched | inflated | deflated) against the
            audit's verdict band, emits an informational finding

  Gate 13 — NEW: Prompt→rubric coverage walk heuristic — extracts imperative
            verbs from prompt + desired_outcome (must / should / include /
            send / create / verify / ensure / etc.) and checks each
            imperative is referenced by at least one rubric criterion title

  Gate 15 — v2.1: Negative-criterion ratio (spec target 25-30% negative)
  Gate 16 — v2.1: Weight calibration — weights must be in {-5,-3,-1,+1,+3,+5}
  Gate 17 — v2.1: SSoT contradiction — desired_outcome numerics vs rubric

  Gate 18 — v2.3 (2026-05-31): Image-grounding. Closes the image-grounding gate
            gap — no other gate inspects the PIXELS a criterion asserts facts
            about. Two parts:
            (A) phantom-filename — a criterion referencing an INPUT image that
                is absent from the task's input artifacts is a Major Incorrect-
                Criteria error (forced; spec: Overall Rubric Quality - Major).
            (B) emits `image_gold_vision_queue` + advisory "correctness PENDING
                vision" for every criterion asserting a fact about an EXISTING
                input image, so image-derived golds are never auto-PASSed by the
                gate. Input manifest is best-effort: QC_IMAGE_GATE_EXTRACT_ROOT
                (reuse a pre-extracted dir) → zip namelist over the network
                (QC_IMAGE_GATE_FETCH=0 disables). Manifest unavailable → Part A
                is skipped (never false-positives), Part B still emitted.

Output schema (different from v1):

    {
      "task_path": str,
      "v": "2.0-beta",
      "active_rubric_step": str | None,

      "per_criterion_findings": [   # ← NEW — first-class per-criterion findings
        {
          "criterion_id": str,
          "criterion_title_preview": str,
          "dim": "6a" | "6b" | "6c" | ... ,
          "severity": "major" | "moderate" | "minor",
          "rule_anchor": "§9a-RuleC" | "§14f" | "§9b" | "§9f-RuleA" | ...,
          "kind": str,                              # short label
          "evidence_snippet": str,                  # ~120-char excerpt
          "confidence": "high" | "medium" | "low",  # ← gate's self-assessed certainty
          "should_dedup_against": [criterion_id]    # if §9h MECE overlap
        }, ...
      ],

      "per_dim_summary": {       # ← rolled up from per_criterion_findings for verdict math
        "6a": {"score": 2|3|5|None, "major_pct": float, "..."},
        "6b": ..., ...
      },

      "gate_9_hidden_conjunctions": {"matches": [...]},
      "gate_10_safety_heuristic": {"risk_indicators": [...]},
      "gate_11_score_grounding": {"auto_score_pct": float | None, "audit_verdict_band": str, "delta_class": str},
      "gate_12_prompt_coverage": {"imperatives": [...], "uncovered": [...]},

      "forced_findings": [...],   # ← top-level dim-rollup findings master inherits
      "advisory_findings": [...], # ← lower-confidence findings master may down-grade
      "informational": [...],     # ← informational only (score grounding, ratios)
    }

Usage (same as v1):

    python3 preaudit_checks_v2.py --task-json <path> --out <path-to-gates_v2.json>
    python3 preaudit_checks_v2.py --task-dir <dir> --out-dir <dir>

Trust note: this is BETA. Treat low-confidence findings as candidates needing
swarm confirmation. The master_auditor should be updated to read
`per_criterion_findings` and apply explicit confidence-based reconciliation.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# STRICT-STANCE CONFIG (2026-05-31, project-lead directive)
# ---------------------------------------------------------------------------
# Process-targeting criteria ("Before composing X, the trajectory consults Y";
# "the agent uses <tool> to ...") are DEMOTED to advisory by the customer's V6
# spec, which defers their major/moderate/minor categorization to a Rubric-
# Quality appendix not present in our spec dump. The project lead has directed
# the STRICT stance: count process-targeting as a Major rubric defect that
# drives the 6a/6b/6c bands and can force a FAIL.
#
# This DIVERGES from the customer's spec-literal grade (which would leave these
# advisory). On the 2026-05-31 L0 batch it moves the fail rate 26% -> 61%.
# Set to False to restore spec-literal behavior (process-targeting = advisory).
PROCESS_TARGETING_MAJOR = True


# ---------- shared helpers ----------------------------------------------------

JUSTIFICATION_FIELDS = [
    "incorrect_rubric_justification",
    "correct_answer_justification_rubric",
    "model_mistake_justification_rubric",
    "why_fail", "why-fail", "justification", "rubric_justification",
]


def _normalize_text(s: str) -> str:
    s = s.replace("\\_", "_").replace("\\.", ".").replace("\\-", "-")
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)  # markdown links → text
    s = s.replace("`", " ").replace("[", " ").replace("]", " ").replace("(", " ").replace(")", " ")
    return s.lower()


# ---------- gate 1: active rubric step (Rule 12, unchanged) -------------------

def gate1_active_rubric_step(before: dict) -> dict:
    candidates = []
    for sid, step in before.items():
        out = step.get("output", {}) if isinstance(step, dict) else {}
        if not isinstance(out, dict):
            continue
        crits = out.get("criteria")
        if not isinstance(crits, list) or not crits:
            continue
        is_builder = "RubricCriteriaBuilder" in sid or bool(re.match(r"^step-\d{13}-\w+$", sid))
        if not is_builder:
            continue
        crit_ids = [c["id"] for c in crits if isinstance(c, dict) and c.get("id")]
        candidates.append({
            "id": sid,
            "criteria_count": len(crits),
            "criterion_ids": set(crit_ids),
            "is_timestamped": bool(re.match(r"^step-\d{13}-", sid)),
        })

    rated_ids = set()
    for sid, step in before.items():
        out = step.get("output", {}) if isinstance(step, dict) else {}
        if not isinstance(out, dict):
            continue
        rr = out.get("responseRatings")
        if isinstance(rr, dict):
            for _c, ratings in rr.items():
                if isinstance(ratings, dict):
                    rated_ids.update(ratings.keys())

    for c in candidates:
        c["match_ratio"] = (len(c["criterion_ids"] & rated_ids) / max(len(c["criterion_ids"]), 1)) if rated_ids else 0.0

    full = [c for c in candidates if c["match_ratio"] >= 0.99]
    if len(full) == 1:
        return {"active_step_id": full[0]["id"], "verdict": "ok"}
    if len(full) > 1:
        ts_full = [c for c in full if c["is_timestamped"]]
        active = max(ts_full, key=lambda c: c["id"]) if ts_full else full[0]
        return {"active_step_id": active["id"], "verdict": "multiple_full_matches_used_latest_timestamp"}
    high = [c for c in candidates if c["match_ratio"] >= 0.5]
    if high:
        active = max(high, key=lambda c: c["match_ratio"])
        return {"active_step_id": active["id"], "verdict": f"partial_match_{active['match_ratio']:.0%}"}
    if not rated_ids and candidates:
        ts = [c for c in candidates if c["is_timestamped"]]
        active = max(ts, key=lambda c: c["id"]) if ts else candidates[0]
        return {"active_step_id": active["id"], "verdict": "no_rating_step_used_latest_timestamp"}
    return {"active_step_id": None, "verdict": "no_match"}


# ---------- gate 3 v2: per-criterion attribution with confidence --------------

BANNED_VOCAB = [
    # "prose" removed 2026-05-28 — can be legitimate rubric language (e.g.,
    # "any cell containing explanatory prose" as a negative single-entry check).
    "delve", "tapestry", "pivotal", "crucial", "comprehensive", "leveraging",
    "seamlessly", "robust", "streamline", "utilize", "facilitate",
    "meticulous", "foster", "garner", "showcase", "ensure", "enable",
    "long-horizon", "group-by", "playbook",
]
SUBJECTIVE_HEDGES = [
    "ambiguous", "unclear", "loosely", "roughly", "approximately", "somewhat",
    "looks good", "well-formatted", "clean", "clear", "best practices",
]
PROCESS_VERBS_BACKHALF = (
    r"\b(?:queries|opens|invokes|calls|searches|fetches|retrieves|"
    r"reads|references|inspects|considers|reviews|examines|decides|"
    r"verifies|demonstrates|attempts?|attempted|reading|referencing|"
    r"querying|calling|invoking|attempting|inspecting)\b"
)

# Hidden-conjunction connectives joining independent assertions
HIDDEN_CONJUNCTIONS = ["so ", "hence ", "therefore ", "thus ", "thereby ", "consequently "]


def _criterion_findings(c: dict, all_crits: list, dim_thresholds=None) -> list[dict]:
    """Return per-criterion finding dicts. Each finding has severity, rule_anchor,
    kind, evidence_snippet, confidence."""
    if not isinstance(c, dict):
        return []
    title = c.get("title") or ""
    cid = c.get("id") or title[:60]
    t = title.lower()
    findings = []

    def _add(severity, rule, kind, conf, snippet=None):
        findings.append({
            "criterion_id": cid,
            "criterion_title_preview": title[:160],
            "severity": severity,
            "rule_anchor": rule,
            "kind": kind,
            "evidence_snippet": (snippet or title[:140]),
            "confidence": conf,
        })

    # --- Process-targeting (§14f) ---
    if re.search(r"\btrajectory shows\b", t):
        # Recall-tuned: emit medium-confidence when back-half has process verb,
        # low-confidence when back-half is ambiguous (state vs process).
        if re.search(PROCESS_VERBS_BACKHALF, t):
            _add("major", "§14f", "process-targeting (trajectory shows <process-verb>)", "high")
        else:
            _add("major", "§14f", "process-targeting (trajectory shows ...)", "low",
                 snippet=f"'trajectory shows' phrasing — verify back-half: {title[:100]}")
    if re.search(r"\bin the trajectory[,]? the (?:agent|model) (?:reads|opens|invokes|calls|searches|fetches|retrieves|processes)\b", t):
        _add("major", "§14f", "process-targeting (sequencing of operations)", "high")
    if re.search(r"\btool[\- ]call\b|\bweb[\- ](?:search|fetch|lookup)\b", t) and \
       re.search(r"\bshows?\b|\bperforms?\b|\battempt", t):
        _add("major", "§14f", "process-targeting (names tool action)", "high")
    if re.search(r"\bbefore (?:deciding|composing|writing|inspecting|computing|beginning|starting|analyzing|writing)\b", t):
        _add("major", "§14f", "process-targeting (sequencing of operations)", "high")

    # --- Self-containment (§9f) ---
    if re.search(r"\blinked\b|\bthe (?:linked|provided) (?:page|url|product page|listing|file)\b", t) and \
       re.search(r"\bconsistent\b|\bmatch(es|ing)?\b|\bsame as\b", t):
        _add("major", "§9f-RuleA", "not self-contained (requires external URL/page verification)", "high")
    if re.search(r"\bcheck (?:the )?(?:url|link|page|site|server|attached)\b", t):
        _add("major", "§9f-RuleA", "not self-contained (requires evaluator to verify external resource)", "high")
    # Rule B — semantic determinacy (vague success markers)
    # Suppress when the criterion's "vague" phrase is in fact a prompt-anchored
    # named category (binary or enumerable). Detected by: the phrase contains a
    # word that also appears in the prompt as part of a "restrict/branch/choose"
    # construct, which signals a closed-category choice the criterion is referencing.
    # Conservative — only fires on the canonical vague-marker tokens themselves.
    if re.search(r"\b(?:the correct answer|properly|as expected|as described|the right value)\b", t):
        _add("major", "§9f-RuleB", "vague success marker — semantic determinacy", "high")
    # NOTE 2026-05-24: Patterns like "digital background processing adjustments"
    # or "physical re-shooting guidelines" are NOT flagged as §9f-RuleB vague
    # when they map to a prompt-defined closed binary/category. Reviewers and
    # specialists should cross-check the criterion's success-marker phrase
    # against the prompt's named-category list before flagging vague. See task
    # 6a076b30fb7ee59da499fd2f (ana_ramos) where the prompt explicitly defines
    # `digital post-processing tools` vs `physical re-shooting` as a closed
    # binary, anchoring both criterion phrases.

    # --- §9a SATURATION GUARDRAIL (added 2026-05-24) ---
    # Per quality_skill.md §9a Rule A:
    #   "Do not split when one part is a modifier, complement, or argument
    #    required to complete the meaning of the other."
    # Detect patterns where the AND'd / listed parts form ONE audit-state
    # assertion or ONE bookkeeping commitment, not N independent facts.
    saturation_patterns = [
        # "X and Y as the only Z" / "as the only Fails" — saturation modifier
        # constrains the set membership (one audit conclusion).
        r"\bas the only\b",
        # "X and Y as the unique Z" — same pattern, different verb.
        r"\bas the unique\b",
        # "are strictly avoided" / "is strictly required" — single compliance
        # commitment over an enumerated set.
        r"\b(?:are|is) strictly\b",
        # "all Criterions (A, B, C, and D)" / "all of the following" —
        # universal-quantifier audit-state, one verdict not N facts.
        r"\ball (?:criterions?|of the (?:following|items)|of these|four|five|six|seven|eight)\b",
        # "designates X and Y as Fails" / "marks X and Y as ..." — one audit
        # conclusion (the set, not N independent flags).
        r"\b(?:designates?|marks?|assigns?|flags?|labels?)\s+[^.]*?\s+as\s+[^.]+?(?:fails?|errors?|violations?|categories|verdict)\b",
        # "between X and Y" — anchor pair required for meaning.
        r"\bbetween\s+[\w./_`-]+\s+and\s+[\w./_`-]+\b",
        # "lists the processed images: X, Y, Z, and W" — single bookkeeping
        # commitment (the log is complete or it isn't).
        r"\b(?:lists?|enumerates?|specifies?|states?)\s+[^.]*?:\s*[\w./_`-]+",
        # "anchored to / pinned to / sourced from" — saturating attribution.
        r"\b(?:anchored|pinned|sourced)\s+to\s+\b",
        # --- ROW-LEVEL SPOT-CHECK pattern (added 2026-05-27 from Spot-Check
        # Rubrics OC post Draft.pdf) ---
        # "X.csv contains a <record-key> row where <field1> ..., <field2> ...,
        # and <field3> ..." is ONE audit assertion about that row's contents.
        # The ANDs join fields of the same record, not N independent facts.
        # The PDF explicitly endorses this as the recommended spot-check pattern.
        r"\b(?:row|entry|record|line|listing)\s+(?:where|with|containing|for|that)\b",
        # "contains a 207 Charm Dr row" — named-record reference even without "where"
        r"\b(?:contains|has|carries|includes)\s+(?:a|the|an)\s+[`\w./_-]+\s+(?:row|entry|record|line|listing)\b",
        # --- SCHEMA-CHECK / CLOSED-SET ENUMERATION pattern ---
        # "<file> parses as a CSV file and contains the columns A, B, C, D" —
        # the list is a closed-set §9a Rule A modifier; one schema/membership
        # assertion not N independent ones. Broadened 2026-05-27 to cover
        # "includes the exact category names …", "lists the allowed status
        # values …", "carries the option labels …" — any container-verb +
        # enumeration-noun idiom.
        r"\b(?:contains?|includes?|has|lists?|carries|enumerates?|specifies?|holds?|uses?|defines?|declares?)\s+"
            r"(?:the\s+)?"
            # Allow up to 4 modifier words between the verb and the enum-noun
            # ("includes individual current Amazon price entries").
            r"(?:[a-z][a-z0-9-]*\s+){0,4}"
            r"(?:columns?|fields?|keys?|headers?|"
                r"categor(?:y|ies)(?:\s+names?)?|"
                r"item\s+names?|"
                r"values?(?:\s+(?:set|list))?|"
                r"enum(?:\s+values?)?|"
                r"status\s+(?:values?|codes?)|"
                r"options?(?:\s+set)?|"
                r"labels?|types?|tags?|"
                r"entries|members|"
                r"allowed\s+values?|valid\s+values?|"
                r"variant\s+names?|sku\s+set|"
                r"price\s+entries|"
                r"records?|rows?|listings?|"
                r"line\s+items?"
            r")\b",
        r"\bparses?\s+as\s+a?n?\s*\w+\s+(?:file|format)\b",
        # Generic closed-set anchor: "the <enum-noun> set" / "the exact set of <X>"
        r"\bthe\s+(?:exact\s+)?set\s+of\s+(?:columns?|fields?|keys?|headers?|categor(?:y|ies)|status\s+values?|allowed\s+values?|valid\s+values?|labels?|entries)\b",
        # --- GROUPING / ASSIGNMENT closed-set idiom (added 2026-05-28) ---
        # "X groups the three photos (A, B, C) into the forearm group" —
        # single grouping assertion; the file list is a §9a Rule A modifier of
        # the verb. Same logic as Schema/Categories — N inputs, 1 grouping
        # target → one set-membership assertion.
        r"\b(?:groups?|categori[zs]es?|classifi(?:es|ed)|assigns?|maps?|sorts?|bins?|buckets?|allocates?|places?|files?\s+(?:into|under))\s+"
            r"(?:the\s+|these\s+|those\s+|all\s+)?"
            r"(?:two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|\d+|specified|listed|enumerated)?\s*"
            r"(?:photos?|images?|files?|items?|entries|records?|rows?|elements?|members|examples?|samples?|receipts?|inputs?|attachments?|artifacts?|values?|categor(?:y|ies))\b",
        # Grouping target marker: "into the <X> group/category/cluster/bucket/set"
        r"\binto\s+(?:the\s+)?[\w\s./_-]{1,40}?\s+(?:group|categor(?:y|ies)|cluster|bucket|set|class|type|bin|tier)\b",
        # --- CARDINAL-QUANTIFIED closed list (general) ---
        # "the three photos", "all four images", "exactly six receipts" —
        # the cardinal quantifier signals closed-set membership; whatever
        # verb operates on it operates on the set as a whole.
        r"\b(?:the|all|exactly|both|either)\s+(?:two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|\d+)\s+"
            r"(?:photos?|images?|files?|items?|entries|records?|rows?|columns?|elements?|members|receipts?|examples?|samples?|values?|categor(?:y|ies)|fields?|options?|labels?|attachments?)\b",
        # --- VOLUME-COUNT pattern ---
        # "contains exactly N records/rows" — single cardinality assertion.
        r"\bcontains\s+exactly\s+\d+\s+(?:records?|rows?|entries|items|files?)\b",
        # --- SPOT CHECK explicit marker (in case CB writes it in title) ---
        r"\bspot[\s-]?check\b",
        # --- PER-UNIT HOLISTIC CHECK (added 2026-05-29 from Spot-Check Rubrics
        # OC post Draft (2).pdf). "each/every/per <unit> ... <verb> ... A, B, C"
        # bundles the attributes of ONE representative unit (a lesson, a photo,
        # a discrepancy row, a worked problem). The customer doc endorses this
        # holistic per-unit check; the facet list is a Rule A modifier of one
        # record, NOT N independent field-split rubrics. ---
        r"\b(?:each|every|per)\s+(?:[a-z][a-z0-9-]*\s+){0,3}"
            r"(?:rows?|entr(?:y|ies)|records?|lines?|listings?|lessons?|summar(?:y|ies)|"
            r"problems?|exercises?|photos?|images?|items?|sections?|paragraphs?|meals?|"
            r"slots?|receipts?|products?|steps?|figures?|tables?|charts?|pages?|cells?)\b",
    ]
    saturation_hit = any(re.search(p, t, re.IGNORECASE) for p in saturation_patterns)

    # --- NAMED-INSTANCE HOLISTIC OBSERVATION (added 2026-05-29, (2) draft) ---
    # A criterion anchored to a specific named file/artifact AND using an
    # observation/depiction verb ("Monday_lunch.jpeg shows ...", "the report
    # states that IMG_4.png depicts ...") is a representative holistic spot check
    # of that one instance — the listed observations are that instance's fields,
    # not N independent assertions. Exempt from the Rule-A field-split sweep.
    _named_instance = re.search(
        r"`[^`]+`|\b[\w./_-]+\.(?:jpe?g|png|webp|gif|pdf|csv|md|txt|docx?|xlsx?|json)\b",
        title, re.IGNORECASE,
    )
    _obs_verb = re.search(
        r"\b(?:shows?|depicts?|displays?|presents?|identif(?:y|ies)|reflects?|"
        r"captures?|describes?|states?\s+that)\b",
        t,
    )
    if _named_instance and _obs_verb:
        saturation_hit = True

    # --- §9a atomicity: "for each" universal (Rule C) ---
    if re.search(r"\bfor each (?:of |)\b", t) and not saturation_hit:
        post = t.split("for each", 1)[1] if "for each" in t else ""
        facts = post.count(",") + (1 if " and " in post else 0) + 1
        if facts >= 4:
            _add("major", "§9a-RuleC", f"atomicity (for-each bundles ≈{facts} facts)", "high")
        elif facts >= 3:
            _add("moderate", "§9a-RuleC", f"atomicity (for-each bundles ≈{facts} facts)", "medium")
        else:
            _add("minor", "§9a-RuleC", "mild atomicity (for-each, 2 facts)", "medium")

    # --- §9a atomicity: backtick-list bundling ---
    # 2026-05-28 fix: STRIP parenthetical content before counting. Parens hold
    # evidence / clarification / (item, value) bookkeeping — not bundled
    # assertions. E.g., "MEMORY.md includes price entries for unverified
    # products (Hydro Flask as 44.95, Edifier as XX.XX, Sony as YY.YY)" is
    # ONE set-property assertion with parenthetical evidence. The list inside
    # parens should not be counted as N bundled facts.
    title_no_parens = re.sub(r"\([^)]*\)", "", title)
    t_no_parens = title_no_parens.lower()
    backticked = re.findall(r"`[^`]+`", title_no_parens)
    if not saturation_hit:
        if len(backticked) >= 4 and " and " in t_no_parens:
            _add("major", "§9a-RuleA", f"atomicity (bundles {len(backticked)} named items)", "high")
        elif len(backticked) == 3 and " and " in t_no_parens:
            _add("moderate", "§9a-RuleA", "atomicity (bundles 3 named items)", "medium")

    # --- §9a atomicity: multiple ANDs (kept for backwards compat) ---
    # 2026-05-28: count ANDs only OUTSIDE parens, same rationale.
    ands = len(re.findall(r"\band\b", t_no_parens))
    if not saturation_hit:
        if ands >= 4 and "for each" not in t_no_parens:
            _add("major", "§9a-RuleA", f"atomicity ({ands} ANDs)", "medium")
        elif ands >= 3 and "for each" not in t_no_parens and len(backticked) < 3:
            _add("moderate", "§9a-RuleA", f"atomicity ({ands} ANDs bundle independent facts)", "medium")

    # --- §9a atomicity NEW: bundled-clause detection (2026-05-23, refined; saturation-guarded 2026-05-24) -----
    # Skip the entire bundled-clause sweep when saturation applies.
    if saturation_hit:
        pass  # saturation-guarded; skip oxford-comma / continuation / pos+neg sweeps
    else:
        pass  # fall through to the existing logic below
    # NOTE: the original block below is gated on the `saturation_hit` check via the
    # `if "for each" not in t and len(backticked) < 3` line — we add `and not saturation_hit`.
    # Catches R11/R21/R25/R30-style bundling that the bare-AND-count missed.
    # Patches added 2026-05-23 after recall test against expert review:
    #   1. Rule B disjunction immunity: skip pure verb-list disjunctions
    #      ("resize, sharpen, enhance, or reprocess any photo") — these are
    #      §9a-Rule-B-immune (single truth-condition, multiple paths to it)
    #   2. Continuation-clause now fires on commas≥1 (R30 has only 1 comma)
    #   3. NEW: "X and Y, and Z" 3-clause-AND pattern (R11 has 1 comma + 2 ANDs)
    if "for each" not in t and len(backticked) < 3 and not saturation_hit:
        # Strip parens to avoid counting parenthetical asides as separate items
        stripped = re.sub(r"\([^)]*\)", "", t)
        sentences = re.split(r"\.(?:\s+|$)", stripped)
        any_flagged = False

        for sent in sentences:
            if any_flagged:
                break
            commas = sent.count(",")

            # --- Rule B Disjunction Immunity check ---
            # If the only conjunction is "or" between similar verbs (verb-list
            # disjunction "resize, sharpen, enhance, or reprocess"), this is
            # ATOMIC per §9a Rule B — don't flag.
            verb_list_disjunction = bool(re.search(
                r"\bto\s+\w+ing?\b.*,\s*\w+ing?\s*,?\s*(?:and|or)?\s*\w+\s*(?:or\s+\w+)?",
                sent
            )) and " or " in sent and " and " not in sent
            if verb_list_disjunction:
                continue  # Rule B immune — skip

            # Pattern: "X and Y, and Z" — 3 clauses joined by ANDs with comma between
            # Catches R11: "names a single winner and a single runner-up, and includes..."
            three_clause_and = bool(re.search(
                r"\band\s+[^,.]+,\s*and\s+", sent
            ))
            if three_clause_and:
                _add("moderate", "§9a-RuleA",
                     "atomicity (3-clause AND bundle — \"X and Y, and Z\")",
                     "high")
                any_flagged = True
                continue

            # Continuation-clause check (NOW fires on commas >= 1)
            # Catches R30: "rules out X and Y, citing Z" → 3 independent assertions
            continuation = bool(re.search(
                r",\s+(?:citing|while|that contains|that includes|and includes|"
                r"and three|and then|noting|stating|naming|listing|and uses|and the)\b",
                sent
            ))
            if continuation and commas >= 1:
                _add("moderate", "§9a-RuleA",
                     "atomicity (continuation-clause adds 3rd fact — \"X and Y, citing Z\")",
                     "medium")
                any_flagged = True
                continue

            # Rest of the rules need commas >= 2 (Oxford-comma style)
            if commas < 2:
                continue

            # Mixed pos+neg list: "X. does not contain Y, Z, or W"
            # R25-style: positive + multi-negative bundled
            neg_list = bool(re.search(
                r"\bdoes not (?:contain|include|have)\b[^.]*,[^.]*,", sent
            ))
            if neg_list:
                _add("moderate", "§9a-RuleA",
                     "atomicity (positive + multi-negative bundled — \"does not contain X, Y, or Z\")",
                     "high")
                any_flagged = True
                continue

            # Counted-list signal: "three numeric counts: A, B, and C"
            counted_list = bool(re.search(
                r"\b(?:two|three|four|five|six|seven|eight|nine|ten|\d+)\s+\w+\s*:\s*\S+",
                sent
            ))
            if counted_list:
                _add("moderate", "§9a-RuleA",
                     "atomicity (counted-list bundle — \"N items: A, B, and C\")",
                     "high")
                any_flagged = True
                continue

            # Oxford-comma fallback: "X, Y, ..., and Z" with 3+ items
            has_oxford = bool(re.search(r",\s+(?:and|or)\s+\w", sent))
            # Skip if the "or" is a Rule B disjunction (already filtered above
            # but belt-and-suspenders for the inner sentence loop)
            if " or " in sent and " and " not in sent.replace(", or ", ""):
                continue
            if has_oxford and commas >= 2:
                _add("moderate", "§9a-RuleA",
                     "atomicity (Oxford-comma list bundles ≥3 facts via \"X, Y, and Z\")",
                     "medium")
                any_flagged = True
                continue

    # --- §9a atomicity: hidden conjunctions (NEW gate 9) ---
    # V6 patch (L10 ground truth — dfd "Nespresso/Espresso" false positive):
    # use \bword\b regex instead of substring match so "so " doesn't match
    # the tail of "espresso" / "nespresso" / "also" etc.
    for connective in HIDDEN_CONJUNCTIONS:
        word = connective.strip()
        # \b at start ensures we're at the beginning of "so", "hence", etc.,
        # not in the middle of another word.
        if not re.search(rf"\b{re.escape(word)}\b\s", t):
            continue
        # Additional guard for "so": skip the adverbial-quantifier idioms
        # ("also so", "just so", "do so", "did so", "will so", "always so")
        if word == "so" and re.search(r"\b(also|just|do|did|will|always)\s+so\b", t):
            continue
        _add("moderate", "§9a-Hidden", f"hidden conjunction ('{word}' joins independent assertions)", "low",
             snippet=f"'{word}' in: {title[:120]}")
        break

    # --- §9b file-existence-only — DISABLED 2026-05-28 ---
    # OpenClaw no longer ships a pytest framework, so file-existence checks
    # belong in the rubric (matches PDF "Spot-Check Rubrics" Criterion #1
    # which recommends "File Existence Check" as the first rubric criterion).
    # The §9b rule that says "file-existence belongs in pytest" is obsolete.

    # --- §17 banned vocab ---
    for v in BANNED_VOCAB:
        if re.search(rf"\b{re.escape(v)}\b", t):
            _add("minor", "§17", f"banned vocab '{v}'", "high")
            break

    # --- §17 subjective qualifiers without anchor ---
    # 2026-05-28: respect paren-strip — "marks Meal 7 (ambiguous mixed bowl)
    # as Unverifiable" should NOT trigger on "ambiguous" because the term is
    # a parenthetical descriptor of the meal type, not the criterion's
    # judgment language.
    t_for_hedge = re.sub(r"\([^)]*\)", "", t)
    for hedge in SUBJECTIVE_HEDGES:
        if hedge in t_for_hedge:
            _add("moderate", "§17/§9f-RuleB", f"subjective qualifier '{hedge}' without anchored definition", "medium")
            break

    # --- §9h MECE overlap candidates (heuristic) ---
    # Refined 2026-05-27 per Spot-Check Rubrics OC post Draft.pdf:
    # The previous heuristic flagged any criterion sharing 4+ core words with
    # another — but multiple criteria on the SAME FILE legitimately share the
    # filename and scope tokens (the PDF's recommended pattern is 6+ criteria
    # all checking different facets of `gabriela_listing_audit.csv`). The fix:
    # treat any token appearing in ≥3 criteria as a SHARED-SCOPE anchor and
    # exclude it from overlap counting. After that filter, require ≥4 distinct
    # meaningful shared words to flag MECE candidate.
    STOPWORDS = {"the","and","with","from","this","that","into","over","their",
                 "than","must","shall","such","when","where","which","what",
                 "have","each","other","contains","contain","exactly","references"}

    # Compute corpus-frequent tokens once (shared-scope anchors)
    if not hasattr(_criterion_findings, "_corpus_cache"):
        _criterion_findings._corpus_cache = {}
    corpus_key = id(all_crits)
    common_tokens = _criterion_findings._corpus_cache.get(corpus_key)
    if common_tokens is None:
        from collections import Counter as _C
        token_counts = _C()
        for cr in all_crits:
            ot_full = (cr.get("title") or "").lower()
            # Include underscore-words (filename-like tokens) in frequency counts
            for w in re.findall(r"\b[a-z][a-z0-9_./]{3,}\b", ot_full):
                token_counts[w] += 1
        common_tokens = {w for w, n in token_counts.items() if n >= 3}
        _criterion_findings._corpus_cache[corpus_key] = common_tokens

    core_words = [w for w in re.findall(r"\b[a-z][a-z0-9_./]{3,}\b", t)
                  if w not in STOPWORDS and w not in common_tokens][:8]

    # --- Entity-identifier extraction (added 2026-05-28) ---
    # Per PDF spot-check pattern: criteria targeting different rows / meals /
    # records / files are MECE-distinct even when they share scope words.
    # Pull the criterion's distinguishing entity identifier(s).
    def _entity_ids(title_text):
        ids = set()
        # "Meal N" / "Receipt N" / "Row N" / "Order N" / "Image N" style
        # Entity word + numeric/alphanumeric-with-digit identifier.
        # IGNORECASE on the entity word but the ID must contain a digit so
        # we don't accidentally treat "Meal entry" as id=entry → all meals
        # would falsely share that ID.
        for m in re.findall(r"\b(meal|receipt|row|order|image|photo|item|line|entry|record|product)\s+(?:#\s*)?(\d+|[A-Za-z][\w-]{0,6}\d[\w-]{0,3})\b",
                            title_text, re.IGNORECASE):
            ids.add(f"{m[0].lower()}_{m[1].lower()}")
        # Filename-with-extension — DROPPED 2026-05-28: filenames are shared
        # rubric scope (most criteria of a meal_report.md rubric will all cite
        # meal_report.md), not distinguishing entity IDs. Including them caused
        # every criterion to share "meal_report.md" as an entity → disjoint
        # check always returned False → §9h fired anyway.
        # Row-key noun phrases like "207 Charm Dr", "5829 Evers Rd" —
        # number + capitalized noun + street suffix (tightened 2026-05-28 to
        # avoid matching "2026 FreshDirect" or similar date+company patterns
        # as row keys).
        for m in re.findall(r"\b(\d{2,5}\s+[A-Z][\w]+(?:\s+[A-Z]\w*){0,2}\s+(?:Dr|Rd|Ave|St|Blvd|Pl|Ln|Way|Hwy|Ct|Avenue|Street|Boulevard|Road|Drive|Lane))\b",
                            title_text):
            ids.add(m.lower())
        # Backticked named items that look like entity identifiers (capitalized brand/product names)
        for m in re.findall(r"`([A-Z][\w &.'/-]{2,40})`", title_text):
            # Trim long phrases
            ids.add(m.lower()[:60])
        return ids

    self_entities = _entity_ids(title)

    # Detect file-existence criteria (creates X / X exists / file named X)
    def _file_existence_target(title_text):
        t = title_text.lower()
        m = re.search(r"(?:creates|writes)\s+(?:a\s+)?file\s+(?:named\s+)?`?([\w._-]+\.[a-z]+)`?", t)
        if m: return m.group(1)
        m = re.search(r"(?:file|the file)\s+`?([\w._-]+\.[a-z]+)`?\s+(?:exists|is created|is present)", t)
        if m: return m.group(1)
        m = re.search(r"`([\w._-]+\.[a-z]+)`\s+exists", t)
        if m: return m.group(1)
        return None

    self_file_existence = _file_existence_target(title)

    overlapping = []
    if len(core_words) >= 4:  # need enough distinct content words to even consider overlap
        for other in all_crits:
            if other is c:
                continue
            ot = (other.get("title") or "").lower()
            shared = sum(1 for w in core_words if w in ot)
            if shared < 4:
                continue

            other_entities = _entity_ids(other.get("title") or "")
            other_file_existence = _file_existence_target(other.get("title") or "")

            # MECE-distinct exception A: both have per-record entity IDs and they're disjoint
            if self_entities and other_entities and not (self_entities & other_entities):
                continue

            # MECE-distinct exception B (added 2026-05-28): file-existence vs
            # row-content. If one criterion is a file-existence check and the
            # other is per-record content, they're checking different facets.
            if (self_file_existence and other_entities and not other_file_existence) \
               or (other_file_existence and self_entities and not self_file_existence):
                continue

            # MECE-distinct exception C: both are file-existence on DIFFERENT files
            if self_file_existence and other_file_existence and self_file_existence != other_file_existence:
                continue

            overlapping.append(other.get("id") or ot[:40])
    if overlapping:
        findings.append({
            "criterion_id": cid,
            "criterion_title_preview": title[:160],
            "severity": "moderate",
            "rule_anchor": "§9h",
            "kind": "MECE overlap candidate",
            "evidence_snippet": f"shares ≥4 non-scope content words with: {overlapping[:3]}",
            "confidence": "low",
            "should_dedup_against": overlapping,
        })

    return findings


def gate3_atomicity_v2(active_step_id, before) -> dict:
    if not active_step_id or active_step_id not in before:
        return {"verdict": "skip_no_active_step", "per_criterion_findings": [], "per_dim_summary": {}}

    out = before[active_step_id].get("output", {}) if isinstance(before[active_step_id], dict) else {}
    crits = out.get("criteria", []) if isinstance(out, dict) else []
    if not crits:
        return {"verdict": "skip_no_criteria", "per_criterion_findings": [], "per_dim_summary": {}}

    total = len(crits)
    pc_findings = []
    for c in crits:
        pc_findings.extend(_criterion_findings(c, crits))

    # Roll up: each criterion contributes its WORST severity once per V3 spec
    order = {"major": 0, "moderate": 1, "minor": 2}
    by_crit = {}
    for f in pc_findings:
        cid = f["criterion_id"]
        existing = by_crit.get(cid)
        if existing is None or order[f["severity"]] < order[existing["severity"]]:
            by_crit[cid] = f

    major = sum(1 for f in by_crit.values() if f["severity"] == "major")
    moderate = sum(1 for f in by_crit.values() if f["severity"] == "moderate")
    minor = sum(1 for f in by_crit.values() if f["severity"] == "minor")
    mod_or_maj = major + moderate
    any_sev = mod_or_maj + minor

    def _band_score(pct, fail_thresh, nonfail_thresh):
        if pct > fail_thresh:
            return 2
        elif pct > nonfail_thresh or pct > 0:
            return 3 if pct > 0 else 5
        return 5

    per_dim = {
        "6a": {
            "score": 2 if (major / total) > 0.10 else (3 if major else 5),
            "major_pct": round(major / total, 4),
            "major_count": major,
        },
        "6b": {
            "score": 2 if (mod_or_maj / total) > 0.15 else (3 if mod_or_maj and (major / total) < 0.05 else 5),
            "mod_or_maj_pct": round(mod_or_maj / total, 4),
        },
        "6c": {
            "score": 2 if (any_sev / total) > 0.20 else (3 if any_sev and (major / total) < 0.05 and (mod_or_maj / total) < 0.15 else 5),
            "any_pct": round(any_sev / total, 4),
        },
    }

    return {
        "verdict": "ok" if (major == 0 and moderate == 0) else "findings_present",
        "total_criteria": total,
        "major_count": major,
        "moderate_count": moderate,
        "minor_count": minor,
        "per_criterion_findings": pc_findings,
        "per_dim_summary": per_dim,
        "negative_weight_ratio": _neg_ratio(crits),
    }


def _neg_ratio(crits):
    neg = sum(1 for c in crits if isinstance(c.get("weight"), (int, float)) and c["weight"] < 0)
    return round(neg / max(len(crits), 1), 4)


# ---------- gate 5: category mismatch (unchanged from v1) ---------------------

CATEGORY_LEXICON = {
    "operations & qa": ["inventory", "audit", "receipt", "document", "ui", "form", "queue", "ticket"],
    "creative & media": ["moodboard", "image", "video", "design", "portfolio", "social", "post", "edit"],
    "visual learning": ["homework", "lab", "textbook", "lecture", "problem", "study", "exam"],
    "commerce & product": ["product", "listing", "shopping", "compare", "brand", "packaging", "sku"],
    "health & wellness": ["meal", "nutrition", "symptom", "skin", "calorie", "protein", "exercise"],
    "property & space": ["listing", "real estate", "vacancy", "tenant", "renovation", "interior"],
}
SUBCATEGORY_ANCHORS = {
    "inventory visual audit": ["inventory", "stock", "sku", "warehouse"],
    "nutrition/meal logging": ["meal", "nutrition", "calorie", "protein"],
    "skin/symptom triage": ["skin", "symptom", "rash", "lesion", "dermat"],
    "real estate listing review": ["listing", "vacancy", "tenant", "property"],
    "design/portfolio review": ["moodboard", "portfolio", "design", "image"],
    "visual shopping/comparison": ["shop", "compare", "price", "product", "lens", "barrel"],
    "homework/problem solving": ["homework", "problem", "solve", "study", "exam", "math"],
    "document/receipt processing": ["receipt", "invoice", "document"],
}


def gate5_category(before, active_step_id) -> dict:
    cat_step = None
    cat_value = ""
    for sid, step in before.items():
        out = step.get("output", {}) if isinstance(step, dict) else {}
        if isinstance(out, dict) and "category_subcategory" in out:
            cat_step = sid
            cat_value = out["category_subcategory"]
            break
    if not cat_value:
        return {"verdict": "no_category_field"}

    parts = re.split(r"\s*[-—]\s*", cat_value, maxsplit=1)
    category_main = parts[0].lower().strip()
    sub = parts[1].lower().strip() if len(parts) > 1 else ""

    blob = ""
    if active_step_id and active_step_id in before:
        out = before[active_step_id].get("output", {})
        for c in out.get("criteria", []):
            blob += " " + (c.get("title") or "")
    for sid, step in before.items():
        if sid.startswith("step-1771366239685") or "PromptInput" in sid:
            out = step.get("output", {}) if isinstance(step, dict) else {}
            for fv in out.values():
                if isinstance(fv, str):
                    blob += " " + fv
    blob_lower = blob.lower()

    lex = CATEGORY_LEXICON.get(category_main, [])
    hits = sum(1 for kw in lex if kw in blob_lower)
    hit_ratio = hits / max(len(lex), 1) if lex else 0

    anchor_hits = None
    if sub in SUBCATEGORY_ANCHORS:
        anchor_terms = SUBCATEGORY_ANCHORS[sub]
        anchor_hits = sum(1 for kw in anchor_terms if kw in blob_lower)

    # V6 (2026-05-27): detect silver_trajectory presence — dim 4a is optional.
    # If no silver_trajectory step exists, this gate produces ADVISORY only.
    silver_present = any(
        ("silvertrajectory" in sid.lower() or "silver_trajectory" in sid.lower()
         or "SilverTrajectory" in sid)
        for sid in before.keys()
    )

    # V6 patch (L10 ground truth):
    # - Trust anchor_hits >= 2: subcategory keyword evidence overrides empty lexicon
    # - When lexicon_total == 0, can't make a strong call from lexicon alone
    if anchor_hits is not None and anchor_hits >= 2:
        verdict = "ok"
    elif len(lex) == 0:
        verdict = "skip_no_lexicon"
    elif hits == 0 or anchor_hits == 0:
        verdict = "mismatch_strong"
    elif hit_ratio < 0.30:
        verdict = "mismatch_weak"
    else:
        verdict = "ok"

    return {
        "category_value": cat_value,
        "lexicon_hits": hits,
        "lexicon_total": len(lex),
        "subcategory": sub,
        "subcategory_anchor_hits": anchor_hits,
        "silver_trajectory_present": silver_present,
        "verdict": verdict,
    }


# ---------- gate 6: coverage cross-check (with markdown-link norm, unchanged) -

FILE_RE = re.compile(r"`?[\w./_-]+\.(?:md|csv|json|py|tar(?:\.gz)?|zip|txt|yml|yaml|sh)`?", re.IGNORECASE)


def gate6_coverage(active_step_id, before) -> dict:
    if not active_step_id or active_step_id not in before:
        return {"verdict": "skip"}
    required = set()
    for sid, step in before.items():
        if not sid.startswith("step-1771366239685"):
            continue
        out = step.get("output", {}) if isinstance(step, dict) else {}
        for fv in out.values():
            if not isinstance(fv, str):
                continue
            for m in FILE_RE.findall(fv):
                clean = m.strip("`").lower()
                if any(skip in clean for skip in ["http://", "https://", "example.com"]):
                    continue
                fn = clean.split("/")[-1]
                if fn:
                    required.add(fn)

    rubric_blob = ""
    crits = before[active_step_id].get("output", {}).get("criteria", [])
    for c in crits:
        rubric_blob += " " + (c.get("title") or "")
    rubric_norm = _normalize_text(rubric_blob)

    unscored = []
    for req in sorted(required):
        if req in rubric_norm:
            continue
        stem, _, ext = req.rpartition(".")
        if re.search(re.escape(stem) + r".{0,40}\." + re.escape(ext), rubric_norm):
            continue
        stem_parts = [p for p in stem.split("_") if len(p) > 2]
        if stem_parts:
            pat = r"\b" + r"[\s\W_]{0,8}".join(re.escape(p) for p in stem_parts) + r"[\s\W_]{0,30}\." + re.escape(ext)
            if re.search(pat, rubric_norm):
                continue
        unscored.append(req)

    return {
        "verdict": "missing_coverage" if unscored else "ok",
        "required_artifacts": sorted(required),
        "unscored_artifacts": unscored,
    }


# ---------- gate 7: contributor-note leak detection (unchanged) ---------------

LEAK_PATTERNS = [
    r"\bgive me the original\b",
    r"\btell me as well\b",
    r"\btrying to cause\b",
    r"\bfix it with the future\b",
    r"\b≥50%? threshold\b",
    r"\bwhich.{0,12}files can i delete\b",
    r"\b@/Users/[^\s]+\b",
    r"^Claude:|\bAs an AI\b",
    r"\bworking notes\b",
    r"\bTODO:|TODO\(",
]


def gate7_leaks(before) -> dict:
    leaks = []
    for sid, step in before.items():
        if not sid.startswith("step-1771366239685"):
            continue
        out = step.get("output", {}) if isinstance(step, dict) else {}
        for fk, fv in out.items():
            if not isinstance(fv, str):
                continue
            for pat in LEAK_PATTERNS:
                m = re.search(pat, fv, re.IGNORECASE)
                if m:
                    leaks.append({
                        "step": sid, "field": fk, "pattern": pat,
                        "excerpt": fv[max(0, m.start()-40):m.end()+40],
                    })
    return {"verdict": "ok" if not leaks else "leaks_found", "leaks": leaks}


# ---------- gate 2: trajectory (recall-tuned) ---------------------------------

TOOL_CATS = {
    "file_write": ["str_replace_editor", "create", "write_file", "edit_file", "Write", "Edit", "write", "edit"],
    "file_read":  ["read_file", "Read", "view", "read"],
    "shell":      ["bash", "Bash", "shell", "exec", "process"],
    "search":     ["grep", "search", "find", "memory_search"],
    "browser":    ["browser_navigate", "browser_click", "browser_fetch", "WebFetch", "browser"],
    "image":      ["read_image", "image_analyze", "ocr", "image", "pdf"],
    "calendar":   ["create_reminder", "schedule_event", "calendar"],
    "email":      ["send_email", "gmail", "send_message"],
    "web":        ["web_fetch", "web_search"],
}


def gate2_trajectory(before) -> dict:
    ae_step = None
    traj = []
    for sid, step in before.items():
        if "AgentExecution" not in sid:
            continue
        out = step.get("output", {}) if isinstance(step, dict) else {}
        if isinstance(out, dict) and isinstance(out.get("trajectory"), list):
            ae_step = sid
            traj = out["trajectory"]
            break
    if not traj:
        return {"verdict": "no_trajectory", "metrics": {}, "step_id": ae_step}

    tool_calls = []
    file_writes = []
    assistant_substantive = 0
    tool_results = 0
    for i, t in enumerate(traj):
        if not isinstance(t, dict):
            continue
        role = t.get("role")
        content = t.get("content")
        if role == "assistant":
            if isinstance(content, str) and content.strip() and "HEARTBEAT_OK" not in content:
                assistant_substantive += 1
            elif isinstance(content, list):
                for c in content:
                    if isinstance(c, dict) and c.get("type") == "text" and "HEARTBEAT_OK" not in c.get("text", ""):
                        assistant_substantive += 1
                    if isinstance(c, dict) and c.get("type") == "tool_use":
                        tool_calls.append((i, c.get("name", ""), c.get("input", {})))
            tc_list = t.get("tool_calls")
            if isinstance(tc_list, list):
                for tc in tc_list:
                    fn = tc.get("function") if isinstance(tc.get("function"), dict) else tc
                    name = fn.get("name", "")
                    args_raw = fn.get("arguments", "")
                    inp = {}
                    if isinstance(args_raw, str):
                        try:
                            inp = json.loads(args_raw)
                        except Exception:
                            pass
                    elif isinstance(args_raw, dict):
                        inp = args_raw
                    tool_calls.append((i, name, inp))
                    if any(p in name.lower() for p in ["write", "create_file", "edit", "str_replace"]):
                        path = inp.get("path") or inp.get("file_path") or inp.get("filename") or ""
                        file_writes.append((i, name, path))
                    if name.lower() in ("bash", "shell", "process"):
                        cmd = inp.get("command") or inp.get("cmd") or ""
                        if isinstance(cmd, str) and re.search(r"(^|[\s;&|])(echo|cat|printf|tee|cp|mv)\s+.*>+", cmd):
                            file_writes.append((i, name + " (shell)", cmd[:120]))
        elif role == "tool":
            tool_results += 1
            meta = t.get("metadata") if isinstance(t.get("metadata"), dict) else {}
            tn = meta.get("toolName")
            if tn and not any(name == tn for _, name, _ in tool_calls):
                tool_calls.append((i, tn, {}))

    cat_hits = {k: 0 for k in TOOL_CATS}
    for _i, name, _inp in tool_calls:
        for cat, pats in TOOL_CATS.items():
            if name.startswith("mcp__"):
                cat_hits.setdefault("mcp", 0)
                cat_hits["mcp"] += 1
                break
            if any(p in name for p in pats):
                cat_hits[cat] += 1
                break

    return {
        "step_id": ae_step,
        "verdict": "ok",
        "metrics": {
            "total_turns": len(traj),
            "assistant_substantive_turns": assistant_substantive,
            "tool_calls": len(tool_calls),
            "unique_tool_names": sorted(set(n for _, n, _ in tool_calls)),
            "file_writes": file_writes[:20],
            "tool_results": tool_results,
            "active_tool_categories": [k for k, n in cat_hits.items() if n > 0],
        },
    }


# ---------- gate 8: REMOVED 2026-05-23 (Tests dims out of scope) --------------

def _walk(obj, depth=0, max_depth=8):
    """Yield (key_path, value) from nested dicts/lists. Used for deep-scan
    when fields live at unpredictable paths inside step outputs."""
    if depth > max_depth:
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield (k, v)
            yield from _walk(v, depth + 1, max_depth)
    elif isinstance(obj, list):
        for item in obj:
            yield from _walk(item, depth + 1, max_depth)


# Gate 8 (verifier.py presence detection) REMOVED 2026-05-23.
# Tests dims 8a-8d are out of scope on this skill — see
# references/openclaw_dimensions.md §8 for the rationale.


# ---------- gate 10 (NEW): semantic ratings sanity heuristic ------------------

def gate10_ratings_sanity(before, active_step_id) -> dict:
    """Heuristic flag for ratings that 'look wrong' — all-Present with empty
    justifications, cross-wired justifications referencing other criterion IDs,
    or ratings that contradict their own justification text."""
    if not active_step_id:
        return {"verdict": "skip"}
    crit_titles = {}
    out = before.get(active_step_id, {}).get("output", {})
    for c in out.get("criteria", []):
        if isinstance(c, dict):
            crit_titles[c.get("id")] = c.get("title", "")

    findings = []
    # Find rating steps
    for sid, step in before.items():
        out = step.get("output", {}) if isinstance(step, dict) else {}
        rr = out.get("responseRatings") if isinstance(out, dict) else None
        if not isinstance(rr, dict):
            continue
        for cand_name, ratings in rr.items():
            if not isinstance(ratings, dict):
                continue
            # Count Present-with-empty-justification
            present_empty = 0
            present_total = 0
            cross_wired_candidates = []
            negation_inconsistencies = []
            for cid, rating_data in ratings.items():
                if not isinstance(rating_data, dict):
                    continue
                rating = rating_data.get("rating") or rating_data.get("score") or rating_data.get("value")
                just = rating_data.get("justification") or rating_data.get("rationale") or ""
                if not isinstance(just, str):
                    just = str(just)
                title = crit_titles.get(cid, "")
                if rating in ("present", "Present", 1, "1", True):
                    present_total += 1
                    if not just.strip() or len(just.strip()) < 10:
                        present_empty += 1
                    # Heuristic: if justification literally says "did not", "couldn't", "failed to" but rating says Present
                    if re.search(r"\b(?:did not|didn't|couldn't|failed to|never|absent|missing)\b", just.lower()):
                        if not re.search(r"\bnot present\b|\bdoes not apply\b", just.lower()):
                            negation_inconsistencies.append((cid, just[:120]))
                # Cross-wired check: justification mentions a different criterion's distinctive noun
                if title and len(title) > 30:
                    title_nouns = set(re.findall(r"\b[a-z]{5,}\b", title.lower()))
                    for other_cid, other_title in crit_titles.items():
                        if other_cid == cid or not other_title:
                            continue
                        other_nouns = set(re.findall(r"\b[a-z]{5,}\b", other_title.lower()))
                        distinctive = other_nouns - title_nouns
                        if distinctive and len(distinctive) >= 3:
                            matches_in_just = sum(1 for n in distinctive if n in just.lower())
                            if matches_in_just >= 3:
                                cross_wired_candidates.append((cid, other_cid))
                                break

            findings.append({
                "rating_step": sid,
                "candidate": cand_name,
                "present_with_empty_justification": present_empty,
                "present_total": present_total,
                "present_empty_pct": round(present_empty / max(present_total, 1), 3),
                "cross_wired_candidates_count": len(cross_wired_candidates),
                "negation_inconsistencies_count": len(negation_inconsistencies),
                "negation_examples": negation_inconsistencies[:3],
            })

    # Forced finding if heuristic strong
    risk = "low"
    for f in findings:
        if f["present_empty_pct"] > 0.30 or f["negation_inconsistencies_count"] >= 3 or f["cross_wired_candidates_count"] >= 3:
            risk = "high"
            break
        if f["present_empty_pct"] > 0.10 or f["negation_inconsistencies_count"] >= 1:
            risk = "medium" if risk != "high" else risk

    return {"verdict": risk, "ratings_findings": findings}


# ---------- gate 11 (NEW): safety artifact heuristic --------------------------

SAFETY_INDICATORS = {
    "medical": ["clinical", "patient", "diagnosis", "lesion", "rash", "dermat", "wound", "scar", "x-ray", "mri", "ct scan"],
    "pii": ["ssn", "social security", "passport", "license", "driver", "address", "phone", "email", "dob", "birthdate"],
    "wikimedia": ["wikimedia", "commons", "wikipedia", "creative commons"],
    "real_face": ["face", "portrait", "selfie", "headshot"],
    "minor": ["child", "minor", "student", "kid", "infant", "baby", "teen"],
    "financial": ["bank account", "credit card", "tax return", "w-2", "1099", "balance"],
}


def gate11_safety_heuristic(before) -> dict:
    """Scan story content for safety risk indicators.

    v2-fix (2026-05-23): added persona-context whitelist. When the story
    carries a fictional persona signal (`assigned_universe`, named characters
    like 'Gabriela'/'Sofia', synthetic-tag annotations), domain-appropriate
    financial / medical / face mentions don't elevate to high risk — they're
    expected fictional-narrative content. Real-PII risk requires either:
      (a) actual identifiable real-person data (real face + real name), OR
      (b) a real-world data source citation (Wikimedia/Commons/Wikipedia)
          for a medical/clinical image with no synthetic-substitution note.
    """
    blob = ""
    persona_signals = []
    for sid, step in before.items():
        if not sid.startswith("step-1771366239685"):
            continue
        out = step.get("output", {}) if isinstance(step, dict) else {}
        for fk, fv in out.items():
            if isinstance(fv, str):
                blob += " " + fv
                if fk == "assigned_universe" and fv:
                    persona_signals.append(("assigned_universe", fv))
            elif isinstance(fv, list):
                for item in fv:
                    if isinstance(item, dict):
                        blob += " " + " ".join(str(v) for v in item.values() if isinstance(v, str))
                    elif isinstance(item, str):
                        blob += " " + item
    blob_lower = blob.lower()

    # Persona-context whitelist: fictional first-names in OpenClaw universes
    # (these are the synthetic personas from the task taxonomy)
    fictional_personas = [
        "gabriela", "sofia", "amanda", "lorraine", "claire", "eric", "lisa",
        "aaliyah", "brandon", "richard", "adrian", "isaiah", "ana", "arjun",
        "jamal", "jessica", "amanda", "long_horizon", "francisco",
    ]
    persona_hits = sum(1 for p in fictional_personas if p in blob_lower)

    risk_indicators = {}
    for category, kws in SAFETY_INDICATORS.items():
        hits = [kw for kw in kws if kw in blob_lower]
        if hits:
            risk_indicators[category] = hits

    # V6 patch (L10 ground truth — task 6863): RFC 2606 reserved domains + NANP
    # fictional 555-01xx prefixes are documented-synthetic; they should NOT trip
    # the PII heuristic. Extract all email addresses + phone-like strings, and
    # if ALL of them are reserved/fictional, demote the pii indicator.
    email_re = re.compile(r"\b[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b")
    phone_re = re.compile(r"\b\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})\b")
    RFC2606_DOMAINS = {"example.com", "example.org", "example.net"}
    def _is_reserved_domain(d):
        dl = d.lower()
        return (dl in RFC2606_DOMAINS or dl.endswith(".example")
                or dl.endswith(".example.com") or dl.endswith(".example.org")
                or dl.endswith(".example.net"))
    emails_found = email_re.findall(blob)
    all_emails_reserved = bool(emails_found) and all(_is_reserved_domain(d) for d in emails_found)
    phones_found = phone_re.findall(blob)
    # 555-01xx is the canonical fictional-use prefix (NANP)
    all_phones_fictional = bool(phones_found) and all(
        m[0] == "555" and m[1].startswith("01") for m in phones_found
    )
    if risk_indicators.get("pii") and (all_emails_reserved or (not emails_found and all_phones_fictional)):
        # PII indicators are only on synthetic identifiers — drop the category
        del risk_indicators["pii"]
        risk_indicators["synthetic_pii_only"] = (
            (["RFC 2606 reserved domains"] if all_emails_reserved else []) +
            (["NANP fictional 555-01xx"] if all_phones_fictional else [])
        )

    # The key adjustment: persona-context downgrades risk
    has_persona_context = persona_hits >= 2 or persona_signals

    risk = "low"
    # External-source citation (Wikimedia/Commons) for medical content = HIGH
    # regardless of persona context. The Wikimedia hit is the smoking gun
    # because it implies a real-world data source rather than synthetic.
    if risk_indicators.get("medical") and risk_indicators.get("wikimedia"):
        risk = "high"
    # Medical + real-face WITHOUT persona context = HIGH (real clinical photo
    # of an identifiable person — §12 f2_medical + f6_real_faces compound)
    elif risk_indicators.get("medical") and risk_indicators.get("real_face") and not has_persona_context:
        risk = "high"
    # Medical + real-face WITH persona context = MEDIUM (likely synthetic narrative
    # mentioning "portrait" / "scar" in fictional context — defer to swarm review)
    elif risk_indicators.get("medical") and risk_indicators.get("real_face") and has_persona_context:
        risk = "medium"
    # PII / Minor concerns trump persona context (real-PII keywords like SSN,
    # passport, license are unambiguous and shouldn't be downgraded)
    elif risk_indicators.get("pii"):
        risk = "high"
    elif risk_indicators.get("minor") and not has_persona_context:
        risk = "medium"
    # Medical alone in persona context = LOW_MEDIUM (synthetic medical narrative)
    elif risk_indicators.get("medical") and has_persona_context:
        risk = "low_medium"
    elif risk_indicators.get("medical"):
        risk = "medium"
    # Financial in persona context = LOW (Frost Bank / Gabriela's balance is
    # fictional-narrative finance, not real PII)
    elif risk_indicators.get("financial") and has_persona_context:
        risk = "low"
    elif risk_indicators.get("wikimedia") or risk_indicators.get("real_face"):
        risk = "low_medium" if not has_persona_context else "low"
    elif risk_indicators.get("financial"):
        risk = "low_medium"

    return {
        "verdict": risk,
        "risk_indicators": risk_indicators,
        "persona_context": has_persona_context,
        "persona_hits": persona_hits,
        "persona_signals": persona_signals,
    }


# ---------- gate 12 (NEW): score grounding ------------------------------------

def gate12_score_grounding(before, audit_verdict_band=None, top_level=None) -> dict:
    """Pull auto-score from eval / QualityMeasurement / responseRatings / etc.

    v2-fix (2026-05-23): the score lives in several different paths across
    OpenClaw responses. Try each in priority order:
      1. step-QualityMeasurement-*.output.content with "(N%)" pattern
      2. step-*-*.output.responseRatings.<cand>.<crit_id>.* with rating numerics
         → aggregate weighted score
      3. Total weight of criteria with rating='present' / numeric weighted average
      4. top-level inline_form_data.eval.evaluations.* (when normalized)
    """
    score_pct = None
    score_source = None
    score_raw = None

    # Path 1: QualityMeasurement content (most common — has "9 / 92 (10%)" pattern)
    for sid, step in before.items():
        if "QualityMeasurement" not in sid:
            continue
        out = step.get("output", {}) if isinstance(step, dict) else {}
        content = out.get("content")
        if isinstance(content, str):
            m = re.search(r"(\d+)\s*/\s*(\d+)\s*\((\d+(?:\.\d+)?)\s*%\)", content)
            if m:
                score_pct = float(m.group(3))
                score_raw = f"{m.group(1)}/{m.group(2)}"
                score_source = sid
                break
            m2 = re.search(r"(\d+(?:\.\d+)?)\s*%", content)
            if m2:
                score_pct = float(m2.group(1))
                score_source = sid
                break

    # Path 2: aggregate from responseRatings — sum positive-rated weights
    if score_pct is None:
        # Find active rubric to get weights
        crit_weights = {}
        for sid, step in before.items():
            out = step.get("output", {}) if isinstance(step, dict) else {}
            if not isinstance(out, dict):
                continue
            crits = out.get("criteria")
            if isinstance(crits, list) and crits:
                for c in crits:
                    if isinstance(c, dict) and c.get("id"):
                        w = c.get("weight")
                        if isinstance(w, (int, float)):
                            crit_weights[c["id"]] = w
        # Find rating step and aggregate
        if crit_weights:
            for sid, step in before.items():
                out = step.get("output", {}) if isinstance(step, dict) else {}
                rr = out.get("responseRatings") if isinstance(out, dict) else None
                if not isinstance(rr, dict):
                    continue
                for cand_name, ratings in rr.items():
                    if not isinstance(ratings, dict):
                        continue
                    earned = 0.0
                    max_pos = sum(w for w in crit_weights.values() if w > 0)
                    for cid, rdata in ratings.items():
                        if cid not in crit_weights:
                            continue
                        if not isinstance(rdata, dict):
                            continue
                        rating_val = rdata.get("rating") or rdata.get("score") or rdata.get("value")
                        w = crit_weights[cid]
                        if rating_val in ("present", "Present", 1, "1", True):
                            earned += w
                        elif rating_val in ("not_present", "Not Present", 0, "0", False):
                            if w < 0:
                                earned += abs(w) * 0  # negative not-fired = no penalty, no credit
                        # else: skip undecided
                    if max_pos > 0:
                        score_pct = round(100 * earned / max_pos, 1)
                        score_raw = f"{earned:.1f}/{max_pos:.1f}"
                        score_source = f"{sid}.responseRatings.{cand_name}"
                        break
                if score_pct is not None:
                    break

    # Path 3: top-level inline_form_data.eval (when normalized record passed)
    if score_pct is None and isinstance(top_level, dict):
        ifd = top_level.get("inline_form_data") or {}
        eval_blob = ifd.get("eval") if isinstance(ifd, dict) else None
        if isinstance(eval_blob, dict):
            for k, v in _walk(eval_blob):
                if "score" in str(k).lower() and isinstance(v, (int, float)):
                    score_pct = float(v) * 100 if v <= 1 else float(v)
                    score_source = f"inline_form_data.eval...{k}"
                    break

    delta_class = None
    if score_pct is not None and audit_verdict_band:
        if audit_verdict_band == "FAIL" and score_pct < 30:
            delta_class = "matched_fail"
        elif audit_verdict_band == "FAIL" and score_pct > 80:
            delta_class = "audit_more_strict"
        elif audit_verdict_band == "PASS" and score_pct < 30:
            delta_class = "audit_missed_low_score"
        elif audit_verdict_band == "PASS" and score_pct > 80:
            delta_class = "matched_pass"
        elif audit_verdict_band == "NON-FAIL" and (score_pct < 30 or score_pct > 80):
            delta_class = "non_fail_score_extreme"
        else:
            delta_class = "ambiguous"

    return {
        "verdict": "ok" if score_pct is not None else "no_score_found",
        "auto_score_pct": score_pct,
        "score_raw": score_raw,
        "score_source": score_source,
        "audit_verdict_band": audit_verdict_band,
        "delta_class": delta_class,
    }


# ---------- gate 13 (NEW): prompt→rubric coverage walk heuristic --------------

IMPERATIVE_PATTERNS = [
    r"\b(?:must|should|shall|please|need to|have to)\s+(\w+)",
    r"\b(?:include|create|write|send|set|verify|check|extract|identify|name|list|append|save|store|cite)\s+(\w+)",
]


def gate13_prompt_coverage(before, active_step_id) -> dict:
    if not active_step_id:
        return {"verdict": "skip"}
    # Extract prompt text
    prompt_text = ""
    for sid, step in before.items():
        if "PromptInput" in sid or sid.startswith("step-1771366239685"):
            out = step.get("output", {}) if isinstance(step, dict) else {}
            for fk, fv in out.items():
                if isinstance(fv, str) and fk in ("content", "agent_objective", "desired_outcome", "core_functionalities"):
                    prompt_text += " " + fv

    # Extract imperative phrases (verb + 1-2 following content words)
    imperatives = []
    for pat in IMPERATIVE_PATTERNS:
        for m in re.finditer(pat, prompt_text, re.IGNORECASE):
            verb = m.group(1) if m.groups() else m.group(0)
            # Capture 2 following words as the "object"
            after = prompt_text[m.end():m.end()+60]
            obj = re.findall(r"\b[a-zA-Z]{4,}\b", after)[:2]
            if obj:
                imperatives.append((verb.lower(), " ".join(obj).lower()))

    # Get rubric blob
    crits = before[active_step_id].get("output", {}).get("criteria", [])
    rubric_blob = " ".join((c.get("title") or "") for c in crits).lower()

    # Check coverage: does the rubric mention any of the imperative's object words?
    uncovered = []
    for verb, obj in imperatives[:50]:  # cap at 50
        obj_tokens = obj.split()
        if not obj_tokens:
            continue
        # If at least one core noun appears in rubric, count as covered
        if any(tok in rubric_blob for tok in obj_tokens if len(tok) >= 5):
            continue
        uncovered.append((verb, obj))

    return {
        "verdict": "missing_coverage" if uncovered else "ok",
        "imperatives_found": len(imperatives),
        "uncovered_count": len(uncovered),
        "uncovered_imperatives": uncovered[:20],
    }


# ---------- top-level runner --------------------------------------------------

# ============================================================================
#  NEW GATES (added 2026-05-28, v2.1) — fill gaps surfaced by the L10 audit
# ============================================================================

# ---------- gate 3b: extended process-targeting (§14f catch-up) -------------
# The existing _criterion_findings catches "trajectory shows ...", "before
# composing X", and tool-call phrasings. The L10 audit (Richard Hwang task
# 6a0b6c51dd899aff89927537) surfaced a pattern none of those caught: bare
# "The agent uses <X> tools to ...". This gate adds the catch-up regex so
# the same defect is flagged structurally next time, not only by a specialist.

PROCESS_VERBS_EXTENDED = (
    r"\bthe agent (?:"
    r"uses|consults|inspects|examines|extracts|queries|opens|reads|calls|"
    r"invokes|accesses|retrieves|fetches|navigates(?: to)?|searches|looks(?: up)?|"
    r"checks|verifies|confirms|computes|calculates"
    r")\b"
)
AFTER_TRAJECTORY = r"\bafter (?:the agent|the trajectory|writing|composing|inspecting|reading|opening|computing)\b"


def gate3b_process_targeting(active_step_id, before) -> dict:
    """Scan active rubric criterion titles for process-targeting patterns the
    existing §14f detection misses. Emits one finding per offending criterion."""
    findings = []
    if not active_step_id or not before:
        return {"verdict": "n/a", "findings": findings, "process_pct": 0.0,
                "active_step_id": active_step_id}
    step = before.get(active_step_id) or {}
    out = step.get("output") if isinstance(step, dict) else None
    crits = (out.get("criteria") if isinstance(out, dict) else None) or []

    for c in crits:
        if not isinstance(c, dict):
            continue
        title = (c.get("title") or "").lower()
        cid = c.get("id") or (c.get("title") or "")[:60]
        ann = c.get("annotations") or {}
        tgt = str(ann.get("evaluation_target", "")).lower() if isinstance(ann, dict) else ""
        hit = None
        # STRICT (2026-05-31): a criterion whose evaluation_target IS the
        # trajectory grades the *process*, not the output — the authoritative
        # process-targeting signal (matches the census heuristic behind the
        # approved strict re-grade). The V6 spec demotes these; strict counts.
        if "trajectory" in tgt:
            hit = "evaluation_target=trajectory"
        elif re.search(PROCESS_VERBS_EXTENDED, title):
            hit = "agent-action-verb"
        elif re.search(AFTER_TRAJECTORY, title):
            hit = "after-trajectory-sequencing"
        elif re.search(r"^\s*before\s+\w+ing\b", title):
            hit = "before-sequencing"
        if hit:
            findings.append({
                "criterion_id": cid,
                "criterion_title_preview": (c.get("title") or "")[:160],
                "severity": "major",
                "rule_anchor": "§14f (extended)",
                "kind": f"process-targeting ({hit})",
                "evidence_snippet": (c.get("title") or "")[:140],
                "confidence": "high",
            })

    total = max(len(crits), 1)
    pct = round(len(findings) / total, 4)
    verdict = "fail" if pct > 0.10 else ("non-fail" if pct > 0 else "pass")
    return {
        "verdict": verdict,
        "process_pct": pct,
        "process_count": len(findings),
        "criteria_total": len(crits),
        "active_step_id": active_step_id,
        "findings": findings,
    }


# ---------- gate 3c: strict self-containment (Rule 3b) ---------------------
# Codified 2026-05-28 after the 6a15cdd7 dispute. Only prompt + inputs +
# model response anchor labels. Sibling criteria, desired_outcome, and
# task_metadata do NOT anchor. This gate flags positional labels (Meal N,
# Row N, Item N, etc.) reused across multiple criteria where the descriptor
# isn't present in prompt or inputs.

SELF_CONTAINMENT_LABEL_NOUNS = (
    r"(?:Meal|Row|Item|Step|Photo|Order|Receipt|Line|Entry|Record|Product|"
    r"Image|Picture|Document|Page|Chapter|Section|Block|Tile|Card|Slide)"
)
SELF_CONTAINMENT_TOKEN = (
    r"\b" + SELF_CONTAINMENT_LABEL_NOUNS + r"\s+(?:#\s*)?(?:\d+|[A-Z](?:\d+)?)\b"
)


def gate3c_self_containment_strict(active_step_id, before, task) -> dict:
    """Detect <Noun N> labels used across multiple criteria whose descriptor
    is NOT anchored in prompt or inputs. See Rule 3b in project_overrides.md."""
    findings = []
    if not active_step_id or not before:
        return {"verdict": "n/a", "findings": findings,
                "active_step_id": active_step_id}

    step = before.get(active_step_id) or {}
    out = step.get("output") if isinstance(step, dict) else None
    crits = (out.get("criteria") if isinstance(out, dict) else None) or []

    ifd = (task.get("inline_form_data") or {}) if isinstance(task, dict) else {}
    story = ifd.get("story") or {}
    anchor_text = " ".join([
        str(story.get("agent_objective") or ""),
        str(story.get("user_prompt") or ""),
        str(story.get("system_prompt") or ""),
        " ".join(str(a.get("filename") or a.get("name") or "")
                 for a in (ifd.get("code_container_attachments") or [])
                 if isinstance(a, dict)),
    ]).lower()

    label_uses = {}    # token -> [(cid, has_inline_descriptor, title)]
    for c in crits:
        if not isinstance(c, dict): continue
        title = c.get("title") or ""
        cid = c.get("id") or title[:60]
        for m in re.finditer(SELF_CONTAINMENT_TOKEN, title):
            token = m.group(0).strip()
            tail = title[m.end():m.end() + 80]
            has_inline = bool(re.match(r"^\s*\(", tail) or re.match(r"^\s*,\s*\w", tail))
            label_uses.setdefault(token, []).append((cid, has_inline, title))

    for token, uses in label_uses.items():
        if len(uses) < 2:
            continue
        if token.lower() in anchor_text:
            continue
        dependents = [(cid, title) for cid, has_inline, title in uses if not has_inline]
        if not dependents:
            continue
        for cid, title in dependents:
            findings.append({
                "criterion_id": cid,
                "criterion_title_preview": title[:160],
                "severity": "major",
                "rule_anchor": "§9c / Rule 3b (strict self-containment)",
                "kind": f"sibling-anchored label without prompt/input anchor: {token!r}",
                "evidence_snippet": f"label {token!r} appears in {len(uses)} criteria; "
                                    f"no inline descriptor here and not anchored in prompt/inputs",
                "confidence": "medium",
            })

    total = max(len(crits), 1)
    pct = round(len(findings) / total, 4)
    verdict = "fail" if pct > 0.10 else ("non-fail" if pct > 0 else "pass")
    return {
        "verdict": verdict,
        "labels_examined": list(label_uses.keys()),
        "findings": findings,
        "pct": pct,
        "active_step_id": active_step_id,
    }


# ---------- gate 15: negative-criterion ratio --------------------------------
# Spec target: 25–30% of criteria should be negative-weighted. L10 audit found
# Luis Flores at 0%, Jessica Nelson at ~7%. No prior gate enforced this.

def gate15_negative_ratio(active_step_id, before) -> dict:
    """Compute negative-criterion ratio for the active rubric step and emit
    a banded advisory finding when it's well below the 25-30% target."""
    if not active_step_id or not before:
        return {"verdict": "n/a", "ratio": None, "band": "n/a",
                "active_step_id": active_step_id}
    step = before.get(active_step_id) or {}
    out = step.get("output") if isinstance(step, dict) else None
    crits = (out.get("criteria") if isinstance(out, dict) else None) or []
    if not crits:
        return {"verdict": "n/a", "ratio": None, "band": "empty",
                "active_step_id": active_step_id}

    ratio = _neg_ratio(crits)
    if ratio < 0.05:
        band, severity, conf = "way-under-target", "moderate", "high"
    elif ratio < 0.15:
        band, severity, conf = "under-target", "minor", "high"
    elif ratio <= 0.30:
        band, severity, conf = "in-band", "info", "high"
    else:
        band, severity, conf = "over-target-unusual", "info", "medium"

    return {
        "verdict": "advisory" if band in ("way-under-target", "under-target") else "info",
        "ratio": ratio,
        "negative_count": sum(1 for c in crits
                              if isinstance(c.get("weight"), (int, float))
                              and c["weight"] < 0),
        "total_count": len(crits),
        "band": band,
        "severity": severity,
        "confidence": conf,
        "active_step_id": active_step_id,
    }


# ---------- gate 16: weight calibration -------------------------------------
# V6 valid weight set: {-5, -3, -1, +1, +3, +5}. Any other value is a Major
# spec violation.

V6_VALID_WEIGHTS = {-5, -3, -1, 1, 3, 5}


def gate16_weight_calibration(active_step_id, before) -> dict:
    """Check every active-step criterion weight ∈ V6 valid set."""
    if not active_step_id or not before:
        return {"verdict": "n/a", "out_of_set_count": 0,
                "active_step_id": active_step_id}
    step = before.get(active_step_id) or {}
    out = step.get("output") if isinstance(step, dict) else None
    crits = (out.get("criteria") if isinstance(out, dict) else None) or []
    out_of_set = []
    for c in crits:
        if not isinstance(c, dict): continue
        w = c.get("weight")
        if w is None: continue
        if not isinstance(w, (int, float)) or w not in V6_VALID_WEIGHTS:
            out_of_set.append({
                "criterion_id": c.get("id") or "?",
                "criterion_title_preview": (c.get("title") or "")[:120],
                "weight_observed": w,
            })
    return {
        "verdict": "fail" if out_of_set else "pass",
        "out_of_set_count": len(out_of_set),
        "out_of_set": out_of_set,
        "active_step_id": active_step_id,
    }


# ---------- gate 17: SSoT contradiction (desired_outcome vs rubric) ---------
# When the contributor's desired_outcome example contradicts a rubric criterion
# on the same fact, that's a single-source-of-truth defect. Jamal Patterson's
# task had desired_outcome saying "10 reviews!!" while the rubric demanded
# "14 reviews!!". L0 reviewer flagged it; no prior gate detected it.

SSOT_NUMERIC_PATTERN = (
    r"\b(\d+)\s+"
    r"(reviews|books|items|meals|products|trips|hours|minutes|days|"
    r"orders|receipts|files|photos|images|songs|tracks|users|rows|"
    r"transactions|entries|sources|sections|chapters)\b"
)


def gate17_ssot_contradiction(task) -> dict:
    """Cross-reference numeric+unit pairs from desired_outcome against rubric
    criterion titles. Flag mismatches on the same unit."""
    ifd = (task.get("inline_form_data") or {}) if isinstance(task, dict) else {}
    story = ifd.get("story") or {}
    desired = (story.get("desired_outcome") or "") if isinstance(story, dict) else ""
    rubrics = ifd.get("rubrics") or []
    rubric_text = " ".join(
        (c.get("title") or "")
        for r in rubrics if isinstance(r, dict)
        for c in (r.get("criteria") or [])
        if isinstance(c, dict)
    )
    if not desired or not rubric_text:
        return {"verdict": "n/a", "contradictions": []}

    contradictions = []
    desired_pairs = {(unit.lower(), int(n))
                     for n, unit in re.findall(SSOT_NUMERIC_PATTERN, desired, re.IGNORECASE)}
    rubric_pairs_by_unit: dict = {}
    for n, unit in re.findall(SSOT_NUMERIC_PATTERN, rubric_text, re.IGNORECASE):
        rubric_pairs_by_unit.setdefault(unit.lower(), set()).add(int(n))

    for unit, desired_n in desired_pairs:
        rubric_ns = rubric_pairs_by_unit.get(unit, set())
        if not rubric_ns or desired_n in rubric_ns:
            continue
        contradictions.append({
            "unit": unit,
            "desired_outcome_value": desired_n,
            "rubric_values": sorted(rubric_ns),
            "severity": "moderate",
            "rule_anchor": "SSoT consistency",
            "evidence_snippet": f"desired_outcome says '{desired_n} {unit}'; "
                                f"rubric says {sorted(rubric_ns)} {unit}",
        })

    return {
        "verdict": "fail" if contradictions else "pass",
        "contradictions": contradictions,
        "contradiction_count": len(contradictions),
    }


# ---------------------------------------------------------------------------
#  gate_18 — image-grounding (v2.3, 2026-05-31)
#  Closes the "image-grounding gate gap": every other gate grades rubric TEXT;
#  none inspect the pixels a criterion asserts facts about. Two parts:
#    (A) DETERMINISTIC phantom-filename check — a criterion references an INPUT
#        image file that is ABSENT from the task's input artifacts. That is an
#        unsatisfiable / hallucinated reference = Incorrect Criteria (Major)
#        per the spec's "Overall Rubric Quality - Major". Forced, high-conf.
#        (Catches the aaliyah 0f3 phantom-filename class: IMG_3787 != IMG_3287.)
#    (B) VISION QUEUE — every criterion that references an EXISTING input image
#        asserts a pixel-fact this gate cannot confirm (a count, colour, value,
#        label, position). Emit a verification queue and flag the rubric's
#        image-derived correctness as PENDING VISION so no downstream consumer
#        treats those criteria as auto-PASS. (Catches the e37 / 686f / 874 class
#        of factually-wrong image-derived golds that text gates score PASS.)
#  Spec anchor: Rubric Criteria - Overall Rubric Quality - Major — "More than
#  10% of the criteria contain major issues". Denominator = total criteria; do
#  NOT double-count. A factually-incorrect image-derived criterion is Major.
#
#  Manifest resolution (best-effort, degrades gracefully, never false-positives
#  when the input set is unknown):
#    1. QC_IMAGE_GATE_EXTRACT_ROOT/<task_id>/  — reuse a pre-extracted dir.
#    2. download the story.zip_folder s3Url + zipfile.namelist() (no extract).
#    3. unavailable → skip Part A entirely, still emit the Part B queue.
#  Set QC_IMAGE_GATE_FETCH=0 to disable network (CI / offline).
# ---------------------------------------------------------------------------

_IMG_EXT = r"(?:jpe?g|png|heic|heif|webp|gif|bmp|tiff?)"
# Two forms: (1) backtick-quoted filename (may contain spaces, e.g.
# `WhatsApp Image 2026-04-28 at 07.43.01.png`); (2) a bare space-free token
# (internal dots/hyphens allowed for double-ext like IMG_4822.HEIC.jpg). The
# bare form is space-free on purpose — allowing spaces makes lazy matching
# swallow preceding sentence words ("...references IMG_3787.jpg").
_IMG_FILE_RE = re.compile(r"`([^`]+?\.%s)`|\b([\w\-.]+\.%s)\b" % (_IMG_EXT, _IMG_EXT), re.I)
_CREATE_VERB_RE = re.compile(
    r"\b(create[sd]?|save[sd]?|write[sd]?|generate[sd]?|produce[sd]?|output[sd]?|"
    r"export[sd]?|render[sd]?|compose[sd]?|build[sd]?|the\s+(?:final\s+)?output)\b", re.I)
_OBSERVE_CUE_RE = re.compile(
    r"\b(show[sn]?|depict|display[sn]?|contain[sn]?|visible|appears?|pictured|"
    r"the\s+(?:photo|image|picture|file|scan|screenshot|input))\b", re.I)
_INPUT_NAME_RE = re.compile(
    r"^(IMG[_-]|DSC[_-]|PXL[_-]|DSCF|Screenshot|screenshot|photo|scan|WhatsApp|input)", re.I)
_IMG_EXT_SET = {"jpg", "jpeg", "png", "heic", "heif", "webp", "gif", "bmp", "tif", "tiff"}


def _img_core(name: str) -> str:
    """Lowercase basename with ALL trailing image extensions stripped, so
    'IMG_4822.HEIC.jpg' (HEIC→JPG conversion artifact) and 'IMG_4822.HEIC'
    both reduce to 'img_4822' and match."""
    n = os.path.basename(name).lower()
    while True:
        root, ext = os.path.splitext(n)
        if ext and ext.lstrip(".") in _IMG_EXT_SET:
            n = root
        else:
            return n


def _input_manifest_for_task(task) -> tuple[set, str]:
    """Best-effort set of input filenames (basenames, lowercased) + a status."""
    task_id = task.get("task_id") if isinstance(task, dict) else None
    # 1) reuse a pre-extracted dir
    root = os.environ.get("QC_IMAGE_GATE_EXTRACT_ROOT")
    if root and task_id:
        d = os.path.join(root, task_id)
        if os.path.isdir(d):
            names = set()
            for r, _, fs in os.walk(d):
                if "__MACOSX" in r:
                    continue
                for fn in fs:
                    names.add(fn.lower())
            if names:
                return names, "local_extract"
    # 2) download zip + namelist (no extract)
    if os.environ.get("QC_IMAGE_GATE_FETCH", "1") == "1":
        ifd = (task.get("inline_form_data") or {}) if isinstance(task, dict) else {}
        story = ifd.get("story") or {}
        for z in (story.get("zip_folder") or []):
            url = z.get("s3Url") if isinstance(z, dict) else None
            if not url or not str(url).startswith("http"):
                continue
            try:
                import io
                import urllib.request
                import zipfile as _zf
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=8) as resp:
                    buf = io.BytesIO(resp.read())
                with _zf.ZipFile(buf) as zf:
                    names = {os.path.basename(n).lower() for n in zf.namelist()
                             if "__MACOSX" not in n and not n.endswith("/")}
                if names:
                    return names, "zip_namelist"
            except Exception:
                continue
    return set(), "unavailable"


def gate18_image_grounding(active_step_id, before, task) -> dict:
    if not active_step_id or active_step_id not in before:
        return {"verdict": "skip_no_active_step", "phantom_findings": [],
                "vision_queue": [], "manifest_status": "n/a"}
    out = before[active_step_id].get("output", {}) if isinstance(before[active_step_id], dict) else {}
    crits = out.get("criteria", []) if isinstance(out, dict) else []
    if not crits:
        return {"verdict": "skip_no_criteria", "phantom_findings": [],
                "vision_queue": [], "manifest_status": "n/a"}

    manifest, mstatus = _input_manifest_for_task(task)
    manifest_cores = {_img_core(n) for n in manifest}  # absorb ext/case/double-ext mismatch

    phantom, queue = [], []
    for c in crits:
        title = c.get("title") or ""
        cid = (c.get("id") or "")[:8]
        refs = {(m.group(1) or m.group(2)).strip() for m in _IMG_FILE_RE.finditer(title)}
        if not refs:
            continue
        is_output_ctx = bool(_CREATE_VERB_RE.search(title))
        for ref in refs:
            base = os.path.basename(ref).lower()
            present = (base in manifest) or (_img_core(ref) in manifest_cores)
            # input-style name = camera/upload artifact (IMG_/DSC_/Screenshot/scan/…).
            # The manifest is the primary signal: a descriptive-named file ABSENT
            # from inputs is an agent OUTPUT, not a phantom — only input-style names
            # that are absent from a KNOWN manifest are phantom (typo/hallucinated).
            input_name = bool(_INPUT_NAME_RE.search(os.path.basename(ref)))
            if present:
                if not is_output_ctx:                       # an input image → vision-verify
                    queue.append({
                        "criterion_id": cid, "criterion_title_preview": title[:220],
                        "image_file": ref, "present_in_inputs": True,
                    })
            elif mstatus == "unavailable":
                if input_name and not is_output_ctx:        # manifest unknown → best-effort queue
                    queue.append({
                        "criterion_id": cid, "criterion_title_preview": title[:220],
                        "image_file": ref, "present_in_inputs": None,
                    })
            elif input_name and not is_output_ctx:          # input-style name absent from KNOWN inputs
                phantom.append({
                    "criterion_id": cid, "criterion_title_preview": title[:180],
                    "missing_file": ref, "manifest_sample": sorted(manifest)[:10],
                    "severity": "major", "kind": "incorrect_criteria_phantom_image",
                })
            # else: descriptive-named file absent from inputs → agent OUTPUT → skip

    if phantom:
        verdict = "phantom_image_findings"
    elif queue:
        verdict = "vision_pending"
    else:
        verdict = "ok_no_input_image_criteria"
    return {
        "verdict": verdict,
        "manifest_status": mstatus,
        "input_files_seen": len(manifest),
        "phantom_findings": phantom,
        "phantom_count": len(phantom),
        "vision_queue": queue,
        "vision_queue_count": len(queue),
        "spec_anchor": ("Rubric Criteria - Overall Rubric Quality - Major "
                        "(Incorrect Criteria; >10% Major → Fail; denom = total criteria)"),
    }


def run_v2(task_path: Path, out_path: Path) -> dict:
    task = json.load(open(task_path))
    response = task.get("response") or task
    before = response.get("before", {}) if isinstance(response, dict) else {}
    if not before and isinstance(task.get("inline_form_data"), dict):
        before = task["inline_form_data"].get("before", {}) or {}
    if not before:
        before = task.get("before", {})

    if not before:
        report = {
            "task_path": str(task_path),
            "v": "2.4-beta",
            "verdict": "no_before_block",
            "forced_findings": [],
        }
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2))
        return report

    g1 = gate1_active_rubric_step(before)
    active_id = g1.get("active_step_id")
    g2 = gate2_trajectory(before)
    g3 = gate3_atomicity_v2(active_id, before)
    g5 = gate5_category(before, active_id)
    g6 = gate6_coverage(active_id, before)
    g7 = gate7_leaks(before)
    # g8 verifier.py presence — V6 (2026-05-27): Tests dims 8a-d are conditionally
    # in scope when contributor_verifier_py is non-null. Compute the presence
    # flag here so downstream consumers (master, swarm) can decide whether to
    # grade Tests dims.
    inline = (task.get("inline_form_data") or {}) if isinstance(task, dict) else {}
    verifier_py = inline.get("contributor_verifier_py") if isinstance(inline, dict) else None
    tests_in_scope = bool(verifier_py) and (
        (verifier_py.get("s3Url") if isinstance(verifier_py, dict) else verifier_py) is not None
    )
    g8 = {"verdict": "in_scope" if tests_in_scope else "skip_no_verifier_py",
          "tests_in_scope_per_v6": tests_in_scope}
    g10 = gate10_ratings_sanity(before, active_id)
    g11 = gate11_safety_heuristic(before)

    # NEW v2.1 gates (added 2026-05-28 after L10 audit gaps)
    g3b = gate3b_process_targeting(active_id, before)
    g3c = gate3c_self_containment_strict(active_id, before, task)
    g15 = gate15_negative_ratio(active_id, before)
    g16 = gate16_weight_calibration(active_id, before)
    g17 = gate17_ssot_contradiction(task)
    g18 = gate18_image_grounding(active_id, before, task)  # NEW v2.3 — image-grounding

    # Pre-compute audit verdict band from gate-3 + forced signals
    audit_band = "PASS"
    if g3.get("per_dim_summary"):
        if any(d.get("score") == 2 for d in g3["per_dim_summary"].values()):
            audit_band = "FAIL"
        elif any(d.get("score") == 3 for d in g3["per_dim_summary"].values()):
            audit_band = "NON-FAIL"
    # V6: only flip band on category mismatch when silver trajectory is present
    if g5["verdict"] == "mismatch_strong" and g5.get("silver_trajectory_present", False):
        audit_band = "FAIL"
    if g6["verdict"] == "missing_coverage":
        audit_band = "FAIL"
    if g7["verdict"] == "leaks_found":
        audit_band = "FAIL"
    if g11["verdict"] == "high":
        audit_band = "FAIL"
    # gate_10 no longer drives audit_band — V6 dropped Ratings Validity dim.

    g12 = gate12_score_grounding(before, audit_band, top_level=task)
    g13 = gate13_prompt_coverage(before, active_id)

    # Roll up findings
    forced = []   # high-confidence — master must inherit
    advisory = [] # medium-confidence — master may down-grade
    info = []     # informational only

    # Per-criterion findings → forced or advisory by confidence
    for f in g3.get("per_criterion_findings", []):
        rec = {
            "dim": "6a" if f["severity"] == "major" else "6b" if f["severity"] == "moderate" else "6c",
            "criterion_id": f["criterion_id"],
            "criterion_title_preview": f["criterion_title_preview"],
            "severity": f["severity"],
            "rule_anchor": f["rule_anchor"],
            "kind": f["kind"],
            "evidence_snippet": f["evidence_snippet"],
            "confidence": f["confidence"],
        }
        if f["confidence"] == "high":
            forced.append(rec)
        elif f["confidence"] == "medium":
            advisory.append(rec)
        else:
            advisory.append(rec)

    # Dim rollups
    for dim, summary in g3.get("per_dim_summary", {}).items():
        if summary.get("score") == 2:
            forced.append({
                "dim": dim,
                "kind": "rubric_quality_threshold_breach",
                "score": 2,
                "rule_anchor": "§9-thresholds",
                "evidence_snippet": json.dumps(summary),
                "confidence": "high",
            })

    # Category mismatch — V6 (2026-05-27): dim 4a is OPTIONAL; only emit
    # forced when a silver_trajectory step actually exists in `before`.
    silver_present = g5.get("silver_trajectory_present", False)
    if g5["verdict"] == "mismatch_strong":
        record = {
            "dim": "4a",
            "kind": "category_mismatch_anchor_zero",
            "score": 2 if silver_present else 3,
            "rule_anchor": "spec dim 4a (V6: only graded when silver trajectory present)",
            "evidence_snippet": f"category={g5.get('category_value')}, anchor_hits={g5.get('subcategory_anchor_hits')}, silver_trajectory_present={silver_present}",
            "confidence": "high" if silver_present else "low",
        }
        if silver_present:
            forced.append(record)
        else:
            advisory.append(record)
    elif g5["verdict"] == "mismatch_weak":
        advisory.append({
            "dim": "4a",
            "kind": "category_mismatch_low_anchor_ratio",
            "score": 3,
            "rule_anchor": "spec dim 4a",
            "evidence_snippet": f"category={g5.get('category_value')}, hit_ratio<0.30, silver_present={silver_present}",
            "confidence": "medium",
        })

    # Coverage
    if g6["verdict"] == "missing_coverage":
        forced.append({
            "dim": "6a",
            "kind": "coverage_gap",
            "score": 2,
            "rule_anchor": "Rule 2 (prompt→rubric coverage)",
            "evidence_snippet": f"unscored_artifacts={g6['unscored_artifacts']}",
            "confidence": "high",
        })

    # Leaks
    if g7["verdict"] == "leaks_found":
        forced.append({
            "dim": "9",
            "kind": "contributor_note_leak",
            "score": 2,
            "rule_anchor": "universe data hygiene",
            "evidence_snippet": f"{len(g7['leaks'])} leaks detected",
            "confidence": "high",
        })

    # Verifier.py block REMOVED 2026-05-23 — Tests dims out of scope

    # Ratings sanity — V6 (2026-05-27) DROPPED Ratings Validity (was dim 7).
    # Gate now emits ADVISORY-ONLY informational signal that masters can use
    # for cross-wired-justification context on dim 9 (Failed-Rubric Justification),
    # but no longer forces a dim-7 finding because dim 7 doesn't exist in V6.
    if g10["verdict"] in ("high", "medium"):
        advisory.append({
            "dim": "9",  # surface as Justification-quality signal under dim 9
            "kind": "ratings_sanity_signal_post_v6",
            "score": 3,
            "rule_anchor": "V6: dim 7 dropped; signal repurposed for dim 9 cross-wiring",
            "evidence_snippet": json.dumps(g10["ratings_findings"][:1]),
            "confidence": "low",  # never force — V6 has no Ratings Validity home
        })

    # Safety
    if g11["verdict"] == "high":
        forced.append({
            "dim": "3",
            "kind": "safety_risk_high",
            "score": 2,
            "rule_anchor": "§12 safety codes (f2_medical + f6_real_faces)",
            "evidence_snippet": json.dumps(g11["risk_indicators"]),
            "confidence": "medium",  # heuristic — swarm should verify Wikimedia license context
        })
    elif g11["verdict"] in ("medium", "low_medium"):
        advisory.append({
            "dim": "3",
            "kind": "safety_risk_medium",
            "score": 3,
            "rule_anchor": "§12 safety codes",
            "evidence_snippet": json.dumps(g11["risk_indicators"]),
            "confidence": "low",
        })

    # Score grounding (informational; never forced)
    info.append({
        "kind": "score_grounding",
        "evidence_snippet": json.dumps(g12),
        "confidence": "high" if g12["auto_score_pct"] is not None else "low",
    })

    # --- v2.1 new-gate rollup ---

    # 3b: extended process-targeting.
    # STRICT stance (PROCESS_TARGETING_MAJOR=True, 2026-05-31 project-lead
    # directive): forced Major, drives the bands. DIVERGES from the V6 spec,
    # which demotes process-targeting to advisory (defers categorization to an
    # appendix not in our dump). Flip the constant to restore spec-literal.
    if PROCESS_TARGETING_MAJOR:
        for f in g3b.get("findings", []):
            forced.append({
                "dim": "6a",
                "criterion_id": f["criterion_id"],
                "criterion_title_preview": f["criterion_title_preview"],
                "kind": f["kind"],
                "rule_anchor": f["rule_anchor"] + " (STRICT: process-targeting=Major — project-lead directive, diverges from V6 spec demotion)",
                "evidence_snippet": f["evidence_snippet"],
                "severity": "major",
                "confidence": f["confidence"],
            })
    else:
        for f in g3b.get("findings", []):
            advisory.append({
                "dim": "6a",
                "criterion_id": f["criterion_id"],
                "criterion_title_preview": f["criterion_title_preview"],
                "kind": f["kind"],
                "rule_anchor": f["rule_anchor"] + " (advisory — appendix not in local spec)",
                "evidence_snippet": f["evidence_snippet"],
                "severity": "minor",
                "confidence": f["confidence"],
            })

    # 3c: strict self-containment — advisory (medium-confidence; rule's
    # heuristic about prompt/input anchoring can have edge cases)
    for f in g3c.get("findings", []):
        advisory.append({
            "dim": "6a",
            "criterion_id": f["criterion_id"],
            "criterion_title_preview": f["criterion_title_preview"],
            "kind": f["kind"],
            "rule_anchor": f["rule_anchor"],
            "evidence_snippet": f["evidence_snippet"],
            "severity": f["severity"],
            "confidence": f["confidence"],
        })

    # 15: negative-criterion ratio — advisory when way-under/under-target
    if g15.get("verdict") == "advisory":
        advisory.append({
            "dim": "6d",  # rubric-quality / weight-calibration sub-dim
            "kind": f"negative_ratio_{g15['band']}",
            "rule_anchor": "spec target 25-30% negative criteria",
            "evidence_snippet": f"ratio={g15['ratio']} ({g15['negative_count']}/{g15['total_count']}); "
                                f"band={g15['band']}",
            "severity": g15["severity"],
            "confidence": g15["confidence"],
        })

    # 16: weight calibration — forced (any out-of-V6-set weight is Major)
    if g16.get("verdict") == "fail":
        forced.append({
            "dim": "6d",
            "kind": "weight_out_of_v6_set",
            "rule_anchor": "V6 valid weights {-5,-3,-1,+1,+3,+5}",
            "evidence_snippet": json.dumps(g16["out_of_set"][:3]),
            "severity": "major",
            "confidence": "high",
        })

    # 17: SSoT contradiction — advisory (heuristic; numeric+unit may match
    # different referents in some tasks)
    for con in g17.get("contradictions", []):
        advisory.append({
            "dim": "6a",
            "kind": "ssot_contradiction_desired_vs_rubric",
            "rule_anchor": "SSoT consistency",
            "evidence_snippet": con["evidence_snippet"],
            "severity": con["severity"],
            "confidence": "medium",
        })

    # 18: image-grounding (v2.3) — Part A phantom-filename = forced Major
    # (Incorrect Criteria, spec-anchored); Part B vision queue = advisory
    # "correctness PENDING vision" (the gate cannot certify PASS on any
    # image-derived gold — that requires a vision pass on the actual pixels).
    for ph in g18.get("phantom_findings", []):
        forced.append({
            "dim": "6a",
            "criterion_id": ph["criterion_id"],
            "criterion_title_preview": ph["criterion_title_preview"],
            "kind": "incorrect_criteria_phantom_image",
            "rule_anchor": "spec: Overall Rubric Quality - Major (referenced input image absent from task inputs)",
            "evidence_snippet": f"criterion references '{ph['missing_file']}' — not in inputs (seen: {ph['manifest_sample']})",
            "severity": "major",
            "confidence": "high",
        })
    if g18.get("vision_queue"):
        advisory.append({
            "dim": "6a",
            "kind": "image_gold_vision_pending",
            "rule_anchor": "image-grounding gate gap — text gates cannot verify image-derived golds; vision pass required before PASS",
            "evidence_snippet": (f"{g18['vision_queue_count']} image-derived criteria need vision verification: "
                                 + ", ".join(f"{q['criterion_id']}:{q['image_file']}" for q in g18["vision_queue"][:8])),
            "severity": "minor",   # a PENDING flag, not a confirmed defect
            "confidence": "low",
        })

    # Image-grounding cascade — phantom-image majors augment the 6a Major tally
    # over the SAME total-criteria denominator the spec mandates. If gate-3
    # majors + phantom majors clear >10%, the rubric Fails 6a.
    ph_n = g18.get("phantom_count", 0)
    if ph_n:
        _tot = g3.get("total_criteria") or 0
        _maj = g3.get("major_count", 0) + ph_n
        if _tot and (_maj / _tot) > 0.10:
            audit_band = "FAIL"

    # Process-targeting strict cascade (PROCESS_TARGETING_MAJOR, 2026-05-31).
    # Fold process-targeting criteria into the 6a/6b/6c bands as Major, over the
    # total-criteria denominator (deduped by criterion_id against gate-3's own
    # findings so a criterion flagged by both isn't counted twice). Diverges
    # from the V6 spec-literal grade; emit a forced band-breach + cascade FAIL.
    # Count process-targeting as 6a Major (>10%). Deliberately combined ONLY
    # with gate-3's adjudicated MAJOR count — NOT its recall-tuned moderate/
    # minor findings, which are the spot-check false-positive flood that v2.2
    # clears. Re-unioning that flood would re-inflate 6c and defeat the
    # spot-check recalibration. So the strict lever is isolated to its own
    # band: (gate-3 majors ∪ process-targeting criteria) / total > 10%.
    strict_bands = None
    if PROCESS_TARGETING_MAJOR and g3b.get("findings"):
        _tot = g3.get("total_criteria") or g3b.get("criteria_total") or 0
        if _tot:
            g3maj = {str(f.get("criterion_id"))[:8] for f in g3.get("per_criterion_findings", []) if f.get("severity") == "major"}
            pt = {str(f.get("criterion_id"))[:8] for f in g3b.get("findings", [])}
            s6a = len(g3maj | pt) / _tot
            strict_bands = {"6a_major_with_process_targeting": round(s6a, 4),
                            "process_count": len(pt), "gate3_major": len(g3maj), "total": _tot}
            if s6a > 0.10:
                audit_band = "FAIL"
                forced.append({
                    "dim": "6a",
                    "kind": "process_targeting_strict_band_breach",
                    "score": 2,
                    "rule_anchor": "STRICT process-targeting=Major (project-lead directive 2026-05-31; diverges from V6 spec)",
                    "evidence_snippet": f"6a Major (incl. process-targeting) = {len(g3maj | pt)}/{_tot} = {s6a:.0%} > 10% (process_targeting={len(pt)})",
                    "confidence": "high",
                })

    # Prompt→rubric coverage walk — V6 patch (L10 ground truth):
    # raised threshold from 3 to 5 (the masters consistently rejected gate_13
    # findings as keyword-walker false positives — bigram tokenisation noise).
    # Even with threshold 5, this stays at confidence=low so masters can prune.
    if g13["verdict"] == "missing_coverage" and g13["uncovered_count"] >= 5:
        advisory.append({
            "dim": "6a",
            "kind": "prompt_imperatives_uncovered",
            "score": 3,
            "rule_anchor": "Rule 2 (prompt→rubric coverage walk)",
            "evidence_snippet": f"{g13['uncovered_count']} uncovered imperatives from {g13['imperatives_found']} total",
            "confidence": "low",  # heuristic; swarm should verify
        })

    # Process-targeting cascade — REMOVED 2026-05-28 pm. The V6 live spec
    # doesn't enumerate process-targeting as a graded failure category
    # (defers to a Rubric Quality Definitions appendix we don't have).
    # gate3b stays as an authoring-advisory signal only, not a verdict driver.

    # Weight-calibration cascade (v2.1) — out-of-set weights = automatic Fail.
    if g16.get("verdict") == "fail":
        audit_band = "FAIL"

    # Final report
    report = {
        "task_path": str(task_path),
        "v": "2.4-beta",
        "strict_process_targeting_major": PROCESS_TARGETING_MAJOR,
        "strict_process_targeting_bands": strict_bands,
        "active_rubric_step": active_id,
        "audit_verdict_band_preview": audit_band,
        "gate_1_active_step": g1,
        "gate_2_trajectory": g2,
        "gate_3_atomicity_v2": g3,
        "gate_3b_process_targeting": g3b,                # NEW v2.1
        "gate_3c_self_containment_strict": g3c,          # NEW v2.1
        "gate_5_category": g5,
        "gate_6_coverage": g6,
        "gate_7_leaks": g7,
        "gate_8_tests_v6_scope": g8,
        "gate_10_ratings_sanity": g10,
        "gate_11_safety_heuristic": g11,
        "gate_12_score_grounding": g12,
        "gate_13_prompt_coverage": g13,
        "gate_15_negative_ratio": g15,                    # NEW v2.1
        "gate_16_weight_calibration": g16,                # NEW v2.1
        "gate_17_ssot_contradiction": g17,                # NEW v2.1
        "gate_18_image_grounding": g18,                   # NEW v2.3
        "image_gold_vision_queue": g18.get("vision_queue", []),  # surfaced for the vision swarm
        "per_criterion_findings": g3.get("per_criterion_findings", []),
        "per_dim_summary": g3.get("per_dim_summary", {}),
        "forced_findings": forced,
        "advisory_findings": advisory,
        "informational": info,
        "forced_findings_count": len(forced),
        "advisory_findings_count": len(advisory),
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, default=str))
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task-json")
    ap.add_argument("--task-dir")
    ap.add_argument("--out")
    ap.add_argument("--out-dir")
    args = ap.parse_args()

    if args.task_json:
        out = Path(args.out) if args.out else Path(args.task_json).with_suffix(".gates_v2.json")
        r = run_v2(Path(args.task_json), out)
        print(f"{Path(args.task_json).stem}: forced={r.get('forced_findings_count', 0)} advisory={r.get('advisory_findings_count', 0)} band={r.get('audit_verdict_band_preview', 'n/a')}", file=sys.stderr)
    elif args.task_dir:
        out_dir = Path(args.out_dir or Path(args.task_dir) / "gates_v2")
        out_dir.mkdir(parents=True, exist_ok=True)
        for p in Path(args.task_dir).glob("*.json"):
            out = out_dir / f"{p.stem}.gates_v2.json"
            r = run_v2(p, out)
            print(f"{p.stem}: forced={r.get('forced_findings_count', 0)} advisory={r.get('advisory_findings_count', 0)} band={r.get('audit_verdict_band_preview', 'n/a')}", file=sys.stderr)
    else:
        ap.print_help()
        sys.exit(2)


if __name__ == "__main__":
    main()
