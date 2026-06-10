#!/usr/bin/env python3
"""
Pre-audit deterministic gates for OpenClaw QC audits.

Runs 7 checks BEFORE any sub-agent grades the task. Each gate either
(a) passes silently, (b) emits a forced finding the sub-agents must inherit,
or (c) marks specific dimensions audit_incomplete so they're not graded blind.

The output is a single `gates_report.json` per task that auditors and the
master MUST read and respect. Sub-agents are forbidden from overriding gate
verdicts — the gates implement the bulletproofing learned from the 2026-05
audit retros.

Failure modes encoded (in order of cost-per-miss):

  Gate 1 — Active rubric step (Rule 12 deterministic)
  Gate 2 — Trajectory inspection mandate (dims 3, 4b, 5, 7)
  Gate 3 — Atomicity quantitative check (dims 6a-c)
  Gate 4 — Signed-URL fetch fallback (preempts audit_incomplete)
  Gate 5 — Category mismatch (dims 1d, 4a)
  Gate 6 — Coverage cross-check vs desired_outcome (dim 6a / 9c)
  Gate 7 — Contributor-note leak in universe data (dim 9)

Usage:

    python3 preaudit_checks.py \
        --task-json <path> \
        --out <path-to-gates_report.json>

Or batch:

    python3 preaudit_checks.py \
        --task-dir <workspace>/tasks/ \
        --out-dir <workspace>/gates/
"""

import argparse, json, os, re, sys
from pathlib import Path
from typing import Any


# ---------- gate 1: active rubric step (Rule 12 deterministic) ---------------

def gate1_active_rubric_step(before: dict) -> dict:
    """
    Find the active rubric step by matching RubricCriteriaRating.responseRatings
    keys against each candidate RubricCriteriaBuilder's criterion IDs.

    Returns:
      {
        "active_step_id": str | None,
        "candidate_steps": [{"id": str, "criteria_count": int, "match_count": int}],
        "rating_steps": [str],
        "verdict": "ok" | "no_rating_step" | "no_match" | "multiple_matches",
        "forced_findings": [{"dim": str, "score": int, "reason": str}],
      }
    """
    # 1. Find all RubricCriteriaBuilder candidate steps
    candidates = []
    for sid, step in before.items():
        out = step.get("output", {}) if isinstance(step, dict) else {}
        if not isinstance(out, dict):
            continue
        crits = out.get("criteria")
        if not isinstance(crits, list) or not crits:
            continue
        # Is it a builder? Either named pattern or has weight/title shape
        is_builder = False
        if "RubricCriteriaBuilder" in sid:
            is_builder = True
        elif re.match(r"^step-\d{13}-\w+$", sid):
            # Timestamp-prefixed step with criteria
            is_builder = True
        if not is_builder:
            continue
        crit_ids = []
        for c in crits:
            if isinstance(c, dict) and c.get("id"):
                crit_ids.append(c["id"])
        candidates.append({
            "id": sid,
            "criteria_count": len(crits),
            "criterion_ids": set(crit_ids),
            "is_timestamped": bool(re.match(r"^step-\d{13}-", sid)),
        })

    # 2. Find rating steps and pull their rated criterion IDs
    rating_steps = []
    rated_ids = set()
    for sid, step in before.items():
        out = step.get("output", {}) if isinstance(step, dict) else {}
        if not isinstance(out, dict):
            continue
        rr = out.get("responseRatings")
        if isinstance(rr, dict):
            rating_steps.append(sid)
            for _candidate, ratings in rr.items():
                if isinstance(ratings, dict):
                    rated_ids.update(ratings.keys())

    # 3. Score each candidate
    for c in candidates:
        if rated_ids:
            c["match_count"] = len(c["criterion_ids"] & rated_ids)
            c["match_ratio"] = c["match_count"] / max(len(c["criterion_ids"]), 1)
        else:
            c["match_count"] = 0
            c["match_ratio"] = 0.0

    if not rated_ids:
        # No rating step — fall back to "latest timestamped wins"
        ts_candidates = [c for c in candidates if c["is_timestamped"]]
        if ts_candidates:
            active = max(ts_candidates, key=lambda c: c["id"])
            verdict = "no_rating_step_used_latest_timestamp"
        elif candidates:
            active = candidates[0]
            verdict = "no_rating_step_used_first_builder"
        else:
            return {
                "active_step_id": None,
                "candidate_steps": [],
                "rating_steps": [],
                "verdict": "no_builder_found",
                "forced_findings": [{
                    "dim": "audit_incomplete",
                    "score": None,
                    "reason": "No RubricCriteriaBuilder step found in response.before — cannot grade any rubric dimension."
                }],
            }
        return {
            "active_step_id": active["id"],
            "candidate_steps": [_clean_cand(c) for c in candidates],
            "rating_steps": rating_steps,
            "verdict": verdict,
            "forced_findings": [],
        }

    # 4. Pick the builder with highest match_ratio (must exceed 0.5)
    full_matches = [c for c in candidates if c["match_ratio"] >= 0.99]
    high_matches = [c for c in candidates if c["match_ratio"] >= 0.50]

    if len(full_matches) == 1:
        active = full_matches[0]
        return {
            "active_step_id": active["id"],
            "candidate_steps": [_clean_cand(c) for c in candidates],
            "rating_steps": rating_steps,
            "verdict": "ok",
            "forced_findings": [],
        }
    elif len(full_matches) > 1:
        # Multiple builders share the same criterion IDs — pick the latest timestamp
        ts_full = [c for c in full_matches if c["is_timestamped"]]
        if ts_full:
            active = max(ts_full, key=lambda c: c["id"])
            return {
                "active_step_id": active["id"],
                "candidate_steps": [_clean_cand(c) for c in candidates],
                "rating_steps": rating_steps,
                "verdict": "multiple_full_matches_used_latest_timestamp",
                "forced_findings": [],
            }
        active = full_matches[0]
        return {
            "active_step_id": active["id"],
            "candidate_steps": [_clean_cand(c) for c in candidates],
            "rating_steps": rating_steps,
            "verdict": "multiple_full_matches_used_first",
            "forced_findings": [],
        }
    elif high_matches:
        active = max(high_matches, key=lambda c: c["match_ratio"])
        return {
            "active_step_id": active["id"],
            "candidate_steps": [_clean_cand(c) for c in candidates],
            "rating_steps": rating_steps,
            "verdict": f"partial_match_{active['match_ratio']:.0%}",
            "forced_findings": [],
        }
    else:
        return {
            "active_step_id": None,
            "candidate_steps": [_clean_cand(c) for c in candidates],
            "rating_steps": rating_steps,
            "verdict": "no_match",
            "forced_findings": [{
                "dim": "audit_incomplete",
                "score": None,
                "reason": (
                    "No RubricCriteriaBuilder step matches the rating step's criterion IDs. "
                    "Cannot identify active rubric — mark all rubric dimensions audit_incomplete."
                )
            }],
        }


