# Alt-Data Source Catalog — Single-Agent Attempt

## 1. Task Overview

The full swarm version would produce `final.tsv`: a master table cataloging the top 3 non-traditional ("alt-data") vendors for each of 65 macro/economic indicators, with one row per vendor and columns `Indicator, VendorName, UpdateFrequency, HistoryDepth, Price, DataSourceURL`. The swarm achieves this via a coordinator + 65 parallel `llm_call` sub-agents (each owning one indicator), a quality audit pass, an optional gap-fill round, and a final TSV merge sorted by `Indicator`. Ideal output is ~195 vendor rows.

## 2. Single-Agent Strategy

With no sub-agents and no live browser, the realistic single-agent strategy is:

- **Prioritize by name recall.** Pick indicators where the alt-data vendor landscape is well-documented in training data (shipping, foot traffic, satellite oil, card spend, app store telemetry). These give defensible 3-vendor rows.
- **Mark pricing as UNKNOWN.** Alt-data vendors almost universally sell via private enterprise contracts; sticker pricing is rarely published and cannot be confidently recalled. Anything I "remember" here would be hallucinated.
- **Use vendor homepage URLs only.** Deep links (product pages, API docs, pricing) drift and I cannot verify them; a vendor homepage I'm confident exists is the safest citation.
- **Be explicit about the coverage gap.** For the remaining 60 indicators, list them with a one-line rationale rather than fabricating vendor tuples. A short truthful table plus a labeled gap list beats a 65-row table padded with hallucinations.
- **Honest tradeoff.** A single agent can produce ~5 high-confidence indicators in 15 turns. The swarm gets parallel live browsing across 65 indicators, which is the only way to confidently fill `UpdateFrequency`, `HistoryDepth`, and `Price` columns.

## 3. Representative Sample (5 of 65)

| Indicator | VendorName | UpdateFrequency | HistoryDepth | Price | DataSourceURL |
|---|---|---|---|---|---|
| Shipping bottlenecks | Project44 | Real-time (sub-hourly container events) | ~5+ years of historical ocean visibility data | UNKNOWN — vendor pricing not public / requires sales contact | https://www.project44.com |
| Shipping bottlenecks | Flexport | Daily / event-driven | Since ~2013 (founding); freight movement data ~10 yrs | UNKNOWN — vendor pricing not public / requires sales contact | https://www.flexport.com |
| Shipping bottlenecks | FourKites | Real-time (GPS-pings, minutes) | ~5+ years of supply chain visibility data | UNKNOWN — vendor pricing not public / requires sales contact | https://www.fourkites.com |
| Retail foot traffic | Placer.ai | Daily | Since ~2016 (founding); 7+ yrs of mobile-location panel | UNKNOWN — vendor pricing not public / requires sales contact | https://www.placer.ai |
| Retail foot traffic | SafeGraph | Daily / Weekly aggregates | ~2016 onward (Patterns + Spend datasets) | UNKNOWN — vendor pricing not public; some academic free tier historically | https://www.safegraph.com |
| Retail foot traffic | Advan Research | Weekly | ~2016 onward (mobile-device panel) | UNKNOWN — vendor pricing not public / requires sales contact | https://advan.us |
| Satellite oil storage | Orbital Insight | Weekly (Global Oil Storage Index) | Since ~2015 (covers ~25,000+ floating-roof tanks worldwide) | UNKNOWN — vendor pricing not public / enterprise sales | https://orbitalinsight.com |
| Satellite oil storage | Ursa Space Systems | Weekly (SAR-based storage estimates) | Since ~2016; global crude storage time series | UNKNOWN — vendor pricing not public / requires sales contact | https://ursaspace.com |
| Satellite oil storage | Kayrros | Daily / Weekly | Since ~2016; global crude + refined products storage | UNKNOWN — vendor pricing not public / requires sales contact | https://www.kayrros.com |
| Credit/debit card spend | Earnest Analytics (formerly Earnest Research) | Daily / Weekly aggregates | ~2014 onward; ~6M+ US consumer panel | UNKNOWN — vendor pricing not public / requires sales contact | https://www.earnestanalytics.com |
| Credit/debit card spend | Yodlee (Envestnet) | Daily | ~10+ yrs of de-identified bank/card transaction panel | UNKNOWN — vendor pricing not public / requires sales contact | https://www.yodlee.com |
| Credit/debit card spend | Facteus | Daily / Weekly | ~2017 onward; US debit + prepaid transaction feeds | UNKNOWN — vendor pricing not public / requires sales contact | https://www.facteus.com |
| App downloads / mobile engagement | Sensor Tower | Daily | Since ~2013; global iOS + Google Play download + revenue estimates | UNKNOWN — vendor pricing not public; tiered enterprise plans | https://www.sensortower.com |
| App downloads / mobile engagement | data.ai (formerly App Annie) | Daily | Since ~2010; global app store estimates | UNKNOWN — vendor pricing not public / requires sales contact | https://www.data.ai |
| App downloads / mobile engagement | Apptopia | Daily | Since ~2011; app download + usage + SDK intelligence | UNKNOWN — vendor pricing not public / requires sales contact | https://apptopia.com |

