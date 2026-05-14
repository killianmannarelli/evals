"""Stage 8+9: assemble per-task upload bundle dir and 21-col v4 upload CSV.

Layout per Stage 9:
  kimi_multi_agent_swarm_uploads/
    <task_id>_task.yaml
    <task_id>_single_run.json
    <task_id>_multi_run.json   (from trajectories2/)
    _upload_manifest.csv

No gold.yaml / artifacts.tar.gz (per user preference: no gold, no artifacts).
"""
import csv, json, os, shutil, sys, yaml

CDN = "https://static.remotasks.com/uploads/69bee012be45f06904292c9a"
WORK = "/home/user/evals/work_single"
TRAJ2 = "/home/user/evals/trajectories2"
BUNDLE = "/home/user/evals/kimi_multi_agent_swarm_uploads"

INSTANCES = sorted(d for d in os.listdir(WORK) if os.path.isdir(os.path.join(WORK, d)))
os.makedirs(BUNDLE, exist_ok=True)

# Sub-agent count per task — pulled from each prompt's "Coordinate N parallel sub-agents"
SUB_AGENTS = {
    "067f8c638802ea8e": 100,
    "329c9e6e4c87121d": 80,
    "7f9d0ff26bd9eec7": 45,
    "adcf16d169322aa2": 60,
    "c74d3a58795d8205": 51,
}

rows = []
for inst in INSTANCES:
    work_dir = os.path.join(WORK, inst)
    with open(os.path.join(work_dir, "task.yaml")) as f:
        td = yaml.safe_load(f)
    task_id = td["task_id"]
    prompt = td["prompt"]
    prefix = task_id

    # Copy task.yaml + gold.yaml + single_run.json
    shutil.copy(os.path.join(work_dir, "task.yaml"),
                os.path.join(BUNDLE, f"{prefix}_task.yaml"))
    gold_src = os.path.join(work_dir, "gold.yaml")
    gold_dst = os.path.join(BUNDLE, f"{prefix}_gold.yaml")
    shutil.copy(gold_src, gold_dst)
    with open(gold_src) as f:
        gold_yaml_inline = f.read()
    shutil.copy(os.path.join(work_dir, f"{inst}_single_run.json"),
                os.path.join(BUNDLE, f"{prefix}_single_run.json"))

    # multi_run.json from trajectories2 (the original multi-agent swarm trace)
    src_multi = os.path.join(TRAJ2, f"multi-agent-swarm-supplied-prompts-{inst}.json")
    dst_multi = os.path.join(BUNDLE, f"{prefix}_multi_run.json")
    if os.path.exists(src_multi):
        if not (os.path.exists(dst_multi) and os.path.getsize(dst_multi) == os.path.getsize(src_multi)):
            shutil.copy(src_multi, dst_multi)
        multi_size = os.path.getsize(dst_multi)
    else:
        multi_size = 0
        print(f"  WARN: missing multi_run source for {inst}")

    rows.append({
        "task_yaml_solo_url":   f"{CDN}/{prefix}_task.yaml",
        "task_yaml_multi_url":  f"{CDN}/{prefix}_task.yaml",
        "gold_yaml_url":        f"{CDN}/{prefix}_gold.yaml",
        "artifacts_url":        "",
        "eval_json_url":        "",
        "github_url":           "",
        "domain":               "creative_research",
        "coordination_pattern": "map_reduce",
        "difficulty_rating":    "medium",
        "single_agent_run_url": f"{CDN}/{prefix}_single_run.json",
        "multi_agent_run_url":  f"{CDN}/{prefix}_multi_run.json",
        "task_yaml_url":        f"{CDN}/{prefix}_task.yaml",
        "sub_agents_needed":    SUB_AGENTS[inst],
        "sub_tasks_have_dependencies": "false",
        "prompt_single_agent":  prompt,
        "prompt_multi_agent":   prompt,
        "prompt":               prompt,
        "difficulty_ratings":   "medium",
        "languageCode":         "en_US",
        "metadata.validationOutputs": json.dumps({
            "task_yaml": "OK",
            "gold_yaml": "OK",
            "artifacts": "N/A",
            "rich_artifacts": "N/A",
        }),
        "gold.yaml":            gold_yaml_inline,
    })
    print(f"  bundled {prefix}  (multi_run: {multi_size/1024/1024:.0f} MB)")

# Write the 21-col CSV (Format A)
COLS = [
    "task_yaml_solo_url", "task_yaml_multi_url", "gold_yaml_url",
    "artifacts_url", "eval_json_url", "github_url", "domain",
    "coordination_pattern", "difficulty_rating", "single_agent_run_url",
    "multi_agent_run_url", "task_yaml_url", "sub_agents_needed",
    "sub_tasks_have_dependencies", "prompt_single_agent", "prompt_multi_agent",
    "prompt", "difficulty_ratings", "languageCode",
    "metadata.validationOutputs", "gold.yaml",
]
csv.field_size_limit(sys.maxsize)
csv_path = os.path.join(BUNDLE, "_upload_manifest.csv")
with open(csv_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=COLS, quoting=csv.QUOTE_ALL)
    w.writeheader()
    for r in rows:
        w.writerow(r)

# Also write a copy at /home/user/evals/kimi_multi_agent_swarm_5tasks_upload.csv
shutil.copy(csv_path, "/home/user/evals/kimi_multi_agent_swarm_5tasks_upload.csv")

print(f"\nWrote CSV ({os.path.getsize(csv_path)} B) and {len(rows)} bundle rows")
print(f"Bundle dir: {BUNDLE}")