def _clean_cand(c: dict) -> dict:
    return {k: (sorted(v) if isinstance(v, set) else v) for k, v in c.items() if k != "criterion_ids"}


# ---------- gate 2: trajectory inspection mandate -----------------------------

# Tool categories the rubric-required workflow expects to see. We bucket tool
# calls into these and check whether the trajectory exercises enough buckets.
TOOL_CATEGORIES = {
    "file_write": ["str_replace_editor", "create", "write_file", "edit_file", "Write", "Edit"],
    "file_read":  ["read_file", "Read", "view"],
    "shell":      ["bash", "Bash", "shell", "exec"],
    "search":     ["grep", "search", "find", "memory_search"],
    "browser":    ["browser_navigate", "browser_click", "browser_fetch", "WebFetch"],
    "mcp":        [],  # any tool name with prefix "mcp__"
    "image":      ["read_image", "image_analyze", "ocr"],
    "calendar":   ["create_reminder", "schedule_event", "calendar"],
    "email":      ["send_email", "gmail", "send_message"],
}


def gate2_trajectory_inspection(before: dict) -> dict:
    """
    Inspect step-AgentExecution-*.trajectory for tool-call distribution,
    file creations, workflow completion. Returns counts and category coverage.
    """
    # Find the agent execution step
    ae_step = None
    for sid, step in before.items():
        if "AgentExecution" not in sid:
            continue
        out = step.get("output", {}) if isinstance(step, dict) else {}
        if isinstance(out, dict) and isinstance(out.get("trajectory"), list):
            ae_step = sid
            traj = out["trajectory"]
            break
    else:
        traj = []

    if not traj:
        return {
            "step_id": ae_step,
            "verdict": "no_trajectory",
            "metrics": {},
            "tool_call_categories": {},
            "forced_findings": [{
                "dim": "3 Trajectory Coherence",
                "score": None,
                "reason": "No step-AgentExecution-* trajectory found — dim 3, 5 (Architectural Depth), 7 not gradable."
            }],
        }

    n_turns = len(traj)
    assistant_text_turns = 0
    assistant_substantive_turns = 0  # non-HEARTBEAT_OK
    tool_calls = []  # (turn_idx, tool_name, input_str)
    file_writes = []
    user_msgs = 0
    tool_results = 0

    for i, t in enumerate(traj):
        if not isinstance(t, dict):
            continue
        role = t.get("role")
        content = t.get("content")

        if role == "assistant":
            if isinstance(content, str):
                assistant_text_turns += 1
                if content.strip() and "HEARTBEAT_OK" not in content:
                    assistant_substantive_turns += 1
            elif isinstance(content, list):
                for c in content:
                    if not isinstance(c, dict):
                        continue
                    if c.get("type") == "tool_use":
                        # Anthropic format
                        name = c.get("name", "")
                        inp = c.get("input", {})
                        tool_calls.append((i, name, json.dumps(inp)[:300] if isinstance(inp, dict) else str(inp)[:300]))
                        if any(p in name.lower() for p in ["write", "create_file", "edit", "str_replace"]):
                            path = ""
                            if isinstance(inp, dict):
                                path = inp.get("path") or inp.get("file_path") or inp.get("filename") or ""
                            file_writes.append((i, name, path))
                    elif c.get("type") == "text":
                        if c.get("text", "").strip() and "HEARTBEAT_OK" not in c.get("text", ""):
                            assistant_substantive_turns += 1
                        assistant_text_turns += 1
            # OpenAI function-calling format: t.tool_calls is a top-level list
            tc_list = t.get("tool_calls")
            if isinstance(tc_list, list):
                for tc in tc_list:
                    if not isinstance(tc, dict):
                        continue
                    fn = tc.get("function") if isinstance(tc.get("function"), dict) else tc
                    name = fn.get("name", "")
                    args_raw = fn.get("arguments", "")
                    if isinstance(args_raw, str):
                        try:
                            inp = json.loads(args_raw)
                        except Exception:
                            inp = {"_raw": args_raw[:300]}
                    elif isinstance(args_raw, dict):
                        inp = args_raw
                    else:
                        inp = {}
                    tool_calls.append((i, name, json.dumps(inp)[:300] if isinstance(inp, dict) else str(inp)[:300]))
                    if any(p in name.lower() for p in ["write", "create_file", "edit", "str_replace"]):
                        path = ""
                        if isinstance(inp, dict):
                            path = inp.get("path") or inp.get("file_path") or inp.get("filename") or ""
                        file_writes.append((i, name, path))
                    # Bash-style shell file writes (echo > file, cat > file, etc.) — detect from command
                    if name.lower() in ("bash", "shell", "process"):
                        cmd = ""
                        if isinstance(inp, dict):
                            cmd = (inp.get("command") or inp.get("cmd") or "") if isinstance(inp.get("command") or inp.get("cmd"), str) else ""
                        if cmd and re.search(r"(^|[\s;&|])(echo|cat|printf|tee|cp|mv)\s+.*>+", cmd):
                            file_writes.append((i, name + " (shell)", cmd[:120]))
        elif role == "user":
            user_msgs += 1
        elif role == "tool":
            tool_results += 1
            # Track tool-name diversity from tool-result metadata for the
            # "unique tool names" stat, but DO NOT add to tool_calls (that
            # would double-count when the assistant turn already declared it).
            meta = t.get("metadata") if isinstance(t.get("metadata"), dict) else {}
            tn = meta.get("toolName")
            if tn:
                # Push to a side-channel via the unique_tool_names path
                if not any(name == tn for _, name, _ in tool_calls):
                    # No assistant tool_call for this — record once
                    tool_calls.append((i, tn, "(from tool-result metadata — assistant tool_call not visible)"))

    # Tool category coverage
    cat_hits = {k: 0 for k in TOOL_CATEGORIES}
    for _i, name, _inp in tool_calls:
        for cat, patterns in TOOL_CATEGORIES.items():
            if name.startswith("mcp__"):
                cat_hits["mcp"] += 1
                break
            if any(p in name for p in patterns):
                cat_hits[cat] += 1
                break

    metrics = {
        "total_turns": n_turns,
        "assistant_text_turns": assistant_text_turns,
        "assistant_substantive_turns": assistant_substantive_turns,
        "tool_calls": len(tool_calls),
        "unique_tool_names": sorted(set(name for _, name, _ in tool_calls)),
        "file_writes": file_writes[:20],
        "user_messages": user_msgs,
        "tool_results": tool_results,
    }

    # Forced-finding triggers
    forced = []
    if len(tool_calls) == 0:
        forced.append({
            "dim": "7 Model Trajectory",
            "score": 2,
            "reason": f"Trajectory has 0 tool calls — agent never executed any workflow action. n_turns={n_turns}.",
            "evidence_path": f"{ae_step}.trajectory",
        })
        forced.append({
            "dim": "5 Trajectory Architectural Depth",
            "score": 2,
            "reason": "No meaningful tool dependency — agent never invoked a tool.",
            "evidence_path": f"{ae_step}.trajectory",
        })
    elif len(tool_calls) <= 2:
        forced.append({
            "dim": "5 Trajectory Architectural Depth",
            "score": 2,
            "reason": (
                f"Only {len(tool_calls)} tool calls in trajectory: "
                f"{', '.join(n for _, n, _ in tool_calls[:3])}. No multi-stage workflow."
            ),
            "evidence_path": f"{ae_step}.trajectory",
        })
        if not file_writes:
            forced.append({
                "dim": "7 Model Trajectory",
                "score": 2,
                "reason": "Trajectory shows no file-write operations despite ≤2 tool calls — workflow unattempted.",
                "evidence_path": f"{ae_step}.trajectory",
            })

    # Active categories count
    active_cats = [cat for cat, n in cat_hits.items() if n > 0]
    metrics["active_tool_categories"] = active_cats

    return {
        "step_id": ae_step,
        "verdict": "ok" if not forced else "fail_band",
        "metrics": metrics,
        "tool_call_categories": cat_hits,
        "forced_findings": forced,
    }


