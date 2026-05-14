# Sneaker Drop: Global Edition - Campaign Plan

## Header: Task & Sneaker Description

### Task
Coordinate a parallel multi-city campaign to generate 45 unique localized
"key visual" images for a new sneaker drop. Each of 45 sub-agents is
assigned exactly one global city. Each sub-agent will (1) read this plan,
(2) locate its city by item number, (3) craft a detailed image prompt that
synthesizes the sneaker description, local cultural elements, an influencer
wearing the sneakers, and the editorial photography style, then (4) call
`mango` to generate `result_{NNN}.jpg` and write `result_{NNN}.txt` with
status and the exact prompt used.

### Sneaker Description (seed 3D model - must be reproduced consistently in every image)

**Name:** AETHER PROTO-01 ("Aether One")

**Silhouette:** Low-mid top runner with a sculpted, futuristic "bio-tech"
shape. Slim, performance-leaning toe box; aggressive heel counter that
flares outward; chunky but not bulbous midsole.

**Colorway:** Core "Polar Drift" - bright optical white as the base color
across roughly 70% of the upper, with cool ice-blue ("glacier blue")
overlays, accents of warm sand-beige on the heel counter and tongue label,
and small neon coral hits on the laces, branding, and pull-tab.

**Materials (upper):**
- Optical-white **smooth leather** on the toe box and forefoot mudguard.
- Cool ice-blue **suede overlays** on the mid-panel and eyestay.
- Translucent **TPU window** on the lateral side revealing an internal
  honeycomb structural cage in glacier blue.
- Lightweight **engineered mesh** on the tongue and collar in pale ivory.
- Embroidered "AETHER" wordmark in neon coral on the lateral heel.

**Sole / Midsole:**
- Sculpted, segmented EVA midsole in dual-density foam: bright white on
  top, glacier-blue carrier on the bottom.
- Visible carbon-fiber forefoot plate edge peeking through the lateral
  midsole.
- Translucent rubber outsole with hexagonal lugs; you can see the foam
  through it.

**Unique features (must appear in every image):**
- Translucent neon-coral heel tab with embossed serial "PROTO-01".
- Glow-in-the-dark lace tips (aglets).
- Asymmetric lacing system: 6 eyelets lateral, 5 eyelets medial.
- Tonal ice-blue 3D-printed lateral cage visible through the TPU window.
- Small reflective dot pattern on the medial side that catches light.

**Branding:** "AETHER" wordmark on lateral heel + circular "A/01" debossed
medallion on the tongue. No other logos.

### Campaign Tagline
**"Drop the Map. Wear the Coordinates."**

---

## Assignment Table (Sub-agent ID -> City)

1.  Tokyo, Japan - generate key visual - result file: result_001
2.  New York City, USA - generate key visual - result file: result_002
3.  London, United Kingdom - generate key visual - result file: result_003
4.  Paris, France - generate key visual - result file: result_004
5.  Seoul, South Korea - generate key visual - result file: result_005
6.  Berlin, Germany - generate key visual - result file: result_006
7.  Shanghai, China - generate key visual - result file: result_007
8.  Los Angeles, USA - generate key visual - result file: result_008
9.  Hong Kong, Hong Kong SAR - generate key visual - result file: result_009
10. Milan, Italy - generate key visual - result file: result_010
11. Mexico City, Mexico - generate key visual - result file: result_011
12. Sao Paulo, Brazil - generate key visual - result file: result_012
13. Mumbai, India - generate key visual - result file: result_013
14. Bangkok, Thailand - generate key visual - result file: result_014
15. Jakarta, Indonesia - generate key visual - result file: result_015
16. Sydney, Australia - generate key visual - result file: result_016
17. Melbourne, Australia - generate key visual - result file: result_017
18. Toronto, Canada - generate key visual - result file: result_018
19. Montreal, Canada - generate key visual - result file: result_019
20. Vancouver, Canada - generate key visual - result file: result_020
21. Chicago, USA - generate key visual - result file: result_021
22. Miami, USA - generate key visual - result file: result_022
23. Atlanta, USA - generate key visual - result file: result_023
24. Lagos, Nigeria - generate key visual - result file: result_024
25. Johannesburg, South Africa - generate key visual - result file: result_025
26. Cairo, Egypt - generate key visual - result file: result_026
27. Istanbul, Turkey - generate key visual - result file: result_027
28. Dubai, UAE - generate key visual - result file: result_028
29. Tel Aviv, Israel - generate key visual - result file: result_029
30. Moscow, Russia - generate key visual - result file: result_030
31. Amsterdam, Netherlands - generate key visual - result file: result_031
32. Stockholm, Sweden - generate key visual - result file: result_032
33. Copenhagen, Denmark - generate key visual - result file: result_033
34. Madrid, Spain - generate key visual - result file: result_034
35. Barcelona, Spain - generate key visual - result file: result_035
36. Lisbon, Portugal - generate key visual - result file: result_036
37. Athens, Greece - generate key visual - result file: result_037
38. Dublin, Ireland - generate key visual - result file: result_038
39. Zurich, Switzerland - generate key visual - result file: result_039
40. Vienna, Austria - generate key visual - result file: result_040
41. Buenos Aires, Argentina - generate key visual - result file: result_041
42. Bogota, Colombia - generate key visual - result file: result_042
43. Lima, Peru - generate key visual - result file: result_043
44. Manila, Philippines - generate key visual - result file: result_044
45. Auckland, New Zealand - generate key visual - result file: result_045

