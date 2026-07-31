# Model gaps register — Mother Tongues

Every open item this research programme has produced, tied to the specific subsystem it would
change. **This is the handover surface between research and the build.**

Priority: **P1** = closes a known visible defect · **P2** = adds real fidelity ·
**P3** = correctness housekeeping · **P4** = worth knowing, no action yet.

Status: **RESOLVED** = answered, with the answer recorded · **MEASURED** = quantified and ready
to apply · **DELIVERED** = the artifact exists · **APPLIED** = in the app, with the measurement ·
**RETIRED** = no longer needed · **CLOSED, negative result** = tried, did not work, recorded so
nobody retries it · items with no status are open.

IDs are referenced from white papers, code comments and commit messages. **Never recycle one.**

*Seeded 2026-07-31 at kickoff, from the scoping interview and `SOURCE-SURVEY.md`.*

---

## APPLIED

<!-- Rewritten in place as items land, so this file describes the app rather than a wish list. -->

### Round 3 (2026-07-31) — resolution, measured surface, autonyms, and the climate result

| item | what shipped | measured |
|---|---|---|
| **resolution** | master grid **16384×8192 (2.44 km at the equator)**, 76% of ETOPO1's native resolution, streamed as a 4-level tile pyramid with a 1 px skirt | 644 tiles, 271 MB total, **level 0 is 5.3 MB** — what first paint blocks on. Everest now reads **8271 m** where the 9.8 km grid read 6428 |
| **C3** | growing season from 12 MODIS LST climatology months, and peak-of-year NDVI, both NASA public domain | growing season **+0.470**, peak NDVI **+0.347**, |lat| **−0.527**, ruggedness **+0.155**. ⚠ **Holding latitude constant, growing season adds nothing (−0.091)** — it is largely what latitude was standing for |
| **C6** | Poisson count model, log land area as offset, IRLS hand-rolled | deviance explained: latitude **25.6%**, growing season **15.4%**, ruggedness **7.8%**, all + greenness **39.4%**. Dispersion **8–20** |
| **C7** | relief per km as an alternative ruggedness | **+0.192** (sd-elevation gives +0.155) — same sign, same order. The terrain finding survives redefinition |
| **D6** | rule 11 enforced in code: the card leads with the autonym, in its own script, from Wikidata P1705 (CC0) | **712 of 7,672 (9.3%)**, 56 non-Latin. **818 candidates rejected** as another language's phrase |
| **B5** | procedural sub-grid detail, engaged only where a screen pixel is finer than a source texel | never overrides measured relief |
| **fidelity** | NDVI tones the ground, biome classifies it, MOD10C1 snow gives a measured snowline, slope exposes rock | 8/8 registration on the shipped **level-3** tile |

**Four bug classes this round found and closed:**

| what | consequence | fix |
|---|---|---|
| Families indexed by the **first 254 alphabetically**; the rest fell to index 0 = "no language recorded" | **175 families rendered as empty ground** — all of Siberia's among them. Coverage was reported as 65% of land; it is **87%** | rank by number of languages; 254 keep an index, the remainder share 255, which the legend names |
| "Diversity" counted **overlapping polygons** | measured how many *datasets* covered a place. Read **1** across the New Guinea highlands and **43** in India, where 22 official languages were stacked on one cell | languages with territory within ~20 km, deduplicated per glottocode. Max is **13** |
| `wikipedia2024officiallang` — 158 country-shaped polygons | painted French across Gabon; the readout said "Indo-European" there | excluded: a map of state policy, not of speech |
| `AVHRR_CLIM_M` reads like a vegetation climatology and **is sea surface temperature** | wired in as greenness, saturated the whole land surface | every source now asserts the **physical range** of its quantity; the wrong dataset fails the build |

