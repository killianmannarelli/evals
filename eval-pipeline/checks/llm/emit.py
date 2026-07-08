"""checks/llm/emit.py — generate the LLM-check Workflow scripts for a run.

Emits self-contained workflow .js files (data baked in — the proven pattern; `args` doesn't
thread through scriptPath) into <run_dir>/workflows/:
  - cdq_static.js       : customer static eval-design QA, 1 Sonnet reviewer / task
  - audit_hybrid31.js   : our Hybrid 3+1 rubric-quality audit vs V10 spec, pipeline per task
  - verify.js           : written on demand by emit_verify() after static findings are harvested

Claude launches these via the Workflow tool; src/resume.py harvests their transcripts.
Reads <run_dir>/ctx/<id>.json (rubric/tests/instruction/reward/task_dir) + batch/<id>.json.
Ensures <run_dir>/spec.md exists (fetches via qc-auditor fetch_spec.py).
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
    if spec.exists() and spec.stat().st_size > 1000:
        return str(spec)
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
    spec = _ensure_spec(cfg, run_dir)
    tasks = _tasks(run_dir)
    model = cfg["pipeline"]["models"]["reviewer"]
    paths = []
    (wf / "cdq_static.js").write_text(_cdq_static_js(tasks, guide, model)); paths.append(str(wf / "cdq_static.js"))
    (wf / "audit_hybrid31.js").write_text(_audit_js(tasks, spec, model)); paths.append(str(wf / "audit_hybrid31.js"))
    return paths


# ── CDQ static ────────────────────────────────────────────────────────────────
def _cdq_static_js(tasks, guide, model):
    data = json.dumps([{"id": t["id"], "batch": t["batch"], "task_dir": t["task_dir"]} for t in tasks])
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
f"  return agent(p,{{label:'static:'+t.id.slice(-6),phase:'Static',model:{json.dumps(model)},schema:SCHEMA}}).then(r=>r&&Object.assign({{}},r,{{task_id:t.id}}))\n"
"}))\nreturn results.filter(Boolean)\n")


# ── Hybrid 3+1 audit ────────────────────────────────────────────────────────
def _audit_js(tasks, spec, model):
    data = json.dumps([{"id": t["id"], "ctx": t["ctx"], "task_dir": t["task_dir"],
                        "cat": t["cat"], "sub": t["sub"], "mm": t["mm"], "ttype": t["ttype"]} for t in tasks])
    AUD = ("{type:'object',additionalProperties:false,required:['task_id','findings','verdict','confidence','rationale'],"
      "properties:{task_id:{type:'string'},findings:{type:'array',items:{type:'object',additionalProperties:false,"
      "required:['dimension','severity','rubric_ids','issue','evidence','fix'],properties:{dimension:{type:'string'},"
      "severity:{enum:['Major','Moderate','Minor']},rubric_ids:{type:'array',items:{type:'integer'}},issue:{type:'string'},"
      "evidence:{type:'string'},fix:{type:'string'}}}},verdict:{enum:['Fail','Non-Fail','Pass']},confidence:{type:'integer'},rationale:{type:'string'}}}")
    MASTER = ("{type:'object',additionalProperties:false,required:['task_id','verdict','confidence','why','what_to_fix',"
      "'flagged_dimensions','major_count','moderate_count','minor_count','agreement','findings'],properties:{task_id:{type:'string'},"
      "verdict:{enum:['Fail','Non-Fail','Pass']},confidence:{type:'integer'},why:{type:'string'},what_to_fix:{type:'string'},"
      "flagged_dimensions:{type:'array',items:{type:'string'}},major_count:{type:'integer'},moderate_count:{type:'integer'},"
      "minor_count:{type:'integer'},agreement:{type:'string'},findings:{type:'array',items:{type:'object',additionalProperties:false,"
      "required:['dimension','severity','rubric_ids','issue','fix'],properties:{dimension:{type:'string'},severity:{enum:['Major','Moderate','Minor']},"
      "rubric_ids:{type:'array',items:{type:'integer'}},issue:{type:'string'},fix:{type:'string'}}}}}}")
    return (
"export const meta = { name:'audit-hybrid31', description:'OpenClaw Hybrid 3+1 rubric audit vs V10 spec', phases:[{title:'Audit'},{title:'Master'}] }\n"
f"const SPEC={json.dumps(spec)}\nconst TASKS={data}\n"
f"const AUD={AUD}\nconst MASTER={MASTER}\n"
"function ap(t,role){const focus=role==='rubric'?'You are the RUBRIC-QUALITY SPECIALIST — focus on atomicity, necessity, value-embedding, target correctness, weight sign, per-criterion MM-dependence, negative-weight ratio, coverage.':'You are a GENERALIST auditor — grade EVERY in-scope spec dimension.';\n"
"  return [\n"
"    'You QC-audit OpenClaw task '+t.id+' ('+t.cat+' / '+t.sub+', modality '+t.mm+'). Grade the QUALITY OF THE AUTHORED EVAL vs the customer V10 spec — NOT the model.',\n"
"    focus,\n"
"    'STEP 1: Read the spec IN FULL: '+SPEC+' (each dimension + [Fail-]/[Non-Fail-] error categories + 1-5 scale).',\n"
"    'STEP 2: Read the task ctx JSON: '+t.ctx+' (full rubric with type/modality/weight/pass_rate, visual_rubrics, test_code, instruction, reward).',\n"
"    'STEP 3: Explore + VIEW media: ls -R '+t.task_dir+' then open images/pdf/video/audio referenced by criteria; verify each criterion is grounded in what the artifacts actually show. Do NOT guess visual content.',\n"
"    'SCOPE: Prompt (MM-dependence, output filename, feasibility), Input Artifacts (realism, verification, answer-leak), Verifiers-Safety, Trajectory dims. SKIP Tests dims (out of scope 2026-05-23). SKIP Silver-Trajectory if none.',\n"
"    'Findings {dimension, severity(Major=[Fail-]/Moderate=[Non-Fail-]/Minor), rubric_ids ints, issue 2-3 sentences, evidence cite file/criterion/image, fix}. Verdict: Fail if any Major; Non-Fail if only Moderate; Pass if clean. confidence 0-100. <=10 findings. Return exactly {task_id:\"'+t.id+'\", findings:[...], verdict, confidence, rationale}.'\n"
"  ].join(String.fromCharCode(10,10));}\n"
"function mp(t,auds){return ['You are the MASTER for OpenClaw task '+t.id+'. Merge these '+auds.length+' auditor reports into ONE verdict.','AUDITOR REPORTS: '+JSON.stringify(auds),'Rules: keep a finding only if corroborated (drop miscounts/misreads, especially visual); merge duplicates noting auditor agreement; Fail if any surviving Major, Non-Fail if only Moderate, else Pass; confidence 0-100 = deliverable/clean. Re-open SPEC '+SPEC+', ctx '+t.ctx+', or media '+t.task_dir+' if needed.','Return {task_id:\"'+t.id+'\", verdict, confidence, why (2-4 sentences), what_to_fix, flagged_dimensions[], major_count, moderate_count, minor_count, agreement, findings(merged {dimension,severity,rubric_ids,issue,fix})}.'].join(String.fromCharCode(10,10));}\n"
"phase('Audit')\nconst ROLES=['gen1','gen2','gen3','rubric']\n"
"const out=await pipeline(TASKS,\n"
f"  t=>parallel(ROLES.map(role=>()=>agent(ap(t,role==='rubric'?'rubric':'gen'),{{label:'aud:'+t.id.slice(-6)+':'+role,phase:'Audit',model:{json.dumps(model)},schema:AUD}}))).then(rs=>({{t,auditors:rs.filter(Boolean)}})),\n"
f"  (prev)=>prev.auditors.length?agent(mp(prev.t,prev.auditors),{{label:'master:'+prev.t.id.slice(-6),phase:'Master',model:{json.dumps(model)},schema:MASTER}}).then(m=>m&&Object.assign({{}},m,{{task_id:prev.t.id}})):null\n"
")\nreturn out.filter(Boolean)\n")