# ---------- gate 3: atomicity quantitative check (6a-c) -----------------------

# Patterns flagging a criterion's defect type and severity.
# Returns a list of (severity, kind) tuples. Severity ∈ {"major","moderate","minor"}.
# Kinds map to project_overrides.md §14/§9 categories.

BANNED_VOCAB = ["prose", "appropriate", "reasonable", "adequate", "good", "high-quality"]
SUBJECTIVE_HEDGES = ["ambiguous", "unclear", "loosely", "roughly", "approximately", "somewhat"]
PROCESS_VERBS = (
    "inspects", "considers", "reads", "reviews", "examines", "decides", "thinks",
    "shows at least one", "shows that", "shows the model", "uses (?:those|these|the)",
    "verifies", "demonstrates",
)


def _atomicity_severity(title: str) -> list[tuple[str, str]]:
    if not title:
        return []
    t = title.lower()
    issues: list[tuple[str, str]] = []

    # --- Major: process-targeting per §14f ---
    # Criterion names a literal tool action / agent process rather than an outcome.
    # Refinement: "trajectory shows X" is ONLY process-targeting when X is a
    # process-verb. "trajectory shows that when the model fails to read X, it
    # routes that photo to the discard section" has an outcome back-half
    # (artifact state: photo is in discard section) — that's not §14f.
    process_back_half = (
        r"\b(?:" + "|".join(PROCESS_VERBS) + r")\b"
        r"|\btool[\- ]call\b|\bweb[\- ](?:search|fetch|lookup)\b"
        r"|\b(?:reading|referencing|querying|calling|invoking|attempting|inspecting)\b"
    )
    if re.search(r"\btrajectory shows\b", t) and re.search(process_back_half, t):
        issues.append(("major", "process-targeting (§14f) — 'trajectory shows <process>' targets HOW agent works"))
    if re.search(r"\bin the trajectory[,]? the (?:agent|model) (?:reads|opens|invokes|calls|searches|fetches|retrieves)\b", t):
        issues.append(("major", "process-targeting (§14f) — names operation sequencing in trajectory"))
    if re.search(r"\btool[\- ]call\b|\bweb[\- ](?:search|fetch|lookup)\b", t) and \
       re.search(r"\bshows?\b|\bperforms?\b|\battempt(?:s|ed|ing)?\b", t):
        issues.append(("major", "process-targeting (§14f) — names a literal tool action instead of an outcome"))
    if re.search(r"\bbefore (?:deciding|composing|writing|inspecting|computing|beginning|starting|analyzing)\b", t):
        issues.append(("major", "process-targeting (§14f) — scores sequencing of operations, not output state"))
    if re.search(r"\bthe agent (?:" + "|".join(PROCESS_VERBS) + r")\b", t):
        issues.append(("major", "process-targeting (§14f) — names agent's mental process instead of artifact state"))

    # --- Major: not self-contained per §9f ---
    # Requires evaluator to access external context to decide PASS/FAIL
    if re.search(r"\blinked\b|\bthe (?:linked|provided) (?:page|url|product page)\b", t) and \
       re.search(r"\bconsistent\b|\bmatch(es|ing)?\b|\bsame as\b", t):
        issues.append(("major", "not self-contained (§9f) — requires external URL/page verification"))
    if re.search(r"\bcheck (?:the )?(?:url|link|page|site|server)\b", t):
        issues.append(("major", "not self-contained (§9f) — requires evaluator to verify external resource"))

    # --- Major: atomicity bundling N independent judgments ---
    # "For each X..." — bundles per-X decisions into single PASS/FAIL
    if re.search(r"\bfor each (?:of |)\b", t):
        # Count downstream facts via commas/and after the "for each" clause
        post = t.split("for each", 1)[1] if "for each" in t else ""
        facts = max(post.count(","), 0) + (1 if " and " in post else 0) + 1
        if facts >= 4:
            issues.append(("major", f"atomicity Rule C (§9a) — 'for each' bundles ≈{facts} facts per ranked item"))
        elif facts >= 3:
            issues.append(("moderate", f"atomicity (§9a) — 'for each' bundles ≈{facts} facts per ranked item"))
        else:
            issues.append(("minor", "mild atomicity — 'for each' bundles 2 facts"))

    # 4+ backtick-quoted items connected with AND → major bundling
    backticked = re.findall(r"`[^`]+`", title)
    if len(backticked) >= 4 and re.search(r"\band\b", t):
        issues.append(("major", f"atomicity (§9a) — bundles {len(backticked)} named items into one verdict"))
    elif len(backticked) == 3 and re.search(r"\band\b", t):
        issues.append(("moderate", "atomicity (§9a) — bundles 3 named items into one verdict"))

    # Multiple independent ANDs without "for each" — moderate atomicity
    ands = len(re.findall(r"\band\b", t))
    if ands >= 3 and "for each" not in t:
        issues.append(("moderate", f"atomicity (§9a) — {ands} ANDs bundle multiple independent facts"))

    # --- Moderate: file-existence check belongs in pytest (§9b) ---
    if re.search(r"\b(?:file|the file) [`'].+?[`']?\s*(?:is created|exists|is present|is at)", t) and \
       not any("contains" in c.get("title", "").lower() and any(part in c.get("title","").lower() for part in title.lower().split() if len(part) > 4)
               for c in []):  # placeholder — caller does the redundancy check
        # Plain existence is OK; mark only if there's no content check elsewhere — but
        # caller has full criteria list. Here we just flag as a candidate for §9b review.
        issues.append(("moderate", "file-existence check (§9b) — belongs in pytest if content is also checked elsewhere"))

    # --- Moderate: subjective hedge language ---
    for hedge in SUBJECTIVE_HEDGES:
        if re.search(rf"\b{hedge}\b", t):
            issues.append(("moderate", f"subjective language (§9f) — '{hedge}' without anchored definition"))
            break

    # --- Minor: banned project vocab (per v8 guidelines / §17) ---
    for v in BANNED_VOCAB:
        if re.search(rf"\b{v}\b", t):
            issues.append(("minor", f"banned vocab (§17) — '{v}' should be replaced with anchored term"))
            break

    return issues


