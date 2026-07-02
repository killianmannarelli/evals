You are evaluating the quality of a single agentic AI task benchmark. You have full file access to verify claims against actual data.

## Benchmark Context

These are agentic benchmarks with intentionally open-ended, conversational prompts. The agent discovers what needs to be done by exploring the task's data directory at runtime.

The agent's runtime environment is defined by the Dockerfile and docker-compose.yaml in the task directory. The agent typically has full filesystem access, can run Python with pip, and can install packages on the fly. Check the Dockerfile if you need to verify specific capabilities before flagging tools as missing. **Only the contents of the `environment/` directory are accessible to the agent at runtime** — files outside `environment/` (e.g., `rubrics.json`, `tests/`, `task.toml`) are not visible to the agent.

The `tests/` directory is **not accessible to the agent at runtime** — it is mounted only by the grading harness after the agent finishes. Files inside `tests/` (e.g., `evidence.json`, `test_weights.json`) are grading artifacts, not task inputs.

Pytest tests and LLM-graded rubrics are **supplementary** with distinct ownership:
- **Tests** own objective/mechanical verification: API state changes, output file structure, delivery confirmation, negative guards.
- **Rubrics** own subjective evaluation: content quality, reasoning, safety, instruction-following nuance.
### Multimodal Artifacts

Some tasks contain image files (JPG, PNG, HEIC, WEBP), PDFs, spreadsheets (XLSX), and ZIP archives among the task inputs (commonly under `artifacts/inputs/`, often nested in subdirectories). These are task input files the agent sees at runtime. `{task_dir}` is the task's `environment/` directory. Run `ls -R {task_dir}` to discover all input files — there is no pre-built manifest listing them.

When rubric criteria reference visual content (e.g., "transcription of slide 17 includes…", "photo shows…"), you **MUST VIEW the referenced image files** to verify whether the rubric's expected content is actually present in the image. Do not guess about image contents — read them.

For PDFs and XLSX files, read or examine them to verify rubric claims about their content. For ZIP archives (e.g., `images.zip`), note their presence — the agent can extract them at runtime, so rubrics referencing their contents are valid.

## Evaluation Dimensions

### 1. Prompt Quality

- **prompt_clarity** (1-5): How clear is the prompt?
  - 1: Contradictory or incomprehensible — objective cannot be determined even with input data
  - 2: Extremely vague with no discernible direction
  - 3: Genuinely ambiguous even with input data — agent cannot determine correct action for a significant portion
  - 4: Clear overall intent with minor ambiguities
  - 5: Crystal clear

  Do NOT penalize for "not specifying file paths" — that's a benchmark convention. Do NOT penalize because the prompt doesn't list every task — if actionable work can be inferred from data, the prompt is clear enough.

### 2. Rubric Accuracy

DO NOT BE LAZY. For EACH rubric (you MUST examine EVERY rubric, do not skip any), check three things:

1. **Evaluable?** Can an LLM grader judge this criterion as pass/fail? Rubrics are graded by an LLM, not regex. A rubric is NOT evaluable if it's so vague that even an LLM grader cannot determine pass vs fail (e.g., "response is helpful" with no context).

2. **Accurate?** Does it correctly reflect what the prompt + data together require? A rubric is NOT accurate if it:
   - Contradicts what the prompt asks for (e.g., penalizes behavior the prompt requests)
   - Contradicts the available data (e.g., expects the agent to confirm an action when the data shows a blocker)

3. **Correct sign?** Does the weight sign match the criterion's intent? A rubric has a sign error if the criterion describes *desired* behavior (e.g., "Agent proceeded resourcefully without asking unnecessary questions") but carries a negative weight — penalizing agents for doing the right thing. Conversely, a criterion describing *undesired* behavior with a positive weight is also a sign error. Flag these with `"issue": "sign_error"`.

Critical guidance — verification procedure (do this FIRST, before judging any rubric):
- **You have full file access.** Read the actual data files to verify rubric claims — don't guess.
- **Identify the correct runtime database before querying.** Services load data in different ways — SQLite files in `seed/`, CSVs, or in-memory seed code. Read `storage.py` or `server.py` to find which data source the service actually loads — do NOT assume any particular file is authoritative — e.g., a `seed/state.sqlite3` may contain pre-populated data that the service never loads because `server.py` points to a different DB file.
- **Verify data through the API's lens, not raw files.** Raw data files (CSVs, JSON) may contain data for multiple users, date ranges, or entities. The agent accesses data through mock APIs that filter by persona, date range, or other parameters. When verifying answer-key rubrics with specific values, check `*_data.py` or `server.py` for filtering logic (default user/persona, date scoping, pagination limits) to confirm the rubric's expected values match what the API actually serves to the agent — not just what exists somewhere in the raw data.

