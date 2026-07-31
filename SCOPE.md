# SCOPE — Mother Tongues

The contract. Produced by the scoping interview at kickoff; every later "was that in scope?" is
settled by reading this file. Amend it deliberately, with a date, rather than drifting.

*Scoped 2026-07-31. Pre-filled from Plate 01 of `~/Modeling Studio/CANDIDATE-PROJECTS.md`, whose
source survey ran before this kickoff — see `Research/SOURCE-SURVEY.md`.*

---

## 1. The claim

> There are roughly seven thousand languages alive now, and a long tail of others we know only from
> inscriptions, wordlists and the memory of the last person to speak them. This atlas draws them as
> what they actually are — **populations on real ground**, each with ancestors, neighbours, a script
> or none, a body of text, a recorded voice where one exists, and for about half of them a horizon
> inside this century.
>
> Zoom to anywhere inhabited and it tells you what is spoken there, what was spoken there before,
> and how the two are related. Zoom out and the shape of human diversity appears — and it is not
> spread evenly. It is piled up in a few mountain ranges, river deltas and island chains, and thin
> across the great plains and empires. **The terrain is not the backdrop to that pattern; it is most
> of the explanation.**

A viewer should leave able to say **why linguistic diversity is where it is** — and should find that
the surface itself makes the answer visible, because the model draws languages as speakers on
terrain rather than as labels on a map.

## 2. Extent

| | |
|---|---|
| time (v1) | **two snapshots: before contact ↔ today.** Not a continuous axis — see §12 D1 |
| time (later) | v2 adds dated-phylogeny animation for the ~12% of languages that support it; v3 pushes back to the linguistic horizon (~8–10 ka) and forward to a labelled 2100 vitality projection |
| stored step | the two snapshots; plus per-language attestation dates and vitality status |
| shown step | v1 crossfades between the two snapshots; **no year label on the contact snapshot** — see §6 |
| space | global, at a resolution that resolves one language's territory, and in the diversity hotspots one valley |
| finest legible thing | a single language's speaker distribution; a single dated attestation |
| projection / substrate | **real Earth** — see §3. The family tree is a *second view*, never the substrate |

**v1's right edge is today.** No forecast pixels. The 2100 vitality projection is a v3 layer and
will be drawn as an explicitly labelled projection when it arrives.

## 3. The substrate

**The real place this model renders:** the inhabited surface of the Earth — terrain, water,
coastline — lit per pixel, with the linguistic field composed over gridded population. Not a
metaphor and not a projection of anything abstract. When a viewer sees diversity shimmer along a
mountain range, they are seeing the actual mountain range that caused it.

**The fields it is composed from,** per pixel at render time:

| field | resolution | encoding | source or mechanism | confidence channel? |
|---|---|---|---|---|
| elevation | ~1 km near zoom, coarser globally | signed, encoded for the *land* relief band — not the ocean floor | open public-domain / CC0 global topo-bathymetry | no (well constrained) |
| relief shading | derived per pixel | — | gradient of the elevation field, lit from a fixed direction — **never a baked hillshade image** | no |
| population density | 100 m–1 km, 5-year steps | log-companded | open CC-BY population raster, **1975 floor** (§12 D3) | yes — pre-1975 is reconstructed |
| dominant language | per cell | family id + language id | polygons × population, resolved per pixel | yes — polygon vs coarse-fallback origin |
| **diversity** | per cell | count, companded | **modelled** — the spine (§4) | yes |
| ruggedness · growing season | derived | — | from elevation and climate; the diversity model's predictors | no |
| documentation status | per cell | ordinal | the catalogue's descriptive-status field | it *is* the confidence layer |

**The visual bar, as a testable sentence:**

> At continental zoom the New Guinea highlands and the Caucasus **shimmer** into many small
> language territories while the North China Plain is one vast smooth field — and the shimmer
> visibly follows the terrain, lit from the elevation field, with no traced borders anywhere.

**Three concrete facts a viewer must be able to read off a full-frame screenshot with no legend:**

1. **which language family dominates here** — from hue;
2. **roughly how many people speak it here** — from luminance, because the field is bright where
   people are and dark where nobody lives;
3. **whether the ground is rugged** — from the lit relief underneath, and therefore whether the
   diversity pattern above it is explained.

