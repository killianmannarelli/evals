# Product in 60 Homes — Campaign Plan

## Core Asset Description

**Product:** The "Lumen Solas" Desk Lamp

A 16-inch tall minimalist desk lamp with the following defining visual characteristics:

- **Shade:** Conical-shaped, matte black powder-coated steel, approximately 7 inches in diameter at the base of the cone, with a soft warm-white LED bulb (2700K) visible from below.
- **Stem:** Thin, polished brass cylindrical rod (5/8-inch diameter), 12 inches tall, with a subtle articulating joint just below the shade allowing a 35-degree tilt.
- **Base:** Round, solid Carrara marble disc (5.5-inch diameter, 1-inch thick) with natural grey veining on a white background; visible brass tension knob where the stem meets the base.
- **Cable:** Braided fabric textile cable in dark charcoal, approximately 6 feet long, terminating in a region-appropriate plug.
- **Switch:** Inline rotary brass dimmer on the cable, 18 inches below the base.
- **Overall silhouette:** Architectural, sculptural, gallery-modern; equally at home in industrial, Scandinavian, mid-century, and contemporary minimalist interiors.

This description must be reproduced (in a slightly compressed form) at the start of every image generation prompt to ensure the lamp's identity remains visually consistent across all 60 images. Only the *environment* around the lamp may vary.

## Campaign Goal

Produce 60 photorealistic lifestyle marketing images of the Lumen Solas lamp placed in 60 distinct, culturally and architecturally diverse global household settings. The collection will power a dynamic product-page image carousel on the DTC site, demonstrating that the lamp belongs anywhere in the world.

## Quality Criteria

A successful image must satisfy ALL of the following:

1. **Lamp fidelity:** Conical matte black shade, thin brass stem, round marble base — clearly visible, unaltered, recognizable as the same SKU in every shot.
2. **Environmental authenticity:** The setting visually matches the assigned location's architecture, materials, light, and cultural artifacts.
3. **Plausible electrical detail:** Where outlets or cables are visible, the plug/socket type matches the region's actual standard (e.g., Type G in Kenya, Type B in the USA, Type C/F in continental Europe, Type I in Australia).
4. **Photorealism:** Natural light direction, consistent shadows, no uncanny artifacts, no warped geometry, no extra lamp limbs.
5. **Composition:** The lamp is a clear hero element but does not dominate; the environment carries equal narrative weight.
6. **Resolution:** 2048 x 2048 minimum, sRGB, 16-bit ideal, web-ready JPEG/PNG export.

## Output Schema

Each of the 60 entries produces two files:

- Image: `app/artifact/images/result_{NNN}.png`
- Status JSON: `app/artifact/results/result_{NNN}.json`

The JSON schema is:

```json
{
  "id": 1,
  "location": "Tokyo micro-apartment",
  "status": "complete",
  "image_path": "app/artifact/images/result_001.png",
  "prompt_used": "Photorealistic lifestyle photo of ...",
  "region_outlet": "Type A/B (Japan, 100V)",
  "key_environmental_details": ["tatami flooring", "shoji screens", "..."]
}
```

`status` is one of `complete` (image generated, all quality criteria met) or `partial` (generation succeeded but with caveats noted in an `issues` field).

## Assignment Table — 60 Household Settings

