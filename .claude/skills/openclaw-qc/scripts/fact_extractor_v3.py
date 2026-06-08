#!/usr/bin/env python3
"""
QC AUDITOR v3 — FACT EXTRACTOR + ROUTER (replaces the "forced gates" model).

The v2 gates EMITTED VERDICTS the swarm was forced to inherit (recall-tuned,
~81% FP at L0). v3 inverts that: this module emits only

  * FACTS   — structurally certain, ~zero-FP statements the swarm treats as
              authoritative (active step, trajectory metrics, weight-set
              validity, leak strings, phantom filenames, platform scores) PLUS
              the three SOURCE-OF-TRUTH layers (agent prompt, input artifacts,
              active rubric).
  * ROUTES  — work-orders telling a judgment agent WHERE to look (vision queue,
              safety candidate, category candidate). No verdict attached.
  * HINTS   — the old recall-tuned heuristics (atomicity §9a, prompt-walk,
              ratings-sanity, hidden-conjunctions, process-targeting,
              self-containment). Surfaced but NEVER forced; the swarm may ignore.

It writes a per-task `sot/<task_id>/` bundle the swarm reads INSTEAD of poking
at the raw task JSON. Critically: it NEVER reads or surfaces
`story.desired_outcome` (the contributor's answer key — grounding requirements
in it is circular). The agent-facing prompt is the real one at
`response.before["step-PromptInput-*"].output.content`.

Reuses the deterministic gate functions from preaudit_checks_v2.py (active-step
resolver, trajectory, coverage, leaks, score, negative-ratio, weights, phantom-
filename, and the category/safety/vision routers) so v2 stays the legacy path.

Usage:
    python3 fact_extractor_v3.py --task-json <path> --out-dir <ws>/sot/ [--spec <spec.md>]
    python3 fact_extractor_v3.py --task-dir <dir>  --out-dir <ws>/sot/ [--spec <spec.md>]
"""
import argparse
import importlib.util
import io
import json
import os
import re
import sys
import zipfile
from pathlib import Path

V2_PATH = Path(__file__).with_name("preaudit_checks_v2.py")
ACTIVE_FALLBACK = "step-1772171628343-3n5s2m"  # canonical OpenClaw active-rubric step id
_IMG_RE = re.compile(r"\.(jpe?g|png|heic|heif|webp|gif|bmp|tiff?)$", re.I)


def _load_v2():
    spec = importlib.util.spec_from_file_location("preaudit_checks_v2", V2_PATH)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _resp(task):
    r = task.get("response") or task
    if isinstance(r, str):
        try:
            r = json.loads(r)
        except Exception:
            r = {}
    before = r.get("before", {}) if isinstance(r, dict) else {}
    if not before and isinstance(task.get("inline_form_data"), dict):
        before = task["inline_form_data"].get("before", {}) or {}
    return r if isinstance(r, dict) else {}, before


# ---------------------------------------------------------------------------
# D0 — source-of-truth layers (NO desired_outcome, ever)
# ---------------------------------------------------------------------------
def _is_noise_turn(c):
    """True for system/heartbeat user turns that are NOT the task prompt
    (e.g. "[OpenClaw heartbeat poll]"). Skipping these stops the extractor from
    grounding the audit in a heartbeat instead of the real instruction."""
    cl = c.strip().lower()
    if "heartbeat" in cl:
        return True
    if cl.startswith("[") and cl.endswith("]") and len(cl) < 80:
        return True
    return False


def _live_conversation_prompt(before):
    """The prompt the model ACTUALLY received: the first SUBSTANTIVE user-role turn of
    the live conversation (step-AgentExecution-*.output.conversationHistory) — skipping
    heartbeat/system turns. The true ground truth; can DIVERGE from step-PromptInput
    (see task 6a17cc59ea9a7319a6ca06d9)."""
    for sid, v in before.items():
        if "AgentExecution" in sid and isinstance(v, dict):
            conv = (v.get("output") or {}).get("conversationHistory")
            if isinstance(conv, list):
                user_turns = [t["content"].strip() for t in conv
                              if isinstance(t, dict) and t.get("role") == "user"
                              and isinstance(t.get("content"), str) and t.get("content").strip()]
                for c in user_turns:
                    if not _is_noise_turn(c):
                        return c, sid
                if user_turns:                       # all noise -> longest user turn
                    return max(user_turns, key=len), sid
    return "", None


