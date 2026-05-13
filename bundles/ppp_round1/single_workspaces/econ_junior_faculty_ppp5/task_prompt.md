# Single-Agent Attempt — Tenure-Track Pipeline Scan — top 3 junior faculty at 55 R1 economics departments

You are a SINGLE agent attempting this task on your own. The original
prompt below was designed for a coordinator + 55 parallel research
sub-agents using `llm_call`. You have none of that — no delegation, no
sub-agents, no live browser. Work from your training knowledge and
reasoning only.

## Your deliverable

Produce `solution_summary.md` in this workspace root (NOT in any
subdirectory) covering:

1. **Task overview** — one-paragraph restatement of what the swarm
   version would produce (final_report.tsv).
2. **Single-agent strategy** — how you'd realistically tackle this with
   no sub-agents. Be honest about the tradeoffs.
3. **Representative sample** — pick **5** entities (out of the 55
   the swarm would cover) and fill the schema columns
   (University, Department, Faculty_Name, Hire_Year, PhD_Granting_Institution, Publication_Count, Research_Keywords) from your training knowledge. Use the exact column
   order. Mark any field you cannot fill confidently as `UNKNOWN` with
   a one-line reason.
4. **Coverage gap** — list the remaining 50 entities you'd
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

### DELEGATION WORKFLOW — Tenure-Track Pipeline Scan

**Objective:** Coordinate 55 parallel sub-agents, each assigned to one R1 university economics department, to identify the top 3 junior faculty hired in the last 2 years. Your role as coordinator is to plan, delegate, audit, and synthesize the final dataset. Do NOT perform any research yourself; all data gathering must be delegated via `llm_call`. Your coordinator messages must be less than 15% of the total swarm token usage.

#### Phase 1 — Create the Plan

1.  First, create a comprehensive plan file. Use `str_replace_editor.create` to write to `/mnt/agent/output/plan.md`. This plan is the single source of truth for all sub-agents. It must contain:

    *   **Header:** A brief description of the task: "Identify the top 3 junior faculty (hired in the last 2 years) from 55 R1 university economics departments."

    *   **Assignment Table:** A numbered list of all 55 university economics departments. Each line represents one sub-agent's assignment.
        ```
        1. [University Name 1] Economics Department — result file: result_001.tsv
        2. [University Name 2] Economics Department — result file: result_002.tsv
        ...
        55. [University Name 55] Economics Department — result file: result_055.tsv
        ```

    *   **Output Schema:** Define the exact TSV (Tab-Separated Values) column headers that each sub-agent's output file must use. This ensures consistency for the final merge.
        `University	Department	Faculty_Name	Hire_Year	PhD_Granting_Institution	Publication_Count	Research_Keywords`

    *   **Quality Criteria:** Define what constitutes a complete result. "Junior faculty" are those hired in the last two academic years (e.g., Assistant Professors with start dates of 2022 or later). "Top 3" can be interpreted as the three most prominent or simply the first three qualified individuals found. A complete entry requires all fields in the output schema to be populated. Specify data sources: official university department websites, faculty CVs (often linked from their profile pages), and Google Scholar for publication metrics.

#### Phase 2 — Parallel Delegation

2.  Launch ALL 55 sub-agent calls in a SINGLE message. This parallel execution is the core of the swarm strategy, maximizing throughput.

    Each `llm_call` must be precisely structured:
    *   **Assignment reference:** "You are sub-agent N. Your task is defined on line N of the plan file at `/mnt/agent/output/plan.md`."
    *   **Entity scope:** The specific university department name.
    *   **Output file:** The corresponding result file, e.g., `/mnt/agent/output/result_{NNN}.tsv` (zero-padded).
    *   **fork_mode:** `none`, as each task is self-contained and relies on the central plan.
    *   **Research instructions:** Instruct the sub-agent to use the `browse` tool. The workflow should be: 1) Find the official faculty directory for the assigned department. 2) Identify faculty with titles like 'Assistant Professor' and check their start date or CV for a hire date within the last two years. 3) For each of the top 3 found, visit their personal page or find their CV to extract their PhD-granting institution. 4) Use Google Scholar to find their profile and record their total publication count and list 3-5 of their primary research keywords. 5) Save the findings to the assigned result file.
    *   **Result format:** Write results as tab-separated rows (one row per faculty member) to the assigned `.tsv` file. Do NOT include a header row in the individual result files. The very first line of the file must be `STATUS: complete` or `STATUS: partial — [reason for incompleteness]`.

    CRITICAL: All 55 `llm_call` invocations must be issued in the same turn to leverage parallel processing. Sequential delegation is inefficient and will fail the task.

#### Phase 3 — Quality Audit & Gap Fill

3.  Once the sub-agents complete, perform a quality check. Do not read the full content of every file yet.
    *   Use `str_replace_editor.view` with `view_range=(0, 1)` to read only the first line of each of the 55 result files.
    *   Parse the `STATUS` line to count how many results are `complete`, `partial`, or missing entirely.
    *   For any `partial` or missing files, launch a single, consolidated follow-up batch of `llm_call`s. Provide these agents with more specific instructions or alternative search queries based on the failure reasons.
    *   Limit this to one round of follow-ups to avoid diminishing returns.

#### Phase 4 — Assemble Final Output

4.  Synthesize the final deliverable. Read the contents of all `complete` and acceptable `partial` result files (skipping the `STATUS` line).

5.  Create a single master file, `/mnt/agent/output/final_report.tsv`. First, write the header row defined in the plan's Output Schema. Then, append the content from all the individual result files.

6.  Write a brief summary file `/mnt/agent/output/summary.md` containing:
    *   Total departments surveyed: 55
    *   Total faculty records compiled: [count]
    *   Departments with complete results: [count]
    *   Departments with partial/missing results: [count] with a brief summary of reasons.
    *   Date of research.

#### Resource Budget
*   **Phase 2 sub-agents:** 55
*   **Phase 3 follow-ups:** up to 10
*   **Sub-agent tools:** `browse`, `str_replace_editor`
*   **Max messages per sub-agent:** 25
*   **Coordinator critical-path target:** <15% of total swarm tokens
