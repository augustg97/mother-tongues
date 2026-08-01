#!/usr/bin/env python3
"""build_fields.py — build the master field rasters at 16384x8192, as memory-mapped .npy.

WHAT CHANGED, AND WHY IT IS NOT JUST A BIGGER NUMBER.

The grid was 4096x2048: 9.8 km per pixel at the equator. At that size a "language area" is a
blob, a coastline is a staircase, and the ground is 15 flat biome colours — a choropleth with
relief shading on it. This build is **16384x8192, 2.44 km at the equator**, which is 76% of
ETOPO1's native 1-arcminute resolution: near the limit of what the elevation source can
honestly support, and 16x the pixels.

Resolution alone would only make a bigger choropleth, so the material changed too:
  * **NDVI** (measured vegetation, NASA public domain) replaces flat biome colour as the tone.
    Biome stays as the *classification* — what a place IS — while greenness carries how much
    is growing there, continuously, per pixel.
  * **snow cover**, measured monthly, instead of a snowline height I would otherwise invent.
  * **slope** is no longer only a lighting term; it becomes a material coordinate, so rock
    shows through on steep ground the way it does on Earth.

MEMORY. 16x the pixels is 2.0 GB of master arrays. Everything is written through
`np.lib.format.open_memmap` and filled in place, and the elevation reduction runs in
output-column blocks, so peak RSS stays near 300 MB rather than near 4 GB. `build_tiles.py`
then memory-maps these and cuts the pyramid without loading them either.

The exact-area reduction, the population geotransform placement and the registration
assertions are unchanged in substance — they are the three things that have each already
caught a silent, invisible, catastrophic error, and they are load-bearing.

Run:  python3 build_fields.py
"""
from __future__ import annotations

import csv
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
DATA = os.path.join(ROOT, "data")
MASTER = os.path.join(DATA, "master")
sys.path.insert(0, os.path.join(ROOT, "Research", "modeling"))

GRID_W, GRID_H = 16384, 8192

# Register B3: measured, not inherited. 16-bit linear over this range reaches the source
# DEM's own quantisation floor, so it contributes no terracing of its own.
Z_LO, Z_HI = -11000.0, 9000.0

ETOPO = os.path.join(DATA, "dem", "etopo1_ice_g_i2.bin")
ETOPO_W, ETOPO_H = 21601, 10801
GEO = os.path.join(DATA, "glottography", "geo")
GLOTTOLOG = os.path.join(DATA, "glottolog")
ECO = os.path.join(DATA, "biome", "Ecoregions2017.shp")
POP_DIR = os.path.join(DATA, "pop")
EARTH = os.path.join(DATA, "earth")
AUTO = os.path.join(DATA, "autonyms")


def log(*a):
    print(*a, flush=True)


REUSE = os.environ.get("MT_REUSE") == "1"


def have(name: str, shape) -> bool:
    """Reuse a master that is already on disk and the right shape (set MT_REUSE=1).

    Iteration only. A build for publication runs without it, so the masters and the tiles
    always come from one pass over the sources.
    """
    p = os.path.join(MASTER, name + ".npy")
    if not (REUSE and os.path.exists(p)):
        return False
    try:
        return np.load(p, mmap_mode="r").shape == tuple(shape)
    except Exception:
        return False


def mm(name: str, shape, dtype):
    os.makedirs(MASTER, exist_ok=True)
    return np.lib.format.open_memmap(os.path.join(MASTER, name + ".npy"), mode="w+",
                                     dtype=dtype, shape=shape)


def _starts(n_in: int, n_out: int) -> np.ndarray:
    """Block boundaries for an exact area reduction of n_in samples into n_out cells.

    ⚠ The obvious `reshape(n_out, k, ...)` block-mean is WRONG whenever the factor is not an
    integer: 10800 // 8192 == 1 would silently crop to the first 8192 rows. That exact bug
    stretched 95% of the world across the grid and made Everest read 178 m. Never reshape.
    """
    idx = (np.arange(n_in) * n_out) // n_in
    return np.flatnonzero(np.diff(idx, prepend=-1))


def _reduce_axis(a: np.ndarray, n_out: int, axis: int) -> np.ndarray:
    n_in = a.shape[axis]
    st = _starts(n_in, n_out)
    counts = np.diff(np.append(st, n_in)).astype(np.float32)
    s = np.add.reduceat(a, st, axis=axis)
    shape = [1] * a.ndim
    shape[axis] = n_out
    return s / counts.reshape(shape)


# ---------------------------------------------------------------------------
# elevation
# ---------------------------------------------------------------------------

