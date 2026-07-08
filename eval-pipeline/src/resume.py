"""src/resume.py — harvest LLM-check results from their Workflow transcripts (durable in
~/.claude, survive scratchpad wipes), schema-validate, normalize to the common finding schema,
and write <run_dir>/findings_llm.json. Reports any tasks still missing so Claude can re-run them.

Usage:
  python -m src.resume --run-dir R --cdq-out F --cdq-tdir D --audit-out F2 --audit-tdir D2

Each --*-out is the Workflow task .output file; each --*-tdir is its transcript dir. Either may
be omitted; harvest falls back to the other. Idempotent — merges into any existing findings_llm.json.
"""
from __future__ import annotations
import argparse, glob, json
from pathlib import Path

SEV2TIER = {"Major": "action_required", "Moderate": "review_recommended", "Minor": "review_recommended"}


def _dim2defect(dim: str) -> str:
    d = (dim or "").lower()
    if "leak" in d: return "ORACLE_LEAK"
    if "safety" in d: return "TOOL_FAILURE" if "tool" in d else "RUBRIC_UNFAIR"
    if "mm" in d or "modal" in d or "visual" in d: return "MULTIMODAL_ARTIFACT"
    if "test" in d: return "RUBRIC_OVERSPEC"
    if "realism" in d or "artifact" in d or "input" in d or "sparse" in d or "data" in d: return "DATA_SPARSE"
    if "feasib" in d or "tool" in d or "environment" in d or "container" in d: return "TOOL_FAILURE"
    if "prompt" in d or "unclear" in d: return "SP_UNCLEAR"
    return "RUBRIC_CONTRADICTION"


def _iter_records(outfile, tdir, signature):
    """Yield candidate result dicts from a workflow output file (result[]) and/or transcripts."""
    seen_from_output = False
    if outfile and Path(outfile).exists() and Path(outfile).stat().st_size > 0:
        try:
            obj = json.load(open(outfile)); res = obj.get("result")
            if isinstance(res, str): res = json.loads(res)
            for r in (res or []):
                yield r
            seen_from_output = True
        except Exception:
            pass
    if tdir and Path(tdir).is_dir():
        for j in glob.glob(f"{tdir}/*.jsonl"):
            txt = open(j, errors="ignore").read()
            if signature not in txt:
                continue
            for line in txt.splitlines():
                if signature not in line:
                    continue
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                st = [rec]
                while st:
                    x = st.pop()
                    if isinstance(x, dict):
                        if x.get("task_id") and signature.strip('"') in x:
                            yield x
                        st.extend(x.values())
                    elif isinstance(x, list):
                        st.extend(x)


def harvest_cdq(outfile, tdir):
    """CDQ static findings are already in the common shape."""
    by = {}
    for r in _iter_records(outfile, tdir, '"findings"'):
        tid = r.get("task_id")
        if not tid or "findings" not in r or not isinstance(r["findings"], list):
            continue
        norm = []
        for f in r["findings"]:
            if not isinstance(f, dict):
                continue
            norm.append({"check": "cdq_static", "defect_type": f.get("defect_type", "RUBRIC_CONTRADICTION"),
                         "tier": f.get("tier", "review_recommended"), "rubric_ids": f.get("rubric_ids", []),
                         "test_names": f.get("test_names", []), "explanation": f.get("explanation", ""),
                         "fix": f.get("fix", ""), "evidence": ""})
        by[tid] = norm       # last write wins (latest transcript)
    return by


def harvest_audit(outfile, tdir):
    """Audit master = the DRAWER eval. Normalize its Task-level flags[{dimension,category,severity,
    reason,fix,spec_ref}] into common findings (severity Fail->action_required, Non-Fail->review).
    The band label (category) is preserved in the explanation so the sheet shows e.g.
    '[Fail - 15%+ Moderate Rubric Errors]'."""
    by = {}
    for r in _iter_records(outfile, tdir, '"agreement"'):
        tid = r.get("task_id")
        if not tid or "flags" not in r or "agreement" not in r:
            continue
        norm = []
        for f in r.get("flags", []):
            if not isinstance(f, dict):
                continue
            cat = f.get("category", "")
            tier = "action_required" if str(f.get("severity", "")).lower().startswith("fail") else "review_recommended"
            norm.append({"check": "audit_hybrid31", "defect_type": _dim2defect(f.get("dimension", "")),
                         "tier": tier, "rubric_ids": [], "test_names": [],
                         "explanation": (f"[{cat}] " if cat else "") + f.get("reason", ""),
                         "fix": f.get("fix", ""),
                         "evidence": f"dim={f.get('dimension','')}; {f.get('spec_ref','')}; verdict={r.get('verdict')}",
                         "flag_category": cat, "flag_dimension": f.get("dimension", "")})
        by[tid] = norm
    return by


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--cdq-out"); ap.add_argument("--cdq-tdir")
    ap.add_argument("--audit-out"); ap.add_argument("--audit-tdir")
    a = ap.parse_args()
    run_dir = Path(a.run_dir)
    merged = {}
    if (run_dir / "findings_llm.json").exists():
        merged = json.load(open(run_dir / "findings_llm.json"))
    cdq = harvest_cdq(a.cdq_out, a.cdq_tdir) if (a.cdq_out or a.cdq_tdir) else {}
    aud = harvest_audit(a.audit_out, a.audit_tdir) if (a.audit_out or a.audit_tdir) else {}
    for tid, fs in list(cdq.items()) + list(aud.items()):
        merged.setdefault(tid, [])
        # replace prior findings from the same check, then extend
        chk = fs[0]["check"] if fs else None
        if chk:
            merged[tid] = [f for f in merged[tid] if f.get("check") != chk] + fs
    json.dump(merged, open(run_dir / "findings_llm.json", "w"), indent=1)
    all_tasks = {Path(p).stem for p in glob.glob(str(run_dir / "ctx" / "*.json"))}
    print(f"resume: cdq tasks={len(cdq)} audit tasks={len(aud)} | merged findings_llm for {len(merged)} tasks")
    miss_cdq = sorted(all_tasks - set(cdq)) if cdq else []
    miss_aud = sorted(all_tasks - set(aud)) if aud else []
    if miss_cdq: print(f"  cdq MISSING ({len(miss_cdq)}): {miss_cdq[:10]}{'…' if len(miss_cdq)>10 else ''}")
    if miss_aud: print(f"  audit MISSING ({len(miss_aud)}): {miss_aud[:10]}{'…' if len(miss_aud)>10 else ''}")


if __name__ == "__main__":
    main()
