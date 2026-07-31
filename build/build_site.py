#!/usr/bin/env python3
"""build_site.py — the ONLY route to publication.

1. run the research selftests and REFUSE TO PUBLISH on any failure;
2. verify the field rasters exist and are registered to the real Earth;
3. stamp the data version BEFORE the app file is copied;
4. copy web/ -> docs/, which GitHub Pages serves from main:/docs.

Step 3's ordering is not cosmetic. A static host serves an asset with a cache lifetime and
an ETag, so a returning viewer can sit on a cached copy well past it: the app runs
perfectly and shows yesterday's data (TRAPS §D2). This already bit us in local development
— a cached app.js kept a fixed 320x240 canvas alive across three rebuilds.

Relative paths throughout, so the project directory can move. It will.

Run:  python3 build_site.py
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
WEB = os.path.join(ROOT, "web")
DOCS = os.path.join(ROOT, "docs")
MODELING = os.path.join(ROOT, "Research", "modeling")

REQUIRED_FIELDS = ["terrain.png", "env.png", "lang_c.png", "lang_t.png", "fields.json"]
BUDGET_MB = 30.0


def die(msg: str) -> None:
    print(f"\nREFUSING TO PUBLISH: {msg}")
    sys.exit(1)


def gate_selftests() -> None:
    print("1. research selftests")
    p = subprocess.run([sys.executable, os.path.join(MODELING, "audit_all.py")],
                       capture_output=True, text=True)
    print("   " + "\n   ".join(p.stdout.strip().splitlines()[-6:]))
    if p.returncode != 0:
        print(p.stderr[-1500:])
        die("a research selftest failed")


def gate_fields() -> None:
    print("2. field rasters")
    fd = os.path.join(WEB, "fields")
    missing = [f for f in REQUIRED_FIELDS if not os.path.exists(os.path.join(fd, f))]
    if missing:
        die(f"missing field files: {missing} — run build_fields.py")
    total = 0.0
    for r, _, fs in os.walk(WEB):
        for f in fs:
            total += os.path.getsize(os.path.join(r, f))
    total /= 1e6
    print(f"   {len(REQUIRED_FIELDS)} fields present · web/ total {total:.1f} MB "
          f"(budget {BUDGET_MB:.0f} MB)")
    if total > BUDGET_MB:
        die(f"web/ is {total:.1f} MB, over the {BUDGET_MB:.0f} MB budget in SCOPE §11")


def gate_registration() -> None:
    """Re-check the shipped raster, not the pipeline's memory of it (TRAPS §D5)."""
    print("3. registration, read back from the shipped PNG")
    try:
        import numpy as np
        from PIL import Image
    except Exception as e:
        die(f"cannot verify the shipped raster: {e}")
    a = np.asarray(Image.open(os.path.join(WEB, "fields", "terrain.png")).convert("RGBA"))
    h, w = a.shape[:2]
    z = ((a[:, :, 0].astype(np.int32) * 256 + a[:, :, 1]) / 65535.0) * 20000.0 - 11000.0

    def at(la, lo):
        return float(z[min(h - 1, int((90 - la) / 180 * h)),
                       min(w - 1, int((lo + 180) / 360 * w))])
    cases = [("Everest", 27.99, 86.93, 4000, None), ("Dead Sea", 31.5, 35.5, None, 0),
             ("North China Plain", 35.5, 116.5, 0, 300), ("Gabon", -0.5, 12.5, 0, 900),
             ("mid-Atlantic", 0.0, -30.0, None, -2000),
             ("East Antarctica", -75.0, 0.0, 1500, None)]
    bad = [f"{n}={at(la, lo):.0f}m" for n, la, lo, lob, hib in cases
           if (lob is not None and at(la, lo) < lob) or (hib is not None and at(la, lo) > hib)]
    if bad:
        die("the SHIPPED raster is not registered to the real Earth: " + "; ".join(bad))
    print(f"   {len(cases)}/{len(cases)} named places in range "
          f"(Everest {at(27.99,86.93):.0f} m, Dead Sea {at(31.5,35.5):.0f} m)")


def stamp() -> str:
    """Bump the data version in web/index.html BEFORE anything is copied."""
    print("4. data-version stamp")
    v = str(int(time.time()))
    p = os.path.join(WEB, "index.html")
    s = open(p, encoding="utf-8").read()
    if 'name="data-version"' not in s:
        die("web/index.html has no data-version meta tag")
    s = re.sub(r'(name="data-version" content=")\d+(")', rf"\g<1>{v}\g<2>", s)
    s = re.sub(r"\?v=\d+", f"?v={v}", s)
    open(p, "w", encoding="utf-8").write(s)
    print(f"   stamped {v}")
    return v


def publish(v: str) -> None:
    print("5. web/ -> docs/")
    if os.path.exists(DOCS):
        shutil.rmtree(DOCS)
    shutil.copytree(WEB, DOCS)
    open(os.path.join(DOCS, ".nojekyll"), "w").close()
    n = sum(len(fs) for _, _, fs in os.walk(DOCS))
    got = open(os.path.join(DOCS, "index.html"), encoding="utf-8").read()
    if v not in got:
        die("the copied index.html does not carry the stamp — copy order is wrong")
    print(f"   {n} files, stamp {v} present in docs/index.html")
    print(f"\nPublished locally. After pushing, verify the LIVE stamp:")
    print(f'   curl -s https://augustg97.github.io/mother-tongues/ | grep data-version')
    print(f"   expect: {v}")


if __name__ == "__main__":
    print("build_site.py — the only route to publication\n")
    gate_selftests()
    gate_fields()
    gate_registration()
    publish(stamp())
