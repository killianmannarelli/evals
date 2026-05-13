# Single-Agent Attempt — Open Source Maintainer Map — top 3 non-FAANG maintainers for 70 npm/PyPI packages

You are a SINGLE agent attempting this task on your own. The original
prompt below was designed for a coordinator + 70 parallel research
sub-agents using `llm_call`. You have none of that — no delegation, no
sub-agents, no live browser. Work from your training knowledge and
reasoning only.

## Your deliverable

Produce `solution_summary.md` in this workspace root (NOT in any
subdirectory) covering:

1. **Task overview** — one-paragraph restatement of what the swarm
   version would produce (final_dossier.tsv).
2. **Single-agent strategy** — how you'd realistically tackle this with
   no sub-agents. Be honest about the tradeoffs.
3. **Representative sample** — pick **5** entities (out of the 70
   the swarm would cover) and fill the schema columns
   (PackageName, MaintainerName, GitHubProfileURL, ContactInfo, EstimatedTimezone, SponsorshipStatus, CurrentEmployer, NonFAANG_EvidenceURL) from your training knowledge. Use the exact column
   order. Mark any field you cannot fill confidently as `UNKNOWN` with
   a one-line reason.
4. **Coverage gap** — list the remaining 65 entities you'd
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

### DELEGATION WORKFLOW — Open Source Maintainer Map

**Objective:** Coordinate 70 parallel sub-agents to research one critical npm/PyPI package each, identifying the top 3 most active maintainers not employed by a FAANG company. Your role as coordinator is to plan, delegate, audit, and synthesize the final dossier. Do NOT perform any research yourself; every lookup must be delegated via `llm_call`. Your coordinator messages should be less than 15% of the total swarm token count.

#### Phase 1 — Create the Plan

1.  Write a plan file to `/mnt/agent/output/plan.md` using `str_replace_editor.create`. This file is the single source of truth for all sub-agents. It must contain:

    **Header:** A brief description of the task, the goal of finding non-FAANG maintainers, and the final output format (TSV).

    **Assignment Table:** A numbered list of all 70 npm/PyPI packages, one per line. This defines the scope for each sub-agent.
    ```
    1. [Package 1 Name] — Find top 3 non-FAANG maintainers — result file: result_001.tsv
    2. [Package 2 Name] — Find top 3 non-FAANG maintainers — result file: result_002.tsv
    ...
    70. [Package 70 Name] — Find top 3 non-FAANG maintainers — result file: result_070.tsv
    ```

    **Output Schema:** Define the exact TSV column headers each sub-agent must use. This ensures consistency for the final assembly.
    `PackageName`, `MaintainerName`, `GitHubProfileURL`, `ContactInfo`, `EstimatedTimezone`, `SponsorshipStatus`, `CurrentEmployer`, `NonFAANG_EvidenceURL`

    **Quality Criteria:** A `complete` result requires all fields to be filled for at least one maintainer. A result is `partial` if key information like `CurrentEmployer` or `ContactInfo` is missing. Explicitly state that any maintainer working at Meta, Apple, Amazon, Netflix, or Google must be excluded.

#### Phase 2 — Parallel Delegation

2.  Launch ALL 70 sub-agent calls in a SINGLE message. This parallel execution is critical for efficiency. Your single coordinator message will trigger a massive research effort.

    Each `llm_call` must be precisely structured:
    -   **Assignment reference:** "You are sub-agent N. Read `/mnt/agent/output/plan.md` and find your assigned package on line N."
    -   **Entity scope:** The specific npm/PyPI package name to research.
    -   **Output file:** `/mnt/agent/output/result_{NNN}.tsv` (zero-padded).
    -   **fork_mode:** `none` — each task is self-contained using the plan file.
    -   **Research instructions:** Provide a clear research workflow. "Use the `browse` tool. Start by finding the package's official GitHub repository. Analyze the 'Contributors' page and recent commit history to identify highly active individuals. For each promising candidate, investigate their GitHub profile, personal website, Twitter, and LinkedIn to determine their current employer. You MUST verify they do not work for a FAANG company; document the evidence URL. Search for their sponsorship status on GitHub Sponsors or OpenCollective. Find a contact method (email or social media handle) and estimate their timezone. Identify the top 3 maintainers who meet all criteria."
    -   **Result format:** "Write your findings as tab-separated rows (one row per maintainer) to your assigned result file using `str_replace_editor`. Do NOT include a header row. The first line of the file must be `STATUS: complete` or `STATUS: partial — [reason for partial status]`."

    CRITICAL: All 70 `llm_call` invocations must be in the same message to enable parallel execution.

#### Phase 3 — Quality Audit & Gap Fill

3.  Once the sub-agents complete, perform a quality check. Do not read the full content of every file yet.
    -   Use `str_replace_editor.view` with `view_range=(0, 1)` to read only the `STATUS` line of all 70 result files.
    -   Tally the number of `complete`, `partial`, and missing files.
    -   For `partial` results (e.g., employer could not be confirmed), launch a small, targeted batch of follow-up sub-agents in a single message. Give them specific instructions, like, "Confirm the employer for [MaintainerName] of package [PackageName]."
    -   Limit this to a single round of follow-ups for no more than 20% of the initial assignments.

#### Phase 4 — Assemble Final Output

4.  Consolidate all verified results into the final deliverable.
    -   Read all `result_*.tsv` files that have a `STATUS: complete` line.
    -   Create a new file `/mnt/agent/output/final_dossier.tsv`.
    -   Write the header row as defined in the `plan.md` schema.
    -   Append the content from all the individual result files, skipping the `STATUS` line for each.
    -   Sort the final table by `PackageName`.

5.  Write a brief summary report in `/mnt/agent/output/summary.md`.
    -   Total packages analyzed: 70
    -   Packages with complete results: [count]
    -   Total maintainers identified: [count]
    -   Notes on common challenges (e.g., difficulty verifying employment for independent consultants).

#### Resource Budget
-   **Phase 2 sub-agents:** 70 (one per package)
-   **Phase 3 follow-ups:** up to 14 (for gaps/partials)
-   **Sub-agent tools:** browse, str_replace_editor
-   **Max messages per sub-agent:** 25
-   **Coordinator critical-path target:** <15% of total swarm tokens
