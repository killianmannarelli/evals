# Multi-Agent Swarm — Task Creation Pipeline (Cloud-prompts variant)

Companion to `PIPELINE_SUMMARY.md`. Captures the end-to-end pipeline for
turning a cloud trajectory manifest of `multi-agent-swarm-supplied-prompts`
runs into a platform-uploadable bundle (task.yaml + gold.yaml +
single_run.json + multi_run.json + upload CSV).

**Key difference vs the SWE pipeline:** these tasks are not SWE-shaped —
they're creative/research multi-agent swarm prompts (e.g. "Coordinate 60
sub-agents to image a lamp in 60 households", "80-country negotiation
handbook"). No `repo`, no PR, no unified-diff deliverable.

> **`artifacts.tar.gz` is NOT necessary.** These tasks have no input
> repository to mount. `artifacts_url` and the inline `artifacts.tar.gz`
> are omitted from the bundle; `metadata.validationOutputs.artifacts`
> reports `"N/A"` (not `"OK"` and not `"MISSING"`).

---

## Input

A trajectory manifest JSON from the cloud platform with shape:

```json
{
  "run_group_id": "<rgid>",
  "task_id": "multi-agent-swarm-supplied-prompts",
  "total": N,
  "trajectories": [
    {
      "instance_id": "multi-agent-swarm-supplied-prompts-<hex>",
      "status": "completed",
      "step_name": "prompt-agent-<short>",
      "s3_uri": "s3://frontier-data-environments/swe-code-benchmark-agents-sdk/trajectory-XXXX.json",
      "presigned_url": "https://...amazonaws.com/...&Expires=..."
    },
    ...
  ]
}
```

Each trajectory is a flat JSON array of OpenInference spans. Sizes vary
wildly — observed 40 MB to 500 MB per trajectory (1.1 GB for 5 instances).

---

## Stage 1 — Download

```python
import json, urllib.request, concurrent.futures, os
with open(manifest_path) as f:
    m = json.load(f)
os.makedirs("trajectories2", exist_ok=True)

def dl(t):
    fn = f"trajectories2/{t['instance_id']}.json"
    urllib.request.urlretrieve(t["presigned_url"], fn)
    return fn

with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
    list(ex.map(dl, m["trajectories"]))
```

Parallel HTTP via presigned URLs — 5 files in ~30s on a fast link. Cache
locally; presigned URLs expire (`expires_in_s`).

---

## Stage 2 — Extract the orchestrator prompt

The cloud trajectory is the full multi-agent swarm trace: orchestrator +
N sub-agents (often 45 – 100). The relevant **supplied prompt** is the
orchestrator's first generation, but **don't trust span order** — for
large traces, sub-agents are sometimes ordered before the orchestrator
in the array.

Heuristic: stream the trajectory with `ijson` (the small ones load
fine; the 500 MB one needs streaming), collect every `generation` span's
user-message content, then pick the one matching the orchestrator
shape. Anchor on `"DELEGATION WORKFLOW"` (the prompt template every
supplied-prompt task uses); fallback to longest user prompt.

```python
import ijson
def extract_orchestrator_prompt(fn):
    candidates = []
    with open(fn, "rb") as f:
        for item in ijson.items(f, "item"):
            if item.get("name") != "generation":
                continue
            attrs = item.get("attributes", {})
            sys_msg = attrs.get("llm.input_messages.0.message.content", "")
            user_msg = attrs.get("llm.input_messages.1.message.content", "")
            if not user_msg:
                continue
            candidates.append({"sys": sys_msg, "user": user_msg,
                               "start": item["start_time"]})
    # Heuristic: orchestrator prompt starts with "### DELEGATION WORKFLOW"
    for c in sorted(candidates, key=lambda x: x["start"]):
        if "DELEGATION WORKFLOW" in c["user"][:300]:
            return c
    return max(candidates, key=lambda x: len(x["user"]))  # fallback
```

`ijson` matters: a `json.load` on the 500 MB trace allocates ~3 GB RAM.

---

## Stage 3 — Write vanilla task.yaml

Strictly two keys — `task_id` + `prompt`. No `mode`, no `include_artifacts`,
no `max_agents`, no `title`, no `name`. Runner-side flags are not part of
task.yaml.