---

## Output Schema (per sub-agent)

Each sub-agent N (where NNN is N zero-padded to 3 digits) must produce
**two files** in `/app/artifact/`:

1. `result_{NNN}.jpg` - a single 16:9 (1920x1080) editorial image showing
   the AETHER PROTO-01 sneaker on a local influencer in the assigned city.
2. `result_{NNN}.txt` - a UTF-8 plaintext status file with exactly two
   lines:
   - Line 1: `STATUS: complete`
   - Line 2: the full, exact prompt string passed to `mango` to generate
     `result_{NNN}.jpg` (single line; no internal newlines).

Filename convention: zero-pad to 3 digits (e.g., `result_001`,
`result_023`, `result_045`).

---

## Quality & Style Criteria

### Style
- Editorial fashion photography, magazine-cover quality.
- Shot on a 35mm equivalent full-frame camera, f/2.8 - f/4 for shallow but
  readable depth of field.
- Golden hour or blue hour lighting whenever possible to fit the
  "hype + exclusive" mood; otherwise high-contrast night lighting with
  ambient neon.
- Cinematic color grade: cool shadows, warm midtones, slightly crushed
  blacks, lifted highlights - feel of a luxury campaign.
- 16:9 landscape orientation only.

### Subject ("local influencer")
- One person, mid-20s to mid-30s, wearing the AETHER PROTO-01 sneakers
  prominently and clearly visible (do not crop or obscure the shoes).
- Outfit must reflect the city's contemporary street-fashion identity.
- Pose should be confident, candid, slightly off-axis.
- Diverse, real-feeling face; one influencer per image (no crowds).

### Background / Localization
- Must unambiguously read as the assigned city within 2 seconds.
- Use at least two of: iconic architecture, local public transit, local
  street-art style, distinctive signage/typography, geographic feature,
  cultural texture (markets, alleys, plazas).
- Avoid clichéd tourist framings; prefer oblique, locals-only angles.

### Mood
- "Hype" - energy, motion, edge.
- "Exclusive" - confident, slightly aloof, premium.
- The sneaker is the hero; the city is the stage; the influencer is the
  conduit.

### Hard constraints (must hold for every image)
- The AETHER PROTO-01 colorway/materials/unique features described above
  must be visually consistent across all 45 images.
- Sneakers must be on-foot (no flat-lay, no studio).
- No text overlays in the image itself (text will be added at the HTML
  layer).
- No competing brand logos.
- 16:9, ~1920x1080.

---

## Prompt Recipe for Sub-agents (synthesis template)

Each sub-agent should craft its `mango` prompt by combining:
- (a) the AETHER PROTO-01 description (optical white leather, glacier-blue
  suede overlays, translucent TPU window with internal blue cage, neon-
  coral heel tab, asymmetric lacing 6x5),
- (b) the assigned city's vibe (specific neighborhood, time-of-day,
  weather, ambient color),
- (c) the influencer (age, styling, pose, ethnicity appropriate to the
  city's contemporary street scene without stereotyping),
- (d) the photographic style (editorial fashion, 35mm, f/2.8, golden or
  blue hour, cinematic grade, 16:9).

Sub-agents should write the prompt as a single dense paragraph of ~80-160
words, ending with the technical tail:
`editorial fashion photography, 35mm, shallow depth of field, cinematic
color grade, 16:9, ultra detailed, hyperreal`.
