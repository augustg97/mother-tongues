# Staged changes — everything ready to apply to the model

The research folder does not change the app. This file is the handover: every
item that would touch the app, **with the artifact that makes it a drop-in**,
ordered by measured value rather than register number.

```
### N. <the change> · <register IDs it closes>
**Evidence:** <module or paper, with the measured number>
**Artifact:** <the file that already exists>
**Change:** <the specific edit, naming the function>
**Gate:** <the pre-existing measurement that must not move backwards>
**Cost:** <rebuild time, if any>
```

*Round 1, 2026-07-31.*

## Tier 1 — measured, high value, ready now

### 1. Encode elevation as 16-bit linear over −11000…+9000 m · closes B3, unblocks B1
**Evidence:** `Research/modeling/encoding.py`. Terracing in the New Guinea highlands — adjacent
land cells collapsing to one encoded level — is **30.9%** under the house reference project's
inherited signed-sqrt ±8000 8-bit encoding, **33.9%** under the best 8-bit land-linear variant,
and **4.0%** at 16-bit. The raw DEM's own floor is **4.0%**: at 16-bit the encoding contributes
*nothing*, because its 0.3 m quantum is already 3× finer than the source's 1 m integers. The
inherited encoding's quantum at 2000 m is **62.7 m**, creating steps of **1.95°** against a true
median slope of **1.34°** — it would invent more relief than the terrain has, in the exact region
SCOPE §3's visual sentence names.
**Artifact:** `encoding.py` — `ENCODINGS[E]`, `quantise()`, `terrace_fraction()`, all selftested.
**Change:** the field packer writes a single 16-bit channel,
`u = (clamp(z, −11000, 9000) + 11000) / 20000`. One channel, not a split domain — which also
avoids two systems owning one output band (TRAPS §C1).
**Gate:** terracing on land in the four SCOPE §3 regions must equal the raw-DEM floor
(4.0% / 1.9% / 39.0% / 0.5%) to within 0.1 pp. If the encoding adds terracing, it regressed.
**Cost:** 16.8 MB raw at 4096×2048; 116.6 MB at ~2 km. Paid **once** — terrain does not change
between the two snapshots (SCOPE §12 D1), so the reference project's 320-vs-23 MB finding across
251 *changing* keyframes does not transfer.

### 2. Import `frames.py` as the ingest frame · closes A1, A2
**Evidence:** Mollweide↔WGS84 round-trip residual **2.8 × 10⁻⁸ m** over a 180×52 global lattice.
Selftest passes, including refusal of out-of-domain points rather than extrapolation (TRAPS §D6).
**Artifact:** `Research/modeling/frames.py`, stdlib only — `build/` can import it as-is.
**Change:** all ingest goes through `Registry`, `NameSet.display()`, `SpeakerCount`, and
`wgs84_to_mollweide` / `mollweide_to_wgs84`. No source is joined to another without it.
**Gate:** `python3 frames.py` exits 0. The antimeridian assertion must hold:
`_wrap180(+180) = −180`, so x is **negative** at +180 — code assuming a positive right edge puts
a global raster's last column on the wrong side of the map.
**Cost:** none.

### 3. Gate the polygon ingest on licence text, not the API · closes A3
**Evidence:** `Research/modeling/licences.py`. **26 of 29** dataset repositories are shippable;
**3 are NonCommercial** and excluded — `bowern2021australia`, `haynie2019modern`,
`wurm1981pacific`. The collection's own platform paper claims blanket CC-BY-4.0, which is false
for those three, and GitHub's licence API returns `NOASSERTION` for all three because it cannot
distinguish CC-BY-NC from "Other".
**Artifact:** `licences.py` — `shippable()` returns the allowlist; the selftest asserts the three
excluded repositories **by name** and asserts the dataset count, so an upstream addition fails
loudly instead of shipping.
**Change:** `build/` iterates `licences.shippable()`. Never a hand-kept list.
**Gate:** `python3 licences.py` exits 0 and prints `shippable : 26`, `EXCLUDED : 3`.
**Cost:** none.

### 4. Filter Glottolog by `category`, not by `Level` · closes A6
**Evidence:** `languages.csv` has 8,618 language-level languoids; only **7,674** are
`Spoken_L1_Language`. Filtering on `Level` alone silently includes **227 sign languages** and
**380 bookkeeping placeholders** — a **12% inflation**, and it would put sign languages on a
terrain-diversity surface where they do not belong. The category lives in `values.csv`.
**Artifact:** `diversity.py:load_spoken_l1()`.
**Gate:** the ingest's language count must be **7,672** (spoken L1 *with coordinates*), and the
selftest asserts `< 8,304` so a regression to `Level`-only filtering fails.
**Cost:** none.

## Tier 2 — text and cards

*Nothing staged this round. Cards were deliberately deferred out of round 1 (SCOPE §12 D1); the
substrate comes first, and a card system built on an unamended claim would need rewriting.*

## Tier 3 — adopt the validators

### 5. Wire the four selftests into the build gate
**Evidence:** `frames.py`, `licences.py`, `encoding.py`, `diversity.py` all pass standalone.
**Change:** `Research/modeling/audit_all.py` runs all four; `build/build_site.py` refuses to
publish if any fails.
**Gate:** the build must fail on a deliberately broken frame conversion. Test that once, on
purpose — a gate never exercised is not known to work (TRAPS §D3).
**Cost:** seconds per build.

---

## NOT staged — needs the user's assent first

### The claim itself, and the visual sentence · new item C5
**Round 1's headline finding is that SCOPE §1 overstates terrain.** Measured: ruggedness↔richness
**+0.141** raw, **+0.108** with |latitude| partialled out, against **−0.582** for |latitude|
itself — latitude beats terrain roughly **4×**, and in **Papunesia (+0.024)** and **Africa
(+0.006)** the terrain effect is indistinguishable from zero with a sign that flips across cell
sizes. Robust at 1°, 2°, 4° and 6°.

SCOPE §1 currently says terrain "is most of the explanation" and §3 promises the shimmer "visibly
follows the terrain". **Neither is supported**, and Papunesia is the region §3 names as the
exemplar.

Proposed replacements are in `WP-01` §4. They are **not applied**, because SCOPE is the contract
and its claim is the user's to set. **This is the round's one blocking question.**
