#!/usr/bin/env python3
"""diversity.py — does linguistic richness follow the terrain? First measurement.

Register: C1 (the spine), C2 (the method risk).

Why this is the spine
---------------------
SCOPE §1 claims the terrain is "most of the explanation" for where linguistic diversity
sits, and SCOPE §3's visual sentence promises the shimmer "visibly follows the terrain".
That is a falsifiable claim about a correlation, and this module is where it gets tested
before a single pixel is drawn. If the correlation is weak, the *claim* has to change —
not the colour ramp.

What this first cut does and does not do
---------------------------------------
DOES: bin Glottolog's spoken-L1 languages into equal-ish cells, compute terrain
ruggedness per cell from ETOPO1, and measure the rank correlation between richness
density and ruggedness — globally and per macroarea, with a crude climate control.

DOES NOT: include growing season, rainfall, or coast/river access. The published
literature finds growing-season length is the *stronger* predictor and terrain secondary,
so a terrain-only correlation is an upper bound on what terrain alone explains and must
not be reported as the whole model. Those predictors are register item C3/C4.

The honest confound is latitude: the tropics have both more languages and, in places,
more relief. So the raw correlation is reported alongside a **partial** correlation with
|latitude| ranks regressed out. Both numbers go in the white paper; neither alone is the
answer.

stdlib + numpy. Run:  python3 diversity.py
"""
from __future__ import annotations

import csv
import math
import os
from collections import defaultdict
from typing import Optional

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
GLOTTOLOG = os.path.join(HERE, "..", "..", "data", "glottolog")
DEM_PATH = os.path.join(HERE, "..", "..", "data", "dem", "etopo1_ice_g_i2.bin")

CELL = 2.0                     # degrees; a compromise between sample size and locality
R_EARTH_KM = 6371.0088
MIN_LAND_KM2 = 2_000.0         # cells with less land than this are noise
CONFIDENCE = ("good", "moderate", "contested", "none")


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

