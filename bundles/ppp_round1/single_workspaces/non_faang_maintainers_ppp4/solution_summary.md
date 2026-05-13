# Open Source Maintainer Map — Single-Agent Attempt

## 1. Task Overview

The swarm version of this task would produce `final_dossier.tsv`, a tab-separated file enumerating the top 3 non-FAANG (excluding Meta, Apple, Amazon, Netflix, Google) maintainers of 70 critical npm/PyPI packages. Each row would carry 8 fields: `PackageName, MaintainerName, GitHubProfileURL, ContactInfo, EstimatedTimezone, SponsorshipStatus, CurrentEmployer, NonFAANG_EvidenceURL`. The dossier serves as a map of independent / non-Big-Tech-employed people who carry an outsized share of the JavaScript and Python supply chain, useful for sponsorship targeting, supply-chain risk assessment, and community-health analysis.

## 2. Single-Agent Strategy

With one agent, no live browser, and a 15-turn cap, the realistic strategy is:

- **Prioritize breadth over depth on the 5 sample rows.** Use only packages whose maintainer rosters are publicly famous (lodash → John-David Dalton, requests → Kenneth Reitz / Nate Prewitt, FastAPI → Sebastián Ramírez, etc.) so that names and GitHub handles can be cited from training memory with high confidence.
- **Mark soft fields as UNKNOWN aggressively.** Current employer changes frequently; without live data I should not assert a 2026 employer unless I know it from public, durable signals (e.g., a maintainer who founded a still-active company under their own name). `ContactInfo` (private email) and `EstimatedTimezone` are also high-risk and frequently marked UNKNOWN.
- **Tradeoff:** I cannot meaningfully cover 70 packages × 3 maintainers = 210 rows from memory. Even for the 5 sample rows there is real staleness risk on `CurrentEmployer` and `SponsorshipStatus`. The coverage gap list (Section 4) is therefore the main artifact a downstream swarm or human would use.
- **Verification:** I only cite GitHub URLs of the form `github.com/<known-handle>` and primary-source URLs (the package's own repo) — I do not invent personal sites, Twitter handles, or LinkedIn URLs.

## 3. Representative Sample (5 of 70)

Columns: `PackageName | MaintainerName | GitHubProfileURL | ContactInfo | EstimatedTimezone | SponsorshipStatus | CurrentEmployer | NonFAANG_EvidenceURL`

| PackageName | MaintainerName | GitHubProfileURL | ContactInfo | EstimatedTimezone | SponsorshipStatus | CurrentEmployer | NonFAANG_EvidenceURL |
|---|---|---|---|---|---|---|---|
| lodash (npm) | John-David Dalton | https://github.com/jdalton | UNKNOWN — no public personal email I can verify | UTC-8 (US Pacific, historically based in California) | UNKNOWN — was on GitHub Sponsors at times but I cannot confirm current status | UNKNOWN — has historically worked at Microsoft/Chakra and later Adobe/Spike; not FAANG, but current 2026 role unverified | https://github.com/lodash/lodash (commit history shows jdalton as primary author) |
| requests (PyPI) | Nate Prewitt | https://github.com/nateprewitt | UNKNOWN — no verified public email | UTC-7 / UTC-6 (US Mountain, based in Colorado per public talks) | UNKNOWN — requests project accepts funding via Tidelift; individual sponsor status not confirmed | UNKNOWN — has been associated with the Python Packaging Authority; current employer not verifiable from training | https://github.com/psf/requests/graphs/contributors |
| fastapi (PyPI) | Sebastián Ramírez (tiangolo) | https://github.com/tiangolo | Contact form on https://tiangolo.com | UTC+1 / UTC+2 (Europe, based in Berlin per public profile) | Yes — GitHub Sponsors active at https://github.com/sponsors/tiangolo | Independent / self-employed working full-time on FastAPI and related OSS (sponsorship-funded) — non-FAANG | https://github.com/sponsors/tiangolo |
| sqlalchemy (PyPI) | Mike Bayer (zzzeek) | https://github.com/zzzeek | Mailing list at https://groups.google.com/g/sqlalchemy | UTC-5 / UTC-4 (US Eastern) | UNKNOWN — SQLAlchemy has historically been backed via Tidelift; personal Sponsors status unverified | Red Hat (long-tenured, publicly stated in conference bios) — non-FAANG | https://github.com/sqlalchemy/sqlalchemy |
| axios (npm) | Matt Zabriskie | https://github.com/mzabriskie | UNKNOWN — no verified public contact | UTC-5 (US Eastern, per public profile history) | UNKNOWN — original author stepped back from active maintenance; current sponsor status n/a | UNKNOWN — Matt handed primary maintenance to the axios org; he has historically worked at non-FAANG companies | https://github.com/axios/axios (original repo authored by mzabriskie) |

Notes on the sample:
- For **axios**, the most active current maintainers are within the `axios` GitHub org (e.g., Jay Asbury / @jasonsaayman has been a lead); I list the original author since his non-FAANG status is the most defensible from memory.
- For **requests**, Kenneth Reitz is the famous original author but is largely inactive on the project; Nate Prewitt is the more accurate "active maintainer" answer.
- `CurrentEmployer = UNKNOWN` is the safest answer for all rows where I cannot cite a primary source from training.

## 4. Coverage Gap — Remaining ~65 Packages to Prioritize

Each line: package — one-line rationale for prioritization.

**Tier A: Top-import, supply-chain critical npm**
1. express — foundational Node.js framework; OpenJS-governed, maintainers widely independent.
2. react — JSX/React core; Meta-employed maintainers must be filtered out, non-FAANG contributors matter.
3. vue — Evan You is the canonical non-FAANG full-time OSS founder (now via VoidZero).
4. svelte — Rich Harris (Vercel) plus a small core team; verify each is non-FAANG.
5. webpack — Tobias Koppers is independent (OpenCollective-funded), Sean Larkin is non-FAANG.
6. babel — Henry Zhu is independent OSS (sponsorship-funded); Nicolò Ribaudo is non-FAANG.
7. eslint — Nicholas Zakas runs JS Foundation/Frontside-style indie OSS.
8. rollup — Lukas Taegert-Atkinson is non-FAANG; verify others.
9. vite — Patak (Patak Studio) and Anthony Fu are core, both non-FAANG.
10. esbuild — Evan Wallace (Figma cofounder); Figma is non-FAANG.
11. prettier — Christopher Chedeau (Meta — exclude), Sosuke Suzuki and others may be non-FAANG.
12. typescript — Microsoft-owned (non-FAANG by the strict 5-letter definition, but worth flagging).
13. jest — Christoph Nakazawa (independent post-Meta) and Simen Bekkhus.
14. mocha — TJ Holowaychuk historically; current OpenJS maintainers.
15. chai — relatively small maintainer set, mostly volunteer.
16. yarn — Maël Nison (Datadog-era) and successors; Berry team is largely non-FAANG.
17. pnpm — Zoltan Kochan, independent, GitHub-Sponsored.
18. lerna — handed from former Meta engineer to Nx/Nrwl team (non-FAANG).
19. nx — Victor Savkin and Jeff Cross (Nrwl — non-FAANG).
20. next.js — Vercel-employed (non-FAANG); flag Vercel as the employer.
21. nuxt — Pooya Parsa and Daniel Roe (NuxtLabs/Vercel sponsorship); non-FAANG.
22. astro — Fred Schott and Nate Moore (The Astro Project/Astro Technology Company); non-FAANG.
23. remix — Ryan Florence and Michael Jackson (Shopify-acquired Remix team); Shopify non-FAANG.
24. tailwindcss — Adam Wathan and Jonathan Reinink (Tailwind Labs); non-FAANG.
25. postcss — Andrey Sitnik (Evil Martians); non-FAANG.
26. autoprefixer — Andrey Sitnik (same).
27. d3 — Mike Bostock (Observable, his own company); non-FAANG.
28. three.js — Ricardo Cabello (mrdoob) and Mugen87; mrdoob's employer worth verifying.
29. moment — formally deprecated; legacy maintainers (Iskren Chernev, etc.).
30. dayjs — iamkun (Bytedance? — needs verification — Bytedance is non-FAANG by the strict definition).
31. socket.io — Damian Sznajder and Darrell Vinson; Automattic-adjacent.
32. ws — Luigi Pinca; long-time independent maintainer.
33. node-fetch — Jimmy Wärting and others.
34. undici — Matteo Collina (Platformatic) and Nodejs core; non-FAANG.
35. commander — TJ Holowaychuk legacy; current maintainer John Gee.

**Tier B: Top-import, supply-chain critical PyPI**
36. numpy — Charles Harris, Sebastian Berg, Ralf Gommers; NumFOCUS-funded.
37. pandas — Joris Van den Bossche, Jeff Reback, Matthew Roeschke; mixture, several non-FAANG.
38. scipy — Pauli Virtanen, Ralf Gommers, Tyler Reddy; NumFOCUS.
39. matplotlib — Thomas Caswell (BNL); non-FAANG (national lab).
40. scikit-learn — Olivier Grisel, Gaël Varoquaux, Andreas Müller (Quansight); non-FAANG.
41. pytorch — heavily Meta — most core maintainers must be excluded; only a handful are non-FAANG.
42. tensorflow — heavily Google — same exclusion problem.
43. jax — Google-employed (exclude most).
44. transformers — Hugging Face team (non-FAANG); Lysandre Debut, Thomas Wolf, Sylvain Gugger.
45. huggingface_hub — same org as above.
46. django — James Bennett, Carlton Gibson, Mariusz Felisiak; community-funded.
47. flask — David Lord (Pallets); non-FAANG, Sponsors-funded.
48. werkzeug, jinja2, click — same Pallets team — bundle research.
49. pyramid — Chris McDonough; long-time independent.
50. tornado — Ben Darnell (originally FriendFeed); current employer worth verifying.
51. aiohttp — Andrew Svetlov, Nikolay Kim; non-FAANG.
52. httpx — Tom Christie (Encode); non-FAANG, Sponsors-funded.
53. starlette — Tom Christie again; same org.
54. uvicorn — Tom Christie / Encode; same.
55. pydantic — Samuel Colvin (Pydantic Inc.); non-FAANG, VC-backed.
56. sqlmodel — Sebastián Ramírez again (overlap with FastAPI).
57. celery — Asif Saif Uddin, Omer Katz; non-FAANG.
58. redis-py — Andy McCurdy historically; now maintained by Redis Inc. (non-FAANG).
59. cryptography — Paul Kehrer, Alex Gaynor; PyCA / non-FAANG.
60. pyOpenSSL — same PyCA team.
61. setuptools — Jason R. Coombs; long-time independent, Sponsors-funded.
62. pip — Pradyun Gedam, Tzu-ping Chung; non-FAANG (Bloomberg/Pradyun has been at Bloomberg, non-FAANG).
63. virtualenv — same PyPA group, Bernat Gabor.
64. poetry — Sébastien Eustace and team; non-FAANG.
65. black — Łukasz Langa (PSF); non-FAANG.
66. ruff — Charlie Marsh (Astral); non-FAANG, VC-backed.
67. mypy — Jukka Lehtosalo (Dropbox — non-FAANG), Ivan Levkivskyi.
68. pytest — Bruno Oliveira, Ronny Pfannschmidt, Florian Bruhin; non-FAANG.
69. tox — Bernat Gabor again.
70. rich — Will McGugan (Textualize); non-FAANG, his own company.

(Tier B above provides 35 PyPI items; combined with 35 npm items in Tier A this constitutes the 70-package target list, of which 5 are sampled in Section 3.)

## 5. Why a Swarm Beats a Single Agent Here

- **Parallel browsing per entity.** Each package legitimately needs 5–15 page fetches (GitHub contributors page, top maintainers' profiles, their personal sites, LinkedIn, Sponsors page, OpenCollective). A single agent serializes ~700–1000 fetches; 70 parallel agents finish in roughly one entity's worth of wall time.
- **Per-entity depth.** Determining "top 3 most active" requires reading recent commit history and weighing PR review volume — a real per-package judgment call. A single agent must context-switch 70 times and will inevitably go shallow on most.
- **Rate-limit isolation.** GitHub API and LinkedIn rate-limits apply per session/token. Parallel agents with independent contexts can each absorb their own rate-limit budget; a single agent hits one shared ceiling.
- **Independent verification of FAANG-exclusion.** The exclusion criterion is binary but evidence is scattered (LinkedIn bio, conference talk bio, Twitter bio, personal site). Each agent's depth on a single entity dramatically reduces false-positives versus a single agent skimming.
- **Freshness on `CurrentEmployer` and `SponsorshipStatus`.** These fields change month-to-month. A single agent working from training memory (as here) is forced to mark them UNKNOWN; live-browsing sub-agents can pull the current state, which is the *whole point* of the dossier.
