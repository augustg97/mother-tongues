#!/usr/bin/env python3
"""climate.py — measure the claim against the variable it is actually about.

Registers **C3**, **C6** and **C7**, and it is the round's substantive result.

THE PROBLEM THIS EXISTS TO FIX. SCOPE §1's amended claim says linguistic diversity is
explained first by **climate** — "how long the growing season is, and how many people a
landscape can feed year-round". Round 1 could not test that. It had no climate data, so it
tested **absolute latitude** as a stand-in and found |lat| beat ruggedness about 4 to 1. But
latitude is not a mechanism. It is a proxy for one, and a bad one across a continent: coastal
Norway and inland Siberia sit at the same latitude with utterly different growing seasons.

So this module brings in the real variables:

  * **growing-season length** — months of the year whose land-surface temperature climatology
    is at or above 5 °C, from twelve MODIS monthly climatologies (NASA, public domain).
  * **peak NDVI** — how much vegetation the place actually carries at its best month.

and asks whether either explains language richness better than latitude did.

THREE METHODS, because the round-1 statistic was a first look and was labelled as one:

  C3  Spearman and partial Spearman, as in round 1, so the numbers are comparable.
  C6  A **Poisson count model with a log-area offset**, because richness is a count over
      unequal areas and only 27% of land cells hold any language at all. A rank correlation
      on density cannot represent that; a count model can, and the overdispersion it reports
      is itself a finding.
  C7  **Relief per kilometre** as an alternative ruggedness measure, because round 1 used
      standard deviation of elevation, and if the terrain result flips under a different
      but equally reasonable definition then it was never a result.

stdlib + numpy. Run: python3 climate.py
"""
from __future__ import annotations

import glob
import math
import os

import numpy as np

import diversity as D

HERE = os.path.dirname(os.path.abspath(__file__))
EARTH = os.path.join(HERE, "..", "..", "data", "earth")

GS_THRESHOLD_C = 5.0        # the conventional threshold for a growing month


def _read_months(prefix: str) -> np.ndarray | None:
    import rasterio
    fs = sorted(glob.glob(os.path.join(EARTH, prefix + "_*.tif")))
    if len(fs) < 12:
        return None
    out = []
    for f in fs:
        with rasterio.open(f) as s:
            a = s.read(1).astype(np.float32)
        out.append(np.where((a > 1e4) | (a < -1e3), np.nan, a))
    return np.stack(out)


def growing_season() -> tuple[np.ndarray, np.ndarray]:
    """(months at or above 5 C, peak NDVI), both on the LST/NDVI source grids."""
    lst = _read_months("lst")
    if lst is None:
        raise SystemExit("no LST climatology in data/earth — run build/fetch_earth.py")
    gsl = np.nansum(lst >= GS_THRESHOLD_C, axis=0).astype(np.float32)
    gsl[np.all(np.isnan(lst), axis=0)] = np.nan          # ocean stays unknown, not zero
    ndvi = _read_months("ndvi")
    peak = np.nanmax(ndvi, axis=0) if ndvi is not None else np.full_like(gsl, np.nan)
    return gsl, peak


def _cell_mean(a: np.ndarray, cell: float) -> dict[tuple[int, int], float]:
    """Mean of a global plate-carree plane over the same cells diversity.py uses."""
    h, w = a.shape
    out: dict[tuple[int, int], float] = {}
    nlat, nlon = int(180 / cell), int(360 / cell)
    for i in range(nlat):
        r0, r1 = int(i * h / nlat), int((i + 1) * h / nlat)
        band = a[r0:r1]
        for j in range(nlon):
            c0, c1 = int(j * w / nlon), int((j + 1) * w / nlon)
            v = band[:, c0:c1]
            m = np.nanmean(v) if np.any(~np.isnan(v)) else np.nan
            if not np.isnan(m):
                # diversity.cell_of indexes by floor(lat/CELL), floor(lon/CELL)
                out[(int(math.floor((90 - (i + 0.5) * cell) / cell)),
                     int(math.floor((-180 + (j + 0.5) * cell) / cell)))] = float(m)
    return out


