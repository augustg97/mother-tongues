# Research — linguistic-geography knowledge base for Mother Tongues

**Started 2026-07-31.** A standing research programme and expert system covering language distribution, genealogy, endangerment, writing systems, and the environmental determinants of linguistic diversity.

**This folder does not change the model.** Nothing here is imported by `build/`. Its output is
*evidence and models* that inform continuous updates to the app — so that when a number, a
boundary, a label or a card changes, the change has a citation and a mechanism behind it rather
than a guess.

---

## How it is organised

```
Research/
├── SOURCE-SURVEY.md              what data exists, in what frame, under what licence
├── MODEL-GAPS.md                 the register that ties research to app defects
├── research/                     evidence: dossiers per domain, with sources and caution flags
│   ├── 01-language-distribution/
│   └── 09-source-documents/      fetched primary material, kept verbatim
├── research reports/             illustrated white papers, each ending in actions
│   └── STAGED-CHANGES.md         the handover surface
├── modeling/                     runnable models + read-only audits
└── figures/
    ├── authored/                 generated FROM the models, so they cannot drift
    └── collected/                third-party + MANIFEST.json (licence + review verdict)
```

---

## The models

All runnable, all self-testing. Each prints a worked demonstration.

```bash
cd Research/modeling && python3 audit_all.py     # all four
cd Research/modeling && python3 diversity.py     # or one at a time
```

| module | what it is | current state |
|---|---|---|
| `frames.py` | the canonical frame: glottocode identity, autonym-first names, (value, year, source) counts, Mollweide↔WGS84 | **selftest passes.** Round-trip residual 2.8e-08 m |
| `licences.py` | the ingest licence gate, classified from licence TEXT | **selftest passes.** 26 of 29 shippable, 3 NC excluded by name |
| `encoding.py` | measures the vertical encoding before it is chosen | **selftest passes.** 16-bit reaches the DEM's own floor |
| `diversity.py` | the spine: does richness follow terrain? | **selftest passes.** First measurement done, and it partly falsifies the claim |

## The audits

Read-only; they change nothing.

| script | catches | current result |
|---|---|---|
| `frames.py:_selftest` | ISO used as a key; a bare speaker count; a year on the earlier snapshot; a slur promoted to a card title; out-of-domain projection | passes |
| `licences.py:_selftest` | an NC repo leaking into the allowlist; the dataset count moving upstream | passes |
| `encoding.py:_selftest` | a non-monotone encoding; a DEM read with the wrong orientation | passes |
| `diversity.py:_selftest` | the category filter silently doing nothing; duplicate glottocodes; a confound surviving a partial correlation | passes |

## The dossiers

| file | covers |
|---|---|
| — | no dossier this round. Round 1 was measurement-led: the four modules and `WP-01` carry the findings, and a literature dossier on environment-versus-diversity is item C4 |

## The white papers

| paper | thesis |
|---|---|
| `WP-01-terrain-is-not-most-of-the-explanation.md` | The headline claim overstates terrain. Latitude beats it ~4x, and in Papunesia and Africa terrain explains nothing. The claim must change — and the honest version is stronger |

---

## Working method

1. **Verify, don't reconstruct from memory.** Every claim traces to a named source; where a
   fetched source is internally inconsistent, the dossier says so rather than propagating it.
2. **Say what is contested.** A card that states an open question flatly misrepresents how well
   it is known.
3. **Prefer a model to a table.** Every finding that could be a hand-written row is written as a
   function with a selftest, so a new input produces a defensible answer without new authoring.
4. **Figures are generated, not drawn.** They read from the same modules, so a corrected value
   propagates automatically.
5. **Every white paper ends in actions**, and every action lands in `MODEL-GAPS.md`.

---

## Status

**v1.0 — round 2 complete and DEPLOYED, 2026-07-31.**

*Round 1* produced four self-testing modules, one white paper, two authored figures and four staged
changes. *Round 2* amended the claim, built the substrate and the language field, and shipped:
**https://augustg97.github.io/mother-tongues/** — live stamp verified.

**The round's headline is a partial falsification of the project's own claim.** Terrain correlates
with linguistic richness at only **+0.141** (**+0.108** controlling for latitude), while latitude
itself reaches **−0.582** — roughly 4x stronger. In Papunesia (**+0.024**) and Africa (**+0.006**)
the terrain effect is indistinguishable from zero. Robust at 1°/2°/4°/6°. SCOPE §1's claim that
terrain is "most of the explanation" and §3's promise that the shimmer "visibly follows the terrain"
both have to change — see `research reports/WP-01`.