def build_elevation() -> np.ndarray:
    """ETOPO1 -> GRID_H x GRID_W int16 metres, exact area-mean, in column blocks."""
    if have("elev", (GRID_H, GRID_W)):
        log("  elevation: reusing master")
        return np.load(os.path.join(MASTER, "elev.npy"), mmap_mode="r")
    src = np.memmap(ETOPO, dtype="<i2", mode="r", shape=(ETOPO_H, ETOPO_W))
    # Grid-registered: row 0 is +90, last row -90, first and last columns the same meridian.
    # Drop the duplicate column and the -90 row so the grid covers 360x180 exactly once.
    ih, iw = ETOPO_H - 1, ETOPO_W - 1
    out = mm("elev", (GRID_H, GRID_W), np.int16)
    cst = np.append(_starts(iw, GRID_W), iw)
    BL = 1024
    for j0 in range(0, GRID_W, BL):
        j1 = min(GRID_W, j0 + BL)
        i0, i1 = int(cst[j0]), int(cst[j1])
        blk = np.asarray(src[:ih, i0:i1], dtype=np.float32)
        blk = _reduce_axis(blk, GRID_H, 0)
        local = _starts(i1 - i0, j1 - j0)
        cnt = np.diff(np.append(local, i1 - i0)).astype(np.float32)
        out[:, j0:j1] = np.rint(np.add.reduceat(blk, local, axis=1) / cnt).astype(np.int16)
    log(f"  elevation {out.shape} range {out.min()}..{out.max()} m  "
        f"land {(np.asarray(out[::8, ::8]) > 0).mean()*100:.1f}%")
    return out


# ---------------------------------------------------------------------------
# biome  — the classification layer. NOT the tone layer any more; NDVI is.
# ---------------------------------------------------------------------------

#   1 tropical moist broadleaf   2 tropical dry broadleaf   3 tropical coniferous
#   4 temperate broadleaf        5 temperate conifer        6 boreal / taiga
#   7 tropical grassland         8 temperate grassland      9 flooded grassland
#  10 montane grassland         11 tundra                  12 mediterranean
#  13 desert & xeric            14 mangrove                15 rock & ice (source 99)
BIOME_REMAP = {n: n for n in range(1, 15)}
BIOME_REMAP[99] = 15
BIOME_REMAP[98] = 0


def build_biome() -> np.ndarray:
    if have("biome", (GRID_H, GRID_W)):
        log("  biome: reusing master")
        return np.load(os.path.join(MASTER, "biome.npy"), mmap_mode="r")
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
    out = mm("biome", (GRID_H, GRID_W), np.uint8)
    # Rasterise in horizontal bands: one 16384x8192 uint8 output is fine, but rasterio's
    # internal buffers for 4,500 polygons at this size are not.
    BH = 1024
    for r0 in range(0, GRID_H, BH):
        r1 = min(GRID_H, r0 + BH)
        sub = from_bounds(-180, 90 - r1 * 180.0 / GRID_H, 180, 90 - r0 * 180.0 / GRID_H,
                          GRID_W, r1 - r0)
        out[r0:r1] = features.rasterize(shapes, out_shape=(r1 - r0, GRID_W), transform=sub,
                                        fill=0, dtype="uint8")
    log(f"  biome: {len(shapes)} ecoregions -> "
        f"{int((np.asarray(out[::8, ::8]) > 0).sum())*64:,} px approx, 15 classes")
    return out


# ---------------------------------------------------------------------------
# measured surface: NDVI greenness and snow cover  (registers C3, fidelity)
# ---------------------------------------------------------------------------

