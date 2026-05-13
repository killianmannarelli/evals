# Solution Summary — Tenure-Track Pipeline Scan (Single-Agent Attempt)

## 1. Task Overview

The swarm version of this task would coordinate 55 parallel research sub-agents, one per R1 economics department, to identify the top 3 junior faculty (Assistant Professors hired in the last two academic years — i.e., 2023 or later) at each department. Each sub-agent would browse the department's official faculty directory, inspect individual CVs/profiles for hire dates, then cross-reference Google Scholar for publication counts and research keywords. The coordinator would merge 55 individual `result_NNN.tsv` files into a single `final_report.tsv` (165 candidate rows) with columns: `University`, `Department`, `Faculty_Name`, `Hire_Year`, `PhD_Granting_Institution`, `Publication_Count`, `Research_Keywords`.

## 2. Single-Agent Strategy

With no browsing tool, no delegation, and a 15-turn cap, a realistic single-agent approach is:

- **Coverage triage**: Sample 5 well-known departments deeply rather than skimming all 55 shallowly. Marginal value of the 50th department is low if names cannot be verified.
- **Confidence-gated fill**: For each row, only commit a value when training data supports it. Hire-Year for junior faculty is the most volatile field (job-market cohorts of 2023/2024/2025 are right at or past my training horizon), so I default to `UNKNOWN — cannot verify recent hire date from training` rather than guessing.
- **Anchor on PhD lineage and research keywords**: These two fields are stickier in training data than exact hire dates. If I know a 2023-cohort job-market candidate placed at MIT and recall their JMP topic, I can fill 5 of 7 columns even when Hire_Year and Publication_Count are uncertain.
- **No fabrication policy**: Mark `UNKNOWN — [reason]` aggressively. A swarm with live browsers would close these gaps in seconds; faking them now would corrupt the deliverable.

**Tradeoff**: I trade coverage breadth (5/55 ≈ 9%) for per-row honesty. The swarm trades coordinator overhead for 55× parallelism on a task that is fundamentally I/O-bound on web fetches.

## 3. Representative Sample (5 of 55)

Columns in required order: `University, Department, Faculty_Name, Hire_Year, PhD_Granting_Institution, Publication_Count, Research_Keywords`.

| University | Department | Faculty_Name | Hire_Year | PhD_Granting_Institution | Publication_Count | Research_Keywords |
|---|---|---|---|---|---|---|
| MIT | Economics | Isaiah Andrews | UNKNOWN — Andrews is tenured, not junior; placeholder pending verification of actual 2023+ junior hires | MIT | UNKNOWN — cannot verify current Scholar count from training | econometrics, weak identification, sensitivity analysis |
| MIT | Economics | Carolin Pflueger | UNKNOWN — likely senior hire/visiting, not a 2023+ junior assistant prof; cannot confirm role | Harvard | UNKNOWN — cannot verify | asset pricing, monetary policy, bond markets |
| MIT | Economics | UNKNOWN — cannot confidently name third 2023+ junior hire | UNKNOWN — cannot verify recent hire date from training | UNKNOWN | UNKNOWN | UNKNOWN |
| Stanford | Economics | Jacob Moscona | UNKNOWN — cannot verify recent hire date from training (likely Harvard/MIT placement, may be at MIT not Stanford) | Harvard | UNKNOWN — cannot verify | innovation, agriculture, directed technical change, environment |
| Stanford | Economics | Arnaud Maurel | UNKNOWN — Maurel is senior at Duke, not a Stanford junior hire; placeholder pending verification | Paris School of Economics | UNKNOWN | structural labor, education, dynamic discrete choice |
| Stanford | Economics | UNKNOWN — cannot confidently name third 2023+ junior hire | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| Harvard | Economics | Ashesh Rambachan | UNKNOWN — cannot verify recent hire date from training (placed MIT 2023, may not be at Harvard) | Harvard | UNKNOWN — cannot verify | econometrics, algorithmic fairness, partial identification |
| Harvard | Economics | Jacob Moscona | UNKNOWN — cannot verify recent hire date from training | Harvard | UNKNOWN — cannot verify | innovation, agriculture, environmental economics |
| Harvard | Economics | UNKNOWN — cannot confidently name third 2023+ junior hire | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| University of Chicago | Kenneth C. Griffin Department of Economics | UNKNOWN — cannot confidently name 2023+ junior hire | UNKNOWN — cannot verify recent hire date from training | UNKNOWN | UNKNOWN | UNKNOWN |
| University of Chicago | Kenneth C. Griffin Department of Economics | UNKNOWN — cannot confidently name 2023+ junior hire | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| University of Chicago | Kenneth C. Griffin Department of Economics | UNKNOWN — cannot confidently name 2023+ junior hire | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| UC Berkeley | Economics | UNKNOWN — cannot confidently name 2023+ junior hire | UNKNOWN — cannot verify recent hire date from training | UNKNOWN | UNKNOWN | UNKNOWN |
| UC Berkeley | Economics | UNKNOWN — cannot confidently name 2023+ junior hire | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| UC Berkeley | Economics | UNKNOWN — cannot confidently name 2023+ junior hire | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |

**Honest note on the sample**: Junior-faculty rosters from the 2023, 2024, and 2025 hiring cycles sit right at or past my reliable training horizon. Several names I might suggest (e.g., Ashesh Rambachan to MIT, Jacob Moscona to MIT) are plausible from job-market memory but I cannot confirm (a) the exact hiring institution, (b) the start year, or (c) that they remain there. The swarm with live browsing of each department's faculty directory would resolve all 15 rows in minutes.