def _promptinput_prompt(before):
    for sid, v in before.items():
        if "PromptInput" in sid and isinstance(v, dict):
            c = (v.get("output") or {}).get("content")
            if isinstance(c, str) and c.strip():
                return c.strip(), sid
    return "", None


def _prompt_drift(live, pin):
    """Flag when step-PromptInput materially differs from the live conversation —
    the failure mode that hid the C2/C5 misalignment on d9."""
    if not live or not pin:
        return None
    norm = lambda x: " ".join(x.lower().split())
    if norm(live) == norm(pin):
        return None
    heads = lambda x: set(re.findall(r'(?:^|\n)\s*#{0,3}\s*\d+\.\s*([a-z0-9 /&\-]{3,50})', x.lower()))
    hl, hp = heads(live), heads(pin)
    return {
        "verdict": "prompt_version_drift",
        "note": ("step-PromptInput differs from the LIVE conversation the model received; "
                 "the audit grounds in the LIVE conversation. Criteria that match the stale "
                 "PromptInput but not the live prompt are Incorrect Criteria (Major)."),
        "headings_only_in_live_prompt": sorted(hl - hp)[:8],
        "headings_only_in_promptinput_stale": sorted(hp - hl)[:8],
    }


def extract_agent_prompt(before):
    """The REAL agent-facing prompt = the LIVE conversation the model received
    (step-AgentExecution.conversationHistory, first user turn) — authoritative.
    step-PromptInput is a FALLBACK and can be STALE; when it diverges we emit a
    prompt_version_drift FACT. step-PromptTextCollection is the last resort.
    NEVER falls back to desired_outcome. Returns (text, step_id, status, drift)."""
    live, live_sid = _live_conversation_prompt(before)
    pin, pin_sid = _promptinput_prompt(before)
    # Sanity: if the live turn is far shorter than a substantive PromptInput, the live
    # extraction likely grabbed a fragment/system turn (e.g. a heartbeat poll) -> prefer
    # PromptInput as the task prompt. (task 6a0ffe25088789f616666863: live was a heartbeat.)
    if live and pin and len(pin) > 200 and len(live) < 0.5 * len(pin):
        return pin, pin_sid, "ok_promptinput_live_too_short", _prompt_drift(live, pin)
    if live:
        drift = _prompt_drift(live, pin) if pin else None
        status = "ok_live_conversation" + ("_DRIFT_vs_promptinput" if drift else "")
        return live, live_sid, status, drift
    if pin:
        return pin, pin_sid, "ok_promptinput_no_conversation", None
    for sid, v in before.items():
        if "PromptTextCollection" in sid and isinstance(v, dict):
            out = v.get("output") or {}
            c = out.get("main_request_summary") or out.get("content")
            if isinstance(c, str) and c.strip():
                return c.strip(), sid, "fallback_main_request_summary", None
    return "", None, "audit_incomplete_no_prompt", None


def extract_active_rubric(before, active_step_id):
    sid = active_step_id if active_step_id in before else (
        ACTIVE_FALLBACK if ACTIVE_FALLBACK in before else None)
    if not sid:
        return [], None
    out = before[sid].get("output", {}) if isinstance(before[sid], dict) else {}
    crits = out.get("criteria", []) if isinstance(out, dict) else []
    return crits, sid


def download_inputs(task, outdir):
    """Download + extract input artifacts; keep images as files for vision.
    Best-effort PDF/text extraction. Returns (manifest, notes)."""
    os.makedirs(outdir, exist_ok=True)
    ifd = (task.get("inline_form_data") or {}) if isinstance(task, dict) else {}
    story = ifd.get("story") or {}
    manifest, notes = [], []
    sources = (story.get("zip_folder") or []) + (story.get("source_screenshot") or [])
    for z in sources:
        url = (z.get("s3Url") or z.get("cdsUrl")) if isinstance(z, dict) else None
        if not url or not str(url).startswith("http"):
            continue
        try:
            import urllib.request
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                blob = resp.read()
        except Exception as e:
            notes.append(f"download failed for {str(url)[:60]}: {e}")
            continue
        name = (z.get("name") if isinstance(z, dict) else None) or "artifact"
        if name.lower().endswith(".zip") or blob[:2] == b"PK":
            try:
                with zipfile.ZipFile(io.BytesIO(blob)) as zf:
                    for n in zf.namelist():
                        if "__MACOSX" in n or n.endswith("/"):
                            continue
                        zf.extract(n, outdir)
                        manifest.append(os.path.basename(n))
            except Exception as e:
                notes.append(f"unzip failed for {name}: {e}")
        else:
            p = os.path.join(outdir, os.path.basename(name))
            with open(p, "wb") as fh:
                fh.write(blob)
            manifest.append(os.path.basename(name))
    # best-effort text extraction of PDFs/text for non-vision criteria
    for fn in list(manifest):
        p = os.path.join(outdir, fn)
        if fn.lower().endswith(".pdf") and os.path.exists(p):
            txt = _pdf_text(p)
            if txt:
                open(p + ".txt", "w").write(txt)
                notes.append(f"extracted text: {fn}.txt")
    return sorted(set(manifest)), notes