---|---|---|
| **B3** | 16-bit elevation, linear −11000…+9000, one channel | terracing equals the source DEM's own floor: **4.0% / 1.9% / 39.0% / 0.5%** in the four SCOPE §3 regions |
| **B1** | the lit-terrain substrate: relief shaded per pixel from the field's gradient, water as a depth-attenuated surface, biome as the land material | 8/8 named places registered, re-read from the **shipped** PNG by the build gate |
| **B2** | the language field: family hue × population luminance × diversity granularity, composed per pixel | **1,391,303 px** covered today, **1,330,358** before contact; max diversity **43** / **41** |
| **C5** | the amended claim, in SCOPE §1/§3 and in the About panel with its numbers | — |
| **C3** *(partial)* | biome as the greenness channel — 847 ecoregions, 15 classes | 2,762,246 px. ⚠ Biome is a *proxy* for growing season, not growing season itself; C3 stays open |
| **A1** *(partial)* | `frames.py` selftested and run by the build gate on every publish | ⚠ **Correction: the ingest does NOT import it.** `build_fields.py` contains no reference to `frames`. The identity discipline it encodes was applied by hand, which is exactly the arrangement the module exists to remove. Wiring it in is a new P1 item, **A7** |
| **A2** | *nothing to apply* | ⚠ **Correction: no reprojection is exercised in this build.** The GHS-POP product used is the **EPSG:4326** one, not the Mollweide one, so the 2.8 × 10⁻⁸ m converter is never called. The frame risk is genuinely lower than the survey assumed; the converter is retained for the 100 m products, which are Mollweide-only |
| **A5** | the attribution ledger, machine-checked: `attribution.py` is the authority, the build regenerates `web/data/attribution.json` from it and **refuses to publish on any drift**, and the About panel renders the ledger rather than prose | 7 rows, **5 ingested and all licence-verified at the source**, 0 ShareAlike in the build. Ecoregions 2017's CC-BY-4.0 was read at source because the selftest refuses to ship an unverified ingested source |
| **B4/D8** *(partial)* | `coverage.py` measures the **shipped** rasters with an independently written decoder; the number is on the frame and in About | **64.8% of land area** and **73.3% of the world's people** stand on mapped ground (before contact: 61.2% / 71.1%). By window: Congo 100%, India 89%, Australia 87%, Sahara 85%, Amazon 61%, New Guinea 60%, Great Plains 54%, **Siberia 31%** |
| **A4** | enforced in the build, not trusted: the publish gate greps the shipped HTML and JS for a four-digit year adjacent to "before contact" and refuses | clean |
| **A3** | the licence gate drives the ingest allowlist | **26 of 29** repos ingested, 3 NC excluded by name |
| **A6** | Glottolog filtered by `category` | **7,672** spoken-L1 with coordinates, not 8,304 |
| **deploy** | `build_site.py` as the only route; live on Pages | gate: 4/4 selftests · 16.7 MB of 30 · 6/6 registration on the shipped raster · live stamp verified |

---

## A. Frames and identity — nothing is combined until these exist

| # | P | item | touches | from |
|---|---|---|---|---|
| **A1** | **P1** | `frames.py` with selftests: glottocode as key, ISO 639-3 as alias only, autonym-first names, (value, year, source) counts | build ingest, every card | SCOPE §6 |
| | | **DELIVERED.** `Research/modeling/frames.py`, stdlib only, selftest passes. Enforces: ISO rejected as a key; a count without year+source refuses construction; the axis label for the earlier snapshot cannot print a year; a name set never promotes a slur to the title | | |
| **A2** | **P1** | Reproject Mollweide→WGS84 once at ingest and record the residual | `build/`, population field | SURVEY §2 |
| | | **DELIVERED, MEASURED: 2.8 × 10⁻⁸ m** worst round-trip over a 180×52 global lattice. Hand-rolled (no pyproj here), which turned out better — the residual is recorded and out-of-domain points **raise** rather than extrapolate. Antimeridian pinned: `_wrap180(+180) = −180`, so x is negative at +180 | | |
| A3 | **P1** | Per-repo licence gate on the polygon ingest | `build/`, polygon ingest | SURVEY §1 |
| | | **DELIVERED. 26 of 29 shippable, 3 excluded by name.** Correction to the survey's framing: it is 29 *dataset* repos, not 34 — five are infrastructure. GitHub's licence API returns `NOASSERTION` for all three NC repos, so the gate reads licence **text** | | |
| **A7** | **P1** | **NEW, from round 2's own audit.** `build_fields.py` does not import `frames.py`. Every identity and coordinate rule the module encodes — glottocode as key, ISO as alias only, (value, year, source) counts, the autonym-first display order — was applied by hand in the ingest instead. That is the arrangement A1 was written to end, and it is how the frame bugs in the two prior projects survived so long. Route the ingest through `Registry` and `NameSet` | `build/build_fields.py` | round 2 |
| **A6** | **P2** | **NEW.** Filter Glottolog by `category`, never by `Level`: `Level == language` yields 8,618 but only **7,674** are spoken L1 — a 12% inflation that would put 227 sign languages and 380 bookkeeping placeholders on a terrain-diversity surface | `build/` ingest | round 1 |
| A4 | P2 | The **before-contact snapshot carries no year**. Enforce in code that no year label can be rendered for it, and attach per-region contact dates to cards instead | time engine, cards | SCOPE §6 |
| A5 | P3 | **D3 attribution ledger** kept current: a row per ShareAlike source with its exact attribution string, checked by the build gate so it cannot go stale | `SOURCE-SURVEY.md` §1, About panel | SCOPE §12 D3 |

