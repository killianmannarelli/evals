<!-- pulled from Redash query 304995 (SPEC_GETTER) for project 69f95a0f0992772af7907a03 -->

# V10 - 6/18 Non-failing error for universe inconsistencies

## Prompt - MM dependence
**Bucket:** Other
**Question:** Rate the MM dependence of the Prompt dimension.
**Description:** NOTE: This error encompasses cases where a non-text input file can be referenced, but is not necessary to reference. E.g., the prompt requests a summary of an audio file, but a transcript of the audio file is also present in the environment. Since the purpose of this project is to assess the MM reasoning of trajectories, environments/prompts that enable the agent to complete the task without such reasoning are similar to "Leaking the Solution" errors on other projects. See the spec doc for examples. For all options except the last, apply the error category.
**Error categories:** [All] [All] [Fail - MM Dependence]

**Options:**

- **Score 5 — Pass**
  The prompt, in the context of the environment, cannot be answered without referencing non-text files in the workspace.

- **Score 2 — Other** (justification required)
  The prompt does not require the agent to reference non-text input files in the environment; the explicit requests of the prompt can be completely fulfilled without any multimodal reasoning or processing.

---

## Prompt - Output file(s) name
**Bucket:** Other
**Question:** Rate the Output file(s) name of the Prompt dimension.
**Description:** The user must specify in the prompt the name that the model should assign to the output file, if the output is expected to be a file. See the spec doc for examples. For all options except the last, apply the error category.
**Error categories:** [All] [All] [Fail - Missing output filename]

**Options:**

- **Score 5 — Pass**
  The prompt requested a file as output and successfully specified the filename.

- **Score 2 — Other** (justification required)
  The prompt requested a file as output, but the filename was not specified.

---

## Prompt - Feasibility With Tools
**Bucket:** Other
**Question:** Rate the Feasibility With Tools
 of the Prompt dimension.
**Description:** The model has access to all tools available in openclaw and is able to create virtual environments and install any python library. So anything that can be solved using a python library running in a linux environment is fair game. See the spec doc for examples. For all options except the last, apply an error category.
**Error categories:** [All] [All] [Non-Fail - Feasibility with Tools] | [All] [All] [Fail - Feasibility with Tools]

**Options:**

- **Score 5 — Pass**
  The requests are completely actionable by the tool framework

- **Score 3 — Other** (justification required)
  One or more secondary requests are impractical or impossible and can't be answered by the tools available or enabled for the task

- **Score 2 — Other** (justification required)
  The primary request is impractical or impossible and can't be answered by the tools available or enabled for the task

---

## Input Artifacts - Realism
**Bucket:** Other
**Question:** Rate the Realism of the Input Artifacts dimension.
**Description:** Tasks should match real-world use-cases and not look contrived or made up. Real user data is messy — IMG_0427.HEIC, duplicates, missing timestamps, blurry phone shots, scanned-skewed PDFs, mixed orientations. Tasks where input_files/ is a curated set of perfectly-cropped JPGs are contrived. See the spec doc for examples. For all options except the last, apply an error category.
**Error categories:** [All] [All] [Fail - Contrived Inputs] | [All] [All] [Non-Fail - Partially Contrived Inputs]

**Options:**

- **Score 5 — Pass**
  The multimodal inputs for the task are plausible and realistic in the context of the prompt; A real user could reasonably have attached these same inputs.

