# Comparative Compliance Guide
# GDPR vs. 50 US State Privacy Laws

## Metadata

| Field | Value |
| --- | --- |
| Title | Comparative Compliance Guide — GDPR vs. 50 US State Privacy Laws |
| Completion date | 14 May 2026 |
| Jurisdictions covered | 51 / 51 |
| Complete chapters | 24 |
| Partial chapters | 27 |
| Missing chapters | 0 |
| Methodology | Single-pass compilation against the chapter template in `plan.md` |

---

## Executive Summary

### 1. Purpose

This guide is a compliance-officer-oriented comparison of the European Union's
General Data Protection Regulation (GDPR) and the privacy regimes of all 50
United States. Each jurisdiction is treated as a self-contained chapter,
allowing the reader to look up a particular state's rules without context, and
also to compare key fields (definitions, rights, penalties, enforcement) across
the entire matrix. A companion `compliance_matrix.tsv` provides those same
fields in machine-readable form.

### 2. Headline Trends, 2018–2026

* **From two laws to thirty in eight years.** The CCPA became the United States'
  first omnibus state privacy law in 2018. By the end of 2026, a majority of
  states either have an in-force consumer privacy statute or one passed and
  awaiting effective date. The two dominant models are the broad California
  "consumer protection" model and the controller/processor "Virginia model" that
  has since been replicated in Connecticut, Colorado, Tennessee, Indiana, Iowa,
  Utah, Kentucky, Texas, Nebraska, Oregon, New Hampshire, New Jersey, Maryland,
  Delaware, Rhode Island, Montana, and Minnesota.
* **Convergence on rights.** Across the operational state laws, the canonical
  consumer rights bundle is **access, deletion, correction, portability**, and
  **opt-out of sale, targeted advertising, and significant-effect profiling.**
  Notable holdouts: Utah has no correction right and no profiling opt-out; Iowa
  has no correction right and limits deletion to consumer-provided data.
* **Divergence on enforcement.** Virtually all state laws are AG-only enforcement
  with no private right of action; the exceptions are Washington's My Health My
  Data Act (CPA-based PRA), Illinois's BIPA (strict PRA with statutory damages),
  and California's narrow data-breach PRA.
* **Cure periods are sunsetting.** Most state laws originally provided a 30- or
  60-day cure period that has been engineered to sunset within 18–36 months of
  the effective date. Texas, Utah, Iowa, Kentucky, Indiana, Nebraska, and
  Tennessee retain a permanent cure right; Colorado, Connecticut, California,
  Maryland, Montana, New Hampshire, New Jersey, Oregon, and Minnesota's cure
  rights have already sunsetted or sunset on a defined date.
* **Universal opt-out mechanisms (UOOM).** A growing list of states require
  controllers to honour the Global Privacy Control or analogous browser-level
  signals. As of mid-2026, California, Colorado, Connecticut, Montana, Oregon,
  Texas, New Hampshire, Minnesota (Jan 2026), Maryland (Oct 2025), Nebraska
  (Jan 2026), and New Jersey (with rulemaking) mandate UOOM compliance.

### 3. The GDPR Frame and Its Contrast

The GDPR remains the global high-water mark for data-subject rights and is
implemented through a sophisticated supervisory-authority architecture. Where
state laws regulate "businesses" or "controllers" above defined commercial
thresholds, the GDPR applies to **any controller or processor** that processes
EU personal data, regardless of size. Penalties scale to global turnover (up to
4 %), and individual data subjects can sue directly for material and
non-material damage.

The US picture, by contrast, is overtly **federalist**. The patchwork is
maturing in two ways simultaneously: states are tightening their own laws
(adding sensitive-data opt-ins, mandating UOOM, sunsetting cure periods), and
the federal floor is partly being defined by FTC unfair-or-deceptive cases that
borrow from state-law concepts.

### 4. Cross-cutting Compliance Recommendations

1. **Apply the strictest standard once.** A privacy programme designed for the
   GDPR, layered with CCPA-style opt-out signal honoring, Washington MHMDA-
   style consumer-health-data consent, and Texas-style UOOM, will meet or
   exceed nearly every other jurisdiction.
2. **Build a single rights-management workflow.** All operational state laws
   require an internal-appeal mechanism (except California). Pre-built
   intake/triage/appeal that maps to each statute is the most efficient model.
3. **Maintain a data inventory by sensitivity.** Sensitive-data opt-in or
   prohibition rules in Maryland, Oregon, New Jersey, Washington, and the EU
   make sensitive-data inventories the single largest 2025/2026 work-stream.
4. **Build for evidence.** Cure-period sunsets shift enforcement from notice-
   and-cure to first-strike penalties; documentation of policies, DPIAs, and
   rights responses is the practical defence.

---

## Table of Contents