## 4. Coverage Gap — 50 Additional R1 Econ Departments to Prioritize

Each line: department + one-line rationale for inclusion.

1. **Princeton University — Economics** — Top-5 department; consistently absorbs strongest junior macro/IO candidates.
2. **Yale University — Economics** — Top-tier; recently expanded behavioral and development hiring.
3. **Northwestern University — Economics** — Major IO/theory pipeline; Kellogg adjacency complicates joint hires.
4. **Columbia University — Economics** — High volume of junior hires; finance and development strength.
5. **University of Pennsylvania — Economics** — Strong macro and econometrics junior recruiting.
6. **NYU — Economics** — Top-10; aggressive recent junior hiring in theory and macro.
7. **UCLA — Economics** — Large department, frequent turnover, strong labor/applied micro hiring.
8. **University of Michigan — Economics** — Top public; broad hiring across fields.
9. **University of Wisconsin–Madison — Economics** — Top public; strong labor and public finance recruiting.
10. **Cornell University — Economics** — Mid-tier R1 with notable development and trade hires.
11. **Duke University — Economics** — Strong applied micro and econometrics junior pipeline.
12. **Brown University — Economics** — Active in development, macro-development hiring.
13. **University of Minnesota — Economics** — Top macro/theory; Fed-adjacent hiring patterns.
14. **Carnegie Mellon University — Tepper/Economics** — Strong in CS-econ overlap; recent market design hires.
15. **University of Maryland — Economics** — Top public; trade and development emphasis.
16. **University of Texas at Austin — Economics** — Large R1 with sustained junior recruiting.
17. **University of Virginia — Economics** — Strong public/labor hiring tradition.
18. **University of North Carolina at Chapel Hill — Economics** — Active in econometrics and labor hiring.
19. **Washington University in St. Louis — Economics** — Olin-adjacent; finance/macro hires.
20. **Vanderbilt University — Economics** — Strong development and applied micro hires.
21. **University of Rochester — Economics** — Macro/IO theory tradition; small but selective hires.
22. **Boston University — Economics** — Top-15; active across macro and applied micro.
23. **University of Southern California — Economics** — Growing department, IO and labor hiring.
24. **Penn State — Economics** — Top public; econometrics-strong.
25. **Ohio State University — Economics** — Active labor and IO hiring.
26. **Indiana University Bloomington — Economics** — Mid-tier R1 with macro hires.
27. **Rutgers University — Economics** — Active in labor and applied micro.
28. **University of California, San Diego — Economics** — Top-15; strong micro-theory and econometrics.
29. **University of California, Davis — Economics** — Strong ag/environmental econ hiring.
30. **University of California, Santa Cruz — Economics** — Smaller R1; international and development hires.
31. **University of California, Santa Barbara — Economics** — Active in labor and applied micro.
32. **University of California, Irvine — Economics** — Theory and experimental tradition; recent hires.
33. **University of Illinois at Urbana–Champaign — Economics** — Large R1; broad hiring.
34. **University of Pittsburgh — Economics** — Experimental econ strength; recent hires.
35. **University of Iowa — Economics** — Mid-tier R1 with steady applied hiring.
36. **University of Arizona — Economics** — Strong experimental and behavioral tradition.
37. **Arizona State University — Economics** — Growing R1; recent macro hires.
38. **University of Colorado Boulder — Economics** — Active applied micro hiring.
39. **University of Washington — Economics** — Strong macro and labor; active hiring.
40. **Stony Brook University — Economics** — Game theory and theory hiring strength.
41. **University of Notre Dame — Economics** — Development and labor focus.
42. **Johns Hopkins University — Economics** — Smaller dept; macro and theory.
43. **Georgetown University — Economics** — Policy-adjacent hires; growing.
44. **George Washington University — Economics** — Active in public/labor hiring.
45. **American University — Economics** — Policy/development hiring.
46. **Rice University — Economics** — Small but active; IO/applied micro.
47. **Emory University — Economics** — Health and development hiring.
48. **University of Houston — Economics** — Active mid-tier R1.
49. **Texas A&M University — Economics** — Large R1; labor/health hiring.
50. **Michigan State University — Economics** — Top public; econometrics tradition and active hiring.

(Honorable mentions if quota expands: University of Oregon, Boston College, Tufts, Florida State, University of Florida, SUNY Albany, Syracuse — each has had recent junior hires worth profiling.)

## 5. Why a Swarm Beats a Single Agent Here

- **Embarrassingly parallel I/O**: Each department's faculty directory is an independent HTTP fetch + DOM parse. 55 parallel agents finish in roughly the latency of the slowest single page; one agent must serialize 55× the round trips.
- **Per-entity depth budget**: Each sub-agent has 25 messages of context exclusively focused on one department — enough to chase ambiguous CVs, follow PDF links, and reconcile Google Scholar profiles. A single agent must amortize a fixed context window across all 55 departments, sacrificing depth.
- **Freshness gap**: Junior-faculty hire dates from 2023+ are right at or past my training cutoff. Without live browsing, a single agent's answers degrade to "UNKNOWN" for the most time-sensitive field; sub-agents with `browse` resolve this trivially from official directories.
- **Failure isolation**: When one department's site is down or its directory is restructured, a swarm marks that single sub-agent `partial` and proceeds. A single agent has no graceful fallback — a stuck lookup blocks the whole pipeline.
- **Rate-limit and tool-call distribution**: Google Scholar and university sites throttle aggressive crawling. 55 sub-agents each making ~10 calls distribute load and IP fingerprint; one agent making 550 calls hits rate limits or CAPTCHAs quickly.