def _read_earth(prefix: str, lo: float, hi: float, how: str = "mean",
                valid: tuple | None = None) -> np.ndarray | None:
    """Reduce the monthly climatology to one plate-carree plane, rescaled to 0..1.

    `how` matters and is not a preference. Annual-MEAN NDVI is dominated by the months a
    boreal forest is under snow, so taiga scores like semi-desert and Siberia renders as bare
    mud — which is what the first build of this looked like. **Peak** NDVI is the standard
    measure of how much vegetation a place actually carries, and it is also the thing the eye
    means by "green". Snow, by contrast, wants the mean: peak snow cover is 100% almost
    everywhere it ever snows, which would put permanent ice on Warsaw.
    """
    import glob
    import rasterio
    fs = sorted(glob.glob(os.path.join(EARTH, prefix + "_*.tif")))
    if not fs:
        return None
    acc = None
    n = 0
    for f in fs:
        with rasterio.open(f) as s:
            a = s.read(1).astype(np.float32)
        # NEO float rasters use 99999 as the no-data sentinel. Left in, it becomes a
        # continent-sized white blob wherever the sensor never reported.
        a = np.where((a > 1e4) | (a < -1e3), np.nan, a)
        if acc is None:
            acc = a
        elif how == "max":
            acc = np.fmax(acc, a)
        else:
            acc = np.nansum(np.dstack([acc, a]), axis=2)
        n += 1
    m = acc if how == "max" else acc / max(n, 1)
    if valid is not None:
        # ⚠ A dataset is not what its name suggests. `AVHRR_CLIM_M` reads like a vegetation
        # climatology and is sea surface temperature: -2..32, NaN over every land pixel. It
        # was wired in as greenness and saturated the entire land surface before anyone
        # looked. Assert the physical range of the QUANTITY, so the wrong file fails the
        # build instead of quietly colouring it.
        lo_, hi_ = float(np.nanmin(m)), float(np.nanmax(m))
        if not (valid[0] <= lo_ and hi_ <= valid[1]):
            raise SystemExit(
                f"{prefix}: values {lo_:.3f}..{hi_:.3f} are outside the physical range "
                f"{valid} for this quantity — this is the wrong dataset")
        log(f"    {prefix}: raw {lo_:.3f}..{hi_:.3f}, within {valid}")
    return np.clip((m - lo) / (hi - lo), 0, 1)


def _upsample(a: np.ndarray, fill: float = 0.0) -> np.ndarray:
    """Nearest-neighbour lift of a coarse global plate-carree grid onto the master grid."""
    a = np.nan_to_num(a, nan=fill)
    r = (np.arange(GRID_H) * a.shape[0]) // GRID_H
    c = (np.arange(GRID_W) * a.shape[1]) // GRID_W
    return a[r][:, c]


