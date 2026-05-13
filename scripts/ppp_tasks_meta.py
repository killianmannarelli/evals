"""Per-task metadata for the PPP swarm bundle pipeline.

Each PPP_N prompt is a coordinator-shaped delegation task: the coordinator
plans, dispatches N research sub-agents in parallel, audits STATUS lines,
runs a small follow-up wave, and assembles the final output. The fields
below capture the structural shape we need to emit task.yaml + gold.yaml
+ single_run.json + the upload CSV for each task.
"""

TASKS = [
    {
        "ppp_id": "PPP_4",
        "slug": "non_faang_maintainers_ppp4",
        "task_id": "swarm__non_faang_maintainers__ppp4",
        "title": "Open Source Maintainer Map — top 3 non-FAANG maintainers for 70 npm/PyPI packages",
        "short_objective": "Identify the top 3 non-FAANG maintainers for each of 70 critical npm/PyPI packages.",
        "n_research_agents": 70,
        "n_followups": 14,
        "entity_unit": "npm/PyPI package",
        "entity_unit_plural": "npm/PyPI packages",
        "primary_pattern": "map_reduce",
        "coordination_pattern": "map_reduce",
        "result_ext": "tsv",
        "final_filename": "final_dossier.tsv",
        "summary_filename": "summary.md",
        "output_schema_cols": [
            "PackageName", "MaintainerName", "GitHubProfileURL",
            "ContactInfo", "EstimatedTimezone", "SponsorshipStatus",
            "CurrentEmployer", "NonFAANG_EvidenceURL",
        ],
        "rows_per_agent": "up to 3 maintainer rows",
        "research_summary": (
            "Find the package's GitHub repo, scan recent commit history and "
            "Contributors page for active maintainers, verify employer from "
            "profile/personal site/LinkedIn, exclude Meta/Apple/Amazon/Netflix/Google, "
            "record sponsorship + contact + timezone."
        ),
        "sources": [
            "GitHub repo Contributors / commit history",
            "Maintainer personal websites, Twitter, LinkedIn",
            "GitHub Sponsors / OpenCollective",
        ],
    },
    {
        "ppp_id": "PPP_5",
        "slug": "econ_junior_faculty_ppp5",
        "task_id": "swarm__econ_junior_faculty__ppp5",
        "title": "Tenure-Track Pipeline Scan — top 3 junior faculty at 55 R1 economics departments",
        "short_objective": "Identify the top 3 junior faculty (hired in the last 2 academic years) at 55 R1 university economics departments.",
        "n_research_agents": 55,
        "n_followups": 10,
        "entity_unit": "R1 university economics department",
        "entity_unit_plural": "R1 university economics departments",
        "primary_pattern": "map_reduce",
        "coordination_pattern": "map_reduce",
        "result_ext": "tsv",
        "final_filename": "final_report.tsv",
        "summary_filename": "summary.md",
        "output_schema_cols": [
            "University", "Department", "Faculty_Name", "Hire_Year",
            "PhD_Granting_Institution", "Publication_Count", "Research_Keywords",
        ],
        "rows_per_agent": "up to 3 faculty rows",
        "research_summary": (
            "Find the official faculty directory, identify Assistant Professors "
            "with start dates in the last 2 academic years, pull PhD-granting "
            "institution from CV, and grab Google Scholar publication counts + "
            "research keywords."
        ),
        "sources": [
            "Official university department faculty directories",
            "Faculty CVs (linked from profile pages)",
            "Google Scholar profile pages",
        ],
    },
    {
        "ppp_id": "PPP_6",
        "slug": "fractional_execs_ppp6",
        "task_id": "swarm__fractional_execs__ppp6",
        "title": "Fractional Exec Marketplace — top 3 fractional leaders for 60 functional roles",
        "short_objective": "Identify the top 3 fractional leaders with public case studies for each of 60 functional roles (e.g., RevOps, Chief of Staff).",
        "n_research_agents": 60,
        "n_followups": 10,
        "entity_unit": "functional role",
        "entity_unit_plural": "functional roles",
        "primary_pattern": "map_reduce",
        "coordination_pattern": "map_reduce",
        "result_ext": "tsv",
        "final_filename": "final.tsv",
        "summary_filename": "summary.md",
        "output_schema_cols": [
            "Role", "LeaderName", "HourlyRate", "TechStack",
            "ClientLogos", "CaseStudyURL", "SourceURL",
        ],
        "rows_per_agent": "up to 3 leader rows",
        "research_summary": (
            "Search LinkedIn, Toptal, and personal portfolios for active fractional "
            "leaders in the assigned role; capture hourly rate, tech stack, client "
            "logos, and at least one public case-study URL per leader."
        ),
        "sources": [
            "LinkedIn profile search",
            "Toptal / Continuum / Bolster directories",
            "Personal portfolio sites and case study posts",
        ],
    },
    {
        "ppp_id": "PPP_7",
        "slug": "micro_pe_rollups_ppp7",
        "task_id": "swarm__micro_pe_rollups__ppp7",
        "title": "Micro-PE Rollup Targets — top 3 acquisition candidates across 75 niches",
        "short_objective": "Identify the top 3 acquisition targets ($1M-$5M EBITDA, owner age 55+) in each of 75 'boring' business niches and produce CIM-style teaser decks.",
        "n_research_agents": 75,
        "n_followups": 15,
        "entity_unit": "business niche",
        "entity_unit_plural": "business niches",
        "primary_pattern": "map_reduce",
        "coordination_pattern": "map_reduce",
        "result_ext": "md",
        "final_filename": "final_report.md",
        "summary_filename": "summary.md",
        # Markdown teaser deck rather than flat TSV columns — describe sections instead.
        "output_schema_cols": [
            "CompanyOverview", "FinancialSnapshot", "OwnershipProfile",
            "InvestmentRationale", "SourceURLs",
        ],
        "rows_per_agent": "3 CIM-style teaser decks (one per candidate company)",
        "research_summary": (
            "Use state business registries, BuiltWith / Apollo, and local news to "
            "find owner-operated SMBs in the niche with $1M-$5M EBITDA and an owner "
            "55+; write a CIM-style teaser deck per company with overview, "
            "financial snapshot, ownership profile, investment rationale, and sources."
        ),
        "sources": [
            "State business registries",
            "Apollo.io / BuiltWith / ZoomInfo",
            "Local business news and trade press",
        ],
    },
    {
        "ppp_id": "PPP_8",
        "slug": "alt_data_vendors_ppp8",
        "task_id": "swarm__alt_data_vendors__ppp8",
        "title": "Alt-Data Source Catalog — top 3 non-traditional vendors for 65 macro indicators",
        "short_objective": "For each of 65 macro indicators, identify the top 3 non-traditional data vendors and capture pricing, update frequency, and history depth.",
        "n_research_agents": 65,
        "n_followups": 15,
        "entity_unit": "macro indicator",
        "entity_unit_plural": "macro indicators",
        "primary_pattern": "map_reduce",
        "coordination_pattern": "map_reduce",
        "result_ext": "tsv",
        "final_filename": "final.tsv",
        "summary_filename": "summary.md",
        "output_schema_cols": [
            "Indicator", "VendorName", "UpdateFrequency",
            "HistoryDepth", "Price", "DataSourceURL",
        ],
        "rows_per_agent": "up to 3 vendor rows",
        "research_summary": (
            "For the assigned indicator, find 3 non-traditional / alternative data "
            "vendors. Use vendor product pages, API docs, and pricing pages to fill "
            "update frequency, history depth, and price."
        ),
        "sources": [
            "Alternative data marketplaces (Datarade, Snowflake Marketplace)",
            "Vendor product / API documentation pages",
            "Vendor pricing pages and sample data downloads",
        ],
    },
    {
        "ppp_id": "PPP_9",
        "slug": "dao_treasury_audit_ppp9",
        "task_id": "swarm__dao_treasury_audit__ppp9",
        "title": "DAO Treasury Asset Audit — top 3 non-stablecoin assets and custody for 50 DAOs",
        "short_objective": "Audit the treasury composition (top 3 non-stablecoin assets) and custody setup of 50 major DAOs.",
        "n_research_agents": 50,
        "n_followups": 10,
        "entity_unit": "DAO",
        "entity_unit_plural": "DAOs",
        "primary_pattern": "map_reduce",
        "coordination_pattern": "map_reduce",
        "result_ext": "tsv",
        "final_filename": "final_dashboard.tsv",
        "summary_filename": "summary.md",
        "output_schema_cols": [
            "DAO_Name", "Asset_1", "Asset_1_Value_USD", "Asset_2",
            "Asset_2_Value_USD", "Asset_3", "Asset_3_Value_USD",
            "Diversification_Non_Stable", "Custody_Type", "Multisig_Address",
            "Signer_Count", "Source_Links",
        ],
        "rows_per_agent": "one TSV row (top 3 assets + custody fields)",
        "research_summary": (
            "Find the DAO treasury address(es) via Etherscan or the relevant block "
            "explorer, pull top 3 non-stablecoin holdings + USD values, and document "
            "custody (Gnosis Safe / multisig signers / signer count) from governance "
            "forum + Snapshot."
        ),
        "sources": [
            "Etherscan / block explorers (Arbiscan, Polygonscan, etc.)",
            "Governance forum treasury reports",
            "Snapshot.org proposal pages",
        ],
    },
    {
        "ppp_id": "PPP_10",
        "slug": "state_ai_laws_ppp10",
        "task_id": "swarm__state_ai_laws__ppp10",
        "title": "State-Level AI Law Tracker — top 3 AI bills per US state since 2023",
        "short_objective": "Build a 50-state AI bill tracker: top 3 bills per state mentioning 'algorithmic' or 'foundation model' since 2023.",
        "n_research_agents": 50,
        "n_followups": 10,
        "entity_unit": "US state",
        "entity_unit_plural": "US states",
        "primary_pattern": "map_reduce",
        "coordination_pattern": "map_reduce",
        "result_ext": "tsv",
        "final_filename": "final_bill_tracker.tsv",
        "summary_filename": "summary.md",
        "output_schema_cols": [
            "State", "Bill_ID", "Title", "Sponsor",
            "Status", "Summary_of_Obligations", "Source_URL",
        ],
        "rows_per_agent": "up to 3 bill rows",
        "research_summary": (
            "Search Legiscan and the state legislature site for bills proposed or "
            "enacted since 2023-01-01 that mention 'algorithmic' or 'foundation "
            "model'; capture bill ID, title, sponsor, status, obligations summary, "
            "and source URL."
        ),
        "sources": [
            "Legiscan.com state pages",
            "Official state legislature websites",
            "State attorney general / AI policy press releases",
        ],
    },
]


def by_ppp_id(ppp_id):
    for t in TASKS:
        if t["ppp_id"] == ppp_id:
            return t
    raise KeyError(ppp_id)
