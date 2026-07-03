# Report: decision CSV (primary) + Markdown (optional)

Both outputs render from **one source**: write `<OUTPUT_DIR>/report_data.json` once, then render the
CSV (and optionally the Markdown) from that same file so they never drift.

**The CSV is the deliverable the team acts on** — one row per task, sized for a Google Sheet where
you sort by `confidence` and decide what ships, what to quick-audit, and what to fix. The Markdown
report is an optional batch-level summary for eyeballing quality issues across a batch (renders
inline in any Markdown viewer — no browser needed).

## Payload

`report_data.json` schema is documented in the docstring of `render_report_md.py`. Key fields:
`title`, `subtitle`, `methodology`, the two tier-split theme sections `action_required_summary[]`
and `review_recommended_summary[]`, and `tasks[]` with `task_name`, optional `has_tests`,
`flagged_rubrics` (`{action_required, review_recommended}` unique-rubric counts), `findings[]` (each
with a `tier`), plus the **decision fields** the CSV consumes (all optional — derived from
`findings` when absent):

- `verdict` — `pass` | `non-fail` | `fail` (fail = any action-required survives; non-fail = only
  review-recommended; pass = none). **Both `fail` and `non-fail` are meant to be human-validated;
  only `pass` is deliver-blindly.**
- `confidence` — 0–100, how confident the task is **deliverable/clean** (the triage sort key).
- `summary` — one-line headline of the worst issue for at-a-glance scanning.
- `flagged_dimensions` — eval-guide dimensions implicated.
- `audit_md` — a terse per-task markdown summary for quick human validation.
- `carryover` — passthrough columns echoed from the input CSV (e.g. `attempt_id`, `review_level`);
  ignored by the eval, emitted verbatim in the output CSV.

This is a **static** QA — there are no reward/pass@K columns. The static dimension scores are **not**
rendered into the Markdown (dropped for the shared report).

## Render

Both renderers are stdlib-only and ship with this skill. **Always produce the CSV**; the Markdown is
optional:

```bash
# CSV — the primary decision output (one row per task). --inputs-dir merges the carryover columns.
python3 <skill_dir>/render_report_csv.py --data <OUTPUT_DIR>/report_data.json \
    --inputs-dir <OUTPUT_DIR> --output /tmp/<eval>_qa_<YYYY_MM_DD>.csv
# Markdown — optional batch-level summary view
python3 <skill_dir>/render_report_md.py  --data <OUTPUT_DIR>/report_data.json --output /tmp/<eval>_qa_<YYYY_MM_DD>.md
```

## Decision CSV columns

`task_name` · `<carryover…>` (e.g. `attempt_id`, `review_level`) · `verdict` · `needs_validation`
(yes for `fail` **and** `non-fail`) · `confidence` · `summary` (one-line headline) ·
`action_required` · `review_recommended` · `flagged_dimensions` · `flags` · `audit_md`. Rows are
sorted worst-first (`fail` → `non-fail` → `pass`, then lowest confidence first) so the tasks needing
attention are at the top. Suggested workflow: **`pass` → deliver blindly**; **`non-fail` and `fail`
(filter `needs_validation = yes`) → skim `summary`/`audit_md` and agree or disagree, fixing what's
real.**

The Markdown report is the batch-level companion: tier-split theme callouts (defects clustered by
type), a per-task summary table, and findings-by-task — good for a quick read of a batch's overall
quality.

## Report IA (default — 2 tabs)

Strip internal IDs and cut UI aggressively to reduce the reader's cognitive load.

1. **Summary** — two tier-split theme callouts at the top (below), then a methodology blurb, then
   one row per task: `task_name` · flagged-rubrics chip · defect count. Sort most-urgent first:
   `(-action_required, -review_recommended, task_name)` — never alphabetical. The `task_name` is the
   click target into the findings tab.
2. **Findings by task** — collapsible card per task (the single findings view), each card headed by
   a findings-count chip; body lists that task's confirmed findings with tier + defect-type chips,
   rubric/test IDs, and a suggested fix each.

**Flagged-rubrics chip** = count of **unique** flagged rubric IDs per tier (dedupe across findings,
each rubric takes its most urgent tier — `action_required` over `review_recommended`), rendered with
the FULL tier names, e.g. `2 action required · 5 review recommended`. Not a raw findings count.

**Tier-split theme sections** (top of Summary — a red `action required` callout and an amber
`review recommended` callout) — cluster the confirmed findings of each tier by `defect_type` into
concise one-line descriptions (a bold human label + one sentence of what the category is + a
`<em>(N findings · M tasks)</em>` count pointer). One bullet per `defect_type` present in that tier,
ordered by finding count. (Each `*_summary` item may optionally carry an `example_task` that the
renderers turn into a link into that task's findings.)

**Methodology blurb** — one paragraph: what ran (a static review of each task's files — prompt,
rubrics, tests, inputs, environment — with **no model rollouts or pass@K**), that **a single neutral
verifier — shown only the claims, with no prior verdict or tier to anchor on — re-derived each
finding from primary evidence and kept only the corroborated ones** (report "N confirmed, M
removed"), and the chip semantics. **Always end with the mandatory caveat:** *"Some flagged rubrics
may be false positives — reviewers are LLMs and can misread intent. Please skim findings rather than
treat them as ground truth."*

## Hygiene check (must be all-zero before sharing)

Before sending the report anywhere, confirm no internal identifiers, raw filesystem paths,
usernames, customer/PII strings, or rubric answer-key text leaked in. Fill the list with whatever is
sensitive in your environment:

```bash
python3 -c "
c=open('<file>').read()
for n in ['<internal_job_name>','<dataset_slug>','<internal_mount_path>','<username>','<customer_id>','why_rubric_is_correct']:
    print(n, c.count(n))
"
```
Run on **both** outputs — the `.csv` (primary) and the `.md`. Every count must be 0. The CSV's
`summary` / `audit_md` cells in particular can echo answer-key text or paths.

## Deliver

Share the `.csv` (the decision artifact) and, if useful, the `.md` batch summary via whatever
channel you use to hand off the QA results. Keep them in sync by always re-rendering from
`report_data.json`.
