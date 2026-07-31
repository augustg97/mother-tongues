#!/usr/bin/env python3
"""coverage.py — measure what SHIPPED, not what the pipeline believed it wrote.

Register items B4 and D8. The app tells the viewer "real polygons exist for 62.5% of living
languages". That number is a property of the *catalogue*, and a viewer looking at the map does
not care about the catalogue: they care whether the ground under their eye is data or absence.
Those are different numbers, and only one of them is measurable from the artefact.

So this module opens the PNGs that are actually in `web/fields/` and counts. It is deliberately
NOT part of the pipeline: TRAPS §D5 — an audit that reads what the pipeline reads is a mirror,
not a witness. It reads the shipped raster with an independently written decoder.

Emits `web/data/coverage.json`, which the About panel renders. `build_site.py` runs it every
build, so the number cannot drift from the raster it describes.

Needs numpy + PIL (it decodes PNGs). Run: python3 coverage.py
"""
from __future__ import annotations

import json
import os

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.join(HERE, "..", "..", "web")
FIELDS = os.path.join(WEB, "fields")


LEVEL = 2          # 8192x4096 — fine enough for an area fraction, cheap enough to stitch


def _rgba(name: str) -> np.ndarray:
    """Stitch one field from its level-2 tiles, dropping the skirt.

    Reading the tiles rather than the masters keeps this an audit of what SHIPPED: if the
    tiler drops a tile, mis-slices a skirt or writes a channel to the wrong band, the number
    moves. An audit that reads the pipeline's own inputs is a mirror, not a witness.
    """
    meta = json.load(open(os.path.join(FIELDS, "fields.json")))
    T, S = meta["tile"], meta["skirt"]
    cols, rows = 2 << LEVEL, 1 << LEVEL
    out = np.zeros((rows * T, cols * T, 4), np.uint8)
    have = set(meta["tiles"][str(LEVEL)])
    for ty in range(rows):
        for tx in range(cols):
            if f"{tx}_{ty}" not in have:
                continue
            p = os.path.join(FIELDS, f"z{LEVEL}", f"{name}_{tx}_{ty}.png")
            a = np.asarray(Image.open(p).convert("RGBA"))
            out[ty*T:(ty+1)*T, tx*T:(tx+1)*T] = a[S:S+T, S:S+T]
    return out