Validity rules — what counts as a valid or invalid rubric:
- **Data-implied actions are valid rubric targets.** When the prompt gives a general directive ("take care of my messages", "handle whatever needs handling") and the data contains specific items requiring action, rubrics checking those items are valid — even though the prompt doesn't name them. This includes multi-step inference: e.g., if Person A asks "are you coming to dinner?" and the user says "yes to everything this week" in a separate conversation, a rubric expecting the agent to confirm dinner is valid — the agent should connect these data points.
- **Data-implied details are valid rubric targets.** When the prompt asks for analysis and the data contains relevant metrics, rubrics checking those metrics are valid. Do NOT treat prompt examples as an exhaustive list excluding other relevant data.
- **Data-implied output formats are valid.** When the environment provides a specific tool (Notion API, Slack API), rubrics expecting output through that tool are reasonable.
- **Answer-key rubrics are valid — when the answer is deterministic.** Rubrics checking specific output values (e.g., "Glucose value is 105") are ground-truth checks verifying correct data extraction. Do NOT flag just because the prompt text doesn't mention the values.
- **Overly specific rubrics penalize valid alternatives.** Flag with `"issue": "overly_specific"` only when the underlying choice is arbitrary — multiple equally valid options exist and the rubric picks one with no justification. Do NOT flag if (a) the correct answer is uniquely determined by the data, even if the rubric's wording is slightly off, or (b) multiple options exist but the rubric's choice is the best fit given the context.
- **Negative rubrics** (negative score) are penalty guards that DEDUCT points for bad behavior (hallucinating data, incorrect formulas, exposing PII). Read as "agent should NOT do X." Only flag if the penalized behavior is actually correct.
- **Intentionally absent data is not a rubric defect.** When data appears missing (e.g., a referenced support ticket doesn't exist), check whether rubrics form a coherent cluster around the absence — negative rubrics penalizing fabrication, positive rubrics rewarding graceful handling. If so, the absence is by design (e.g., hallucination resistance testing) and these rubrics are valid, not inaccurate.
- **Rubrics are LLM-graded, not regex-matched.** Only flag a rubric as inaccurate if the error would mislead the LLM grader — not for cosmetic differences (ID prefixes, formatting variants) that the grader would see through when all substantive details match.
- **Skill-usage rubrics are valid when the skill genuinely helps.** The prompt is not expected to tell the agent which skills to use — discovering and leveraging available tools is core agentic behavior. Only flag a skill-usage rubric as inaccurate if the rubric-required skill is broken, dysfunctional, or irrelevant to the task. Read the skill's SKILL.md and any scripts it provides to verify before flagging.
- **Runtime-discoverable data is available data.** The agent has pip, apt, curl, and general tooling in the Docker environment. If the prompt names a package, library, or external resource that the agent can install or fetch at runtime, rubrics referencing that data are valid — the data is reachable, not missing. Do NOT flag rubrics as inaccurate just because the referenced artifacts aren't pre-loaded in `input/`.
- **When a task provides an evaluation framework, use it.** If the task asks the agent to review or assess content using a provided framework (governance policies, risk taxonomies, review rubrics), consider that framework when judging rubric accuracy. Content that appears benign on the surface may have legitimate issues under the task's analytical lens.
- Only flag a rubric as inaccurate if it **contradicts** the prompt or the available data, NOT because the action/format/value isn't explicitly stated in the prompt — as long as following the rubric makes the agent produce objectively better output.

### 3. Test Correctness

If a task has zero tests (empty `test_code` and `test_sh` in the batch JSON, or no `tests/` directory in task_dir), skip this dimension entirely: set `problematic_tests` to `"[]"` and `test_quality_rationale` to `"No tests in this task."` Then evaluate Coverage & Balance based on rubrics alone — do not penalize `criteria_completeness` for lack of test coverage.

DO NOT BE LAZY. For each `def test_*` function (you MUST examine EVERY test, do not skip any), identify whether its assertions are logically sound and technically correct. Report issues in `problematic_tests` — this dimension evaluates only the quality of tests that exist. The *absence* of tests is a coverage issue (evaluated under Coverage & Balance). If a task has zero tests, leave `problematic_tests` empty.

  **When a task has no pytest tests** (no `test_outputs.py` or `test.sh` — check the batch JSON `has_pytest_tests` field): This is normal for LLM-rubric-only tasks. Leave `problematic_tests` as an empty array and set `test_quality_rationale` to "No pytest tests in this task; evaluation uses LLM-graded rubrics only."

  **For each test, first check if a rubric covers the same requirement.** If yes, the test is a redundant safety net — still evaluate it for real bugs (wrong assertions, contradicts prompt), but do NOT flag it for being weak (existence-only, `!= old_value`, count-only). Weakness is only a problem when the test is the **sole** verification layer for that requirement.

  **Judge the assertion code, not the test name or comment.** A misleading docstring or test name does not make the assertion wrong. If the actual assertion logic would correctly pass/fail based on agent behavior, the test is sound — even if the comment describes the wrong rationale. Conversely, a well-named test with a broken assertion is still a real issue.

  **Read the actual *_data.py files** to understand what mock APIs return before judging assertions. Mock APIs may transform CSV column names (e.g., `user_id` → `from_user_id`).

  Examples of issues (not exhaustive): wrong API endpoint or expected values, tautological assertions that always pass by construction, seed-comparison without ground truth (`!= old_value` instead of `== expected_value`), existence-only checks where a verifiable correct value exists (e.g., `len(orders) >= 1` when the test could check `order["status"] == "SHIPPED"`), overly strict matching or wrong tolerances, fragile regex.

  Keyword-list matching with `any()` or flexible OR conditions (e.g., checking if a note mentions at least N of M reasonable terms) is a standard test pattern for verifying free-form content — do NOT flag as brittle unless the keyword list is unreasonably narrow or the terms are unlikely to appear in a valid response.

  Do NOT flag a test as overly strict if the stricter assertion makes the agent produce objectively better output. Only flag when the strictness is very arbitrary or contradicts the prompt's flexibility.

  **Seed-comparison (`!= old_value`) case-by-case:**
  - Objectively determinable correct value AND no rubric covers it → weak assertion, flag it
  - Genuinely subjective (e.g., risk assessment "high" vs "moderate") → appropriate, do NOT flag

### 4. Coverage & Balance

The final reward for a task is calculated as:

    reward = sum(weights of passed items) / sum(all positive weights)

where "items" includes BOTH rubrics and tests in one shared pool. Each rubric and each test carries a weight. Test weights come from the `test_weights` field in the batch JSON (a dict mapping test name to its point weight); if `test_weights` is empty or absent, each test has a default weight of 3. When evaluating `has_redundancies` and `score_distribution_reasonable`, consider whether test+rubric overlap on the same requirement produces a combined weight that is disproportionate to the requirement's importance.

IMPORTANT guidance for criteria_completeness and uncovered_requirements:
- Do NOT count criteria that are implicitly verified by answer-key rubrics as uncovered. For example, if rubrics check for specific values that can only come from input files, "verifying the agent read the files" is implicitly covered.
- Do NOT count criteria that would be unevaluable by either grader or test as "uncovered." Unevaluable means: agent execution behaviors, intermediate steps (API call ordering, retry logic, tool selection), or purely internal system state with no user-facing manifestation.
- A requirement covered by a test does NOT need a rubric, and vice versa. Only flag requirements that have NEITHER test nor rubric coverage. Score based on their **joint** coverage — not the worse of the two individually. If rubrics thoroughly cover a requirement, weak or missing test coverage for that same requirement does not reduce the completeness score.

- **criteria_completeness** (1-5): Do rubrics + tests jointly cover all key success criteria?
  - 1: Major requirements have neither rubric nor test coverage
  - 3: Core requirements covered, some gaps
  - 5: All key requirements covered — no meaningful gaps in joint rubric + test coverage
- **uncovered_requirements**: Requirements with NEITHER rubric nor test coverage. Empty string if none.
- **has_redundancies** (yes/no): Any rubrics/tests testing the same thing?
- **score_distribution_reasonable** (yes/no): Rubrics have explicit weights; test weights come from the `test_weights` field (defaulting to 3 per test if absent). Is the overall evaluation weight distribution reasonable, considering both rubrics and tests combined? Are the most important requirements weighted highest? Is positive/negative balance sensible? Check that each rubric's weight sign is correct given its criterion: rubrics that reward desired behavior should have positive weights, rubrics that penalize bad behavior should have negative weights. If any rubric has a `sign_error`, score "no".

  **Do NOT conflate with rubric accuracy.** A rubric being factually inaccurate is a Dimension 2 issue, not a distribution issue. Score "no" only for sign errors, gross weight imbalance, or redundant weight stacking — not because a rubric has wrong expected values.

**When a task has no pytest tests** (`has_pytest_tests` is false in the batch JSON): Evaluate rubric coverage alone. The absence of tests does not automatically make coverage incomplete — if rubrics thoroughly cover all key requirements, `overall_completeness` can still be 5. Set `has_redundancies` based on rubric-to-rubric overlap only. Evaluate `score_distribution_reasonable` based on rubric weights alone.

### 5. Task Adequacy

- **is_self_contained** (yes/no): Can the agent complete the task as defined by the rubrics and tests, using the provided data, environment, and resources discoverable at runtime (e.g., installable packages named in the prompt)? This is the primary signal for whether a task is broken. Score "no" only when the task is unsolvable — not for minor gaps or rough edges.
- **input_adequacy** (1-5): Quality of the data available to the agent. A score below 5 does not necessarily mean the task is broken — minor issues (e.g., a misleading filename, a non-essential file missing) warrant a 4 but `is_self_contained` remains "yes". Reserve low scores (1-2) for issues that genuinely block task completion.
  - 1: Critical data is missing — task is unsolvable
  - 3: Most data is present, some rubrics may require unavailable information
  - 5: All required data is available

  **Before scoring below 5, check whether the rubrics treat the absence as the challenge itself.** Many tasks intentionally omit data, mismatch persona names, or introduce conflicting sources to test agent behavior (inference, hallucination resistance, source prioritization, deriving answers from provided artifacts). If rubrics reward the agent for handling the gap correctly — or penalize fabricating missing data — the absence is by design, not a defect. This includes tasks where a specific answer must be derived from source code, binaries, configuration files, or other bundled artifacts rather than looked up directly.

  **Data discoverable at runtime counts as available.** The agent has pip, apt, curl, and general internet-capable tools in the Docker environment. If the prompt names a package, service, or external resource that the agent can install or fetch at runtime, that data is reachable — not missing. For example, a prompt referencing a "maze-runner package" is a breadcrumb the agent can follow via `pip install maze-runner`. Score based on whether a resourceful agent *can* obtain the data, not whether it's pre-loaded in `input/`.
- **environment_adequacy** (1-5): Quality of the runtime environment. Same principle as input_adequacy — minor gaps warrant a 4 but don't make the task broken. Reserve low scores (1-2) for issues that genuinely block task completion.
  - 1: Critical tools/services are missing — task is unsolvable
  - 3: Most capabilities present, some gaps
  - 5: Environment fully supports all required actions
  Only score low if a specialized external API is genuinely missing. Do NOT downgrade because a service returns empty results for a particular query — that is a data issue (input_adequacy), not an environment issue. The environment is adequate if the tool/service exists and functions; whether it contains relevant data is a separate question.
- **missing_data**: Data required by prompt/rubrics/tests but not found in the task directory. Empty string if none.
- **missing_tools**: Tools required but not provided. Only flag specialized external APIs — do NOT list filesystem, PDF/Excel/CSV readers, image processing, web scraping, etc.


## Output Format

Respond ONLY with valid JSON:
```json
{
  "prompt_clarity": <int 1-5>,
  "prompt_quality_rationale": "<brief>",
  "problematic_rubrics": [
    {"rubric_number": <int>, "criterion": "<text>", "issue": "<not_evaluable|inaccurate|sign_error|overly_specific>", "rationale": "<brief>"}
  ],
  "rubric_quality_rationale": "<brief>",
  "criteria_completeness": <int 1-5>,
  "uncovered_requirements": "<comma-separated or empty>",
  "has_redundancies": "<yes|no>",
  "score_distribution_reasonable": "<yes|no>",
  "coverage_and_balance_rationale": "<brief>",
  "is_self_contained": "<yes|no>",
  "input_adequacy": <int 1-5>,
  "environment_adequacy": <int 1-5>,
  "missing_data": "<comma-separated or empty>",
  "missing_tools": "<comma-separated or empty>",
  "task_adequacy_rationale": "<brief>",
  "problematic_tests": [
    {"test_name": "<name>", "issue_type": "<incorrect_assertion|wrong_endpoint|brittle_match|tautological|other>", "rationale": "<brief>"}
  ],
  "test_quality_rationale": "<brief>"
}
```
