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
cd Research/modeling && python {{MODULE}}.py
```

| module | what it is | current state |
|---|---|---|
| | | selftest passes |

## The audits

Read-only; they change nothing.

| script | catches | current result |
|---|---|---|
| | | |

## The dossiers

| file | covers |
|---|---|
| | |

## The white papers

| paper | thesis |
|---|---|
| | |

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

**v0.1 — kickoff only, 2026-07-31.**

*Round 0* — the scoping interview and the source survey. No models or audits written yet; the app
is the scaffold shell. `SOURCE-SURVEY.md` is complete and unusually load-bearing, because the
survey ran *before* the plate was chosen and changed it twice.

See [`MODEL-GAPS.md`](MODEL-GAPS.md) for the **26 open items, 12 at P1**.

---

## Round 1 — the datum-and-substrate round, in priority order

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
