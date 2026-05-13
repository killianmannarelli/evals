# Single-Agent Attempt — Micro-PE Rollup Targets — top 3 acquisition candidates across 75 niches

You are a SINGLE agent attempting this task on your own. The original
prompt below was designed for a coordinator + 75 parallel research
sub-agents using `llm_call`. You have none of that — no delegation, no
sub-agents, no live browser. Work from your training knowledge and
reasoning only.

## Your deliverable

Produce `solution_summary.md` in this workspace root (NOT in any
subdirectory) covering:

1. **Task overview** — one-paragraph restatement of what the swarm
   version would produce (final_report.md).
2. **Single-agent strategy** — how you'd realistically tackle this with
   no sub-agents. Be honest about the tradeoffs.
3. **Representative sample** — pick **5** entities (out of the 75
   the swarm would cover) and fill the schema columns
   (CompanyOverview, FinancialSnapshot, OwnershipProfile, InvestmentRationale, SourceURLs) from your training knowledge. Use the exact column
   order. Mark any field you cannot fill confidently as `UNKNOWN` with
   a one-line reason.
4. **Coverage gap** — list the remaining 70 entities you'd
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

### DELEGATION WORKFLOW — Micro-PE Rollup Targets

**Objective:** Coordinate 75 parallel sub-agents to research one “boring” business niche each (e.g., HVAC, elevator repair, car wash). Each sub-agent will identify the top 3 potential acquisition targets within their assigned niche that meet specific financial and demographic criteria ($1M-$5M EBITDA, owner age 55+). The final output will be a collection of CIM-style teaser decks for each identified company. Your role as coordinator is to plan, delegate, audit, and synthesize. Do NOT perform any research yourself; all data gathering must be delegated via `llm_call`. Your coordinator messages must constitute less than 15% of the total swarm token usage.

#### Phase 1 — Create the Plan

1.  Write a detailed plan to `/mnt/agent/output/plan.md` using `str_replace_editor.create`. This file is the single source of truth for all sub-agents. It must contain:

    **Header:** A brief overview of the task, its objective, and a description of the final deliverable.

    **Assignment Table:** A numbered list of all 75 business niches, one per line. This list defines the scope for each sub-agent.
    ```
    1. HVAC Services — find 3 companies — result file: result_001.md
    2. Commercial Elevator Repair — find 3 companies — result file: result_002.md
    ...
    75. Self-Storage Facilities — find 3 companies — result file: result_075.md
    ```

    **Output Schema:** A detailed markdown template for the CIM-style teaser deck. Each sub-agent must use this exact structure for each of the 3 companies they find. The schema must include sections for Company Overview, Financial Snapshot (with estimated EBITDA), Ownership Profile (with estimated owner age), Investment Rationale, and a list of Source URLs.

    **Quality Criteria:** Define what constitutes a `complete` vs. `partial` result. A complete result must include all sections of the teaser deck for 3 companies, with credible estimates for EBITDA and owner age, supported by evidence from the specified data sources (state business registries, BuiltWith, local news, industry-specific directories).

#### Phase 2 — Parallel Delegation

2.  Launch ALL 75 sub-agent calls in a SINGLE message. This parallel execution is critical for efficiency. Your single coordinator turn will spawn a massive research effort.

    Each `llm_call` must specify:
    *   **Assignment reference:** "You are sub-agent N. Your task is defined in `/mnt/agent/output/plan.md` on line N of the Assignment Table."
    *   **Entity scope:** The specific business niche to research (e.g., "HVAC Services").
    *   **Output file:** The designated result file, e.g., `/mnt/agent/output/result_{NNN}.md` (zero-padded).
    *   **fork_mode:** `none`. Each task is self-contained and guided by the central plan file.
    *   **Research instructions:** Instruct the sub-agent to use the `browse` tool to query sources like state business registries, company database tools like BuiltWith or Apollo.io, and local business news articles. Queries should be specific, such as "[niche] companies in [state/region] owner retiring" or "[company name] executive team age". The goal is to find companies fitting the $1M-$5M EBITDA and 55+ owner age criteria.
    *   **Result format:** Write the three teaser decks into the assigned result file using the exact markdown schema from the plan. The very first line of the file must be `STATUS: complete` or `STATUS: partial — [reason for incompleteness]`. For each company, all fields must be populated.

#### Phase 3 — Quality Audit & Gap Fill

3.  Once the sub-agents have completed their work, perform a quality audit. Do not read the full content of every file initially.
    *   Use `str_replace_editor.view` with a small `view_range` (e.g., lines 1-2) to read the `STATUS` line of all 75 result files.
    *   Tally the number of `complete`, `partial`, and missing files.
    *   For any `partial` or missing results, launch a targeted follow-up wave of `llm_call`s (again, in a single message) to address the gaps. Provide these agents with more specific instructions or alternative search strategies.
    *   Fully review 3-5 `complete` files to ensure the output format is correct and the quality of research is high.

#### Phase 4 — Assemble Final Output

4.  Consolidate the individual results into a comprehensive final report.
    *   Read the content of all `complete` result files.
    *   Assemble them into a single document: `/mnt/agent/output/final_report.md`.
    *   Generate a Table of Contents at the beginning of the report, linking to each business niche section.
    *   Ensure consistent formatting and headers throughout the document.

5.  Write a brief executive summary at the top of the final report, including:
    *   Total niches researched: 75
    *   Total target companies identified: [count]
    *   Completion rate: [count of complete results] / 75
    *   Date of research.

This final, consolidated document is the deliverable for the task.

#### Resource Budget
*   **Phase 2 sub-agents:** 75 (one per business niche)
*   **Phase 3 follow-ups:** up to 15 (for gaps/partials)
*   **Sub-agent tools:** browse, str_replace_editor
*   **Max messages per sub-agent:** 25
*   **Coordinator critical-path target:** <15% of total swarm tokens