def build_surface() -> tuple[np.ndarray, np.ndarray]:
    """NDVI greenness and snow-cover fraction, both 0..255. Absent source -> zeros, stated."""
    g = _read_earth("ndvi", 0.0, 0.90, "max", valid=(-1.0, 1.0))   # PEAK, not mean
    s = _read_earth("snow", 0.0, 100.0, valid=(0.0, 100.0))
    ndvi = mm("ndvi", (GRID_H, GRID_W), np.uint8)
    snow = mm("snow", (GRID_H, GRID_W), np.uint8)
    if g is None:
        log("  NDVI: NO RASTERS — greenness channel zero, the map falls back to biome tone")
    else:
        BH = 2048
        up = _upsample(g)
        for r0 in range(0, GRID_H, BH):
            ndvi[r0:r0 + BH] = np.rint(up[r0:r0 + BH] * 255).astype(np.uint8)
        log(f"  NDVI (peak of year): mean {float(np.nanmean(g)):.3f}, "
            f"vegetated (>0.3) {float((g > 0.3).mean())*100:.1f}% of the grid")
        del up
    if s is None:
        log("  snow: NO RASTERS — snow channel zero")
    else:
        up = _upsample(s)
        for r0 in range(0, GRID_H, 2048):
            snow[r0:r0 + 2048] = np.rint(up[r0:r0 + 2048] * 255).astype(np.uint8)
        log(f"  snow: mean cover {float(np.nanmean(s))*100:.1f}%")
        del up
    return ndvi, snow


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
    out = mm("pop", (GRID_H, GRID_W), np.uint8)
    if not tif:
        log("  population: NO RASTER FOUND -> channel left at 0")
        return out

    import rasterio
    acc = np.zeros((GRID_H, GRID_W), np.float32)   # 7 source cells per dest: f32 is exact
    with rasterio.open(tif) as src:
        b = src.bounds
        log(f"  population: {os.path.basename(tif)} {src.width}x{src.height}")
        # ⚠ GHS-POP does NOT span -90..+90 — this raster covers about 89.10N..-89.10S.
        # Assuming a full 180 deg shifted the field and put 70 people/km2 on Everest.
        log(f"    bounds N{b.top:.3f} S{b.bottom:.3f} -> {b.top - b.bottom:.2f} deg, not 180")
        r0 = max(0, int(round((90.0 - b.top) / 180.0 * GRID_H)))
        r1 = min(GRID_H, int(round((90.0 - b.bottom) / 180.0 * GRID_H)))
        c0 = max(0, int(round((b.left + 180.0) / 360.0 * GRID_W)))
        c1 = min(GRID_W, int(round((b.right + 180.0) / 360.0 * GRID_W)))
        oh, ow = r1 - r0, c1 - c0
        # COUNTS, so the reduction must SUM. rasterio's Resampling.sum is warp-only.
        rowmap = (np.arange(src.height) * oh) // src.height
        colstarts = np.flatnonzero(np.diff((np.arange(src.width) * ow) // src.width,
                                           prepend=-1))
        for s0 in range(0, src.height, 2048):
            s1 = min(src.height, s0 + 2048)
            w = rasterio.windows.Window(0, s0, src.width, s1 - s0)
            a = src.read(1, window=w, masked=True).filled(0).astype(np.float32)
            np.maximum(a, 0.0, out=a)
            colsum = np.add.reduceat(a, colstarts, axis=1)
            np.add.at(acc, (r0 + rowmap[s0:s1], slice(c0, c1)), colsum)
    total = float(acc.sum())
    if not (6.5e9 < total < 8.5e9):
        raise SystemExit(f"POPULATION TOTAL IMPLAUSIBLE: {total/1e9:.2f} billion")
    log(f"  population total {total/1e9:.2f} billion (expect ~7.7 for 2020)")

    lat = 90.0 - (np.arange(GRID_H) + 0.5) * (180.0 / GRID_H)
    dlat_km = (180.0 / GRID_H) * 111.32
    dlon_km = (360.0 / GRID_W) * 111.32 * np.cos(np.radians(lat))
    area = np.maximum(dlat_km * dlon_km, 1e-9)[:, None]
    dens = acc / area
    del acc

    # ⚠ These bounds must test REGISTRATION, not resolution. The previous set sampled a single
    # cell, and at 9.8 km "52.1N 5.3E" averaged in the whole Randstad and read 400/km2; at
    # 2.45 km the same coordinate is rural Utrecht province and reads 103. Nothing moved — the
    # grid got finer. A single-cell bound therefore has to be re-tuned every time the grid
    # changes, which is a bound that tests the wrong thing. Take the MAX over a ~15 km window
    # instead: misregistration still fails it, a resolution change does not.
    K = max(1, int(round(7.0 / (360.0 / GRID_W * 111.32))))

    def win(la, lo):
        r = min(GRID_H - 1, int((90 - la) / 180 * GRID_H))
        c = min(GRID_W - 1, int((lo + 180) / 360 * GRID_W))
        return dens[max(0, r - K):r + K + 1, max(0, c - K):c + K + 1]

    # Lower bounds ("this region is inhabited") take the window MAX: robust to where a city
    # centre falls inside a cell. Upper bounds ("this cell is empty") take the CENTRE CELL:
    # a max would fail on Gorak Shep, a real settlement 7 km from Everest's summit with real
    # people in it. Asking "is the summit cell empty" and "is anywhere near here inhabited"
    # are different questions and they need different statistics.
    def at(la, lo):
        return float(win(la, lo).max())

    def cell(la, lo):
        return float(dens[min(GRID_H - 1, int((90 - la) / 180 * GRID_H)),
                          min(GRID_W - 1, int((lo + 180) / 360 * GRID_W))])
    checks = [("Netherlands", 52.1, 5.3, 400, None), ("Nile delta", 30.9, 31.2, 400, None),
              ("Bangladesh", 23.8, 90.4, 800, None), ("Everest", 27.99, 86.93, None, 5),
              ("empty Sahara", 24.0, 20.0, None, 8), ("East Antarctica", -75.0, 0.0, None, 1),
              ("central Greenland", 72.0, -42.0, None, 1),
              ("mid-Pacific", 10.0, -150.0, None, 1)]
    bad = []
    for n, la, lo, lob, hib in checks:
        if lob is not None and at(la, lo) < lob:
            bad.append(f"{n} peak {at(la, lo):.0f}/km2 < {lob}")
        if hib is not None and cell(la, lo) > hib:
            bad.append(f"{n} cell {cell(la, lo):.0f}/km2 > {hib}")
    if bad:
        raise SystemExit("POPULATION REGISTRATION FAILED: " + "; ".join(bad))
    log(f"  registration: {len(checks)}/{len(checks)} density checks pass "
        f"(Netherlands {at(52.1,5.3):.0f}, Bangladesh {at(23.8,90.4):.0f}, "
        f"Everest {at(27.99,86.93):.1f}/km2)")
    for r0 in range(0, GRID_H, 1024):
        out[r0:r0 + 1024] = np.rint(
            np.clip(np.log10(1.0 + dens[r0:r0 + 1024]) / 4.0, 0, 1) * 255).astype(np.uint8)
    log(f"  density max {dens.max():.0f}/km2")
    return out


# ---------------------------------------------------------------------------
# languages
# ---------------------------------------------------------------------------

