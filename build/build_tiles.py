#!/usr/bin/env python3
"""build_tiles.py — cut the master fields into a tile pyramid the browser can afford.

WHY TILES. A 16384x8192 16-bit elevation raster is one 215 MB PNG. Nobody waits for that, and
a phone cannot hold it. The pyramid ships a 2048x1024 world that paints in under a second, then
replaces what is on screen with detail as the viewer zooms. Level 3 is the full 2.44 km grid;
the viewer only ever downloads the handful of tiles they are looking at.

  level 0   2048 x 1024    2 x 1 tiles     19.5 km/px    always loaded, the fallback
  level 1   4096 x 2048    4 x 2 tiles      9.8 km/px    (the whole of the previous build)
  level 2   8192 x 4096    8 x 4 tiles      4.9 km/px
  level 3  16384 x 8192   16 x 8 tiles      2.44 km/px   master

THE SKIRT. Tiles are cut 1026 px square for a 1024 px core: one pixel of the neighbouring tile
on every side. Without it, LINEAR filtering at a tile edge samples the clamp colour instead of
the neighbour and every tile boundary draws a visible seam across the terrain — 24 vertical
lines down the Pacific. The skirt costs 0.4% in pixels and removes the class entirely.

REDUCTION IS PER FIELD, and getting this wrong is not subtle:
  * elevation, NDVI, snow  -> area mean. Continuous quantities; the mean is the value.
  * biome, family, MED     -> nearest. These are CATEGORICAL. Averaging biome 6 (taiga) and
                              biome 8 (temperate grassland) gives 7 (tropical grassland),
                              which is how you put savanna in Siberia.
  * diversity              -> MAX. It is a count of overlapping languages, and the entire
                              visual argument is that some cells hold forty. A mean at level 0
                              turns New Guinea into its regional average and erases the thing
                              the map exists to show.
  * coverage               -> MAX. Any covered pixel makes the parent covered; a mean would
                              fade real data into half-transparency.

Empty-ocean tiles are not written at levels 2 and 3: no land, no language, nothing but smooth
bathymetry the parent level already renders correctly. The manifest records exactly which
tiles exist, and the renderer walks up to the nearest ancestor it has.

Run:  python3 build_tiles.py
"""
from __future__ import annotations

import json
import os

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
MASTER = os.path.join(ROOT, "data", "master")
OUT = os.path.join(ROOT, "web", "fields")

TILE = 1024
SKIRT = 1
MAXLEVEL = 3
Z_LO, Z_HI = -11000.0, 9000.0


def log(*a):
    print(*a, flush=True)


def load(name):
    return np.load(os.path.join(MASTER, name + ".npy"), mmap_mode="r")


