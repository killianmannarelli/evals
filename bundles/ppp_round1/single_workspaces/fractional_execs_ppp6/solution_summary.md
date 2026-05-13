# Fractional Exec Marketplace — Single-Agent Solution Summary

## 1. Task Overview

The swarm version of this task would produce a `final.tsv` file mapping the top 3 fractional/interim leaders across **60 functional executive roles** (Fractional CFO, Fractional CMO, Fractional CTO, Chief of Staff, RevOps Leader, Head of People, Fractional GC, etc.). Each row would represent a single leader, with columns: `Role, LeaderName, HourlyRate, TechStack, ClientLogos, CaseStudyURL, SourceURL`. The final artifact is intended to be importable into Airtable or a spreadsheet as a sourcing/marketplace dataset, with each row corroborated by a public case study URL.

## 2. Single-Agent Strategy (honest tradeoffs)

With no sub-agents and no live browser, a realistic single-agent approach is:

- **Cover breadth, not depth.** Enumerate the 60 roles confidently from training knowledge (executive function taxonomy is stable). Provide a representative sample of 5 roles with as much schema data as I can responsibly recall.
- **Refuse to invent names paired with rates.** Specific HourlyRate figures, case-study URLs, and ClientLogos lists are exactly the kind of facts that drift, churn, or get fabricated under pressure. I will mark these `UNKNOWN — requires live browsing` rather than risk hallucination.
- **Use category-level knowledge for TechStack.** Tooling commonly used inside each functional discipline (e.g., RevOps → Salesforce/HubSpot/Outreach/Gong) is stable and safe to assert generically, not per-person.
- **Defer the long tail.** Document the remaining 55 roles as a prioritized backlog with one-line rationale, so a downstream human or swarm can pick up cleanly.

Tradeoff: the deliverable becomes a *scaffold + integrity flags* rather than a populated marketplace. That is the correct tradeoff under hard turn caps and a no-browser constraint.

## 3. Representative Sample (5 of 60)

Schema column order: `Role | LeaderName | HourlyRate | TechStack | ClientLogos | CaseStudyURL | SourceURL`

| Role | LeaderName | HourlyRate | TechStack | ClientLogos | CaseStudyURL | SourceURL |
|---|---|---|---|---|---|---|
| Fractional CFO | UNKNOWN — specific named leaders cannot be paired confidently with case studies without live verification (Paro, Preferred CFO, NOW CFO, Burkland are well-known firms but per-person attribution risks fabrication) | UNKNOWN — requires live browsing (typical band $200–$500/hr per Paro/Toptal directories, but per-leader rates not memorizable) | NetSuite, QuickBooks Online, Xero, Sage Intacct, Bill.com, Ramp, Brex, Mosaic, Pigment, Anaplan, Carta, Stripe, Excel/Google Sheets | UNKNOWN — requires live browsing | UNKNOWN — requires live browsing | https://www.toptal.com/finance/cfos and https://burklandassociates.com (firm-level only; per-leader URLs not memorizable) |
| Fractional CMO | UNKNOWN — Chief Outsiders, Authentic Brand, and CMOx host rosters but I will not invent a specific name+study pairing | UNKNOWN — requires live browsing (commonly $250–$600/hr) | HubSpot, Marketo, Salesforce Marketing Cloud, Pardot, Iterable, Braze, Customer.io, Segment, GA4, Mixpanel, Amplitude, Looker, Webflow, Contentful, Figma | UNKNOWN — requires live browsing | UNKNOWN — requires live browsing | https://chiefoutsiders.com and https://cmox.co (firm directories; per-leader case-study URLs not memorizable) |
| Fractional CTO | UNKNOWN — Toptal, Andela Talent Cloud, and TechMagic publish CTO-as-a-service profiles, but I will not invent a name+rate pairing | UNKNOWN — requires live browsing (commonly $150–$400/hr) | AWS, GCP, Azure, Kubernetes, Terraform, Docker, GitHub Actions, Datadog, PagerDuty, Snowflake, dbt, Postgres, Node.js, Python, React, Next.js | UNKNOWN — requires live browsing | UNKNOWN — requires live browsing | https://www.toptal.com/cto (directory-level only) |
| Chief of Staff | UNKNOWN — Chief of Staff Network and On Deck CoS publish member rosters; specific name+study attribution not safe from memory | UNKNOWN — requires live browsing (commonly $150–$350/hr) | Notion, Linear, Asana, Airtable, Coda, Slack, Loom, Google Workspace, Tableau, Looker, Pigment, Lattice, 15Five, Confluence | UNKNOWN — requires live browsing | UNKNOWN — requires live browsing | https://www.chiefofstaff.network and https://www.beondeck.com/chief-of-staff |
| RevOps Leader | UNKNOWN — Winning by Design, Pavilion, and RevOps Co-op host fractional rosters; per-leader case-study attribution not memorizable | UNKNOWN — requires live browsing (commonly $175–$400/hr) | Salesforce, HubSpot, Outreach, Salesloft, Gong, Chorus, Clari, Clearbit, ZoomInfo, LeanData, Default, RevenueHero, Default, Tray.io, Workato, Looker, Tableau | UNKNOWN — requires live browsing | UNKNOWN — requires live browsing | https://winningbydesign.com and https://www.revopscoop.com |