def _is_redundant(criterion: dict, all_criteria: list) -> bool:
    """
    Existence-only criteria (file is created) are redundant if other criteria
    grade the file's contents (which implicitly assume existence).
    """
    title = (criterion.get("title") or "").lower()
    if not re.search(r"\bis created\b|\bexists at\b|\bworkspace contains\b", title):
        return False
    # Look for content-level criteria referencing the same file
    file_refs = re.findall(r"`/?[\w./_-]+\.(?:md|csv|json|py|txt|tar|zip)`", title)
    if not file_refs:
        return False
    target = file_refs[0]
    for other in all_criteria:
        if other is criterion:
            continue
        ot = other.get("title", "")
        if target in ot:
            # Found another criterion referencing the same file — likely content-level
            return True
    return False


def gate3_atomicity_check(active_step_id: str | None, before: dict) -> dict:
    """
    Count atomicity violations in the active rubric. Apply V3 spec thresholds:
      - 6a Major:    >10% major → FAIL
      - 6b Mod+Maj:  >15% → FAIL
      - 6c Any:      >20% → FAIL
    """
    if not active_step_id or active_step_id not in before:
        return {"verdict": "skip_no_active_step", "forced_findings": []}

    out = before[active_step_id].get("output", {}) if isinstance(before[active_step_id], dict) else {}
    crits = out.get("criteria", []) if isinstance(out, dict) else []
    if not isinstance(crits, list) or not crits:
        return {"verdict": "skip_no_criteria", "forced_findings": []}

    total = len(crits)
    # Set-based counting: each criterion contributes its WORST severity once.
    # (A criterion with 2 major + 1 moderate issues counts as 1 major.)
    crit_severity = {}  # criterion_id -> "major"|"moderate"|"minor"
    per_crit = []

    for c in crits:
        if not isinstance(c, dict):
            continue
        title = c.get("title", "")
        issues = _atomicity_severity(title)
        if _is_redundant(c, crits):
            issues.append(("moderate", "redundant — existence check shadowed by content-level criteria"))
        if not issues:
            continue
        # Worst severity wins per V3 counting rules
        order = {"major": 0, "moderate": 1, "minor": 2}
        worst = min(issues, key=lambda x: order[x[0]])[0]
        crit_severity[c.get("id") or title[:60]] = worst
        per_crit.append({
            "id": c.get("id"),
            "title_preview": title[:160],
            "worst_severity": worst,
            "all_issues": issues,
        })

    major_count = sum(1 for s in crit_severity.values() if s == "major")
    moderate_count = sum(1 for s in crit_severity.values() if s == "moderate")
    minor_count = sum(1 for s in crit_severity.values() if s == "minor")
    moderate_or_major = major_count + moderate_count
    any_severity = moderate_or_major + minor_count
    redundant_count = sum(1 for pc in per_crit if any("redundant" in i[1] for i in pc.get("all_issues", [])))
    process_targeting = sum(1 for pc in per_crit if any("process-targeting" in i[1] for i in pc.get("all_issues", [])))

    major_pct = major_count / total
    mod_pct = moderate_or_major / total
    any_pct = any_severity / total

    forced = []
    if major_pct > 0.10:
        forced.append({
            "dim": "6a Rubric Quality — Major",
            "score": 2,
            "reason": f"{major_count}/{total} criteria with major atomicity defects = {major_pct:.0%} (>10% threshold).",
            "evidence_path": f"{active_step_id}.criteria",
        })
    elif major_count > 0:
        forced.append({
            "dim": "6a Rubric Quality — Major",
            "score": 3,
            "reason": f"{major_count}/{total} criteria with major atomicity defects = {major_pct:.0%} (≤10%).",
            "evidence_path": f"{active_step_id}.criteria",
        })

    if mod_pct > 0.15:
        forced.append({
            "dim": "6b Rubric Quality — Major/Moderate",
            "score": 2,
            "reason": f"{moderate_or_major}/{total} criteria with moderate-or-major defects = {mod_pct:.0%} (>15% threshold).",
            "evidence_path": f"{active_step_id}.criteria",
        })
    elif moderate_or_major > 0 and major_pct < 0.05:
        forced.append({
            "dim": "6b Rubric Quality — Major/Moderate",
            "score": 3,
            "reason": f"{moderate_or_major}/{total} = {mod_pct:.0%} ≤15%, major <5%.",
            "evidence_path": f"{active_step_id}.criteria",
        })

    if any_pct > 0.20:
        forced.append({
            "dim": "6c Rubric Quality — Major/Moderate/Minor",
            "score": 2,
            "reason": f"{any_severity}/{total} criteria with any-severity defects = {any_pct:.0%} (>20% threshold).",
            "evidence_path": f"{active_step_id}.criteria",
        })

    return {
        "verdict": "ok" if not forced else "fail_band",
        "total_criteria": total,
        "major_count": major_count,
        "moderate_count": moderate_count,
        "redundant_count": redundant_count,
        "process_targeting": process_targeting,
        "major_pct": round(major_pct, 4),
        "mod_or_maj_pct": round(mod_pct, 4),
        "any_severity_pct": round(any_pct, 4),
        "per_criterion_flags": per_crit,
        "forced_findings": forced,
    }