```yaml
task_id: multi_agent_swarm__<inst_hex>
prompt: |
  ### DELEGATION WORKFLOW — <title from prompt>
  ...verbatim orchestrator user-message text...
```

`task_id` format: `multi_agent_swarm__` + the 16-hex `instance_id` suffix
(the part after `multi-agent-swarm-supplied-prompts-`).

---

## Stage 4 — gold.yaml

These tasks are intrinsically map-reduce — there's a coordinator, N
identical parallel workers, then an assembler. The SWE pipeline's
2-agent cap (`primary_implementer` + `integration_verifier`) does NOT
apply here. Use a 3-stage decomposition with `optimal_agents = N + 2`:

```yaml
task_id: multi_agent_swarm__<inst_hex>
primary_decomposition:
- subtask_id: coordinator_planner
  description: 'Read the supplied task prompt, design the N-way work
    breakdown, and write /app/artifact/plan.md as the single source of
    truth. plan.md must contain: a header describing the core
    asset/goal, an assignment table listing all N sub-agent assignments
    numbered 1..N, the per-result file schema, and the quality criteria
    for a complete vs partial result.'
  expected_input: Supplied task prompt.
  expected_output: /app/artifact/plan.md containing header, N-row
    numbered assignment table, output schema, and quality criteria.
  depends_on: []
  is_parallelizable: false
- subtask_id: parallel_workers
  description: 'In parallel, produce one result per assignment from
    plan.md (<short shape>). Each worker writes result_NNN.* files into
    /app/artifact/ per the schema. Workers operate independently.'
  expected_input: /app/artifact/plan.md (assignment N, schema, criteria).
  expected_output: 'N sets of result_NNN.* files matching the schema.
    Each begins with STATUS: complete (or STATUS: partial with reason).'
  depends_on: [coordinator_planner]
  is_parallelizable: true
- subtask_id: integration_assembler
  description: 'Audit all N result files for completeness and schema
    compliance, refine up to 10 failures via a focused retry batch,
    then assemble the final consolidated deliverables: <deliverables>.
    Write /app/artifact/summary.md with totals and unresolved gaps.'
  expected_input: All N result_NNN.* files plus plan.md.
  expected_output: Final assembled deliverables in /app/artifact/
    matching the task prompt's Phase 4 spec, plus summary.md.
  depends_on: [parallel_workers]
  is_parallelizable: false
minimum_viable_agents: 1
optimal_agents: <N + 2>
maximum_useful_agents: <N + 2>
```

No PR refs. Reference `/app/artifact/` paths only. `N` per task is read
from the prompt's "Coordinate N parallel sub-agents" line.

---

## Stage 5 — Artifacts: SKIP

**Do not generate `artifacts.tar.gz`.** These tasks have no input
repository to mount; the orchestrator's "artifacts" are the deliverables
it produces, not inputs. In the bundle:
- omit `<task_id>_artifacts.tar.gz`
- leave `artifacts_url` empty in the upload CSV
- set `metadata.validationOutputs.artifacts` = `"N/A"` and
  `rich_artifacts` = `"N/A"`

---

## Stage 6 — single_run.json (Path B: Claude Agent sub-agent)

Per-task workflow:

1. **Prep workspace** at `work_single/<inst>/`:
   - Copy `task.yaml` in. Nothing else (no `repo/`, no artifacts).

2. **Spawn one Agent per task in a single message** (multiple Agent
   tool calls in one assistant turn → true parallelism):

   ```
   Agent(
     subagent_type = "general-purpose",
     model         = "opus",
     run_in_background = true,
     prompt = textwrap.dedent("""\
       You are a single-agent solver. Your workspace is
       /home/user/evals/work_single/<inst>/.

       1. Read task.yaml.
       2. Solve the task end-to-end YOURSELF (NO sub-agents — do NOT
          spawn Agent tool calls; do not delegate; do the work in this
          transcript). The task prompt may describe a multi-agent
          swarm — ignore that and produce the deliverables yourself as
          a single agent.
       3. Write solution_summary.md in the workspace ROOT covering:
          task description, solution overview, files produced,
          key findings/output samples.

       Use Bash/Read/Edit/Write/Glob/Grep inside the workspace only.
       Stay within <workspace>. Do NOT make network calls. Do NOT use
       browse/fetch/image tools. The task may reference tools you
       don't have (browse, mango, llm_call, str_replace_editor) —
       substitute with textual descriptions or write files directly
       with Write.

       There is no turn cap. End your final response with the FULL
       CONTENTS of solution_summary.md."""),
   )
   ```

   **`run_in_background=true` + parallel dispatch is mandatory.** Five
   sequential runs take 30 – 60 min; parallel finishes the slowest one
   in ~12 min.