def _pdf_text(path):
    for mod in ("pypdf", "PyPDF2"):
        try:
            m = __import__(mod)
            rd = m.PdfReader(path)
            return "\n".join((pg.extract_text() or "") for pg in rd.pages)
        except Exception:
            continue
    try:
        import subprocess
        r = subprocess.run(["pdftotext", path, "-"], capture_output=True, text=True, timeout=30)
        if r.returncode == 0:
            return r.stdout
    except Exception:
        pass
    return ""


# ---------------------------------------------------------------------------
# FACTS / ROUTES / HINTS
# ---------------------------------------------------------------------------
def build_facts(v2, task, before, active_id):
    facts = {}
    try:
        facts["trajectory"] = v2.gate2_trajectory(before)
    except Exception as e:
        facts["trajectory"] = {"error": str(e)}
    try:
        facts["coverage_gaps"] = v2.gate6_coverage(active_id, before)
    except Exception as e:
        facts["coverage_gaps"] = {"error": str(e)}
    try:
        facts["leaks"] = v2.gate7_leaks(before)
    except Exception as e:
        facts["leaks"] = {"error": str(e)}
    try:
        facts["platform_score"] = v2.gate12_score_grounding(before, None, top_level=task)
    except Exception as e:
        facts["platform_score"] = {"error": str(e)}
    try:
        facts["negative_ratio"] = v2.gate15_negative_ratio(active_id, before)
    except Exception as e:
        facts["negative_ratio"] = {"error": str(e)}
    try:
        facts["weight_validity"] = v2.gate16_weight_calibration(active_id, before)
    except Exception as e:
        facts["weight_validity"] = {"error": str(e)}
    try:
        g18 = v2.gate18_image_grounding(active_id, before, task)
        facts["phantom_image_filenames"] = g18.get("phantom_findings", [])
    except Exception as e:
        facts["phantom_image_filenames"] = []
    return facts


def build_routes(v2, task, before, active_id):
    routes = {}
    try:
        g18 = v2.gate18_image_grounding(active_id, before, task)
        routes["vision_queue"] = g18.get("vision_queue", [])
    except Exception:
        routes["vision_queue"] = []
    try:
        routes["category_candidate"] = v2.gate5_category(before, active_id)
    except Exception as e:
        routes["category_candidate"] = {"error": str(e)}
    try:
        routes["safety_candidate"] = v2.gate11_safety_heuristic(before)
    except Exception as e:
        routes["safety_candidate"] = {"error": str(e)}
    return routes


def build_hints(v2, before, active_id):
    """Recall-tuned heuristics — surfaced as IGNORABLE hints, never forced."""
    hints = {}
    for name, fn in (("atomicity", lambda: v2.gate3_atomicity_v2(active_id, before)),
                     ("process_targeting", lambda: v2.gate3b_process_targeting(active_id, before)),
                     ("self_containment", lambda: v2.gate3c_self_containment_strict(active_id, before, {})),
                     ("ratings_sanity", lambda: v2.gate10_ratings_sanity(before, active_id)),
                     ("prompt_walk", lambda: v2.gate13_prompt_coverage(before, active_id))):
        try:
            hints[name] = fn()
        except Exception as e:
            hints[name] = {"error": str(e)}
    return hints