## B. The substrate — the thing the work is judged on

| # | P | item | touches | from |
|---|---|---|---|---|
| **B1** | **P1** | **The lit-terrain substrate**: elevation encoded for the *land* relief band, relief shaded per pixel from the field's gradient, water as a surface. **Before any language layer.** Screenshot and assess against the SCOPE §3 sentence | `web/`, shader | WORKING-RULES §13, SCOPE §3 |
| **B2** | **P1** | **The language field**: family hue × population luminance × diversity granularity, composed per pixel. The moment this reads as a rendered world rather than a chart is the moment the project exists | shader, `build/` | SCOPE §3 |
| B3 | **P1** | Vertical encoding decision, measured before it is chosen | `build/fieldpack`-equivalent | TRAPS §B1–B2 |
| | | **MEASURED → STAGED.** The inherited signed-sqrt ±8000 8-bit encoding has a **62.7 m** quantum at 2000 m, creating steps of **1.95°** against a true median slope of **1.34°** in the New Guinea highlands — it invents more relief than the terrain has. Terracing: 30.9% (inherited) vs **4.0%** at 16-bit, and the raw DEM's own floor is also **4.0%**, so at 16-bit the encoding contributes nothing. **Decision: single 16-bit channel, linear −11000…+9000.** 16.8 MB at 4096×2048, paid once because terrain is static here | | |
| B4 | P2 | Coarse-fallback territories render **visibly differently** from real polygons — a viewer must be able to tell 62.5% from the remainder without reading About | shader, legend | SURVEY §3 |
| B5 | P2 | Procedural sub-grid detail keyed to a shipped material coordinate, so zoom reveals structure rather than running out of it | shader | ARCHITECTURE-PATTERNS §7 |

## C. The spine — the diversity model