Checked every round against WORKING-RULES §13c. **The family tree, the phylogenies and any
similarity space are secondary views**, reached by selecting a language from the surface. None of
them is ever the substrate.

## 4. The layer table

Features sit *on* the rendered substrate; they never replace it.

| layer | kind | mechanism (if modelled) or source (if authored) | engine |
|---|---|---|---|
| Terrain, coasts, rivers, lit relief | **authored** | open global topo-bathymetry, composed per pixel | field |
| Ruggedness · growing season · biome | **modelled** | derived from elevation and climate — the diversity model's predictors | field |
| Gridded population | **authored** | open CC-BY raster, 5-year steps, 1975 floor | field |
| **Language field** | **modelled** | family hue × speaker luminance × diversity granularity, composed per pixel | field |
| Language territories | **authored + modelled** | CC-BY areal polygons for ~5,300 languages; coarse administrative fallback for the rest, **labelled as coarse** | feature → field |
| **Diversity** | **modelled** | richness per unit area from ruggedness, growing season, coastal and river access, settlement time-depth — **the spine** | field |
| Genealogy | **authored** | the catalogue's classification, as a tree per family | second view |
| Dated phylogenies | **authored** | published posterior samples, drawn *as posteriors* (v2) | second view |
| Attestation | **authored** | first and last attested date per language, with confidence | feature |
| Scripts | **authored** | writing systems per language with adoption dates, rendered in the actual script | feature + cards |
| Sample texts | **authored** | three tiers — wordlists (~6,100 languages), parallel prose (~450), CC0 lexemes (~1,550) | cards |
| Voices | **authored** | one openly licensed recording where one exists — **~6–8% of languages** (§9) | cards |
| Vitality | **authored** | the catalogue's endangerment status, six levels | field + cards |
| **Documentation status** | **authored** | how well each language is actually described — the layer showing the map is partly a map of survey effort | field |
| Language-shift events | **authored** | dated policy and violence: school bans, resettlement, residential schooling | feature |
| Chapters — the tour | **authored** | the hotspots and the great spreads | timeline |

**The spine, and it is built first.** The diversity model: predict language richness per grid cell
from terrain ruggedness, growing-season length, coastal and river access, and settlement time-depth,
then score against observed richness **cell by cell, with no averaging**. It is what makes the
surface mean something. Without it this is a beautiful inventory; with it, the shimmer over the
highlands is a prediction that came out right, and the cells where it fails — because history is not
geography — become the most interesting layer in the model.

## 5. The evidence boundary

Three boundaries, and the model changes behaviour at each.

| boundary | where | what the UI does past it |
|---|---|---|
| **the linguistic horizon** | ~8–10 ka; beyond it relatedness is not demonstrable | draws **nothing**. Terrain keeps rendering; languages are absent, not faded guesses. Proposed deep macrofamilies are named in About as *proposed, by whom* and never drawn |
| **the documentation boundary** | wherever a region was thinly surveyed | documentation status is a **drawn field**, so thin description renders as thin description rather than as linguistic uniformity |
| **the vintage boundary** | speaker counts, many decades old and copied between sources | every count carries **the year of the estimate and its source**; a bare number is not a datum here |

**Deep-time hard limits, measured, from the survey:** of the ~217 languages carrying an attestation
date, only **82 have a polygon**, and of the pre-Common-Era ones **nine** do — Hittite, Sanskrit,
Old Persian, Avestan, Attic Greek, Lycian, Oscan, Umbrian, Latin. Only **524 of 1,356 extinct
languages (38.6%)** have an area at all. The "past" in *past and present* is a handful of
well-documented ancient languages plus an honest confidence gradient. v1 does not pretend otherwise.

**Where the sources disagree, and the shape of the disagreement:**

| disagreement | shape | how the model handles it |
|---|---|---|
| how many languages exist | **amount** — ~8,600 language-level vs ~7,100 vs ISO's 7,927, from different splitting policies | one stated authority, **with the alternative counts shown in the UI**. Never one number as the fact |
| deep macrofamilies (Transeurasian, Amerind, Nostratic) | **existence** | not drawn. Named in About as proposed, with who disputes them |
| validity of Bayesian dating | **existence of the method's warrant** | phylogenies drawn *as posteriors*; the published critique cited on the card |
| whether isolates are real or artefacts of poor documentation | **existence of the category** | the documentation-status layer is the answer: an isolate in a thinly described region renders as thinly described |
| language-area boundaries in contested regions | **position** | drawn as contested; soft fields, never hard borders |