3. **Gotchas observed in this session:**
   - **Shared `/app/artifact` contamination.** If two solvers both
     write to `/app/artifact/` (the rooted path some prompts mandate),
     the second one reads the first's `plan.md` and solves the wrong
     task. **Mitigation:** the brief above forces workspace-relative
     paths only (`/home/user/evals/work_single/<inst>/`). When
     contamination happens, empty `/app/artifact/` and relaunch with
     an explicit "ignore anything at `/app/artifact/`" line plus the
     actual task title.
   - **API transport errors on long transcripts.** Tasks that produce
     80+ items with rich text per item (e.g. negotiation handbook)
     hit `400 Could not process image` and `socket closed
     unexpectedly` mid-run. **Mitigation:** push the data into a
     single Python literal, run it as a script. Keeps inline
     assistant text under ~30 KB per turn. Works first try.

4. **Wrap each `solution_summary.md` into a synthetic 3-span
   OpenInference trace** (`build_single_traces.py`):

   ```python
   trace_id = secrets.token_hex(16)
   agent_id = "0x" + secrets.token_hex(8)
   gen_id   = "0x" + secrets.token_hex(8)
   tool_id  = "0x" + secrets.token_hex(8)
   t_start  = "<workspace mtime, ISO Z>"
   t_end    = "<solution_summary.md mtime, ISO Z>"

   spans = [
     # 1. Root Agent span
     {"name": "Agent workflow", "kind": "SpanKind.INTERNAL",
      "context": {"trace_id": trace_id, "span_id": agent_id,
                  "trace_state": "[]"},
      "parent_id": None,
      "start_time": t_start, "end_time": t_end,
      "status": {"status_code": "OK"},
      "attributes": {"openinference.span.kind": "AGENT",
                     "agent.name": "single_solver",
                     "agent.task_id": task_id,
                     "agent.mode": "single",
                     "agent.runner": "claude-code-agent-subagent"},
      "events": [], "links": [], "resource": RESOURCE},

     # 2. Generation span (prompt + final response)
     {"name": "generation", "kind": "SpanKind.INTERNAL",
      "context": {"trace_id": trace_id, "span_id": gen_id,
                  "trace_state": "[]"},
      "parent_id": agent_id,
      "start_time": t_start, "end_time": t_end,
      "status": {"status_code": "OK"},
      "attributes": {
        "openinference.span.kind": "LLM",
        "llm.system": "anthropic",
        "llm.model_name": "claude-opus-4-6",
        "llm.input_messages.0.message.role": "system",
        "llm.input_messages.0.message.content": SINGLE_AGENT_SYSTEM,
        "llm.input_messages.1.message.role": "user",
        "llm.input_messages.1.message.content": task_prompt,
        "llm.output_messages.0.message.role": "assistant",
        "llm.output_messages.0.message.content": solution_summary_md,
      },
      "events": [], "links": [], "resource": RESOURCE},

     # 3. write_file tool span (records the summary write)
     {"name": "write_file", "kind": "SpanKind.INTERNAL",
      "context": {"trace_id": trace_id, "span_id": tool_id,
                  "trace_state": "[]"},
      "parent_id": agent_id,
      "start_time": t_start, "end_time": t_end,
      "status": {"status_code": "OK"},
      "attributes": {"openinference.span.kind": "TOOL",
                     "tool.name": "write_file",
                     "tool.parameters": json.dumps({"path":
                       "solution_summary.md",
                       "content_length": len(solution_summary_md)}),
                     "tool.output": f"wrote solution_summary.md "
                                    f"({len(solution_summary_md)} B)"},
      "events": [], "links": [], "resource": RESOURCE},
   ]
   open(f"{workspace}/{inst}_single_run.json", "w").write(
       json.dumps(spans, indent=2))
   ```

   Synthetic 3-span shape matches OpenInference; the platform accepts
   it identically to a 100-span LiteLLM trace. `agent.mode: "single"`
   distinguishes it from the multi-agent variant.

