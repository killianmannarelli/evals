"""checks/llm/emit.py — generate the LLM-check Workflow scripts for a run.

Emits self-contained workflow .js files (data baked in) into <run_dir>/workflows/:
  - cdq_static.js       : customer static eval-design QA, 1 reviewer / task (finds defects)
  - audit_hybrid31.js   : the DRAWER eval — Hybrid 3+1 QC audit that grades every V10-spec
                          dimension and emits the per-dimension "Task-level flags"
                          ([Fail - X]/[Non-Fail - Y]) exactly like the viewer's trajectory drawer.

Reviewers run on the config model+effort (Opus MAX). Graders read the ACTUAL spec:
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
    effort = cfg["pipeline"]["models"].get("reviewer_effort", "high")  # "max"
    paths = []
    (wf / "cdq_static.js").write_text(_cdq_static_js(tasks, guide, model, effort)); paths.append(str(wf / "cdq_static.js"))
    (wf / "audit_hybrid31.js").write_text(_audit_js(tasks, csv_path, appendix, model, effort)); paths.append(str(wf / "audit_hybrid31.js"))
    return paths


def _opts(label, phase, model, effort, schema):
    return f"{{label:{json.dumps(label)},phase:{json.dumps(phase)},model:{json.dumps(model)},effort:{json.dumps(effort)},schema:{schema}}}"


# ── CDQ static (defect finder) ────────────────────────────────────────────────
def _cdq_static_js(tasks, guide, model, effort):
    data = json.dumps([{"id": t["id"], "batch": t["batch"], "task_dir": t["task_dir"]} for t in tasks])
    opts = ("{label:'static:'+t.id.slice(-6),phase:'Static',model:" + json.dumps(model) +
            ",effort:" + json.dumps(effort) + ",schema:SCHEMA}")
    return (
"export const meta = { name:'cdq-static', description:'CDQ static eval-design QA (Opus MAX)', phases:[{title:'Static'}] }\n"
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
def _audit_js(tasks, csv_path, appendix, model, effort):
    data = json.dumps([{"id": t["id"], "ctx": t["ctx"], "task_dir": t["task_dir"],
                        "cat": t["cat"], "sub": t["sub"], "mm": t["mm"], "ttype": t["ttype"]} for t in tasks])
    DIMGRADE = ("{type:'object',additionalProperties:false,required:['dimension','score','category','severity','reason'],"
      "properties:{dimension:{type:'string'},score:{enum:[2,3,5]},category:{type:'string'},"
      "severity:{enum:['Fail','Non-Fail','Pass','Skip']},reason:{type:'string'},spec_ref:{type:'string'}}}")
    AUD = ("{type:'object',additionalProperties:false,required:['task_id','grades','verdict','confidence'],"
      "properties:{task_id:{type:'string'},grades:{type:'array',items:" + DIMGRADE + "},"
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
"export const meta = { name:'audit-drawer-flags', description:'DRAWER eval — Task-level flags graded vs V10 spec (Opus MAX)', phases:[{title:'Audit'},{title:'Master'}] }\n"
f"const CSV={json.dumps(csv_path)}\nconst APPENDIX={json.dumps(appendix)}\nconst TASKS={data}\n"
f"const AUD={AUD}\nconst MASTER={MASTER}\n"
"function ap(t,role){const focus=role==='rubric'?'You are the RUBRIC-QUALITY SPECIALIST — grade the three Overall Rubric Quality dimensions (Major / Major-Moderate / Major-Moderate-Minor), Rubric Structure (weights in {-5,-3,-1,1,3,5}), Rubric Spot Checks, and negative-weight ratio (§9g ~25%, cap 30%) with extra rigor.':'You are a GENERALIST grader — grade EVERY applicable dimension.';\n"
"  return [\n"
"    'You produce the TASK-LEVEL FLAGS eval (the viewer trajectory drawer) for OpenClaw task '+t.id+' ('+t.cat+' / '+t.sub+', modality '+t.mm+'). You grade the AUTHORED EVAL (prompt/inputs/rubric/tests/trajectory) — NOT the model.',\n"
"    focus,\n"
"    'STEP 1: Read THE SPEC (authoritative grading form): '+CSV+' — a CSV of 21 dimensions; each row-group has questionText/questionDescription and answer options with answerOptionScore 2 (a [Fail - X] category), 3 (a [Non-Fail - Y] category), or 5 (clean). The errorCategories column names the exact band label.',\n"
"    'STEP 2: Read the appendix definitions: '+APPENDIX+' — major/moderate/minor rubric-error definitions (for the three Overall Rubric Quality dimensions: >10% major=Fail; >15% moderate-or-major=Fail; >20% minor+=Fail) and §9g negative-weight ~25% (cap 30%).',\n"
"    'STEP 3: Read the task ctx JSON: '+t.ctx+' (full rubric with type/modality/weight, visual_rubrics, test_code, instruction, reward). Explore + VIEW media: ls -R '+t.task_dir+' then open referenced images/pdf/video/audio and verify each graded fact.',\n"
"    'STEP 4: For EACH of the 21 dimensions pick the score option (2/3/5) from the CSV. Score 5 = no issue. For dimensions gated \"only evaluate if silver trajectory / unit tests present\", set score 5 and severity Skip when N/A. For the three Overall Rubric Quality dims, COUNT criteria with major/moderate/minor issues (denominator = # criteria the CB wrote; do not double-count) and apply the % thresholds.',\n"
"    'Return grades[] for ALL dimensions {dimension (CSV title), score (2/3/5), category (the exact [Fail-]/[Non-Fail-] label from errorCategories, or \"clean\"), severity (Fail if score 2 / Non-Fail if 3 / Pass if 5 / Skip), reason (cite the criteria %/the exact defect/the media), spec_ref (dimension or § section)}. Overall verdict: Fail if any score-2, Non-Fail if any score-3, else Pass. Return {task_id:\"'+t.id+'\", grades:[...], verdict, confidence}.'\n"
"  ].join(String.fromCharCode(10,10));}\n"
"function mp(t,auds){return ['You are the MASTER for the Task-level flags eval of OpenClaw task '+t.id+'. Merge these '+auds.length+' independent graders (3 generalists + 1 rubric specialist) into the FINAL drawer flags.','GRADER REPORTS (JSON): '+JSON.stringify(auds),'Rules: for each dimension take the consensus/most-defensible score; keep a Fail/Non-Fail only if corroborated (drop miscounts/misreads, especially visual). A FLAG is any dimension whose final severity is Fail or Non-Fail. Overall verdict: Fail if any Fail flag, Non-Fail if any Non-Fail flag, else Pass. Re-open CSV '+CSV+', appendix '+APPENDIX+', ctx '+t.ctx+' or media '+t.task_dir+' to adjudicate.','Return {task_id:\"'+t.id+'\", verdict, confidence (0-100 the task is deliverable/clean), flags:[{dimension, category (exact [Fail-]/[Non-Fail-] band label), severity, reason, fix, spec_ref}], why (2-4 sentences), agreement (e.g. \"3/4 graders flagged §9g\")}.'].join(String.fromCharCode(10,10));}\n"
"phase('Audit')\nconst ROLES=['gen1','gen2','gen3','rubric']\n"
"const out=await pipeline(TASKS,\n"
f"  t=>parallel(ROLES.map(role=>()=>agent(ap(t,role==='rubric'?'rubric':'gen'),{aopts}))).then(rs=>({{t,auditors:rs.filter(Boolean)}})),\n"
f"  (prev)=>prev.auditors.length?agent(mp(prev.t,prev.auditors),{mopts}).then(m=>m&&Object.assign({{}},m,{{task_id:prev.t.id}})):null\n"
")\nreturn out.filter(Boolean)\n")
