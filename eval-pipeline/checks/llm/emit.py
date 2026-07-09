"""checks/llm/emit.py — generate the LLM-check Workflow scripts for a run.

Emits self-contained workflow .js files (data baked in) into <run_dir>/workflows/:
  - cdq_static.js       : customer static eval-design QA, 1 reviewer / task (finds defects)
  - audit_hybrid31.js   : the DRAWER eval — Hybrid 3+1 QC audit that grades every V10-spec
                          dimension and emits the per-dimension "Task-level flags"
                          ([Fail - X]/[Non-Fail - Y]) exactly like the viewer's trajectory drawer.

Reviewers run on the config model+effort (Opus; effort from config, default high). Graders read the ACTUAL spec:
spec/V10_rubric.csv (21 dimensions + bands) + spec/authoring_spec.md (§ definitions, §9g).
"""
from __future__ import annotations
import csv, glob, json, os, re, subprocess
from pathlib import Path
from src import common

FIND_SCHEMA = ("{type:'object',additionalProperties:false,required:['task_id','findings','dims'],"
  "properties:{task_id:{type:'string'},findings:{type:'array',items:{type:'object',additionalProperties:false,"
  "required:['tier','defect_type','rubric_ids','test_names','explanation','fix'],properties:{"
  "tier:{enum:['action_required','review_recommended']},defect_type:{type:'string'},"
  "rubric_ids:{type:'array',items:{type:'integer'}},test_names:{type:'array',items:{type:'string'}},"
  "explanation:{type:'string'},fix:{type:'string'}}}},dims:{type:'object',additionalProperties:true}}}")


def _signals(findings):
    """Compact per-task summary of the deterministic linter signals already computed, handed to the
    LLM graders as PRE-VERIFIED starting points so they confirm rather than re-derive them."""
    parts = []
    for f in (findings or [])[:6]:
        ev = (f.get("evidence") or f.get("explanation") or "").strip().replace("\n", " ")
        parts.append(f"{f.get('check')}[{f.get('defect_type')}]: {ev[:140]}")
    return " || ".join(parts)


def _grading_card(csv_path):
    """Distill the V10 rubric CSV into a compact one-page grading card (21 dimensions, each with its
    score-2 [Fail-]/score-3 [Non-Fail-]/score-5 bands + labels). Graders read this instead of the
    full CSV + 1380-line appendix; the full docs stay available by path for edge cases."""
    rows = list(csv.reader(open(csv_path, newline="")))
    H = rows[0]
    ti, ec, ao, asc = (H.index("title"), H.index("errorCategories"),
                       H.index("answerOptionText"), H.index("answerOptionScore"))

    def _band(errcat):
        m = re.findall(r"\[(?:Fail|Non-Fail)[^\]]*\]", errcat or "")
        return m[0] if m else ""

    dims, cur = [], None
    for r in rows[1:]:
        if not any(c.strip() for c in r):
            continue
        if r[ti].strip():
            cur = {"title": r[ti].strip(), "opts": []}
            dims.append(cur)
        if cur is None:
            continue
        cur["opts"].append((r[asc].strip(), _band(r[ec]), (r[ao] or "").strip()))
    out = ["# V10 GRADING CARD — compact. 21 dimensions. Pick ONE score per dimension:",
           "#   2 = a [Fail-…] band · 3 = a [Non-Fail-…] band · 5 = clean.",
           "# Overall Rubric Quality: >10% criteria with a MAJOR issue = Fail; >15% moderate-or-major = Fail;",
           "# >20% minor-or-worse = Fail. Negative-weight ratio §9g ~25% (cap 30%); zero negatives = Fail-band.",
           "# Gated dims (silver trajectory / unit tests) absent = clean. Full CSV + appendix available by path.",
           ""]
    for d in dims:
        out.append(f"## {d['title']}")
        for sc, bd, txt in d["opts"]:
            tag = "FAIL" if sc == "2" else ("NON-FAIL" if sc == "3" else "clean")
            out.append(f"- [{sc}={tag}] {bd + ' ' if bd else ''}{txt[:120]}")
        out.append("")
    return "\n".join(out)


