# Single-Agent Attempt — Fractional Exec Marketplace — top 3 fractional leaders for 60 functional roles

You are a SINGLE agent attempting this task on your own. The original
prompt below was designed for a coordinator + 60 parallel research
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
3. **Representative sample** — pick **5** entities (out of the 60
   the swarm would cover) and fill the schema columns
   (Role, LeaderName, HourlyRate, TechStack, ClientLogos, CaseStudyURL, SourceURL) from your training knowledge. Use the exact column
   order. Mark any field you cannot fill confidently as `UNKNOWN` with
   a one-line reason.
4. **Coverage gap** — list the remaining 55 entities you'd
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

### DELEGATION WORKFLOW — Fractional Exec Marketplace

**Objective:** Coordinate 60 parallel sub-agents to research 1 functional role each (e.g., RevOps, Chief of Staff) and identify the top 3 fractional leaders with public case studies. Your role as coordinator is to plan, delegate, and synthesize the final dataset. Do NOT research entities yourself — every lookup must be delegated via `llm_call`. Your coordinator messages should be <15% of total assistant tokens across the swarm.

#### Phase 1 — Create the Plan

1. Write a detailed plan file to `/mnt/agent/output/plan.md` using `str_replace_editor.create`. This plan is the single source of truth for all sub-agents. It must contain:

   **Header:** A brief task description, specifying the goal of finding 3 fractional leaders per role.

   **Assignment Table:** A numbered list of all 60 functional roles, one per line. This is the master list of assignments.
   ```
   1. [Functional Role 1] — Find top 3 fractional leaders — result file: result_001.tsv
   2. [Functional Role 2] — Find top 3 fractional leaders — result file: result_002.tsv
   ...
   60. [Functional Role 60] — Find top 3 fractional leaders — result file: result_060.tsv
   ```

   **Output Schema:** Define the EXACT TSV column headers each sub-agent must use:
   `Role`, `LeaderName`, `HourlyRate`, `TechStack`, `ClientLogos`, `CaseStudyURL`, `SourceURL`

   **Quality Criteria:** Define what constitutes a complete result. A leader entry is 'complete' if it includes at least `LeaderName`, `CaseStudyURL`, and one of `HourlyRate`, `TechStack`, or `ClientLogos`. If criteria cannot be met for 3 leaders, the sub-agent should still list what they found and mark the file as `partial`.

#### Phase 2 — Parallel Delegation

2. Launch ALL 60 sub-agent calls in a SINGLE message. This parallel execution is critical for efficiency. Your coordinator turn should only consist of these 60 `llm_call` invocations.

   Each `llm_call` must include:
   - **Assignment reference:** "You are sub-agent N. Your task is to research the functional role listed at line N in `/mnt/agent/output/plan.md`."
   - **Entity scope:** The specific functional role to research.
   - **Output file:** `/mnt/agent/output/result_{NNN}.tsv` (zero-padded).
   - **fork_mode:** `none` — each task is self-contained and relies on the central plan file.
   - **Research instructions:** "Use the `browse` tool to search LinkedIn, Toptal, and personal portfolio sites. Use targeted queries like '[Role] fractional consultant case study' or 'interim [Role] Toptal'. For each of the top 3 leaders you find, extract the required data points defined in the plan's Output Schema."
   - **Result format:** "Write results as tab-separated rows (one row per leader) to your assigned result file. Do not include a header row. The first line of the file must be `STATUS: complete` or `STATUS: partial — [reason for partial result, e.g., 'could not find hourly rates']`."

   CRITICAL: Issuing all `llm_call`s in the same message is mandatory for parallel execution. Sequential delegation will fail the task.

#### Phase 3 — Quality Audit & Gap Fill

3. Once all 60 sub-agents have completed, perform a quality audit:
   - Use `str_replace_editor.view` to read the first line (the `STATUS` line) of each of the 60 result files.
   - Tally the number of `complete`, `partial`, and any missing files (if a sub-agent failed).
   - For any `partial` or missing results, launch a single batch of follow-up `llm_call`s (up to 10 agents) with more specific instructions or alternative search terms to fill the gaps.
   - Limit this to ONE round of follow-ups to avoid diminishing returns.

#### Phase 4 — Assemble Final Output

4. Consolidate all individual results into the final deliverable.
   - Read all `result_*.tsv` files.
   - Create a new file `/mnt/agent/output/final.tsv`.
   - Write the header row first, as defined in the `plan.md` file: `Role`, `LeaderName`, `HourlyRate`, ...
   - Append the content from all result files, skipping the `STATUS` lines.
   - Ensure the final TSV is well-formatted and can be easily imported into a spreadsheet or Airtable.

5. Write a brief summary report in `/mnt/agent/output/summary.md`:
   - Total functional roles researched: 60
   - Total leaders identified: [count]
   - Completion rate: [count of 'complete' files] / 60
   - Summary of challenges (e.g., "Hourly rates were difficult to find for 45% of leaders.")

#### Resource Budget
- **Phase 2 sub-agents:** 60 (one per functional role)
- **Phase 3 follow-ups:** up to 10 (for gaps/partials)
- **Sub-agent tools:** `browse`, `str_replace_editor`
- **Max messages per sub-agent:** 25
- **Coordinator critical-path target:** <15% of total swarm tokens
