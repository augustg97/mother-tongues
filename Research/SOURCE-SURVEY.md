# Source survey — Mother Tongues

*Surveyed 2026-07-31, before any app code was written. This is Phase 2 of `/model-kickoff`.*

Every figure below was fetched and, where a count is given, counted — not recalled. Items marked
**⚠ UNVERIFIED** could not be confirmed and mean "not found", never "does not exist".

**Licence policy in force: SCOPE §12 D3 — ShareAlike is permitted for data and images.
NonCommercial and NoDerivatives remain excluded.** That is a change from the previous house rule
and it is what unlocks PHOIBLE and the Wiktionary derivatives below.

---

## 1. What data exists, per layer

### Shippable

| layer | source | format | scale / resolution | licence | access |
|---|---|---|---|---|---|
| **language polygons** ⭐ | **Glottography** — Ranacher, Forkel, Efrat-Kowalsky, Urban et al., *Sci Data* 12:1466 (2025), `10.1038/s41597-025-05828-6`; platform paper *JOHD* `10.5334/johd.459` | CLDF + GeoJSON | **5,297 glottocodes = 62.5% of spoken-L1 languages**; 4,500 features, 1.27 M vertices; 53 MB raw → **3.9 MB gz at 3-dp (~110 m)** | **CC-BY-4.0 on 26 of 34 repos** | `github.com/Glottography` — **gate ingest per repo LICENSE** |
| language spine, vitality, genealogy | **Glottolog 5.3** (2026-03-02) | CLDF, CSV, Newick | 27,177 languoids · 8,618 language-level · 7,674 spoken L1 · 246 families + 183 isolates · AES on 8,672 · **attestation years on 217** | CC-BY-4.0 | Zenodo `10.5281/zenodo.18840967` |
| typology (for card prose) | **Grambank** v1.0.3 · **WALS** 2020.4 | CLDF | 195 features × 2,467 varieties · 192 features × 3,573 languages | CC-BY-4.0 | Zenodo / `wals.info` |
| **wordlists — the breadth tier** ⭐ | **ASJP** | CLDF | **11,540 wordlists across 6,135 ISO-coded languages** — the widest cleanly licensed language resource that exists | CC-BY-4.0 | `asjp.clld.org` |
| lexemes | **Wikidata Lexemes** | SPARQL / dumps | 1,538,535 lexemes across **1,558 languages** | **CC0** | `query.wikidata.org` |
| sentences | **Tatoeba** | TSV | 13.5 M sentences, 431 languages | CC-BY 2.0 FR (+ a CC0 subset) | `tatoeba.org/downloads` |
| **parallel prose** | **UDHR in XML** (ex-Unicode) | XML / TXT / HTML | 615 entries · 528 stage-4 · **446 distinct languages** · 49 scripts · all with coordinates | ⚠ **NO LICENCE — ships under SCOPE §12 D2** | `efele.net/udhr`, `github.com/eric-muller/udhr` (pushed 2026-07-28) |
| population | **GHS-POP R2023A** | GeoTIFF | 100 m / 1 km, **1975–2030 at 5-year steps** | CC-BY-4.0 | JRC GHSL |
| population (alt) | **WorldPop** | GeoTIFF | 100 m / 1 km, 2015–2030 | CC-BY-4.0 | `worldpop.org` |
| terrain / bathymetry | **GEBCO_2026** · **ETOPO 2022** | netCDF / GeoTIFF | 15 arcsec | **public domain** · **CC0** | `gebco.net` · NOAA `10.25921/fd45-gt74` |
| coarse admin fallback | **Natural Earth** admin-1 | Shapefile | 4,500+ units, 1:10 m | **public domain** | `naturalearthdata.com` |
| indigenous-to fallback | **Wikidata P2341** | SPARQL | 8,012 languages → 4,153 areas, 2,132 with geoshapes; mostly admin-1 — strongest in PNG (805), Indonesia (743), Nigeria (509) | **CC0** | `query.wikidata.org` |
| dated phylogenies (v2) | **Phlorest** | CLDF + Newick + posteriors | **30 families**, e.g. Sino-Tibetan 7,185 *and* 5,871 (both shipped), IE 6,008, Pama-Nyungan 5,671, Austronesian 4,633 | **all CC-BY 2.0 / 4.0** | `github.com/phlorest` |
| scripts | **Unicode UCD 17.0** · **CLDR** · **ISO 15924** | data files | 172 scripts with assigned characters · 7,324 language→script pairs · 226 codes | Unicode License v3 | `unicode.org` |
| script inception dates | **Wikidata** | SPARQL | **256 of 274 coded scripts carry an inception date (93%)** | CC0 | `query.wikidata.org` |
| concept / phoneme alignment | **Concepticon** · **CLTS** | CLDF | 4,165 concept sets · 5 transcription systems | CC-BY-4.0 | `concepticon.clld.org` · `clts.clld.org` |
| **phonology** — unlocked by D3 | **PHOIBLE 2.0** | CSV | 3,020 inventories, 2,186 languages, 3,183 segment types | **CC-BY-SA 3.0** | `phoible.org` |
| audio backbone | **Lingua Libre** (Wikimedia) | ogg/wav via Commons API | 337 language categories; **~742,406 CC0 + ~35,541 CC-BY** of 1.62 M files | per file — filter at ingest | Commons API |
| audio, parallel | **FLEURS** | flac | 102 languages | CC-BY-4.0 | HuggingFace |
| audio, long tail | **Wikimedia Commons** | mixed | 1,165,995 CC0 audio files | per file | Commons API |
| speaker counts | national census tabulations | CSV | US ACS ~350 languages (public domain); **Australia ABS CC-BY-4.0**; StatCan OGL ⚠; India Census ⚠ | varies, all open | per agency |

