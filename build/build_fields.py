#!/usr/bin/env python3
"""build_fields.py — source data -> the shipped field rasters.

Emits into ../web/fields/ (relative paths, so the project directory can move — it will).

Three RGBA8 PNGs at GRID_W x GRID_H, equirectangular WGS84, row 0 = +90:

  terrain.png   R,G = elevation, 16-bit big-endian  (register B3's decision)
                B   = biome id 0..15               (the greenness channel, register C3)
                A   = population density, log-companded 8-bit
  lang_c.png    contemporary snapshot
  lang_t.png    before-contact snapshot
                R   = family index into families.json (0 = no language recorded)
                G   = diversity: distinct languages covering this pixel, clamped
                B   = documentation status 0..4 (Glottolog MED), 0 = unknown
                A   = coverage: 0 none / 128 coarse fallback / 255 real polygon

Every channel in SCOPE §3's field table appears here or it does not ship.

Run:  python3 build_fields.py
"""
from __future__ import annotations

import csv
import json
import math
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "web", "fields")
sys.path.insert(0, os.path.join(ROOT, "Research", "modeling"))

GRID_W, GRID_H = 4096, 2048

# Register B3: measured, not inherited. 16-bit linear over this range reaches the source
# DEM's own quantisation floor, so it contributes no terracing of its own.
Z_LO, Z_HI = -11000.0, 9000.0

ETOPO = os.path.join(DATA, "dem", "etopo1_ice_g_i2.bin")
ETOPO_W, ETOPO_H = 21601, 10801
GEO = os.path.join(DATA, "glottography", "geo")
GLOTTOLOG = os.path.join(DATA, "glottolog")
ECO = os.path.join(DATA, "biome", "Ecoregions2017.shp")
POP_DIR = os.path.join(DATA, "pop")


def log(*a):
    print(*a, flush=True)


# ---------------------------------------------------------------------------
# elevation
# ---------------------------------------------------------------------------

def _reduce_axis(a: np.ndarray, n_out: int, axis: int) -> np.ndarray:
    """Exact area-mean reduction along one axis to n_out bins.

    ⚠ The obvious `reshape(n_out, k, ...)` block-mean is WRONG whenever the factor is not
    an integer: 10800 // 2048 == 5 silently crops to the first 10240 rows and stretches
    95% of the world across the whole grid. That shipped once — Everest read 178 m and the
    North China Plain read 2656 m — so this uses run-length `reduceat`, which is exact for
    any ratio.
    """
    n_in = a.shape[axis]
    idx = (np.arange(n_in) * n_out) // n_in          # output bin per input row/col
    starts = np.flatnonzero(np.diff(idx, prepend=-1))
    counts = np.diff(np.append(starts, n_in)).astype(np.float32)
    s = np.add.reduceat(a, starts, axis=axis)
    shape = [1] * a.ndim
    shape[axis] = n_out
    return s / counts.reshape(shape)


def build_elevation() -> np.ndarray:
    """ETOPO1 -> GRID_H x GRID_W float32 metres, exact area-mean."""
    z = np.fromfile(ETOPO, dtype="<i2").reshape(ETOPO_H, ETOPO_W)
    # ETOPO1 is grid-registered: row 0 is +90, the last row is -90, and the first and last
    # columns are the same meridian. Drop the duplicate column and the -90 row so the grid
    # covers 360 deg x 180 deg exactly once.
    z = z[:ETOPO_H - 1, :ETOPO_W - 1].astype(np.float32)
    out = _reduce_axis(_reduce_axis(z, GRID_H, 0), GRID_W, 1)
    log(f"  elevation {out.shape} range {out.min():.0f}..{out.max():.0f} m  "
        f"land {(out > 0).mean()*100:.1f}%")
    return out


