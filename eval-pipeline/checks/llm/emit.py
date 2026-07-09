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
import glob, json, os, subprocess
from pathlib import Path
from src import common

FIND_SCHEMA = ("{type:'object',additionalProperties:false,required:['task_id','findings','dims'],"
  "properties:{task_id:{type:'string'},findings:{type:'array',items:{type:'object',additionalProperties:false,"
  "required:['tier','defect_type','rubric_ids','test_names','explanation','fix'],properties:{"
  "tier:{enum:['action_required','review_recommended']},defect_type:{type:'string'},"
  "rubric_ids:{type:'array',items:{type:'integer'}},test_names:{type:'array',items:{type:'string'}},"
  "explanation:{type:'string'},fix:{type:'string'}}}},dims:{type:'object',additionalProperties:true}}}")


def _ensure_spec(cfg, run_dir: Path):
    spec = run_dir / "spec.md"
    if not (spec.exists() and spec.stat().st_size > 1000):
        script = common.expand(cfg["pipeline"]["spec"]["fetch_script"])
        proj = cfg["pipeline"]["project"]["id"]
        subprocess.run(["python3", script, "--project", proj, "--api-key", os.environ["REDASH_KEY"],
                        "--out", str(spec)], check=False)
    return str(spec)


def _tasks(run_dir: Path):
    out = []
    for p in sorted(glob.glob(str(run_dir / "ctx" / "*.json"))):
        c = json.load(open(p))
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
    model = cfg["pipeline"]["models"]["reviewer"]                 # "opus"
    effort = cfg["pipeline"]["models"].get("reviewer_effort", "high")  # from config (default high)
    paths = []
    (wf / "cdq_static.js").write_text(_cdq_static_js(tasks, guide, model, effort)); paths.append(str(wf / "cdq_static.js"))
    roles = cfg["pipeline"]["models"].get("audit_grader_roles", ["gen1", "gen2", "gen3", "rubric"])
    master_mode = cfg["pipeline"]["models"].get("audit_master", "if_flagged")
    (wf / "audit_hybrid31.js").write_text(_audit_js(tasks, csv_path, appendix, model, effort, roles, master_mode)); paths.append(str(wf / "audit_hybrid31.js"))
    return paths


def _opts(label, phase, model, effort, schema):
    return f"{{label:{json.dumps(label)},phase:{json.dumps(phase)},model:{json.dumps(model)},effort:{json.dumps(effort)},schema:{schema}}}"


# ── CDQ static (defect finder) ────────────────────────────────────────────────
def _cdq_static_js(tasks, guide, model, effort):
    data = json.dumps([{"id": t["id"], "batch": t["batch"], "task_dir": t["task_dir"]} for t in tasks])
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
"    'Emit findings (exact taxonomy tokens): RUBRIC_CONTRADICTION / RUBRIC_AMBIGUOUS / RUBRIC_OVERSPEC / RUBRIC_UNFAIR / RUBRIC_INACCURATE / DATA_SPARSE / MEDIA_PATH / MULTIMODAL_ARTIFACT / ORACLE_LEAK / GRADER_BROKEN / TOOL_FAILURE / SKILL_LOADOUT / CONTAINER_ENV / SP_UNCLEAR. eval-design defects ONLY, never model behavior. A grader/judge CRASH is infra not GRADER_BROKEN. Data-implied targets are VALID. Negative-weight rubrics are penalty guards. Intentionally-absent data testing hallucination-resistance is by design.',\n"
"    'OUTPUT DISCIPLINE: explanation 2-3 sentences, fix 1 sentence, <=8 findings. Each finding EXACTLY six keys: tier, defect_type, rubric_ids (ints), test_names, explanation, fix. Clean task -> findings:[].',\n"
"    'Also dims {prompt_clarity,criteria_completeness,input_adequacy,environment_adequacy,is_self_contained,missing_data,missing_tools}. Return exactly {task_id:\"'+t.id+'\", findings:[...], dims:{...}}.'\n"
"  ].join(String.fromCharCode(10,10))\n"
f"  return agent(p,{opts}).then(r=>r&&Object.assign({{}},r,{{task_id:t.id}}))\n"
"}))\nreturn results.filter(Boolean)\n")