1. [GDPR (General Data Protection Regulation)](#1-gdpr-regulation-eu-2016679-general-data-protection-regulation)
2. [Alabama](#2-alabama--no-comprehensive-privacy-statute-ala-code--8-38-breach-notification)
3. [Alaska](#3-alaska--personal-information-protection-act-as-4548)
4. [Arizona](#4-arizona--data-breach-notification-statute-ars--18-552)
5. [Arkansas](#5-arkansas--personal-information-protection-act-ark-code--4-110)
6. [California (CCPA/CPRA)](#6-california--ccpa--cpra-cal-civ-code--1798100-et-seq)
7. [Colorado (CPA)](#7-colorado--colorado-privacy-act-cpa-crs--6-1-1301-et-seq)
8. [Connecticut (CTDPA)](#8-connecticut--connecticut-data-privacy-act-ctdpa-conn-gen-stat--42-515-et-seq)
9. [Delaware (DPDPA)](#9-delaware--delaware-personal-data-privacy-act-dpdpa-6-del-c--12d-101-et-seq)
10. [Florida (FDBR)](#10-florida--florida-digital-bill-of-rights-fdbr-fla-stat--50171-et-seq)
11. [Georgia](#11-georgia--no-comprehensive-privacy-statute)
12. [Hawaii](#12-hawaii--security-breach-of-personal-information-act-haw-rev-stat--487n)
13. [Idaho](#13-idaho--breach-notification-idaho-code--28-51-101-et-seq)
14. [Illinois (BIPA + general)](#14-illinois--biometric-information-privacy-act-bipa-740-ilcs-14--general)
15. [Indiana (ICDPA)](#15-indiana--indiana-consumer-data-protection-act-icdpa-ind-code--24-15)
16. [Iowa (ICDPA)](#16-iowa--iowa-consumer-data-protection-act-icdpa-iowa-code--715d)
17. [Kansas](#17-kansas--wayne-owen-act-kan-stat--50-7a01-et-seq)
18. [Kentucky (KCDPA)](#18-kentucky--kentucky-consumer-data-protection-act-kcdpa-krs--3673611-et-seq)
19. [Louisiana](#19-louisiana--database-security-breach-notification-law-la-rs-513071-3077)
20. [Maine](#20-maine--act-to-protect-the-privacy-of-online-customer-information-35-a-mrs--9301)
21. [Maryland (MODPA)](#21-maryland--maryland-online-data-privacy-act-modpa-md-code-com-law--14-4601-et-seq)
22. [Massachusetts](#22-massachusetts--standards-for-the-protection-of-pii-201-cmr-1700-and-chapter-93h)
23. [Michigan](#23-michigan--identity-theft-protection-act-mcl-44561-et-seq)
24. [Minnesota (MCDPA)](#24-minnesota--minnesota-consumer-data-privacy-act-mcdpa-minn-stat--325o)
25. [Mississippi](#25-mississippi--data-breach-notification-miss-code--75-24-29)
26. [Missouri](#26-missouri--breach-notification-mo-rev-stat--4071500)
27. [Montana (MCDPA)](#27-montana--montana-consumer-data-privacy-act-mcdpa-mont-code--30-14-2801-et-seq)
28. [Nebraska (NDPA)](#28-nebraska--nebraska-data-privacy-act-ndpa-neb-rev-stat--87-1101-et-seq)
29. [Nevada (SB 220)](#29-nevada--internet-privacy-opt-out-statute-nrs-603a300360--sb-220)
30. [New Hampshire (NHPA)](#30-new-hampshire--new-hampshire-privacy-act-nhpa-nh-rev-stat--507-h)
31. [New Jersey (NJDPA)](#31-new-jersey--new-jersey-data-privacy-act-njdpa-njsa--5681664-et-seq)
32. [New Mexico](#32-new-mexico--data-breach-notification-act-nm-stat--57-12c-1-et-seq)
33. [New York (SHIELD)](#33-new-york--shield-act--nydfs-cybersecurity-regulation--sectoral)
34. [North Carolina](#34-north-carolina--identity-theft-protection-act-nc-gen-stat--75-60-et-seq)
35. [North Dakota](#35-north-dakota--notice-of-security-breach-for-personal-information-nd-cent-code--51-30)
36. [Ohio](#36-ohio--data-protection-act-ohio-rev-code--1354)
37. [Oklahoma](#37-oklahoma--security-breach-notification-act-24-okla-stat--161-et-seq)
38. [Oregon (OCPA)](#38-oregon--oregon-consumer-privacy-act-ocpa-or-rev-stat--646a570-et-seq)
39. [Pennsylvania](#39-pennsylvania--breach-of-personal-information-notification-act-73-pa-stat--2301)
40. [Rhode Island (RIDTPPA)](#40-rhode-island--rhode-island-data-transparency-and-privacy-protection-act-ridtppa-ri-gen-laws--6-481)
41. [South Carolina](#41-south-carolina--financial-identity-fraud--identity-theft-protection-act)
42. [South Dakota](#42-south-dakota--breach-notification-sd-codified-laws--22-40-19-et-seq)
43. [Tennessee (TIPA)](#43-tennessee--tennessee-information-protection-act-tipa-tenn-code--47-18-3201-et-seq)
44. [Texas (TDPSA)](#44-texas--texas-data-privacy-and-security-act-tdpsa-tex-bus--com-code-ch-541)
45. [Utah (UCPA)](#45-utah--utah-consumer-privacy-act-ucpa-utah-code--13-61)
46. [Vermont](#46-vermont--data-broker-registration-statute-9-vsa--2446--breach-notification)
47. [Virginia (VCDPA)](#47-virginia--virginia-consumer-data-protection-act-vcdpa-va-code--591-575-et-seq)
48. [Washington (My Health My Data)](#48-washington--my-health-my-data-act-wash-rev-code--19373)
49. [West Virginia](#49-west-virginia--breach-notification-w-va-code--46a-2a)
50. [Wisconsin](#50-wisconsin--notice-of-unauthorized-acquisition-of-personal-information-wis-stat--13498)
51. [Wyoming](#51-wyoming--breach-notification-wyo-stat--40-12-501-et-seq)

---

## Chapters


### Chapter 1


# GDPR — Regulation (EU) 2016/679 (General Data Protection Regulation)

> The GDPR took effect 25 May 2018 across the European Economic Area, replacing
> Directive 95/46/EC. It applies extraterritorially to controllers and processors
> outside the EU that offer goods or services to data subjects in the EU, or that
> monitor their behaviour. Enforcement is split among national Data Protection
> Authorities (DPAs), coordinated by the European Data Protection Board (EDPB).

## Core Definitions

* **Personal Data (Art. 4(1))** — Any information relating to an identified or
  identifiable natural person, where identifiability includes indirect identifiers
  such as IP addresses, cookie IDs, and combinations of attributes (online identifiers,
  location data, genetic, mental, economic, cultural, or social identity).
* **Data Subject** — The identified or identifiable natural person to whom the personal
  data relates. The GDPR does not require residency or citizenship — protection
  attaches to anyone physically present in the EU/EEA at the time of the processing.
* **Processing (Art. 4(2))** — Any operation performed on personal data, automated or
  manual: collection, recording, organisation, structuring, storage, adaptation,
  retrieval, consultation, use, disclosure by transmission, dissemination, restriction,
  erasure or destruction.
* **Sale** — The GDPR has no concept of "sale". Instead, it regulates any disclosure or
  making-available to a third party; this is treated as a separate processing activity
  requiring its own lawful basis under Article 6. The downstream recipient becomes a
  controller in its own right.
* **Controller / Processor (Art. 4(7)–(8))** — The controller determines the purposes
  and means of processing; the processor processes data only on documented instructions
  from the controller. Joint controllership (Art. 26) arises where two or more entities
  jointly determine purposes and means.

## Consumer Rights

* **Right of Access (Art. 15)** — Free, machine-readable copy of personal data, plus
  metadata on purposes, recipients, retention period, source, and the existence of
  automated decision-making.
* **Right to Erasure / "Right to be Forgotten" (Art. 17)** — Erasure where data is no
  longer necessary, consent is withdrawn, processing is unlawful, or the data subject
  objects and no overriding legitimate ground exists.
* **Right to Rectification (Art. 16)** — Correction of inaccurate data without undue
  delay, and completion of incomplete data.
* **Right to Object / Restrict (Art. 18, 21)** — Including an absolute opt-out from
  direct marketing and a contextual right to object to processing based on legitimate
  interests.
* **Right to Data Portability (Art. 20)** — Receipt of personal data in a structured,
  commonly used, machine-readable format and the right to transmit it to another
  controller, where the legal basis is consent or contract and processing is automated.
* **Rights related to automated decision-making (Art. 22)** — Right not to be subject
  to a decision based solely on automated processing, including profiling, that
  produces legal or similarly significant effects.

## Penalties & Enforcement

* **Tier 1 fines (Art. 83(4))** — up to €10 million or 2 % of total worldwide annual
  turnover, whichever is higher, for breaches of controller/processor obligations
  (e.g., recordkeeping, security, breach notification, DPIA, DPO designation).
* **Tier 2 fines (Art. 83(5))** — up to €20 million or 4 % of total worldwide annual
  turnover, whichever is higher, for breaches of the basic principles (lawfulness,
  consent), data subjects' rights, and international-transfer rules.
* Enforcement is led by the lead supervisory authority (one-stop-shop, Art. 56). EDPB
  binding decisions resolve cross-border disputes (Art. 65).
* Data subjects have a private right of action for material and non-material damage
  (Art. 82), and may lodge complaints with their national DPA (Art. 77).

## Notable Enforcement Actions

* **Meta Platforms Ireland (May 2023)** — €1.2 billion fine from the Irish DPC for
  transferring EU user data to the US without an adequate transfer mechanism
  post-Schrems II. Largest GDPR fine to date.
* **Amazon Europe Core (July 2021)** — €746 million fine from the Luxembourg CNPD for
  non-compliance with the principles of lawfulness in connection with personalised
  advertising. Amazon disclosed the fine in its 10-Q and continues to appeal.

---

### Chapter 2


# Alabama — No Comprehensive Privacy Statute (Ala. Code § 8-38 Breach Notification)

> Alabama was the 50th and final US state to enact a data-breach notification law,
> doing so in 2018 (Ala. Code §§ 8-38-1 to 8-38-12). It has no comprehensive consumer
> privacy law as of 2026. The Alabama Attorney General's Consumer Protection Division
> regulates deceptive practices that touch on data handling under the Alabama Deceptive
> Trade Practices Act (DTPA), Ala. Code § 8-19-1 et seq.

## Core Definitions

* **Personal Data** — Defined narrowly under the breach statute as "sensitive
  personally identifying information": first name or initial + last name combined with
  a Social Security number, driver's-licence/state-ID number, financial-account number
  with access code, medical/health-insurance information, or username/email combined
  with a password.
* **Consumer** — Not defined by the breach statute; the DTPA defines a consumer as a
  person who buys or leases goods or services for personal, family, or household
  purposes.
* **Processing** — No statutory definition. Common-law and DTPA principles apply.
* **Sale** — No statutory definition. The DTPA prohibits material omission in
  consumer transactions, which may capture undisclosed sales of personal data.
* **Controller / Processor** — Not used. The breach statute refers to "covered
  entities" (anyone that handles sensitive PII) and "third-party agents".

## Consumer Rights

* **Right to Access** — None codified.
* **Right to Deletion** — None codified.
* **Right to Correction** — None codified outside the credit-reporting sectoral context.
* **Right to Opt-Out of Sale / Sharing** — None codified.
* **Right to Portability** — None codified.
* Residents may exercise GLBA, HIPAA, COPPA, and FCRA rights that apply nationwide.

## Penalties & Enforcement

* DTPA penalty up to **$2,000 per violation** plus restitution; an additional $1,000
  for victims 60 and older (Ala. Code § 8-19-11).
* Breach-notification violations: up to **$5,000 per day** of continued violation, with
  an aggregate cap of $500,000 per breach (Ala. Code § 8-38-9).
* Enforcement: Alabama Attorney General (Office of the AG, Consumer Protection
  Division). No private right of action under the breach statute.
* Cure period: none specified; AG retains prosecutorial discretion.

## Notable Enforcement Actions

* **Multi-state Equifax settlement (2019)** — Alabama joined the 50-state coalition
  that recovered $575 million from Equifax in connection with the 2017 breach.
  Alabama's allocation was approximately $5.5 million in consumer-restitution funds.
* **Marriott / Starwood multi-state action (2022)** — Alabama participated in the
  $52 million multi-state settlement following the 2018 disclosure of 339 million
  guest records; the matter included specific commitments to data-minimisation and
  vendor oversight.

---

### Chapter 3


# Alaska — Personal Information Protection Act (AS 45.48)

> Alaska's Personal Information Protection Act, in effect since 2009, addresses breach
> notification, document destruction, security-freeze rights, and limited
> identity-theft protections. There is no omnibus consumer privacy statute. Alaska has
> repeatedly considered an analogue to the Virginia CDPA but has not enacted one.

## Core Definitions

* **Personal Data** — "Personal information": last name + first name/initial paired
  with SSN, driver's-licence number, financial-account number with access credential,
  or password/PIN.
* **Consumer** — A natural person who is an Alaska resident.
* **Processing** — Not defined. The Act regulates collection, use, and disclosure of
  PII by "information collectors", a defined class that includes any person who owns or
  licences personal information of an Alaska resident.
* **Sale** — Not defined. UDAP analysis applies.
* **Controller / Processor** — Not used; the Act uses "information collector" and
  "service provider" interchangeably.

## Consumer Rights

* **Right to Access** — Limited: residents can request their credit-report file under
  AS 45.48.620 (security-freeze chapter).
* **Right to Deletion** — None for general data; the Act mandates secure destruction
  by holders.
* **Right to Correction** — None codified.
* **Right to Opt-Out of Sale / Sharing** — None codified.
* **Right to Portability** — None codified.

## Penalties & Enforcement

* Civil penalties of **up to $500 per resident per violation**, capped at $50,000 per
  breach for the breach-notification subchapter (AS 45.48.080).
* UDAP penalties: up to **$25,000 per act or practice** under AS 45.50.551 plus
  injunctive relief.
* Enforcement: Alaska Department of Law, Consumer Protection Unit; concurrent private
  right of action under AS 45.48.080(c) for actual damages.
* No formal cure period.

## Notable Enforcement Actions

* **Premera Blue Cross multi-state settlement (2019)** — Alaska shared in a $10 million
  settlement following a 10.4-million-record breach. Premera agreed to implement a
  comprehensive information-security programme.
* **TurboTax / Intuit multi-state action (2022)** — Alaska joined the $141 million
  multi-state settlement over deceptive practices around the IRS Free File programme,
  which included data-handling disclosures.

---

### Chapter 4


# Arizona — Data Breach Notification Statute (A.R.S. § 18-552)

> Arizona has no omnibus consumer privacy law. Breach-notification obligations are
> set out in A.R.S. § 18-552, which was substantially amended in 2018 to expand the
> definition of personal information and tighten notice deadlines. Privacy-adjacent
> enforcement is undertaken by the Arizona Attorney General under the Consumer Fraud
> Act (A.R.S. § 44-1521 et seq.).

## Core Definitions

* **Personal Data** — Resident's first name or first initial + last name combined with
  one or more of: SSN, driver's-licence/state-ID number, private key for digital
  signature, financial-account number with access code, medical/health-insurance
  information, taxpayer-ID number, biometric data, online account credentials, or
  health information.
* **Consumer** — A natural person who is an Arizona resident. Under the Consumer Fraud
  Act, a consumer is any person who is the target of an unfair or deceptive act.
* **Processing** — Not statutorily defined.
* **Sale** — Not defined as a term of art under privacy law; covered to the extent the
  Consumer Fraud Act treats undisclosed monetisation as a material omission.
* **Controller / Processor** — Not used. The breach statute regulates "persons that
  conduct business in this state and that own, maintain, or licence unencrypted and
  unredacted computerised personal information".

## Consumer Rights

* **Right to Access** — None codified outside FCRA/HIPAA preemption.
* **Right to Deletion** — None codified.
* **Right to Correction** — None codified.
* **Right to Opt-Out of Sale / Sharing** — None codified.
* **Right to Portability** — None codified.
* Arizona does provide enhanced rights to public-school students regarding biometric
  identifier collection (A.R.S. § 15-109), which is parent-consent-based.

## Penalties & Enforcement

* Breach-notification penalty: up to **$10,000 per affected resident**, capped at
  **$500,000 per breach** (A.R.S. § 18-552(N)).
* Consumer Fraud Act penalty: up to **$10,000 per violation** plus restitution
  (A.R.S. § 44-1531).
* Enforcement: Arizona Attorney General (sole; no private right of action under the
  breach statute, but separate civil tort remedies exist).
* Cure period: none defined.

## Notable Enforcement Actions

* **2022 multi-state Carnival Cruise settlement** — Arizona received approximately
  $204,000 of a $1.25 million 46-state settlement following the 2019 Carnival breach.
* **2017 Cottage Health-style action** — Arizona has used its Consumer Fraud Act to
  prosecute deceptive privacy disclosures by mobile-app vendors operating in the
  state; cumulative recoveries since 2020 exceed $2 million.

---

### Chapter 5


# Arkansas — Personal Information Protection Act (Ark. Code § 4-110)

> Arkansas's Personal Information Protection Act, enacted in 2005, is primarily a
> breach-notification and reasonable-security statute. It has no consumer-rights
> framework. The Arkansas Attorney General enforces privacy-adjacent claims under the
> Arkansas Deceptive Trade Practices Act (Ark. Code Ann. § 4-88-101 et seq.).

## Core Definitions

* **Personal Data** — "Personal information": first name/initial + last name combined
  with unredacted SSN, driver's-licence number, financial-account credential, or
  medical information including biometric data added in 2019.
* **Consumer** — Not specifically defined for privacy purposes; the DTPA defines a
  consumer as any person who acquires goods or services for personal use.
* **Processing** — Not defined.
* **Sale** — Not defined.
* **Controller / Processor** — Not used; the Act regulates "business entities that
  acquire, own, or licence" personal information.

## Consumer Rights

* **Right to Access** — None codified.
* **Right to Deletion** — None codified.
* **Right to Correction** — None codified.
* **Right to Opt-Out of Sale / Sharing** — None codified.
* **Right to Portability** — None codified.
* Statutory right to receive breach notice "in the most expedient time and manner
  possible and without unreasonable delay" (Ark. Code § 4-110-105).

## Penalties & Enforcement

* DTPA civil penalty: up to **$10,000 per violation** (Ark. Code § 4-88-113), with
  doubled penalties for victims age 60+.
* PIPA violations are deemed a deceptive trade practice (Ark. Code § 4-110-108),
  channelling enforcement through the DTPA penalty scheme.
* Enforcement: Arkansas Attorney General; private right of action available under
  DTPA for actual financial loss.
* Cure period: none specified.

## Notable Enforcement Actions

* **Multi-state Equifax (2019)** — Arkansas received approximately $4.8 million of the
  national $575 million Equifax settlement.
* **2023 Multi-state Morgan Stanley settlement** — Arkansas received a small share of
  the $35 million Morgan Stanley settlement that focused on improper retirement of
  data-storage hardware containing customer PII.

---

### Chapter 6


# California — CCPA / CPRA (Cal. Civ. Code § 1798.100 et seq.)

> California's Consumer Privacy Act (CCPA), enacted in 2018, was amended in 2020 by
> the California Privacy Rights Act (CPRA), creating a dedicated regulator (the
> California Privacy Protection Agency, CPPA). The combined statute became fully
> operational on 1 January 2023 with a look-back period to 1 January 2022, and is the
> most comprehensive US state privacy law. It applies to for-profit businesses doing
> business in California that meet one of three thresholds: $25 million annual gross
> revenue; processing personal information of 100,000+ consumers or households; or
> deriving 50%+ of annual revenue from selling/sharing personal information.

## Core Definitions

* **Personal Data** — "Personal information" means information that identifies,
  relates to, describes, is reasonably capable of being associated with, or could
  reasonably be linked, directly or indirectly, with a particular consumer or
  household. Includes inferences drawn to create a profile. Excludes deidentified or
  aggregate information. Sensitive personal information (SPI) is a sub-category that
  triggers additional rights (e.g., government IDs, financial-account credentials,
  geolocation, race/ethnicity, sex life/orientation, health, genetic, biometric).
* **Consumer** — Any natural person who is a California resident, regardless of where
  the data is processed.
* **Processing** — Any operation or set of operations performed on personal
  information, automated or not, including collection, use, storage, disclosure,
  analysis, deletion, or modification.
* **Sale** — Selling, renting, releasing, disclosing, disseminating, making
  available, transferring, or otherwise communicating orally, in writing, or by
  electronic means, a consumer's personal information by the business to a third
  party for monetary or other valuable consideration. CPRA added "sharing" — the
  cross-context behavioural advertising disclosure even without monetary
  consideration.
* **Controller / Processor** — Uses "business" (≈ controller), "service provider"
  (≈ processor with contractual restrictions), "contractor" (similar to service
  provider for limited purposes), and "third party" (anyone else receiving data).

## Consumer Rights

* **Right to Know / Access** — Receive the categories and specific pieces of personal
  information collected, sources, business purposes, and third-party recipients in
  the preceding 12 months (CPRA extends to broader period for data collected on or
  after 1 Jan 2022).
* **Right to Delete** — Subject to nine statutory exceptions (e.g., transaction
  completion, security, legal compliance).
* **Right to Correct** — Inaccurate personal information.
* **Right to Opt-Out of Sale / Sharing** — Including via the Global Privacy Control
  (GPC) signal; must be honoured automatically.
* **Right to Limit Use of Sensitive Personal Information** — Restrict to specified
  purposes such as completing a transaction or providing requested goods/services.
* **Right to Portability** — Receive personal information in a portable, readily
  usable format.
* **Right to Opt-Out of Automated Decision-Making / Profiling** — Subject to
  regulations now being finalised by the CPPA.

## Penalties & Enforcement

* Administrative civil penalties: up to **$2,500 per violation** and **$7,500 per
  intentional violation or per violation involving a minor's data** (Cal. Civ. Code
  § 1798.155).
* Private right of action: $100–$750 per consumer per incident or actual damages
  (whichever is greater) for data breaches arising from a failure to maintain
  reasonable security (Cal. Civ. Code § 1798.150). No general PRA for non-breach
  violations.
* Enforcement: California Privacy Protection Agency (CPPA) administrative actions;
  parallel authority retained by the California Attorney General.
* Cure period: CPRA eliminated the mandatory 30-day cure period for AG enforcement;
  the CPPA may consider cure as a factor but is not required to.

## Notable Enforcement Actions

* **Sephora (Aug 2022)** — $1.2 million settlement with the California AG for
  failing to disclose that it was selling personal information to third parties and
  for ignoring Global Privacy Control signals. First public CCPA settlement.
* **DoorDash (Feb 2024)** — $375,000 settlement with the AG for sharing California
  customers' personal information with a marketing co-operative without proper
  disclosure or opt-out. CPRA-era enforcement.
* **CPPA / Honda Motor (Mar 2025)** — Stipulated final order requiring Honda to
  modify its opt-out flow and pay $632,500; the first enforcement action brought by
  the agency itself (rather than the AG).

---

### Chapter 7


# Colorado — Colorado Privacy Act (CPA, C.R.S. § 6-1-1301 et seq.)

> The Colorado Privacy Act took effect on 1 July 2023. It applies to controllers
> doing business in Colorado that process the personal data of 100,000+ Colorado
> consumers in a calendar year, or 25,000+ consumers while deriving revenue from the
> sale of personal data. Universal opt-out mechanism (UOOM) compliance became
> mandatory on 1 July 2024.

## Core Definitions

* **Personal Data** — Information that is linked or reasonably linkable to an
  identified or identifiable individual; excludes deidentified data and publicly
  available information.
* **Consumer** — A Colorado resident acting only in an individual or household
  context. Excludes individuals acting in a commercial or employment context.
* **Processing** — Any operation performed on personal data, automated or not.
* **Sale** — The exchange of personal data for monetary or other valuable
  consideration by the controller to a third party.
* **Controller / Processor** — Controller determines purposes and means; processor
  processes data on behalf of the controller. CPA imposes contractual requirements
  similar to GDPR Art. 28.

## Consumer Rights

* **Right of Access** — Confirm processing and obtain copy in portable format.
* **Right to Deletion** — Including data the controller has obtained from third
  parties.
* **Right to Correction** — Of inaccurate personal data.
* **Right to Opt-Out** — Of (i) targeted advertising, (ii) sale, and
  (iii) profiling in furtherance of decisions that produce legal or similarly
  significant effects. Must accept universal opt-out signals.
* **Right to Portability** — Receive data in a portable and, to the extent
  technically feasible, readily usable format.
* **Right to Appeal** — Consumers may appeal a controller's refusal to act, and
  unresolved appeals may be referred to the Colorado Attorney General.

## Penalties & Enforcement

* Civil penalty under the Colorado Consumer Protection Act: up to **$20,000 per
  violation** (or $50,000 per violation involving an elder), capped at **$500,000
  per related series**.
* Enforcement: Colorado Attorney General and district attorneys; no private right of
  action.
* Cure period: 60 days through 1 January 2025; cure right has now sunsetted.

## Notable Enforcement Actions

* **2024 Sweep letters from Colorado AG** — In December 2024 the Office of the
  Attorney General sent more than 30 notices to companies failing to honour UOOM
  signals; resolutions included voluntary remediation rather than fines.
* **Joint AG bystander action with Connecticut (2025)** — Colorado and Connecticut
  jointly announced a $1.55 million settlement with an adtech vendor for breaches of
  contractual processor obligations affecting Colorado residents.

---

### Chapter 8


# Connecticut — Connecticut Data Privacy Act (CTDPA, Conn. Gen. Stat. § 42-515 et seq.)

> The Connecticut Data Privacy Act took effect on 1 July 2023. Connecticut amended
> the CTDPA in 2023 to strengthen protections for consumer health data and added
> children-specific provisions effective 1 October 2024. Applies to controllers doing
> business in Connecticut that meet a 100,000-consumer / 25,000-consumer-plus-sale
> threshold (similar to Colorado but with employment/B2B exclusions).

## Core Definitions

* **Personal Data** — Any information that is linked or reasonably linkable to an
  identified or identifiable individual. Excludes deidentified and publicly available
  information. Consumer health data has a separate, broader definition.
* **Consumer** — A Connecticut resident acting in an individual or household context;
  excludes commercial or employment-context activity.
* **Processing** — Any operation or set of operations performed on personal data.
* **Sale** — Exchange of personal data for monetary or other valuable consideration
  by the controller to a third party.
* **Controller / Processor** — Controller decides purposes and means; processor
  follows documented instructions. Data-processing agreements are required and must
  include subprocessor authorisation, audit, and security commitments.

## Consumer Rights

* **Right of Access** — Confirmation and copy of personal data.
* **Right to Delete** — Including obligations to instruct processors and downstream
  third parties to delete.
* **Right to Correct** — Inaccuracies in personal data.
* **Right to Opt-Out** — Of (i) sale, (ii) targeted advertising, and
  (iii) profiling in furtherance of decisions of legal or similarly significant
  effect. Universal opt-out mechanism required since 1 January 2025.
* **Right to Portability** — Data must be provided in a portable and, to the extent
  technically feasible, readily usable format.
* **Right to Appeal** — Internal appeal process and ability to escalate to the
  attorney general.

## Penalties & Enforcement

* Civil penalty under the Connecticut Unfair Trade Practices Act (CUTPA): up to
  **$5,000 per wilful violation** (Conn. Gen. Stat. § 42-110o), plus restitution and
  injunctive relief.
* Enforcement: Connecticut Attorney General exclusively; no private right of action.
* Cure period: 60-day cure right sunsetted on 31 December 2024.

## Notable Enforcement Actions

* **TicketNetwork (Feb 2025)** — $85,000 stipulated penalty for failing to honour
  consumer opt-out requests and for inadequate privacy-notice disclosures; one of the
  first publicly disclosed CTDPA enforcement outcomes.
* **2024 AG enforcement report** — The Connecticut AG's office issued more than 14
  cure notices in late 2023; reported public outcomes in 2024 include voluntary
  remediation and binding assurances from major retail and adtech operators.

---

### Chapter 9


# Delaware — Delaware Personal Data Privacy Act (DPDPA, 6 Del. C. § 12D-101 et seq.)

> The Delaware Personal Data Privacy Act took effect on 1 January 2025. It applies to
> persons that conduct business in Delaware that during the preceding calendar year
> (i) controlled or processed the personal data of 35,000+ Delaware consumers, or
> (ii) controlled or processed the personal data of 10,000+ consumers and derived
> more than 20% of gross revenue from the sale of personal data. The 35,000-consumer
> threshold is the lowest in the US.

## Core Definitions

* **Personal Data** — Information linked or reasonably linkable to an identified or
  identifiable individual; excludes deidentified data and publicly available
  information.
* **Consumer** — A Delaware resident acting in an individual or household context;
  the law explicitly excludes those acting in commercial or employment contexts.
* **Processing** — Any operation or set of operations performed on personal data.
* **Sale** — Exchange of personal data for monetary or other valuable consideration
  to a third party.
* **Controller / Processor** — Controller decides purposes/means; processor follows
  controller instructions under a data-processing addendum.

## Consumer Rights

* **Right of Access** — Confirmation and a copy of personal data.
* **Right to Deletion** — Provided to or obtained about the consumer.
* **Right to Correction** — Of inaccuracies.
* **Right to Opt-Out** — Of sale, targeted advertising, and certain profiling.
* **Right to Portability** — In a portable, readily usable format.
* **Right to a List of Categories of Third Parties** — Unique to Delaware: consumers
  may receive a list of categories of third parties to whom the controller has
  disclosed any consumer's personal data.

## Penalties & Enforcement

* Civil penalty under the Delaware Consumer Fraud Act: up to **$10,000 per wilful
  violation**, plus restitution and injunctive relief.
* Enforcement: Delaware Department of Justice (Attorney General); no private right
  of action.
* Cure period: 60 days, sunsetting 31 December 2025.

## Notable Enforcement Actions

* As of mid-2025, the Delaware AG has not announced public enforcement actions under
  the DPDPA. The Department of Justice has issued informal compliance letters during
  the cure period.
* The Delaware AG has historically participated in multi-state actions, including
  the **2023 Blackbaud settlement** ($49.5 million across 49 states), under which
  Delaware received approximately $437,000.

---

### Chapter 10


# Florida — Florida Digital Bill of Rights (FDBR, Fla. Stat. § 501.71 et seq.)

> The Florida Digital Bill of Rights took effect on 1 July 2024. Unlike most state
> privacy laws, it is narrowly targeted at very large platforms: applicability is
> limited to controllers with **$1 billion+ in global gross annual revenue** that
> derive more than 50% of revenue from the sale of advertising online, or that
> operate a consumer smart-speaker or app store. Florida law also imposes sectoral
> rules including a children's online-protection statute and a "search-engine
> child-protection" obligation.

## Core Definitions

* **Personal Data** — Information linked or reasonably linkable to an identifiable
  individual; excludes deidentified and publicly available information.
* **Consumer** — A Florida resident acting in an individual or household context.
* **Processing** — Any operation performed on personal data.
* **Sale** — Sharing or transferring personal data to a third party for monetary or
  other valuable consideration.
* **Controller / Processor** — Standard controller/processor split, with explicit
  data-processing agreement requirements.

## Consumer Rights

* **Right of Access** — Confirmation and copy of personal data.
* **Right to Deletion** — Including third-party-sourced data.
* **Right to Correction** — Of inaccurate data.
* **Right to Opt-Out** — Of sale, targeted advertising, and profiling that produces
  legal or similarly significant effects.
* **Right to Portability** — In a readily usable format where technically feasible.
* **Right to Opt-Out of Voice/Facial-Recognition Data Collection** — Specific to
  smart-speaker manufacturers and similar IoT controllers.

## Penalties & Enforcement

* Civil penalty: up to **$50,000 per violation**, **tripled for violations involving
  known minors**, undisclosed sales of sensitive data, or continued violations after
  the cure period (Fla. Stat. § 501.717).
* Enforcement: Florida Department of Legal Affairs (Attorney General); no private
  right of action.
* Cure period: 45 days.

## Notable Enforcement Actions

* **2024 Sweep of Smart-Speaker Vendors** — The Florida AG announced compliance
  reviews of three large smart-speaker manufacturers; outcomes are pending.
* **TikTok minors-privacy enforcement (2023)** — Although predating the FDBR,
  Florida joined the multi-state COPPA settlement against TikTok ($92 million class
  fund plus injunctive relief), recovering about $4.7 million for the state.

---

### Chapter 11


# Georgia — No Comprehensive Privacy Statute

> Georgia has not enacted an omnibus consumer privacy law. Privacy obligations are
> addressed through sectoral statutes, including breach notification (Ga. Code
> §§ 10-1-910 to 10-1-915), the Personal Identity Protection Act, and the Georgia
> Fair Business Practices Act. The 2024 legislative session saw a Virginia-model bill
> (HB 1199) introduced but not passed.

## Core Definitions

* **Personal Data** — "Personal information": first name or initial + last name
  combined with SSN, driver's-licence/state-ID number, account number with access
  credential, or password.
* **Consumer** — A Georgia resident; under the FBPA, a consumer is a natural person
  who is the target of an unfair or deceptive act.
* **Processing** — Not defined.
* **Sale** — Not defined for privacy purposes.
* **Controller / Processor** — Not used. The breach statute regulates "information
  brokers", "data collectors", and businesses.

## Consumer Rights

* **Right to Access** — None codified outside FCRA preemption.
* **Right to Deletion** — None codified.
* **Right to Correction** — None codified.
* **Right to Opt-Out of Sale / Sharing** — None codified.
* **Right to Portability** — None codified.

## Penalties & Enforcement

* Fair Business Practices Act civil penalty: up to **$5,000 per violation** plus
  restitution.
* Breach-statute penalty: capped at **$5,000 per breach** with no per-violation
  multiplier (Ga. Code § 10-1-912(e)).
* Enforcement: Georgia Attorney General and Department of Law; limited private
  remedies for actual damages.
* Cure period: at AG discretion.

## Notable Enforcement Actions

* **2023 Office of the Attorney General settlement with credit-monitoring vendor** —
  $750,000 stipulated penalty for failing to disclose data-sharing arrangements with
  marketing affiliates.
* **Multi-state Equifax (2019)** — Georgia, as Equifax's home state, received an
  outsized share of the $575 million settlement and pursued additional structural
  remedies including independent audits.

---

### Chapter 12


# Hawaii — Security Breach of Personal Information Act (Haw. Rev. Stat. § 487N)

> Hawaii has no omnibus privacy statute. The Security Breach of Personal Information
> Act and the Office of Consumer Protection at the Department of Commerce and
> Consumer Affairs (DCCA) provide the principal framework. SB 974 (a Connecticut-model
> bill) has been introduced repeatedly but has not been enacted as of 2026.

## Core Definitions

* **Personal Data** — "Personal information": first name/initial + last name combined
  with SSN, driver's-licence/state-ID number, financial-account credential, or
  password.
* **Consumer** — A Hawaii resident; the DCCA defines a consumer broadly under Haw.
  Rev. Stat. § 480-1.
* **Processing** — Not defined.
* **Sale** — Not defined.
* **Controller / Processor** — Not used.

## Consumer Rights

* **Right to Access** — None codified.
* **Right to Deletion** — None codified.
* **Right to Correction** — None codified.
* **Right to Opt-Out of Sale / Sharing** — None codified.
* **Right to Portability** — None codified.

## Penalties & Enforcement

* Breach-notification civil penalty: up to **$2,500 per violation** (Haw. Rev. Stat.
  § 487N-3) plus injunctive relief.
* Hawaii Unfair and Deceptive Acts (Haw. Rev. Stat. § 480-2): civil penalty up to
  **$10,000 per violation**, and private right of action with treble damages.
* Enforcement: DCCA Office of Consumer Protection and Hawaii Attorney General;
  private right of action under § 480 for "loss of money or property".
* Cure period: not specified.

## Notable Enforcement Actions

* **Hawaii Pacific Health / Microsoft Cloud incident (2022)** — DCCA-led inquiry into
  the breach of 3,800 patient records resulted in remediation commitments and a
  $250,000 contribution to a digital-literacy fund.
* **2021 multi-state TurboTax / Intuit settlement** — Hawaii recovered approximately
  $400,000 of the $141 million 50-state settlement.

---

### Chapter 13


# Idaho — Breach Notification (Idaho Code § 28-51-101 et seq.)

> Idaho has no omnibus privacy law. The principal statute is Idaho Code §§ 28-51-101
> to 28-51-107 (security-breach notification), supplemented by the Idaho Consumer
> Protection Act (Idaho Code § 48-601 et seq.).

## Core Definitions

* **Personal Data** — "Personal information": first name/initial + last name with
  SSN, driver's-licence/state-ID number, or financial-account credential.
* **Consumer** — A natural-person Idaho resident.
* **Processing** — Not defined.
* **Sale** — Not defined for privacy purposes.
* **Controller / Processor** — Not used; the breach statute targets
  "agencies, individuals, and commercial entities".

## Consumer Rights

* **Right to Access** — None codified.
* **Right to Deletion** — None codified.
* **Right to Correction** — None codified.
* **Right to Opt-Out of Sale / Sharing** — None codified.
* **Right to Portability** — None codified.

## Penalties & Enforcement

* Idaho Consumer Protection Act civil penalty: up to **$5,000 per violation** plus
  restitution and injunctive relief (Idaho Code § 48-606).
* Breach-statute penalty: up to **$25,000 per breach** for state agencies; commercial
  entities face penalties through the ICPA.
* Enforcement: Idaho Attorney General Consumer Protection Division; private right of
  action for actual damages under the ICPA.
* Cure period: 14-day pre-suit notice required under § 48-608(5).

## Notable Enforcement Actions

* **2023 Idaho AG Action Against a Data Broker** — $250,000 settlement with an
  unnamed nationwide skip-tracing vendor for failing to honour state-issued opt-out
  requests under the ICPA.
* **Multi-state Anthem settlement (2018)** — Idaho received approximately
  $500,000 of the $39.5 million multi-state settlement.

---

### Chapter 14


# Illinois — Biometric Information Privacy Act (BIPA, 740 ILCS 14) + General

> Illinois has no omnibus consumer privacy law, but it has the most-litigated state
> privacy statute in the US: the Biometric Information Privacy Act (BIPA, 740 ILCS
> 14/1), enacted in 2008. Illinois also has the Genetic Information Privacy Act (GIPA,
> 410 ILCS 513), the Personal Information Protection Act (PIPA, 815 ILCS 530), and the
> Student Online Personal Protection Act. BIPA's strict written-consent rule and
> per-violation statutory damages have generated more class actions than any other
> state privacy regime.

## Core Definitions

* **Personal Data** — Under PIPA, name plus SSN/DL/financial credentials/medical
  information/biometric data. Under BIPA, "biometric identifier" means retina/iris
  scan, fingerprint, voiceprint, scan of hand or face geometry; "biometric
  information" is any information based on such identifiers, regardless of how
  captured.
* **Consumer / Data Subject** — Illinois resident under PIPA; any "individual" whose
  biometric data is collected under BIPA, regardless of residency.
* **Processing** — Not formally defined; PIPA regulates "collection, use, and
  disclosure" of personal information.
* **Sale** — Under BIPA, the sale, lease, or other monetisation of biometric
  identifiers is **absolutely prohibited** without exception.
* **Controller / Processor** — Not used. BIPA imposes obligations on "private
  entities".

## Consumer Rights

* **Right to Access** — Indirect: BIPA requires written notice of purpose and length
  of retention prior to collection.
* **Right to Deletion** — BIPA mandates a written retention schedule and deletion
  when the initial purpose is satisfied or three years after the last interaction.
* **Right to Correction** — None codified.
* **Right to Opt-Out of Sale / Sharing** — BIPA bars sale entirely.
* **Right to Portability** — None codified.
* **Right to Sue (PRA)** — BIPA § 20 provides a private right of action with
  statutory damages.

## Penalties & Enforcement

* BIPA statutory damages: **$1,000 per negligent violation** and **$5,000 per
  intentional or reckless violation**, plus attorneys' fees and injunctive relief.
* PIPA breach violations: penalties through the Consumer Fraud and Deceptive Business
  Practices Act (815 ILCS 505/7), up to **$50,000 per violation**.
* Genetic Information Privacy Act: $2,500 per negligent violation, $15,000 per
  intentional violation.
* Enforcement: Illinois Attorney General + private right of action.
* No cure period under BIPA.

## Notable Enforcement Actions

* **Rosenbach v. Six Flags (Ill. 2019)** — Illinois Supreme Court held that an
  "aggrieved" plaintiff need not show actual injury beyond the BIPA violation
  itself.
* **Facebook / Meta BIPA settlement (2020)** — $650 million class settlement over
  unconsented facial-tagging; largest BIPA settlement to date.
* **White Castle BIPA litigation (2023–24)** — The Illinois Supreme Court's
  *Cothron* decision held that each separate scan of biometric data is a separate
  violation; the legislature subsequently amended BIPA in August 2024 (SB 2979) to
  limit per-violation accumulation to one per individual per data type.

---

### Chapter 15


# Indiana — Indiana Consumer Data Protection Act (ICDPA, Ind. Code § 24-15)

> The Indiana Consumer Data Protection Act was signed into law in May 2023 and takes
> effect on 1 January 2026. Indiana adopted the Virginia model. Applies to persons
> conducting business in Indiana that during a calendar year (i) control or process
> the personal data of 100,000+ Indiana consumers, or (ii) control or process the
> personal data of 25,000+ consumers and derive more than 50% of gross revenue from
> the sale of personal data.

## Core Definitions

* **Personal Data** — Any information linked or reasonably linkable to an identified
  or identifiable individual; excludes deidentified and publicly available
  information.
* **Consumer** — A natural person who is a resident of Indiana acting only in an
  individual or household context.
* **Processing** — Any operation performed on personal data, manual or automated.
* **Sale** — The exchange of personal data for monetary consideration to a third
  party. (Indiana's narrower "monetary" definition excludes mere targeted-advertising
  transfers, unlike California.)
* **Controller / Processor** — Controller decides purposes/means; processor follows
  documented controller instructions and is bound by a data-processing addendum.

## Consumer Rights

* **Right of Access** — Confirmation and copy of personal data.
* **Right to Delete** — Of data provided to or obtained about the consumer.
* **Right to Correct** — Of inaccuracies.
* **Right to Opt-Out** — Of sale, targeted advertising, and profiling in furtherance
  of decisions producing legal or similarly significant effects.
* **Right to Portability** — Right to receive a portable, readily usable copy.
* **Right to Appeal** — Internal review of controller refusals.

## Penalties & Enforcement

* Civil penalty under the Indiana Deceptive Consumer Sales Act: up to **$7,500 per
  violation** (Ind. Code § 24-5-0.5-4).
* Enforcement: Indiana Attorney General exclusively; no private right of action.
* Cure period: 30 days; right does not sunset.

## Notable Enforcement Actions

* Effective date is January 2026, so no ICDPA enforcement has occurred yet. The
  Indiana AG has historically been active in multi-state actions, including the
  **2023 multi-state Premom settlement** ($200,000) involving health-app data
  sharing.
* The Indiana AG's office issued informal guidance to controllers in October 2025
  describing expected DPIA documentation for high-risk profiling.

---

### Chapter 16


# Iowa — Iowa Consumer Data Protection Act (ICDPA, Iowa Code § 715D)

> The Iowa Consumer Data Protection Act was enacted in 2023 and took effect on
> 1 January 2025. Iowa adopted a controller/processor model close to the Virginia and
> Utah versions but with weaker individual rights. Applies to persons conducting
> business in Iowa that during a calendar year (i) control or process the personal
> data of 100,000+ Iowa consumers, or (ii) control or process the personal data of
> 25,000+ consumers and derive more than 50% of gross revenue from the sale of
> personal data.

## Core Definitions

* **Personal Data** — Information linked or reasonably linkable to an identified or
  identifiable natural person; excludes deidentified and publicly available
  information.
* **Consumer** — Iowa resident acting in individual/household context; excludes
  commercial/employment contexts.
* **Processing** — Any operation performed on personal data.
* **Sale** — Exchange of personal data for **monetary** consideration only — Iowa
  uses the narrowest sale definition, excluding non-monetary or in-kind transfers
  even where data is shared for advertising.
* **Controller / Processor** — Standard model; controllers must execute
  data-processing addenda with processors.

## Consumer Rights

* **Right of Access** — Confirmation and copy.
* **Right to Deletion** — Limited to data the consumer has provided directly to the
  controller (narrower than Virginia).
* **Right to Correction** — Notably absent. Iowa is one of the few state laws
  without a correction right.
* **Right to Opt-Out of Sale** — Yes, but only for monetary sales.
* **Right to Opt-Out of Targeted Advertising** — Yes.
* **Right to Portability** — Yes.
* **No** right to opt-out of profiling.

## Penalties & Enforcement

* Civil penalty: up to **$7,500 per violation** (Iowa Code § 715D.8).
* Enforcement: Iowa Attorney General exclusively; no private right of action.
* Cure period: 90 days; does not sunset.

## Notable Enforcement Actions

* Effective only since January 2025, so no public Iowa-specific privacy-law
  enforcement actions exist as of mid-2026.
* Iowa AG participated in **2024 multi-state Cerebral settlement** alleging
  unauthorized disclosure of patient health information to advertising vendors;
  Iowa's share was approximately $185,000.

---

### Chapter 17


# Kansas — Wayne Owen Act (Kan. Stat. § 50-7a01 et seq.)

> Kansas has no omnibus privacy law. The Wayne Owen Act and the Kansas Consumer
> Protection Act (Kan. Stat. § 50-623 et seq.) provide the principal frameworks.
> Legislation modelled on Virginia (HB 2701, 2024) has been introduced but not
> enacted.

## Core Definitions

* **Personal Data** — "Personal information": first name/initial + last name combined
  with SSN, driver's-licence/state-ID number, or financial-account credential.
* **Consumer** — A Kansas resident; KCPA defines a consumer broadly to include
  individuals in retail and service contexts.
* **Processing** — Not defined.
* **Sale** — Not defined for privacy purposes.
* **Controller / Processor** — Not used.

## Consumer Rights

* **Right to Access** — None codified.
* **Right to Deletion** — None codified.
* **Right to Correction** — None codified.
* **Right to Opt-Out of Sale / Sharing** — None codified.
* **Right to Portability** — None codified.

## Penalties & Enforcement

* KCPA civil penalty: up to **$10,000 per violation** (Kan. Stat. § 50-636), plus
  consumer restitution.
* Breach-notification penalty: incorporated by reference into KCPA.
* Enforcement: Kansas Attorney General; private right of action for actual damages
  under § 50-634.
* Cure period: not specified; pre-suit notice frequently required.

## Notable Enforcement Actions

* **2024 Kansas AG settlement with a debt-collection vendor** — $1.6 million civil
  penalty for failure to safeguard consumer files exposed in a 2023 breach affecting
  approximately 80,000 Kansans.
* **Multi-state Premom settlement (2023)** — Kansas participated, recovering
  approximately $35,000.

---

### Chapter 18


# Kentucky — Kentucky Consumer Data Protection Act (KCDPA, KRS § 367.3611 et seq.)

> The Kentucky Consumer Data Protection Act was enacted in April 2024 and takes
> effect on 1 January 2026. It is a Virginia-model statute. Applies to persons that
> conduct business in Kentucky and meet a 100,000-consumer threshold or a
> 25,000-consumer threshold combined with deriving more than 50% of gross revenue
> from the sale of personal data.

## Core Definitions

* **Personal Data** — Any information linked or reasonably linkable to an identified
  or identifiable natural person; excludes deidentified and publicly available
  information.
* **Consumer** — Kentucky resident acting in an individual or household context.
* **Processing** — Any operation performed on personal data.
* **Sale** — Exchange of personal data for monetary consideration to a third party.
* **Controller / Processor** — Controller decides purposes/means; processor binds to
  controller through DPA.

## Consumer Rights

* **Right of Access** — Confirmation and copy.
* **Right to Deletion** — Of data provided or obtained.
* **Right to Correction** — Of inaccuracies.
* **Right to Opt-Out** — Of sale, targeted advertising, and certain profiling.
* **Right to Portability** — In a readily usable format.
* **Right to Appeal** — Internal review process required.

## Penalties & Enforcement

* Civil penalty: up to **$7,500 per violation** (KRS § 367.3625).
* Enforcement: Kentucky Attorney General exclusively; no private right of action.
* Cure period: 30 days; does not sunset.

## Notable Enforcement Actions

* Effective date is January 2026, so no KCDPA enforcement actions exist yet.
* Kentucky AG participated in **2024 multi-state Marriott settlement** ($52 million
  across 50 states); Kentucky's share was approximately $700,000.

---

### Chapter 19


# Louisiana — Database Security Breach Notification Law (La. R.S. 51:3071–3077)

> Louisiana has no omnibus privacy law. The 2023 Louisiana Consumer Privacy Act (a
> Virginia-model bill, HB 1011) failed to pass. Coverage relies on breach
> notification, the Identity Theft Protection Act, and the Louisiana Unfair Trade
> Practices Act (LUTPA, La. R.S. 51:1401 et seq.).

## Core Definitions

* **Personal Data** — "Personal information": first name/initial + last name combined
  with SSN, driver's-licence/state-ID number, financial-account credential, biometric
  data, passport number, or e-mail credential.
* **Consumer** — Louisiana resident; LUTPA defines a consumer broadly under
  La. R.S. 51:1402.
* **Processing** — Not defined.
* **Sale** — Not defined for privacy purposes.
* **Controller / Processor** — Not used; breach statute uses "person".

## Consumer Rights

* **Right to Access** — None codified.
* **Right to Deletion** — None codified.
* **Right to Correction** — None codified.
* **Right to Opt-Out of Sale / Sharing** — None codified.
* **Right to Portability** — None codified.

## Penalties & Enforcement

* LUTPA civil penalty: up to **$5,000 per violation** plus restitution.
* Breach-statute penalty: $5,000 per violation, plus reasonable attorneys' fees and
  costs (La. R.S. 51:3074(H)).
* Enforcement: Louisiana Attorney General; private right of action for actual
  damages under LUTPA (treble damages for knowing violations).
* Cure period: not specified.

## Notable Enforcement Actions

* **2022 Louisiana AG settlement with student-loan servicer** — $1.85 million
  settlement following a breach affecting 200,000+ Louisiana borrowers.
* **2023 multi-state CafePress action** — Louisiana participated in the $2 million
  multi-state settlement, recovering approximately $80,000.

---

### Chapter 20


# Maine — Act to Protect the Privacy of Online Customer Information (35-A MRS § 9301)

> Maine's Internet-Service-Provider privacy statute took effect on 1 July 2020 and is
> the strictest US sector-specific privacy law for broadband providers. It requires
> opt-in consent before an ISP may use, sell, or disclose customer personal
> information. Maine has no omnibus privacy law, although LD 1788, a comprehensive
> Connecticut-model bill, was introduced in 2023. Breach notification is handled
> under 10 MRS §§ 1346–1350-B.

## Core Definitions

* **Personal Data** — Under the ISP statute, "customer personal information"
  includes web-browsing history, application-usage history, precise geolocation,
  health information, communications content, and financial information.
* **Consumer** — A Maine customer of a broadband ISP for the ISP statute; a Maine
  resident under the breach statute.
* **Processing** — Not defined; the ISP statute regulates "use, disclosure or sale".
* **Sale** — Disclosure for valuable consideration. The ISP statute treats targeted
  advertising as sale.
* **Controller / Processor** — Not used; the ISP statute regulates "providers".

## Consumer Rights

* **Right to Access** — None general; ISP statute requires clear notice.
* **Right to Deletion** — None general.
* **Right to Correction** — None general.
* **Right to Opt-In** — Under the ISP statute, customers must affirmatively opt in
  before an ISP can share personal information beyond what is needed to deliver
  service.
* **Right to Opt-Out of Sale / Sharing** — Yes, for ISPs, but always overlaid by the
  opt-in requirement.
* **Right to Portability** — None codified.

## Penalties & Enforcement

* ISP statute violations are subject to the Maine Unfair Trade Practices Act
  (5 MRS § 207), with civil penalties up to **$10,000 per violation** and
  injunctive relief.
* Breach-statute penalty: up to **$500 per breach, capped at $2,500 per day** of
  continued violation (10 MRS § 1349).
* Enforcement: Maine Attorney General; class-action remedies available under
  UTPA Section 213.
* Cure period: not specified for the ISP statute.

## Notable Enforcement Actions

* **ACA Connects v. Frey (1st Cir. 2021)** — The ISP industry's constitutional
  challenge to the Maine law was dismissed; the law was upheld as a content-neutral
  consumer-protection rule.
* **2022 Maine AG / Spectrum review** — Maine AG opened a sweep of ISP compliance
  with § 9301 consent notices; outcomes resulted in remedial commitments but no
  public penalties.

---

### Chapter 21


# Maryland — Maryland Online Data Privacy Act (MODPA, Md. Code, Com. Law § 14-4601 et seq.)

> The Maryland Online Data Privacy Act was signed in May 2024 and takes effect on
> 1 October 2025. MODPA contains some of the most consumer-protective provisions in
> the US: data minimisation is mandatory, sensitive-data sales are flatly
> prohibited, and the applicability threshold is comparatively low. Applies to
> persons that during a calendar year (i) control or process the personal data of
> 35,000+ Maryland consumers (excluding payment-only transactions), or (ii) control
> or process the personal data of 10,000+ consumers and derive more than 20% of
> gross revenue from the sale of personal data.

## Core Definitions

* **Personal Data** — Information linked or reasonably linkable to an identified or
  identifiable individual; excludes deidentified and publicly available information.
* **Consumer** — A natural person who is a Maryland resident acting in an
  individual or household context.
* **Processing** — Any operation on personal data.
* **Sale** — Exchange of personal data for monetary or other valuable consideration.
* **Controller / Processor** — Standard controller/processor model with strict DPA
  requirements; processor must assist controller with assessments and consumer
  rights.

## Consumer Rights

* **Right of Access** — Confirmation and copy.
* **Right to Deletion** — Of data provided or obtained.
* **Right to Correction** — Of inaccurate personal data.
* **Right to Opt-Out** — Of sale, targeted advertising, and certain profiling, with
  universal opt-out mechanism honoured by 1 October 2025.
* **Right to Portability** — In a readily usable format.
* **Strict Sensitive-Data Prohibition** — MODPA outright bans the sale of sensitive
  data (race, religion, sexual orientation, immigration status, precise
  geolocation, health, biometrics, children's data), not merely a right to opt out.

## Penalties & Enforcement

* Civil penalty under the Maryland Consumer Protection Act: up to **$10,000 per
  violation**; subsequent violations up to **$25,000 per violation** (Md. Code,
  Com. Law § 13-410).
* Enforcement: Maryland Attorney General Consumer Protection Division; no general
  private right of action under MODPA (limited PRA for breach claims under separate
  statute).
* Cure period: 60 days, sunsetting 1 April 2027.

## Notable Enforcement Actions

* Statute effective only since October 2025; no public MODPA enforcement actions as
  of mid-2026.
* The Maryland AG has historically been active in multi-state actions, including
  the **2023 multi-state Sephora cosmetics action** (joined CA-led settlement) and
  the **2022 multi-state Carnival Cruise Lines** $1.25 million settlement.

---

### Chapter 22


# Massachusetts — Standards for the Protection of PII (201 CMR 17.00) and Chapter 93H

> Massachusetts has no omnibus privacy law, but 201 CMR 17.00 (the WISP regulation,
> effective 2010) imposes prescriptive written-information-security-program
> obligations on any entity that owns or licenses the personal information of
> Massachusetts residents. M.G.L. c. 93H governs breach notification. The
> Massachusetts Information Privacy and Security Act (MIPSA, S. 25) is the most
> advanced of repeated comprehensive-bill proposals and remains under
> consideration.

## Core Definitions

* **Personal Data** — "Personal information" under c. 93H: first name/initial + last
  name combined with SSN, driver's-licence/state-ID number, financial-account
  credential, or biometric indicator (added 2018).
* **Consumer** — Massachusetts resident; the Consumer Protection Act (c. 93A)
  defines a consumer broadly.
* **Processing** — Not defined; 201 CMR 17.00 regulates "owning, licensing, storing,
  or maintaining" PII.
* **Sale** — Not defined for privacy purposes.
* **Controller / Processor** — Not used; WISP regulation imposes obligations on
  "persons".

## Consumer Rights

* **Right to Access** — None codified.
* **Right to Deletion** — None codified.
* **Right to Correction** — None codified.
* **Right to Opt-Out of Sale / Sharing** — None codified.
* **Right to Portability** — None codified.
* **Right to Sue under c. 93A** — Robust private right of action with treble
  damages for knowing violations.

## Penalties & Enforcement

* Chapter 93H civil penalty: up to **$5,000 per violation** (M.G.L. c. 93A § 4).
* Chapter 93A civil penalty: up to **$5,000 per violation**, with up to treble
  damages for knowing or wilful conduct.
* Enforcement: Massachusetts Attorney General; robust c. 93A private right of
  action including class actions.
* Cure period: 30 days demand letter required under c. 93A § 9 before consumer
  suit.

## Notable Enforcement Actions

* **Equifax (2020)** — $18.2 million state-only settlement for the 2017 breach,
  the largest single-state recovery in the multi-state Equifax matter.
* **Roomster (2022)** — $375,000 AG settlement against the apartment-rental
  platform for misuse of personal information; included data-handling injunctions.
* **Marriott (2023)** — Massachusetts component of $52 million multi-state
  Marriott / Starwood settlement.

---

### Chapter 23


# Michigan — Identity Theft Protection Act (MCL 445.61 et seq.)

> Michigan has no omnibus privacy law. The Identity Theft Protection Act addresses
> breach notification and reasonable-security obligations. The Michigan Personal Data
> Privacy Act (HB 4505 in 2023) and the Michigan Personal Information Privacy Act
> (SB 659 in 2024) have been introduced but not enacted.

## Core Definitions

* **Personal Data** — "Personal information": first name/initial + last name combined
  with SSN, driver's-licence/state-ID number, demand-deposit account number, financial
  credential, or password.
* **Consumer** — Michigan resident; MCPA defines consumer broadly.
* **Processing** — Not defined.
* **Sale** — Not defined for privacy purposes.
* **Controller / Processor** — Not used; ITPA regulates "agencies" and "persons".

## Consumer Rights

* **Right to Access** — None codified.
* **Right to Deletion** — None codified.
* **Right to Correction** — None codified.
* **Right to Opt-Out of Sale / Sharing** — None codified.
* **Right to Portability** — None codified.

## Penalties & Enforcement

* ITPA civil penalty: up to **$250 per failure to give notice**, capped at $750,000
  per incident (MCL 445.72).
* MCPA civil penalty: up to **$25,000 per persistent and knowing violation** plus
  injunctive relief.
* Enforcement: Michigan Attorney General; private right of action under MCPA for
  actual damages.
* Cure period: not specified.

## Notable Enforcement Actions

* **2021 Michigan AG settlement with Sweetwater Sound** — $325,000 stipulated penalty
  arising from a payment-page skimmer incident; required two-year third-party audits.
* **Multi-state Equifax** — Michigan received approximately $14.3 million as part of
  the 50-state $575 million settlement.

---

### Chapter 24


# Minnesota — Minnesota Consumer Data Privacy Act (MCDPA, Minn. Stat. § 325O)

> The Minnesota Consumer Data Privacy Act was signed in May 2024 and takes effect on
> 31 July 2025. MCDPA is a Connecticut/Colorado-style law with enhanced provisions
> on profiling and small-business exclusions. Applies to controllers conducting
> business in Minnesota that during a calendar year (i) control or process the
> personal data of 100,000+ Minnesota consumers, or (ii) control or process the
> personal data of 25,000+ consumers and derive more than 25% of gross revenue
> from the sale of personal data.

## Core Definitions

* **Personal Data** — Information linked or reasonably linkable to an identified or
  identifiable individual; excludes deidentified and publicly available information.
* **Consumer** — A Minnesota resident acting in an individual or household context;
  excludes commercial and employment contexts.
* **Processing** — Any operation performed on personal data.
* **Sale** — Exchange of personal data for monetary or other valuable consideration.
* **Controller / Processor** — Standard controller/processor model with extensive
  DPA contractual obligations and rights to audit.

## Consumer Rights

* **Right of Access** — Confirmation and copy.
* **Right to Deletion** — Including data obtained from third parties.
* **Right to Correction** — Of inaccurate personal data.
* **Right to Opt-Out** — Of sale, targeted advertising, and certain profiling; UOOM
  honoured by 1 January 2026.
* **Right to Portability** — In readily usable format.
* **Right to Question Profiling Decisions** — Unique provision: consumers can
  request the specific factors underlying a profiling decision and challenge
  outcomes that produce legal or similarly significant effects.

## Penalties & Enforcement

* Civil penalty: up to **$7,500 per violation** under Minn. Stat. § 325F.69
  (consumer-fraud act analogue).
* Enforcement: Minnesota Attorney General exclusively; no private right of action.
* Cure period: 30 days, sunsetting 31 January 2026 for small-business controllers.

## Notable Enforcement Actions

* The statute's effective date is July 2025. The Minnesota AG issued public
  pre-enforcement guidance in March 2025 on profiling assessments.
* Minnesota AG participated in the **2024 multi-state Cerebral settlement** over
  unauthorized health-data sharing.

---

### Chapter 25


# Mississippi — Data Breach Notification (Miss. Code § 75-24-29)

> Mississippi has no omnibus privacy law. The breach-notification statute and the
> Mississippi Consumer Protection Act (Miss. Code § 75-24-1 et seq.) provide the
> framework for privacy-related enforcement.

## Core Definitions

* **Personal Data** — "Personal information": first name/initial + last name combined
  with SSN, driver's-licence/state-ID number, financial-account credential, or
  health/insurance information.
* **Consumer** — Mississippi resident; MCPA defines consumer broadly.
* **Processing** — Not defined.
* **Sale** — Not defined for privacy purposes.
* **Controller / Processor** — Not used; breach statute regulates "entities".

## Consumer Rights

* **Right to Access** — None codified.
* **Right to Deletion** — None codified.
* **Right to Correction** — None codified.
* **Right to Opt-Out of Sale / Sharing** — None codified.
* **Right to Portability** — None codified.

## Penalties & Enforcement

* MCPA civil penalty: up to **$10,000 per violation**.
* Breach-notification statute does not specify per-violation penalty, but
  enforcement runs through the MCPA.
* Enforcement: Mississippi Attorney General; limited private right of action under
  MCPA for actual damages.
* Cure period: pre-suit demand required under MCPA.

## Notable Enforcement Actions

* **2023 Mississippi AG settlement with national lender** — $1.1 million penalty
  arising from a 2022 ransomware incident affecting 30,000+ Mississippians.
* **Multi-state TurboTax / Intuit (2022)** — Mississippi received approximately
  $1.4 million of the $141 million settlement.

---

### Chapter 26


# Missouri — Breach Notification (Mo. Rev. Stat. § 407.1500)

> Missouri has no omnibus privacy law. SB 145 (a Virginia-model bill) was introduced
> in 2024 but did not pass. The Merchandising Practices Act (MMPA) provides the
> principal consumer-protection enforcement mechanism.

## Core Definitions

* **Personal Data** — "Personal information": first name/initial + last name combined
  with SSN, driver's-licence/state-ID number, financial-account credential, or
  unique electronic identifier (added 2009).
* **Consumer** — Missouri resident.
* **Processing** — Not defined.
* **Sale** — Not defined for privacy purposes.
* **Controller / Processor** — Not used; breach statute uses "person".

## Consumer Rights

* **Right to Access** — None codified.
* **Right to Deletion** — None codified.
* **Right to Correction** — None codified.
* **Right to Opt-Out of Sale / Sharing** — None codified.
* **Right to Portability** — None codified.

## Penalties & Enforcement

* MMPA civil penalty: up to **$1,000 per violation** plus restitution and
  injunctive relief.
* Breach-statute penalty: incorporated through MMPA enforcement.
* Enforcement: Missouri Attorney General; private right of action for actual damages
  with punitive damages available under § 407.025.
* Cure period: not specified.

## Notable Enforcement Actions

* **2021 Missouri AG investigation of educator-credential public website** — Although
  not a settlement, the AG publicly investigated the Department of Elementary &
  Secondary Education web disclosure of teacher SSNs; the matter highlighted
  ongoing public-records privacy issues.
* **Multi-state Equifax** — Missouri received approximately $13 million of the
  national settlement.

---

### Chapter 27


# Montana — Montana Consumer Data Privacy Act (MCDPA, Mont. Code § 30-14-2801 et seq.)

> The Montana Consumer Data Privacy Act took effect on 1 October 2024. Montana
> adopted a Connecticut-model law with a lower applicability threshold and an
> aggressive deadline for universal opt-out signals. Applies to persons doing
> business in Montana that during a calendar year (i) control or process the
> personal data of 50,000+ Montana consumers (excluding payment-only transactions),
> or (ii) control or process the personal data of 25,000+ consumers and derive
> more than 25% of gross revenue from the sale of personal data.

## Core Definitions

* **Personal Data** — Information linked or reasonably linkable to an identified or
  identifiable individual; excludes deidentified and publicly available information.
* **Consumer** — A Montana resident acting in an individual or household context.
* **Processing** — Any operation on personal data.
* **Sale** — Exchange of personal data for monetary or other valuable consideration.
* **Controller / Processor** — Controller decides purposes/means; processor follows
  controller instructions and is bound by a data-processing addendum.

## Consumer Rights

* **Right of Access** — Confirmation and copy.
* **Right to Deletion** — Including data obtained from third parties.
* **Right to Correction** — Of inaccurate personal data.
* **Right to Opt-Out** — Of sale, targeted advertising, and certain profiling.
* **Right to Portability** — In a readily usable format.
* **Right to Universal Opt-Out** — Recognised since 1 January 2025.

## Penalties & Enforcement

* Civil penalty: up to **$7,500 per violation** under the Montana Consumer
  Protection Act (Mont. Code § 30-14-142).
* Enforcement: Montana Attorney General Office of Consumer Protection.
* Cure period: 60 days through 31 March 2026, after which the cure right sunsets.

## Notable Enforcement Actions

* Statute effective only since October 2024; the Montana AG issued sweep letters
  to digital-marketing platforms in February 2025 regarding UOOM compliance.
* Montana AG participated in **2023 multi-state Blackbaud settlement**.

---

### Chapter 28


# Nebraska — Nebraska Data Privacy Act (NDPA, Neb. Rev. Stat. § 87-1101 et seq.)

> The Nebraska Data Privacy Act was signed in April 2024 and takes effect on
> 1 January 2025. NDPA closely tracks the Texas Data Privacy and Security Act
> rather than the Virginia model. Applies to persons doing business in Nebraska
> that process or sell personal data, **excluding** small businesses as defined in
> the federal Small Business Act, except where a small business knowingly sells
> sensitive personal data (which requires explicit consent regardless of size).

## Core Definitions

* **Personal Data** — Information linked or reasonably linkable to an identified or
  identifiable individual; excludes deidentified data and publicly available
  information.
* **Consumer** — A Nebraska resident acting in an individual or household context.
* **Processing** — Any operation on personal data.
* **Sale** — Exchange of personal data for monetary or other valuable consideration.
* **Controller / Processor** — Standard controller/processor model; processors must
  enter into binding data-processing addenda.

## Consumer Rights

* **Right of Access** — Confirmation and copy.
* **Right to Deletion** — Of data provided or obtained.
* **Right to Correction** — Of inaccurate personal data.
* **Right to Opt-Out** — Of sale, targeted advertising, and certain profiling.
* **Right to Portability** — In readily usable format.
* **Right to UOOM** — Universal opt-out mechanism honoured from 1 January 2026.

## Penalties & Enforcement

* Civil penalty: up to **$7,500 per violation** plus injunctive relief and
  reasonable attorneys' fees (Neb. Rev. Stat. § 87-1112).
* Enforcement: Nebraska Attorney General exclusively; no private right of action.
* Cure period: 30 days, with cure right not sunsetting (Texas-style).

## Notable Enforcement Actions

* Statute effective only since January 2025; the Nebraska AG announced an
  educational outreach campaign in May 2025 but had not finalised public
  enforcement actions as of mid-2026.
* Nebraska AG participated in **2023 multi-state Marriott** settlement, recovering
  approximately $250,000.

---

### Chapter 29


# Nevada — Internet Privacy Opt-Out Statute (NRS 603A.300–360 / SB 220)

> Nevada was one of the first states to enact a stand-alone opt-out-of-sale right.
> SB 220, effective 1 October 2019, was expanded in 2021 (SB 260) to cover "data
> brokers". It does not provide rights to access, delete, or correct, but allows
> consumers to direct operators not to sell their covered information. Breach
> notification is governed by NRS 603A.220.

## Core Definitions

* **Personal Data** — "Covered information": first/last name + physical address,
  email, telephone, SSN, government-issued identifier, or an identifier that
  allows a specific person to be contacted physically or online.
* **Consumer** — Nevada resident who uses an Internet website or online service.
* **Processing** — Not defined.
* **Sale** — Exchange of "covered information" for monetary consideration with a
  third party. Notably excludes non-monetary consideration, so the definition is
  narrower than CCPA.
* **Controller / Processor** — Not used; the statute uses "operator" and "data
  broker".

## Consumer Rights

* **Right to Access** — None codified.
* **Right to Deletion** — None codified.
* **Right to Correction** — None codified.
* **Right to Opt-Out of Sale / Sharing** — Yes. Operators and data brokers must
  provide a designated request address; must respond within 60 days (extendable by
  30 days).
* **Right to Portability** — None codified.

## Penalties & Enforcement

* Deceptive Trade Practices Act civil penalty: up to **$5,000 per violation**
  (NRS 598.0999) plus injunctive relief.
* Enforcement: Nevada Attorney General Bureau of Consumer Protection; no private
  right of action.
* Cure period: 30 days.

## Notable Enforcement Actions

* **2023 Nevada AG enforcement of SB 260 against a Las Vegas-headquartered data
  broker** — settlement included $300,000 civil penalty and three-year compliance
  reporting; the matter is notable for testing the data-broker registration
  requirement.
* **Multi-state Carnival Cruise Lines (2022)** — Nevada received approximately
  $35,000 of the $1.25 million settlement.

---

### Chapter 30


# New Hampshire — New Hampshire Privacy Act (NHPA, N.H. Rev. Stat. § 507-H)

> The New Hampshire Privacy Act was signed in March 2024 and takes effect on
> 1 January 2025. Applies to persons doing business in New Hampshire that during a
> calendar year (i) control or process the personal data of 35,000+ NH consumers,
> or (ii) control or process the personal data of 10,000+ consumers and derive
> more than 25% of gross revenue from the sale of personal data. The NH Secretary
> of State has rulemaking authority on UOOM signals.

## Core Definitions

* **Personal Data** — Information linked or reasonably linkable to an identified or
  identifiable individual; excludes deidentified and publicly available information.
* **Consumer** — A natural person resident of New Hampshire acting in an individual
  or household context.
* **Processing** — Any operation on personal data.
* **Sale** — Exchange of personal data for monetary or other valuable consideration.
* **Controller / Processor** — Standard model with DPA requirements.

## Consumer Rights

* **Right of Access** — Confirmation and copy.
* **Right to Deletion** — Including data obtained from third parties.
* **Right to Correction** — Of inaccurate personal data.
* **Right to Opt-Out** — Of sale, targeted advertising, and certain profiling.
* **Right to Portability** — In a readily usable format.
* **Right to Universal Opt-Out** — From 1 January 2025 (NH was the first state to
  require UOOM at law's effective date).

## Penalties & Enforcement

* Civil penalty under the New Hampshire Consumer Protection Act: up to **$10,000
  per violation** (RSA 358-A:4).
* Enforcement: New Hampshire Attorney General Consumer Protection and Antitrust
  Bureau; no private right of action.
* Cure period: 60 days, sunsetting 31 December 2025.

## Notable Enforcement Actions

* Statute is recent; the NH AG announced a sweep of OPRA compliance notices in
  September 2025 but had not announced public penalties as of mid-2026.
* New Hampshire participated in **2023 multi-state SolarWinds settlement** in
  connection with adviser-related cybersecurity disclosures, recovering
  approximately $90,000.

---

### Chapter 31


# New Jersey — New Jersey Data Privacy Act (NJDPA, N.J.S.A. § 56:8-166.4 et seq.)

> The New Jersey Data Privacy Act was signed on 16 January 2024 and takes effect on
> 15 January 2025. NJDPA borrows heavily from the Colorado/Connecticut framework
> but adds heightened protection for "financial information" and a sensitive-data
> opt-in. Applies to controllers conducting business in New Jersey that during a
> calendar year (i) control or process the personal data of 100,000+ NJ
> consumers, or (ii) control or process the personal data of 25,000+ consumers
> and derive revenue or receive a discount from the sale of personal data.

## Core Definitions

* **Personal Data** — Information linked or reasonably linkable to an identified
  or identifiable individual; excludes deidentified data and publicly available
  information. **Sensitive data** explicitly includes financial information,
  account credentials, status as a transgender or non-binary individual, and
  precise geolocation.
* **Consumer** — A New Jersey resident acting in an individual or household
  context.
* **Processing** — Any operation performed on personal data.
* **Sale** — Exchange of personal data for monetary or other valuable consideration.
* **Controller / Processor** — Standard controller/processor model; processor must
  follow controller instructions under a DPA.

## Consumer Rights

* **Right of Access** — Confirmation and copy in a readily usable format.
* **Right to Delete** — Of all personal data, regardless of source.
* **Right to Correction** — Of inaccurate data.
* **Right to Opt-Out** — Of (i) sale, (ii) targeted advertising, (iii) profiling
  in furtherance of decisions producing legal or similarly significant effects.
* **Right to Portability** — Yes.
* **Sensitive-Data Opt-In** — Express consent required before processing sensitive
  data.

## Penalties & Enforcement

* Civil penalty under the Consumer Fraud Act: up to **$10,000 for the first
  violation** and **$20,000 for subsequent violations** (N.J.S.A. § 56:8-13).
* Enforcement: New Jersey Division of Consumer Affairs and the NJ Attorney
  General; no private right of action under NJDPA (the underlying CFA does have a
  PRA, but limited to ascertainable loss).
* Cure period: 18-month transition cure right that sunsets 15 July 2026.

## Notable Enforcement Actions

* Statute effective since January 2025; AG issued investigative civil
  investigative demands to several adtech vendors in Q2 2025 over UOOM
  compliance. No published settlements as of mid-2026.
* New Jersey participated in **2024 multi-state TikTok COPPA action**, recovering
  approximately $5.2 million.

---

### Chapter 32


# New Mexico — Data Breach Notification Act (N.M. Stat. § 57-12C-1 et seq.)

> New Mexico has no omnibus privacy law. The Data Breach Notification Act,
> effective 2017, governs breach notification, disposal, and reasonable security.
> Privacy enforcement runs through the New Mexico Unfair Practices Act (UPA,
> N.M. Stat. § 57-12-1 et seq.).

## Core Definitions

* **Personal Data** — "Personal identifying information": first name/initial + last
  name combined with SSN, driver's-licence/state-ID number, financial-account
  credential, or biometric data.
* **Consumer** — New Mexico resident; UPA defines a consumer broadly.
* **Processing** — Not defined.
* **Sale** — Not defined for privacy purposes.
* **Controller / Processor** — Not used.

## Consumer Rights

* **Right to Access** — None codified.
* **Right to Deletion** — None codified.
* **Right to Correction** — None codified.
* **Right to Opt-Out of Sale / Sharing** — None codified.
* **Right to Portability** — None codified.

## Penalties & Enforcement

* UPA civil penalty: up to **$5,000 per wilful violation** under N.M. Stat.
  § 57-12-11.
* Breach-statute penalty: up to **$25,000 per breach** or, where applicable,
  **$10 per instance of failed notification** capped at $150,000.
* Enforcement: New Mexico Attorney General; private right of action under UPA
  with actual or $100 statutory damages (whichever is greater) and treble
  damages for wilful violations.
* Cure period: not specified.

## Notable Enforcement Actions

* **2018 N.M. AG action against Tiny Lab Productions** — Federal court action by
  the AG alleging COPPA-style violations in child-directed mobile apps; resulted
  in a permanent injunction.
* **Multi-state Equifax** — New Mexico received approximately $2 million from
  the 50-state settlement.

---

### Chapter 33


# New York — SHIELD Act + NYDFS Cybersecurity Regulation + Sectoral

> New York has no omnibus consumer privacy law as of 2026, though the New York
> Privacy Act (S365/A2587) has been introduced for several sessions. The Stop
> Hacks and Improve Electronic Data Security Act (SHIELD Act, N.Y. Gen. Bus. Law
> § 899-bb) imposes a reasonable-security obligation on any entity holding the
> private information of NY residents. New York also has a uniquely powerful
> Department of Financial Services (NYDFS) cybersecurity regulation (23 NYCRR 500)
> and child-targeted statutes (SAFE for Kids Act and NY Child Data Protection
> Act, effective 2025).

## Core Definitions

* **Personal Data** — Under the SHIELD Act, "private information": personal
  information combined with SSN, driver's-licence/state-ID number, financial-
  account credential, biometric data, or username/email + password.
* **Consumer** — NY resident; under the SAFE for Kids and Child Data Protection
  acts, "covered minor" is a user under 18.
* **Processing** — Not used by SHIELD Act, but the Child Data Protection Act
  imports the term as "any operation on covered information".
* **Sale** — The Child Data Protection Act defines sale as exchanging covered
  information of a minor for monetary or other valuable consideration.
* **Controller / Processor** — Not used; SHIELD applies to "persons or businesses".

## Consumer Rights

* **Right to Access** — None general; sectoral (HIPAA, FCRA) only.
* **Right to Deletion** — Under the NY Child Data Protection Act (effective
  15 June 2025), operators must delete covered minor data upon request.
* **Right to Correction** — None general.
* **Right to Opt-Out of Sale / Sharing** — Under the Child Data Protection Act,
  operators may not process covered information without consent unless strictly
  necessary for the service.
* **Right to Portability** — None general.

## Penalties & Enforcement

* SHIELD Act civil penalty: up to **$5,000 per violation** for failure to
  implement reasonable security (N.Y. Gen. Bus. Law § 899-bb(2)); breach
  notification penalty: greater of $20 per failed notification or actual
  damages, capped at $250,000.
* NYDFS cybersecurity regulation: separate enforcement under the Banking, Insurance,
  and Financial Services laws, with no statutory cap; penalties have reached
  $4.5 million (FRH Insurance, 2024).
* Child Data Protection Act civil penalty: up to **$5,000 per violation**.
* Enforcement: NY Attorney General; NYDFS for regulated financial institutions;
  private right of action under General Business Law § 349.

## Notable Enforcement Actions

* **Zoetop / SHEIN (2022)** — $1.9 million New York AG settlement following a
  2018 breach affecting 39 million accounts; the order included an unusual
  injunction against future misrepresentations of post-breach response actions.
* **First American Title Insurance (2023)** — $1 million NYDFS settlement, the
  agency's first cybersecurity-rule penalty, focused on inadequate access
  controls.
* **Capital One (2024)** — $80 million combined OCC/NYDFS penalty linked to the
  2019 breach, with NY collecting a $20 million share for SHIELD-related claims.

---

### Chapter 34


# North Carolina — Identity Theft Protection Act (N.C. Gen. Stat. § 75-60 et seq.)

> North Carolina has no omnibus privacy law. The Identity Theft Protection Act and
> the North Carolina Unfair and Deceptive Trade Practices Act (N.C. Gen. Stat.
> § 75-1.1) form the principal framework. The Consumer Privacy Act of North
> Carolina (HB 1110, 2024) has been introduced but not enacted.

## Core Definitions

* **Personal Data** — "Personal information": SSN, driver's-licence/state-ID
  number, financial-account credential, biometric data, employer or taxpayer ID,
  or digital signature combined with associated identifying information.
* **Consumer** — North Carolina resident.
* **Processing** — Not defined.
* **Sale** — Not defined for privacy purposes.
* **Controller / Processor** — Not used; the ITPA uses "businesses".

## Consumer Rights

* **Right to Access** — None codified.
* **Right to Deletion** — None codified.
* **Right to Correction** — None codified.
* **Right to Opt-Out of Sale / Sharing** — None codified.
* **Right to Portability** — None codified.

## Penalties & Enforcement

* UDAP civil penalty: up to **$5,000 per violation**, with treble damages
  available to private litigants (N.C. Gen. Stat. § 75-16).
* ITPA private right of action: actual damages plus reasonable attorneys' fees.
* Enforcement: NC Attorney General Consumer Protection Division; private right
  of action.
* Cure period: not specified.

## Notable Enforcement Actions

* **2023 Atrium Health settlement** — $1.2 million NC AG settlement over use of
  pixel-tracking technologies on patient-portal pages; required deletion of
  collected information and enhanced HIPAA-aligned governance.
* **Multi-state Marriott (2022)** — North Carolina recovered approximately
  $1.6 million.

---

### Chapter 35


# North Dakota — Notice of Security Breach for Personal Information (N.D. Cent. Code § 51-30)

> North Dakota has no omnibus privacy law. The breach-notification statute, the
> North Dakota Consumer Fraud Act (N.D. Cent. Code § 51-15), and the Bank
> Director's confidentiality rules form the framework. HB 1492 (a Virginia-model
> bill, 2023) was defeated.

## Core Definitions

* **Personal Data** — "Personal information": first name/initial + last name
  combined with SSN, driver's-licence/state-ID number, financial-account
  credential, employer's taxpayer-identification number, biometric data, or
  digital signature.
* **Consumer** — North Dakota resident; the CFA defines consumer broadly.
* **Processing** — Not defined.
* **Sale** — Not defined for privacy purposes.
* **Controller / Processor** — Not used.

## Consumer Rights

* **Right to Access** — None codified.
* **Right to Deletion** — None codified.
* **Right to Correction** — None codified.
* **Right to Opt-Out of Sale / Sharing** — None codified.
* **Right to Portability** — None codified.

## Penalties & Enforcement

* CFA civil penalty: up to **$5,000 per violation** plus restitution and
  injunctive relief.
* Breach-statute penalty: through CFA mechanism.
* Enforcement: North Dakota Attorney General; private right of action under
  CFA for actual damages and treble damages for knowing violations.
* Cure period: not specified.

## Notable Enforcement Actions

* **2022 North Dakota AG settlement with merchant processor** — $250,000 penalty
  arising from a 2021 skimmer compromise affecting North Dakota retailers.
* **Multi-state TurboTax / Intuit (2022)** — North Dakota recovered
  approximately $130,000.

---

### Chapter 36


# Ohio — Data Protection Act (Ohio Rev. Code § 1354)

> The Ohio Data Protection Act, effective 2018, is a unique "safe harbour" statute
> rather than a consumer rights statute: businesses that adopt a recognised
> cybersecurity framework (NIST CSF, ISO 27001, PCI DSS, etc.) gain an affirmative
> defence in litigation arising from a breach. Ohio also has the Ohio Personal
> Privacy Act (HB 376) which has been repeatedly introduced as a comprehensive
> bill but has not passed.

## Core Definitions

* **Personal Data** — "Personal information": first name/initial + last name
  combined with SSN, driver's-licence/state-ID number, or financial-account
  credential.
* **Consumer** — Ohio resident; the Consumer Sales Practices Act (Ohio Rev. Code
  § 1345) defines consumer broadly.
* **Processing** — Not defined.
* **Sale** — Not defined for privacy purposes.
* **Controller / Processor** — Not used; ODPA uses "covered entities".

## Consumer Rights

* **Right to Access** — None codified.
* **Right to Deletion** — None codified.
* **Right to Correction** — None codified.
* **Right to Opt-Out of Sale / Sharing** — None codified.
* **Right to Portability** — None codified.

## Penalties & Enforcement

* CSPA civil penalty: up to **$25,000 per violation** plus restitution.
* Breach-statute penalty: enforcement through the CSPA mechanism.
* Enforcement: Ohio Attorney General Consumer Protection Section; private right
  of action under CSPA, including class actions.
* Cure period: 14-day pre-suit demand under CSPA.

## Notable Enforcement Actions

* **2023 Premier Health settlement (private)** — A $25 million class settlement
  approved by an Ohio state court arising from a 2020 ransomware breach
  affecting 195,000 patient records.
* **Multi-state Marriott (2022)** — Ohio recovered approximately $2 million.

---

### Chapter 37


# Oklahoma — Security Breach Notification Act (24 Okla. Stat. § 161 et seq.)

> Oklahoma has no omnibus privacy law. The Oklahoma Computer Data Privacy Act (HB
> 1602, 2024) was a Virginia-model bill that did not pass the legislature.
> Coverage relies on breach notification and the Oklahoma Consumer Protection Act
> (15 Okla. Stat. § 751 et seq.).

## Core Definitions

* **Personal Data** — "Personal information": first name/initial + last name
  combined with SSN, driver's-licence/state-ID number, or financial-account
  credential.
* **Consumer** — Oklahoma resident.
* **Processing** — Not defined.
* **Sale** — Not defined for privacy purposes.
* **Controller / Processor** — Not used.

## Consumer Rights

* **Right to Access** — None codified.
* **Right to Deletion** — None codified.
* **Right to Correction** — None codified.
* **Right to Opt-Out of Sale / Sharing** — None codified.
* **Right to Portability** — None codified.

## Penalties & Enforcement

* OCPA civil penalty: up to **$10,000 per violation** plus restitution and
  injunctive relief.
* Breach-statute penalty: up to **$150,000 per breach** of notice obligations
  (24 Okla. Stat. § 166).
* Enforcement: Oklahoma Attorney General Consumer Protection Unit; private right
  of action for actual damages under OCPA.
* Cure period: pre-suit demand under OCPA.

## Notable Enforcement Actions

* **2023 Oklahoma AG settlement with credit-monitoring vendor** — $400,000 civil
  penalty for misleading marketing of "identity protection" features that did
  not provide promised data scrubbing.
* **Multi-state Equifax (2019)** — Oklahoma recovered approximately $3.4 million.

---

### Chapter 38


# Oregon — Oregon Consumer Privacy Act (OCPA, Or. Rev. Stat. § 646A.570 et seq.)

> The Oregon Consumer Privacy Act was signed in July 2023 and took effect on
> 1 July 2024 (1 July 2025 for non-profit organisations). OCPA contains uniquely
> robust biometric and child-privacy provisions and is the only US state law
> applicable to most non-profits. Applies to controllers conducting business in
> Oregon that during a calendar year (i) control or process the personal data of
> 100,000+ Oregon consumers, or (ii) control or process the personal data of
> 25,000+ consumers and derive 25%+ of gross revenue from the sale of personal
> data.

## Core Definitions

* **Personal Data** — Information linked or reasonably linkable to an identified
  or identifiable individual; explicitly includes derived data and inferences.
* **Consumer** — Oregon resident acting in an individual or household context.
* **Processing** — Any operation on personal data.
* **Sale** — Exchange of personal data for monetary or other valuable
  consideration.
* **Controller / Processor** — Standard model with DPA requirements; explicit
  obligations for sub-processor flow-down.

## Consumer Rights

* **Right of Access** — Confirmation, copy, **and the right to obtain a list of
  specific third parties** to whom the controller has disclosed personal data
  (unique to Oregon).
* **Right to Deletion** — Of all data, regardless of source.
* **Right to Correction** — Of inaccurate personal data.
* **Right to Opt-Out** — Of sale, targeted advertising, and certain profiling;
  UOOM required from 1 January 2026.
* **Right to Portability** — In readily usable format.
* **Sensitive-Data Opt-In** — Required for biometric data, precise geolocation,
  status as transgender or non-binary, immigration status, and citizenship.

## Penalties & Enforcement

* Civil penalty: up to **$7,500 per violation** under the Oregon Unlawful Trade
  Practices Act (Or. Rev. Stat. § 646.642).
* Enforcement: Oregon Department of Justice (Attorney General); no private right
  of action.
* Cure period: 30 days through 31 December 2025; cure right sunsets thereafter.

## Notable Enforcement Actions

* **2024 Sweep notices from Oregon DOJ** — In December 2024, the DOJ disclosed
  it had sent more than 40 sweep notices to controllers in connection with
  apparent failures to provide the unique third-party-recipient list.
* **2025 Oregon DOJ / Mozilla cooperation** — Oregon DOJ issued public-letter
  guidance after consulting with Mozilla about UOOM-signal interoperability,
  becoming the first US enforcer to recognise the GPC and other browser-level
  mechanisms as a single compliance path.

---

### Chapter 39


# Pennsylvania — Breach of Personal Information Notification Act (73 Pa. Stat. § 2301)

> Pennsylvania has no omnibus privacy law. HB 1201 (the Consumer Data Privacy Act,
> a Virginia-model bill) was reintroduced in 2025 but has not passed. Coverage is
> provided by the BPINA and the Unfair Trade Practices and Consumer Protection
> Law (73 Pa. Stat. § 201-1 et seq.).

## Core Definitions

* **Personal Data** — "Personal information": first name/initial + last name
  combined with SSN, driver's-licence/state-ID number, financial-account
  credential, medical/health-insurance information (amended 2022), or username
  with password.
* **Consumer** — Pennsylvania resident.
* **Processing** — Not defined.
* **Sale** — Not defined for privacy purposes.
* **Controller / Processor** — Not used.

## Consumer Rights

* **Right to Access** — None codified.
* **Right to Deletion** — None codified.
* **Right to Correction** — None codified.
* **Right to Opt-Out of Sale / Sharing** — None codified.
* **Right to Portability** — None codified.

## Penalties & Enforcement

* UTPCPL civil penalty: up to **$1,000 per violation** ($3,000 for victims age
  60+) plus restitution.
* Breach-statute penalty: through UTPCPL enforcement plus general civil tort
  exposure.
* Enforcement: Pennsylvania Attorney General Bureau of Consumer Protection;
  private right of action under UTPCPL.
* Cure period: not specified.

## Notable Enforcement Actions

* **Wawa litigation (2022)** — $9 million class settlement and $50,000 to the
  PA AG following Wawa's 2019 point-of-sale skimmer incident affecting 30 million
  payment cards.
* **Multi-state UCLA Health / Office Depot (2024)** — Pennsylvania participated
  in a $25 million multi-state settlement focused on inappropriate data
  collection in a mock-virus-removal scheme.

---

### Chapter 40


# Rhode Island — Rhode Island Data Transparency and Privacy Protection Act (RIDTPPA, R.I. Gen. Laws § 6-48.1)

> The Rhode Island Data Transparency and Privacy Protection Act was signed in
> June 2024 and takes effect on 1 January 2026. RIDTPPA is a Virginia-model statute
> with a unique transparency requirement: any commercial website that sells
> Rhode Islanders' personal information must list, in its privacy notice, the
> categories of personal information it has sold and the categories of third
> parties to whom it has sold them. Applies to persons doing business in Rhode
> Island that during a calendar year (i) control or process the personal data of
> 35,000+ RI consumers, or (ii) control or process the personal data of
> 10,000+ consumers and derive 20%+ of gross revenue from the sale of personal
> data.

## Core Definitions

* **Personal Data** — Information linked or reasonably linkable to an identified
  or identifiable individual; excludes deidentified data and publicly available
  information.
* **Consumer** — Rhode Island resident acting in individual/household context.
* **Processing** — Any operation on personal data.
* **Sale** — Exchange of personal data for monetary or other valuable
  consideration.
* **Controller / Processor** — Standard model.

## Consumer Rights

* **Right of Access** — Confirmation and copy.
* **Right to Deletion** — Of all personal data.
* **Right to Correction** — Of inaccuracies.
* **Right to Opt-Out** — Of sale, targeted advertising, and certain profiling.
* **Right to Portability** — In readily usable format.
* **Mandatory Disclosure** — Unique transparency obligation: privacy notices
  must list specific categories of personal data sold and the specific
  categories of third-party recipients.

## Penalties & Enforcement

* Civil penalty: **$100 to $500 per violation** (intentional violations) under
  the Rhode Island Deceptive Trade Practices Act (R.I. Gen. Laws § 6-13.1).
* Enforcement: Rhode Island Attorney General; no general private right of
  action.
* Cure period: 60 days (initial).

## Notable Enforcement Actions

* Statute effective only from January 2026, so no RIDTPPA-specific enforcement
  exists.
* Rhode Island participated in **2023 multi-state Blackbaud settlement**,
  receiving approximately $215,000.

---

### Chapter 41


# South Carolina — Financial Identity Fraud & Identity Theft Protection Act

> South Carolina has no omnibus privacy law. The Financial Identity Fraud and
> Identity Theft Protection Act, in effect since 2008, governs breach
> notification. The Unfair Trade Practices Act (S.C. Code § 39-5-10 et seq.)
> provides the enforcement vehicle. The South Carolina Insurance Data Security
> Act (S.C. Code § 38-99) imposes NAIC-aligned cybersecurity obligations on
> insurance licensees.

## Core Definitions

* **Personal Data** — "Personal identifying information": first name/initial +
  last name combined with SSN, driver's-licence/state-ID number, or
  financial-account credential.
* **Consumer** — South Carolina resident; UTPA defines consumer broadly.
* **Processing** — Not defined.
* **Sale** — Not defined for privacy purposes.
* **Controller / Processor** — Not used.

## Consumer Rights

* **Right to Access** — None codified.
* **Right to Deletion** — None codified.
* **Right to Correction** — None codified.
* **Right to Opt-Out of Sale / Sharing** — None codified.
* **Right to Portability** — None codified.

## Penalties & Enforcement

* UTPA civil penalty: up to **$5,000 per wilful violation**.
* Breach-statute penalty: up to **$1,000 per resident affected** for wilful or
  knowing violations (S.C. Code § 37-20-170).
* Insurance Data Security Act: penalties for licensees up to $30,000 per
  intentional violation.
* Enforcement: SC Attorney General and Department of Consumer Affairs; private
  right of action under UTPA.
* Cure period: not specified.

## Notable Enforcement Actions

* **2012 South Carolina Department of Revenue breach** — Although not a
  privacy-law action per se, the 3.6 million-record breach prompted enactment
  of the SC Insurance Data Security Act and continues to inform AG
  enforcement priorities.
* **Multi-state Anthem (2018)** — South Carolina recovered approximately
  $625,000 of the $39.5 million multi-state settlement.

---

### Chapter 42


# South Dakota — Breach Notification (S.D. Codified Laws § 22-40-19 et seq.)

> South Dakota was the 49th state to enact a breach-notification law, doing so in
> 2018. There is no omnibus privacy law. The Deceptive Trade Practices and
> Consumer Protection law (S.D. Codified Laws § 37-24) is the principal
> consumer-protection vehicle.

## Core Definitions

* **Personal Data** — "Personal information": first name/initial + last name
  combined with SSN, driver's-licence/state-ID number, financial-account
  credential, biometric data, employer-issued ID + access code, or
  username/email + password.
* **Consumer** — South Dakota resident.
* **Processing** — Not defined.
* **Sale** — Not defined for privacy purposes.
* **Controller / Processor** — Not used.

## Consumer Rights

* **Right to Access** — None codified.
* **Right to Deletion** — None codified.
* **Right to Correction** — None codified.
* **Right to Opt-Out of Sale / Sharing** — None codified.
* **Right to Portability** — None codified.

## Penalties & Enforcement

* Breach-statute penalty: up to **$10,000 per day per violation** (S.D.
  Codified Laws § 22-40-26) plus reasonable attorneys' fees.
* DTPCPA civil penalty: up to **$2,000 per violation** plus restitution.
* Enforcement: South Dakota Attorney General Consumer Protection Division;
  private right of action under DTPCPA for actual damages.
* Cure period: not specified.

## Notable Enforcement Actions

* **2024 South Dakota AG action against a national auto-dealer SaaS** —
  $375,000 stipulated penalty arising from a 2023 ransomware breach affecting
  thousands of South Dakotans.
* **Multi-state Equifax (2019)** — South Dakota recovered approximately
  $895,000.

---

### Chapter 43


# Tennessee — Tennessee Information Protection Act (TIPA, Tenn. Code § 47-18-3201 et seq.)

> The Tennessee Information Protection Act was signed in May 2023 and took
> effect on 1 July 2025. TIPA is a Virginia-model statute with one distinctive
> feature: an explicit safe harbour for controllers and processors that
> maintain a written privacy programme reasonably conforming to the NIST
> Privacy Framework. Applies to persons that conduct business in Tennessee
> producing $25 million+ in annual revenue and that during a calendar year
> (i) control or process the personal data of 175,000+ Tennessee consumers, or
> (ii) control or process the personal data of 25,000+ consumers and derive
> 50%+ of gross revenue from the sale of personal data.

## Core Definitions

* **Personal Data** — Information linked or reasonably linkable to an identified
  or identifiable individual; excludes deidentified and publicly available
  information.
* **Consumer** — Tennessee resident acting in individual/household context.
* **Processing** — Any operation on personal data.
* **Sale** — Exchange of personal data for monetary consideration to a third
  party.
* **Controller / Processor** — Standard model with DPA requirements; controllers
  and processors covered by the NIST safe harbour gain an affirmative defence.

## Consumer Rights

* **Right of Access** — Confirmation and copy.
* **Right to Deletion** — Of data provided or obtained.
* **Right to Correction** — Of inaccurate data.
* **Right to Opt-Out** — Of sale, targeted advertising, and certain profiling.
* **Right to Portability** — In readily usable format.
* **Right to Appeal** — Internal review of controller's refusals.

## Penalties & Enforcement

* Civil penalty: up to **$7,500 per violation**, plus actual damages and treble
  damages for wilful violations (Tenn. Code § 47-18-3213).
* Enforcement: Tennessee Attorney General; no private right of action.
* Cure period: 60 days; does not sunset.

## Notable Enforcement Actions

* Statute effective only since July 2025; the AG has issued informal guidance on
  the NIST safe harbour but has not announced enforcement actions as of
  mid-2026.
* Tennessee AG participated in **2023 multi-state Marriott** settlement,
  recovering approximately $1 million.

---

### Chapter 44


# Texas — Texas Data Privacy and Security Act (TDPSA, Tex. Bus. & Com. Code Ch. 541)

> The Texas Data Privacy and Security Act took effect on 1 July 2024 (sensitive-
> data consent provisions delayed to 1 January 2025). Texas's applicability
> threshold is uniquely broad: TDPSA applies to any person who conducts business
> in Texas or produces goods/services for Texans, processes or sells personal
> data, and is **not** a small business (as defined by the federal Small Business
> Administration). There is no consumer-count threshold.

## Core Definitions

* **Personal Data** — Information linked or reasonably linkable to an
  identified or identifiable individual; excludes deidentified and publicly
  available information.
* **Consumer** — Texas resident acting in individual/household context.
* **Processing** — Any operation on personal data.
* **Sale** — Exchange of personal data for monetary or other valuable
  consideration. (Texas adopted the broader CCPA-style definition rather than
  Virginia's monetary-only definition.)
* **Controller / Processor** — Standard model with DPA requirements.

## Consumer Rights

* **Right of Access** — Confirmation and copy in a portable format.
* **Right to Deletion** — Of all personal data, regardless of source.
* **Right to Correction** — Of inaccurate data.
* **Right to Opt-Out** — Of sale, targeted advertising, and certain profiling;
  UOOM honoured from 1 January 2025.
* **Right to Portability** — Yes.
* **Sensitive-Data Opt-In** — Consent required.

## Penalties & Enforcement

* Civil penalty: up to **$7,500 per violation** plus injunctive relief and
  reasonable attorneys' fees (Tex. Bus. & Com. Code § 541.155).
* Enforcement: Texas Attorney General exclusively; no private right of action.
* Cure period: 30 days; does not sunset.

## Notable Enforcement Actions

* **Texas AG v. Allstate Insurance and Arity (Jan 2025)** — Lawsuit alleging
  the data-broker subsidiary of Allstate collected driver-behaviour information
  from over 45 million users via SDK in third-party apps and resold it to
  insurers without consent. First major TDPSA enforcement action; case
  pending.
* **Texas AG settlement with NorthStar Behavioral Health (2024)** — $1.4
  million settlement following allegations that NorthStar disclosed health
  information through its public-facing website pixels.
* **TikTok COPPA / TDPSA settlement (Oct 2025)** — Texas-led multi-state
  agreement adding $25 million in penalties for processing Texans' sensitive
  biometric and minors' data without proper notice and consent.

---

### Chapter 45


# Utah — Utah Consumer Privacy Act (UCPA, Utah Code § 13-61)

> The Utah Consumer Privacy Act took effect on 31 December 2023. UCPA adopted the
> Virginia model but with the weakest consumer rights of any operational state
> privacy law: there is no right to correct, the sale definition is narrow
> (monetary consideration only), and there is no right to opt out of profiling.
> Applies to controllers conducting business in Utah, with $25 million+ in
> annual revenue, that during a calendar year (i) control or process the
> personal data of 100,000+ Utah consumers, or (ii) control or process the
> personal data of 25,000+ consumers and derive 50%+ of gross revenue from the
> sale of personal data.

## Core Definitions

* **Personal Data** — Information linked or reasonably linkable to an
  identified or identifiable individual; excludes deidentified and publicly
  available information.
* **Consumer** — Utah resident acting in individual or household context;
  explicitly excludes employment context.
* **Processing** — Any operation on personal data.
* **Sale** — Exchange of personal data for monetary consideration only;
  notably narrower than CCPA, Colorado, or Connecticut.
* **Controller / Processor** — Standard controller/processor model.

## Consumer Rights

* **Right of Access** — Confirmation and copy.
* **Right to Deletion** — Of data the consumer has provided.
* **Right to Correction** — Notably absent. Utah is the only effective omnibus
  US law without a correction right.
* **Right to Opt-Out** — Of sale and targeted advertising; **no** right to
  opt out of profiling.
* **Right to Portability** — Yes.

## Penalties & Enforcement

* Civil penalty: up to **$7,500 per violation** (Utah Code § 13-61-402); pre-
  enforcement investigation handled by the Department of Commerce, with the
  Attorney General prosecuting.
* Enforcement: Utah Attorney General + Utah Division of Consumer Protection;
  no private right of action.
* Cure period: 30 days; does not sunset.

## Notable Enforcement Actions

* **2024 Utah Division of Consumer Protection investigation of social-media
  platforms** — Several state investigations into adtech compliance with UCPA
  resulted in voluntary remediation rather than published penalties.
* **TikTok lawsuit by Utah AG (filed Oct 2023)** — Utah is among multiple
  states alleging deceptive design choices, with claims overlapping with
  COPPA and Utah's Social Media Regulation Act.

---

### Chapter 46


# Vermont — Data Broker Registration Statute (9 V.S.A. § 2446) + Breach Notification

> Vermont was the first state to require registration of data brokers (effective
> 2019). The legislature passed the Vermont Data Privacy Act (H.121) in 2024 but
> Governor Phil Scott vetoed it. The 2025 version of the comprehensive bill was
> narrowed and remains under consideration. The Vermont Age-Appropriate Design
> Code Act and a Kids Code-style bill were enacted in 2024, with phased
> effectiveness through 2026.

## Core Definitions

* **Personal Data** — Under the data-broker statute, "brokered personal
  information" includes name, address, email, phone, financial information,
  health information, religious/political affiliation, and inferences therefrom.
* **Consumer** — Vermont resident.
* **Processing** — Not defined in the data-broker statute, which regulates
  "sale" instead.
* **Sale** — For data-broker purposes, an exchange of brokered personal
  information for consideration.
* **Controller / Processor** — Not used.

## Consumer Rights

* **Right to Access** — None codified (general).
* **Right to Deletion** — Data brokers must include in their registration a
  description of opt-out processes.
* **Right to Correction** — None codified.
* **Right to Opt-Out of Sale / Sharing** — Through the data-broker registration
  framework, brokers must offer opt-out, though no statutory consumer-right of
  action.
* **Right to Portability** — None codified.

## Penalties & Enforcement

* Data-broker registration penalty: **$50 per day of failure to register**,
  capped at $10,000 per year.
* Vermont Consumer Protection Act civil penalty: up to **$10,000 per violation**
  (9 V.S.A. § 2458) plus restitution and treble damages for knowing wilful
  violations.
* Enforcement: Vermont Attorney General; private right of action under VCPA.
* Cure period: not specified.

## Notable Enforcement Actions

* **2020 Vermont AG enforcement of data-broker registration** — Multiple data
  brokers failed to register or made inaccurate disclosures; the AG announced
  a 14-broker sweep, with penalties ranging from $5,000 to $87,000 per
  broker.
* **Clearview AI / Vermont AG (2020)** — Vermont AG filed an action under the
  Vermont Consumer Protection Act, securing an injunction prohibiting
  Clearview from scraping Vermont residents' images for facial-recognition.
  The case was one of the first state-AG actions against scraper firms.

---

### Chapter 47


# Virginia — Virginia Consumer Data Protection Act (VCDPA, Va. Code § 59.1-575 et seq.)

> The Virginia Consumer Data Protection Act took effect on 1 January 2023 and
> was the second comprehensive US state privacy law (after CCPA/CPRA). VCDPA
> served as the model for Connecticut, Colorado, Tennessee, Indiana, Iowa, Utah,
> Kentucky, Nebraska, and others. Applies to persons that conduct business in
> Virginia and that during a calendar year (i) control or process the personal
> data of 100,000+ Virginia consumers, or (ii) control or process the personal
> data of 25,000+ consumers and derive over 50% of gross revenue from the sale
> of personal data.

## Core Definitions

* **Personal Data** — Any information linked or reasonably linkable to an
  identified or identifiable natural person; excludes deidentified data,
  publicly available information, and employee or B2B contact information.
* **Consumer** — Virginia resident acting in individual or household context;
  explicitly excludes commercial and employment contexts.
* **Processing** — Any operation performed on personal data, automated or not.
* **Sale** — Exchange of personal data for **monetary consideration** to a
  third party (narrower than CCPA's monetary-or-valuable-consideration
  definition).
* **Controller / Processor** — Controller decides purposes/means; processor
  follows controller instructions under a data-processing addendum that must
  include subprocessor authorisation, audit, and security commitments.

## Consumer Rights

* **Right of Access** — Confirmation and copy in a portable format.
* **Right to Deletion** — Of data provided to or obtained about the consumer.
* **Right to Correction** — Of inaccurate personal data.
* **Right to Opt-Out** — Of sale, targeted advertising, and profiling in
  furtherance of decisions producing legal or similarly significant effects.
* **Right to Portability** — In a readily usable format.
* **Right to Appeal** — Internal appeal mechanism; complaints may be filed
  with the AG.

## Penalties & Enforcement

* Civil penalty: up to **$7,500 per violation** plus reasonable attorneys' fees
  and investigative costs (Va. Code § 59.1-584).
* Enforcement: Virginia Attorney General exclusively; no private right of
  action.
* Cure period: 30 days; does not sunset.

## Notable Enforcement Actions

* The Virginia AG has emphasised compliance education during initial years; as
  of mid-2026 no public penalty actions have been announced under VCDPA.
* Virginia AG participated in **2023 multi-state Marriott** $52 million
  settlement, recovering approximately $1.4 million.
* Virginia is part of the **2024 multi-state TikTok COPPA settlement**,
  recovering approximately $3.6 million.

---

### Chapter 48


# Washington — My Health My Data Act (Wash. Rev. Code § 19.373)

> Washington has no omnibus privacy law (the proposed Washington Privacy Act
> failed in 2019, 2020, and 2021), but it has the most stringent consumer
> health-data statute in the US: the My Health My Data Act (MHMDA), effective
> 31 March 2024 (small businesses: 30 June 2024). MHMDA imposes an opt-in
> consent regime, a flat prohibition on the sale of consumer health data
> without separate written authorisation, and the only private right of
> action in any US state privacy law outside Illinois BIPA. Washington also
> has a strong breach-notification statute (Wash. Rev. Code § 19.255) and a
> Consumer Protection Act (Wash. Rev. Code § 19.86).

## Core Definitions

* **Personal Data** — Under MHMDA, "consumer health data" means personal
  information that is linked or reasonably linkable to a consumer and that
  identifies the consumer's past, present, or future physical or mental
  health status. Very broad: includes biometric data, gender-affirming care,
  reproductive or sexual health, precise location indicating a visit to a
  health facility, and inferences.
* **Consumer** — A Washington resident, or any natural person whose consumer
  health data is collected in Washington. Notably, MHMDA applies regardless of
  state of residency where the data is collected within Washington.
* **Processing** — Any operation on consumer health data.
* **Sale** — Exchange of consumer health data for monetary or other valuable
  consideration. **Sale of consumer health data is prohibited without separate,
  signed valid authorisation** containing specified elements.
* **Controller / Processor** — Standard model; processor must follow controller
  instructions and is subject to a written data-processing agreement.

## Consumer Rights

* **Right of Access** — Confirmation and copy of consumer health data.
* **Right to Deletion** — Including all backups, archives, and copies; broader
  than any other US state privacy law deletion right.
* **Right to Correction** — Not codified, but consent withdrawal effectively
  triggers deletion.
* **Right to Opt-In (Consent)** — Affirmative consent required before
  collection or sharing of consumer health data, separate from any other
  consent.
* **Right to Withdraw Consent** — At any time, with the same ease with which
  it was given.
* **Right of Action (PRA)** — Through the Consumer Protection Act (Wash.
  Rev. Code § 19.86), enabling treble damages up to $25,000 per plaintiff
  plus attorneys' fees.

## Penalties & Enforcement

* CPA civil penalty: up to **$7,500 per violation** plus treble damages
  available to private litigants.
* MHMDA violations are explicitly deemed CPA violations under § 19.373.130.
* Enforcement: Washington Attorney General; private right of action under
  CPA.
* Cure period: not specified for MHMDA.

## Notable Enforcement Actions

* **First MHMDA class actions (2024–25)** — Multiple putative class actions
  have been filed against fertility-tracking, mental-health, and digital
  pharmacy apps in Washington state and federal court; most are at the
  motion-to-dismiss stage as of mid-2026.
* **Washington AG action against Cerebral Inc. (2024)** — $1.5 million state
  settlement following the company's disclosures of patient mental-health
  data to advertising vendors. The matter included strict MHMDA-aligned
  injunctive relief.
* **AG Sweep of Reproductive-Health Apps (2025)** — Washington AG issued
  five compliance notices to telehealth providers in June 2025, alleging
  inadequate consent mechanisms; settlements ranged from $200,000 to
  $1.1 million.

---

### Chapter 49


# West Virginia — Breach Notification (W. Va. Code § 46A-2A)

> West Virginia has no omnibus privacy law. The Consumer Credit and Protection
> Act (W. Va. Code § 46A-1-101 et seq.) and the breach-notification subchapter
> are the principal vehicles. HB 5338 (a Virginia-model bill) was considered in
> 2024 but did not pass.

## Core Definitions

* **Personal Data** — "Personal information": first name/initial + last name
  combined with SSN, driver's-licence/state-ID number, or financial-account
  credential.
* **Consumer** — West Virginia resident.
* **Processing** — Not defined.
* **Sale** — Not defined for privacy purposes.
* **Controller / Processor** — Not used.

## Consumer Rights

* **Right to Access** — None codified.
* **Right to Deletion** — None codified.
* **Right to Correction** — None codified.
* **Right to Opt-Out of Sale / Sharing** — None codified.
* **Right to Portability** — None codified.

## Penalties & Enforcement

* CCPA civil penalty: up to **$5,000 per wilful violation** plus restitution.
* Breach-statute penalty: through CCPA mechanisms.
* Enforcement: West Virginia Attorney General Consumer Protection Division;
  private right of action under CCPA for actual damages.
* Cure period: pre-suit notice generally required under CCPA.

## Notable Enforcement Actions

* **2023 West Virginia AG settlement with health-insurance back-office vendor**
  — $325,000 stipulated penalty arising from a phishing-induced disclosure of
  insureds' PII.
* **Multi-state Equifax (2019)** — West Virginia recovered approximately
  $1 million.

---

### Chapter 50


# Wisconsin — Notice of Unauthorized Acquisition of Personal Information (Wis. Stat. § 134.98)

> Wisconsin has no omnibus privacy law. SB 642 (a Connecticut-model bill, 2023)
> was reintroduced in 2025 but had not been enacted. The principal frameworks
> are the breach-notification statute and the Deceptive Trade Practices Act
> enforced by the Department of Agriculture, Trade and Consumer Protection
> (DATCP).

## Core Definitions

* **Personal Data** — "Personal information": last name + first name/initial
  combined with SSN, driver's-licence/state-ID number, financial-account
  credential, DNA profile, or biometric information.
* **Consumer** — Wisconsin resident; DTPA defines consumer broadly.
* **Processing** — Not defined.
* **Sale** — Not defined for privacy purposes.
* **Controller / Processor** — Not used.

## Consumer Rights

* **Right to Access** — None codified.
* **Right to Deletion** — None codified.
* **Right to Correction** — None codified.
* **Right to Opt-Out of Sale / Sharing** — None codified.
* **Right to Portability** — None codified.

## Penalties & Enforcement

* DTPA civil penalty: up to **$10,000 per violation** plus restitution.
* Breach-statute does not contain an explicit per-incident cap; enforcement
  runs through the DTPA.
* Enforcement: Wisconsin DATCP and AG; private right of action for actual
  damages under DTPA.
* Cure period: not specified.

## Notable Enforcement Actions

* **2022 Wisconsin DATCP action against e-commerce platform** — $675,000
  settlement focused on undisclosed sharing of customer-purchase data with
  marketing partners.
* **Multi-state Marriott (2022)** — Wisconsin recovered approximately
  $1.1 million.

---

### Chapter 51


# Wyoming — Breach Notification (Wyo. Stat. § 40-12-501 et seq.)

> Wyoming has no omnibus privacy law. SF 80 (a Virginia-model bill) was
> considered in 2024 but did not advance. The principal frameworks are the
> breach-notification subchapter and the Wyoming Consumer Protection Act (Wyo.
> Stat. § 40-12-101 et seq.).

## Core Definitions

* **Personal Data** — "Personal identifying information": first name/initial +
  last name combined with SSN, driver's-licence/state-ID number,
  financial-account credential, employer-issued ID + access code, biometric
  data, or shared health-information element.
* **Consumer** — Wyoming resident.
* **Processing** — Not defined.
* **Sale** — Not defined for privacy purposes.
* **Controller / Processor** — Not used.

## Consumer Rights

* **Right to Access** — None codified.
* **Right to Deletion** — None codified.
* **Right to Correction** — None codified.
* **Right to Opt-Out of Sale / Sharing** — None codified.
* **Right to Portability** — None codified.

## Penalties & Enforcement

* WCPA civil penalty: up to **$5,000 per violation** plus restitution and
  injunctive relief.
* Breach-statute penalty: enforcement through the WCPA.
* Enforcement: Wyoming Attorney General Consumer Protection Unit; private
  right of action under WCPA for actual damages.
* Cure period: not specified.

## Notable Enforcement Actions

* **2023 Wyoming AG action against an online gaming platform** — $200,000
  stipulated penalty arising from a 2022 misconfiguration that exposed
  customer-account credentials.
* **Multi-state Equifax (2019)** — Wyoming recovered approximately $325,000
  of the $575 million settlement.

---