---

## Stage 7 — multi_run.json

Just copy the original cloud trajectory verbatim from `trajectories2/`
into the bundle:

```bash
cp trajectories2/multi-agent-swarm-supplied-prompts-<inst>.json \
   kimi_multi_agent_swarm_uploads/multi_agent_swarm__<inst>_multi_run.json
```

No re-encoding. No filtering. The cloud trace IS the multi-agent
trajectory — keep it as-is.

---

## Stage 8 — Upload CSV (21-col Format A)

Column order is identical to the SWE pipeline's v4b4u16 template.
Fill differences for these tasks:

| col | value |
|---|---|
| `task_yaml_solo_url` = `task_yaml_multi_url` = `task_yaml_url` | `<CDN>/<task_id>_task.yaml` |
| `gold_yaml_url` | `<CDN>/<task_id>_gold.yaml` |
| `artifacts_url` | empty (no artifacts) |
| `eval_json_url` | empty |
| `github_url` | empty (no repo) |
| `domain` | `creative_research` |
| `coordination_pattern` | `map_reduce` |
| `difficulty_rating` / `difficulty_ratings` | `medium` |
| `single_agent_run_url` | `<CDN>/<task_id>_single_run.json` |
| `multi_agent_run_url` | `<CDN>/<task_id>_multi_run.json` |
| `sub_agents_needed` | N from the prompt (45/60/80/51/100…) |
| `sub_tasks_have_dependencies` | `false` |
| `prompt_single_agent` = `prompt_multi_agent` = `prompt` | the verbatim supplied user prompt |
| `languageCode` | `en_US` |
| `metadata.validationOutputs` | `{"task_yaml":"OK","gold_yaml":"OK","artifacts":"N/A","rich_artifacts":"N/A"}` |
| `gold.yaml` | inline gold YAML text |

CDN base unchanged: `https://static.remotasks.com/uploads/69bee012be45f06904292c9a/`

```python
csv.field_size_limit(sys.maxsize)   # prompt strings are 5 KB+
csv.DictWriter(f, fieldnames=COLS, quoting=csv.QUOTE_ALL)
```

---

## Stage 9 — Bundle dir + archive

Flat layout, slug-prefix grouping (one prefix per task, no per-task subdirs):

```
kimi_multi_agent_swarm_uploads/
├── multi_agent_swarm__<inst>_task.yaml         (×5)
├── multi_agent_swarm__<inst>_gold.yaml         (×5)
├── multi_agent_swarm__<inst>_single_run.json   (×5)
├── multi_agent_swarm__<inst>_multi_run.json    (×5)
└── _upload_manifest.csv
```

Archive at sibling level:
`kimi_multi_agent_swarm_<count>tasks.tar.gz`

```bash
tar -czf kimi_multi_agent_swarm_5tasks.tar.gz kimi_multi_agent_swarm_uploads/
sha256sum kimi_multi_agent_swarm_5tasks.tar.gz \
  > kimi_multi_agent_swarm_uploads/kimi_multi_agent_swarm_5tasks.tar.gz.sha256
```

If pushing to GitHub for hand-off and the tar.gz is > 100 MB
(it will be: each multi_run.json is 40 – 500 MB), split first:

```bash
split -b 90M --numeric-suffixes=01 \
  kimi_multi_agent_swarm_5tasks.tar.gz \
  kimi_multi_agent_swarm_uploads/kimi_multi_agent_swarm_5tasks.tar.gz.part

# Receiver:
cat *.part0* > kimi_multi_agent_swarm_5tasks.tar.gz
shasum -a 256 -c kimi_multi_agent_swarm_5tasks.tar.gz.sha256
```

---

## Full re-run recipe