# ---------- gate 5: category-mismatch check -----------------------------------

# Category-typical lexicon (lower-case keywords). Used to verify that the
# claimed category_subcategory matches the rubric content.
CATEGORY_LEXICON = {
    "operations & qa": ["inventory", "audit", "receipt", "document", "ui", "form", "queue", "ticket"],
    "creative & media": ["moodboard", "image", "video", "design", "portfolio", "social", "post", "edit"],
    "visual learning": ["homework", "lab", "textbook", "lecture", "problem", "study"],
    "commerce & product": ["product", "listing", "shopping", "compare", "brand", "packaging", "sku"],
    "health & wellness": ["meal", "nutrition", "symptom", "skin", "calorie", "protein", "exercise"],
    "property & space": ["listing", "real estate", "vacancy", "tenant", "renovation", "interior"],
}


def gate5_category_mismatch(before: dict, active_step_id: str | None) -> dict:
    """Check that the claimed category_subcategory matches the rubric content."""
    cat_step = None
    cat_value = ""
    for sid, step in before.items():
        out = step.get("output", {}) if isinstance(step, dict) else {}
        if isinstance(out, dict) and "category_subcategory" in out:
            cat_step = sid
            cat_value = out["category_subcategory"]
            break

    if not cat_value:
        return {"verdict": "no_category_field", "forced_findings": []}

    # Extract just the category part (before " - " or " — ")
    parts = re.split(r"\s*[-—]\s*", cat_value, maxsplit=1)
    category_main = parts[0].lower().strip()

    lexicon = CATEGORY_LEXICON.get(category_main)
    if not lexicon:
        return {
            "verdict": "unknown_category",
            "category_main": category_main,
            "forced_findings": [],
        }

    # Collect rubric content (titles + agent_objective + desired_outcome)
    blob = ""
    if active_step_id and active_step_id in before:
        out = before[active_step_id].get("output", {})
        for c in out.get("criteria", []):
            if isinstance(c, dict):
                blob += " " + (c.get("title") or "")
    for sid, step in before.items():
        if sid.startswith("step-1771366239685") or "PromptInput" in sid:
            out = step.get("output", {}) if isinstance(step, dict) else {}
            for fk, fv in out.items():
                if isinstance(fv, str):
                    blob += " " + fv

    blob_lower = blob.lower()
    hits = sum(1 for kw in lexicon if kw in blob_lower)
    hit_ratio = hits / max(len(lexicon), 1)

    # Subcategory-specific "anchor terms" — if claimed subcategory's anchor
    # appears 0 times in the rubric content, that's a FAIL regardless of
    # global lexicon hit count. This catches cases like T1 (claimed "Inventory
    # Visual Audit" but rubric is a meal plan — "inventory" appears 0 times).
    subcategory_anchors = {
        "inventory visual audit":   ["inventory", "stock", "sku", "warehouse"],
        "document/receipt processing": ["receipt", "invoice", "document"],
        "ui/ux screenshot audit":   ["ui", "ux", "screen", "button", "form"],
        "nutrition/meal logging":   ["meal", "nutrition", "calorie", "protein"],
        "skin/symptom triage":      ["skin", "symptom", "rash", "lesion"],
        "real estate listing review": ["listing", "vacancy", "tenant", "property"],
        "design/portfolio review":  ["moodboard", "portfolio", "design", "image", "moodboard"],
        "image/video editing":      ["edit", "video", "crop", "filter"],
        "social media content audit": ["post", "social", "caption", "hashtag"],
        "homework/problem solving": ["homework", "problem", "solve", "study"],
        "textbook/lecture comprehension": ["textbook", "lecture", "chapter", "concept"],
        "lab/fieldwork documentation": ["lab", "experiment", "field", "data"],
        "visual shopping/comparison": ["shop", "compare", "price", "product"],
        "product listing qa":       ["product", "listing", "sku", "title"],
        "brand/packaging audit":    ["brand", "packaging", "logo", "label"],
        "interior design/renovation": ["interior", "renovation", "room", "furniture"],
    }
    sub = parts[1].lower().strip() if len(parts) > 1 else ""
    anchor_hits = None
    if sub in subcategory_anchors:
        anchor_terms = subcategory_anchors[sub]
        anchor_hits = sum(1 for kw in anchor_terms if kw in blob_lower)

    forced = []
    if hits == 0:
        forced.append({
            "dim": "1a Categorization / 4a Silver Trajectory Category",
            "score": 2,
            "reason": (
                f"Claimed category '{cat_value}' has ZERO lexicon-matches in rubric/prompt content "
                f"(checked {len(lexicon)} category-typical terms). Likely mislabel."
            ),
            "evidence_path": f"{cat_step}.category_subcategory",
        })
    elif anchor_hits == 0:
        # Subcategory anchor terms appear nowhere — this is the strong signal
        forced.append({
            "dim": "1a Categorization / 4a Silver Trajectory Category",
            "score": 2,
            "reason": (
                f"Claimed subcategory '{sub}' has ZERO anchor-term matches in rubric content "
                f"(anchors: {subcategory_anchors[sub]}). Rubric content describes a different task than the labeled subcategory."
            ),
            "evidence_path": f"{cat_step}.category_subcategory",
        })
    elif hit_ratio < 0.30:
        forced.append({
            "dim": "1a Categorization",
            "score": 3,
            "reason": (
                f"Claimed category '{cat_value}' has only {hits}/{len(lexicon)} lexicon matches "
                f"({hit_ratio:.0%} < 30%). Borderline mislabel — manual review recommended."
            ),
            "evidence_path": f"{cat_step}.category_subcategory",
        })

    return {
        "verdict": "ok" if not forced else "mismatch",
        "category_step": cat_step,
        "category_value": cat_value,
        "category_main": category_main,
        "lexicon_hits": hits,
        "lexicon_total": len(lexicon),
        "lexicon_hit_ratio": round(hit_ratio, 3),
        "subcategory": sub,
        "subcategory_anchor_hits": anchor_hits,
        "forced_findings": forced,
    }