def measure() -> dict:
    terrain = _rgba("terrain")
    env = _rgba("env")
    h, w = terrain.shape[:2]

    # Independent decode of the 16-bit elevation: R*256+G over 0..65535 -> -11000..+9000.
    z = ((terrain[:, :, 0].astype(np.int32) * 256 + terrain[:, :, 1]) / 65535.0) * 20000.0 - 11000.0
    biome = env[:, :, 0]
    pop = env[:, :, 1].astype(np.float64)          # 0..255, a log-ish density code, not people

    # Land is defined by the biome field, not by z > 0: the Dead Sea shore and the Caspian are
    # below sea level and are unambiguously land, and the Netherlands would vanish.
    land = biome > 0
    n_land = int(land.sum())

    # Latitude weight: an equirectangular cell's area goes as cos(lat), so an unweighted pixel
    # count over-counts the Arctic by ~40x against the equator. Unweighted first, then weighted.
    lat = 90.0 - (np.arange(h) + 0.5) * (180.0 / h)
    wgt = np.cos(np.radians(lat))[:, None] * np.ones((1, w))

    out = {"grid": [w, h], "land_px": n_land,
           "land_area_frac_of_grid": round(float((wgt * land).sum() / wgt.sum()), 5)}

    for tag, fn in (("today", "lang_c"), ("before_contact", "lang_t")):
        a = _rgba(fn)
        cov = a[:, :, 3] > 0                       # alpha is the coverage channel
        cov_land = cov & land
        lp = float((wgt * land).sum())
        d = {
            "covered_px": int(cov_land.sum()),
            # of the world's land AREA, how much has a mapped language area under it
            "frac_of_land_area": round(float((wgt * cov_land).sum() / lp), 4),
            # of the world's PEOPLE, how many stand on mapped ground. This is the number a
            # viewer actually wants, and it is much higher than the land fraction, because
            # polygon coverage is best exactly where people are.
            "frac_of_population": round(float(pop[cov_land].sum() / max(pop[land].sum(), 1)), 4),
            "max_languages_within_20km": int(a[:, :, 1].max()),
        }
        out[tag] = d

    # Where the absence is worst, in named terms a viewer can check. Boxes, and labelled as
    # boxes: these are not the regions, they are windows onto them.
    boxes = {"Siberia": (60, 180, 50, 75), "Sahara": (-15, 35, 18, 30),
             "Amazon basin": (-72, -50, -12, 2), "New Guinea": (131, 151, -11, 0),
             "Australia": (113, 154, -39, -11), "Great Plains": (-105, -95, 32, 49),
             "India": (69, 89, 8, 32), "Congo basin": (12, 30, -8, 5)}
    reg = {}
    a = _rgba("lang_c")
    cov = (a[:, :, 3] > 0) & land
    for name, (lo0, lo1, la0, la1) in boxes.items():
        r0, r1 = int((90 - la1) / 180 * h), int((90 - la0) / 180 * h)
        c0, c1 = int((lo0 + 180) / 360 * w), int((lo1 + 180) / 360 * w)
        sl = (slice(r0, r1), slice(c0, c1))
        lsum = float((wgt[sl] * land[sl]).sum())
        reg[name] = round(float((wgt[sl] * cov[sl]).sum() / lsum), 3) if lsum > 0 else None
    out["by_window_today"] = reg
    out["note"] = ("Measured from the shipped rasters, not from the pipeline. Land is defined "
                   "by the biome field. Fractions are cos(latitude)-weighted, so they are "
                   "areas rather than pixel counts. Windows are bounding boxes, not regions.")
    return out


def _selftest(m: dict) -> None:
    # Land is 29.2% of the Earth's surface. Allow 26–32% for the coastline the grid resolves.
    la = m["land_area_frac_of_grid"]
    assert 0.26 <= la <= 0.32, f"land is {la:.1%} of the grid — the biome field is wrong"

    t, b = m["today"], m["before_contact"]
    for tag, d in (("today", t), ("before", b)):
        assert 0.05 < d["frac_of_land_area"] < 0.95, f"{tag}: coverage {d['frac_of_land_area']}"
        assert d["frac_of_population"] > d["frac_of_land_area"], \
            (f"{tag}: population coverage ({d['frac_of_population']:.1%}) is not above land "
             f"coverage ({d['frac_of_land_area']:.1%}). Polygon coverage is densest where "
             f"people are; if this inverts, the population channel is misregistered.")
        assert 1 <= d["max_languages_within_20km"] <= 255

    # New Guinea is the densest language region on Earth and is well surveyed by Glottography's
    # schapper2020papuan. If its coverage is not among the best, the polygon ingest lost a file.
    ng = m["by_window_today"]["New Guinea"]
    assert ng is not None and ng > 0.5, f"New Guinea coverage is {ng} — the Papuan set is missing"
    print("coverage.py selftest OK")


if __name__ == "__main__":
    m = measure()
    _selftest(m)
    out = os.path.join(WEB, "data", "coverage.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(m, open(out, "w"), indent=1)
    t = m["today"]
    print(f"\nland          {m['land_area_frac_of_grid']:.1%} of the grid, {m['land_px']:,} px")
    print(f"today         {t['frac_of_land_area']:.1%} of land area · "
          f"{t['frac_of_population']:.1%} of the world's people stand on mapped ground")
    b = m["before_contact"]
    print(f"before        {b['frac_of_land_area']:.1%} of land area · "
          f"{b['frac_of_population']:.1%} of people")
    print("\nby window (today):")
    for k, v in sorted(m["by_window_today"].items(), key=lambda kv: -(kv[1] or 0)):
        print(f"  {k:16s} {'—' if v is None else f'{v:.0%}'}")
    print(f"\nwrote {os.path.relpath(out, os.path.join(HERE, '..', '..'))}")
