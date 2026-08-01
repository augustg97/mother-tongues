#!/usr/bin/env python3
"""spatial.py — register C10: how much of our confidence was an artefact of geography?

THE PROBLEM WE ADMITTED. Every statistic this project has published treats a 2 degree cell as
an independent observation. They are not. Adjacent cells share climate, share terrain, and
share languages, so the effective sample is far smaller than 4,600 and every interval quoted
so far is too narrow. Worse, the bias is not uniform: **absolute latitude is smooth across the
whole planet**, so it benefits most from the pretence of independence — and latitude is
exactly the variable that has been outcompeting growing season in our numbers.

WHAT THIS DOES, in increasing order of how much it costs to believe:

  1. **Moran's I** on richness and on the model residuals — a number for how much spatial
     structure is there at all. If the residuals are uncorrelated, the worry was misplaced.
  2. **A spatial block bootstrap.** Resample 10x10 degree BLOCKS of cells with replacement,
     refit, and take the spread of the coefficient across resamples. Blocks keep neighbours
     together, so the resampling respects the dependence instead of destroying it. The ratio
     of this interval to the model-based one is the honest inflation factor.
  3. **Distance thinning.** Refit on subsets whose cells are at least k cells apart. If a
     coefficient survives thinning, it is not an artefact of oversampling one region.

stdlib + numpy. Run: python3 spatial.py
"""
from __future__ import annotations

import math
import os

import numpy as np

import climate as C
import diversity as D


def build_rows() -> dict:
    """The same table climate.py fits, but keyed so neighbours can be found."""
    langs = D.load_spoken_l1()
    z = D.load_dem()
    terr = D.terrain_per_cell(z)
    gsl_grid, ndvi_grid = C.growing_season()
    gsl = C._cell_mean(gsl_grid, D.CELL)
    ndvi = C._cell_mean(ndvi_grid, D.CELL)
    rich: dict = {}
    for L in langs:
        k = D.cell_of(L["lat"], L["lon"])
        rich[k] = rich.get(k, 0) + 1
    keys, y, X, area = [], [], [], []
    for k, t in terr.items():
        if k not in gsl or t["land_km2"] <= 2000 or k not in ndvi:
            continue
        if np.isnan(ndvi[k]):
            continue
        keys.append(k)
        y.append(rich.get(k, 0))
        X.append([gsl[k], t["rugged"], ndvi[k], abs(t["lat_mid"])])
        area.append(t["land_km2"])
    X = np.array(X, float)
    return {"keys": keys, "y": np.array(y, float), "X": X,
            "off": np.log(np.maximum(np.array(area, float), 1.0))}


def morans_i(keys: list, v: np.ndarray) -> float:
    """Queen adjacency on the cell lattice. Positive I = like values sit together."""
    idx = {k: i for i, k in enumerate(keys)}
    zc = v - v.mean()
    num = 0.0
    W = 0
    for k, i in idx.items():
        r, c = k
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                j = idx.get((r + dr, c + dc))
                if j is None:
                    continue
                num += zc[i] * zc[j]
                W += 1
    den = float(np.sum(zc ** 2))
    if W == 0 or den == 0:
        return 0.0
    return (len(keys) / W) * (num / den)


def zs(a):
    s = a.std()
    return (a - a.mean()) / (s if s > 1e-12 else 1.0)