- **Score 3 — Other** (justification required)
  The multimodal inputs for the task are slightly unrealistic in the context of the prompt, but it is possible that a real user may include inputs of similar quality or standardization. A reasonable explanation exists for why the inputs may seem unnatural, but actually are not (e.g., the user mentions they're analyzing a public dataset, and this premade dataset is among the inputs), OR <=20% of the multimodal inputs for the task are highly realistic in the context of the prompt.

- **Score 2 — Other** (justification required)
  >20% of the multimodal inputs for the task (or 1+ xlsx, docx, or pdf inputs) are highly unrealistic in the context of the prompt; They are highly artificial, overly curated, or otherwise "too perfect" to reflect a real-world use-case, and there is no reasonable explanation for this (e.g., curated & standardized MNIST handwriting samples are included alongside a prompt asking the agent to digitize notes)

---

## Input Artifacts - Artifact Verification
**Bucket:** Other
**Question:** Rate the Artifact Verification of the Input Artifacts dimension.
**Description:** The rubric or tests should verify a value, match, mismatch, visual detail, quality judgment, extraction result, or decision that depends on the media. It is not sufficient to only check for existence. See the spec doc for examples. For all options except the last, apply the error category.
**Error categories:** [All] [All] [Fail - Missing Artifact Verification]

**Options:**

- **Score 5 — Pass**
  At least one test/criterion exists which is dependent on the contents (rather than just the existence) of a non-text input file.

- **Score 2 — Other** (justification required)
  Across both forms of verifier (tests and rubric criteria), no test/criterion dependent on the content of a non-text file exists.
  
  Note: Tests/Criteria which only verify existence (e.g., a test asserting that some given file exists in a particular location) do not count as a test/criterion that is "dependent on content."

---

## Input Artifacts - Leak Prevention
**Bucket:** Other
**Question:** Rate the Leak Prevention
 of the Input Artifacts dimension.
**Description:** Evaluates the degree to which the task remains a true "inference" challenge by ensuring no "spoiler" information is present in the administrative or metadata layers. It checks that filenames, asset manifests, contributor notes, and helper documents are completely sanitized of the solutions, values, or conclusions the model is expected to derive solely from the multimodal media. See the spec doc for examples. For all options except the last, apply an error category.
**Error categories:** [All] [All] [Non-Fail - Suggestive Metadata] | [All] [All] [Fail - Direct Answer Leak]

**Options:**

- **Score 5 — Pass**
  All non-media identifiers are strictly neutral or randomized. Filenames follow a "messy" real-world convention (e.g., IMG_0427.HEIC, Doc_Scan_v2.pdf) and notes are restricted to process instructions, forcing the agent to rely entirely on its multimodal perception to find the answer.

- **Score 3 — Other** (justification required)
  The answer isn't explicitly stated, but the labeling provides heavy "leading" hints that narrow the search space unnaturally. For example, naming an image kitchen_sink_damage_closeup.jpg when the user’s prompt was a vague "Find all issues in this house."

- **Score 2 — Other** (justification required)
  The solution is explicitly stated in a non-media field. For example, a file is named overdue_balance_500.pdf when the task is to find the balance, or the contributor notes state "The agent should see the crack in the foundation" in a field the model can access.

---

## Verifiers - Safety
**Bucket:** Other
**Question:** Rate the Safety of the Verifiers dimension.
**Description:** Medical images, homework screenshots, tax/financial documents, insurance claims, seller messaging, faces, children, IDs, and private images need explicit limits and should use mocked or synthetic data where appropriate. See the spec doc for examples. For all options except the last, apply the error category.
**Error categories:** [All] [All] [Fail - Harmful Inputs]

**Options:**

- **Score 5 — Pass**
  No provided input files contain real PII.

- **Score 2 — Other** (justification required)
  One or more input artifacts are harmful and include sensitive private information that can identify a real, existing person. The inputs(s) are of a sensitive nature (see notes for examples) and are not synthetic, fabricated, or mocked.

---

## Silver Trajectory - Category and Subcategory
**Bucket:** Other
**Question:** Only evaluate if the silver trajectory is present -- otherwise skip this selection. Rate the Category and Subcategory of the Silver Trajectory dimension.
**Description:** Categories:

Visual Learning
Users leverage academic media like worksheets or slides for content mastery. The agent interprets text and diagrams to generate study artifacts such as notes, lab reports, and guides.

Subcategories: Homework/Problem Solving, Lab/Fieldwork Documentation, Textbook/Lecture Comprehension

Commerce & Product
Shoppers and sellers use marketplace imagery to manage listings. The agent matches items across platforms, audits photo quality, and ensures brand or packaging compliance.

Subcategories: Visual Shopping/Comparison, Product Listing QA, Brand/Packaging Audit

Creative & Media
Creators refine existing visual content through editing and auditing. The agent applies operations like cropping, zooming, or feedback to user-shot footage and designs without generating new assets.

Subcategories: Image/Video Editing, Social Media Content Audit, Design/Portfolio Review

Operations & QA
Acting as a back-office operator, the agent processes visual evidence such as receipts or screenshots. It updates systems of record, manages inventory, and validates claims against visual data.

Subcategories: Document/Receipt Processing, Inventory Visual Audit, UI/UX Screenshot Audit/Form-filling

Health & Wellness
Users track physical health or nutrition through photos of meals and symptoms. The agent analyzes visual changes over time and compares them against nutritional or medical references.

Subcategories: Skin/Symptom Triage, Nutrition/Meal Logging

Property & Space
Homeowners and agents assess physical environments using room or renovation photos. The agent detects progress changes, matches listings to reality, and reviews interior staging.

Subcategories: Real Estate Listing Review, Interior Design/Renovation. See the spec doc for examples. For all options except the last, apply the error category.
**Error categories:** [All] [All] [Non-Fail - Category Relevance]

**Options:**

- **Score 5 — Pass**
  The Trajectory is clearly related to the selected category.

- **Score 3 — Other** (justification required)
  The Trajectory is objectively unrelated to the selected category, or contradicts the definition of, the assigned category.
  The Trajectory is somewhat related to the selected category, but better fits a different category.
  
  Note: subcategories are not defined and misalignments should not be flagged.

---

## Silver Trajectory - Cross-Modal & Cross-Service Synthesis
**Bucket:** Other
**Question:** Only evaluate if the silver trajectory is present -- otherwise skip this selection. Rate the Cross-Modal & Cross-Service Synthesis of the Silver Trajectory dimension.
**Description:** Evaluates the agent's ability to execute complex reasoning chains where information is not just gathered, but transformed or verified across different modalities (e.g., Image → Text) or services (e.g., PDF → Calendar). It measures whether the agent can successfully use an output from one source as a mandatory predicate for the next step, or if it can identify discrepancies when cross-referencing multiple "messy" real-world artifacts. See the spec doc for examples. For all options except the last, apply the error category.
**Error categories:** [All] [All] [Fail - Disconnected Processing] | [All] [All] [Fail - Simple Processing] | [All] [All] [Non-Fail - Trivial Integration]

**Options:**

- **Score 5 — Pass**
  The agent demonstrates a "seamless handoff" between modalities. It extracts a specific, non-obvious value from a primary source and uses it as the required search parameter or logic filter for a secondary source, successfully flagging any inconsistencies or dependencies between the two.

- **Score 3 — Non-Fail** (justification required)
  [Non-Fail - Trivial Integration]
  The agent acknowledges both sources but combines them superficially. It may summarize a PDF and describe an image in the same response, but it fails to establish a logical link between them, requiring explicit manual prompting to "connect the dots" that should have been handled autonomously.

- **Score 2 — Fail** (justification required)
  [Fail - Disconnected Processing]
  The agent treats inputs as isolated silos. It fails to extract a necessary value from one modality to use in another (e.g., ignores a date in a blurry HEIC photo when searching a database) or provides a response based on only one source while ignoring conflicting evidence in a second source.

- **Score 2 — Fail** (justification required)
  [Fail - Simple Processing]
  The trajectory has no opportunity to extract a necessary value from one modality to use in another. (This means the prompt and modality is too easy and not a good task)

---

## Trajectory - Architectural Depth & Friction Exposure
**Bucket:** Other
**Question:** Rate the Architectural Depth & Friction Exposure of the Trajectory dimension.
**Description:** This evaluates whether the task itself meaningfully tests agent-building capability and exposes differences across models. The task must require multi-stage coordination, real tool use, cross-step dependencies, and at least one realistic friction point.

// A task requires multi-system coordination when the agent must retrieve, reconcile, or act upon information across two or more distinct systems (apps, data sources, tools, or environments), where outputs from one system meaningfully influence decisions or actions in another system and/or outputs from both systems inform the final result.

// MEMORY.md usage: (UPDATED 03/10)
The prompts in multi-turn tasks have to require the model—explicitly or implicitly—to write details to the MEMORY.md file. (This file is used as “long-term” context for future conversations.) This can be done by:
- Asking the model to write it to memory directly
“Write this down to your memory”,
“Remember this”
- Implicitly needing the model to remember the information somehow to use it later:
“track my progress”,
“make sure you don’t post duplicates”,
“One important thing to know about me is that I have a bad knee”,
“I always prefer taking the subway over a cab”.
**Error categories:** [All] [All] [Fail - Major Depth Issues] | [All] [All] [Non-Fail - Minor Depth Issues]

**Options:**

- **Score 5 — Pass**
  The task clearly forces architectural reasoning.
  Requires modular separation or structured multi-stage planning.
  Includes real friction (e.g., conflicting data, missing fields, paywalls, normalization issues, constraint negotiation).
  Requires state reuse or refactoring.
  Meaningfully differentiates model capability

- **Score 3 — Non-Fail** (justification required)
  [Non-Fail - Minor Depth Issues]
  - Architectural evolution is possible but not clearly required.
  - Tool use is present but not deeply integrated into reasoning.
  - Task meets minimum requirements but lacks strong differentiation power.

- **Score 2 — Fail** (justification required)
  [Fail - Major Depth Issues]
  No meaningful tool dependency.

---

## Tests - Correctness
**Bucket:** Other
**Question:** Only evaluate if the unit tests are present -- otherwise skip this selection. Rate the Correctness of the Tests dimension.
**Description:** Test logic should align with the conversational and environmental context.

(04/09) Overly specific unit tests are also counted as incorrect unit tests. See the spec doc for examples. For all options except the last, apply an error category.
**Error categories:** [All] [All] [Fail - Incorrect Tests] | [All] [All] [Non-Fail - Incorrect Tests]

**Options:**

- **Score 5 — Pass**
  All of the unit tests contain correct logic and are aligned with the task’s context.

- **Score 3 — Other** (justification required)
  At least one of the unit tests (but fewer than 10%) contains incorrect logic or is misaligned with the task’s context.

- **Score 2 — Other** (justification required)
  At least 10% of the unit tests contain incorrect logic or are misaligned with the task’s context.

---

## Tests - Underfitted Tests
**Bucket:** Other
**Question:** Only evaluate if the unit tests are present -- otherwise skip this selection.  Rate the Underfitted Tests of the Tests dimension.
**Description:** Underfitted tests are tests that are too loose, overly broad or lenient. These tests accept all the valid solutions, but also accept some incorrect, invalid or arguably undesirable ones.

// NOTE: Some tests may be wider to account for artifacts which cannot be easily validated, more general prompt requests, or requests which may be fulfilled in multiple ways. In these cases, also consider whether the rubric criteria corresponding to the test in question (e.g., "...include a column for average temperature" -- it would be inappropriate for the test suite to enforce a specific format, unit, or name for this column) when determining if the test is truly underfitted or not (if the criteria + test cover the valid solutions for the request in question, it is not underfitted).
**Error categories:** [All] [All] [Non-Fail - Underfitted Tests] | [All] [All] [Fail - Underfitted Tests]

**Options:**

- **Score 5 — Pass**
  There are no underfitted tests

- **Score 3 — Other** (justification required)
  Up to 30% of the unit tests are underfitted

- **Score 2 — Other** (justification required)
  More than 30% of the unit tests are underfitted

---

## Tests - Coverage
**Bucket:** Other
**Question:** Only evaluate if the unit tests are present -- otherwise skip this selection. Rate the Coverage of the Tests dimension.
**Description:** Tests revolve around generated artifacts and should verify:
- Explicit prompt requests
- Implicit prerequisites for explicit prompt requests
E.g., Instructions say "respond to all my unread emails". The model must explore and discover the unread emails. There should be test cases to check whether emails were sent to all recipients. Some emails may also contain other requirements that should be tested as well.

// NOTE: Do not penalize omissions for things that should not be covered by unit tests (see notes).

// Examples:
- Prompt asks for a file -> check that file exists
- Prompt asks to write to memory -> check that not memory is not empty
- Prompt asks to add/remove/edit entities -> check that they were modified
- Prompt asks for a verifiable artifact (CSV, JSON, etc.) -> check any applicable constraints (see below for more info)

// What should/shouldn’t be covered by unit tests
- Keep in mind that the expected coverage of the unit test suite highly depends on the specific requests of the conversation. If a prompt asks for a CSV while providing a pre-defined (and exact) schema, then several factors should be validated: file existence, schema definition, and content correctness. However, if the prompt requests an artifact that isn’t easily validated—such as a PDF—then it’s sufficient for the unit tests to only include structural checks, e.g., file existence.

// Examples:
- “... create a PDF for my personal calendar”
This file format isn’t easily verifiable/extractable, so the unit tests do not need to include content validation.

- “... include a column for average temperature”
Doesn’t specify the exact column name or units, so schema definition and content correctness should not be considered in the unit tests. (This should instead be covered by the rubric, which inherently has more “wiggle room” in response evaluation.)

However, there should still be a unit test to validate file existence (and perhaps the total number of columns/rows, depending on the prompt).

- “... include a column called “average temperature (F°)”
Specifies an exact schema and the expected units, so both schema definition and content correctness should be validated by the unit tests.
**Error categories:** [All] [All] [Non-Fail - Test Coverage] | [All] [All] [Fail - Test Coverage] | [All] [All] [Non-Fail - Incorrectly Covered by Rubric]

**Options:**

- **Score 5 — Pass**
  The unit tests cover all of the task’s expected constraints.

- **Score 3 — Non-Fail** (justification required)
  [Non-Fail - Test Coverage]:
  Suboptimal Overall Coverage: 20% or fewer tests are missing (see notes on calculating this proportion and what should/shouldn’t be covered by unit tests)

- **Score 3 — Non-Fail** (justification required)
  [Non-Fail - Incorrectly Covered by Rubric]
  At least one unit test is missing but is instead covered by the rubric. (See notes for what should/shouldn’t be covered by unit tests.)

- **Score 2 — Fail** (justification required)
  [Fail - Test Coverage]:
  Insufficient Overall Coverage: >20% of tests are missing (see notes on calculating this proportion)
  
  // NOTE 05/04: Tests which are covered by the rubric (even if they should be covered by a test) do not count towards this error – see [Non-Fail - Incorrectly Covered by Rubric] instead. Tests should only be counted as missing if they are not covered by a verifier at all.

---

## Tests - Redundancy
**Bucket:** Other
**Question:** Only evaluate if the unit tests are present -- otherwise skip this selection. Rate the Redundancy of the Tests dimension.
**Description:** Evaluates the structural efficiency of the task’s grading logic. It identifies overlaps where a rubric is redundant because a Unit Test (Pytest) is already covering the same ground. High-quality tasks use Pytests for deterministic, binary checks (file existence, exact string matches, file formats) and reserve Rubrics for nuanced, qualitative analysis (reasoning quality, visual interpretation).

Redundancy could be:
Two unit tests check the same thing
One unit test and one criterion check the same thing. See the spec doc for examples.
**Error categories:** [All] [All] [Fail - Highly redundant tests] | [All] [All] [Non-Fail - Some redundant tests]

**Options:**

- **Score 5 — Pass**
  Tests and criteria are consolidated and non-redundant. Efficient coverage of requirements.

- **Score 3 — Other** (justification required)
  1 pair of tests or rubric criteria check exactly the same behavior with no difference (e.g., three tests all asserting total_cost == 500).
  
  Tests or rubric criteria have some overlap, but no direct 1:1 overlap

- **Score 2 — Other** (justification required)
  More than 1 pair of tests or rubric criteria check exactly the same behavior with no difference (e.g., three tests all asserting total_cost == 500).
  
  NOTE: Tests with identical structure but different inputs/expected values are not considered to have "no difference". (These types of “test consolidation” issues can be penalized with a non-failing category.)

---

## Failed Rubric/Unit Test - Justification
**Bucket:** Other
**Question:** Rate the Justification of the Failed Rubric/Unit Test dimension.
**Description:** For each rubric or unit test that the Claude model failed on, the CB must answer 3 justification questions:
1. Why is your test/rubric correct?
e.g., "Prompt asks for file.json, rubric checks it's present"

"Prompt asks for a calculation -- explain the calculator logic and how the answer was reached."

2. Why is it necessary for a correct answer from the model?
e.g., "Prompt asks for file.json, rubric makes sure it's present";

"Prompt asks for average spend, rubric makes sure it's present."

3. Where did the model make a mistake?
e.g., "Model missed transaction B and didn't include it in the calculations";

"In turn 23, the model did XYZ which was incorrect because XYZ.". See the spec doc for examples. For all options except the last, apply an error category.
**Error categories:** [All] [All] [Non-Fail - Weak Justification] | [All] [All] [Non-Fail - Incorrect Justification]

**Options:**

- **Score 5 — Pass**
  All justification sets defend valid, prompt-requested rubrics and each set provides thorough, specific answers to all 3 questions

- **Score 3 — Other** (justification required)
  1 or more justifications set defends an overly specific or unrequested rubric/test that model A (Claude Opus) failed
  
  Ex: a rubric penalizes the model for something the prompt never asked for, justification incorrectly argues that it’s a valid rubric

- **Score 3 — Other** (justification required)
  All justification sets defend valid, prompt-requested rubrics (none are overly prescriptive or unrequested), but justification sets lack sufficient detail -- e.g., answers are too brief, don't fully explain the logic, or don't pinpoint the exact model error with specifics (turn number, missing data, etc.).

---

## Universe - Universe Viewer Consistency
**Bucket:** Other
**Question:** Does Universe Viewer show data that doesn't match the universe data the agent actually queries?
**Description:** This error is for the universe viewer presenting data that is inconsistent with the "actual" contents of the universe (as present in trajectory evidence/the universe database contents (not viewer)). This typically involves timezone conversion + aggregation logic. Issues have been noticed so far with the following servers: MyFitnessPal, AppleHealth, LogisticsTracking, although others are likely affected. Please include the source of the inconsistency in your feedback.
**Error categories:** [All] [All] [Non-Fail - Universe Viewer Inconsistency]

**Options:**

- **Score 5 — Pass**
  The universe viewer is completely consistent with more authoritative sources of universe data (tool call results/universe database).

- **Score 3 — Non-Fail** (justification required)
  [Non-Fail - Universe Viewer Inconsistency]
  1+ facts, values, etc. in the universe explorer are misaligned with actual universe data (as seen in trajectory tool calls and the universe database--not viewer).

---

## Rubric Criteria - Overall Rubric Quality - Major
**Bucket:** Rubric Criteria
**Question:** Rate the Overall Rubric Quality - Major of the Rubric Criteria dimension.
**Description:** Use the number of criteria that the CB wrote as the denominator while calculating % values. See the additional notes section for the numerator. Do NOT double count criteria while tallying even if it has multiple issues.

See Rubric Quality Definitions in the spec appendix for descriptions and categorization (major/moderate/minor) for rubric criteria errors. See the spec doc for examples. For all options except the last, apply an error category.
**Error categories:** [All] [All] [Non-Fail - Up to 10% Major Errors] | [All] [All] [Fail - 10%+ Major Rubric Errors]

**Options:**

- **Score 5 — Pass**
  No Major Issues

- **Score 3 — Other** (justification required)
  Up to 10% (<=10%) of the criteria contain major issues

- **Score 2 — Other** (justification required)
  More than 10% (>10%) of the criteria contain major issues

---

## Rubric Criteria - Overall Rubric Quality - Major/Moderate
**Bucket:** Rubric Criteria
**Question:** Rate the Overall Rubric Quality - Major/Moderate of the Rubric Criteria dimension.
**Description:** Use the number of criteria that the CB wrote as the denominator while calculating % values. See the additional notes section for the numerator. Do NOT double count criteria while tallying even if it has multiple issues.

See Rubric Quality Definitions in the spec appendix for descriptions and categorization (major/moderate/minor) for rubric criteria errors. See the spec doc for examples. For all options except the last, apply an error category.
**Error categories:** [All] [All] [Non-Fail - Up to 15% Moderate Errors] | [All] [All] [Fail - 15%+ Moderate Rubric Errors]

**Options:**

- **Score 5 — Pass**
  No major or moderate issues

- **Score 3 — Other** (justification required)
  Up to 15% (<=15%) of criteria contain moderate or major issues (with major issues contributing lower than 5%)

- **Score 2 — Other** (justification required)
  More than 15% (>15%) of the criteria contain moderate or major issues

---

## Rubric Criteria - Overall Rubric Quality - Major/Moderate/Minor
**Bucket:** Rubric Criteria
**Question:** Rate the Overall Rubric Quality - Major/Moderate/Minor of the Rubric Criteria dimension.
**Description:** Use the number of criteria that the CB wrote as the denominator while calculating % values. See the additional notes section for the numerator. Do NOT double count criteria while tallying even if it has multiple issues.

See Rubric Quality Definitions in the spec appendix for descriptions and categorization (major/moderate/minor) for rubric criteria errors. See the spec doc for examples. For all options except the last, apply an error category.
**Error categories:** [All] [All] [Non-Fail - 5-20% Minor Errors] | [All] [All] [Fail - 20%+ Minor Rubric Errors]

**Options:**

- **Score 5 — Pass**
  Less than 5% (<5%) of the rubrics have minor issues
  No major or moderate issues

- **Score 3 — Other** (justification required)
  Between 5 and 20% (>=5% and <=20%) of criteria contain minor or moderate or major issues (with major issues contributing lower than 5% and moderate issues contributing lower than 15%)

- **Score 2 — Other** (justification required)
  More than 20% (>20%) of the criteria contain minor or moderate or major issues

---

## Rubric Criteria - Rubric Structure
**Bucket:** Rubric Criteria
**Question:** Rate the Rubric Structure
 of the Rubric Criteria dimension.
**Description:** These errors reflect structural problems within the rubric and are failing if present. Weights should be added according to the difficulty of the thing the verifier is testing, not its importance to responding to the prompt. See the spec doc for examples.
**Error categories:** [All] [All] [Fail - Invalid Weights]

**Options:**

- **Score 5 — Pass**
  All rubric criteria have weights within the set {-5, -3, -1, +1, +3, +5}

- **Score 2 — Other** (justification required)
  One or more criteria use weights outside of the allowed set {-5, -3, -1, +1, +3, +5}.

---

## Rubric Criteria - Rubric Spot Checks
**Bucket:** Rubric Criteria
**Question:** Rate the Rubric Spot Checks of the Rubric Criteria dimension.
**Description:** CBs are expected to provide up to 5 spot checks if there are sufficiently similar outcomes as well as add a criterion to check the volume of the outcomes.
If there are more than 5 spot checks, use the [Non-Fail - Too Many Spot Checks] category. See the spec doc for examples. For all options except the last, apply the error category.
**Error categories:** [All] [All] [Non-Fail - Too Many Spot Checks]

**Options:**

- **Score 5 — Pass**
  Every group of outcomes has up to 5 spot checks

- **Score 3 — Other** (justification required)
  There are more than 5 spot checks for any group of outcomes.