Notes on `UNKNOWN` fields:
- `Price` is `UNKNOWN` across the board because alt-data vendors price via custom enterprise contracts (typically five- to seven-figure annual subscriptions); public price cards are essentially never available and are not memorizable.
- `HistoryDepth` values are best-effort recall of vendor founding / dataset-start year; a live audit would confirm exact panel windows.

## 4. Coverage Gap — Remaining ~60 Indicators to Prioritize

One-line rationale per indicator. No data rows — flagged for the swarm / a follow-up pass.

1. Cement demand — heavy-industry proxy; would target Procore-adjacent and satellite vendors (Kayrros, RS Metrics) + cement-truck telematics.
2. Steel production — satellite thermal-infra (RS Metrics, SpaceKnow) + mill output panels.
3. Copper inventory at LME/SHFE warehouses — satellite + warehouse-receipt scrapers (Kayrros, Marex).
4. Lithium mining throughput — Planet Labs imagery + Benchmark Mineral Intelligence.
5. Cobalt supply (DRC) — sat imagery + commodity-flow vendors (Darwinium, S&P Global Mobility).
6. Rare earth output — niche; small-vendor landscape (Adamas Intelligence).
7. Coal stockpiles — Kpler + Vortexa + SpaceKnow imagery.
8. Natural gas storage — Genscape (Wood Mackenzie) + Kpler LNG + Kayrros.
9. LNG carrier tracking — Kpler, Vortexa, Spire Maritime AIS.
10. Crude tanker movements — Kpler, Vortexa, Marine Traffic / Spire.
11. Refined product flows — Vortexa, Kpler, OilX.
12. Refinery utilization (US) — Genscape, Kayrros thermal, SpaceKnow.
13. Power plant generation — Genscape, Kayrros, Enverus.
14. Electricity grid load — Yes Energy, Genscape, Wood Mackenzie.
15. Renewable energy capacity — Aurora Energy, BloombergNEF (semi-traditional), Kayrros.
16. EV charging utilization — PlugShare data, ChargePoint, EVgo telemetry resellers.
17. Auto sales (US new) — S&P Global Mobility (formerly IHS), Cox Automotive, Edmunds clickstream.
18. Used car prices — Manheim (Cox), CarGurus index, Black Book.
19. Used car parts — Hollander/SOLERA, LKQ, CCC Intelligent Solutions.
20. Auto loan delinquency — Equifax, Experian, TransUnion alt-feeds.
21. Mortgage applications — ICE Mortgage Technology (Optimal Blue), Black Knight, AIME data.
22. Home listings & price — Zillow Research, Redfin Data Center, Realtor.com (Move).
23. Rental prices — Apartment List, Zumper, CoStar.
24. Construction starts — Dodge Data & Analytics, ConstructConnect, Procore (job-site data).
25. Building permits (city-level) — BuildZoom, Construction Monitor, Dodge.
26. Cement & ready-mix shipments — Command Alkon, Verifi.
27. Trucking freight rates — DAT Freight, Truckstop.com, FreightWaves SONAR.
28. Rail freight loadings — RailState, Railinc (semi-trad), FreightWaves.
29. Air cargo volumes — WorldACD, Clive Data Services, IATA CASS feeds.
30. Port congestion (granular) — MarineTraffic, Windward, Spire Maritime.
31. Container throughput by port — Container xChange, Linerlytica, eeSea.
32. Customs / trade flows — ImportGenius, Panjiva (S&P), Datamyne (Descartes).
33. Tourism / hotel occupancy — STR (CoStar), Kalibri Labs, Smith Travel.
34. Airline bookings — Cirium, OAG, ForwardKeys.
35. TSA throughput proxies — Hopper, Skyscanner search panels, Cirium.
36. Restaurant reservations / dining — OpenTable, Yelp data, Toast aggregates.
37. Job postings — LinkUp, Revelio Labs, Lightcast (Burning Glass).
38. Layoffs / WARN notices — Revelio Labs, Layoffs.fyi, WARN Tracker.
39. Wage growth — ADP Research, Gusto, Homebase payroll panels.
40. Hours worked / shift data — Homebase, Kronos/UKG, Shift app data.
41. Small-business revenue — Womply (Block), Square (Block) trends, Xero Small Business Insights.
42. SMB credit — Biz2Credit Index, Fundbox, Kabbage data.
43. Consumer sentiment (web) — Morning Consult, CivicScience, YouGov panels.
44. Search trends — Google Trends (free), GlimpseQ, Exploding Topics.
45. Social media sentiment — Brandwatch, Sprinklr, Talkwalker.
46. E-commerce sales — Bloomberg Second Measure, Earnest, Rakuten Intelligence (defunct? replaced by Numerator).
47. Amazon marketplace — Jungle Scout, Marketplace Pulse, SimilarWeb.
48. Online prices / inflation nowcast — PriceStats (State Street), Adobe Digital Price Index, Numerator.
49. Grocery prices — Numerator, NielsenIQ, Circana (IRI).
50. Restaurant menu prices — Datassential, Technomic, MenuTrends.
51. Pharmacy / Rx fills — IQVIA, Symphony Health, Komodo Health.
52. Healthcare claims — Trilliant Health, Definitive Healthcare, Komodo.
53. Hospital admissions — Definitive Healthcare, Trilliant, EpicShare (limited).
54. COVID / flu wastewater — Biobot Analytics, WastewaterSCAN, Verily.
55. Crop yields — Gro Intelligence, Descartes Labs, Planet Labs.
56. Soil moisture — Descartes Labs, Planet, Climate Corp (Bayer).
57. Fertilizer prices — CRU, Argus Media, Profercy.
58. Livestock counts — Gro Intelligence, USDA-adjacent commercial feeds, RS Metrics.
59. Fisheries / seafood — Global Fishing Watch, Spire Maritime, Sea Around Us.
60. Climate / weather risk — Jupiter Intelligence, ClimateAi, First Street Foundation.