### Measure-against-only, or blocked

| source | why |
|---|---|
| **WLMS** (World Language Mapping System) | *"redistribution of the data is not allowed except… by explicit, prior, written permission"* — **blocked** |
| **Ethnologue** GIS + speaker data | *"Republication of any Content is expressly prohibited"*; datasets sold separately — **blocked** |
| **UNESCO WAL / Atlas** | NC **+ no-derivatives + no-redistribution**, currently **HTTP 503**, and the downloadable data has **no geometry at all** — blocked twice over |
| **GADM** | *"Redistribution or commercial use is not allowed"* — blocked |
| **Glottography**: `bowern2021australia`, `haynie2019modern`, `wurm1981pacific` | **CC-BY-NC** — excluded. The platform paper's blanket CC-BY claim is inaccurate; gate per repo |
| **HYDE 3.5** (deep-time gridded population) | **CC-BY-NC** — blocked. **This is why 1975 is the population floor** |
| **PanLex** | **CC-BY-NC-SA** — the NC blocks it even under D3. Widely and wrongly assumed CC0 |
| **ELCat / ELP** (endangerment) | signals conflict across CC-BY-SA, CC-BY-NC and personal-use-only; the NC reading disqualifies. **Use Glottolog AES, which launders the same upstream into CC-BY** |
| **IPUMS International** | *"You will not redistribute the data"* + *"Commercial use is strictly prohibited"*; and language variables cover barely five countries — blocked, use census tabulations |
| **Mozilla Common Voice** | content CC0 but the package says *"forbidden to re-host or re-share this dataset"* — ⚠ **needs a legal call before use**; not assumed |
| **Wikitongues** | CC-BY-**NC** by default; usable slice ≈ **124 files** of an ~820-language collection. **Worth an email, not a workaround** |
| **PARADISEC · ELAR** | NC + SA **plus** *"not to distribute the data to third parties"* and a bar on uploading to *"web-based systems"* — they name our use case. **Link out, never mirror** |
| **OSM `boundary=aboriginal_lands`** | 6,236 objects under **ODbL**. SA is permitted under D3, but ODbL's obligations attach to the whole produced database — **a separate decision, not covered by D3** |
| **Native Land Digital** | 2,059 territory + 936 language polygons; Data Sovereignty Treaty forbids storing and redistributing. **Only route is written permission — worth an email** |
| **VoxLingua107** | CC-BY-4.0 but scraped from YouTube with *"copyright remains with the original owners"* — licence laundering, blocked |
| **GeoEPR** · **D-PLACE** · **Murdock** | points-only, NC, or **no licence statement at all** |

### The D3 attribution ledger

ShareAlike obligations are only dischargeable if you know what you took. Every SA source gets a row
here at ingest, with the exact attribution string the licence requires.

| source | licence | attribution string | where it appears in the app |
|---|---|---|---|
| PHOIBLE 2.0 | CC-BY-SA 3.0 | *to be filled at ingest* | phonology panel (v2+) |
| *(add a row per SA source before it is ingested — the build gate checks this table is not stale)* | | | |

---

## 2. Frames

| source | coordinates | dating | naming | unit / vintage |
|---|---|---|---|---|
| Glottography | WGS84, GeoJSON | two snapshots, **no date fields** | glottocode | "contemporary" vs "traditional" |
| Glottolog | WGS84 points | attestation years, 217 populated, to 2100 BCE | glottocode + name + aliases | 5.3, 2026-03-02 |
| ASJP | — | — | ISO 639-3 + own names | — |
| Wikidata | WGS84 | Julian/Gregorian flags on dates | QIDs | live |
| UDHR in XML | WGS84 points | — | ISO 639-3 + BCP-47 | 528 stage-4 |
| GHS-POP | **Mollweide** (also WGS84 tiers) | 5-year epochs | — | R2023A |
| GEBCO / ETOPO | WGS84 | — | — | 2026 / 2022 |
| ISO 639-3 | — | — | ISO codes, **no "ancient" type** | 20260715, 7,927 codes |
| census tabulations | national grids | census dates | national language names | per country |

**Canonical frame chosen:**