# ---------- gate 6: coverage cross-check vs desired_outcome -------------------

# Files-in-prose pattern: catches /path/to/file.md, `file.csv`, file.tar.gz
FILE_RE = re.compile(r"`?[\w./_-]+\.(?:md|csv|json|py|tar(?:\.gz)?|zip|txt|yml|yaml|sh)`?", re.IGNORECASE)


def gate6_coverage_check(active_step_id: str | None, before: dict) -> dict:
    """
    Extract required-output filenames from desired_outcome / agent_objective.
    Check that each appears in at least one rubric criterion title.
    """
    if not active_step_id or active_step_id not in before:
        return {"verdict": "skip_no_active_step", "forced_findings": []}

    # Required artifacts from desired_outcome + agent_objective
    required = set()
    for sid, step in before.items():
        if not sid.startswith("step-1771366239685"):
            continue
        out = step.get("output", {}) if isinstance(step, dict) else {}
        for fk, fv in out.items():
            if not isinstance(fv, str):
                continue
            for m in FILE_RE.findall(fv):
                clean = m.strip("`").lower()
                # Drop common non-artifact false positives
                if any(skip in clean for skip in ["http://", "https://", "example.com", "memory.md]"]):
                    continue
                # Keep only the filename, not the full path
                fn = clean.split("/")[-1]
                if fn:
                    required.add(fn)

    # Files referenced in active-rubric criterion titles. Normalize the blob
    # to defeat markdown-link wrapping that contributors sometimes apply to
    # filenames — e.g. `sofia_lens\_[comparison.md](http://comparison.md)`
    # should match the literal filename `sofia_lens_comparison.md`.
    rubric_blob = ""
    crits = before[active_step_id].get("output", {}).get("criteria", [])
    for c in crits:
        if isinstance(c, dict):
            rubric_blob += " " + (c.get("title") or "")

    def _normalize(s: str) -> str:
        # Strip backslash-escapes
        s = s.replace("\\_", "_").replace("\\.", ".").replace("\\-", "-")
        # Collapse markdown-link wrapping `[text](url)` → `text`
        s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
        # Drop backticks and stray punctuation that splits filename parts
        s = s.replace("`", " ").replace("[", " ").replace("]", " ").replace("(", " ").replace(")", " ")
        return s.lower()

    rubric_norm = _normalize(rubric_blob)

    unscored = []
    for req in sorted(required):
        # Try both the verbatim filename and a "stem in proximity to extension"
        # fallback (e.g. `sofia_lens_comparison.md` may appear as
        # `sofia_lens_comparison` + nearby `.md` after normalization).
        if req in rubric_norm:
            continue
        stem, _, ext = req.rpartition(".")
        # Look for the stem and the extension within a 40-char window
        m = re.search(re.escape(stem) + r".{0,40}\." + re.escape(ext), rubric_norm)
        if m:
            continue
        # Also try splitting the stem on underscores and require all tokens
        # appear within a small window followed by the extension
        stem_parts = [p for p in stem.split("_") if len(p) > 2]
        if stem_parts:
            pat = r"\b" + r"[\s\W_]{0,8}".join(re.escape(p) for p in stem_parts) + r"[\s\W_]{0,30}\." + re.escape(ext)
            if re.search(pat, rubric_norm):
                continue
        unscored.append(req)

    forced = []
    if unscored:
        forced.append({
            "dim": "6a Rubric Quality — Coverage / 9 Overall Quality",
            "score": 2,
            "reason": (
                f"{len(unscored)} required output(s) not scored by any criterion: {', '.join(unscored)}. "
                f"Required artifacts derived from desired_outcome/agent_objective."
            ),
            "evidence_path": f"{active_step_id}.criteria + step-1771366239685.desired_outcome",
        })

    return {
        "verdict": "ok" if not forced else "missing_coverage",
        "required_artifacts": sorted(required),
        "unscored_artifacts": unscored,
        "forced_findings": forced,
    }