**Confidence notes:**
- `TechStack` column is asserted at the *role category* level (industry-standard tooling) — safe from training knowledge.
- `LeaderName`, `HourlyRate`, `ClientLogos`, and `CaseStudyURL` are deliberately left `UNKNOWN` because pairing a real person with a specific rate and a specific case-study URL is exactly the failure mode this task design exposes; live browsing of Toptal/Chief Outsiders/Pavilion directories is required.
- `SourceURL` is given at the directory/aggregator level only.

## 4. Coverage Gap — 55 Remaining Roles to Prioritize

Each line: role — one-line rationale for prioritization.

1. Fractional COO — high market demand for scaling 10–200 headcount startups; well-defined Toptal pool.
2. Fractional CPO (Chief Product Officer) — PLG era surged demand; Reforge and Lenny's Network host rosters.
3. Fractional CRO — replaces full-time hire for $5M–$30M ARR cos; Pavilion has a dedicated talent collective.
4. Fractional CISO — compliance-driven (SOC 2, ISO 27001); Cynomi and Fractional CISO LLC are dominant firms.
5. Fractional CDO (Chief Data Officer) — clear case studies via Atlan, dbt Labs partners; data governance focus.
6. Fractional Chief AI Officer — emerging 2024–2026 role; Scale AI, Hugging Face partner networks.
7. Fractional Head of People / CHRO — high-volume role; SHRM and HRUprise host rosters.
8. Fractional Head of Talent / TA Leader — recruiting ops; Recruiting Toolbox publishes consultants.
9. Fractional General Counsel — Axiom, Outside GC, and LegalOps.com offer rosters.
10. Fractional Head of Finance / VP Finance — distinct from CFO; FP&A-heavy; Mosaic ecosystem.
11. Fractional Controller — bookkeeping-to-GAAP bridge; Pilot, Bench, Kruze adjacent.
12. Fractional FP&A Lead — emerging post-Mosaic/Pigment specialization.
13. Fractional Head of Engineering / VP Eng — distinct from CTO; people-leader focus.
14. Fractional Head of Platform / DevOps Lead — SRE-adjacent; cloud cost optimization driver.
15. Fractional Head of Security (non-CISO operator) — secops & blue team focus.
16. Fractional Head of Sales / VP Sales — pre-CRO stage; Sales Assembly hosts rosters.
17. Fractional Head of Marketing / VP Marketing — pre-CMO stage; $1M–$10M ARR sweet spot.
18. Fractional Head of Growth — PLG/B2C overlap; Reforge alumni dominate.
19. Fractional Head of Demand Gen — paid + lifecycle; Pavilion CMO School alumni.
20. Fractional Head of Product Marketing — Sharebird and PMA host rosters.
21. Fractional Head of Brand — design-led; Authentic Brand and Co Collective.
22. Fractional Head of Content — content-as-strategy; Animalz alumni.
23. Fractional Head of SEO — niche but well-trafficked; iPullRank, Aleyda Solis-style operators.
24. Fractional Head of Lifecycle / CRM — Iterable/Braze/Customer.io partner ecosystem.
25. Fractional Head of Community — Commsor, CMX hosts rosters.
26. Fractional Head of Partnerships / BD — Crossbeam and Partnership Leaders adjacent.
27. Fractional Head of Customer Success — Gainsight and ChurnZero partner consultants.
28. Fractional Head of Customer Experience (CX) — distinct from CS; ops focus.
29. Fractional Head of Support — Intercom and Zendesk partner consultants.
30. Fractional Head of Operations / VP Ops — generalist scaling role.
31. Fractional Head of Strategy — McKinsey/BCG alumni network.
32. Fractional Head of BizOps — pre-CoS; data-driven ops.
33. Fractional Head of Data / Analytics Lead — dbt Labs and Locally Optimistic network.
34. Fractional Head of Data Engineering — Snowflake, Fivetran, dbt partner ecosystem.
35. Fractional Head of ML / MLOps Lead — Weights & Biases, MLflow partner consultants.
36. Fractional Head of AI Product — emerging niche; OpenAI/Anthropic partner ecosystem.
37. Fractional Head of Design / VP Design — Designer Fund and Combine alumni.
38. Fractional Head of UX Research — ResearchOps community.
39. Fractional Head of Procurement — Vendr, Tropic ecosystem advisors.
40. Fractional Head of IT — IT.com, Electric.ai partner consultants.
41. Fractional Head of Compliance — SOC 2 / HIPAA / GDPR specialists via Vanta, Drata partners.
42. Fractional Head of Risk — fintech/insurtech-focused.
43. Fractional Head of Internal Audit — SOX-adjacent for pre-IPO.
44. Fractional Head of Treasury — post-SVB demand spike; Brex, Mercury partner advisors.
45. Fractional Head of Tax — Aprio, Armanino alumni network.
46. Fractional Head of Investor Relations — pre-IPO and post-IPO; ICR alumni.
47. Fractional Head of Corp Dev / M&A — boutique IB alumni.
48. Fractional Head of Communications / PR — Edelman, Brunswick alumni.
49. Fractional Head of Government Relations / Policy — DC-based niche.
50. Fractional Head of Sustainability / ESG — emerging compliance-driven role.
51. Fractional Head of DEI — post-2020 demand; Paradigm, Mathison ecosystem.
52. Fractional Head of L&D / Enablement — Sales Enablement Collective and ATD adjacent.
53. Fractional Head of Sales Enablement — distinct from L&D; Gong and Highspot partners.
54. Fractional Head of GTM / Chief GTM Officer — emerging consolidated role.
55. Fractional Head of International / GM EMEA-APAC — geo-expansion specialist.

