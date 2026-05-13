"""Build the 21-column v4 upload CSV for the PPP round 1 bundle.

Column order (per the pipeline summary, Stage 8 Format A):

    task_yaml_solo_url, task_yaml_multi_url, gold_yaml_url, artifacts_url,
    eval_json_url, github_url, domain, coordination_pattern,
    difficulty_rating, single_agent_run_url, multi_agent_run_url,
    task_yaml_url, sub_agents_needed, sub_tasks_have_dependencies,
    prompt_single_agent, prompt_multi_agent, prompt, difficulty_ratings,
    languageCode, metadata.validationOutputs, gold.yaml

Invariants:
- task_yaml_solo_url == task_yaml_multi_url == task_yaml_url
- prompt == prompt_multi_agent
- eval_json_url empty
- languageCode = en_US
- metadata.validationOutputs is a JSON literal (artifacts/rich_artifacts
  are N/A here since these tasks have no source repo)
- gold.yaml column contains inline YAML text
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ppp_tasks_meta import TASKS

REPO_ROOT = Path(__file__).resolve().parents[1]
BUNDLE_DIR = REPO_ROOT / "bundles" / "ppp_round1"
SOURCE_CSV = BUNDLE_DIR / "_source_prompts.csv"
OUT_CSV = BUNDLE_DIR / "ppp_round1_upload.csv"

CDN_BASE = "https://static.remotasks.com/uploads/69bee012be45f06904292c9a/"

COLUMNS = [
    "task_yaml_solo_url",
    "task_yaml_multi_url",
    "gold_yaml_url",
    "artifacts_url",
    "eval_json_url",
    "github_url",
    "domain",
    "coordination_pattern",
    "difficulty_rating",
    "single_agent_run_url",
    "multi_agent_run_url",
    "task_yaml_url",
    "sub_agents_needed",
    "sub_tasks_have_dependencies",
    "prompt_single_agent",
    "prompt_multi_agent",
    "prompt",
    "difficulty_ratings",
    "languageCode",
    "metadata.validationOutputs",
    "gold.yaml",
]

VALIDATION_OUTPUTS = json.dumps({
    "task_yaml": "OK",
    "gold_yaml": "OK",
    "artifacts": "N/A",
    "rich_artifacts": "N/A",
})


def load_prompts() -> dict[str, str]:
    csv.field_size_limit(sys.maxsize)
    out: dict[str, str] = {}
    with SOURCE_CSV.open(newline="") as f:
        for row in csv.DictReader(f):
            out[row["Id"]] = row["Prompt"]
    return out


def row_for(task: dict, prompt_text: str) -> dict:
    slug = task["slug"]
    task_yaml_url = f"{CDN_BASE}{slug}_task.yaml"
    gold_yaml_url = f"{CDN_BASE}{slug}_gold.yaml"
    single_run_url = f"{CDN_BASE}{slug}_single_run.json"
    gold_inline = (BUNDLE_DIR / f"{slug}_gold.yaml").read_text()
    return {
        "task_yaml_solo_url": task_yaml_url,
        "task_yaml_multi_url": task_yaml_url,
        "gold_yaml_url": gold_yaml_url,
        "artifacts_url": "",
        "eval_json_url": "",
        "github_url": "",
        "domain": "swarm_research",
        "coordination_pattern": task["coordination_pattern"],
        "difficulty_rating": "easy",
        "single_agent_run_url": single_run_url,
        "multi_agent_run_url": "",
        "task_yaml_url": task_yaml_url,
        "sub_agents_needed": task["n_research_agents"] + 1,
        "sub_tasks_have_dependencies": True,
        "prompt_single_agent": prompt_text,
        "prompt_multi_agent": prompt_text,
        "prompt": prompt_text,
        "difficulty_ratings": "easy",
        "languageCode": "en_US",
        "metadata.validationOutputs": VALIDATION_OUTPUTS,
        "gold.yaml": gold_inline,
    }


def main() -> None:
    csv.field_size_limit(sys.maxsize)
    prompts = load_prompts()
    rows = [row_for(t, prompts[t["ppp_id"]]) for t in TASKS]
    with OUT_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {OUT_CSV} ({len(rows)} rows, {len(COLUMNS)} cols)")
    print(f"Size: {OUT_CSV.stat().st_size} bytes")


if __name__ == "__main__":
    main()