# ---------- gate 7: contributor-note leak detection ---------------------------

LEAK_PATTERNS = [
    r"\bgive me the original\b",
    r"\btell me as well\b",
    r"\btrying to cause\b",
    r"\bfix it with the future\b",
    r"\b≥50%? threshold\b",
    r"\bwhich.{0,12}files can i delete\b",
    r"\b@/Users/[^\s]+\b",     # leaked local file paths
    r"^Claude:|\bAs an AI\b",  # leaked AI turn-of-phrase
]


def gate7_contributor_note_leak(before: dict) -> dict:
    """Scan universe data for contributor working-notes leaks."""
    findings = []
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
                    findings.append({
                        "step": sid,
                        "field": fk,
                        "pattern": pat,
                        "excerpt": fv[max(0, m.start()-40):m.end()+40],
                    })

    forced = []
    if findings:
        forced.append({
            "dim": "9 Overall Quality",
            "score": 2,
            "reason": (
                f"Detected {len(findings)} contributor-note leak(s) in universe data — "
                f"working notes accidentally committed to agent_objective/desired_outcome."
            ),
            "evidence_path": ", ".join(f"{f['step']}.{f['field']}" for f in findings[:3]),
        })

    return {
        "verdict": "ok" if not findings else "leaks_found",
        "leaks": findings,
        "forced_findings": forced,
    }