## 6. The canonical frame

The highest-value section in this file. Every source is converted into this frame, and the
conversions live in `Research/modeling/frames.py` with selftests.

| dimension | canonical choice | sources that differ, and the conversion |
|---|---|---|
| **language identity** | the catalogue's stable **glottocode** | names collide, nest and get reused; two sources' "Miao" are not the same object. ISO 639-3 codes carried as an alias, never as the key |
| **names** | **the autonym first, always**, in its own script, with the English exonym second and historical exonyms marked as historical | the most important decision in the project. Many exonyms are colonial or slurs. Alias table per language; display order enforced in code, not left to data entry |
| **language vs dialect** | one stated splitting authority, named in About, **with alternative counts shown** | the varieties of Chinese, Arabic and Hindi–Urdu, and the successor languages of Serbo-Croatian, are counted differently for non-linguistic reasons |
| **speaker counts** | value **+ year of estimate + source**, always as a triple | a bare number is not a datum; sources copy each other's decades-old figures forward |
| **the "before contact" snapshot** | **no single year.** A per-region pre-contact state, with the region's contact date on the card where known | contact ranges from the 1490s to the 20th century and never happened in some places. Putting one year on this snapshot would be the frame error of the project |
| **dates** | one era convention; radiocarbon-derived dates as calibrated ranges with the curve named | mixing calibrated and uncalibrated moves deep layers by centuries |
| **scripts** | the community's current orthography, in its own script | transliterating everything to Latin is a choice, and the wrong one here |
| **coordinates** | WGS84 | polygons, points and rasters arrive in different grids; reproject once, at ingest, and record the residual |

**Never combine two sources without checking they are in the same frame.** This is the most
expensive class of bug in this kind of project.

## 7. The card contract

Every language card carries:

- **autonym**, in its own script, with a pronunciation, and the exonym second
- **lineage**, clickable up the tree, each step named
- **speakers** — value, year, source — and vitality status
- **where** — the territory on the surface, plus the states it spans
- **script(s)**, with adoption dates, rendered in the actual writing system
- **first and last attestation**, where either is known
- **a sample text** — the same passage across every language that has one, plus a wordlist tier
- **a voice**, where an openly licensed recording exists
- **what it is like** — three or four typological facts as prose a non-linguist can read
  (*verb-final; eighteen noun classes; no tone; four vowels*)
- **neighbours and borrowings**, because no language on this map is alone
- **sources and confidence** on all of it

**Fallback tiers, and the heading names the tier:**

1. curated exception → **"Recorded for this language"**
2. model-derived → **"Derived from its family and region"**
3. generic → **"Typical of this family"** — *and the heading says so.*

Approximate counts: ~8,600 language cards (200–400 hand-written, the rest generated and audited) ·
~250 family cards · ~170 script cards · the tour chapters.

## 8. The standard for done

**Named artefacts a result is compared against:**

1. **the diversity model** — published environment-versus-diversity relationships, scored per grid
   cell, no averaging;
2. **speaker counts and distributions** — national census language returns, at stated dates;
3. **the surface** — the visual sentence in §3, assessed from a full-frame screenshot every round,
   together with the three readable facts.

**The independent witness: national census language returns.** States ask about language for their
own administrative reasons, on their own schedules, entirely independently of the linguistic
catalogues — so census tabulations can test both the counts and the distributions this atlas draws.
Where the two disagree, that disagreement is a finding worth a card.

## 9. Sensitivities

Carried in the substance, distributed through the layers — never in a disclaimer.

- **Naming is the ethics of this project.** Autonym first, every time. Exonyms that are slurs appear
  only in a historical-names row, marked as such.
- **Indigenous data sovereignty.** Language material is cultural property, and some communities have
  asked that their languages not be mapped, recorded or circulated. Policy: **only openly licensed,
  community-released material; a documented takedown path; and no language mapped against a
  community's stated wish.** A standing constraint on the pipeline, enforced at ingest.
- **The audio gap is ethical, not technical.** Clean recordings exist for ~6–8% of languages because
  the archives holding the rest forbid republication **as a condition of community consent**. The
  atlas ships what is clean, states the coverage plainly, names the archives, and **links out rather
  than mirrors**. A "hear this language" button that works one time in fifteen is a truthful
  representation of who controls these recordings.