The round also settled the encoding it was asked to settle: **16-bit linear −11000…+9000**, which
reaches the source DEM's own quantisation floor and therefore contributes no terracing of its own.
The inherited signed-sqrt encoding would have created steps **1.4x steeper than the real terrain**
in the highlands.

See [`MODEL-GAPS.md`](MODEL-GAPS.md) for the **31 items, 13 at P1**.

---

## Round 1 — COMPLETE. What it did, in the order it was planned

| planned | outcome |
|---|---|
| A1 `frames.py` | **DELIVERED**, selftest passes |
| A2 Mollweide→WGS84 | **DELIVERED**, residual 2.8e-08 m recorded |
| A3 licence gate | **DELIVERED**, 26/29 shippable, 3 excluded by name |
| B3 encoding measurement | **MEASURED**, 16-bit chosen, staged |
| B1/B2 substrate + language field | **staged, not built** — app work, handed to `/model-build` |
| C1 diversity model | **first measurement delivered**, and it changed the claim |
| E1 census witness | **NOT DONE** — see below |

**Not done, and why:** E1, the census witness. Round 1 ran out of room after the C1 result forced
a white paper and a claim amendment. It stays P1 and moves to round 2. Also not done: a literature
dossier (C4) and the growing-season field (C3), the latter now the register's top substantive item.

---

## Round 2 — in priority order

**0. Settle C5 first.** The claim amendment is blocking and it is the user's call. Everything
downstream of the claim is provisional until it is settled, including the visual bar that `/model-build`
will be measured against.

**1. C3 — get a climate field.** Growing-season length or an equivalent. The spine is currently
measuring the secondary variable, and this is the highest-value substantive item in the register.

**2. C6 — re-estimate with a count model.** Poisson or negative binomial, land area as an offset,
zero-inflation handled: 1,672 of 6,143 land cells hold a language. The rank correlation is a first
look, not the statistic that ships.

**3. E1 — the census witness**, carried over. Built early because it settles later disputes.

**4. C7 — relief-per-kilometre** as an alternative ruggedness measure, and C4, the literature check.

**Then `/model-build`** takes `STAGED-CHANGES.md` Tier 1 into the app: the 16-bit encoding, the
frames module, the licence gate and the category filter — and builds B1, the lit substrate, whose
gate is a screenshot against SCOPE §3's sentence (as amended).

---

## The original round-1 plan, for the record

The ordering is not negotiable: **frames before joins, substrate before layers, spine before
polish.** Two prior projects reached "feature complete" on flat ground and were assessed as charts.

**1. A1 — `frames.py`, with selftests.** Glottocode as the key; ISO 639-3 as alias only; the
autonym-first name resolver with its exonym and historical-exonym tables; the (value, year, source)
triple for speaker counts. *Nothing may be joined to anything until this passes its selftest.*

**2. A2 + A3 — the ingest gates.** Reproject GHS-POP from Mollweide to WGS84 once and record the
residual. Gate the Glottography ingest per repository licence so the three CC-BY-NC sets are
excluded by machine rather than by memory.

**3. B3 → B1 — measure, then build the substrate.** Histogram how many quantisation levels fall in
the *land* relief band before choosing an encoding — do not inherit one tuned for bathymetry. Then
build the lit-terrain substrate and **screenshot it against the SCOPE §3 sentence.** This is the
round's gate: if the frame does not read as a rendered world, nothing else in round 1 counts.

**4. B2 — the language field.** Family hue × population luminance × diversity granularity, composed
per pixel. The moment this reads as a world rather than a chart is the moment the project exists.

**5. C1 + C2 — the diversity model and its per-cell residual audit.** Read the regional
dialectometry literature first and record why the chosen interpolation was chosen; **we own the
method risk, because no global continuous linguistic surface has been built before.**

**6. E1 — the census witness.** Built early, because it is the instrument every later dispute is
settled with.

**Deferred out of round 1, deliberately:** cards beyond a minimal probe (D1–D5), audio (D3), the
phylogeny second view, and everything in v2/v3 per SCOPE §12 D1.

**The first white paper writes itself:** *"Diversity follows the terrain — how far, and where it
doesn't."* The residual map from C1 is the figure, and the cells where environment fails to predict
richness are where history has to be told instead.