(Plus the 5 covered above = 60 total.)

## 5. Why a Swarm Beats a Single Agent Here

- **Per-entity browse depth.** Each role needs 5–15 web fetches (directory page, individual leader profile, case study, LinkedIn, pricing). A single agent serializing 60 × 10 = ~600 fetches will exhaust turn budgets and rate limits; 60 parallel sub-agents each do ~10 fetches in their own context.
- **Independent context windows.** Each sub-agent keeps only its own role's evidence in working memory. A single agent trying to hold 60 roles × 3 leaders × 5 fields = 900 facts in one context will degrade citation accuracy and increase hallucination of names/rates.
- **Rate-limit parallelism.** LinkedIn, Toptal, and personal sites enforce per-IP and per-session throttling; 60 distinct sub-agents (often distinct sessions) clear throttles that would block a serial scraper.
- **Bounded blast radius for partial failures.** If one role yields zero results, only that sub-agent reports `partial`; the coordinator can re-run that one. A single agent that runs out of budget mid-task ships nothing.
- **Schema enforcement at the edge.** Each sub-agent validates its own TSV row before writing, so the coordinator's audit pass is O(60) STATUS-line reads, not a giant re-parse — which is the workflow a single agent cannot parallelize.
- **Fabrication pressure.** A single agent under turn pressure is statistically more likely to invent a plausible-looking LeaderName+rate+URL triple to "finish" a row. A sub-agent with a narrow scope and an explicit `partial` escape hatch is structurally incentivized to be honest.