def poisson_glm(X: np.ndarray, y: np.ndarray, offset: np.ndarray,
                iters: int = 60) -> tuple[np.ndarray, float, float]:
    """Poisson GLM by IRLS. Returns (coefficients, deviance, Pearson dispersion).

    Hand-rolled because there is no statsmodels here and adding a dependency to `build/`
    for one regression is a bad trade. IRLS on a log link is fifteen lines and testable.
    """
    n, k = X.shape
    b = np.zeros(k)
    b[0] = math.log(max(y.mean(), 1e-6))
    for _ in range(iters):
        eta = X @ b + offset
        eta = np.clip(eta, -30, 30)
        mu = np.exp(eta)
        W = mu
        z = eta - offset + (y - mu) / np.maximum(mu, 1e-9)
        XtW = X.T * W
        try:
            bn = np.linalg.solve(XtW @ X + 1e-8 * np.eye(k), XtW @ z)
        except np.linalg.LinAlgError:
            break
        if np.max(np.abs(bn - b)) < 1e-9:
            b = bn
            break
        b = bn
    mu = np.exp(np.clip(X @ b + offset, -30, 30))
    with np.errstate(divide="ignore", invalid="ignore"):
        dev = 2 * np.nansum(np.where(y > 0, y * np.log(y / mu), 0) - (y - mu))
    disp = float(np.sum((y - mu) ** 2 / np.maximum(mu, 1e-9)) / max(n - k, 1))
    return b, float(dev), disp


def nb_glm(X: np.ndarray, y: np.ndarray, offset: np.ndarray,
           rounds: int = 12, fixed_theta: float | None = None
           ) -> tuple[np.ndarray, np.ndarray, float, float]:
    """Negative binomial (NB2) GLM. Returns (coefficients, standard errors, theta, deviance).

    **Register C9, and it is a correction to what round 3 published.** The Poisson fit
    reported a Pearson dispersion of 8-20. Poisson assumes variance equals the mean; at
    dispersion 15 the true variance is fifteen times that, so Poisson standard errors are
    too small by a factor of about sqrt(15) — every interval it would produce is roughly
    four times too narrow, and anything would look significant. The effect sizes were
    quotable and were quoted; the intervals were not, and were not.

    NB2 lets the variance be mu + mu^2/theta. Theta is estimated by moment matching against
    the current fit and the whole thing re-solved, a few times, which is enough here because
    the mean structure barely moves — it is the WEIGHTS that were wrong.
    """
    b, _, _ = poisson_glm(X, y, offset)
    theta = 1.0
    for _ in range(rounds):
        mu = np.exp(np.clip(X @ b + offset, -30, 30))
        if fixed_theta is not None:
            theta = fixed_theta
        else:
            num = float(np.sum(mu ** 2))
            den = float(np.sum((y - mu) ** 2 - mu))
            theta = max(1e-3, num / den) if den > 0 else 1e6
        for _ in range(25):
            eta = np.clip(X @ b + offset, -30, 30)
            mu = np.exp(eta)
            w = mu / (1.0 + mu / theta)                       # NB2 IRLS weight
            zv = eta - offset + (y - mu) / np.maximum(mu, 1e-9)
            XtW = X.T * w
            try:
                bn = np.linalg.solve(XtW @ X + 1e-9 * np.eye(X.shape[1]), XtW @ zv)
            except np.linalg.LinAlgError:
                break
            if np.max(np.abs(bn - b)) < 1e-10:
                b = bn
                break
            b = bn
    mu = np.exp(np.clip(X @ b + offset, -30, 30))
    w = mu / (1.0 + mu / theta)
    cov = np.linalg.pinv((X.T * w) @ X)
    se = np.sqrt(np.maximum(np.diag(cov), 0.0))
    with np.errstate(divide="ignore", invalid="ignore"):
        dev = 2 * np.nansum(
            np.where(y > 0, y * np.log(np.maximum(y, 1e-9) / mu), 0.0)
            - (y + theta) * np.log((y + theta) / (mu + theta)))
    return b, se, float(theta), float(dev)


