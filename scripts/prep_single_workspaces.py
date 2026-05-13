"""Create per-task single-agent workspaces under bundles/ppp_round1/single_workspaces/<slug>/.

Each workspace gets a `task_prompt.md` that frames the swarm prompt for a
SINGLE solver (no delegation). The single-agent variant has to acknowledge
that the original is shaped for N parallel sub-agents and instead produce
a representative degraded solution with explicit gap notes.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ppp_tasks_meta import TASKS

REPO_ROOT = Path(__file__).resolve().parents[1]
BUNDLE_DIR = REPO_ROOT / "bundles" / "ppp_round1"
SINGLE_DIR = BUNDLE_DIR / "single_workspaces"
SOURCE_CSV = BUNDLE_DIR / "_source_prompts.csv"


def load_prompts() -> dict[str, str]:
    csv.field_size_limit(sys.maxsize)
    out: dict[str, str] = {}
    with SOURCE_CSV.open(newline="") as f:
        for row in csv.DictReader(f):
            out[row["Id"]] = row["Prompt"]
    return out


SINGLE_AGENT_FRAME = """# Single-Agent Attempt — {title}

You are a SINGLE agent attempting this task on your own. The original
prompt below was designed for a coordinator + {n} parallel research
sub-agents using `llm_call`. You have none of that — no delegation, no
sub-agents, no live browser. Work from your training knowledge and
reasoning only.

## Your deliverable

Produce `solution_summary.md` in this workspace root (NOT in any
subdirectory) covering:

1. **Task overview** — one-paragraph restatement of what the swarm
   version would produce ({final_output}).
2. **Single-agent strategy** — how you'd realistically tackle this with
   no sub-agents. Be honest about the tradeoffs.
3. **Representative sample** — pick **5** entities (out of the {n}
   the swarm would cover) and fill the schema columns
   ({schema_str}) from your training knowledge. Use the exact column
   order. Mark any field you cannot fill confidently as `UNKNOWN` with
   a one-line reason.
4. **Coverage gap** — list the remaining {n_minus_5} entities you'd
   prioritize next, with one-line rationale each (no full data rows).
5. **Why a swarm beats a single agent here** — 3-5 bullets on the
   specific bottlenecks (rate limits, parallel browsing, per-entity
   depth, etc.).

## Constraints

- Hard turn cap: **15 turns**. Stop early if you have a publishable
  draft.
- Single file output: `solution_summary.md` in workspace root.
- End your final response with the **full contents** of
  `solution_summary.md` so the wrapper script can verify the write.

## Original swarm prompt (for reference)

The text below is what the coordinator role would receive. Read it for
context, then ignore the delegation instructions — you are not a
coordinator.

---

{prompt}
"""


def main() -> None:
    prompts = load_prompts()
    SINGLE_DIR.mkdir(parents=True, exist_ok=True)
    for task in TASKS:
        ws = SINGLE_DIR / task["slug"]
        ws.mkdir(parents=True, exist_ok=True)
        n = task["n_research_agents"]
        body = SINGLE_AGENT_FRAME.format(
            title=task["title"],
            n=n,
            n_minus_5=n - 5,
            final_output=task["final_filename"],
            schema_str=", ".join(task["output_schema_cols"]),
            prompt=prompts[task["ppp_id"]],
        )
        (ws / "task_prompt.md").write_text(body)
        print(f"[{task['ppp_id']}] {ws}/task_prompt.md  ({len(body)} bytes)")


if __name__ == "__main__":
    main()
