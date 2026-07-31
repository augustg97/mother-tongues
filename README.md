# Mother Tongues

Every human language we know of, on the ground it is spoken on

**Live:** not yet deployed — first ship creates https://augustg97.github.io/mother-tongues/
**Contact:** augustgweon@gmail.com

---

## 1. What this is trying to be

A **model**, not a slideshow. It ships terrain, population and language fields, and composes the linguistic surface **per pixel in the shader** — the app ships state and rules and assembles
the world at render time. Nothing is a pre-rendered picture of a moment.

That choice is the whole architecture, and everything below follows from it:

- diversity **shimmers** along a mountain range because the field is computed from ruggedness and population at that pixel — not because someone drew hatching there;
- a language's territory is bright where its speakers are and dark where nobody lives, because the luminance channel *is* the population raster — so an "area" is never a flat wash of colour;
- Every layer is derived from the same underlying data, so the layers cannot disagree with each
  other.

### Goals

1. **Veracity first.** Where the record says something, follow it. Where it does not, model the
   mechanism and say plainly that it is modelled.
2. **Coherence.** One world, internally consistent.
3. **Detail that survives inspection.** The interesting scale is a valley in the New Guinea highlands, well below any shippable global grid. Sub-grid texture is grown from the mechanism on material coordinates, so zoom reveals structure rather than running out of it.
4. **Honesty about uncertainty.** Real polygons exist for 62.5% of living languages; nine pre-Common-Era languages have an area at all; audio exists for 6–8%. Coverage is a **drawn layer**, not a footnote. The UI says so, and the model degrades
   gracefully rather than inventing confident detail.

---

## 2. Working rules

Standing constraints on how work is done here, not suggestions. Each came from a specific
failure. *(Copied from `Modeling Studio/references/WORKING-RULES.md` — keep in sync; add rules
as new failures produce them.)*

**2.1 Always visually verify.** An update is not done when the data contains the value. It is
done when it has been rendered and looked at.

**2.2 Fix the system, not the instance.** Make the change at the level that fixes the whole class
across the whole timeline.

**2.3 Prefer structural, model-based changes over cosmetic ones.** Model the object or process;
let the appearance fall out of it.

**2.4 Measure before tuning.** If you cannot say what the number is now, you cannot say your
change improved it.

**2.5 Track every request; never silently drop one.** If something cannot be done, say so and say
why.

**2.6 Always deploy, and verify the live artefact.** Local-only changes read as "not done".

**2.7 Never ship on an average.** Score every item individually and classify every regression.

**2.8 When an audit disagrees with the app, check the audit first.**

**2.9 Say what is contested.** Confidence is a field on the data, not a footnote.

**2.10 "Unknown" is a legitimate return** — and where a fallback is unavoidable, the UI labels it.

**11. Autonym first, always** — in its own script, exonym second, historical exonyms marked.
Enforced in code. This is the ethics of the project, not a formatting preference.

**12. No language mapped against its community's stated wish.** Only openly licensed,
community-released material. The audio gap exists because archives withhold recordings as a
condition of consent — ship what is clean, state coverage, link out rather than mirror.

**13. Never one number for how many languages exist.** State the authority; show the alternatives.

**14. Every speaker count is a triple** — (value, year, source).

**15. The before-contact snapshot carries no year.** It is a per-region state.

**16. ShareAlike permitted, NonCommercial and NoDerivatives not** (SCOPE §12 D3) — and our own
emitted data therefore inherits SA.

---

## 3. Repository layout

```
```
build/            offline: polygons + population + terrain -> web/ fields
web/              the app and its data — the working copy (what launch.json serves)
  data/           app data as JS/JSON
  fields/         encoded field rasters
docs/             the built static site; Pages serves main:/docs
data/             large source datasets — GITIGNORED (anchored /data/, see §7)
Research/         the standing research programme; never imported by build/
SCOPE.md          the contract
```
```

---

## 4. The layers

| layer | kind | source or mechanism |
|---|---|---|
| Terrain, coasts, rivers, lit relief | **authored** | open global topo-bathymetry, composed per pixel |
| Ruggedness · growing season · biome | **modelled** | derived from elevation and climate — the diversity model's predictors |
| Gridded population | **authored** | open CC-BY raster, 5-year steps, **1975 floor** |
| **Language field** | **modelled** | family hue × speaker luminance × diversity granularity, per pixel |
| Language territories | **authored + modelled** | CC-BY polygons for ~5,300 languages; coarse admin fallback for the rest, marked coarse |
| **Diversity** | **modelled** | richness from ruggedness, growing season, coast, settlement time-depth — **the spine** |
| Genealogy · dated phylogenies | **authored** | the catalogue's classification; published posteriors drawn *as posteriors* (v2) — **second view** |
| Attestation | **authored** | first/last attested date per language, with confidence |
| Scripts | **authored** | writing systems with adoption dates, rendered in the actual script |
| Sample texts | **authored** | wordlists (~6,100 languages) · parallel prose (~450) · CC0 lexemes (~1,550) |
| Voices | **authored** | one openly licensed recording where one exists — **~6–8% of languages** |
| Vitality | **authored** | the catalogue's endangerment status, six levels |
| **Documentation status** | **authored** | how well each language is described — the map is partly a map of survey effort |
| Language-shift events | **authored** | dated policy and violence, with named actors |
| Chapters — the tour | **authored** | the hotspots and the great spreads |

