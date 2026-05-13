# Single-Agent Attempt — DAO Treasury Asset Audit

## 1. Task Overview

The swarm version would produce `final_dashboard.tsv`: a 50-row, alphabetically sorted dashboard of major DAOs with their top 3 non-stablecoin treasury assets (with USD values), a diversification flag, custody setup (multisig type, signer count, multisig address), and source links. A 50-agent swarm would parallelize live browsing across Etherscan, governance forums, and Snapshot.org pages, then a coordinator would audit `STATUS: complete` vs. `STATUS: partial` files, fill gaps with a follow-up round of up to 10 sub-agents, and synthesize a brief findings report covering most common non-stable holdings, dominant custody pattern (almost always Gnosis Safe), and average signer counts.

## 2. Single-Agent Strategy

With no sub-agents and no live browser, a realistic single-agent strategy is:

- **Tier 1 (high-confidence, structural data):** For 5–10 well-known DAOs, recall structural facts that change slowly: which assets dominate the treasury (usually the DAO's own governance token plus ETH and one or two strategic positions), custody type (overwhelmingly Gnosis Safe on Ethereum L1), and signer count for the canonical multisig. These are governance-parameter-level facts and are reasonably stable.
- **Tier 2 (volatile data):** Refuse to fabricate USD-denominated values. Asset prices and balance sizes shift hourly; any number I write from memory would be misleading. Mark every `Asset_*_Value_USD` cell `UNKNOWN — value time-varying, requires live treasury snapshot`.
- **Tier 3 (address recall):** Only fill `Multisig_Address` when I have high recall confidence and can flag it as needing on-chain verification. For most DAOs, mark `UNKNOWN` rather than risk a wrong checksum.
- **Coverage:** Cover 5 in depth, then enumerate ~45 more by name with one-line rationale so a follow-up swarm has a prioritized worklist.

**Honest tradeoffs:** A single agent cannot match a swarm here. The bottleneck is not reasoning — it is per-entity browsing depth × 50. Any single-agent attempt is a planning artifact, not a finished dashboard.

## 3. Representative Sample (5 of 50)

Schema columns: `DAO_Name | Asset_1 | Asset_1_Value_USD | Asset_2 | Asset_2_Value_USD | Asset_3 | Asset_3_Value_USD | Diversification_Non_Stable | Custody_Type | Multisig_Address | Signer_Count | Source_Links`

### Row 1 — Uniswap
- **DAO_Name:** Uniswap
- **Asset_1:** UNI (governance token, dominates treasury)
- **Asset_1_Value_USD:** UNKNOWN — value time-varying, requires live treasury snapshot
- **Asset_2:** ETH
- **Asset_2_Value_USD:** UNKNOWN — value time-varying, requires live treasury snapshot
- **Asset_3:** ENS (small strategic holding) — UNKNOWN with high uncertainty; could equally be wrapped/LP positions
- **Asset_3_Value_USD:** UNKNOWN — value time-varying, requires live treasury snapshot
- **Diversification_Non_Stable:** Low — treasury is overwhelmingly concentrated in native UNI
- **Custody_Type:** Governance-controlled Timelock contract; operational Gnosis Safe(s) for grants/ops
- **Multisig_Address:** UNKNOWN — Uniswap treasury is governed by the Timelock (`0x1a9C8182C09F50C8318d769245beA52c32BE35BC` is the Timelock address from memory; needs on-chain verification)
- **Signer_Count:** N/A for Timelock; ops multisigs typically 4–6 signers (UNKNOWN exact)
- **Source_Links:** gov.uniswap.org; etherscan.io (Timelock); snapshot.org/#/uniswapgovernance.eth

### Row 2 — MakerDAO (Sky)
- **DAO_Name:** MakerDAO
- **Asset_1:** MKR (governance token)
- **Asset_1_Value_USD:** UNKNOWN — value time-varying, requires live treasury snapshot
- **Asset_2:** ETH (and stETH via RWA / PSM-adjacent allocations)
- **Asset_2_Value_USD:** UNKNOWN — value time-varying, requires live treasury snapshot
- **Asset_3:** RWA-backed assets (US Treasury exposure via Monetalis/BlockTower vaults — borderline "non-stable" depending on classification)
- **Asset_3_Value_USD:** UNKNOWN — value time-varying, requires live treasury snapshot
- **Diversification_Non_Stable:** Medium — significant ETH/stETH plus MKR; large portion of overall surplus is in DAI/stable RWA which is excluded from "non-stable"
- **Custody_Type:** Protocol-controlled smart contracts (Surplus Buffer, vaults) governed by MKR voting; not a single Gnosis Safe
- **Multisig_Address:** UNKNOWN — Maker uses protocol contracts, not a canonical treasury multisig
- **Signer_Count:** N/A — governance is on-chain MKR voting, not a fixed-signer multisig
- **Source_Links:** forum.makerdao.com; makerburn.com; daistats.com; etherscan.io

### Row 3 — Aave
- **DAO_Name:** Aave
- **Asset_1:** AAVE (governance token; Ecosystem Reserve)
- **Asset_1_Value_USD:** UNKNOWN — value time-varying, requires live treasury snapshot
- **Asset_2:** ETH / aWETH (interest-bearing)
- **Asset_2_Value_USD:** UNKNOWN — value time-varying, requires live treasury snapshot
- **Asset_3:** stkAAVE / Safety Module assets, plus assorted aTokens from protocol fees
- **Asset_3_Value_USD:** UNKNOWN — value time-varying, requires live treasury snapshot
- **Diversification_Non_Stable:** Medium-Low — heavy AAVE concentration plus diversified aToken streams
- **Custody_Type:** Aave Collector contracts + governance-controlled; operational Gnosis Safe for Aave Companies / Guardian
- **Multisig_Address:** UNKNOWN — collector contracts are per-market; Guardian Safe address not confidently recalled
- **Signer_Count:** Guardian multisig commonly cited around 5–6 signers (UNKNOWN exact)
- **Source_Links:** governance.aave.com; snapshot.org/#/aave.eth; etherscan.io (Collector)

### Row 4 — Compound
- **DAO_Name:** Compound
- **Asset_1:** COMP (governance token)
- **Asset_1_Value_USD:** UNKNOWN — value time-varying, requires live treasury snapshot
- **Asset_2:** cTokens / aTokens accumulated from reserves (cUSDC, cETH balances)
- **Asset_2_Value_USD:** UNKNOWN — value time-varying, requires live treasury snapshot
- **Asset_3:** ETH
- **Asset_3_Value_USD:** UNKNOWN — value time-varying, requires live treasury snapshot
- **Diversification_Non_Stable:** Low — dominated by COMP
- **Custody_Type:** Governance Timelock contract controls reserves; no single canonical operational multisig
- **Multisig_Address:** UNKNOWN — Timelock address (`0x6d903f6003cca6255D85CcA4D3B5E5146dC33925` from memory; verify on-chain)
- **Signer_Count:** N/A for Timelock
- **Source_Links:** compound.finance/governance; etherscan.io (Timelock + Reservoir); snapshot still used historically

### Row 5 — ENS (Ethereum Name Service)
- **DAO_Name:** ENS
- **Asset_1:** ETH (largest non-token holding from registration fees)
- **Asset_1_Value_USD:** UNKNOWN — value time-varying, requires live treasury snapshot
- **Asset_2:** ENS (governance token in DAO treasury / endowment)
- **Asset_2_Value_USD:** UNKNOWN — value time-varying, requires live treasury snapshot
- **Asset_3:** Diversified endowment assets managed by Karpatkey (includes stETH, rETH, and other staked-ETH variants)
- **Asset_3_Value_USD:** UNKNOWN — value time-varying, requires live treasury snapshot
- **Diversification_Non_Stable:** Medium-High — Karpatkey-managed endowment is intentionally diversified across ETH LSTs
- **Custody_Type:** Gnosis Safe (multiple — DAO wallet, endowment, working groups) governed by ENS token holders
- **Multisig_Address:** UNKNOWN — DAO wallet commonly cited as `0xFe89cc7aBB2C4183683ab71653C4cdc9B02D44b7` from memory; verify
- **Signer_Count:** ENS DAO root multisig has historically been 4-of-6 or 5-of-8 (UNKNOWN exact — governance-set)
- **Source_Links:** discuss.ens.domains; snapshot.org/#/ens.eth; etherscan.io; karpatkey reports

> All `Asset_*_Value_USD` cells above intentionally `UNKNOWN`. A live snapshot from DeBank / Zapper / Karpatkey dashboards / direct Etherscan token balance reads is required.

## 4. Coverage Gap — Remaining 45 DAOs to Prioritize

Each listed with a one-line rationale. (No data rows — these are the work queue.)

1. **Lido DAO** — Largest LST issuer; LDO + stETH dominance; complex Aragon-based governance.
2. **Optimism Collective** — Massive OP allocation across RetroPGF; dual-house governance.
3. **Arbitrum DAO** — Largest L2 treasury by ARB tokens; recent grants programs make composition fluid.
4. **Gnosis DAO** — Founder of Safe; treasury includes GNO + diversified ETH; benchmark for "good" custody.
5. **Curve DAO** — CRV-heavy; veCRV mechanics make non-stable composition unique.
6. **Balancer DAO** — BAL + 80/20 BPT positions; service-provider DAO model.
7. **SushiSwap** — SUSHI + xSUSHI; multiple historical multisig migrations.
8. **dYdX** — DYDX token; treasury moved to Cosmos chain (dYdX v4); unusual custody.
9. **Synthetix** — SNX-heavy; treasury Council elections; pDAO multisig.
10. **Yearn Finance** — YFI; multisig was famously small/elite; yvToken holdings.
11. **MolochDAO** — Original Moloch; small ETH treasury; historical importance.
12. **MetaCartel** — Moloch v2; ETH-denominated; community grants DAO.
13. **Gitcoin DAO** — GTC + diversified grants pool; many sub-Safes per workstream.
14. **Index Coop** — INDEX + product tokens (DPI, MVI); revenue from methodology fees.
15. **BadgerDAO** — BADGER + BTC-denominated assets (very unusual mix for an Ethereum DAO).
16. **Olympus DAO** — OHM + bonded LP positions; protocol-owned liquidity pioneer.
17. **Frax Finance** — FXS + frxETH + locked liquidity; AMO-controlled holdings.
18. **Convex Finance** — CVX + vlCVX + bribed CRV; metagovernance-heavy treasury.
19. **Rocket Pool** — RPL + ETH; oDAO vs pDAO custody split.
20. **Decentraland** — MANA + LAND NFTs; DCL DAO multisig.
21. **The Sandbox DAO** — SAND + LAND; corporate-adjacent governance.
22. **ApeCoin DAO** — APE; managed by Ape Foundation board, not pure on-chain.
23. **Nouns DAO** — ETH-only treasury by design (one Noun/day auction); benchmark for ETH-native DAO.
24. **PleasrDAO** — NFT-collector DAO; non-fungible heavy treasury; unusual valuation challenge.
25. **FWB (Friends With Benefits)** — FWB token; social DAO; small treasury.
26. **Bankless DAO** — BANK; media DAO with many sub-guilds and Safes.
27. **DXdao** — DXD + diversified positions; uses Reality.eth-based governance.
28. **Aragon DAO** — ANT; tooling DAO; historical merger with Vocdoni.
29. **1inch DAO** — 1INCH token; aggregator fees in many assets.
30. **Hop Protocol DAO** — HOP; cross-chain bridge DAO; multi-chain custody.
31. **Stargate DAO** — STG; cross-chain liquidity; LayerZero-aligned.
32. **GMX DAO** — GMX + esGMX + GLP composition; Arbitrum-native.
33. **Radiant Capital DAO** — RDNT; cross-chain lending; LayerZero OFT.
34. **Pendle DAO** — PENDLE + vePENDLE; yield-trading DAO.
35. **Maple Finance** — MPL/SYRUP; institutional lending DAO; partial off-chain treasury.
36. **Goldfinch** — GFI; RWA lending; mixed on/off-chain custody.
37. **Centrifuge DAO** — CFG; Polkadot+Ethereum hybrid.
38. **ShapeShift DAO** — FOX; multi-chain treasury after CEX shutdown.
39. **KeeperDAO / Rook** — ROOK; troubled history; informative custody case.
40. **Tornado Cash DAO** — TORN; governance frozen post-sanctions; instructive custody risk case.
41. **Mango DAO** — MNGO; Solana-based; post-exploit treasury reconstitution.
42. **Marinade Finance DAO** — MNDE + mSOL; Solana LST DAO.
43. **Jito DAO** — JTO + JitoSOL; Solana MEV-aware DAO.
44. **Osmosis DAO** — OSMO; Cosmos-based, very different custody model.
45. **Juno / Stargaze / Other Cosmos DAOs** — bucket for Cosmos-chain governance DAOs; CosmWasm-based custody differs sharply from EVM Gnosis Safe norm.

## 5. Why a Swarm Beats a Single Agent Here

- **Parallel browsing dominates wall-clock time.** Each DAO requires 3–8 page fetches (Etherscan balances, forum threads, Snapshot, dashboards). 50 × ~5 fetches = ~250 sequential page loads for one agent vs ~5 for each of 50 agents in parallel. End-to-end time difference is roughly 50×.
- **Per-entity depth matters more than breadth.** A sub-agent dedicated to a single DAO can chase a forum link to its Karpatkey report, cross-check the multisig on Etherscan, and read a recent treasury-management proposal. A single agent forced to cover 50 will satisfice on each, producing thin rows.
- **Volatile data needs a tight, synchronized read window.** USD values fluctuate; 50 parallel reads give a coherent snapshot at ~minute T. Sequential reads over hours produce inconsistent valuations that cannot be summed or compared.
- **Rate limits and explorer pagination favor concurrency.** Etherscan, DeBank, and forum APIs throttle per-IP. With 50 separate sub-agent sessions, effective throughput multiplies; a single agent hits the same ceiling repeatedly.
- **Independent quality audit becomes possible.** The coordinator pattern (read first line of each result file, re-dispatch partials) is impossible without sub-agents. A single agent has no second set of eyes to catch its own fabricated values or stale addresses — making `UNKNOWN`-heavy output the only honest path.