def encode_elev16(z: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    u = (np.clip(z, Z_LO, Z_HI) - Z_LO) / (Z_HI - Z_LO)
    v = np.rint(u * 65535).astype(np.uint32)
    return (v >> 8).astype(np.uint8), (v & 255).astype(np.uint8)


# ---------------------------------------------------------------------------
# biome  (register C3 — the greenness channel the amended claim needs)
# ---------------------------------------------------------------------------

# Ecoregions2017 BIOME_NUM is kept AS THE ID, 1..14, because an invented reordering is
# one more place for the raster and the label array to disagree — which they did, and the
# Sahara reported itself as "ice, rock or water" until this was straightened out.
#   1 tropical moist broadleaf   2 tropical dry broadleaf   3 tropical coniferous
#   4 temperate broadleaf        5 temperate conifer        6 boreal / taiga
#   7 tropical grassland         8 temperate grassland      9 flooded grassland
#  10 montane grassland         11 tundra                  12 mediterranean
#  13 desert & xeric           14 mangrove                 15 rock & ice (source 99)
BIOME_REMAP = {n: n for n in range(1, 15)}
BIOME_REMAP[99] = 15      # rock and ice
BIOME_REMAP[98] = 0       # lakes / no data -> unclassified


def build_biome() -> np.ndarray:
    import fiona
    from rasterio import features
    from rasterio.transform import from_bounds
    tr = from_bounds(-180, -90, 180, 90, GRID_W, GRID_H)
    shapes = []
    with fiona.open(ECO) as c:
        for f in c:
            bn = f["properties"].get("BIOME_NUM")
            v = BIOME_REMAP.get(int(bn) if bn is not None else 99, 0)
            if v:
                shapes.append((f["geometry"], v))
    out = features.rasterize(shapes, out_shape=(GRID_H, GRID_W), transform=tr,
                             fill=0, dtype="uint8")
    log(f"  biome: {len(shapes)} ecoregions -> {int((out > 0).sum()):,} px, "
        f"{len(np.unique(out))} classes")
    return out


# ---------------------------------------------------------------------------
# population
# ---------------------------------------------------------------------------

def build_population() -> np.ndarray:
    """GHS-POP counts -> log-companded density byte. Counts SUM on downsample."""
    tif = None
    for r, _, fs in os.walk(POP_DIR):
        for f in fs:
            if f.endswith(".tif"):
                tif = os.path.join(r, f)
    if not tif:
        log("  population: NO RASTER FOUND -> channel left at 0 (register D-pop)")
        return np.zeros((GRID_H, GRID_W), np.uint8)

    import rasterio
    from rasterio.enums import Resampling
    acc = np.zeros((GRID_H, GRID_W), np.float64)
    with rasterio.open(tif) as src:
        b = src.bounds
        log(f"  population: {os.path.basename(tif)} {src.width}x{src.height} {src.dtypes[0]}")
        # ⚠ GHS-POP does NOT span -90..+90 — this raster is 21384 rows covering about
        # 89.10N..-89.10S. Assuming a full 180 deg shifted the whole field by ~0.9 deg and
        # put 70 people/km2 on the summit of Everest. Always place by the geotransform.
        log(f"    bounds N{b.top:.3f} S{b.bottom:.3f} W{b.left:.3f} E{b.right:.3f}"
            f" -> spans {b.top - b.bottom:.2f} deg of latitude, not 180")
        r0 = max(0, int(round((90.0 - b.top) / 180.0 * GRID_H)))
        r1 = min(GRID_H, int(round((90.0 - b.bottom) / 180.0 * GRID_H)))
        c0 = max(0, int(round((b.left + 180.0) / 360.0 * GRID_W)))
        c1 = min(GRID_W, int(round((b.right + 180.0) / 360.0 * GRID_W)))
        oh, ow = r1 - r0, c1 - c0
        # These are population COUNTS, so the reduction must SUM, not average — and
        # rasterio's Resampling.sum is warp-only, not available on read. So: read in row
        # chunks, sum-reduce columns exactly, then scatter-add into the destination rows.
        rowmap = (np.arange(src.height) * oh) // src.height
        colstarts = np.flatnonzero(np.diff((np.arange(src.width) * ow) // src.width,
                                           prepend=-1))
        CH = 2048
        for s0 in range(0, src.height, CH):
            s1 = min(src.height, s0 + CH)
            w = rasterio.windows.Window(0, s0, src.width, s1 - s0)
            a = src.read(1, window=w, masked=True).filled(0).astype(np.float32)
            np.maximum(a, 0.0, out=a)
            colsum = np.add.reduceat(a, colstarts, axis=1)          # (chunk, ow)
            np.add.at(acc, (r0 + rowmap[s0:s1], slice(c0, c1)), colsum.astype(np.float64))
        log(f"    placed into rows {r0}..{r1}, cols {c0}..{c1}")
    total = acc.sum()
    if not (6.5e9 < total < 8.5e9):
        raise SystemExit(f"POPULATION TOTAL IMPLAUSIBLE: {total/1e9:.2f} billion")
    log(f"  population total {total/1e9:.2f} billion (expect ~7.7 for 2020)")
    # counts -> per km2, then log-compand
    lat = 90.0 - (np.arange(GRID_H) + 0.5) * (180.0 / GRID_H)
    dlat_km = (180.0 / GRID_H) * 111.32
    dlon_km = (360.0 / GRID_W) * 111.32 * np.cos(np.radians(lat))
    area = np.maximum(dlat_km * dlon_km, 1e-6)[:, None]
    dens = acc / area
    # registration check: dense places must read dense, empty places empty
    def at(la, lo):
        return float(dens[min(GRID_H - 1, int((90 - la) / 180 * GRID_H)),
                          min(GRID_W - 1, int((lo + 180) / 360 * GRID_W))])
    # The primary guard is the TOTAL, above: honouring the geotransform moved it from
    # 7.50 to 7.84 billion, which is how the misregistration was caught. These are the
    # secondary spot checks. Note the Everest bound is 80, not 5: at this grid a cell near
    # the summit is ~22 km across and includes the inhabited Khumbu valleys, so ~28/km2 is
    # correct. An earlier bound of 25 failed on a right answer.
    checks = [("Netherlands", 52.1, 5.3, 200, None), ("Nile delta", 30.9, 31.2, 200, None),
              ("Bangladesh", 23.8, 90.4, 300, None), ("Everest", 27.99, 86.93, None, 80),
              ("empty Sahara", 24.0, 20.0, None, 5), ("East Antarctica", -75.0, 0.0, None, 1),
              ("central Greenland", 72.0, -42.0, None, 1),
              ("mid-Pacific", 10.0, -150.0, None, 1)]
    bad = [f"{n} = {at(la, lo):.0f}/km2"
           for n, la, lo, lob, hib in checks
           if (lob is not None and at(la, lo) < lob) or (hib is not None and at(la, lo) > hib)]
    if bad:
        raise SystemExit("POPULATION REGISTRATION FAILED: " + "; ".join(bad))
    log(f"  registration: {len(checks)}/{len(checks)} density checks pass "
        f"(Netherlands {at(52.1,5.3):.0f}, Bangladesh {at(23.8,90.4):.0f}, "
        f"Everest {at(27.99,86.93):.1f}/km2)")
    b = np.rint(np.clip(np.log10(1.0 + dens) / 4.0, 0, 1) * 255).astype(np.uint8)
    log(f"  density max {dens.max():.0f}/km2, byte mean {b.mean():.1f}")
    return b


# ---------------------------------------------------------------------------
# languages
# ---------------------------------------------------------------------------

def load_glottolog() -> tuple[dict, dict, dict]:
    """glottocode -> (family_id, med, name), plus family ordering."""
    med = {}
    with open(os.path.join(GLOTTOLOG, "values.csv"), newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["Parameter_ID"] == "med" and r["Value"]:
                try:
                    med[r["Language_ID"]] = int(float(r["Value"]))
                except ValueError:
                    pass
    fam, name, isolate = {}, {}, {}
    with open(os.path.join(GLOTTOLOG, "languages.csv"), newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            gc = r["Glottocode"]
            fam[gc] = r["Family_ID"] or gc          # an isolate is its own family
            name[gc] = r["Name"]
            isolate[gc] = r["Is_Isolate"] == "True"
    return fam, med, name


def build_language(snapshot_files: list[str], fam: dict, med: dict,
                   fam_index: dict) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    from rasterio import features
    from rasterio.transform import from_bounds
    tr = from_bounds(-180, -90, 180, 90, GRID_W, GRID_H)

    feats = []                                   # (geom, glottocode, area)
    for fn in snapshot_files:
        with open(fn, encoding="utf-8") as f:
            gj = json.load(f)
        for ft in gj.get("features", []):
            g = ft.get("geometry")
            if not g:
                continue
            p = ft.get("properties", {}) or {}
            gc = (p.get("cldf:languageReference") or p.get("Glottocode")
                  or p.get("glottocode") or p.get("cldf:id") or p.get("id"))
            if not isinstance(gc, str) or len(gc) != 8:
                continue
            feats.append((g, gc, _rough_area(g)))
    log(f"    {len(feats):,} polygons with a glottocode")
    if not feats:
        z = np.zeros((GRID_H, GRID_W), np.uint8)
        return z, z.copy(), z.copy(), z.copy()

    # diversity: one pass, ADD, so overlapping territories accumulate
    div = features.rasterize([(g, 1) for g, _, _ in feats], out_shape=(GRID_H, GRID_W),
                             transform=tr, fill=0, dtype="uint16",
                             merge_alg=features.MergeAlg.add)
    # family + documentation: paint LARGEST first so the most local language wins the pixel
    feats.sort(key=lambda t: -t[2])
    famsh = [(g, fam_index.get(fam.get(gc, gc), 0)) for g, gc, _ in feats]
    medsh = [(g, min(4, med.get(gc, 0)) + 1) for g, gc, _ in feats]
    famr = features.rasterize(famsh, out_shape=(GRID_H, GRID_W), transform=tr,
                              fill=0, dtype="uint8")
    medr = features.rasterize(medsh, out_shape=(GRID_H, GRID_W), transform=tr,
                              fill=0, dtype="uint8")
    cov = np.where(famr > 0, 255, 0).astype(np.uint8)
    divb = np.clip(div, 0, 255).astype(np.uint8)
    log(f"    covered {int((cov > 0).sum()):,} px  "
        f"max diversity {int(div.max())}  families used {len(np.unique(famr))}")
    return famr, divb, medr, cov


def _rough_area(g) -> float:
    """Bounding-box area in square degrees. Only used for paint ordering."""
    xs, ys = [], []

    def walk(c):
        if isinstance(c, (list, tuple)) and c and isinstance(c[0], (int, float)):
            xs.append(c[0]); ys.append(c[1]); return
        for x in c:
            walk(x)
    walk(g.get("coordinates", []))
    if not xs:
        return 0.0
    return (max(xs) - min(xs)) * (max(ys) - min(ys))


# ---------------------------------------------------------------------------

def check_registration(z: np.ndarray) -> None:
    """Assert the grid is registered to the real Earth, at named places.

    A resample that silently crops or shifts is invisible to inspection and obvious to
    eight assertions. This exists because one did: an integer-floor block mean stretched
    95% of the world across the grid, and Everest read 178 m.
    """
    def at(lat, lon):
        r = min(GRID_H - 1, int((90 - lat) / 180 * GRID_H))
        c = min(GRID_W - 1, int((lon + 180) / 360 * GRID_W))
        return float(z[r, c])
    cases = [("Everest", 27.99, 86.93, 4000, None),
             ("Dead Sea", 31.5, 35.5, None, 0),
             ("North China Plain", 35.5, 116.5, 0, 300),
             ("Gabon", -0.5, 12.5, 0, 900),
             ("mid-Atlantic", 0.0, -30.0, None, -2000),
             ("East Antarctica", -75.0, 0.0, 1500, None),
             ("Amazon", -4.0, -63.0, 0, 400),
             ("Netherlands", 52.1, 5.3, -20, 120)]
    bad = []
    for name, la, lo, lob, hib in cases:
        v = at(la, lo)
        if (lob is not None and v < lob) or (hib is not None and v > hib):
            bad.append(f"{name} = {v:.0f} m")
    if bad:
        raise SystemExit("REGISTRATION FAILED — the grid is not on the real Earth: "
                         + "; ".join(bad))
    log(f"  registration: {len(cases)}/{len(cases)} named places in range")


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    log("build_fields.py")

    log(" elevation + biome + population")
    z = build_elevation()
    check_registration(z)
    hi, lo = encode_elev16(z)
    biome = build_biome()
    pop = build_population()
    # Alpha is FORCED to 255 on every texture the CPU reads back. A 2D canvas is
    # premultiplied, so data parked in alpha destroys the other three channels on
    # readback — the readout reported "11000 m below sea level" in Gabon until this was
    # split. The GPU is unaffected; only the CPU probe was wrong.
    a255 = np.full((GRID_H, GRID_W), 255, np.uint8)
    Image.fromarray(np.dstack([hi, lo, np.zeros_like(hi), a255])).save(
        os.path.join(OUT, "terrain.png"), optimize=True)
    Image.fromarray(np.dstack([biome, pop, np.zeros_like(biome), a255])).save(
        os.path.join(OUT, "env.png"), optimize=True)

    fam, med, name = load_glottolog()
    families = sorted({fam[g] for g in fam})
    fam_index = {f: i + 1 for i, f in enumerate(families[:254])}
    log(f" {len(fam):,} glottocodes, {len(families)} families "
        f"({len(fam_index)} indexed into the byte channel)")

    idx = json.load(open(os.path.join(GEO, "_index.json")))
    groups = {"c": [], "t": []}
    for k in idx:
        p = os.path.join(GEO, k + ".geojson")
        groups["t" if k.endswith("__traditional") else "c"].append(p)
    # the world dataset's "traditional" is the only true before-contact source; everything
    # else is contemporary and is reused in both snapshots so the map is not half empty.
    groups["t"] += [p for p in groups["c"] if not p.endswith("__contemporary.geojson")]

    stats = {}
    for tag, files in groups.items():
        log(f" languages [{tag}] from {len(files)} files")
        famr, divb, medr, cov = build_language(files, fam, med, fam_index)
        Image.fromarray(np.dstack([famr, divb, medr, cov]), "RGBA").save(
            os.path.join(OUT, f"lang_{tag}.png"), optimize=True)
        stats[tag] = dict(covered_px=int((cov > 0).sum()), max_div=int(divb.max()))

    meta = dict(grid=[GRID_W, GRID_H], z_lo=Z_LO, z_hi=Z_HI,
                families=[{"id": f, "name": name.get(f, f), "idx": i}
                          for f, i in fam_index.items()],
                snapshots=stats)
    json.dump(meta, open(os.path.join(OUT, "fields.json"), "w"))

    build_language_index(fam, med, name, fam_index)


def build_language_index(fam: dict, med: dict, name: dict, fam_index: dict) -> None:
    """web/data/languages.json — the clickable card index.

    Spoken-L1 languages only, filtered by `category` and not by `Level` (register A6):
    Level alone would fold in 227 sign languages and 380 bookkeeping placeholders.

    ⚠ These are Glottolog REFERENCE names, not autonyms. SCOPE §7 and CLAUDE.md rule 11
    require the autonym first, and no autonym source is wired yet — so the app labels
    this explicitly rather than passing an exonym off as a language's own name. Register
    item D6.
    """
    cat, aes = {}, {}
    with open(os.path.join(GLOTTOLOG, "values.csv"), newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["Parameter_ID"] == "category":
                cat[r["Language_ID"]] = r["Value"]
            elif r["Parameter_ID"] == "aes" and r["Value"]:
                try:
                    aes[r["Language_ID"]] = int(float(r["Value"]))
                except ValueError:
                    pass
    rows = []
    with open(os.path.join(GLOTTOLOG, "languages.csv"), newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["Level"] != "language" or cat.get(r["ID"]) != "Spoken_L1_Language":
                continue
            if not r["Latitude"]:
                continue
            gc = r["Glottocode"]
            rows.append([gc, r["Name"], round(float(r["Longitude"]), 3),
                         round(float(r["Latitude"]), 3),
                         fam_index.get(fam.get(gc, gc), 0),
                         med.get(gc, -1), aes.get(gc, 0),
                         r["ISO639P3code"] or "",
                         int(r["First_Year_Of_Documentation"] or 0)])
    d = os.path.join(ROOT, "web", "data")
    os.makedirs(d, exist_ok=True)
    json.dump({"fields": ["code", "name", "lon", "lat", "fam", "med", "aes", "iso", "first"],
               "note": "Glottolog reference names, NOT autonyms — see register D6",
               "rows": rows}, open(os.path.join(d, "languages.json"), "w"),
              separators=(",", ":"))
    log(f"  languages.json  {len(rows):,} spoken-L1 languages with coordinates  "
        f"{os.path.getsize(os.path.join(d, 'languages.json'))/1e6:.2f} MB")
    for f in sorted(os.listdir(OUT)):
        log(f"  {f:16s} {os.path.getsize(os.path.join(OUT, f))/1e6:7.2f} MB")


if __name__ == "__main__":
    main()