def _ensure_spec(cfg, run_dir: Path):
    spec = run_dir / "spec.md"
    if not (spec.exists() and spec.stat().st_size > 1000):
        script = common.expand(cfg["pipeline"]["spec"]["fetch_script"])
        proj = cfg["pipeline"]["project"]["id"]
        subprocess.run(["python3", script, "--project", proj, "--api-key", os.environ["REDASH_KEY"],
                        "--out", str(spec)], check=False)
    return str(spec)


def _tasks(run_dir: Path):
    # tasks whose LLM verdict is cached (attempt_id unchanged) are pre-seeded and listed in
    # skip_llm.json — skip emitting LLM work for them (see src/cache.py).
    skip = set()
    sp = run_dir / "skip_llm.json"
    if sp.exists():
        try:
            skip = set(json.load(open(sp)))
        except Exception:
            skip = set()
    out = []
    for p in sorted(glob.glob(str(run_dir / "ctx" / "*.json"))):
        c = json.load(open(p))
        if c["task_id"] in skip:
            continue
        out.append({"id": c["task_id"], "batch": c.get("batch_file"), "task_dir": c.get("task_dir"),
                    "ctx": p, "cat": c.get("category"), "sub": c.get("subcategory"),
                    "mm": c.get("mm_input"), "ttype": c.get("task_type")})
    return out


def emit_all(cfg, run_dir):
    run_dir = Path(run_dir)
    wf = run_dir / "workflows"; wf.mkdir(parents=True, exist_ok=True)
    guide = common.expand(cfg["pipeline"]["skill"]["eval_guide"])
    _ensure_spec(cfg, run_dir)
    csv_path = str(common.PKG / cfg["pipeline"]["spec"]["rubric_csv"])
    appendix = str(common.PKG / cfg["pipeline"]["spec"]["appendix_doc"])
    tasks = _tasks(run_dir)
    # ground the graders: hand each task its already-computed deterministic linter signals
    lint = json.load(open(run_dir / "findings_linters.json")) if (run_dir / "findings_linters.json").exists() else {}
    for t in tasks:
        t["sig"] = _signals(lint.get(t["id"], []))
    # distill the spec into a compact grading card the graders read instead of the full CSV+appendix
    card_path = str(run_dir / "grading_card.md")
    (run_dir / "grading_card.md").write_text(_grading_card(csv_path))
    model = cfg["pipeline"]["models"]["reviewer"]                 # from config (reviewer)
    effort = cfg["pipeline"]["models"].get("reviewer_effort", "high")  # from config (default high)
    paths = []
    (wf / "cdq_static.js").write_text(_cdq_static_js(tasks, guide, model, effort)); paths.append(str(wf / "cdq_static.js"))
    roles = cfg["pipeline"]["models"].get("audit_grader_roles", ["gen1", "gen2", "gen3", "rubric"])
    master_mode = cfg["pipeline"]["models"].get("audit_master", "if_flagged")
    verify = cfg["pipeline"].get("audit_verify", {}) or {}
    (wf / "audit_hybrid31.js").write_text(_audit_js(tasks, csv_path, appendix, card_path, model, effort, roles, master_mode, verify)); paths.append(str(wf / "audit_hybrid31.js"))
    return paths


def _opts(label, phase, model, effort, schema):
    return f"{{label:{json.dumps(label)},phase:{json.dumps(phase)},model:{json.dumps(model)},effort:{json.dumps(effort)},schema:{schema}}}"


