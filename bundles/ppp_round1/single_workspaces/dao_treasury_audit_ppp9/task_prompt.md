# Single-Agent Attempt — DAO Treasury Asset Audit — top 3 non-stablecoin assets and custody for 50 DAOs

You are a SINGLE agent attempting this task on your own. The original
prompt below was designed for a coordinator + 50 parallel research
sub-agents using `llm_call`. You have none of that — no delegation, no
sub-agents, no live browser. Work from your training knowledge and
reasoning only.

## Your deliverable

Produce `solution_summary.md` in this workspace root (NOT in any
subdirectory) covering:

1. **Task overview** — one-paragraph restatement of what the swarm
   version would produce (final_dashboard.tsv).
2. **Single-agent strategy** — how you'd realistically tackle this with
   no sub-agents. Be honest about the tradeoffs.
3. **Representative sample** — pick **5** entities (out of the 50
   the swarm would cover) and fill the schema columns
   (DAO_Name, Asset_1, Asset_1_Value_USD, Asset_2, Asset_2_Value_USD, Asset_3, Asset_3_Value_USD, Diversification_Non_Stable, Custody_Type, Multisig_Address, Signer_Count, Source_Links) from your training knowledge. Use the exact column
   order. Mark any field you cannot fill confidently as `UNKNOWN` with
   a one-line reason.
4. **Coverage gap** — list the remaining 45 entities you'd
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

### DELEGATION WORKFLOW — DAO Treasury Asset Audit

**Objective:** Coordinate 50 parallel sub-agents to research the treasury composition and custody setup of 50 major DAOs (Decentralized Autonomous Organizations). Your role as coordinator is to plan the research, delegate to sub-agents, audit the results, and synthesize the final risk dashboard. Do NOT perform any research yourself; all data gathering must be delegated via `llm_call`. Your coordinator messages should constitute less than 15% of the total swarm token usage.

#### Phase 1 — Create the Plan

1.  Begin by creating a detailed plan file at `/mnt/agent/output/plan.md` using `str_replace_editor.create`. This plan is the single source of truth for all sub-agents.

    **Header:** Include a task description, the objective (auditing DAO treasuries), and the final output format specification (a TSV file).

    **Assignment Table:** Create a numbered list of all 50 DAOs to be investigated. Each line should follow this format:
    ```
    1. [DAO Name] — Find top 3 non-stablecoin assets and custody setup — result file: result_001.tsv
    2. [DAO Name] — Find top 3 non-stablecoin assets and custody setup — result file: result_002.tsv
    ...
    50. [DAO Name] — Find top 3 non-stablecoin assets and custody setup — result file: result_050.tsv
    ```

    **Output Schema:** Define the exact TSV columns each sub-agent must produce. The required headers are: `DAO_Name`, `Asset_1`, `Asset_1_Value_USD`, `Asset_2`, `Asset_2_Value_USD`, `Asset_3`, `Asset_3_Value_USD`, `Diversification_Non_Stable`, `Custody_Type`, `Multisig_Address`, `Signer_Count`, `Source_Links`.

    **Quality Criteria:** A `complete` result must populate all fields, especially the top 3 assets and custody details. A `partial` result is one where custody information (like signer count) is unavailable after a thorough search. Specify that sub-agents must use reliable sources.

#### Phase 2 — Parallel Delegation

2.  In a SINGLE message, launch all 50 `llm_call` invocations to run in parallel. This concurrent execution is crucial for efficiency.

    Each `llm_call` must be precisely configured:
    *   **Assignment reference:** "You are sub-agent N. Your task is to audit a DAO treasury. Read `/mnt/agent/output/plan.md` and find your assigned DAO under item N."
    *   **Entity scope:** The specific DAO name (e.g., "Uniswap DAO").
    *   **Output file:** `/mnt/agent/output/result_{NNN}.tsv` (zero-padded).
    *   **fork_mode:** `none`, as each task is self-contained based on the plan file.
    *   **Research instructions:** Instruct the sub-agent to use the `browse` tool to investigate its assigned DAO. Key data sources include Etherscan (or other block explorers for the relevant chain) for on-chain holdings, the DAO's official governance forum for treasury reports and custody discussions, and Snapshot.org pages for governance proposals related to treasury management. Example queries: "[DAO Name] treasury address Etherscan", "[DAO Name] multisig signers", "[DAO Name] treasury diversification report forum".
    *   **Result format:** Write a single tab-separated value (TSV) row to the assigned result file, matching the columns in the plan's Output Schema. The file must begin with a status line: `STATUS: complete` or `STATUS: partial — [reason for partial result]`, followed by a newline, and then the TSV data row. Do not include the header row in the result file.

#### Phase 3 — Quality Audit & Gap Fill

3.  Once the sub-agents complete their work, perform a quality audit. Use `str_replace_editor.view` to read the first line of each of the 50 result files.
    *   Tally the number of `complete`, `partial`, and missing files.
    *   For any `partial` or missing results (up to a maximum of 10), launch a targeted follow-up round of `llm_call`s in a single message. Provide these agents with more specific search queries or alternative data sources to try.
    *   Randomly spot-check 3-5 `complete` files to ensure data accuracy and correct formatting.

#### Phase 4 — Assemble Final Output

4.  Consolidate all successful results into the final deliverable. Read the data row from every `complete` and acceptable `partial` result file.
    *   Merge these rows into a single file at `/mnt/agent/output/final_dashboard.tsv`.
    *   Write the header row (as defined in the plan) at the top of this file.
    *   Sort the final table alphabetically by `DAO_Name`.

5.  Write a brief summary report in `/mnt/agent/output/summary.md`. This report should include:
    *   Total DAOs audited.
    *   Completion statistics (complete/partial counts).
    *   A high-level analysis of findings, such as the most commonly held non-stablecoin assets across all DAOs, common custody setups (e.g., Gnosis Safe), and average signer counts.

#### Resource Budget
*   **Phase 2 sub-agents:** 50
*   **Phase 3 follow-ups:** up to 10
*   **Sub-agent tools:** `browse`, `str_replace_editor`
*   **Max messages per sub-agent:** 25
*   **Coordinator critical-path target:** <15% of total swarm tokens
