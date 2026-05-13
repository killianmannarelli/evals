"""Wrap each single-agent solution_summary.md into a 3-span OpenInference OTel JSON.

Span shape (matches the pipeline summary, Stage 6 Path B):
  1. Agent workflow      — INTERNAL / openinference.span.kind=AGENT
  2. generation          — LLM span with system+user input, assistant output
  3. write_file tool     — TOOL span recording the summary write

Output files: bundles/ppp_round1/<slug>_single_run.json
"""

from __future__ import annotations

import json
import secrets
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ppp_tasks_meta import TASKS

REPO_ROOT = Path(__file__).resolve().parents[1]
BUNDLE_DIR = REPO_ROOT / "bundles" / "ppp_round1"
SINGLE_DIR = BUNDLE_DIR / "single_workspaces"

MODEL_NAME = "claude-opus-4-7"
LLM_SYSTEM = "anthropic"
RUNNER = "claude-code-agent-subagent"

SYSTEM_PROMPT = (
    "You are a single-agent SWE-research solver attempting a task that was "
    "designed for a parallel swarm. You have NO sub-agent delegation, NO live "
    "browser. Work from training knowledge and reasoning only. Produce "
    "solution_summary.md in your workspace root following the schema in "
    "task_prompt.md. Mark any field you cannot fill confidently as `UNKNOWN — "
    "[reason]`. Hard limit: 15 turns."
)


def _hex(nbytes: int) -> str:
    return secrets.token_hex(nbytes)


def _ns() -> int:
    return time.time_ns()


def build_trace(task: dict, prompt_text: str, summary_text: str) -> list[dict]:
    trace_id = _hex(16)
    agent_span_id = _hex(8)
    gen_span_id = _hex(8)
    tool_span_id = _hex(8)

    t0 = _ns()
    t1 = t0 + 1_000_000_000        # agent start → gen start
    t2 = t1 + 60_000_000_000       # gen end (60s synthetic)
    t3 = t2 + 100_000_000          # tool start
    t4 = t3 + 5_000_000            # tool end
    t5 = t4 + 100_000_000          # agent end

    agent_span = {
        "name": "Agent workflow",
        "context": {"trace_id": trace_id, "span_id": agent_span_id},
        "kind": "INTERNAL",
        "parent_id": None,
        "start_time": t0,
        "end_time": t5,
        "status": {"status_code": "OK"},
        "attributes": {
            "openinference.span.kind": "AGENT",
            "agent.name": "single_solver",
            "agent.task_id": task["task_id"],
            "agent.mode": "single",
            "agent.runner": RUNNER,
            "agent.ppp_id": task["ppp_id"],
            "agent.swarm_n": task["n_research_agents"],
        },
        "events": [],
        "links": [],
    }

    gen_span = {
        "name": "generation",
        "context": {"trace_id": trace_id, "span_id": gen_span_id},
        "kind": "INTERNAL",
        "parent_id": agent_span_id,
        "start_time": t1,
        "end_time": t2,
        "status": {"status_code": "OK"},
        "attributes": {
            "openinference.span.kind": "LLM",
            "llm.system": LLM_SYSTEM,
            "llm.model_name": MODEL_NAME,
            "llm.input_messages.0.message.role": "system",
            "llm.input_messages.0.message.content": SYSTEM_PROMPT,
            "llm.input_messages.1.message.role": "user",
            "llm.input_messages.1.message.content": prompt_text,
            "llm.output_messages.0.message.role": "assistant",
            "llm.output_messages.0.message.content": summary_text,
        },
        "events": [],
        "links": [],
    }

    write_params = json.dumps({
        "path": "solution_summary.md",
        "content_length": len(summary_text),
    })
    tool_span = {
        "name": "write_file",
        "context": {"trace_id": trace_id, "span_id": tool_span_id},
        "kind": "INTERNAL",
        "parent_id": agent_span_id,
        "start_time": t3,
        "end_time": t4,
        "status": {"status_code": "OK"},
        "attributes": {
            "openinference.span.kind": "TOOL",
            "tool.name": "write_file",
            "tool.parameters": write_params,
            "tool.output": f"wrote solution_summary.md ({len(summary_text)} bytes)",
        },
        "events": [],
        "links": [],
    }

    return [agent_span, gen_span, tool_span]


def main() -> None:
    missing = []
    written = []
    for task in TASKS:
        ws = SINGLE_DIR / task["slug"]
        prompt_path = ws / "task_prompt.md"
        summary_path = ws / "solution_summary.md"
        if not summary_path.exists():
            missing.append(task["slug"])
            print(f"[MISSING] {task['ppp_id']} {task['slug']}: no solution_summary.md")
            continue
        prompt_text = prompt_path.read_text()
        summary_text = summary_path.read_text()
        trace = build_trace(task, prompt_text, summary_text)
        out_path = BUNDLE_DIR / f"{task['slug']}_single_run.json"
        out_path.write_text(json.dumps(trace, indent=2))
        written.append((task["ppp_id"], out_path.name, len(summary_text)))
        print(f"[{task['ppp_id']}] {out_path.name} (summary {len(summary_text)} bytes)")

    print(f"\nWrote {len(written)} trace files; {len(missing)} missing.")
    if missing:
        print("Missing slugs:", missing)
        sys.exit(1)


if __name__ == "__main__":
    main()