```bash
# 0. Save the trajectory manifest somewhere reachable.

# 1. Download all completed prompt-agent trajectories.
python3 -c "
import json, urllib.request, concurrent.futures, os
m = json.load(open('manifest.json'))
os.makedirs('trajectories2', exist_ok=True)
def dl(t):
    urllib.request.urlretrieve(t['presigned_url'],
        f'trajectories2/{t[\"instance_id\"]}.json')
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
    list(ex.map(dl, m['trajectories']))"

# 2. Extract the orchestrator prompt from each (ijson streaming, DELEGATION
#    WORKFLOW heuristic). Write vanilla tasks/<group>/<inst>.yaml
#    (task_id + prompt only).
python3 extract_prompts.py

# 3. Prep workspaces.
for inst in $(ls trajectories2 | sed 's/.json//;s/.*-//'); do
    mkdir -p work_single/$inst
    cp tasks/<group>/$inst.yaml work_single/$inst/task.yaml
done

# 4. Spawn one Agent(sub_agent_type=general-purpose, model=opus,
#    run_in_background=true) per task in a SINGLE assistant message.
#    Each Agent writes solution_summary.md in workspace root.

# 5. Build gold.yaml per task (3-stage map-reduce, optimal=N+2).
python3 build_gold.py

# 6. Build synthetic 3-span single_run.json per task.
python3 build_single_traces.py

# 7. Assemble bundle dir + 21-col upload CSV.
#    Includes: task.yaml, gold.yaml, single_run.json, multi_run.json
#    (copied from trajectories2/). Skips artifacts.tar.gz entirely.
python3 build_upload_bundle.py

# 8. Archive.
tar -czf kimi_multi_agent_swarm_5tasks.tar.gz kimi_multi_agent_swarm_uploads/
sha256sum kimi_multi_agent_swarm_5tasks.tar.gz \
  > kimi_multi_agent_swarm_uploads/kimi_multi_agent_swarm_5tasks.tar.gz.sha256

# 9. (Optional) Split for GitHub hand-off.
split -b 90M --numeric-suffixes=01 \
  kimi_multi_agent_swarm_5tasks.tar.gz \
  kimi_multi_agent_swarm_uploads/kimi_multi_agent_swarm_5tasks.tar.gz.part

# 10. cp -r kimi_multi_agent_swarm_uploads/* <cdn-target>/
```

---

## Gotchas (this variant)

1. **`artifacts.tar.gz` is NOT a deliverable** for these tasks — no
   repo to mount. The 21-col CSV row leaves `artifacts_url` empty
   and `metadata.validationOutputs.artifacts` = `"N/A"`.

2. **`task.yaml` is vanilla — task_id + prompt only.** No `mode`,
   `include_artifacts`, `max_agents`, `title`. Runner flags are NOT
   part of task.yaml.

3. **Span order ≠ time order in the cloud trajectory.** Don't grab
   the first `generation` and assume orchestrator. Anchor on
   `"DELEGATION WORKFLOW"` in the user prompt.

4. **`/app/artifact/` is shared across parallel solvers** when the
   prompt mandates absolute paths. Force workspace-relative output
   in the solver brief. If contamination happens, empty
   `/app/artifact/`, relaunch with an explicit ignore line and the
   real task title.

5. **Long transcripts kill the API.** Tasks with 80+ rich-text items
   need the data pushed into a Python literal + one `bash python3
   gen.py` call. Avoid emitting each item inline in the transcript.

6. **GitHub's 100 MB per-file cap** matters because `multi_run.json`
   files run to 500 MB. Use the split-and-reassemble dance for
   hand-off via the repo; the CDN itself has no such cap.

7. **2-agent gold cap does NOT apply.** The SWE pipeline forces
   `primary_decomposition` to exactly 2 entries; map-reduce swarm
   tasks need a 3-stage decomposition with
   `optimal_agents = N + 2`.

8. **Map-reduce coordination pattern** in the CSV — these are all
   `coordination_pattern: map_reduce`. No specialist_routing.

9. **`languageCode: en_US`** unchanged. **`difficulty_rating: medium`**
   default for these creative/research swarms.

10. **CDN project_id reuse:** `69bee012be45f06904292c9a` — same as
    kimi_10 / v4b4u16 / kimi_round2-4. Don't mint a new one.
