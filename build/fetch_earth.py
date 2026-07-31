#!/usr/bin/env python3
"""fetch_earth.py — the measured Earth-surface fields. Registers C3, B5, and the fidelity ask.

WHY NOT WORLDCLIM. The obvious climate source for a growing-season variable is WorldClim, and
it is **NonCommercial** — SCOPE §12 D3 excludes it. CHELSA's licence could not be confirmed at
source. NASA's Earth Observations archive is **public domain**, needs no login, and carries the
variables this project actually argues about, so it is the source of record here.

WHAT EACH FIELD IS FOR — every one has a job, none is decoration:

  MOD_LSTD_CLIM_M    12-month land-surface-temperature climatology.
                     -> GROWING SEASON, the variable SCOPE §1's amended claim is about. Round 1
                        measured against ruggedness and latitude; latitude was standing in for
                        this. C3 exists because a proxy for a variable is not the variable.
  MOD_NDVI_M         12 monthly MOD13C2 NDVI granules (2024).
                     ⚠ NOT AVHRR_CLIM_M. That dataset's name suggests a vegetation
                     climatology and it is **sea surface temperature** — values -2..32, NaN
                     over every land pixel. It was wired in as greenness and the whole land
                     surface saturated. `build_surface` now asserts the NDVI source lies in
                     [-1,1], so a wrong dataset fails the build instead of colouring it.
                     -> GREENNESS, continuous. The map currently paints 15 flat biome classes,
                        which is a choropleth wearing a basemap. Real vegetation density varies
                        per pixel and so should the ground.
  MOD17A3H_Y_NPP     annual net primary productivity.
                     -> "HOW MANY PEOPLE A LANDSCAPE CAN FEED YEAR-ROUND" — the claim's own
                        words. NPP is the closest measured quantity to it that exists.
  MOD10C1_M_SNOW     monthly snow cover.
                     -> A SNOWLINE THAT IS MEASURED rather than a height threshold I invented.
  MCD43C3_M_BSA      black-sky albedo.
                     -> How bright the ground actually is. Deserts are not one tan.

All are NASA public domain. Grids are plate carrée, row 0 = +90, so they need no reprojection —
the one coordinate-frame risk in this project is absent for this whole family of sources.

Run: python3 fetch_earth.py
"""
from __future__ import annotations

import os
import ssl
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "data", "earth")
BASE = "https://neo.gsfc.nasa.gov/archive/geotiff.float"
UA = "MotherTongues/1.0 (research atlas; augustgweon@gmail.com)"

MONTHS = [f"{m:02d}" for m in range(1, 13)]
NDVI_GRANULES = ['MOD13C2.A2024001.061.2024038052740.tif', 'MOD13C2.A2024032.061.2024066075101.tif', 'MOD13C2.A2024061.061.2024099222643.tif', 'MOD13C2.A2024092.061.2024133223503.tif', 'MOD13C2.A2024122.061.2024162181836.tif', 'MOD13C2.A2024153.061.2024198104950.tif', 'MOD13C2.A2024183.061.2024228034735.tif', 'MOD13C2.A2024214.061.2024267164812.tif', 'MOD13C2.A2024245.061.2024291123221.tif', 'MOD13C2.A2024275.061.2024337120446.tif', 'MOD13C2.A2024306.061.2024338122222.tif', 'MOD13C2.A2024336.061.2025007011400.tif']
WANT: list[tuple[str, str]] = []
for i, m in enumerate(MONTHS):
    WANT.append((f"MOD_NDVI_M/{NDVI_GRANULES[i]}", f"ndvi_{m}.tif"))
    WANT.append((f"MOD_LSTD_CLIM_M/MOD_LSTD_CLIM_M_2001-{m}.FLOAT.TIFF", f"lst_{m}.tif"))

    WANT.append((f"MOD10C1_M_SNOW/MOD10C1_2020{m}_month.tif", f"snow_{m}.tif"))


def get(rel: str, dest: str, tries: int = 3) -> bool:
    p = os.path.join(OUT, dest)
    if os.path.exists(p) and os.path.getsize(p) > 4096:
        return True
    url = f"{BASE}/{rel}"
    ctx = ssl.create_default_context()
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=240, context=ctx) as r, \
                    open(p + ".part", "wb") as f:
                while True:
                    c = r.read(1 << 20)
                    if not c:
                        break
                    f.write(c)
            os.replace(p + ".part", p)
            return True
        except Exception as e:                     # noqa: BLE001
            if i == tries - 1:
                print(f"   MISS {dest}: {type(e).__name__} {e}")
            time.sleep(3 * (i + 1))
    return False


def discover_latest(ds: str, pat: str) -> str | None:
    """Datasets with dated granules: take the most recent file rather than guessing a date."""
    try:
        req = urllib.request.Request(f"{BASE}/{ds}/", headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=120,
                                    context=ssl.create_default_context()) as r:
            html = r.read().decode("utf8", "replace")
    except Exception as e:                         # noqa: BLE001
        print(f"   cannot list {ds}: {e}")
        return None
    import re
    hits = sorted(set(re.findall(r'href="(' + pat + r')"', html)))
    return hits[-1] if hits else None


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    print("NASA Earth Observations — public domain, no login\n")

    ok = 0
    for rel, dest in WANT:
        if get(rel, dest):
            ok += 1
        sys.stdout.write(f"\r   monthly fields: {ok}/{len(WANT)}")
        sys.stdout.flush()
    print()

    for ds, pat, dest in (("MOD17A3H_Y_NPP", r"MOD17A3H_Y_NPP_[0-9-]+\.FLOAT\.TIFF", "npp.tif"),
                          ("MCD43C3_M_BSA", r"MCD43C3_M_BSA_[0-9-]+\.FLOAT\.TIFF", "albedo.tif")):
        if os.path.exists(os.path.join(OUT, dest)):
            print(f"   have {dest}")
            continue
        f = discover_latest(ds, pat)
        if f and get(f"{ds}/{f}", dest):
            print(f"   {dest} <- {f}")

    have = sorted(f for f in os.listdir(OUT) if f.endswith(".tif"))
    mb = sum(os.path.getsize(os.path.join(OUT, f)) for f in have) / 1e6
    print(f"\n{len(have)} rasters, {mb:.0f} MB in data/earth/")