# ---------- gate runner --------------------------------------------------------

def run_gates(task_json_path: Path, out_path: Path) -> dict:
    with open(task_json_path) as f:
        task = json.load(f)

    # Find the RESPONSE blob — fetch may have wrapped it
    response = task.get("response") or task
    before = response.get("before", {}) if isinstance(response, dict) else {}

    if not before:
        # Try task.inline_form_data.before (alternate wrap)
        inline = task.get("inline_form_data") or {}
        before = inline.get("before", {}) or {}
    if not before and "before" in task:
        before = task["before"]

    if not before:
        report = {
            "task_path": str(task_json_path),
            "gate_status": "no_before_block",
            "forced_findings": [{
                "dim": "audit_incomplete",
                "score": None,
                "reason": "No response.before block — task may be CDS-pointer shape. Try gate-4 signed-URL fetch."
            }],
        }
        with open(out_path, "w") as f:
            json.dump(report, f, indent=2)
        return report

    # Run gates 1-3, 5-7 (gate 4 is the fetch fallback, run by the fetcher)
    g1 = gate1_active_rubric_step(before)
    active_id = g1.get("active_step_id")

    g2 = gate2_trajectory_inspection(before)
    g3 = gate3_atomicity_check(active_id, before)
    g5 = gate5_category_mismatch(before, active_id)
    g6 = gate6_coverage_check(active_id, before)
    g7 = gate7_contributor_note_leak(before)

    all_forced = (
        g1["forced_findings"] + g2["forced_findings"] + g3["forced_findings"]
        + g5["forced_findings"] + g6["forced_findings"] + g7["forced_findings"]
    )

    report = {
        "task_path": str(task_json_path),
        "active_rubric_step": active_id,
        "gate_1_active_step": g1,
        "gate_2_trajectory": g2,
        "gate_3_atomicity": g3,
        "gate_5_category": g5,
        "gate_6_coverage": g6,
        "gate_7_leaks": g7,
        "forced_findings_count": len(all_forced),
        "forced_findings": all_forced,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task-json", help="single task JSON path")
    ap.add_argument("--task-dir", help="directory of <task_id>.json files")
    ap.add_argument("--out", help="output path (single mode)")
    ap.add_argument("--out-dir", help="output directory (batch mode)")
    args = ap.parse_args()

    if args.task_json:
        out = Path(args.out) if args.out else Path(args.task_json).with_suffix(".gates.json")
        r = run_gates(Path(args.task_json), out)
        print(f"Wrote {out} — {r['forced_findings_count']} forced findings", file=sys.stderr)
    elif args.task_dir:
        if not args.out_dir:
            print("--out-dir required with --task-dir", file=sys.stderr)
            sys.exit(2)
        out_dir = Path(args.out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        for p in Path(args.task_dir).glob("*.json"):
            out = out_dir / f"{p.stem}.gates.json"
            r = run_gates(p, out)
            print(f"{p.stem}: {r['forced_findings_count']} forced findings", file=sys.stderr)
    else:
        ap.print_help()
        sys.exit(2)


if __name__ == "__main__":
    main()