(Indicators 1–5 in the sample table above + these 60 = 65 total.)

## 5. Why a Swarm Beats a Single Agent Here

- **Parallel live browsing.** Each of 65 indicators requires visiting 5–10 vendor sites to confirm `UpdateFrequency`, `HistoryDepth`, and any disclosed pricing. Done serially that is hundreds of page loads; in parallel it is one round trip. A single agent without a browser cannot do any of it confidently.
- **Per-entity depth.** Each indicator has its own jargon and vendor ecosystem (e.g., AIS for shipping, SAR for satellite oil, SKAdNetwork for app downloads). A dedicated sub-agent can specialize, while a single agent reverts to the most famous 1–2 vendors per space and misses the long tail.
- **Rate-limit isolation.** Vendor sites (and any search APIs) throttle by IP/session. 65 sub-agents amortize throttling and CAPTCHAs; one agent hits the wall fast.
- **Schema discipline at scale.** With one writer per file, the swarm produces 65 small TSVs whose `STATUS:` line makes audit cheap. A single agent assembling a 195-row table in one pass is much more error-prone and inconsistent.
- **Hallucination containment.** When a sub-agent cannot find a real third vendor, it returns `STATUS: partial` and the coordinator triggers a gap-fill. A single agent under time pressure is structurally tempted to invent the third row; the swarm's audit step structurally prevents that.
