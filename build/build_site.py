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
    print(f"   {len(REQUIRED_FIELDS)} fields present")
    # The SIZE check lives in publish(), not here: later gates WRITE files into web/, so
    # measuring the budget at this point would check a directory that does not exist yet.


def _web_size_mb() -> float:
    return sum(os.path.getsize(os.path.join(r, f))
               for r, _, fs in os.walk(WEB) for f in fs) / 1e6


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


def gate_attribution() -> None:
    """A5. The shipped ledger must BE the module's output, byte for byte.

    A hand-written sources list in an About panel is not an attribution ledger: it drifts from
    the ingest the first time a source is added, and nobody notices, because nothing checks it.
    So the module is the authority and this regenerates the shipped file from it. If they ever
    differ, that difference is the bug — publish the regenerated one and fail loudly.
    """
    print("3b. attribution ledger")
    sys.path.insert(0, MODELING)
    import attribution
    attribution._selftest()
    want = attribution.to_json()
    p = os.path.join(WEB, "data", "attribution.json")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    got = open(p, encoding="utf-8").read() if os.path.exists(p) else None
    if got != want:
        open(p, "w", encoding="utf-8").write(want)
        if got is not None:
            die("web/data/attribution.json had drifted from attribution.py. It has been "
                "REGENERATED — inspect the diff, then re-run. (A stale ledger means the app "
                "was crediting sources it no longer uses, or failing to credit ones it does.)")
        print("   generated web/data/attribution.json")
    sa = attribution.share_alike_ingested()
    print(f"   {len(attribution.ingested())} sources ingested, all licence-verified · "
          f"{len(sa)} ShareAlike{' — our emitted data inherits SA' if sa else ''}")


def gate_coverage() -> None:
    """B4/D8. Recompute coverage from the SHIPPED rasters every build, so the number in the
    About panel is a measurement of the artefact rather than a remembered figure."""
    print("3c. coverage, measured from the shipped rasters")
    p = subprocess.run([sys.executable, os.path.join(MODELING, "coverage.py")],
                       capture_output=True, text=True)
    if p.returncode != 0:
        print(p.stdout[-1200:]); print(p.stderr[-1200:])
        die("coverage.py failed against the shipped rasters")
    for ln in p.stdout.strip().splitlines():
        if ln.startswith(("land", "today", "before")):
            print("   " + ln)


def gate_no_year_on_before_contact() -> None:
    """A4, enforced rather than trusted.

    Rule 15: the earlier snapshot is a per-region STATE, not a year. Contact runs from the
    1490s to the twentieth century and never happened in some places, so printing one year on
    that snapshot would be the frame error of the project. `frames.snapshot_label` refuses it
    in Python — but the app's labels are authored in HTML and JS, where nothing was checking.
    This greps the shipped surfaces for a four-digit year near the snapshot control.
    """
    print("3d. no year on the before-contact snapshot")
    import re as _re
    bad = []
    for f in ("index.html", os.path.join("js", "app.js")):
        s = open(os.path.join(WEB, f), encoding="utf-8").read()
        for m in _re.finditer(r"before[ _]?contact", s, _re.I):
            window = s[max(0, m.start() - 90):m.end() + 90]
            for y in _re.finditer(r"\b1[4-9]\d\d\b|\b20[0-2]\d\b", window):
                # A century range in prose ("the 1490s to the twentieth century") is the
                # honest statement, not the error; a bare year label is the error.
                if "s to the" not in window and "ranges from" not in window:
                    bad.append(f"{f}: '{y.group()}' next to '{m.group()}'")
    if bad:
        die("a year is rendered on the before-contact snapshot (rule 15): " + "; ".join(bad))
    print("   clean — the earlier snapshot is labelled as a state, not a date")


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
    total = _web_size_mb()
    print(f"   web/ total {total:.1f} MB (budget {BUDGET_MB:.0f} MB)")
    if total > BUDGET_MB:
        die(f"web/ is {total:.1f} MB, over the {BUDGET_MB:.0f} MB budget in SCOPE §11")
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
    gate_attribution()
    gate_coverage()
    gate_no_year_on_before_contact()
    publish(stamp())