# ── CDQ static (defect finder) ────────────────────────────────────────────────
def _cdq_static_js(tasks, guide, model, effort):
    data = json.dumps([{"id": t["id"], "batch": t["batch"], "task_dir": t["task_dir"], "sig": t.get("sig", "")} for t in tasks])
    opts = ("{label:'static:'+t.id.slice(-6),phase:'Static',model:" + json.dumps(model) +
            ",effort:" + json.dumps(effort) + ",schema:SCHEMA}")
    return (
"export const meta = { name:'cdq-static', description:'CDQ static eval-design QA', phases:[{title:'Static'}] }\n"
f"const GUIDE={json.dumps(guide)}\nconst TASKS={data}\n"
f"const SCHEMA={FIND_SCHEMA}\n"
"phase('Static')\n"
"const results=await parallel(TASKS.map(t=>()=>{\n"
"  const p=[\n"
"    'You audit EVAL-DESIGN QUALITY for benchmark task '+t.id+' from its STATIC files alone — no model rollouts. Flag defects a careful reader finds before any model runs.',\n"
"    'STEP 1: Read the eval guide in full: '+GUIDE,\n"
"    'STEP 2: Read the batch record: '+t.batch+' (prompt_text, rubrics[] {id,criterion,weight}, tests, task_dir, has_pytest_tests).',\n"
"    'STEP 3: Explore agent-visible tree: ls -R '+t.task_dir+'  — ONLY environment/ is visible at runtime; tests/ is a hidden grading harness.',\n"
"    'STEP 4: READ TO VERIFY — open mock-API data/schema files, CSVs backing rubric claims, task.toml, Dockerfile. VIEW every referenced image/PDF/xlsx/video/audio to check visual claims.',\n"
"    (t.sig?('DETERMINISTIC LINTER SIGNALS (already computed — confirm and fold in, do not re-derive): '+t.sig):'(no linter signals fired)'),\n"
"    'Emit findings (exact taxonomy tokens): RUBRIC_CONTRADICTION / RUBRIC_AMBIGUOUS / RUBRIC_OVERSPEC / RUBRIC_UNFAIR / RUBRIC_INACCURATE / DATA_SPARSE / MEDIA_PATH / MULTIMODAL_ARTIFACT / ORACLE_LEAK / GRADER_BROKEN / TOOL_FAILURE / SKILL_LOADOUT / CONTAINER_ENV / SP_UNCLEAR. eval-design defects ONLY, never model behavior. A grader/judge CRASH is infra not GRADER_BROKEN. Data-implied targets are VALID. Negative-weight rubrics are penalty guards. Intentionally-absent data testing hallucination-resistance is by design.',\n"
"    'TOKEN CHOICE (pick the MOST SPECIFIC; do not default everything to CONTRADICTION): RUBRIC_AMBIGUOUS = a criterion with multiple defensible readings graded as one (under-determined / subjective / vague) — use this liberally, it is common. RUBRIC_CONTRADICTION = the criterion conflicts with the prompt, the data, an image, or another criterion. RUBRIC_OVERSPEC = demands an exact value/timestamp where a range is defensible. RUBRIC_INACCURATE = the expected value is simply wrong vs the data. DATA_SPARSE = a graded fact is not derivable from any agent-visible source.',\n"
"    'OUTPUT DISCIPLINE: explanation 2-3 sentences, fix 1 sentence, <=8 findings. Each finding EXACTLY six keys: tier, defect_type, rubric_ids (ints), test_names, explanation, fix. Clean task -> findings:[].',\n"
"    'Also dims {prompt_clarity,criteria_completeness,input_adequacy,environment_adequacy,is_self_contained,missing_data,missing_tools}. Return exactly {task_id:\"'+t.id+'\", findings:[...], dims:{...}}.'\n"
"  ].join(String.fromCharCode(10,10))\n"
f"  return agent(p,{opts}).then(r=>r&&Object.assign({{}},r,{{task_id:t.id}}))\n"
"}))\nreturn results.filter(Boolean)\n")


