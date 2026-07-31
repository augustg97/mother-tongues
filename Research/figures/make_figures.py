#!/usr/bin/env python3
"""make_figures.py — authored figures, generated FROM the models.

House rule: figures are generated, not drawn, so a corrected number propagates
automatically and the figure cannot drift from the table it illustrates.

Writes into Research/figures/authored/. stdlib + numpy + PIL.
"""
from __future__ import annotations

import importlib.util
import sys
import math
import os

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "authored")
MOD = os.path.join(HERE, "..", "modeling")

BG = (14, 18, 17)
FG = (231, 236, 234)
DIM = (128, 140, 136)
ACCENT = (76, 181, 165)
WARN = (217, 130, 95)


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, os.path.join(MOD, f"{name}.py"))
    m = importlib.util.module_from_spec(spec)
    # Register before exec: dataclasses resolve annotations via sys.modules[__module__],
    # and a module loaded by path alone is not there yet.
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def _panel(d: ImageDraw.ImageDraw, x0, y0, w, h, xs, ys, xlabel, ylabel, title,
           colour, rho):
    d.rectangle([x0, y0, x0 + w, y0 + h], outline=(44, 52, 50))
    if len(xs) == 0:
        return
    # log10 the density axis: it spans orders of magnitude
    ys = np.log10(np.maximum(ys, 1e-3))
    xlo, xhi = float(np.percentile(xs, 0.5)), float(np.percentile(xs, 99.5))
    ylo, yhi = float(ys.min()), float(ys.max())
    if xhi <= xlo or yhi <= ylo:
        return
    for xv, yv in zip(xs, ys):
        px = x0 + (xv - xlo) / (xhi - xlo) * w
        py = y0 + h - (yv - ylo) / (yhi - ylo) * h
        if x0 <= px <= x0 + w and y0 <= py <= y0 + h:
            d.point((px, py), fill=colour)
    d.text((x0 + 6, y0 + 6), title, fill=FG)
    d.text((x0 + 6, y0 + 20), f"Spearman {rho:+.3f}", fill=colour)
    d.text((x0 + 6, y0 + h + 6), xlabel, fill=DIM)
    d.text((x0 + 6, y0 - 14), ylabel, fill=DIM)


def figure_diversity() -> str:
    div = _load("diversity")
    r = div.measure(verbose=False)
    rows = r["rows"]
    # The scatter plots OCCUPIED cells only. 4,471 of 6,143 land cells hold no recorded
    # language, and on a log axis they all collapse onto one line that hides the
    # relationship. That zero-inflation is a real fact and it is why a count model is
    # needed (register C6) — but it belongs in the caption, not smeared across the axis.
    occ = [x for x in rows if x["n"] > 0]
    nzero = len(rows) - len(occ)
    rug = np.array([x["rugged"] for x in occ])
    alat = np.array([x["abslat"] for x in occ])
    dens = np.array([x["density"] for x in occ])

    W, H = 1000, 470
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.text((24, 18), "Does linguistic richness follow the terrain?", fill=FG)
    d.text((24, 34), f"{len(occ):,} occupied land cells at {div.CELL:.0f}deg  "
                     f"({nzero:,} empty cells omitted from the scatter)  ·  "
                     f"7,672 spoken-L1 languages  ·  Glottolog 5.3 + ETOPO1", fill=DIM)

    pw, ph = 430, 300
    _panel(d, 40, 96, pw, ph, rug, dens,
           "terrain ruggedness  (elevation SD, m)", "log10 languages per Mkm2",
           "terrain", ACCENT, r["spearman_raw"])
    _panel(d, 520, 96, pw, ph, alat, dens,
           "|latitude|  (degrees)", "log10 languages per Mkm2",
           "latitude  (climate proxy)", WARN, r["spearman_abslat_density"])

    d.text((40, 436), "Latitude beats terrain by about 4x, and the correlations above are "
                      "computed on ALL land cells, not just these.", fill=FG)
    d.text((40, 450), "The claim that terrain is 'most of the explanation' is not supported.", fill=FG)
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, "fig-01-richness-vs-terrain.png")
    img.save(p)
    return p


def figure_encoding() -> str:
    enc = _load("encoding")
    if not os.path.exists(enc.DEM):
        return ""
    z = enc.load_dem()
    zw = enc.window(z, *enc.REGIONS["New Guinea highlands"])
    names, tf = [], []
    for e in enc.ENCODINGS:
        names.append(e.name.split("  ")[0] + " " + ("16-bit" if e.bits == 16 else "8-bit"))
        tf.append(enc.terrace_fraction(zw, e) * 100)
    m = (zw[:, 1:] > 0) & (zw[:, :-1] > 0)
    floor = float((zw[:, 1:] == zw[:, :-1])[m].mean() * 100)

    W, H = 1000, 400
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.text((24, 18), "Encoding measured before it was chosen  (New Guinea highlands)", fill=FG)
    d.text((24, 34), "terracing: adjacent land cells collapsing to one encoded level "
                     "- lower is better", fill=DIM)
    x0, y0, bw, gap = 60, 90, 90, 40
    scale = 240.0 / max(max(tf), floor, 1.0)
    for i, (n, v) in enumerate(zip(names, tf)):
        x = x0 + i * (bw + gap)
        hgt = v * scale
        col = ACCENT if v <= floor * 1.02 else WARN
        d.rectangle([x, y0 + 240 - hgt, x + bw, y0 + 240], fill=col)
        d.text((x, y0 + 246), n, fill=DIM)
        d.text((x, y0 + 226 - hgt), f"{v:.1f}%", fill=FG)
    fy = y0 + 240 - floor * scale
    d.line([x0 - 12, fy, W - 30, fy], fill=FG)
    # Caption goes ABOVE the line and hard right, clear of the bars and their value
    # labels — the first version collided with the last bar's "4.0%".
    # Caption sits in the empty region above the two short 16-bit bars and right of the
    # tall 8-bit ones. Two earlier placements collided with the F bar's value label.
    cx, cy = x0 + 4 * (bw + gap) - 30, y0 + 150
    d.text((cx, cy), f"source floor {floor:.1f}%", fill=FG)
    d.text((cx, cy + 13), "the DEM's own 1 m quantum", fill=DIM)
    d.line([cx + 8, cy + 30, cx + 8, fy - 2], fill=(90, 100, 98))
    d.text((40, 360), "The 16-bit encodings reach the source floor exactly: at that point the "
                      "encoding contributes nothing.", fill=FG)
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, "fig-02-encoding-terracing.png")
    img.save(p)
    return p


if __name__ == "__main__":
    for f in (figure_diversity, figure_encoding):
        p = f()
        print("wrote", os.path.relpath(p, HERE) if p else "(skipped, data absent)")
