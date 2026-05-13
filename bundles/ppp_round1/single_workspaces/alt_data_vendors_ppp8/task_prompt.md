# Single-Agent Attempt — Alt-Data Source Catalog — top 3 non-traditional vendors for 65 macro indicators

You are a SINGLE agent attempting this task on your own. The original
prompt below was designed for a coordinator + 65 parallel research
sub-agents using `llm_call`. You have none of that — no delegation, no
sub-agents, no live browser. Work from your training knowledge and
reasoning only.

## Your deliverable

Produce `solution_summary.md` in this workspace root (NOT in any
subdirectory) covering:

1. **Task overview** — one-paragraph restatement of what the swarm
   version would produce (final.tsv).
2. **Single-agent strategy** — how you'd realistically tackle this with
   no sub-agents. Be honest about the tradeoffs.
3. **Representative sample** — pick **5** entities (out of the 65
   the swarm would cover) and fill the schema columns
   (Indicator, VendorName, UpdateFrequency, HistoryDepth, Price, DataSourceURL) from your training knowledge. Use the exact column
   order. Mark any field you cannot fill confidently as `UNKNOWN` with
   a one-line reason.
4. **Coverage gap** — list the remaining 60 entities you'd
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

### DELEGATION WORKFLOW — Alt-Data Source Catalog

**Objective:** Coordinate 65 parallel sub-agents, each assigned to one macro indicator, to find the top 3 non-traditional data vendors for that indicator. Your role as coordinator is to plan the research, delegate tasks, audit results for quality, and assemble the final data matrix. Do NOT perform any research yourself; all data gathering must be delegated via `llm_call`. Your coordinator messages must constitute less than 15% of the total swarm token usage.

#### Phase 1 — Create the Plan

1.  Begin by creating a detailed plan file at `/mnt/agent/output/plan.md` using `str_replace_editor.create`. This file is the single source of truth for all sub-agents. It must include:

    *   **Header:** A brief description of the task, the objective, and the final output format (a TSV file).
    *   **Assignment Table:** A numbered list of all 65 macro indicators. Each line should follow the format: `[N]. [Indicator Name] — Find top 3 alternative data vendors — result file: result_{NNN}.tsv`.
        ```
        1. Shipping bottlenecks — Find top 3 alternative data vendors — result file: result_001.tsv
        2. Cement demand — Find top 3 alternative data vendors — result file: result_002.tsv
        ...
        65. Used car parts — Find top 3 alternative data vendors — result file: result_065.tsv
        ```
    *   **Output Schema:** Clearly define the exact TSV column headers each sub-agent must use for their output file: `Indicator`, `VendorName`, `UpdateFrequency`, `HistoryDepth`, `Price`, `DataSourceURL`. This ensures consistency for the final merge.
    *   **Quality Criteria:** Define what constitutes a `complete` result (all columns filled for at least 2-3 vendors) versus a `partial` result (missing key data points like Price or History Depth). Specify that `DataSourceURL` must link directly to the vendor's product page, API docs, or pricing page.

#### Phase 2 — Parallel Delegation

2.  Launch ALL 65 sub-agent calls in a SINGLE message. This parallel execution is the core of the swarm strategy. Sequential delegation is inefficient and will fail the task.

    Each `llm_call` must contain:
    *   **Assignment reference:** "You are sub-agent N. Your task is defined on line N of the Assignment Table in `/mnt/agent/output/plan.md`."
    *   **Entity scope:** The specific macro indicator to research (e.g., "Shipping bottlenecks").
    *   **Output file:** The unique, zero-padded file path from the plan, e.g., `/mnt/agent/output/result_001.tsv`.
    *   **fork_mode:** `none`. Each sub-agent's task is self-contained and guided by the plan file.
    *   **Research instructions:** "Use the `browse` tool to find 3 non-traditional data vendors for your assigned indicator. Investigate vendor websites, API documentation, and look for sample data to find the update frequency, historical data depth, and pricing. Be persistent and try multiple search queries (e.g., '[indicator] data provider', '[indicator] alternative data API')."
    *   **Result format:** "Write your findings to the assigned result file using `str_replace_editor`. The file must be a TSV. The first line must be `STATUS: complete` or `STATUS: partial — [reason for partial status]`. The second line must be the header row from the plan. Subsequent lines are your data, with one vendor per row."

#### Phase 3 — Quality Audit & Gap Fill

3.  Once the sub-agents have completed their work, perform a quality audit. Do not read the full content of every file yet.
    *   Efficiently scan just the first line of each of the 65 result files using `str_replace_editor.view` with a small `view_range` to check the `STATUS`.
    *   Tally the number of `complete`, `partial`, and missing files.
    *   For any `partial` or missing results, launch a single, consolidated follow-up batch of `llm_call`s. These agents can be given more specific instructions, such as trying different search terms or focusing on finding a specific missing data point (e.g., pricing).
    *   Limit this to one round of follow-ups to avoid diminishing returns.

#### Phase 4 — Assemble Final Output

4.  Gather all the individual TSV files and synthesize the final report.
    *   Read the contents of all `complete` and acceptable `partial` result files.
    *   Create a final master file at `/mnt/agent/output/final.tsv`.
    *   Write a single header row at the top, matching the schema from the plan.
    *   Append the data from all individual files, ensuring consistent TSV formatting. Sort the final table by the `Indicator` column.

5.  Add a brief summary at the top of the `final.tsv` file (commented out with a `#` so it doesn't interfere with parsing).
    *   `# Total Indicators Researched: 65`
    *   `# Complete Results: [count]`
    *   `# Partial/Missing: [count]`
    *   `# Research Date: [current date]`

#### Resource Budget
*   **Phase 2 sub-agents:** 65 (one per macro indicator)
*   **Phase 3 follow-ups:** Up to 15 (for gaps/partials)
*   **Sub-agent tools:** `browse`, `str_replace_editor`
*   **Max messages per sub-agent:** 25
*   **Coordinator critical-path target:** <15% of total swarm tokens
