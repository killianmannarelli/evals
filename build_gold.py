"""Generate gold.yaml for each multi-agent-swarm task.

Tasks here fan out to N parallel sub-agents (N from the prompt's "Coordinate
N parallel sub-agents" line), so the gold decomposition is map-reduce:
coordinator -> N parallel workers -> integration assembler.
"""
import os, re, yaml, glob

WORK = "/home/user/evals/work_single"

# (N sub-agents, deliverable shape phrase, output_dir relative to /app/artifact)
TASK_SHAPES = {
    "067f8c638802ea8e": (
        100, "100 psychology replication studies",
        "result_NNN.md (YAML frontmatter + >=500-word narrative) per study; "
        "meta_analysis_data.csv; forest_plot.png; bias_table.md; final_report.md",
    ),
    "329c9e6e4c87121d": (
        80, "80 country negotiation chapters",
        "result_NNN.md per country (Cultural Context / Legal Framework / "
        "Case Study / Do's & Don'ts table >=5 rows / References); index.csv; "
        "final_handbook.md; summary.md",
    ),
    "7f9d0ff26bd9eec7": (
        45, "45 sneaker drop city campaigns",
        "result_NNN.jpg (16:9 key visual) + result_NNN.txt (STATUS: complete + "
        "mango prompt) per city; <slug>.html landing pages; index.html portal; "
        "summary.md",
    ),
    "adcf16d169322aa2": (
        60, "60 lifestyle lamp placements",
        "result_NNN.png/jpg + result_NNN.json (status + image_path + "
        "prompt_used + region_outlet) per setting; pdp_carousel_manifest.json; "
        "summary.md",
    ),
    "c74d3a58795d8205": (
        51, "51 privacy-law jurisdiction chapters (GDPR + 50 US states)",
        "result_NNN.md per jurisdiction (Core Definitions / Consumer Rights / "
        "Penalties & Enforcement / Notable Enforcement Actions); "
        "compliance_matrix.tsv (7 cols, 1 row per jurisdiction); final_guide.md",
    ),
}


def make_gold(inst):
    n, shape, deliverables = TASK_SHAPES[inst]
    task_id = f"multi_agent_swarm__{inst}"
    return {
        "task_id": task_id,
        "primary_decomposition": [
            {
                "subtask_id": "coordinator_planner",
                "description": (
                    f"Read the supplied task prompt, design the {n}-way work breakdown, "
                    f"and write /app/artifact/plan.md as the single source of truth. "
                    f"plan.md must contain: a header describing the core asset/goal, "
                    f"an assignment table listing all {n} sub-agent assignments numbered "
                    f"1..{n}, the per-result file schema, and the quality criteria for "
                    f"a complete vs partial result."
                ),
                "expected_input": (
                    "Supplied task prompt (the multi-agent-swarm orchestrator prompt)."
                ),
                "expected_output": (
                    f"/app/artifact/plan.md containing header, {n}-row numbered "
                    f"assignment table, output schema, and quality criteria."
                ),
                "depends_on": [],
                "is_parallelizable": False,
            },
            {
                "subtask_id": "parallel_workers",
                "description": (
                    f"In parallel, produce one result per assignment from plan.md "
                    f"({shape}). Each worker writes result_NNN.* files into "
                    f"/app/artifact/ per the schema in plan.md. Workers operate "
                    f"independently and do not communicate."
                ),
                "expected_input": (
                    "/app/artifact/plan.md (assignment N, schema, quality criteria)."
                ),
                "expected_output": (
                    f"{n} sets of result_NNN.* files in /app/artifact/ matching the "
                    f"schema. Each result file begins with STATUS: complete (or "
                    f"STATUS: partial with reason)."
                ),
                "depends_on": ["coordinator_planner"],
                "is_parallelizable": True,
            },
            {
                "subtask_id": "integration_assembler",
                "description": (
                    f"Audit all {n} result files for completeness and schema "
                    f"compliance, refine up to 10 failures via a focused retry "
                    f"batch, then assemble the final consolidated deliverables: "
                    f"{deliverables}. Write a brief /app/artifact/summary.md "
                    f"with totals and any unresolved gaps."
                ),
                "expected_input": (
                    f"All {n} result_NNN.* files from parallel_workers plus "
                    f"/app/artifact/plan.md."
                ),
                "expected_output": (
                    "Final assembled deliverables in /app/artifact/ matching the "
                    "task prompt's Phase 4 specification, plus summary.md "
                    "reporting coverage and any failed-and-not-recovered items."
                ),
                "depends_on": ["parallel_workers"],
                "is_parallelizable": False,
            },
        ],
        "minimum_viable_agents": 1,
        "optimal_agents": n + 2,
        "maximum_useful_agents": n + 2,
    }


for inst in sorted(TASK_SHAPES):
    work_dir = os.path.join(WORK, inst)
    out = os.path.join(work_dir, "gold.yaml")
    g = make_gold(inst)
    with open(out, "w") as f:
        yaml.safe_dump(g, f, sort_keys=False, allow_unicode=True, default_flow_style=False, width=10**9)
    print(f"wrote {out}  ({os.path.getsize(out)} B, optimal_agents={g['optimal_agents']})")
