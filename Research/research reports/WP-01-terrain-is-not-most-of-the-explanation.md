# WP-01 — Terrain is not most of the explanation, and the claim has to change

**Round 1 · 2026-07-31 · Register: C1, C2, and an amendment to SCOPE §1 and §3**

**Modules:** `Research/modeling/diversity.py`, `Research/modeling/encoding.py`,
`Research/modeling/frames.py` — all selftests pass.
**Data:** Glottolog 5.3 (CC-BY-4.0) · ETOPO1 ice-surface 1 arc-minute (public domain).

---

## Executive summary

The project's headline claim — *"the terrain is not the backdrop to that pattern; it is most of
the explanation"* — **is not supported by the first measurement, and the measurement is robust.**

Across 7,672 spoken-L1 languages and 6,143 land cells:

| relationship | Spearman |
|---|---|
| ruggedness ↔ richness density | **+0.141** |
| ruggedness ↔ richness density, \|latitude\| partialled out | **+0.108** |
| **\|latitude\| ↔ richness density** | **−0.582** |

Latitude — a crude stand-in for growing-season length — is **four times stronger than terrain**.
And in the two macroareas the claim leans on hardest, terrain explains essentially nothing:
**Papunesia +0.024, Africa +0.006**, both sign-unstable across cell sizes.

This is not a cell-size artefact. Swept at 1°, 2°, 4° and 6°, terrain stays in the band
**+0.08 to +0.14** while latitude *strengthens* from −0.43 to −0.79.

**The defect has three causes, and only one of them was being worked on.** The plate assumed the
problem was *drawing* the correlation well (an encoding and shader problem). In fact: (1) the
correlation is weak; (2) the predictor the literature says dominates — growing season — is not in
the model at all; and (3) the visual promise in SCOPE §3 names Papunesia specifically, which is
the worst case in the data. Fixing the encoding, which round 1 also did, addresses none of that.

**Recommendation: amend the claim before building the substrate.** The honest version is stronger,
not weaker — see §4.

---

## 1. What the thing is, and what it cannot know

Linguistic richness per unit area is an observed quantity with a real literature behind it, and
that literature's finding is consistent: **growing-season length and rainfall are the primary
environmental correlates of language richness; terrain is secondary.** The plate inverted that
ordering. This round measured the inversion.

Three things this measurement cannot know, stated so the numbers are not over-read:

- **Growing season is absent.** The model has no climate field yet (register C3/C4). \|Latitude\|
  is standing in for it, badly: it conflates tropicality with day length, seasonality and
  rainfall. The −0.582 should be read as *"a crude climate proxy beats terrain by 4×"*, not as a
  measurement of climate's true effect.
- **Ruggedness is elevation standard deviation within a cell.** That is the literature's simple
  measure, but at 2° it conflates "contains mountains" with "is rough at the scale a community
  lives at". A slope- or relief-per-kilometre measure may behave differently; that is C3.
- **Richness density is a ratio, not a count model.** Only 1,672 of 6,143 land cells hold any
  language, so the data are zero-inflated and a Poisson or negative-binomial count model with
  land area as an offset is the correct estimator. A rank correlation on density is a first look,
  not the final statistic. **This is the single largest methodological caveat.**

---

## 2. The record, in the form the model needs

Glottolog 5.3's counts reproduce exactly, which validates the ingest:

| quantity | measured | expected |
|---|---|---|
| languoids, all levels | 27,177 | 27,177 |
| language-level | 8,618 | 8,618 |
| **spoken L1** | **7,674** | 7,674 |
| spoken L1 with coordinates | **7,672** | — |
| dialects | 13,706 | 13,706 |
| family-level | 4,853 | 4,853 |
| sign languages | 227 | 227 |
| bookkeeping placeholders | 380 | 380 |

**The category filter is load-bearing.** `languages.csv` alone cannot separate a spoken language
from a sign language, a pidgin, an artificial language or a bookkeeping placeholder — that lives
in `values.csv` under the `category` parameter. Counting the 8,618 "language-level" languoids as
languages would silently fold in 227 sign languages and 380 placeholders, a **12% inflation**, and
would put sign languages on a terrain-diversity plot where they do not belong.

---

## 3. What we measured

### 3.1 The correlation, and its robustness

| cell | land cells | occupied | terrain (raw) | terrain (partial) | \|lat\| | Papunesia | Africa |
|---|---|---|---|---|---|---|---|
| 1° | 23,313 | 3,095 | +0.142 | +0.089 | −0.426 | **−0.058** | +0.044 |
| 2° | 6,143 | 1,672 | +0.141 | +0.108 | −0.582 | **+0.024** | +0.006 |
| 4° | 1,615 | 733 | +0.081 | +0.083 | −0.674 | +0.091 | −0.079 |
| 6° | 803 | 432 | +0.097 | +0.123 | −0.791 | — | −0.049 |

Per macroarea at 2°: North America +0.238 · Eurasia +0.173 · South America +0.145 ·
Australia +0.113 · **Papunesia +0.024** · **Africa +0.006**.

The terrain effect is weakly positive, stable in magnitude, and **absent where it was promised**.

### 3.2 The encoding, measured before it was chosen (register B3)

Separately, and this one came out cleanly in the project's favour.