- **Language death is not weather.** Languages are overwhelmingly displaced — by schooling in another
  language, resettlement, law and violence. Those are dated events with named actors, so the decline
  curves have causes attached.
- **Contested territories** are drawn as contested. A language-area map is a political claim in
  Kurdistan, Catalonia, Tibet, Ukraine and the Balkans.
- **The count itself is political.** See §6.
- **Reproduce the source's own disclaimer** where we draw indigenous territories from a project that
  states its maps are not official sources and do not define legal boundaries.

## 10. Non-goals

- Not a translation tool, and not a language-learning app.
- No proto-language reconstruction of our own; published trees, with their posteriors.
- No deep macrofamilies drawn as established.
- No mapping of any language whose community has declined.
- No claim to have counted the world's languages correctly — a claim to have shown honestly how the
  counting works.
- v1: no continuous time axis, no forecast pixels, no phonology panel.
- Not a gazetteer of every dialect; the splitting authority is stated and its level is the unit.

## 11. Budget and delivery

| | |
|---|---|
| delivery | static site, GitHub Pages from `main:/docs`, `.nojekyll`, relative paths, data-version stamp |
| total bytes over the wire | target **< 30 MB** for a usable global surface; the polygon set is ~3.9 MB gzipped and the language field a few MB of raster |
| time to first usable frame | **< 1.5 s** — fetch what the opening frame needs, fill in behind it |
| offline / `file://` required? | **no** — this project needs streamed field textures, so it trades `file://` portability for the visual bar |
| pipeline? | **yes.** `build/` turns polygons + population + terrain into the shipped fields; `web/` is the working copy; `docs/` is published |

**The two real budget problems are fonts and audio.** Rendering ~170 scripts means large font
coverage: subset per language and load on card open, never up front. Audio is one short clip per
language, fetched on demand, never bundled.

## 12. Decisions of record

Verbatim from the kickoff interview, 2026-07-31. These are the user's calls; changing them needs a
dated amendment.

**D1 — v1 builds the surface, not the time axis.** *"Surface first, two snapshots."* v1 renders
present-day and before-contact — exactly what the polygon data supports — and gets the diversity
spine, the lit-terrain surface and the card system right. v2 adds dated-phylogeny animation for the
~12% that support it; v3 pushes to the horizon.

**D2 — the parallel-prose tier ships on the "commons" claim.** *"Ship the prose on the 'commons'
claim."* The 446-language parallel corpus has **no licence file**: the Unicode Consortium
discontinued the project in January 2024, the surviving maintainer's only rights statement is that
the text is "obviously part of our commons", and the UN's own terms are all-rights-reserved and
non-commercial. **The user accepted this civil licensing risk deliberately, having been shown it.**
Basis: the declaration and its translations are among the most widely republished texts in existence
and the practical exposure is low. **Mitigations that are part of the decision:** every prose block
carries its provenance, the tier sits behind a single feature flag so it can be withdrawn in one
commit, and About documents a takedown path. Revisit if the maintainer grants an explicit licence —
worth an email either way.

**D3 — ShareAlike is permitted, for data and images.** *"allow sharealike for data and images."*
This supersedes the previous house no-SA policy. **NonCommercial and NoDerivatives remain
excluded.** Consequences, accepted:

- **our own emitted data inherits ShareAlike**, which constrains any future relicensing or
  commercial use of the whole project — the real cost, recorded here;
- unlocked for this project: the phoneme-inventory database (CC-BY-SA) and the Wiktionary
  derivatives, so a phonology panel is in scope for a later version;
- still blocked here: the three NonCommercial regional polygon sets and the UNESCO atlas (NC + ND).
  The OSM indigenous-lands layer is ODbL — share-alike is now permitted, but ODbL's obligations
  attach to the whole produced database, so treat it as a separate decision rather than assuming D3
  covers it;
- **every SA source is recorded in `Research/SOURCE-SURVEY.md` with its attribution string**, because
  SA obligations are only dischargeable if you know what you took.

**D4 — audio ships from v1 with coverage stated honestly.** *"Include from v1, coverage stated
honestly."* The clean ~400–600 languages ship, the coverage number is displayed rather than buried,
and the archives holding the remainder are named and linked.