| # | P | item | touches | from |
|---|---|---|---|---|
| **C1** | **P1** | The diversity model and its per-cell residual audit | `Research/modeling/`, diversity field | SCOPE §4 |
| | | **FIRST MEASUREMENT DELIVERED, and it partly falsifies the claim.** Spearman(ruggedness, richness density) = **+0.141**; **+0.108** with \|latitude\| partialled out; \|latitude\| alone = **−0.582**. Latitude beats terrain ~4×. Per macroarea: N America +0.238, Eurasia +0.173, S America +0.145, Australia +0.113, **Papunesia +0.024, Africa +0.006**. Robust at 1°/2°/4°/6°. See `WP-01` |
| **C5** | **P1** | **NEW, BLOCKING.** Amend SCOPE §1's claim and §3's visual sentence: terrain is **not** "most of the explanation", and the shimmer does **not** visibly follow the terrain in Papunesia — the region §3 names. Proposed replacements in `WP-01` §4. **Needs the user's assent; SCOPE is the contract** | `SCOPE.md`, About panel | round 1 |
| **C3** | **P1** | **PROMOTED from P2.** Acquire a growing-season / climate field. It is now the highest-value item in the register: without it the spine measures the wrong variable, and the model cannot make the claim it should be making | `Research/`, diversity field | round 1 |
| **C6** | **P1** | **NEW.** Re-estimate with a zero-inflated count model (Poisson / negative binomial, land area as offset). Only **1,672 of 6,143** land cells hold a language, so a rank correlation on density is a first look, not the shipped statistic | `Research/modeling/diversity.py` | round 1 |
| C2 | P2 | **PARTLY ADDRESSED.** The method risk is real and now quantified: no global continuous linguistic surface exists, and our first terrain-only correlation is weak. Read the regional dialectometry literature before choosing an interpolation | `Research/`, C1 | SURVEY §7 |
| C7 | P2 | **NEW.** Try relief-per-kilometre instead of elevation standard deviation. The current measure may be answering "are there mountains in this cell" rather than "is the ground rough where people live" | `diversity.py` | round 1 |
| C4 | P2 | Reproduce published environment-versus-diversity relationships as the external check on C1 | audits | SCOPE §8 |
| C8 | P2 | **NEW.** Settlement time-depth, a C1 predictor with no ready source. Derive per region from the archaeological and aDNA literature; carry its wide uncertainty | `Research/`, diversity field | SURVEY §6 |

## D. Cards, texts and voices