def measure(verbose: bool = True) -> dict:
    R = build_rows()
    keys, y, off = R["keys"], R["y"], R["off"]
    gs, rug, nd, alat = (zs(R["X"][:, i]) for i in range(4))
    n = len(keys)
    names = ["growing season", "ruggedness", "peak NDVI", "|latitude|"]
    Xf = np.column_stack([np.ones(n), gs, rug, nd, alat])

    b, se, theta, _ = C.nb_glm(Xf, y, off)
    mu = np.exp(np.clip(Xf @ b + off, -30, 30))
    resid = (y - mu) / np.sqrt(np.maximum(mu, 1e-9))

    out = {"cells": n, "theta": round(theta, 3),
           "morans_i_richness": round(morans_i(keys, y / np.exp(off)), 4),
           "morans_i_residuals": round(morans_i(keys, resid), 4)}

    # ---- spatial block bootstrap: blocks of 5x5 cells = 10x10 degrees ------------------
    rng = np.random.RandomState(11)
    BLK = 5
    blocks: dict = {}
    for i, (r, c) in enumerate(keys):
        blocks.setdefault((r // BLK, c // BLK), []).append(i)
    bk = list(blocks)
    draws = []
    for _ in range(160):
        pick = [blocks[bk[j]] for j in rng.randint(0, len(bk), len(bk))]
        sel = np.concatenate(pick)
        if len(sel) < 200:
            continue
        try:
            bb, _, _, _ = C.nb_glm(Xf[sel], y[sel], off[sel], rounds=5)
        except Exception:                                    # noqa: BLE001
            continue
        draws.append(bb[1:])
    draws = np.array(draws)
    bse = draws.std(axis=0)

    out["coefficients"] = {}
    for i, nm in enumerate(names):
        infl = float(bse[i] / se[i + 1]) if se[i + 1] > 0 else float("nan")
        lo, hi = b[i + 1] - 1.96 * bse[i], b[i + 1] + 1.96 * bse[i]
        out["coefficients"][nm] = {
            "coef": round(float(b[i + 1]), 4),
            "se_model": round(float(se[i + 1]), 4),
            "se_block_bootstrap": round(float(bse[i]), 4),
            "inflation": round(infl, 2),
            "ci95": [round(float(lo), 3), round(float(hi), 3)],
            "survives": bool(lo * hi > 0),
        }

    # ---- distance thinning: keep cells at least k apart, refit ------------------------
    thin = {}
    for step in (2, 3):
        sel = [i for i, (r, c) in enumerate(keys) if r % step == 0 and c % step == 0]
        if len(sel) < 150:
            continue
        tb, tse, _, _ = C.nb_glm(Xf[sel], y[sel], off[sel])
        thin[f"every_{step}nd_cell"] = {
            "n": len(sel),
            **{nm: round(float(tb[i + 1]), 3) for i, nm in enumerate(names)}}
    out["thinned"] = thin

    if verbose:
        print("C10  spatial dependence\n")
        print(f"    {n:,} cells · Moran's I on richness "
              f"{out['morans_i_richness']:+.3f} · on model residuals "
              f"{out['morans_i_residuals']:+.3f}\n")
        print(f"    {'variable':16s} {'coef':>8s} {'SE model':>9s} {'SE block':>9s} "
              f"{'inflate':>8s}  95% CI")
        for nm in names:
            c = out["coefficients"][nm]
            print(f"    {nm:16s} {c['coef']:+8.3f} {c['se_model']:9.3f} "
                  f"{c['se_block_bootstrap']:9.3f} {c['inflation']:7.1f}x  "
                  f"[{c['ci95'][0]:+.2f}, {c['ci95'][1]:+.2f}]"
                  + ("" if c["survives"] else "   ← CROSSES ZERO"))
        print("\n    thinned refits (coefficients only):")
        for k2, v in thin.items():
            print(f"      {k2:16s} n={v['n']:5d}  " +
                  "  ".join(f"{nm.split()[0]} {v[nm]:+.2f}" for nm in names))
    return out


def _selftest() -> None:
    m = measure(verbose=False)
    assert m["cells"] > 1000
    # The whole premise: richness IS spatially autocorrelated. If this were near zero the
    # register item would have been imaginary.
    assert m["morans_i_richness"] > 0.15, \
        f"Moran's I on richness is {m['morans_i_richness']} — no spatial structure to correct"
    for nm, c in m["coefficients"].items():
        assert c["se_block_bootstrap"] > 0
        # A block bootstrap that came out TIGHTER than the naive model SE would mean the
        # resampling is not preserving the dependence it exists to preserve.
        assert c["inflation"] > 0.8, f"{nm}: block SE is smaller than the model SE"
    print("spatial.py selftest OK")


if __name__ == "__main__":
    _selftest()
    print()
    measure()