def load_spoken_l1() -> list[dict]:
    """Spoken L1 languages with coordinates.

    The category filter matters: `languages.csv` alone cannot distinguish a spoken
    language from a sign language, a pidgin, an artificial language or a Bookkeeping
    placeholder — that lives in `values.csv` under the `category` parameter. Counting
    8,618 "language-level" languoids as languages would silently include 227 sign
    languages and 380 bookkeeping entries.
    """
    cat: dict[str, str] = {}
    with open(os.path.join(GLOTTOLOG, "values.csv"), newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["Parameter_ID"] == "category":
                cat[r["Language_ID"]] = r["Value"]
    out = []
    with open(os.path.join(GLOTTOLOG, "languages.csv"), newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["Level"] != "language":
                continue
            if cat.get(r["ID"]) != "Spoken_L1_Language":
                continue
            if not r["Latitude"] or not r["Longitude"]:
                continue
            out.append(dict(code=r["Glottocode"], lat=float(r["Latitude"]),
                            lon=float(r["Longitude"]), macroarea=r["Macroarea"],
                            family=r["Family_ID"] or r["Glottocode"]))
    return out


def load_dem() -> np.ndarray:
    a = np.fromfile(DEM_PATH, dtype="<i2")
    return a.reshape(10801, 21601)


# ---------------------------------------------------------------------------
# Gridding
# ---------------------------------------------------------------------------

def cell_of(lat: float, lon: float) -> tuple[int, int]:
    return (int(math.floor(lat / CELL)), int(math.floor(lon / CELL)))


def cell_area_km2(irow: int) -> float:
    """Area of a CELLxCELL cell at that latitude band, on a sphere."""
    lat0 = math.radians(irow * CELL)
    lat1 = math.radians((irow + 1) * CELL)
    return (R_EARTH_KM ** 2) * math.radians(CELL) * abs(math.sin(lat1) - math.sin(lat0))


def terrain_per_cell(z: np.ndarray) -> dict[tuple[int, int], dict]:
    """Land area, mean elevation and ruggedness per cell.

    Ruggedness is the standard deviation of elevation among the cell's land pixels — the
    standard simple measure, and the one the environment-diversity literature uses in the
    same role. Cells with no land are absent rather than zero: "unknown" is a legitimate
    return.
    """
    step = int(round(CELL * 60))              # ETOPO1 is 1 arc-minute
    out: dict[tuple[int, int], dict] = {}
    nrows, ncols = z.shape
    for r0 in range(0, nrows - 1, step):
        # row 0 is +90; a block starting at r0 spans latitudes [90 - (r0+step)/60, 90 - r0/60]
        lat_top = 90.0 - r0 / 60.0
        lat_bot = 90.0 - min(r0 + step, nrows - 1) / 60.0
        irow = int(math.floor((lat_bot + 1e-9) / CELL))
        band = z[r0:r0 + step, :]
        if band.size == 0:
            continue
        lat_mid = (lat_top + lat_bot) / 2.0
        coslat = max(math.cos(math.radians(lat_mid)), 1e-6)
        px_km2 = (R_EARTH_KM * math.radians(1 / 60.0)) ** 2 * coslat
        for c0 in range(0, ncols - 1, step):
            blk = band[:, c0:c0 + step]
            land = blk > 0
            n = int(land.sum())
            if n == 0:
                continue
            icol = int(math.floor(((c0 / 60.0) - 180.0 + 1e-9) / CELL))
            vals = blk[land].astype(np.float64)
            out[(irow, icol)] = dict(
                land_km2=n * px_km2,
                elev_mean=float(vals.mean()),
                rugged=float(vals.std()),
                lat_mid=lat_mid,
            )
    return out


# ---------------------------------------------------------------------------
# Statistics — implemented here because scipy is not available
# ---------------------------------------------------------------------------

def _ranks(x: np.ndarray) -> np.ndarray:
    order = np.argsort(x, kind="mergesort")
    r = np.empty(len(x), dtype=np.float64)
    r[order] = np.arange(1, len(x) + 1, dtype=np.float64)
    # average ties
    sx = x[order]
    i = 0
    while i < len(sx):
        j = i
        while j + 1 < len(sx) and sx[j + 1] == sx[i]:
            j += 1
        if j > i:
            r[order[i:j + 1]] = (i + j + 2) / 2.0
        i = j + 1
    return r


def pearson(a: np.ndarray, b: np.ndarray) -> float:
    a = a - a.mean(); b = b - b.mean()
    d = math.sqrt(float((a * a).sum()) * float((b * b).sum()))
    return float((a * b).sum() / d) if d > 0 else float("nan")


def spearman(a: np.ndarray, b: np.ndarray) -> float:
    return pearson(_ranks(a), _ranks(b))


def partial_spearman(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    """Spearman(a,b) with c's rank influence removed from both — a crude control."""
    ra, rb, rc = _ranks(a), _ranks(b), _ranks(c)

    def resid(y, x):
        x0 = x - x.mean()
        den = float((x0 * x0).sum())
        beta = float(((y - y.mean()) * x0).sum()) / den if den > 0 else 0.0
        return y - y.mean() - beta * x0

    return pearson(resid(ra, rc), resid(rb, rc))


# ---------------------------------------------------------------------------
# The measurement
# ---------------------------------------------------------------------------

def measure(verbose: bool = True) -> dict:
    langs = load_spoken_l1()
    z = load_dem()
    terr = terrain_per_cell(z)

    counts: dict[tuple[int, int], int] = defaultdict(int)
    area_of: dict[tuple[int, int], str] = {}
    for l in langs:
        k = cell_of(l["lat"], l["lon"])
        counts[k] += 1
        area_of.setdefault(k, l["macroarea"])

    rows = []
    for k, t in terr.items():
        if t["land_km2"] < MIN_LAND_KM2:
            continue
        n = counts.get(k, 0)
        rows.append(dict(cell=k, n=n, density=n / t["land_km2"] * 1e6,   # per Mkm2
                         rugged=t["rugged"], elev=t["elev_mean"],
                         abslat=abs(t["lat_mid"]), land=t["land_km2"],
                         macroarea=area_of.get(k, "")))
    if verbose:
        print(f"languages (spoken L1, with coordinates): {len(langs):,}")
        print(f"cells with >= {MIN_LAND_KM2:,.0f} km2 of land: {len(rows):,}")
        print(f"of which hold at least one language: "
              f"{sum(1 for r in rows if r['n'] > 0):,}")

    dens = np.array([r["density"] for r in rows])
    rug = np.array([r["rugged"] for r in rows])
    alat = np.array([r["abslat"] for r in rows])

    res = {
        "n_cells": len(rows),
        "spearman_raw": spearman(rug, dens),
        "spearman_partial_abslat": partial_spearman(rug, dens, alat),
        "spearman_abslat_density": spearman(alat, dens),
        "rows": rows,
    }
    return res


def _selftest() -> None:
    # --- statistics --------------------------------------------------------
    x = np.array([1.0, 2, 3, 4, 5])
    assert abs(spearman(x, x) - 1.0) < 1e-12
    assert abs(spearman(x, -x) + 1.0) < 1e-12
    assert abs(pearson(x, 2 * x + 3) - 1.0) < 1e-12
    # monotone but non-linear: Spearman 1, Pearson < 1
    y = x ** 3
    assert abs(spearman(x, y) - 1.0) < 1e-12 and pearson(x, y) < 1.0
    # ties handled
    t = np.array([1.0, 1, 2, 2, 3])
    assert abs(spearman(t, t) - 1.0) < 1e-12
    # a partial correlation must kill a pure confound: a and b both driven by c only
    rng = np.random.default_rng(7)
    c = rng.normal(size=400)
    a = c + 0.001 * rng.normal(size=400)
    b = c + 0.001 * rng.normal(size=400)
    assert spearman(a, b) > 0.99
    assert abs(partial_spearman(a, b, c)) < 0.5, partial_spearman(a, b, c)

    # --- geometry ---------------------------------------------------------
    # cell areas must sum to the sphere
    tot = sum(cell_area_km2(i) * (360 / CELL) for i in range(int(-90 / CELL), int(90 / CELL)))
    sphere = 4 * math.pi * R_EARTH_KM ** 2
    assert abs(tot / sphere - 1.0) < 1e-6, tot / sphere
    assert cell_area_km2(0) > cell_area_km2(int(80 / CELL)), "equatorial cells are larger"
    assert cell_of(-7.5, 141.2) == (-4, 70)

    # --- data, if present -------------------------------------------------
    if os.path.exists(os.path.join(GLOTTOLOG, "values.csv")):
        langs = load_spoken_l1()
        # Glottolog 5.3: 7,674 spoken L1; 8,304 of 8,618 language-level have coordinates.
        # So spoken-L1-with-coordinates must be under 7,674 and comfortably over 7,000.
        assert 7_000 < len(langs) <= 7_674, len(langs)
        # the category filter must actually exclude something
        assert len(langs) < 8_304, "category filter did nothing — sign languages leaked in"
        codes = {l["code"] for l in langs}
        assert len(codes) == len(langs), "duplicate glottocodes"
        assert all(-90 <= l["lat"] <= 90 and -180 <= l["lon"] <= 180 for l in langs)
        # a known high-diversity cell: the New Guinea highlands must be dense
        ng = sum(1 for l in langs if -7 <= l["lat"] <= -3 and 137 <= l["lon"] <= 147)
        assert ng > 100, f"only {ng} languages in the New Guinea highlands box — check coords"

    print("diversity.py selftest: OK")


if __name__ == "__main__":
    _selftest()
    if not (os.path.exists(DEM_PATH) and os.path.exists(os.path.join(GLOTTOLOG, "values.csv"))):
        raise SystemExit("data absent; selftest only")
    print()
    print("=" * 78)
    print("C1 — first measurement: does linguistic richness follow the terrain?")
    print("=" * 78)
    r = measure()
    print()
    print(f"Spearman(ruggedness, richness density)                : {r['spearman_raw']:+.3f}")
    print(f"  ... partial, |latitude| removed from both            : "
          f"{r['spearman_partial_abslat']:+.3f}")
    print(f"Spearman(|latitude|, richness density)  [the confound] : "
          f"{r['spearman_abslat_density']:+.3f}")
    print()
    print("per macroarea (cells with land, richness density vs ruggedness):")
    by = defaultdict(list)
    for row in r["rows"]:
        if row["macroarea"]:
            by[row["macroarea"]].append(row)
    for ma, rows in sorted(by.items(), key=lambda kv: -len(kv[1])):
        if len(rows) < 30 or ";" in ma:
            continue
        d = np.array([x["density"] for x in rows])
        g = np.array([x["rugged"] for x in rows])
        print(f"  {ma:16s} n={len(rows):4d}  Spearman {spearman(g, d):+.3f}")
    print()
    print("NOTE: terrain only. Growing season, rainfall and coast/river access are")
    print("register items C3/C4 and the literature finds growing season the stronger")
    print("predictor — so this is an UPPER bound on what terrain alone explains.")
