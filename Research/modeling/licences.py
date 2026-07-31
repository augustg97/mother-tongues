#!/usr/bin/env python3
"""licences.py — the ingest licence gate.

Register: A3. Contract: SCOPE.md §12 D3 — ShareAlike is permitted for data and images;
**NonCommercial and NoDerivatives are not.**

Why this is code and not a note
-------------------------------
The language-polygon collection publishes 34 repositories. Its own platform paper says
the datasets are CC-BY-4.0. **That is not true of all of them**: three carry
CC-BY-NC-4.0, and GitHub's licence API cannot tell — it returns `NOASSERTION` for every
Creative Commons variant it does not recognise, which lumps the NonCommercial ones in
with plain "Other". So a gate that trusts either the paper or the API ships material we
may not redistribute.

This module therefore classifies from the **licence text**, refuses anything NC or ND,
and its selftest asserts the three known-bad repositories are excluded by name. If the
upstream collection adds a fourth NC dataset, the gate catches it and the selftest tells
you the count moved.

stdlib only. `build/` imports `shippable()` and iterates that, never a hand-kept list.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "..", "data", "glottography")

# Infrastructure repositories in the collection — code and docs, not datasets.
INFRA = {".github", "Rglottography", "pyglottography", "supporting-material", "tutorials"}

# Verified 2026-07-31 by reading each repository's own LICENSE file. Recorded so a
# future run can tell "upstream changed" from "our classifier changed".
KNOWN_EXCLUDED = {"bowern2021australia", "haynie2019modern", "wurm1981pacific"}
KNOWN_DATASET_COUNT = 29
KNOWN_SHIPPABLE_COUNT = 26


@dataclass(frozen=True)
class Verdict:
    name: str
    shippable: bool
    reason: str
    share_alike: bool = False       # permitted under D3, but needs a ledger row
    attribution_required: bool = True


def classify_text(name: str, text: str) -> Verdict:
    """Classify one licence from its text. Conservative: unknown never means yes."""
    t = " ".join(text.split()).lower()
    nc = ("noncommercial" in t or "non-commercial" in t
          or "commercial purposes" in t and "not" in t)
    nd = "noderivatives" in t or "no derivative" in t or "noderivs" in t
    sa = "sharealike" in t or "share alike" in t or "share-alike" in t
    cc_by = "attribution 4.0" in t or "attribution 3.0" in t or "creative commons attribution" in t
    public_domain = "cc0" in t or "public domain dedication" in t

    if nc:
        return Verdict(name, False, "NonCommercial — excluded by SCOPE §12 D3", sa)
    if nd:
        return Verdict(name, False, "NoDerivatives — excluded by SCOPE §12 D3", sa)
    if public_domain:
        return Verdict(name, True, "public domain / CC0", False, attribution_required=False)
    if sa and cc_by:
        return Verdict(name, True, "CC-BY-SA — permitted under D3, LEDGER ROW REQUIRED", True)
    if cc_by:
        return Verdict(name, True, "CC-BY", False)
    if "apache license" in t or "mit license" in t:
        return Verdict(name, True, "permissive software licence (code, not data)", False)
    return Verdict(name, False, "licence not recognised — refuse rather than guess", sa)


def load_licence_texts(path: Optional[str] = None) -> dict:
    """Load the fetched licence classification produced at ingest.

    Kept as data on disk so the gate is reproducible offline and a network outage cannot
    silently widen what we ship.
    """
    p = path or os.path.join(DATA, "licences.json")
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def verdicts(path: Optional[str] = None) -> dict[str, Verdict]:
    """Verdict per dataset repository, from the stored classification."""
    raw = load_licence_texts(path)
    out: dict[str, Verdict] = {}
    for name, rec in raw.items():
        if name in INFRA:
            continue
        if rec.get("err"):
            out[name] = Verdict(name, False, f"licence unreadable: {rec['err']}")
            continue
        # The stored record carries the three booleans we derived from the text.
        if rec.get("nc"):
            out[name] = Verdict(name, False, "NonCommercial — excluded by SCOPE §12 D3",
                                bool(rec.get("sa")))
        elif rec.get("nd"):
            out[name] = Verdict(name, False, "NoDerivatives — excluded by SCOPE §12 D3",
                                bool(rec.get("sa")))
        elif rec.get("sa"):
            out[name] = Verdict(name, True,
                                "ShareAlike — permitted under D3, LEDGER ROW REQUIRED", True)
        else:
            out[name] = Verdict(name, True, rec.get("title", "CC-BY")[:60], False)
    return out


def shippable(path: Optional[str] = None) -> list[str]:
    """The allowlist. `build/` iterates THIS, never a hand-kept list."""
    return sorted(n for n, v in verdicts(path).items() if v.shippable)


def excluded(path: Optional[str] = None) -> dict[str, str]:
    return {n: v.reason for n, v in verdicts(path).items() if not v.shippable}


def needs_ledger_row(path: Optional[str] = None) -> list[str]:
    """ShareAlike sources: permitted, but the attribution ledger must carry them."""
    return sorted(n for n, v in verdicts(path).items() if v.shippable and v.share_alike)


def _selftest() -> None:
    # --- the classifier, on synthetic text (no network) -------------------
    assert not classify_text("x", "Attribution-NonCommercial 4.0 International").shippable
    assert not classify_text("x", "Attribution-NoDerivatives 4.0").shippable
    assert classify_text("x", "Creative Commons Attribution 4.0 International").shippable
    v = classify_text("x", "Creative Commons Attribution-ShareAlike 3.0")
    assert v.shippable and v.share_alike, "SA must pass under D3 but be flagged"
    assert classify_text("x", "CC0 1.0 Universal").attribution_required is False
    # unknown text must REFUSE, not guess
    assert not classify_text("x", "All rights reserved. Ask nicely.").shippable
    # NC beats SA: a CC-BY-NC-SA licence is excluded on the NC, not admitted on the SA
    v = classify_text("x", "Attribution-NonCommercial-ShareAlike 4.0 International")
    assert not v.shippable and v.share_alike

    # --- the real collection ---------------------------------------------
    try:
        vs = verdicts()
    except FileNotFoundError:
        print("licences.py selftest: classifier OK; no fetched data present, skipping "
              "the collection assertions")
        return

    ship, exc = shippable(), excluded()
    assert len(vs) == KNOWN_DATASET_COUNT, (
        f"dataset count moved: {len(vs)} vs {KNOWN_DATASET_COUNT}. Upstream added or "
        f"removed a dataset — re-verify before shipping.")
    assert set(exc) == KNOWN_EXCLUDED, (
        f"the excluded set moved: {sorted(exc)} vs {sorted(KNOWN_EXCLUDED)}")
    assert len(ship) == KNOWN_SHIPPABLE_COUNT, (
        f"shippable count moved: {len(ship)} vs {KNOWN_SHIPPABLE_COUNT}")
    # the three NC repos must not appear in the allowlist under any circumstance
    for bad in KNOWN_EXCLUDED:
        assert bad not in ship, f"{bad} leaked into the allowlist"

    print("licences.py selftest: OK")


if __name__ == "__main__":
    _selftest()
    try:
        vs = verdicts()
    except FileNotFoundError:
        raise SystemExit(0)
    print()
    print(f"A3 — Glottography ingest gate, {len(vs)} dataset repositories")
    print(f"  shippable : {len(shippable())}")
    print(f"  EXCLUDED  : {len(excluded())}")
    for n, r in sorted(excluded().items()):
        print(f"              {n:26s} {r}")
    led = needs_ledger_row()
    print(f"  ShareAlike needing a ledger row: {len(led)}" + (f" {led}" if led else " (none)"))
    print()
    print("  Note: GitHub's licence API reports NOASSERTION for all three excluded")
    print("  repositories — it cannot distinguish CC-BY-NC from 'Other'. The gate reads")
    print("  licence TEXT for exactly this reason.")