def run(task_path, out_root, spec_path=None):
    task = json.load(open(task_path))
    tid = task.get("task_id") or Path(task_path).stem
    resp, before = _resp(task)
    out = Path(out_root) / tid
    out.mkdir(parents=True, exist_ok=True)
    v2 = _load_v2()

    # active rubric (Rule 12)
    try:
        active_id = v2.gate1_active_rubric_step(before).get("active_step_id")
    except Exception:
        active_id = None
    crits, active_id = extract_active_rubric(before, active_id)

    # D0 layers
    prompt_text, prompt_step, prompt_status, prompt_drift = extract_agent_prompt(before)
    manifest, input_notes = download_inputs(task, str(out / "inputs"))

    # write agent_prompt.md
    drift_banner = ""
    if prompt_drift:
        drift_banner = (
            f"> \u26a0\ufe0f PROMPT-VERSION DRIFT — step-PromptInput is STALE vs the live conversation the model received.\n"
            f"> This file is the LIVE conversation (authoritative). Headings only in the live prompt: "
            f"{prompt_drift.get('headings_only_in_live_prompt')}; only in the stale PromptInput: "
            f"{prompt_drift.get('headings_only_in_promptinput_stale')}.\n"
            f"> Grade criteria against THIS prompt; criteria that match the stale PromptInput are Incorrect Criteria (Major).\n\n")
    (out / "agent_prompt.md").write_text(
        f"# Agent-facing prompt — task {tid}\n\n"
        f"source: `{prompt_step}` · status: {prompt_status}\n\n"
        + drift_banner +
        f"> NOTE: This is the ACTUAL prompt the agent received (the LIVE conversation). It is the\n"
        f"> ONLY grounding source for 'required by prompt'. desired_outcome is intentionally NOT included.\n\n"
        f"---\n\n{prompt_text or '(no agent-facing prompt found — D3 prompt-grounding = audit_incomplete)'}\n")

    # write active_rubric.md
    rb = [f"# Active rubric (step `{active_id}`) — {len(crits)} criteria — task {tid}\n"]
    for i, c in enumerate(crits, 1):
        rb.append(f"\n## C{i}. [{(c.get('id') or '')[:8]}] (weight {c.get('weight')})\n"
                  f"{c.get('title','')}")
        ann = c.get("annotations") or {}
        if isinstance(ann, dict) and ann:
            rb.append(f"_annotations: {json.dumps(ann)}_")
    (out / "active_rubric.md").write_text("\n".join(rb))

    # inputs listing
    img = [f for f in manifest if _IMG_RE.search(f)]
    (out / "inputs" / "LISTING.md").write_text(
        f"# Input artifacts — task {tid}\n\nfiles ({len(manifest)}): "
        + ", ".join(manifest) + f"\n\nimages to VIEW ({len(img)}): " + ", ".join(img)
        + ("\n\nnotes: " + "; ".join(input_notes) if input_notes else "") + "\n")

    # spec catalog pointer
    if spec_path and Path(spec_path).exists():
        (out / "spec_catalog.md").write_text(Path(spec_path).read_text())

    facts = build_facts(v2, task, before, active_id)
    facts["prompt_version_drift"] = prompt_drift or {"verdict": "ok"}
    routes = build_routes(v2, task, before, active_id)
    hints = build_hints(v2, before, active_id)

    sot = {
        "task_id": tid,
        "v": "3.0-beta",
        "agent_prompt": {"step": prompt_step, "status": prompt_status, "chars": len(prompt_text), "drift": prompt_drift},
        "active_rubric_step": active_id,
        "criteria_count": len(crits),
        "input_files": manifest,
        "input_images_to_view": img,
        "desired_outcome_used": False,   # invariant — v3 never reads it
        "passatk_used": False,           # invariant — v3 never uses platform grader as evidence
    }
    (out / "sot.json").write_text(json.dumps(sot, indent=2))
    (out / "facts.json").write_text(json.dumps(facts, indent=2, default=str))
    (out / "routes.json").write_text(json.dumps(routes, indent=2, default=str))
    (out / "hints.json").write_text(json.dumps(hints, indent=2, default=str))
    return sot


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task-json")
    ap.add_argument("--task-dir")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--spec")
    a = ap.parse_args()
    paths = []
    if a.task_json:
        paths = [a.task_json]
    elif a.task_dir:
        paths = sorted(str(p) for p in Path(a.task_dir).glob("*.json"))
    else:
        ap.print_help(); sys.exit(2)
    for p in paths:
        try:
            s = run(p, a.out_dir, a.spec)
            print(f"{s['task_id']}: prompt={s['agent_prompt']['status']}({s['agent_prompt']['chars']}c) "
                  f"crit={s['criteria_count']} imgs={len(s['input_images_to_view'])}", file=sys.stderr)
        except Exception as e:
            print(f"{Path(p).stem}: ERROR {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