The house reference project encodes elevation as signed-square-root over ±8000 m at 8 bits, which
concentrates precision at **sea level** because a migrating coastline was its product. Inheriting
it here would inherit a tuning for someone else's contour. Measured against the regions SCOPE §3
names:

| encoding | quantum @2000 m | step slope | vs true slope | terracing, New Guinea |
|---|---|---|---|---|
| inherited signed-sqrt ±8000, 8-bit | 62.7 m | 1.95° | **1.4×** | 30.9% |
| linear −500…+3000, 8-bit | 13.7 m | 0.43° | 0.3× | 33.9% |
| **linear −11000…+9000, 16-bit** | **0.3 m** | **0.01°** | **0.0×** | **4.0%** |
| *(source floor: raw int16 DEM, 1 m)* | 1 m | — | — | **4.0%** |

Two results:

1. **The inherited encoding invents relief.** Its quantum at highland elevations creates steps of
   1.95°, against a true median slope of **1.34°** in the New Guinea highlands. The step is
   *steeper than the terrain* — TRAPS §B1 exactly, in the region the claim names.
2. **16-bit reaches the source floor and stops.** Its terracing is 4.0% against the raw DEM's own
   4.0%: the encoding contributes **nothing**, because at 0.3 m it is already 3× finer than the
   source's 1 m integers. Precision beyond 16-bit is pointless; below it is lossy.

**Cost:** 16.8 MB raw at 4096×2048, 116.6 MB at ~2 km — paid **once**, because terrain does not
change between this project's two snapshots (SCOPE §12 D1). The reference project's 320 MB-vs-23 MB
finding was measured across **251 changing keyframes** and does not transfer.

### 3.3 The frame, as tested code (registers A1, A2)

`frames.py` passes. Mollweide↔WGS84 round-trip residual over a 180×52 global lattice:
**2.8 × 10⁻⁸ m**. Written by hand because there is no pyproj here, which turned out to be an
advantage: the residual is *measured and recorded* rather than assumed, and out-of-domain points
**raise** instead of extrapolating a plausible lie.

The antimeridian is pinned by assertion: `_wrap180(+180) = −180`, so x is **negative** at +180.
Code assuming a positive right edge would place a global raster's last column on the wrong side of
the map.

### 3.4 The licence gate (register A3)

29 dataset repositories in the polygon collection: **26 shippable, 3 excluded** as NonCommercial —
`bowern2021australia`, `haynie2019modern`, `wurm1981pacific`. The collection's own platform paper
says the datasets are CC-BY-4.0; **that is false for three of them.** GitHub's licence API cannot
help: it returns `NOASSERTION` for every CC variant it does not recognise, lumping NonCommercial in
with "Other". The gate therefore classifies from **licence text**, and its selftest asserts those
three by name so an upstream addition is caught rather than shipped.

---

## 4. Ranked remediations

**1. Amend the claim (SCOPE §1) and the visual sentence (SCOPE §3). P1, needs the user's assent.**

The claim cannot say terrain is "most of the explanation". The honest version is *better*, because
it is both true and more interesting:

> Linguistic diversity is not spread evenly, and the first thing that explains it is **climate** —
> the length of the growing season, and how many people a landscape can feed year-round. Terrain
> matters too, but less, and unevenly: it is visible in Eurasia and North America and effectively
> absent in Africa and the Pacific. The atlas draws both, and draws **where neither explains what
> is there** — because that residual is where history has to be told instead.

And the visual sentence must stop promising that the shimmer follows the terrain, because in
Papunesia it does not. Proposed replacement:

> At continental zoom the New Guinea highlands and the Caucasus **shimmer** into many small
> language territories while the North China Plain is one vast smooth field — and the viewer can
> see, from the same frame, that the shimmer tracks the **green** far more closely than the relief.

That is still a legible, falsifiable, three-facts-off-the-frame promise. It is simply the promise
the data supports.

**2. Get a climate field. P1.** Growing-season length or an equivalent. Without it the spine is
measuring the wrong variable, and the model cannot make the claim it should be making. This is now
the highest-value item in the register.

**3. Re-estimate with a count model. P1.** Poisson or negative binomial, land area as an offset,
zero-inflation handled. The rank correlation is a first look; the coefficient the model ships must
come from an estimator appropriate to counts.

**4. Adopt 16-bit linear −11000…+9000 for elevation. P1, MEASURED, ready to apply.** One channel,
no split domain — which also avoids the two-systems-texturing-one-surface trap (TRAPS §C1).

**5. Try relief-per-kilometre instead of elevation SD. P2.** The current measure may be answering
"are there mountains in this cell" rather than "is the ground rough where people live".

---

## 5. Actions → the register

| action | register | status |
|---|---|---|
| Amend SCOPE §1 claim and §3 visual sentence | **C5 (new), P1** | proposed, awaiting assent |
| Acquire a growing-season / climate field | **C3, promoted to P1** | open |
| Re-estimate with a zero-inflated count model | **C6 (new), P1** | open |
| Adopt 16-bit linear −11000…+9000 | **B3** | **MEASURED → staged** |
| Relief-per-km as an alternative ruggedness measure | **C7 (new), P2** | open |
| `frames.py` + residual recorded | **A1, A2** | **DELIVERED** |
| Licence gate, 26/29, three excluded by name | **A3** | **DELIVERED** |
| Glottolog category filter is mandatory (12% inflation without it) | **A6 (new), P2** | recorded |