---

## 5. Subsystems

Nothing built yet beyond the scaffold shell. Planned, in the order round 1 builds them:

- **`frames.py`** — the identity and naming layer. Glottocode keys, autonym-first resolution,
  the (value, year, source) triple. Everything else depends on it.
- **The substrate** — elevation encoded for the *land* relief band, relief lit per pixel from the
  field's gradient, water as a surface.
- **The language field** — family hue x population luminance x diversity granularity, composed per
  pixel. The project exists the moment this reads as a world rather than a chart.
- **The diversity model** — richness predicted from ruggedness, growing season, coast and settlement
  time-depth, scored per cell. The spine.
- **The card generator** — ~8,600 cards, three-tier fallback with the tier named in the heading.

---

## 6. Build and deploy

```bash
# run locally (port 8146)
python3 -m http.server 8146 --directory "/Users/augustgweon/Mother Tongues/web"

# research selftests — must pass before any two sources are joined
cd Research/modeling && python3 frames.py && python3 audit_all.py

# deploy — the only route, once build_site.py exists
python3 build/build_site.py && git add -A && git commit && git push
```

The build **runs the validators first and refuses to publish if one moved backwards**:

```bash
python audit_all.py           # all of them
python audit_all.py --quick   # skip the slow ones
```

| check | baseline | what it catches |
|---|---|---|
| *(no validators yet — round 1 adds the frames selftest and the diversity residual audit)* | — | — |

The baselines are not all zero and should not be — a genuine open disagreement belongs in the
baseline with a note. The rule is that **none of them may move backwards**; when one legitimately
improves, tighten the baseline in the same commit, so the ratchet turns one way only.
`SKIP_AUDIT=1` overrides, deliberately awkwardly.

**Verify the live data-version stamp after every push.**

---

## 7. Traps

Failures that have each cost real time here. *(The general catalogue is in
`Modeling Studio/references/TRAPS.md`; add new ones to both.)*

- **The scaffold layout bug** (fixed here and upstream): the shell belongs in `web/`, and
  `.gitignore` must anchor **`/data/`** — an unanchored `data/` also matches `web/data/` and
  silently ships a site that renders nothing.
- **The scaffold shell is dots on flat ground** — a placeholder. Replacing it is the job.
- **Glottolog's three language counts are all correct** (27,177 languoids / 8,618 language-level /
  7,674 spoken L1) and get conflated constantly. Label which is in use.
- **3 of Glottography's 34 repos are CC-BY-NC** though its platform paper says otherwise. Gate per
  repo licence, by machine.
- **GHS-POP is Mollweide.** Reproject once at ingest and record the residual.
- **PanLex is CC-BY-NC-SA, not CC0.**
- **One Phlorest tree's unit field yields 692,970 years.** Sanity-check every tree.

---

## 8. Sources

| role | source |
|---|---|
| see `Research/SOURCE-SURVEY.md` §1 for the full table, per layer, with licences | Glottolog · Glottography · ASJP · Grambank · WALS · Phlorest · GHS-POP · GEBCO/ETOPO · Lingua Libre · census tabulations |

**Canonical frame:** glottocode as identity, WGS84, autonym-first names, (value, year, source) counts, two snapshots of which the earlier is a state not a year — every source is converted into it; the conversions are
in `Research/modeling/frames.py`.

---

## 9. Known limits

The section that makes the rest credible. State plainly what is reconstructed, what is contested,
and what the model cannot know.

- Real areal polygons cover **62.5%** of living languages; the rest render as a coarse
  administrative field, visibly marked as coarse.
- **Nine** pre-Common-Era languages have a mapped area; **38.6%** of extinct languages do. The deep
  past is a handful of well-documented ancient languages plus a confidence gradient.
- Gridded population is compliant only from **1975**; earlier luminance is reconstructed.
- Openly licensed audio exists for **6–8%** of languages, and the reason is community consent
  rather than oversight.
- **No global continuous linguistic surface has ever been built.** The interpolation method is ours
  and so is the method risk.
- The parallel-prose text tier ships under a recorded decision (SCOPE §12 D2) on a corpus with no
  licence file, behind a feature flag.

---

## 10. Reference material

The standing architectural reference is **Tectonic Earth**
(`~/Tectonic Plate Model`) — read its FRAG shader, its lazy loader and its verification harness
before building the field engine here. It is the *only* exemplar in the house set: Territorial US
and Aztec Conquest are deprecated as references (they put features on flat ground), and the AI Atlas
is a cautionary case — a beautifully rendered surface of an abstract space still reads as a chart.

Protocol: `~/Modeling Studio` — `references/WORKING-RULES.md`, `ARCHITECTURE-PATTERNS.md` §0 for the
visual standard, and Plate 01 of `CANDIDATE-PROJECTS.md`, which is this project's pre-filled scope.

`HANDOFF.md` carries the live state, the measured facts, and the work queue for a fresh session.
