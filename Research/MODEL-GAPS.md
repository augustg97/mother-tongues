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

| item | what shipped | measured |
|---|---|---|
| — | nothing yet; the app is the scaffold shell | — |

---

## A. Frames and identity — nothing is combined until these exist

| # | P | item | touches | from |
|---|---|---|---|---|
| **A1** | **P1** | **`frames.py` with selftests**: glottocode as the key, ISO 639-3 as alias only, autonym-first name resolution with an exonym/historical-exonym alias table, and the (value, year, source) triple for every speaker count. **No two sources may be joined before this exists.** | build ingest, every card | SCOPE §6 |
| **A2** | **P1** | **Reproject GHS-POP from Mollweide to WGS84 once at ingest and record the residual.** The one live coordinate-frame trap in the project — population and polygons arrive in different grids | `build/`, population field | SURVEY §2 |
| A3 | **P1** | **Per-repo licence gate on the Glottography ingest.** 3 of 34 component repos are CC-BY-NC and must be excluded by machine, not by memory; the platform paper's blanket CC-BY claim is wrong | `build/`, polygon ingest | SURVEY §1 |
| A4 | P2 | The **before-contact snapshot carries no year**. Enforce in code that no year label can be rendered for it, and attach per-region contact dates to cards instead | time engine, cards | SCOPE §6 |
| A5 | P3 | **D3 attribution ledger** kept current: a row per ShareAlike source with its exact attribution string, checked by the build gate so it cannot go stale | `SOURCE-SURVEY.md` §1, About panel | SCOPE §12 D3 |

## B. The substrate — the thing the work is judged on

| # | P | item | touches | from |
|---|---|---|---|---|
| **B1** | **P1** | **The lit-terrain substrate**: elevation encoded for the *land* relief band, relief shaded per pixel from the field's gradient, water as a surface. **Before any language layer.** Screenshot and assess against the SCOPE §3 sentence | `web/`, shader | WORKING-RULES §13, SCOPE §3 |
| **B2** | **P1** | **The language field**: family hue × population luminance × diversity granularity, composed per pixel. The moment this reads as a rendered world rather than a chart is the moment the project exists | shader, `build/` | SCOPE §3 |
| B3 | **P1** | **Vertical encoding decision, measured before it is chosen.** Histogram how many quantisation levels fall in the land relief band that actually carries the shimmer. Do not inherit an encoding tuned for a different range | `build/fieldpack`-equivalent | TRAPS §B1–B2 |
| B4 | P2 | Coarse-fallback territories render **visibly differently** from real polygons — a viewer must be able to tell 62.5% from the remainder without reading About | shader, legend | SURVEY §3 |
| B5 | P2 | Procedural sub-grid detail keyed to a shipped material coordinate, so zoom reveals structure rather than running out of it | shader | ARCHITECTURE-PATTERNS §7 |

## C. The spine — the diversity model

| # | P | item | touches | from |
|---|---|---|---|---|
| **C1** | **P1** | **The diversity model and its per-cell residual audit**, scored against observed richness with **no averaging**. This is the spine; without it the atlas is an inventory | `Research/modeling/`, diversity field | SCOPE §4 |
| C2 | **P1** | **The method risk is ours.** No global continuous linguistic surface has ever been built — only regional dialectometry by kriging. Read that literature before choosing an interpolation, and record why the chosen method was chosen | `Research/`, C1 | SURVEY §7 |
| C3 | P2 | **Settlement time-depth**, a C1 predictor with no ready source. Derive per region from the archaeological and aDNA literature; its uncertainty is wide and must be carried | `Research/`, diversity field | SURVEY §6 |
| C4 | P2 | Reproduce published environment-versus-diversity relationships as the first external check on C1 | audits | SCOPE §8 |

## D. Cards, texts and voices

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

**What the survey did NOT find** — recorded so the next round does not re-litigate it:

- **No open polygon source beyond Glottography.** WLMS, Ethnologue, GADM and UNESCO were each
  checked and each forbids redistribution; the OSM layer is ODbL, which is a separate decision.
- **No global language-density surface, anywhere.** The search returns the population literature.
  This is a negative result with a positive reading: the idea has no precedent.
- **No dated language-death dataset.** Only ~57 language items carry a dissolution date.
- **No machine-readable language-shift event catalogue.** Hence E3 is authored.
- **Glottolog does carry attestation years** — an earlier assumption that it did not was wrong.

---

**Count: 26 items — 12 at P1.** The ones that would move the model furthest, in order:

1. **A1** — `frames.py`. Nothing may be joined before it, and every later bug traces here.
2. **B1 + B2** — the lit substrate and the language field. Until the frame reads as a rendered
   world, no other item matters; this is what the work is judged on.
3. **C1** — the diversity model with its per-cell residual audit. The spine.
4. **A2** — the Mollweide→WGS84 reprojection with a recorded residual.
5. **E1** — the census witness, built early because it settles every later dispute.