# ── Hybrid 3+1 — the DRAWER eval (grade all 21 dims -> Task-level flags) ────────
def _audit_js(tasks, csv_path, appendix, card_path, model, effort, roles=("gen1", "gen2", "gen3", "rubric"), master_mode="if_flagged", verify=None):
    data = json.dumps([{"id": t["id"], "ctx": t["ctx"], "task_dir": t["task_dir"],
                        "cat": t["cat"], "sub": t["sub"], "mm": t["mm"], "ttype": t["ttype"], "sig": t.get("sig", "")} for t in tasks])
    # grader returns ONLY the flagged (Fail/Non-Fail) dimensions — small output, avoids the
    # StructuredOutput retry wall that a full 21-dimension array caused under Opus MAX.
    GFLAG = ("{type:'object',additionalProperties:false,required:['dimension','category','severity','reason'],"
      "properties:{dimension:{type:'string'},category:{type:'string'},severity:{enum:['Fail','Non-Fail']},"
      "reason:{type:'string'},spec_ref:{type:'string'}}}")
    AUD = ("{type:'object',additionalProperties:false,required:['task_id','flags','verdict','confidence'],"
      "properties:{task_id:{type:'string'},flags:{type:'array',items:" + GFLAG + "},"
      "verdict:{enum:['Fail','Non-Fail','Pass']},confidence:{type:'integer'}}}")
    FLAG = ("{type:'object',additionalProperties:false,required:['dimension','category','severity','reason'],"
      "properties:{dimension:{type:'string'},category:{type:'string'},severity:{enum:['Fail','Non-Fail']},"
      "reason:{type:'string'},fix:{type:'string'},spec_ref:{type:'string'}}}")
    MASTER = ("{type:'object',additionalProperties:false,required:['task_id','verdict','confidence','flags','why','agreement'],"
      "properties:{task_id:{type:'string'},verdict:{enum:['Fail','Non-Fail','Pass']},confidence:{type:'integer'},"
      "flags:{type:'array',items:" + FLAG + "},why:{type:'string'},agreement:{type:'string'}}}")
    verify = verify or {}
    v_en = bool(verify.get("enabled", False)); v_on = verify.get("on", "fail")
    v_conf = int(verify.get("confidence_below", 70))
    v_model = verify.get("model", model); v_effort = verify.get("effort", "high")
    VERIFY = ("{type:'object',additionalProperties:false,required:['task_id','upheld','final_verdict','why'],"
      "properties:{task_id:{type:'string'},upheld:{type:'boolean'},final_verdict:{enum:['Fail','Non-Fail','Pass']},"
      "overturned_dimensions:{type:'array',items:{type:'string'}},why:{type:'string'}}}")
    aopts = "{label:'aud:'+t.id.slice(-6)+':'+role,phase:'Audit',model:" + json.dumps(model) + ",effort:" + json.dumps(effort) + ",schema:AUD}"
    mopts = "{label:'flags:'+prev.t.id.slice(-6),phase:'Master',model:" + json.dumps(model) + ",effort:" + json.dumps(effort) + ",schema:MASTER}"
    vopts = "{label:'verify:'+m.task_id.slice(-6),phase:'Verify',model:" + json.dumps(v_model) + ",effort:" + json.dumps(v_effort) + ",schema:VERIFY}"
    return (
"export const meta = { name:'audit-drawer-flags', description:'DRAWER eval — Task-level flags graded vs V10 spec', phases:[{title:'Audit'},{title:'Master'},{title:'Verify'}] }\n"
f"const CSV={json.dumps(csv_path)}\nconst APPENDIX={json.dumps(appendix)}\nconst CARD={json.dumps(card_path)}\nconst TASKS={data}\n"
f"const AUD={AUD}\nconst MASTER={MASTER}\nconst VERIFY={VERIFY}\n"
f"const VERIFY_ENABLED={json.dumps(v_en)}, VERIFY_ON={json.dumps(v_on)}, VERIFY_CONF={v_conf};\n"
"function ap(t,role){const focus=role==='rubric'?'You are the RUBRIC-QUALITY SPECIALIST — grade the three Overall Rubric Quality dimensions (Major / Major-Moderate / Major-Moderate-Minor), Rubric Structure (weights in {-5,-3,-1,1,3,5}), Rubric Spot Checks, and negative-weight ratio (§9g ~25%, cap 30%) with extra rigor.':'You are THE grader (single-grader + master design) — grade EVERY applicable dimension, AND apply extra rigor to the three Overall Rubric Quality dimensions (Major / Major-Moderate / Major-Moderate-Minor), Rubric Structure (weights in {-5,-3,-1,1,3,5}), Rubric Spot Checks, and the negative-weight ratio (§9g ~25%, cap 30%).';\n"
"  return [\n"
"    'You produce the TASK-LEVEL FLAGS eval (the viewer trajectory drawer) for OpenClaw task '+t.id+' ('+t.cat+' / '+t.sub+', modality '+t.mm+'). You grade the AUTHORED EVAL (prompt/inputs/rubric/tests/trajectory) — NOT the model.',\n"
"    focus,\n"
"    (t.sig?('DETERMINISTIC LINTER SIGNALS for this task (already computed — treat as verified starting points; confirm and fold into the matching dimensions, do NOT re-derive; absence of a signal is NOT proof of clean): '+t.sig):'No deterministic linter signals fired for this task.'),\n"
"    'STEP 1: Read THE GRADING CARD (your primary, authoritative grading form): '+CARD+' — the 21 dimensions, each with its score-2 [Fail-]/score-3 [Non-Fail-]/score-5 clean bands + exact band labels, plus the Overall Rubric Quality % thresholds and §9g.',\n"
"    'STEP 2 (only if a card entry is ambiguous for THIS case): the full CSV '+CSV+' and appendix '+APPENDIX+' have the verbose per-band definitions — consult them narrowly, do not read them wholesale.',\n"
"    'STEP 3: Read the task ctx JSON: '+t.ctx+' (full rubric with type/modality/weight, visual_rubrics, test_code, instruction, reward). Explore + VIEW media: ls -R '+t.task_dir+' then open referenced images/pdf/video/audio and verify each graded fact.',\n"
"    'STEP 4: Work through ALL 21 dimensions internally, picking each one score 2 (=[Fail-X]), 3 (=[Non-Fail-Y]) or 5 (clean) from the CSV; for gated dims (silver trajectory / unit tests) treat absent as clean. For the three Overall Rubric Quality dims COUNT criteria with major/moderate/minor issues (denominator = # criteria the CB wrote; no double-count) and apply the % thresholds (>10% major, >15% moderate+, >20% minor+).',\n"
"    'OUTPUT ONLY THE FLAGGED DIMENSIONS (score 2 or 3) — NOT the clean ones. Keep it small: reason <=2 sentences. Each flag {dimension (CSV title), category (exact [Fail-]/[Non-Fail-] label from errorCategories), severity (Fail if score 2 / Non-Fail if 3), reason, spec_ref (dimension name or § section)}. If every dimension is clean, flags:[]. Overall verdict: Fail if any Fail flag, Non-Fail if any Non-Fail flag, else Pass. Return exactly {task_id:\"'+t.id+'\", flags:[...], verdict, confidence}.'\n"
"  ].join(String.fromCharCode(10,10));}\n"
"function mp(t,auds){return ['You are the MASTER for the Task-level flags eval of OpenClaw task '+t.id+'. You are the independent VERIFICATION pass over these '+auds.length+' grader report(s) — produce the FINAL drawer flags.','GRADER REPORTS (JSON): '+JSON.stringify(auds),'Rules: UNION the grader flags by dimension; independently CONFIRM each flag by re-checking its cited evidence; when multiple graders ran, prefer flags >=2 of them agreed on; DROP any miscount/misread (especially visual) you cannot reconfirm. When graders disagree on a dimension, keep the most-defensible severity/category. Overall verdict: Fail if any surviving Fail flag, Non-Fail if any Non-Fail flag, else Pass. Re-open the grading card '+CARD+' (full CSV '+CSV+' / appendix '+APPENDIX+' only if needed), ctx '+t.ctx+' or media '+t.task_dir+' to adjudicate.','Return {task_id:\"'+t.id+'\", verdict, confidence (0-100 the task is deliverable/clean), flags:[{dimension, category (exact [Fail-]/[Non-Fail-] band label), severity, reason, fix, spec_ref}], why (2-4 sentences), agreement (e.g. \"grader flagged §9g, confirmed\" or \"2/2 graders agreed\")}.'].join(String.fromCharCode(10,10));}\n"
"function vp(m){return ['You are an ADVERSARIAL reviewer for the Task-level flags eval of OpenClaw task '+m.task_id+'. The audit marked it '+m.verdict+' (confidence '+m.confidence+'). Try to REFUTE it — show the task is actually deliverable.','Flags to challenge (JSON): '+JSON.stringify(m.flags||[]),'For EACH flag decide: a genuine spec violation, or a defensible authoring choice / a misread (especially of an image or a number)? Re-open the grading card '+CARD+' (or full CSV '+CSV+'/appendix '+APPENDIX+'), ctx '+m._ctx+', media '+m._tdir+' to confirm. Overturn ONLY flags you can positively refute with evidence; keep the rest.','Return {task_id:\"'+m.task_id+'\", upheld (true if >=1 Fail-severity flag genuinely stands), final_verdict (Fail if a Fail flag stands, else Non-Fail if a Non-Fail flag stands, else Pass), overturned_dimensions (the dimensions you refuted), why (2-3 sentences)}.'].join(String.fromCharCode(10,10));}\n"
"function applyVerify(m,v){if(!v) return m; const ov=new Set(v.overturned_dimensions||[]); const kept=(m.flags||[]).filter(f=>!ov.has(f.dimension)); if(v.upheld && !ov.size) return Object.assign({},m,{why:(m.why||'')+' [adversarial check upheld the verdict]'}); return Object.assign({},m,{verdict:(v.final_verdict||m.verdict),flags:kept,why:(m.why||'')+' [adversarial review: '+(v.why||'')+']',agreement:(m.agreement||'')+' | adversarial:'+(v.upheld?'upheld':'downgraded->'+(v.final_verdict||''))});}\n"
"phase('Audit')\nconst ROLES=" + json.dumps(list(roles)) + "\nconst MASTER_MODE=" + json.dumps(master_mode) + "\n"
"const out=await pipeline(TASKS,\n"
f"  t=>parallel(ROLES.map(role=>()=>agent(ap(t,role==='rubric'?'rubric':'gen'),{aopts}))).then(rs=>({{t,auditors:rs.filter(Boolean)}})),\n"
"  (prev)=>{\n"
"    if(!prev.auditors.length) return null;\n"
"    const a=prev.auditors[0];\n"
"    const flagged=(a.verdict&&a.verdict!=='Pass')||(a.flags&&a.flags.length>0);\n"
"    if(MASTER_MODE==='never'||(MASTER_MODE==='if_flagged'&&!flagged))\n"
"      return {task_id:prev.t.id, verdict:(a.verdict||'Pass'), confidence:(a.confidence||90), flags:(a.flags||[]).map(f=>Object.assign({},f,{fix:(f.fix||'')})), why:(flagged?('Single-grader flags kept; master verification skipped by config (audit_master='+MASTER_MODE+').'):'Clean per the single grader; master verification skipped.'), agreement:('1 grader ('+(flagged?'flagged':'clean')+'), no master pass'), _ctx:prev.t.ctx, _tdir:prev.t.task_dir};\n"
f"    return agent(mp(prev.t,prev.auditors),{mopts}).then(m=>m&&Object.assign({{}},m,{{task_id:prev.t.id,_ctx:prev.t.ctx,_tdir:prev.t.task_dir}}));\n"
"  },\n"
"  (m)=>{\n"
"    if(!m) return null;\n"
"    const strip=x=>{const r=Object.assign({},x); delete r._ctx; delete r._tdir; return r;};\n"
"    const needy=VERIFY_ENABLED&&(((VERIFY_ON==='fail'||VERIFY_ON==='both')&&m.verdict==='Fail')||((VERIFY_ON==='low_confidence'||VERIFY_ON==='both')&&(m.confidence!=null&&m.confidence<VERIFY_CONF)));\n"
"    if(!needy) return strip(m);\n"
f"    return agent(vp(m),{vopts}).then(v=>strip(applyVerify(m,v)));\n"
"  }\n"
")\nreturn out.filter(Boolean)\n")
