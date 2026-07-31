#!/usr/bin/env python3
"""encoding.py — measure the vertical encoding BEFORE choosing it.

Register: B3, which gates B1 (the lit-terrain substrate).

The question
------------
Mother Tongues' claim is that linguistic diversity *visibly follows the terrain*. The
shimmer is read against **lit relief**, and relief is the gradient of the elevation
field — so the encoding has to resolve elevation *differences between neighbouring cells
on inhabited land*. That is a different requirement from the one the house's reference
project solved: it encodes signed-sqrt over +/-8000 m to put precision at **sea level**,
because a migrating coastline was its product. Inheriting that encoding here would be
inheriting a tuning for someone else's contour.

WORKING-RULES §4: measure before tuning. TRAPS §B1: quantisation does not read as a
slightly rough field, it reads as **flat terraces**, and anything periodic keyed to it
draws the terrace contours. The reference project measured 75% of adjacent abyssal cells
encoding identically and spent several rounds tuning the texture that was drawing it.

So the decisive metric here is the same one: **the fraction of adjacent land cell pairs
that collapse to the same encoded level.** If that is high in the New Guinea highlands,
the shimmer is drawn on terraces and the project's central claim is compromised.

Data: ETOPO1 ice-surface, 1 arc-minute, raw int16 — chosen because it reads with numpy
alone (no GDAL/rasterio in this environment) and because the *distribution* of land
relief is what is being measured, for which 1 arc-minute is ample. The shipped substrate
will use a current DEM; this measurement decides its encoding, not its source.

Run:  python3 encoding.py
"""
from __future__ import annotations

import math
import os
from dataclasses import dataclass
from typing import Callable, Optional

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DEM = os.path.join(HERE, "..", "..", "data", "dem", "etopo1_ice_g_i2.bin")
NCOLS, NROWS = 21601, 10801
CELL_DEG = 1.0 / 60.0
R_EARTH = 6371008.8  # m

# Regions named in SCOPE §3's visual sentence — the measurement targets the claim.
REGIONS = {
    "New Guinea highlands": (137.0, 147.0, -7.0, -3.0),
    "Caucasus":             (40.0, 48.0, 41.0, 44.0),
    "North China Plain":    (114.0, 119.0, 33.0, 38.0),
    "Vanuatu":              (166.0, 170.0, -20.0, -13.0),
}


# ---------------------------------------------------------------------------
# Candidate encodings. Each maps metres -> [0,1]; we then quantise to N levels.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Encoding:
    name: str
    bits: int
    to_unit: Callable[[np.ndarray], np.ndarray]
    note: str

    @property
    def levels(self) -> int:
        return (1 << self.bits) - 1

    def quantise(self, z: np.ndarray) -> np.ndarray:
        u = np.clip(self.to_unit(z.astype(np.float64)), 0.0, 1.0)
        return np.rint(u * self.levels).astype(np.int32)


def _signed_sqrt(z, zmax=8000.0):
    return 0.5 + 0.5 * np.sign(z) * np.sqrt(np.minimum(np.abs(z), zmax) / zmax)


def _linear(z, lo, hi):
    return (np.clip(z, lo, hi) - lo) / (hi - lo)


ENCODINGS = [
    Encoding("A  inherited signed-sqrt +/-8000, 8-bit", 8,
             lambda z: _signed_sqrt(z),
             "the reference project's encoding: precision at SEA LEVEL"),
    Encoding("B  linear 0..6000, 8-bit", 8,
             lambda z: _linear(z, 0.0, 6000.0),
             "naive land-only linear"),
    Encoding("C  linear -500..+6000, 8-bit", 8,
             lambda z: _linear(z, -500.0, 6000.0),
             "land channel with a little headroom below sea level"),
    Encoding("D  linear -500..+3000, 8-bit (clip high)", 8,
             lambda z: _linear(z, -500.0, 3000.0),
             "concentrate on inhabited elevations, clip the high peaks"),
    Encoding("E  linear -11000..+9000, 16-bit", 16,
             lambda z: _linear(z, -11000.0, 9000.0),
             "pay for precision ONCE: terrain is static in this project"),
    Encoding("F  linear -500..+6000, 16-bit", 16,
             lambda z: _linear(z, -500.0, 6000.0),
             "land channel at 16-bit"),
]


# ---------------------------------------------------------------------------
# Loading and slicing
# ---------------------------------------------------------------------------

def load_dem(path: str = DEM) -> np.ndarray:
    """ETOPO1 as (NROWS, NCOLS) int16. Row 0 is +90 (north), col 0 is -180."""
    a = np.fromfile(path, dtype="<i2")
    if a.size != NCOLS * NROWS:
        raise ValueError(f"unexpected size {a.size}, expected {NCOLS*NROWS}")
    return a.reshape(NROWS, NCOLS)


