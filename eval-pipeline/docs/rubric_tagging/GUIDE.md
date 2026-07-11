# Rubric Tagging Guide — for Scale

## Rubric tagger (accuracy / exist / formatting / process / safety)

Classifies each eval rubric criterion into one of five buckets — by the primary
thing that must be true for the criterion to pass. Useful for curating rubrics:
seeing how reward is distributed across content-correctness vs. structure vs.
presentation.

Each criterion gets exactly ONE dominant tag:

- **accuracy** — passing requires the substantive CONTENT to be CORRECT: a
  specific value/date/name/fact/classification/computation, a correct
  cross-reference, a required SPECIFIC entity (event *for Dr. Okonkwo*,
  reference to a *specific* file), or the absence of a hallucinated/ungrounded
  claim. Plain structure/format does not count.
- **exist** — the deliverable merely CONTAINS the required artifact / section /
  field / column / row (or a count), content-agnostic.
- **formatting** — purely how the output is PRESENTED: casing/greeting, ORDER of
  sections/columns, file-format type, valid-PNG/PDF, tone/register,
  brevity/length, number/date styling. NOT mere presence of required fields.
- **process** — how the agent WORKED: tools/skills invoked, queries/steps,
  scoping, conduct.
- **safety** — a HARM/BOUNDARY guardrail (usually negative points). Negative
  points alone do NOT mean safety — penalizing incorrect/fabricated content is
  accuracy.

## Input format

The tagger reads **one JSON file per task** from a local store directory
(default `./tagger_store/tagger_tasks/<task>.json`). You produce these from your
own rubric files — there is no dependency on any external system. Each file:

```json
{
  "task": "<task name (matches the filename stem)>",
  "source": "<optional free-text provenance>",
  "goal": "<one short paragraph: what the agent was asked to do>",
  "criteria": [
    { "n": 1, "points": 3,  "text": "writes the value 64 in the expected column", "source_type": "task_completion" },
    { "n": 2, "points": -3, "text": "reveals a private salary figure",            "source_type": "safety" }
  ]
}
```

Field notes:

- `criteria[].n` — a stable integer id per criterion (used to join results back).
- `criteria[].points` — signed weight; magnitude is not otherwise interpreted by
  the tagger.
- `criteria[].text` — the criterion text the tagger classifies.
- `criteria[].source_type` — OPTIONAL pre-existing label from your own pipeline;
  treated only as a weak hint. The tagger judges from `text` + `goal`.
- `goal` — the agent's task, used only for disambiguation.

The `formatting_recheck_workflow.js` reads a slightly different shape from
`./tagger_store/formatting_recheck/<chunk>.json`: a flat JSON list of
`{id, task, n, points, text, goal}` items.

> The `.js` workflows are written for an agentic-workflow runner (a harness that
> exposes `agent(prompt, {schema, model, ...})`, `pipeline(items, ...stages)`,
> `log(...)`, and an `args` input, and runs each phase as an LLM call with a JSON
> schema). You will likely need to adapt that runner harness to your own
> environment. The substance you are receiving is the **prompts, taxonomy, and
> schemas** — those transfer directly regardless of harness.

## Pipeline

Runs against a local store directory (default `./tagger_store/`). Re-tag only
when tasks/rubrics change (tags are a property of the criteria, not the model).
**Delta-tagging**: pass only NEW task names as the workflow `args` and re-merge;
prior tags for unchanged tasks are reused.

1. **Build inputs** — produce one `./tagger_store/tagger_tasks/<task>.json` per
   task from your own rubric files, in the shape shown under "Input format"
   above.
2. **Run the workflow** (via your workflow runner; phases Tag→Review):
   ```
   run(rubric_tagger_workflow.js, args: [<task names>])
   ```
   Returns `[{task, tagger, review}]`. Save to a JSON file for your own
   downstream use.

## `formatting_recheck_workflow.js`

Targeted refinement pass re-tagging only `formatting`-labeled criteria under the
sharpened exist/formatting rule.

## Notes

- Data artifacts (per-task inputs, classification) live in the store directory,
  not alongside the code — they are large and regenerable.
- Illustrative result shape (one run over ~90 tasks / ~1970 criteria):
  accuracy dominates positive points (~81%), with the remainder split across
  exist / formatting / process / safety, at high tagger↔reviewer agreement
  (~98%). Your numbers will differ — treat these as a sanity check on
  the pipeline, not as targets.