def load_glottolog() -> tuple[dict, dict, dict]:
    med = {}
    with open(os.path.join(GLOTTOLOG, "values.csv"), newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["Parameter_ID"] == "med" and r["Value"]:
                try:
                    med[r["Language_ID"]] = int(float(r["Value"]))
                except ValueError:
                    pass
    fam, name = {}, {}
    with open(os.path.join(GLOTTOLOG, "languages.csv"), newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            gc = r["Glottocode"]
            fam[gc] = r["Family_ID"] or gc
            name[gc] = r["Name"]
    return fam, med, name


def _rough_area(g) -> float:
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


RICH_W, RICH_H = 2048, 1024          # ~19.6 km cells: the neighbourhood richness is counted in


def build_language(tag: str, snapshot_files: list[str], fam: dict, med: dict,
                   fam_index: dict) -> dict:
    """Rasterise one snapshot's language field.

    ⚠ WHAT "DIVERSITY" MEANS, AND WHAT IT USED TO MEAN. The first version counted OVERLAPPING
    POLYGONS per pixel. That is not linguistic diversity — it is a count of how many source
    datasets happen to cover the same ground. Most Glottography datasets PARTITION space, one
    territory per language, so the count was 1 almost everywhere, and it was highest exactly
    where two datasets overlapped. Measured in the New Guinea highlands — the densest
    linguistic region on Earth and the one SCOPE §3 names — it read **1**, while a cell in
    India read 43 because 22 official languages were stacked on it.

    Richness is a NEIGHBOURHOOD property: how many distinct languages have territory within
    ~20 km. That is the standard measure, it is what the shimmer is supposed to show, and it
    is what this now computes.

    Duplicates are resolved per glottocode BEFORE counting: a language mapped by three
    datasets is one language. The most spatially specific dataset wins — smallest total area,
    because a regional survey that draws a valley is better evidence than a world atlas that
    draws a province.
    """
    from rasterio import features
    from rasterio.transform import from_bounds

    per: dict[str, dict[str, dict]] = {}
    total_feats = 0
    for fn in snapshot_files:
        ds = os.path.basename(fn).split(".")[0]
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
            total_feats += 1
            e = per.setdefault(gc, {}).setdefault(ds, {"geoms": [], "area": 0.0})
            e["geoms"].append(g)
            e["area"] += _rough_area(g)

    # Two sets, because counting and painting want different things.
    #  * RICHNESS counts languages, so each glottocode appears exactly once, from its most
    #    spatially specific dataset — a regional survey that draws a valley is better evidence
    #    than a world atlas that draws a province.
    #  * COVERAGE and family paint the UNION of all the evidence: dropping a broader polygon
    #    because a narrower one exists would erase ground the record does cover. Using the
    #    deduped set for painting cost 10.6 million pixels of real coverage.
    ded = []
    for gc, dsmap in per.items():
        ds = min(dsmap, key=lambda d: dsmap[d]["area"])
        for g in dsmap[ds]["geoms"]:
            ded.append((g, gc, dsmap[ds]["area"]))
    feats = [(g, gc, e["area"]) for gc, dsmap in per.items()
             for ds, e in dsmap.items() for g in e["geoms"]]
    log(f"    {total_feats:,} polygons · {len(per):,} distinct languages · "
        f"{len(ded):,} parts counted for richness, {len(feats):,} painted")

    famr = mm(f"fam_{tag}", (GRID_H, GRID_W), np.uint8)
    divr = mm(f"div_{tag}", (GRID_H, GRID_W), np.uint8)
    medr = mm(f"med_{tag}", (GRID_H, GRID_W), np.uint8)
    covr = mm(f"cov_{tag}", (GRID_H, GRID_W), np.uint8)
    if not feats:
        return {"covered": 0, "max_div": 0, "languages": 0}

    # ---- richness, on its own coarse grid, one count per distinct language ---------------
    rtr = from_bounds(-180, -90, 180, 90, RICH_W, RICH_H)
    rich = features.rasterize([(g, 1) for g, _, _ in ded], out_shape=(RICH_H, RICH_W),
                              transform=rtr, fill=0, dtype="uint16",
                              merge_alg=features.MergeAlg.add)
    log(f"    richness on a {RICH_W}x{RICH_H} grid (~{360/RICH_W*111.32:.0f} km cells): "
        f"max {int(rich.max())}, mean where occupied {float(rich[rich>0].mean()):.2f}")
    rr = (np.arange(GRID_H) * RICH_H) // GRID_H
    rc = (np.arange(GRID_W) * RICH_W) // GRID_W

    feats.sort(key=lambda t: -t[2])              # largest first: the most local wins the pixel
    famsh = [(g, fam_index.get(fam.get(gc, gc), 255)) for g, gc, _ in feats]
    medsh = [(g, min(4, med.get(gc, 0)) + 1) for g, gc, _ in feats]

    covered = 0
    BH = 1024
    for r0 in range(0, GRID_H, BH):
        r1 = min(GRID_H, r0 + BH)
        sub = from_bounds(-180, 90 - r1 * 180.0 / GRID_H, 180, 90 - r0 * 180.0 / GRID_H,
                          GRID_W, r1 - r0)
        sh = (r1 - r0, GRID_W)
        f_ = features.rasterize(famsh, out_shape=sh, transform=sub, fill=0, dtype="uint8")
        m_ = features.rasterize(medsh, out_shape=sh, transform=sub, fill=0, dtype="uint8")
        famr[r0:r1] = f_
        medr[r0:r1] = m_
        divr[r0:r1] = np.clip(rich[rr[r0:r1]][:, rc], 0, 255).astype(np.uint8)
        covr[r0:r1] = np.where(f_ > 0, 255, 0).astype(np.uint8)
        covered += int((f_ > 0).sum())
    log(f"    covered {covered:,} px")
    return {"covered": covered, "max_div": int(rich.max()), "languages": len(per),
            "rich_grid": [RICH_W, RICH_H], "rich_km": round(360 / RICH_W * 111.32)}


# ---------------------------------------------------------------------------

def check_registration(z) -> None:
    """Assert the grid is on the real Earth, at named places. This has caught a real bug."""
    def at(lat, lon):
        return float(z[min(GRID_H - 1, int((90 - lat) / 180 * GRID_H)),
                       min(GRID_W - 1, int((lon + 180) / 360 * GRID_W))])
    cases = [("Everest", 27.99, 86.93, 4000, None), ("Dead Sea", 31.5, 35.5, None, 0),
             ("North China Plain", 35.5, 116.5, 0, 300), ("Gabon", -0.5, 12.5, 0, 900),
             ("mid-Atlantic", 0.0, -30.0, None, -2000),
             ("East Antarctica", -75.0, 0.0, 1500, None), ("Amazon", -4.0, -63.0, 0, 400),
             ("Netherlands", 52.1, 5.3, -20, 120)]
    bad = [f"{n} = {at(la, lo):.0f} m" for n, la, lo, lob, hib in cases
           if (lob is not None and at(la, lo) < lob) or (hib is not None and at(la, lo) > hib)]
    if bad:
        raise SystemExit("REGISTRATION FAILED — not on the real Earth: " + "; ".join(bad))
    log(f"  registration: {len(cases)}/{len(cases)} named places in range "
        f"(Everest {at(27.99,86.93):.0f} m)")


def main() -> None:
    os.makedirs(MASTER, exist_ok=True)
    log(f"build_fields.py — master grid {GRID_W}x{GRID_H} "
        f"({360/GRID_W*111.32:.2f} km per pixel at the equator)")

    log(" elevation")
    z = build_elevation()
    check_registration(z)
    del z
    log(" biome")
    build_biome()
    log(" measured surface")
    build_surface()
    log(" population")
    build_population()

    log(" languages")
    fam, med, name = load_glottolog()
    # One byte holds the family, so at most 255 distinct values exist. The previous build
    # took the first 254 families in ALPHABETICAL order and silently dropped the rest to 0,
    # i.e. to "no language recorded" — Uto-Aztecan and Yeniseian rendered as empty ground.
    # Rank by number of languages instead, and give everything past 254 the shared index 255,
    # which the legend names honestly rather than pretending it is absence.
    from collections import Counter
    cnt = Counter(fam.get(gc, gc) for gc in fam)
    ranked = [f for f, _ in cnt.most_common()]
    fam_index = {f: i + 1 for i, f in enumerate(ranked[:254])}
    for f in ranked[254:]:
        fam_index[f] = 255
    log(f"  {len(cnt)} families; 254 carry their own index, "
        f"{max(0, len(ranked)-254)} share index 255")

    allg = sorted(os.path.join(GEO, f) for f in os.listdir(GEO) if f.endswith(".geojson"))
    # ⚠ EXCLUDED: `wikipedia2024officiallang` is 158 country-shaped polygons of *official*
    # languages. It is a map of state policy, not of where a language is spoken. Rasterised
    # with the rest it adds +1 to the diversity count over entire countries, inflates the
    # coverage figure with ground nobody surveyed linguistically, and paints French across
    # Gabon and Spanish across the Andes — the readout said "Indo-European" in Gabon, which
    # is how this was caught. The other 25 datasets are actual language areas.
    dropped = [f for f in allg if "officiallang" in os.path.basename(f)]
    allg = [f for f in allg if f not in dropped]
    if dropped:
        log(f"  excluded {len(dropped)} official-language dataset(s): state policy, "
            f"not language distribution")
    contemporary = [f for f in allg if "contemporary" in os.path.basename(f)]
    traditional = [f for f in allg if "traditional" in os.path.basename(f)]
    other = [f for f in allg if f not in contemporary and f not in traditional]
    # Datasets that are neither explicitly contemporary nor traditional are contemporary and
    # are reused in both snapshots, so neither map is half empty.
    log("  today")
    st_c = build_language("c", contemporary + other, fam, med, fam_index)
    log("  before contact")
    st_t = build_language("t", traditional + other, fam, med, fam_index)

    en = {}
    ep = os.path.join(AUTO, "en_names.json")
    if os.path.exists(ep):
        en = json.load(open(ep, encoding="utf-8"))
    def fname(f):
        # Glottolog's own name where we have it (families are not in languages.csv, so this
        # mostly misses), then Wikidata's English label, then the bare glottocode. Never a
        # blank: an unnamed family reads as a rendering bug rather than a naming gap.
        return name.get(f) or en.get(f) or f
    families = [{"id": f, "name": fname(f), "idx": fam_index[f], "n": cnt[f]}
                for f in ranked[:254]]
    families.append({"id": "", "idx": 255, "n": sum(cnt[f] for f in ranked[254:]),
                     "name": f"one of {max(0, len(ranked)-254)} smaller families or isolates"})
    named = sum(1 for f in families if f["name"] != f["id"])
    log(f"  family names resolved for {named}/{len(families)}")

    meta = {"grid": [GRID_W, GRID_H], "z_lo": Z_LO, "z_hi": Z_HI,
            "families": families, "snapshots": {"c": st_c, "t": st_t}}
    json.dump(meta, open(os.path.join(MASTER, "meta.json"), "w"))
    build_language_index(fam, med, name, fam_index, en)
    log("\nmasters in data/master/ — now run build_tiles.py")


# A native label that begins with another language's word for "language" is that other
# language's NAME for it, not an autonym: Wikidata's P1705 carries "bahasa Pyu" — Indonesian
# for "the Pyu language" — for 385 of the 1,089 languages we matched, a third of the set.
# Displaying those as autonyms is exactly the substitution rule 11 exists to prevent, so they
# are rejected unless the language IS the language doing the naming (Bahasa Indonesia is the
# autonym of Indonesian). This throws away a handful of true positives to avoid many false
# ones, which is the right way round for a naming rule that exists for ethical reasons.
GENERIC_LANG_WORDS = {
    "bahasa": {"ind", "zsm", "msa", "min", "bjn", "zlm"},   # Indonesian / Malay
    "lengua": {"spa"}, "idioma": {"spa"}, "langue": {"fra"},
    "língua": {"por"}, "lingua": {"ita"}, "wikang": {"tgl"},
    "limba": {"ron"}, "jezik": {"hrv", "srp", "bos", "slv"},
}


def _is_exonym_phrase(label: str, iso: str, refname: str = "") -> bool:
    """Only reject a label that is literally "<another language's word for 'language'> +
    <our own reference name>" — "bahasa Pyu" for the language we call Pyu. Anything else is
    kept: a name a community is recorded under is worth showing, and an over-tight rule threw
    away 818 candidates to remove a few hundred descriptions."""
    parts = label.strip().split(" ")
    if len(parts) < 2:
        return False
    owners = GENERIC_LANG_WORDS.get(parts[0].lower().strip(".,"))
    if owners is None or iso in owners:
        return False
    rest = " ".join(parts[1:]).lower().strip(" .,()")
    ref = refname.lower().strip()
    return bool(ref) and (rest == ref or ref.startswith(rest) or rest.startswith(ref))


def build_language_index(fam: dict, med: dict, name: dict, fam_index: dict,
                         en: dict) -> None:
    """web/data/languages.json — the card source.

    Register D6, and CLAUDE.md rule 11: **the autonym is resolved here, in code.** Not in a
    card template, not by data entry. Glottolog's `Name` is a reference name — a unique
    English catalogue key like "Paku Karen" or "San Francisco del Mar Huave" — and shipping
    it as a language's name is what rule 11 exists to prevent. Where Wikidata gives a native
    label (P1705, CC0) we carry it, in its own script, and the card puts it first.

    Where there is none we say "no autonym recorded" and show the reference name labelled as
    a reference name. That is rule 10: unknown is a legitimate return, and a labelled
    fallback is honest where a silent one is not.
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

    desc, spk = {}, {}
    dp = os.path.join(AUTO, "descriptions.json")
    if os.path.exists(dp):
        desc = json.load(open(dp, encoding="utf-8"))
    sp2 = os.path.join(AUTO, "speakers.json")
    if os.path.exists(sp2):
        # Rule 14: a bare number is not a datum. Keep only counts that carry a YEAR, so the
        # triple (value, year, source) is complete; drop the rest rather than imply currency.
        spk = {k: v for k, v in json.load(open(sp2, encoding="utf-8")).items() if v[1]}
    auto_g, auto_i, self_g = {}, {}, {}
    ap = os.path.join(AUTO, "autonyms.json")
    if os.path.exists(ap):
        a = json.load(open(ap, encoding="utf-8"))
        auto_g, auto_i = a["by_glottocode"], a["by_iso639_3"]
    sp = os.path.join(AUTO, "selflabels.json")
    if os.path.exists(sp):
        self_g = json.load(open(sp, encoding="utf-8"))

    rows, n_auto, n_nonlatin = [], 0, 0
    rejected = [0]
    famset = set()
    with open(os.path.join(GLOTTOLOG, "languages.csv"), newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            # Register A6: filter on `category`, never on `Level` alone — Level would fold in
            # 227 sign languages and 380 bookkeeping placeholders, a 12% inflation.
            if r["Level"] != "language" or cat.get(r["ID"]) != "Spoken_L1_Language":
                continue
            if not r["Latitude"]:
                continue
            gc = r["Glottocode"]
            iso = r["ISO639P3code"] or ""
            names, scripts = [], []
            # Precedence: our own key first, the ISO alias second, the item's self-label
            # last. ISO is an alias and is treated as one (the canonical frame).
            for src in (auto_g.get(gc), auto_i.get(iso) if iso else None):
                if src:
                    for n in src["names"]:
                        if _is_exonym_phrase(n[0], iso, r["Name"]):
                            rejected[0] += 1
                            continue
                        if n not in names:
                            names.append(n)
                    for s in src["scripts"]:
                        if s not in scripts:
                            scripts.append(s)
            # ⚠ The self-label path is the loosest of the three and it leaks. Wikidata gave
            # "bahasa Pyu" tagged `id` — Indonesian for "the Pyu language", a description in
            # someone else's language, which is precisely the thing rule 11 exists to keep off
            # the card. P1705 is *declared* to be the native label; a self-label is only
            # trustworthy when its language tag IS this language, so require that.
            for n in self_g.get(gc, []):
                if n[1] and iso and n[1] != iso:
                    continue
                if n not in names:
                    names.append(n)
            if names:
                n_auto += 1
                if any(any(ord(ch) > 0x2E7F for ch in n[0]) for n in names):
                    n_nonlatin += 1
            fid = fam.get(gc, gc)
            famset.add(fid)
            rows.append([gc, r["Name"], round(float(r["Longitude"]), 3),
                         round(float(r["Latitude"]), 3), fam_index.get(fid, 255),
                         med.get(gc, -1), aes.get(gc, 0), iso,
                         int(r["First_Year_Of_Documentation"] or 0),
                         names[:4], scripts[:2], fid,
                         desc.get(gc, ""), spk.get(gc) or None,
                         (r.get("Countries") or "")[:60]])

    famnames = {f: (name.get(f) or en.get(f) or f) for f in famset}
    d = os.path.join(ROOT, "web", "data")
    os.makedirs(d, exist_ok=True)
    json.dump({"fields": ["code", "name", "lon", "lat", "fam", "med", "aes", "iso", "first",
                          "autonyms", "scripts", "famid"],
               "familyNames": famnames, "rows": rows},
              open(os.path.join(d, "languages.json"), "w"), ensure_ascii=False,
              separators=(",", ":"))
    log(f"  languages.json: {len(rows):,} rows, {os.path.getsize(os.path.join(d, 'languages.json'))/1e6:.2f} MB")
    log(f"  AUTONYMS (D6): {n_auto:,} of {len(rows):,} languages "
        f"({n_auto/max(len(rows),1)*100:.1f}%), of which {n_nonlatin:,} are in a non-Latin script")
    log(f"    descriptions {sum(1 for r in rows if r[12]):,} · "
        f"speaker triples {sum(1 for r in rows if r[13]):,}")
    log(f"    {rejected[0]:,} candidate labels rejected as another language's phrase "
        f"(\"bahasa X\" and kin) rather than an autonym")


if __name__ == "__main__":
    main()