def row_of(lat: float) -> int:
    return int(round((90.0 - lat) / CELL_DEG))


def col_of(lon: float) -> int:
    return int(round((lon + 180.0) / CELL_DEG))


def window(z: np.ndarray, lon0: float, lon1: float, lat0: float, lat1: float) -> np.ndarray:
    r0, r1 = row_of(lat1), row_of(lat0)          # lat1 is the NORTH edge -> smaller row
    c0, c1 = col_of(lon0), col_of(lon1)
    return z[r0:r1 + 1, c0:c1 + 1]


# ---------------------------------------------------------------------------
# The metrics
# ---------------------------------------------------------------------------

def true_slope_deg(zw: np.ndarray, lat_mid: float) -> np.ndarray:
    """Local slope in degrees from east-west and north-south neighbour differences."""
    dy_m = CELL_DEG * math.pi / 180.0 * R_EARTH
    dx_m = dy_m * max(math.cos(math.radians(lat_mid)), 1e-6)
    zf = zw.astype(np.float64)
    gx = (zf[:, 2:] - zf[:, :-2]) / (2.0 * dx_m)
    gy = (zf[2:, :] - zf[:-2, :]) / (2.0 * dy_m)
    g = np.hypot(gx[1:-1, :], gy[:, 1:-1])
    return np.degrees(np.arctan(g))


def terrace_fraction(zw: np.ndarray, enc: Encoding, land_only: bool = True) -> float:
    """Fraction of horizontally adjacent LAND pairs that encode to the same level.

    This is the number the reference project measured at 75% over the abyss and spent
    rounds of texture tuning against. Anything above a few per cent on inhabited land
    means the relief is being drawn as steps.
    """
    q = enc.quantise(zw)
    same = q[:, 1:] == q[:, :-1]
    if land_only:
        m = (zw[:, 1:] > 0) & (zw[:, :-1] > 0)
        if not m.any():
            return float("nan")
        return float(same[m].mean())
    return float(same.mean())


def quantum_m(enc: Encoding, z0: float) -> float:
    """Metres per encoded level at elevation z0 — the local vertical resolution."""
    z = np.array([z0 - 0.5, z0 + 0.5], dtype=np.float64)
    u = enc.to_unit(z)
    du = abs(float(u[1] - u[0]))
    if du <= 0:
        return float("inf")
    return 1.0 / (du * enc.levels)


def apparent_step_slope_deg(enc: Encoding, z0: float, lat: float) -> float:
    """Slope of the artificial step the quantum creates across ONE cell.

    If this exceeds the terrain's true slope, the encoding invents relief.
    """
    dy_m = CELL_DEG * math.pi / 180.0 * R_EARTH
    dx_m = dy_m * max(math.cos(math.radians(lat)), 1e-6)
    return math.degrees(math.atan(quantum_m(enc, z0) / dx_m))


# ---------------------------------------------------------------------------
# Selftest
# ---------------------------------------------------------------------------

def _selftest() -> None:
    # --- encodings are monotone and bounded, with no data -----------------
    zs = np.linspace(-11000, 9000, 4001)
    for e in ENCODINGS:
        u = np.clip(e.to_unit(zs), 0, 1)
        assert np.all(np.diff(u) >= -1e-12), f"{e.name} is not monotone"
        assert 0.0 <= u.min() and u.max() <= 1.0
    # signed-sqrt must put MORE precision at sea level than a land-linear encoding
    a = next(e for e in ENCODINGS if e.name.startswith("A"))
    c = next(e for e in ENCODINGS if e.name.startswith("C"))
    assert quantum_m(a, 5.0) < quantum_m(c, 5.0), "signed-sqrt should be finer at sea level"
    # ...and CORRESPONDINGLY COARSER up where the highlands are. This is the whole point.
    assert quantum_m(a, 2000.0) > quantum_m(c, 2000.0), (
        "signed-sqrt should be coarser than a land-linear encoding at highland elevations")
    # 16-bit must be ~256x finer than the same 8-bit range
    c16 = next(e for e in ENCODINGS if e.name.startswith("F"))
    r = quantum_m(c, 2000.0) / quantum_m(c16, 2000.0)
    assert 200 < r < 300, r

    if not os.path.exists(DEM):
        print("encoding.py selftest: encoding maths OK; DEM absent, skipping geography")
        return

    z = load_dem()
    # --- geography sanity: a test satisfied by the wrong hemisphere is a real
    #     prior-project bug, so pin actual places. ---------------------------
    def at(lat, lon):
        return int(z[row_of(lat), col_of(lon)])
    everest = z[row_of(27.99) - 2:row_of(27.99) + 3, col_of(86.93) - 2:col_of(86.93) + 3].max()
    assert everest > 7500, f"Everest region max {everest} — grid orientation is wrong"
    dead = z[row_of(31.5) - 2:row_of(31.5) + 3, col_of(35.5) - 2:col_of(35.5) + 3].min()
    assert dead < -300, f"Dead Sea region min {dead} — grid orientation is wrong"
    assert at(0.0, -30.0) < -1000, "mid-Atlantic should be deep ocean"
    assert at(-75.0, 0.0) > 1000, "East Antarctic ice surface should be high"

    print("encoding.py selftest: OK")