def relief_per_km(z: np.ndarray) -> dict[tuple[int, int], float]:
    """C7. Range of land elevation across a cell, per kilometre of cell width.

    Round 1 measured ruggedness as the STANDARD DEVIATION of elevation in a cell. That is one
    reasonable definition and there are others; if the terrain finding flips when the
    definition changes, it was never a finding. This is the obvious alternative — how much
    height the ground actually gains and loses — and it weights a single deep valley very
    differently from sd, which is the point of checking.
    """
    step = int(D.CELL * 60)
    out: dict[tuple[int, int], float] = {}
    for r0 in range(0, 10800, step):
        band = z[r0:r0 + step]
        lat_mid = 90.0 - (r0 + step / 2.0) / 60.0
        irow = int(math.floor((lat_mid - 1e-9) / D.CELL))
        km = D.CELL * 111.32
        for c0 in range(0, 21600, step):
            blk = band[:, c0:c0 + step]
            land = blk > 0
            if not land.any():
                continue
            icol = int(math.floor(((c0 / 60.0) - 180.0 + 1e-9) / D.CELL))
            v = blk[land]
            out[(irow, icol)] = float(v.max() - v.min()) / km
    return out


def measure(verbose: bool = True) -> dict:
    langs = D.load_spoken_l1()
    z = D.load_dem()
    terr = D.terrain_per_cell(z)
    rpk = relief_per_km(z)
    gsl_grid, ndvi_grid = growing_season()
    gsl = _cell_mean(gsl_grid, D.CELL)
    ndvi = _cell_mean(ndvi_grid, D.CELL)

    rich: dict[tuple[int, int], int] = {}
    for L in langs:
        k = D.cell_of(L["lat"], L["lon"])
        rich[k] = rich.get(k, 0) + 1

    rows = []
    for k, t in terr.items():
        if k not in gsl:
            continue
        rows.append({
            "cell": k, "n": rich.get(k, 0),
            "rug": t["rugged"], "relief_km": rpk.get(k, 0.0),
            "abslat": abs(t["lat_mid"]), "gsl": gsl[k], "ndvi": ndvi.get(k, np.nan),
            "area": t["land_km2"], "land": t["land_km2"],
        })
    # Drop slivers: a cell with a few coastal pixels has an unstable density.
    rows = [r for r in rows if r["land"] > 2000.0 and not np.isnan(r["ndvi"])]
    n = len(rows)
    dens = np.array([r["n"] / r["area"] * 1e4 for r in rows])
    rug = np.array([r["rug"] for r in rows])
    rkm = np.array([r["relief_km"] for r in rows])
    alat = np.array([r["abslat"] for r in rows])
    gs = np.array([r["gsl"] for r in rows])
    nd = np.array([r["ndvi"] for r in rows])
    y = np.array([r["n"] for r in rows], float)
    area = np.array([r["area"] for r in rows])

    out = {"cells": n, "occupied": int((y > 0).sum()),
           "occupied_frac": round(float((y > 0).mean()), 4)}

    # ---- C3: the same statistic as round 1, so the numbers are comparable ---------------
    out["spearman"] = {
        "growing_season": round(D.spearman(gs, dens), 4),
        "peak_ndvi": round(D.spearman(nd, dens), 4),
        "abs_latitude": round(D.spearman(alat, dens), 4),
        "ruggedness": round(D.spearman(rug, dens), 4),
    }
    out["partial_on_growing_season"] = {
        "ruggedness": round(D.partial_spearman(rug, dens, gs), 4),
        "abs_latitude": round(D.partial_spearman(alat, dens, gs), 4),
        "peak_ndvi": round(D.partial_spearman(nd, dens, gs), 4),
    }
    out["partial_on_abs_latitude"] = {
        "growing_season": round(D.partial_spearman(gs, dens, alat), 4),
        "ruggedness": round(D.partial_spearman(rug, dens, alat), 4),
    }

    # ---- C7: does the terrain result survive a different definition of ruggedness? ------
    out["c7_relief_per_km"] = {
        "spearman": round(D.spearman(rkm, dens), 4),
        "partial_on_growing_season": round(D.partial_spearman(rkm, dens, gs), 4),
        "agrees_in_sign_with_sd_elevation":
            bool(np.sign(D.spearman(rkm, dens)) == np.sign(D.spearman(rug, dens))),
    }

    # ---- C6: a count model, with the land area each count came from as an offset --------
    def zs(a):
        s = a.std()
        return (a - a.mean()) / (s if s > 1e-12 else 1.0)
    off = np.log(np.maximum(area, 1.0))
    models = {
        "growing_season": np.column_stack([np.ones(n), zs(gs)]),
        "ruggedness": np.column_stack([np.ones(n), zs(rug)]),
        "abs_latitude": np.column_stack([np.ones(n), zs(alat)]),
        "gs+rug": np.column_stack([np.ones(n), zs(gs), zs(rug)]),
        "gs+rug+ndvi": np.column_stack([np.ones(n), zs(gs), zs(rug), zs(nd)]),
    }
    null_b, null_dev, _ = poisson_glm(np.ones((n, 1)), y, off)
    c6 = {"null_deviance": round(null_dev, 1)}
    for name, X in models.items():
        b, dev, disp = poisson_glm(X, y, off)
        c6[name] = {"coef": [round(float(v), 4) for v in b[1:]],
                    "deviance_explained": round(float(1 - dev / null_dev), 4),
                    "dispersion": round(disp, 2)}
    out["c6_poisson"] = c6

    # ---- C9: the same models under NB2, where the intervals mean something ---------------
    # ⚠ Deviance is only comparable at a FIXED theta. Comparing a model's deviance at its own
    # theta against a null fitted at a different theta gave "deviance explained" of -22% to
    # -86% — a negative proportion, which is the arithmetic telling you the comparison is
    # meaningless rather than the model being worse than nothing. Each model's null is now
    # refitted at that model's theta.
    c9 = {}
    for name, X in models.items():
        b, se, th, dev = nb_glm(X, y, off)
        _, _, _, ndev = nb_glm(np.ones((n, 1)), y, off, fixed_theta=th)
        c9[name] = {
            "null_deviance": round(ndev, 1),
            "coef": [round(float(v), 4) for v in b[1:]],
            "se": [round(float(v), 4) for v in se[1:]],
            "z": [round(float(v / s2), 2) if s2 > 0 else None for v, s2 in zip(b[1:], se[1:])],
            "theta": round(th, 3),
            "deviance_explained": round(float(1 - dev / ndev), 4),
        }
    out["c9_negative_binomial"] = c9

    if verbose:
        print(f"cells {n:,} · occupied {out['occupied']:,} "
              f"({out['occupied_frac']*100:.1f}%) · CELL {D.CELL}deg\n")
        print("C3  Spearman against language density")
        for k2, v in out["spearman"].items():
            print(f"      {k2:18s} {v:+.3f}")
        print("\n    partial, holding GROWING SEASON constant")
        for k2, v in out["partial_on_growing_season"].items():
            print(f"      {k2:18s} {v:+.3f}")
        print("\n    partial, holding ABSOLUTE LATITUDE constant")
        for k2, v in out["partial_on_abs_latitude"].items():
            print(f"      {k2:18s} {v:+.3f}")
        print(f"\nC7  relief per km  {out['c7_relief_per_km']['spearman']:+.3f} "
              f"(partial on growing season {out['c7_relief_per_km']['partial_on_growing_season']:+.3f})"
              f"  sign agrees with sd-elevation: "
              f"{out['c7_relief_per_km']['agrees_in_sign_with_sd_elevation']}")
        print("\nC6  Poisson count model, log land area as offset")
        for name in models:
            m = c6[name]
            print(f"      {name:14s} coef {m['coef']}  "
                  f"deviance explained {m['deviance_explained']*100:5.1f}%  "
                  f"dispersion {m['dispersion']:.1f}")
        print("\nC9  negative binomial (NB2) — the intervals Poisson could not give")
        for name in models:
            m = c9[name]
            terms = " ".join(f"{c:+.3f}+-{s2:.3f} (z={zz})"
                             for c, s2, zz in zip(m["coef"], m["se"], m["z"]))
            print(f"      {name:14s} {terms}")
            print(f"      {'':14s} theta {m['theta']:.2f}  "
                  f"deviance explained {m['deviance_explained']*100:5.1f}%")
    return out


