"""Generate task.yaml + gold.yaml for each PPP swarm task.

Reads the source prompt CSV and the per-task metadata, writes one
`<slug>_task.yaml` and `<slug>_gold.yaml` per PPP into bundles/ppp_round1/.

gold.yaml uses the actual swarm fanout (coordinator + N research agents),
NOT the v4b7 2-agent collapse — these tasks are explicitly multi-agent.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ppp_tasks_meta import TASKS

REPO_ROOT = Path(__file__).resolve().parents[1]
BUNDLE_DIR = REPO_ROOT / "bundles" / "ppp_round1"
SOURCE_CSV = BUNDLE_DIR / "_source_prompts.csv"


def load_prompts() -> dict[str, str]:
    csv.field_size_limit(sys.maxsize)
    out: dict[str, str] = {}
    with SOURCE_CSV.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            out[row["Id"]] = row["Prompt"]
    return out


def build_task_yaml(task: dict, prompt_text: str) -> dict:
    schema_str = ", ".join(task["output_schema_cols"])
    return {
        "task_id": task["task_id"],
        "name": task["title"],
        "domain": "swarm_research",
        "difficulty": "easy",
        "primary_pattern": task["primary_pattern"],
        "coordination_pattern": task["coordination_pattern"],
        "estimated_sub_agents": task["n_research_agents"] + 1,
        "has_dependencies": True,
        "sandbox": "docker",
        "sandbox_image": "swarm-bench-general:latest",
        "simulated_actors": [],
        "tools": [
            "llm_call",
            "str_replace_editor",
            "browse",
            "read_file",
            "list_files",
            "submit_deliverable",
        ],
        "time_limit": 5400,
        "prompt": prompt_text,
        "single_agent_prompt": prompt_text,
        "metadata": {
            "ppp_id": task["ppp_id"],
            "n_research_agents": task["n_research_agents"],
            "n_followups": task["n_followups"],
            "entity_unit": task["entity_unit"],
            "entity_unit_plural": task["entity_unit_plural"],
            "final_output_filename": task["final_filename"],
            "output_schema_columns": task["output_schema_cols"],
            "research_summary": task["research_summary"],
            "data_sources": task["sources"],
        },
    }


def build_gold_yaml(task: dict) -> dict:
    n = task["n_research_agents"]
    n_fu = task["n_followups"]
    unit = task["entity_unit"]
    schema_str = ", ".join(task["output_schema_cols"])
    final = task["final_filename"]
    summary = task["summary_filename"]
    ext = task["result_ext"]
    rows_per = task["rows_per_agent"]
    research_summary = task["research_summary"]

    plan_path = "/mnt/agent/output/plan.md"
    out_dir = "/mnt/agent/output"

    decomp = []

    decomp.append({
        "subtask_id": "coordinator",
        "description": (
            f"Coordinator role. Phase 1: write {plan_path} containing the task header, "
            f"a numbered assignment table of {n} {task['entity_unit_plural']} "
            f"(one per research sub-agent), the exact output schema columns "
            f"({schema_str}), and quality criteria (complete vs. partial). "
            f"Phase 2: dispatch all {n} research sub-agents in a single message with "
            f"`fork_mode: none`, each pointing at its zero-padded result file. "
            f"Phase 3: audit STATUS lines via `str_replace_editor.view` "
            f"with a tiny `view_range`, tally complete/partial/missing, then "
            f"launch up to {n_fu} follow-up sub-agents in one batch (single round). "
            f"Phase 4: read every complete result_NNN.{ext}, assemble "
            f"{out_dir}/{final} with the schema header row, sort by the first "
            f"schema column, and write {out_dir}/{summary}. "
            f"Coordinator messages must stay under 15% of total swarm tokens."
        ),
        "expected_input": (
            f"Master task prompt for {task['title']!s} (see task.yaml `prompt`)."
        ),
        "expected_output": (
            f"{plan_path} (plan with assignment table + schema + quality criteria); "
            f"{out_dir}/{final} (assembled deliverable, schema header + sorted rows); "
            f"{out_dir}/{summary} (tally of complete/partial/missing + brief notes)."
        ),
        "depends_on": [],
        "is_parallelizable": False,
    })

    for i in range(1, n + 1):
        nnn = f"{i:03d}"
        result_path = f"{out_dir}/result_{nnn}.{ext}"
        decomp.append({
            "subtask_id": f"research_agent_{nnn}",
            "description": (
                f"Research one {unit} assigned at line {i} of {plan_path}. "
                f"{research_summary} "
                f"Write {rows_per} to {result_path}. The first line of the "
                f"file MUST be `STATUS: complete` or "
                f"`STATUS: partial — [reason]`. Subsequent lines are the data "
                f"rows; do NOT include the schema header in this file "
                f"(coordinator owns the final header). Hard ceiling: 25 "
                f"sub-agent messages."
            ),
            "expected_input": (
                f"{plan_path} (read line {i} for the {unit} assignment + the "
                f"shared output schema and quality criteria)."
            ),
            "expected_output": (
                f"{result_path} (STATUS line + {rows_per} matching the schema "
                f"defined in plan.md)."
            ),
            "depends_on": ["coordinator"],
            "is_parallelizable": True,
        })

    return {
        "task_id": task["task_id"],
        "primary_decomposition": decomp,
        "minimum_viable_agents": 1,
        "optimal_agents": n + 1,
        "maximum_useful_agents": n + 1 + n_fu,
    }


def dump_yaml(path: Path, data: dict) -> None:
    path.write_text(
        yaml.safe_dump(
            data,
            sort_keys=False,
            default_flow_style=False,
            width=100,
            allow_unicode=True,
        )
    )


def main() -> None:
    prompts = load_prompts()
    BUNDLE_DIR.mkdir(parents=True, exist_ok=True)

    for task in TASKS:
        prompt_text = prompts[task["ppp_id"]]
        task_yaml = build_task_yaml(task, prompt_text)
        gold_yaml = build_gold_yaml(task)
        task_path = BUNDLE_DIR / f"{task['slug']}_task.yaml"
        gold_path = BUNDLE_DIR / f"{task['slug']}_gold.yaml"
        dump_yaml(task_path, task_yaml)
        dump_yaml(gold_path, gold_yaml)
        print(
            f"[{task['ppp_id']}] {task['slug']} → task.yaml + gold.yaml "
            f"(coordinator + {task['n_research_agents']} research agents)"
        )


if __name__ == "__main__":
    main()