1.  Tokyo micro-apartment with tatami flooring and shoji screens - result file: result_001.json
2.  Kenyan farmhouse near Naivasha with corrugated iron roof - result file: result_002.json
3.  Brooklyn loft with exposed brick and cast-iron columns - result file: result_003.json
4.  Parisian Haussmann apartment with herringbone parquet floors - result file: result_004.json
5.  Modernist glass house in a Brazilian rainforest near Paraty - result file: result_005.json
6.  Reykjavik turf-roof cottage with painted timber interior - result file: result_006.json
7.  Marrakech riad with carved cedar doors and zellige tile - result file: result_007.json
8.  Mumbai high-rise apartment with view of monsoon skyline - result file: result_008.json
9.  Santorini cave house with whitewashed plaster walls - result file: result_009.json
10. Mongolian ger (yurt) on the steppes outside Ulaanbaatar - result file: result_010.json
11. New Mexico adobe pueblo-style home in Santa Fe - result file: result_011.json
12. Buenos Aires Recoleta apartment with French balcony - result file: result_012.json
13. Stockholm Scandinavian-minimalist flat with light oak floors - result file: result_013.json
14. Hanoi tube house with internal courtyard - result file: result_014.json
15. Cape Town Bo-Kaap cottage with brightly painted exterior, modern interior - result file: result_015.json
16. Berlin Altbau apartment with double doors and stucco ceilings - result file: result_016.json
17. Cairo midcentury apartment in Zamalek, Nile-side - result file: result_017.json
18. Lisbon azulejo-tiled townhouse in Alfama - result file: result_018.json
19. Mexico City Roma Norte Art Deco apartment - result file: result_019.json
20. Sydney harbourside terrace house with iron lace balcony - result file: result_020.json
21. Helsinki design-forward apartment in a Alvar Aalto-era block - result file: result_021.json
22. Bangkok shophouse converted into a modern residence - result file: result_022.json
23. Seoul hanok with maru wooden floors and paper doors - result file: result_023.json
24. Dubai high-rise apartment overlooking the Burj - result file: result_024.json
25. Edinburgh tenement flat with Georgian sash windows - result file: result_025.json
26. Amsterdam canal house with steep wooden staircase - result file: result_026.json
27. Buenos Aires conventillo loft in San Telmo - result file: result_027.json
28. Lagos modern duplex in Lekki Phase 1 - result file: result_028.json
29. Istanbul yali waterfront wooden mansion on the Bosphorus - result file: result_029.json
30. Reykjavik concrete brutalist apartment with fjord view - result file: result_030.json
31. Quebec City stone farmhouse with timber beams - result file: result_031.json
32. Hong Kong Mid-Levels apartment with floor-to-ceiling city views - result file: result_032.json
33. Havana colonial home with terrazzo floors and louvered shutters - result file: result_033.json
34. Wellington wooden villa with corrugated iron roof - result file: result_034.json
35. Tel Aviv Bauhaus White City apartment - result file: result_035.json
36. Kyoto machiya townhouse with engawa veranda - result file: result_036.json
37. Vermont post-and-beam farmhouse in winter - result file: result_037.json
38. Mendoza adobe winery cottage at the foot of the Andes - result file: result_038.json
39. London Notting Hill stucco-fronted terrace flat - result file: result_039.json
40. Marfa, Texas concrete-and-glass desert home - result file: result_040.json
41. Singapore HDB flat with tropical balcony garden - result file: result_041.json
42. Oaxaca courtyard home with hand-painted walls - result file: result_042.json
43. Copenhagen waterside warehouse conversion in Nordhavn - result file: result_043.json
44. Mexico City Coyoacan colonial home with bougainvillea courtyard - result file: result_044.json
45. Toronto Victorian semi with bay window and refinished trim - result file: result_045.json
46. Bali jungle villa with thatched alang-alang roof - result file: result_046.json
47. Tbilisi balcony apartment in a 19th-century courtyard building - result file: result_047.json
48. Kerala backwater home with sloping clay-tile roof - result file: result_048.json
49. Sao Paulo Vila Madalena live/work loft - result file: result_049.json
50. Vancouver West Coast cedar-and-glass home in the forest - result file: result_050.json
51. Reykjavik fisherman's cottage repurposed as a writer's studio - result file: result_051.json
52. Athens neoclassical apartment in Plaka - result file: result_052.json
53. Marseille Le Corbusier Unite d'Habitation apartment - result file: result_053.json
54. Phnom Penh shophouse with French-colonial louvers - result file: result_054.json
55. Tasmanian off-grid timber cabin near Cradle Mountain - result file: result_055.json
56. Charleston single house with side piazza - result file: result_056.json
57. Hampi heritage stone house in rural Karnataka - result file: result_057.json
58. Beijing hutong courtyard home with grey brick walls - result file: result_058.json
59. Galway stone cottage on the Wild Atlantic Way - result file: result_059.json
60. Quito colonial-era home with carved wooden balcony in the Old Town - result file: result_060.json

## Regional Outlet Reference (for sub-agent prompts)

| Region | Type | Notes |
|---|---|---|
| Japan | Type A / B | 100V flat blades |
| Kenya, UK, Ireland, Singapore, HK, Malaysia | Type G | Three rectangular pins |
| USA, Canada, Mexico, Caribbean | Type A / B | Flat blades, Type B grounded |
| Continental Europe, S. America (most) | Type C / E / F | Round pins (Schuko in Germany) |
| Australia, NZ, China, Argentina | Type I | Angled flat pins |
| India, S. Africa, Nepal | Type D / M | Large round pins |
| Brazil | Type N | Round, slightly inset |
| Israel | Type H | Triangular three-pin |
| Switzerland | Type J | Three round pins, hexagonal recess |
| Italy | Type L | Three round pins inline |

## Sub-Agent Brief (template)

> You are sub-agent N, assigned to the "[Entity Name]" setting.
>
> **Step 1 — Research:** Synthesize a paragraph on the typical architecture, interior design, materials, color palette, light quality, and electrical outlet of [Entity Name].
>
> **Step 2 — Compose mango prompt:** Combine the lamp description from plan.md with the environmental details. Aim for a single cohesive paragraph describing one cinematic frame.
>
> **Step 3 — Generate & report:** Save the image to `images/result_{NNN}.png` and write `results/result_{NNN}.json` with `status`, `image_path`, and `prompt_used`.

## Coordinator Notes

- Coordinator messages are kept terse to honor the <15% token budget.
- Outputs are written under `/home/user/evals/work_single/adcf16d169322aa2/app/artifact/`.
- Final deliverable: `app/artifact/pdp_carousel_manifest.json` plus `app/artifact/summary.md`.