| # | P | item | touches | from |
|---|---|---|---|---|
| **C9** | **P1** | **NEW.** The Poisson model's dispersion is **8–20**. Poisson standard errors are therefore meaningless and only the effect sizes above are quotable. A negative binomial (or quasi-Poisson) is owed before any interval is published | `climate.py` | round 3 |
| **D9** | **P2** | **NEW.** Autonym coverage is **9.3%**. Wikidata P1705 is the only CC0 source wired and a third of what it returns is another language's phrase. CLDR carries autonyms for ~600 high-population locales under the Unicode licence and would lift coverage weighted by speakers far more than by count | `build/fetch_autonyms.py` | round 3 |
| **D10** | P2 | **NEW.** Font coverage: `wáꞏšiw ʔítlu` renders U+A789 as a missing-glyph box in the system stack. Rule 11 says "in its own script", and a tofu box is not the script. Needs a subsetted webfont (register D4's real content) | `web/css`, `build/` | round 3 |

| # | P | item | touches | from |
|---|---|---|---|---|
| **D6** | **P1** | **NEW, and it breaks a standing rule.** The cards show Glottolog *reference names*, not autonyms. CLAUDE.md rule 11 and SCOPE §7 require the autonym first, and no autonym source is wired. The card says so explicitly rather than passing an exonym off as a language's own name — but that is a disclosure, not a fix | cards, `build/` | round 2 |
| **D7** | P2 | **NEW.** The grid is 4096×2048 (~10 km): small-island languages are under-resolved — a probe in the Vanuatu channel returns open ocean. Small archipelagos need either a finer grid or a point-symbol fallback that is honestly marked | `build/`, shader | round 2 |
| **D8** | P2 | **NEW.** Polygon coverage inside covered regions is patchy at pixel scale — parts of the New Guinea highlands return "no polygon" while neighbours are covered. Quantify coverage per macroarea and surface it, rather than leaving it to the toggle | `build/`, About | round 2 |

| # | P | item | touches | from |
|---|---|---|---|---|
| D1 | **P1** | **Card generator with the three-tier fallback and the tier named in the heading.** ~8,600 cards; a generic list presented as local is a lie | cards | SCOPE §7 |
| D2 | P2 | **Text tiers wired with a per-item provenance line**, and the parallel-prose tier **behind a single feature flag** so D2-the-decision can be reversed in one commit | cards, `build/` | SCOPE §12 D2 |
| D3 | P2 | **Audio pipeline with a per-file licence gate**, plus the coverage number displayed rather than buried, and the withholding archives named and linked | cards | SCOPE §12 D4 |
| D4 | P2 | Script rendering in the language's own orthography; **font subsetting per language, loaded on card open**, never up front | cards, budget | SCOPE §11 |
| D5 | P3 | Typological facts rendered as prose a non-linguist can read, from Grambank/WALS | cards | SCOPE §7 |

## E. Honesty layers — these are content, not caveats

| # | P | item | touches | from |
|---|---|---|---|---|
| **E1** | **P1** | **The independent witness**: census language returns ingested and scored against our counts and distributions. Build it early — it is the instrument every later dispute is settled with | audits | SCOPE §8 |
| E2 | **P1** | **Documentation-status field drawn**, so a thinly surveyed region renders as thinly surveyed rather than as linguistically uniform | shader | SCOPE §5 |
| E3 | P2 | **Language-shift events** authored with named actors and dates, so decline curves have causes attached | features, cards | SCOPE §9 |
| E4 | P2 | Contested language areas drawn as contested; reproduce the indigenous-territory source's own disclaimer where used | shader, About | SCOPE §9 |
| E5 | P2 | The alternative language counts shown in the UI, not just the chosen authority's | About, readout | SCOPE §6 |

## F. The research programme itself

| # | P | item |
|---|---|---|
| F1 | P2 | **Two emails worth more than more searching:** the UDHR maintainer, for an explicit grant (would retire the D2 risk); and the ~820-language oral-history archive that is NC by default (would multiply audio coverage severalfold) |
| F2 | P3 | ⚠ **Legal call on the CC0 speech dataset** whose package forbids re-hosting while its content is CC0 |
| F3 | P3 | ⚠ Confirm exact licence strings for StatCan and India Census tabulations |
| F4 | P4 | Native Land Digital: written permission is the only route to 936 language polygons |

---

**What round 1 checked and found CLEAN** — so the next round does not re-litigate it:

- **Glottolog's counts reproduce exactly** from the CLDF tables: 27,177 languoids · 8,618
  language-level · 7,674 spoken L1 · 13,706 dialects · 4,853 family-level · 227 sign · 380
  bookkeeping. The ingest is not misreading the source.
- **The licence gate's classifier refuses correctly** on synthetic input, including the case that
  matters: CC-BY-**NC**-SA is excluded on the NC, not admitted on the SA.
- **The DEM's orientation is correct** — asserted against Everest, the Dead Sea, the mid-Atlantic
  and the East Antarctic plateau, because a test satisfied by the wrong hemisphere is a real
  prior-project bug.
- **The cell-size sweep found no MAUP artefact.** The weak terrain correlation and the strong
  latitude correlation both hold at 1°, 2°, 4° and 6°.
- **16-bit is sufficient, not merely better.** It reaches the source DEM's own quantisation floor,
  so there is nothing to gain from more precision. Do not revisit.

**What the survey did NOT find** — recorded so the next round does not re-litigate it:

- **No open polygon source beyond Glottography.** WLMS, Ethnologue, GADM and UNESCO were each
  checked and each forbids redistribution; the OSM layer is ODbL, which is a separate decision.
- **No global language-density surface, anywhere.** The search returns the population literature.
  This is a negative result with a positive reading: the idea has no precedent.
- **No dated language-death dataset.** Only ~57 language items carry a dissolution date.
- **No machine-readable language-shift event catalogue.** Hence E3 is authored.
- **Glottolog does carry attestation years** — an earlier assumption that it did not was wrong.

---

**Count after round 1: 31 items — 13 at P1.** Delivered: A1, A2, A3, B3 (measured), C1 (first
measurement), A6. New: C5, C6, C7, C8. Promoted: C3 to P1.

The ones that would move the model furthest, in order:

1. **C5 — amend the claim.** Blocking, and it is the user's call. Everything downstream of the
   claim is provisional until it is settled.
2. **C3 — get a climate field.** The spine is currently measuring the secondary variable.
3. **B1 + B2** — the lit substrate and the language field, now unblocked by B3's encoding decision.
   Until the frame reads as a rendered world, no other item matters.
4. **C6** — re-estimate with a count model; the density correlation is a first look.
5. **E1** — the census witness, built early because it settles every later dispute.