- **identity — the Glottolog glottocode.** ISO 639-3 is an *alias*, never a key: it has no "ancient"
  type (Latin, Sumerian and Akkadian are all coded *historical*, so bucketing by *extinct* returns
  almost nothing) and its coverage differs from Glottolog's by hundreds of entries.
- **names — autonym first, in its own script**, exonym second, historical exonyms flagged. Display
  order enforced in code.
- **coordinates — WGS84.** GHS-POP arrives in Mollweide and **must be reprojected once at ingest,
  with the residual recorded** — this is the one live coordinate-frame trap in the project.
- **time — the two snapshots are not years.** "Before contact" is a per-region state; the contact
  date goes on the card where known and is never printed on the timeline.
- **counts — always the triple (value, year, source).**

**Conversions:** written as tested code in `Research/modeling/frames.py`, with selftests, not applied
by eye. Nothing is combined across two sources until `frames.py` can convert between them.

---

## 3. Where the record stops

| boundary | measured | UI behaviour past it |
|---|---|---|
| the linguistic horizon, ~8–10 ka | relatedness not demonstrable; macrofamilies not accepted | draws **nothing** — terrain keeps rendering, languages are absent |
| polygon coverage | **62.5%** of spoken-L1 languages have a real area | the rest render as a **coarse administrative field, labelled coarse** |
| deep-time areas | of 217 dated languages only **82** have a polygon; of pre-CE ones, **nine** | the deep atlas is those nine plus a confidence gradient |
| extinct languages | **524 of 1,356 (38.6%)** have an area | the remainder are cards without territory, and say so |
| animatable languages | **1,003** have both a dated tree and a polygon ≈ **12%** | v2's animation covers that 12% and states it |
| population | compliant floor **1975** | earlier luminance is a reconstruction, labelled |
| audio | **~400–600 languages, 6–8%** | coverage displayed, not buried; archives named and linked |

---

## 4. Where the sources disagree

| disagreement | shape | how the model will handle it |
|---|---|---|
| how many languages exist | **amount** — Glottolog 8,618 language-level vs Ethnologue ~7,100 vs ISO 7,927. Hammarström's *Language* review documents **191 spurious entries and 236 missing languages** in one Ethnologue edition | one stated authority, alternative counts shown, never one number as the fact |
| Transeurasian / "Altaic" | **existence** | not drawn; named in About with both sides — Robbeets et al. 2021 vs the reply that it *"does not conform to the minimal standards required by traditional scholarship"* |
| Amerind | **existence** | not drawn; consensus is rejection of mass comparison |
| Bayesian dating's warrant | **existence of the method's warrant** | posteriors drawn as posteriors; the published critique cited on the card |
| isolates as a category | **existence** | answered by the documentation-status layer rather than asserted |
| Sino-Tibetan root age | **amount** — 7,185 vs 5,871 years, both in Phlorest | **ship both**, as two posteriors |
| language areas in contested regions | **position** | soft fields, drawn as contested, never hard borders |

---

## 5. The independent witness

**National census language returns.** States ask about language for their own administrative
reasons, on their own schedules, using their own categories — entirely independently of the
linguistic catalogues. So census tabulations can score both the speaker counts and the spatial
distributions this atlas draws.

Confirmed usable: **US ACS detailed-language tables** (~350 languages, public domain) and
**Australian ABS** (CC-BY-4.0, verified verbatim). ⚠ StatCan (OGL) and India's Census — which
reduces 19,569 raw returns to 1,369 mother tongues to 121 languages, itself a superb illustration of
the splitting problem — are unverified on exact licence strings.

It is a genuine witness precisely because it disagrees: census categories are political artefacts,
so where the census and the catalogue diverge, **the divergence is the finding** and gets a card.

---

## 6. Layers with no usable source — authored deliberately

- **Language-shift events** (school bans, resettlement, residential schooling, language police). No
  machine-readable global dataset found. **Authored**, per event, with citations — and this is the
  layer that stops decline curves from reading as weather.
- **Settlement time-depth**, a diversity-model predictor. Must be derived from archaeological and
  aDNA literature per region. **Authored + modelled**, and its uncertainty is wide.
- **The "tour" chapters.** Authored narrative, ~15–20 chapters.
- **Contact dates per region**, for the before-contact snapshot's cards. Authored from the
  historical literature; wide and regionally uneven.

---

## 7. Prior work, and what it leaves open

Every prior global visualisation is a **dot map or a tree**. Glottolog's map is points with no areal
extent and no time. Ethnologue has polygons and forbids republication. The famous viral language
tree is Indo-European and Uralic only, and its author says so explicitly. National Geographic's
enduring-voices project is now served from an `/archive/` path.

**Continuous linguistic surfaces exist only regionally** — the dialectometry literature interpolates
them by kriging (Goebl's Visual DialectoMetry, Gabmap), and Grieve's spatial-autocorrelation work
recovers five primary US dialect regions from 206 cities. **Nobody has built one globally.**
Searches for a global language-density surface return the population literature instead.

That is the strongest argument for building this — and it means **we own the method risk**, which is
why the diversity model's per-cell residual audit is a P1 item and not a nicety.