def reduce_mean(a: np.ndarray, f: int) -> np.ndarray:
    h, w = a.shape
    return a.reshape(h // f, f, w // f, f).mean(axis=(1, 3))


def reduce_max(a: np.ndarray, f: int) -> np.ndarray:
    h, w = a.shape
    return a.reshape(h // f, f, w // f, f).max(axis=(1, 3))


def reduce_near(a: np.ndarray, f: int) -> np.ndarray:
    return a[f // 2::f, f // 2::f]


def cut(a: np.ndarray, y0: int, x0: int, n: int) -> np.ndarray:
    """n x n window at (y0,x0) with the skirt, wrapping in x and clamping in y.

    Wrapping in x is not a nicety: the antimeridian is a real edge of the array and a
    non-wrapping read draws a seam down the Bering Strait and through Fiji.
    """
    h, w = a.shape
    ys = np.clip(np.arange(y0, y0 + n), 0, h - 1)
    xs = np.mod(np.arange(x0, x0 + n), w)
    return np.asarray(a[ys][:, xs])


def rgba(r, g, b, a) -> Image.Image:
    return Image.fromarray(np.dstack([r, g, b, a]).astype(np.uint8), "RGBA")


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    meta = json.load(open(os.path.join(MASTER, "meta.json")))
    MW, MH = meta["grid"]

    src = {n: load(n) for n in ("elev", "biome", "ndvi", "snow", "pop",
                                "fam_c", "div_c", "med_c", "cov_c",
                                "fam_t", "div_t", "med_t", "cov_t")}
    manifest: dict[str, list[str]] = {}
    nfiles = 0
    nbytes = 0

    for lvl in range(MAXLEVEL + 1):
        f = 1 << (MAXLEVEL - lvl)                     # master pixels per level pixel
        cols, rows = 2 << lvl, 1 << lvl
        lw, lh = TILE * cols, TILE * rows
        assert lw == MW // f and lh == MH // f, f"level {lvl} geometry: {lw}x{lh}"
        d = os.path.join(OUT, f"z{lvl}")
        os.makedirs(d, exist_ok=True)
        kept = []
        n = TILE + 2 * SKIRT

        for ty in range(rows):
            for tx in range(cols):
                # Read the master window this tile covers, with the skirt scaled to master px.
                y0, x0 = ty * TILE * f - SKIRT * f, tx * TILE * f - SKIRT * f
                m = n * f

                def get(name, how):
                    w = cut(src[name], y0, x0, m)
                    if f == 1:
                        return w
                    if how == "mean":
                        return reduce_mean(w.astype(np.float32), f)
                    if how == "max":
                        return reduce_max(w, f)
                    return reduce_near(w, f)

                biome = get("biome", "near").astype(np.uint8)
                cov_c = get("cov_c", "max").astype(np.uint8)
                cov_t = get("cov_t", "max").astype(np.uint8)
                # Nothing but open water: the parent level already draws this correctly.
                if lvl >= 2 and not biome.any() and not cov_c.any() and not cov_t.any():
                    continue

                z = get("elev", "mean").astype(np.float32)
                u = np.rint((np.clip(z, Z_LO, Z_HI) - Z_LO) / (Z_HI - Z_LO) * 65535
                            ).astype(np.uint32)
                snow = get("snow", "mean").astype(np.uint8)
                full = np.full(z.shape, 255, np.uint8)
                imgs = {
                    "terrain": rgba((u >> 8).astype(np.uint8), (u & 255).astype(np.uint8),
                                    snow, full),
                    "env": rgba(biome, get("pop", "mean").astype(np.uint8),
                                get("ndvi", "mean").astype(np.uint8), full),
                    "lang_c": rgba(get("fam_c", "near").astype(np.uint8),
                                   get("div_c", "max").astype(np.uint8),
                                   get("med_c", "near").astype(np.uint8), cov_c),
                    "lang_t": rgba(get("fam_t", "near").astype(np.uint8),
                                   get("div_t", "max").astype(np.uint8),
                                   get("med_t", "near").astype(np.uint8), cov_t),
                }
                for k, im in imgs.items():
                    p = os.path.join(d, f"{k}_{tx}_{ty}.png")
                    im.save(p, optimize=False, compress_level=6)
                    nfiles += 1
                    nbytes += os.path.getsize(p)
                kept.append(f"{tx}_{ty}")
        manifest[str(lvl)] = kept
        log(f"  level {lvl}  {cols}x{rows} grid  {len(kept)}/{cols*rows} tiles kept  "
            f"({360/lw*111.32:.2f} km/px)")

    meta.update({"tile": TILE, "skirt": SKIRT, "maxLevel": MAXLEVEL, "tiles": manifest,
                 "base": [2048, 1024]})
    json.dump(meta, open(os.path.join(OUT, "fields.json"), "w"))
    log(f"\n{nfiles} tile images, {nbytes/1e6:.1f} MB total")
    l0 = sum(os.path.getsize(os.path.join(OUT, "z0", f)) for f in os.listdir(os.path.join(OUT, "z0")))
    log(f"level 0 (what loads before first paint): {l0/1e6:.2f} MB")


if __name__ == "__main__":
    main()
