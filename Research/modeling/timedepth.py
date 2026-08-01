#!/usr/bin/env python3
"""timedepth.py — register C8: does a region's language richness track how long people have
been there?

THE HYPOTHESIS. Linguistic diversity takes time to accumulate: a region settled for forty
thousand years has had longer to differentiate than one settled for four. It is one of the
standard explanations offered alongside climate and terrain, and this project has never
tested it.

THE DATA. **p3k14c** (Bird et al., *Scientific Data* 9:27, 2022, CC-BY): 173,946 archaeological
radiocarbon determinations with coordinates. Per grid cell we take the OLDEST date as a floor
on occupation and the COUNT of dates as a measure of how hard anyone has looked.

⚠ THE CONFOUND IS THE WHOLE PROBLEM, and it is not subtle. Radiocarbon coverage measures
archaeological effort at least as much as it measures human presence: western Europe and the
United States are saturated, New Guinea and central Africa are nearly blank. A raw correlation
between "oldest date" and language richness would largely be a correlation between two
different consequences of where archaeologists work. So the count of dates per cell is carried
as an explicit effort control and partialled out, and the result is reported both ways. Where
they disagree, the partial is the one to believe.

stdlib + numpy. Run: python3 timedepth.py
"""
from __future__ import annotations

import csv
import math
import os

import numpy as np

import diversity as D

HERE = os.path.dirname(os.path.abspath(__file__))
C14 = os.path.join(HERE, "..", "..", "data", "c14", "p3k14c.csv")

MIN_DATES = 3          # a cell with one date has an "oldest date" that is one excavation
MAX_AGE = 55000        # beyond the method's range; anything older is a lab artefact


def load_cells() -> dict[tuple[int, int], dict]:
    if not os.path.exists(C14):
        raise SystemExit("no radiocarbon file — see build/ for the p3k14c download")
    per: dict[tuple[int, int], dict] = {}
    with open(C14, newline="", encoding="utf-8", errors="replace") as f:
        for r in csv.DictReader(f):
            try:
                age = float(r["Age"])
                lat = float(r["Lat"])
                lon = float(r["Long"])
            except (TypeError, ValueError):
                continue
            if not (0 < age < MAX_AGE) or not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                continue
            k = D.cell_of(lat, lon)
            e = per.setdefault(k, {"oldest": 0.0, "n": 0})
            e["n"] += 1
            if age > e["oldest"]:
                e["oldest"] = age
    return per


def measure(verbose: bool = True) -> dict:
    c14 = load_cells()
    langs = D.load_spoken_l1()
    z = D.load_dem()
    terr = D.terrain_per_cell(z)

    rich: dict[tuple[int, int], int] = {}
    for L in langs:
        rich[D.cell_of(L["lat"], L["lon"])] = rich.get(D.cell_of(L["lat"], L["lon"]), 0) + 1

    rows = []
    for k, t in terr.items():
        e = c14.get(k)
        if not e or e["n"] < MIN_DATES or t["land_km2"] < 2000:
            continue
        rows.append((rich.get(k, 0) / t["land_km2"] * 1e4, e["oldest"], e["n"],
                     abs(t["lat_mid"])))
    n = len(rows)
    if n < 100:
        raise SystemExit(f"only {n} cells have both language and radiocarbon coverage")

    dens = np.array([r[0] for r in rows])
    old = np.array([r[1] for r in rows])
    eff = np.log10(np.array([r[2] for r in rows], float))
    alat = np.array([r[3] for r in rows])

    out = {
        "cells": n,
        "cells_with_c14_of_all_land": round(n / max(len(terr), 1), 4),
        "raw_spearman_oldest_vs_richness": round(D.spearman(old, dens), 4),
        "partial_on_effort": round(D.partial_spearman(old, dens, eff), 4),
        "partial_on_latitude": round(D.partial_spearman(old, dens, alat), 4),
        "effort_vs_richness": round(D.spearman(eff, dens), 4),
        "effort_vs_oldest": round(D.spearman(eff, old), 4),
        "median_oldest_bp": int(np.median(old)),
    }
    if verbose:
        print(f"C8  settlement time-depth vs language richness\n")
        print(f"    {n:,} cells with >= {MIN_DATES} dates "
              f"({out['cells_with_c14_of_all_land']*100:.0f}% of land cells) · "
              f"median oldest date {out['median_oldest_bp']:,} BP (uncalibrated)\n")
        print(f"    oldest date  vs richness            {out['raw_spearman_oldest_vs_richness']:+.3f}")
        print(f"      holding EFFORT constant           {out['partial_on_effort']:+.3f}")
        print(f"      holding LATITUDE constant         {out['partial_on_latitude']:+.3f}")
        print(f"    number of dates vs richness         {out['effort_vs_richness']:+.3f}")
        print(f"    number of dates vs oldest date      {out['effort_vs_oldest']:+.3f}")
        print("\n    Radiocarbon coverage is a map of archaeologists as much as of people:")
        print("    only the partials are interpretable, and even they are conditioned on")
        print("    the 'has been excavated at all' sample.")
    return out


def _selftest() -> None:
    m = measure(verbose=False)
    assert m["cells"] >= 100
    # Ages must be plausible: the median oldest date in an excavated cell should be
    # Holocene-to-late-Pleistocene, not last Tuesday and not 200,000 years.
    assert 1500 < m["median_oldest_bp"] < 30000, \
        f"median oldest date {m['median_oldest_bp']} BP is not a plausible archaeological range"
    # The effort confound must be REAL and visible, otherwise the control is theatre.
    assert m["effort_vs_oldest"] > 0.2, \
        "number of dates does not predict the oldest date — check the effort proxy"
    for k in ("raw_spearman_oldest_vs_richness", "partial_on_effort", "partial_on_latitude"):
        assert -1.0 <= m[k] <= 1.0
    print("timedepth.py selftest OK")


if __name__ == "__main__":
    _selftest()
    print()
    measure()