# ── Hybrid 3+1 — the DRAWER eval (grade all 21 dims -> Task-level flags) ────────
def _audit_js(tasks, csv_path, appendix, model, effort, roles=("gen1", "gen2", "gen3", "rubric"), master_mode="if_flagged"):
    data = json.dumps([{"id": t["id"], "ctx": t["ctx"], "task_dir": t["task_dir"],
                        "cat": t["cat"], "sub": t["sub"], "mm": t["mm"], "ttype": t["ttype"]} for t in tasks])
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
    aopts = "{label:'aud:'+t.id.slice(-6)+':'+role,phase:'Audit',model:" + json.dumps(model) + ",effort:" + json.dumps(effort) + ",schema:AUD}"
    mopts = "{label:'flags:'+prev.t.id.slice(-6),phase:'Master',model:" + json.dumps(model) + ",effort:" + json.dumps(effort) + ",schema:MASTER}"
    return (
"export const meta = { name:'audit-drawer-flags', description:'DRAWER eval — Task-level flags graded vs V10 spec', phases:[{title:'Audit'},{title:'Master'}] }\n"
f"const CSV={json.dumps(csv_path)}\nconst APPENDIX={json.dumps(appendix)}\nconst TASKS={data}\n"
f"const AUD={AUD}\nconst MASTER={MASTER}\n"
"function ap(t,role){const focus=role==='rubric'?'You are the RUBRIC-QUALITY SPECIALIST — grade the three Overall Rubric Quality dimensions (Major / Major-Moderate / Major-Moderate-Minor), Rubric Structure (weights in {-5,-3,-1,1,3,5}), Rubric Spot Checks, and negative-weight ratio (§9g ~25%, cap 30%) with extra rigor.':'You are THE grader (single-grader + master design) — grade EVERY applicable dimension, AND apply extra rigor to the three Overall Rubric Quality dimensions (Major / Major-Moderate / Major-Moderate-Minor), Rubric Structure (weights in {-5,-3,-1,1,3,5}), Rubric Spot Checks, and the negative-weight ratio (§9g ~25%, cap 30%).';\n"
"  return [\n"
"    'You produce the TASK-LEVEL FLAGS eval (the viewer trajectory drawer) for OpenClaw task '+t.id+' ('+t.cat+' / '+t.sub+', modality '+t.mm+'). You grade the AUTHORED EVAL (prompt/inputs/rubric/tests/trajectory) — NOT the model.',\n"
"    focus,\n"
"    'STEP 1: Read THE SPEC (authoritative grading form): '+CSV+' — a CSV of 21 dimensions; each row-group has questionText/questionDescription and answer options with answerOptionScore 2 (a [Fail - X] category), 3 (a [Non-Fail - Y] category), or 5 (clean). The errorCategories column names the exact band label.',\n"
"    'STEP 2: Read the appendix definitions: '+APPENDIX+' — major/moderate/minor rubric-error definitions (for the three Overall Rubric Quality dimensions: >10% major=Fail; >15% moderate-or-major=Fail; >20% minor+=Fail) and §9g negative-weight ~25% (cap 30%).',\n"
"    'STEP 3: Read the task ctx JSON: '+t.ctx+' (full rubric with type/modality/weight, visual_rubrics, test_code, instruction, reward). Explore + VIEW media: ls -R '+t.task_dir+' then open referenced images/pdf/video/audio and verify each graded fact.',\n"
"    'STEP 4: Work through ALL 21 dimensions internally, picking each one score 2 (=[Fail-X]), 3 (=[Non-Fail-Y]) or 5 (clean) from the CSV; for gated dims (silver trajectory / unit tests) treat absent as clean. For the three Overall Rubric Quality dims COUNT criteria with major/moderate/minor issues (denominator = # criteria the CB wrote; no double-count) and apply the % thresholds (>10% major, >15% moderate+, >20% minor+).',\n"
"    'OUTPUT ONLY THE FLAGGED DIMENSIONS (score 2 or 3) — NOT the clean ones. Keep it small: reason <=2 sentences. Each flag {dimension (CSV title), category (exact [Fail-]/[Non-Fail-] label from errorCategories), severity (Fail if score 2 / Non-Fail if 3), reason, spec_ref (dimension name or § section)}. If every dimension is clean, flags:[]. Overall verdict: Fail if any Fail flag, Non-Fail if any Non-Fail flag, else Pass. Return exactly {task_id:\"'+t.id+'\", flags:[...], verdict, confidence}.'\n"
"  ].join(String.fromCharCode(10,10));}\n"
"function mp(t,auds){return ['You are the MASTER for the Task-level flags eval of OpenClaw task '+t.id+'. You are the independent VERIFICATION pass over these '+auds.length+' grader report(s) — produce the FINAL drawer flags.','GRADER REPORTS (JSON): '+JSON.stringify(auds),'Rules: UNION the grader flags by dimension; independently CONFIRM each flag by re-checking its cited evidence; when multiple graders ran, prefer flags >=2 of them agreed on; DROP any miscount/misread (especially visual) you cannot reconfirm. When graders disagree on a dimension, keep the most-defensible severity/category. Overall verdict: Fail if any surviving Fail flag, Non-Fail if any Non-Fail flag, else Pass. Re-open CSV '+CSV+', appendix '+APPENDIX+', ctx '+t.ctx+' or media '+t.task_dir+' to adjudicate.','Return {task_id:\"'+t.id+'\", verdict, confidence (0-100 the task is deliverable/clean), flags:[{dimension, category (exact [Fail-]/[Non-Fail-] band label), severity, reason, fix, spec_ref}], why (2-4 sentences), agreement (e.g. \"grader flagged §9g, confirmed\" or \"2/2 graders agreed\")}.'].join(String.fromCharCode(10,10));}\n"
"phase('Audit')\nconst ROLES=" + json.dumps(list(roles)) + "\nconst MASTER_MODE=" + json.dumps(master_mode) + "\n"
"const out=await pipeline(TASKS,\n"
f"  t=>parallel(ROLES.map(role=>()=>agent(ap(t,role==='rubric'?'rubric':'gen'),{aopts}))).then(rs=>({{t,auditors:rs.filter(Boolean)}})),\n"
"  (prev)=>{\n"
"    if(!prev.auditors.length) return null;\n"
"    const a=prev.auditors[0];\n"
"    const flagged=(a.verdict&&a.verdict!=='Pass')||(a.flags&&a.flags.length>0);\n"
"    if(MASTER_MODE==='never'||(MASTER_MODE==='if_flagged'&&!flagged))\n"
"      return {task_id:prev.t.id, verdict:(a.verdict||'Pass'), confidence:(a.confidence||90), flags:(a.flags||[]).map(f=>Object.assign({},f,{fix:(f.fix||'')})), why:(flagged?('Single-grader flags kept; master verification skipped by config (audit_master='+MASTER_MODE+').'):'Clean per the single grader; master verification skipped.'), agreement:('1 grader ('+(flagged?'flagged':'clean')+'), no master pass')};\n"
f"    return agent(mp(prev.t,prev.auditors),{mopts}).then(m=>m&&Object.assign({{}},m,{{task_id:prev.t.id}}));\n"
"  }\n"
")\nreturn out.filter(Boolean)\n")