# ---------------------------------------------------------------------------

def report() -> None:
    z = load_dem()
    land = z > 0

    print("=" * 78)
    print("B3 — vertical encoding measurement (ETOPO1 ice-surface, 1 arc-minute)")
    print("=" * 78)
    print(f"global land cells: {int(land.sum()):,} ({land.mean()*100:.1f}% of the grid)")
    zl = z[land].astype(np.float64)
    ps = [50, 75, 90, 95, 99]
    print("land elevation percentiles (m): " +
          "  ".join(f"p{p}={np.percentile(zl, p):.0f}" for p in ps))
    print()

    # --- per-region truth --------------------------------------------------
    print("--- the regions SCOPE §3's visual sentence names " + "-" * 25)
    stats = {}
    for name, (lo0, lo1, la0, la1) in REGIONS.items():
        zw = window(z, lo0, lo1, la0, la1)
        lat_mid = (la0 + la1) / 2
        m = zw > 0
        if not m.any():
            continue
        zz = zw[m].astype(np.float64)
        sl = true_slope_deg(zw, lat_mid)
        slm = sl[(zw[1:-1, 1:-1] > 0)]
        stats[name] = dict(zw=zw, lat=lat_mid, med=float(np.median(zz)),
                           p90=float(np.percentile(zz, 90)),
                           slope_med=float(np.median(slm)) if slm.size else float("nan"),
                           slope_p90=float(np.percentile(slm, 90)) if slm.size else float("nan"))
        s = stats[name]
        print(f"{name:22s} land median {s['med']:6.0f} m   p90 {s['p90']:6.0f} m   "
              f"true slope median {s['slope_med']:5.2f}°  p90 {s['slope_p90']:5.2f}°")
    print()

    # --- the decisive table -----------------------------------------------
    print("--- terrace fraction: adjacent LAND pairs collapsing to one level " + "-" * 11)
    print(f"{'encoding':44s}" + "".join(f"{n.split()[0][:9]:>10s}" for n in REGIONS))
    for e in ENCODINGS:
        row = f"{e.name:44s}"
        for name in REGIONS:
            if name not in stats:
                row += f"{'-':>10s}"; continue
            tf = terrace_fraction(stats[name]["zw"], e)
            row += f"{tf*100:9.1f}%"
        print(row)

    # The floor. ETOPO1 is int16 METRES, so the source itself is quantised at 1 m and
    # some adjacent land cells are genuinely equal. An encoding cannot beat this, and
    # once it reaches it, the encoding has stopped being the binding constraint.
    row = f"{'--- SOURCE FLOOR (raw int16 DEM, 1 m quantum)':44s}"
    for name in REGIONS:
        if name not in stats:
            row += f"{'-':>10s}"; continue
        zw = stats[name]["zw"]
        m = (zw[:, 1:] > 0) & (zw[:, :-1] > 0)
        same = (zw[:, 1:] == zw[:, :-1])
        row += f"{(same[m].mean() if m.any() else float('nan'))*100:9.1f}%"
    print(row)
    print()

    print("--- vertical quantum, and the slope the STEP itself creates " + "-" * 17)
    print(f"{'encoding':44s}{'q@2000m':>10s}{'step slope':>12s}{'vs true':>10s}")
    ng = stats.get("New Guinea highlands")
    for e in ENCODINGS:
        q = quantum_m(e, 2000.0)
        ss = apparent_step_slope_deg(e, 2000.0, ng["lat"]) if ng else float("nan")
        ratio = ss / ng["slope_med"] if ng and ng["slope_med"] > 0 else float("nan")
        print(f"{e.name:44s}{q:9.1f}m{ss:11.2f}°{ratio:9.1f}x")
    print()

    # --- the bytes argument -----------------------------------------------
    print("--- what precision costs HERE, where terrain is static " + "-" * 22)
    for res, label in ((4096 * 2048, "4096x2048 global"), (10800 * 5400, "10800x5400 (~2 km)")):
        print(f"  {label:22s} 8-bit {res/1e6:6.1f} MB raw   16-bit {2*res/1e6:6.1f} MB raw")
    print("  Terrain does not change between this project's two snapshots (SCOPE §12 D1),")
    print("  so 16-bit is paid ONCE on a static base — not per keyframe. The reference")
    print("  project's 320 MB-vs-23 MB finding was measured across 251 CHANGING keyframes")
    print("  and does not transfer.")


if __name__ == "__main__":
    _selftest()
    print()
    report()