def _selftest() -> None:
    gsl, peak = growing_season()
    # Physical sanity, at named places, on the SOURCE grid — a growing season is 0..12 months.
    assert np.nanmin(gsl) >= 0 and np.nanmax(gsl) <= 12, "growing season outside 0..12 months"

    def at(a, la, lo):
        return float(a[int((90 - la) / 180 * a.shape[0]), int((lo + 180) / 360 * a.shape[1])])
    # Singapore is warm every month; central Antarctica is warm in none. If these two are not
    # 12 and 0 the climatology is upside down or in the wrong units.
    # Kuala Lumpur, not Singapore: at 0.1 deg the island is classified as water and the
    # LST climatology has no land retrieval there at all.
    assert at(gsl, 3.1, 101.7) >= 11, f"Malaysian growing season {at(gsl,3.1,101.7)}"
    assert at(gsl, -80.0, 0.0) <= 1, f"Antarctic growing season {at(gsl,-80,0)}"
    assert at(gsl, 68.0, 100.0) <= 6, f"Siberian growing season {at(gsl,68,100)} — too long"
    assert -1.0 <= np.nanmin(peak) and np.nanmax(peak) <= 1.0, "NDVI outside -1..1"

    # NB2 must recover a known slope too, and its SEs must be LARGER than Poisson's on
    # overdispersed data — that is the entire point of fitting it.
    rs = np.random.RandomState(1)
    mu_t = np.exp(0.4 + 1.2 * np.arange(400) / 400.0)
    yo = rs.negative_binomial(2.0, 2.0 / (2.0 + mu_t))
    Xo = np.column_stack([np.ones(400), np.arange(400) / 400.0])
    bn, sen, th, _ = nb_glm(Xo, yo, np.zeros(400))
    bp, _, _ = poisson_glm(Xo, yo, np.zeros(400))
    covp = np.linalg.pinv((Xo.T * np.exp(Xo @ bp)) @ Xo)
    assert abs(bn[1] - 1.2) < 0.8, f"NB2 did not recover a known slope: {bn}"
    assert sen[1] > np.sqrt(covp[1, 1]), \
        "NB2 standard error is not larger than Poisson's on overdispersed data"
    assert 0.5 < th < 12, f"theta {th} implausible for data generated with theta=2"
    # A proportion of deviance explained outside 0..1 means the two deviances were computed
    # under different models and are not comparable. This is exactly how the first NB2 pass
    # reported -86%.
    _, _, thf, dv = nb_glm(Xo, yo, np.zeros(400))
    _, _, _, dv0 = nb_glm(np.ones((400, 1)), yo, np.zeros(400), fixed_theta=thf)
    frac = 1 - dv / dv0
    assert -0.01 <= frac <= 1.0, f"deviance explained {frac:.3f} is not a proportion"

    b, dev, disp = poisson_glm(np.column_stack([np.ones(200), np.arange(200) / 200.0]),
                               np.random.RandomState(0).poisson(
                                   np.exp(0.5 + 1.5 * np.arange(200) / 200.0)),
                               np.zeros(200))
    assert abs(b[1] - 1.5) < 0.6, f"Poisson IRLS did not recover a known slope: {b}"
    print("climate.py selftest OK")


if __name__ == "__main__":
    _selftest()
    print()
    measure()
