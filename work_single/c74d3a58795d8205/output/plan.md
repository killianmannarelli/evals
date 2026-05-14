# GDPR vs 50 US State Privacy Laws — Master Plan

## Overview

This plan coordinates the production of a comprehensive comparative analysis of privacy
legislation: the European Union's **General Data Protection Regulation (GDPR)** and the
privacy statutes in effect (or enacted but not yet effective) across **all 50 United
States**. The end product is a 220-page compliance guide (`final_guide.md`) plus a
side-by-side comparison matrix (`compliance_matrix.tsv`).

The guide is intended for:

* In-house counsel and compliance officers building multi-jurisdiction privacy programs
* Privacy professionals seeking a single reference for definitional and rights-based
  variance across US states and the EU
* Academic and policy researchers comparing the federal-style EU regime with the
  state-by-state US patchwork

Each jurisdiction is treated as a self-contained chapter authored against a uniform
schema, so that the resulting compliance matrix can be programmatically populated by
extracting fields from each chapter.

## Assignment Table

1.  GDPR (General Data Protection Regulation) — result file: result_001.md
2.  Alabama — result file: result_002.md
3.  Alaska — result file: result_003.md
4.  Arizona — result file: result_004.md
5.  Arkansas — result file: result_005.md
6.  California (CCPA/CPRA) — result file: result_006.md
7.  Colorado (CPA) — result file: result_007.md
8.  Connecticut (CTDPA) — result file: result_008.md
9.  Delaware (DPDPA) — result file: result_009.md
10. Florida (FDBR) — result file: result_010.md
11. Georgia — result file: result_011.md
12. Hawaii — result file: result_012.md
13. Idaho — result file: result_013.md
14. Illinois (BIPA + general) — result file: result_014.md
15. Indiana (ICDPA) — result file: result_015.md
16. Iowa (ICDPA) — result file: result_016.md
17. Kansas — result file: result_017.md
18. Kentucky (KCDPA) — result file: result_018.md
19. Louisiana — result file: result_019.md
20. Maine — result file: result_020.md
21. Maryland (MODPA) — result file: result_021.md
22. Massachusetts — result file: result_022.md
23. Michigan — result file: result_023.md
24. Minnesota (MCDPA) — result file: result_024.md
25. Mississippi — result file: result_025.md
26. Missouri — result file: result_026.md
27. Montana (MCDPA) — result file: result_027.md
28. Nebraska (NDPA) — result file: result_028.md
29. Nevada (SB 220) — result file: result_029.md
30. New Hampshire (NHPA) — result file: result_030.md
31. New Jersey (NJDPA) — result file: result_031.md
32. New Mexico — result file: result_032.md
33. New York (SHIELD) — result file: result_033.md
34. North Carolina — result file: result_034.md
35. North Dakota — result file: result_035.md
36. Ohio — result file: result_036.md
37. Oklahoma — result file: result_037.md
38. Oregon (OCPA) — result file: result_038.md
39. Pennsylvania — result file: result_039.md
40. Rhode Island (RIDTPPA) — result file: result_040.md
41. South Carolina — result file: result_041.md
42. South Dakota — result file: result_042.md
43. Tennessee (TIPA) — result file: result_043.md
44. Texas (TDPSA) — result file: result_044.md
45. Utah (UCPA) — result file: result_045.md
46. Vermont — result file: result_046.md
47. Virginia (VCDPA) — result file: result_047.md
48. Washington (My Health My Data) — result file: result_048.md
49. West Virginia — result file: result_049.md
50. Wisconsin — result file: result_050.md
51. Wyoming — result file: result_051.md

## Output Schema (Chapter Template)

Every result file MUST begin with a status line and adhere strictly to the structure
below. Status line examples:

```
STATUS: complete
STATUS: partial — Penalties section missing because no enforcement statute is enacted.
```

After the status line, each chapter has the following H1/H2 layout:

```markdown
# [Jurisdiction Name] — [Short Statute Name]

> One-paragraph orientation: scope, in-force date, citation.

## Core Definitions

* **Personal Data** — ...
* **Consumer / Data Subject** — ...
* **Processing** — ...
* **Sale** — ...
* **Controller / Processor (or Business / Service Provider)** — ...

## Consumer Rights

* **Right to Access** — ...
* **Right to Deletion** — ...
* **Right to Correction** — ...
* **Right to Opt-Out of Sale / Sharing** — ...
* **Right to Portability** — ...
* (Additional rights such as opt-out of profiling or appeal, where applicable.)

## Penalties & Enforcement

* Statutory civil penalty per violation
* Cure period (if any)
* Primary enforcement authority (Attorney General, dedicated agency, private right of
  action)
* Statute of limitations and other procedural features

## Notable Enforcement Actions

* 1–2 case summaries (settlement amount, allegations, year). Where no enforcement
  has yet occurred, state this explicitly and reference the most analogous action.
```

## Quality Criteria

* **complete** — All four H2 sections are filled with substantive, sourced
  information. Where a jurisdiction has no comprehensive privacy law, the chapter must
  still describe the sectoral/consumer-protection regime that fills the gap (e.g.,
  breach-notification statutes, attorney-general guidance under UDAP doctrine) so that
  the four sections are non-empty.
* **partial** — A section is missing, contains only placeholder text, or summarises in
  one sentence what the schema requires several sentences to describe.

## Source Tier Guidance

1. Primary statutes (state code or EU Official Journal)
2. Attorney General / Data Protection Authority guidance
3. IAPP resource center, NAAG, Future of Privacy Forum trackers
4. Reputable legal-tech publications (Wilson Sonsini, Hunton Andrews Kurth, Davis
   Wright Tremaine, etc.) for case summaries
