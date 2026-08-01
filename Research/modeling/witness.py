#!/usr/bin/env python3
"""witness.py — register E1, the independent witness. Planned for round 1; built in round 7.

WHAT AN INDEPENDENT WITNESS IS FOR. Every number this project publishes about where languages
are comes from one catalogue. Glottolog is a good catalogue, but a model scored only against
its own source cannot detect that the source is wrong — it can only detect that the pipeline
disagrees with itself. TRAPS §D5: an audit that reads what the pipeline reads is a mirror.

So this scores our language POSITIONS against a genuinely separate compilation: **Wikidata's
coordinate location (P625)** for items carrying a Glottolog id. Different editors, different
sourcing conventions, different errors. Where the two agree, the position is corroborated.
Where they disagree by hundreds of kilometres, at least one of them is wrong and the language
is named here so it can be checked by hand.

WHAT IT CANNOT DO. Wikidata is not a random sample: it covers the better-known languages, so
agreement here says nothing about the long tail. It is also not fully independent — some
Wikidata coordinates were surely copied from Glottolog. Both limits are printed with the
result rather than left for a reader to assume away.

stdlib + the shared frame. Run: python3 witness.py
"""
from __future__ import annotations

import json
import math
import os

import diversity as D

HERE = os.path.dirname(os.path.abspath(__file__))
WD = os.path.join(HERE, "..", "..", "data", "autonyms", "wd_coords.json")

# A language's "point" is a centroid of a speech area, not a pin. Two catalogues placing the
# same language 100 km apart are agreeing; 500 km apart are not.
AGREE_KM = 100.0
GROSS_KM = 500.0


def haversine(a: tuple[float, float], b: tuple[float, float]) -> float:
    lo1, la1, lo2, la2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = (math.sin((la2 - la1) / 2) ** 2
         + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2)
    return 2 * 6371.0088 * math.asin(min(1.0, math.sqrt(h)))


def measure(verbose: bool = True) -> dict:
    if not os.path.exists(WD):
        raise SystemExit("no witness file — run the Wikidata coordinate fetch first")
    wd = json.load(open(WD, encoding="utf-8"))
    ours = {L["code"]: (L["lon"], L["lat"]) for L in D.load_spoken_l1()}

    pairs = [(gc, ours[gc], tuple(wd[gc])) for gc in ours if gc in wd]
    d = sorted((haversine(o, w), gc) for gc, o, w in pairs)
    n = len(d)
    if n < 50:
        raise SystemExit(f"only {n} languages in both catalogues — too few to score")
    km = [x[0] for x in d]

    def pct(p):
        return km[min(n - 1, int(p / 100 * n))]

    gross = [(round(k), gc) for k, gc in d if k > GROSS_KM]
    out = {
        "compared": n,
        "of_our_languages": round(n / max(len(ours), 1), 4),
        "median_km": round(pct(50), 1),
        "p90_km": round(pct(90), 1),
        "agree_within_100km": round(sum(1 for k in km if k <= AGREE_KM) / n, 4),
        "gross_disagreements": len(gross),
        "worst": [{"glottocode": gc, "km": k} for k, gc in gross[-8:][::-1]],
        "limits": ("Wikidata covers better-known languages, so this says nothing about the "
                   "long tail; and it is not fully independent, since some of its "
                   "coordinates were probably taken from Glottolog in the first place."),
    }
    if verbose:
        print(f"E1  independent witness: Wikidata P625 vs Glottolog\n")
        print(f"    {n:,} languages in both ({out['of_our_languages']*100:.1f}% of ours)")
        print(f"    median displacement {out['median_km']:.1f} km · "
              f"90th percentile {out['p90_km']:.0f} km")
        print(f"    agree within {AGREE_KM:.0f} km: {out['agree_within_100km']*100:.1f}%")
        print(f"    disagree by more than {GROSS_KM:.0f} km: {len(gross)}")
        for w in out["worst"]:
            print(f"      {w['glottocode']}  {w['km']:,} km")
        print(f"\n    {out['limits']}")
    return out


def _selftest() -> None:
    # The distance function first: London-Paris is 344 km, and a point against itself is 0.
    assert abs(haversine((-0.1276, 51.5072), (2.3522, 48.8566)) - 344) < 12
    assert haversine((10.0, 10.0), (10.0, 10.0)) == 0.0

    m = measure(verbose=False)
    # These are the ratchet. If a future ingest shifts our coordinates, the witness moves
    # before anything visible does — which is the entire reason to have one.
    assert m["compared"] >= 300, f"only {m['compared']} languages to score against"
    assert m["median_km"] < 60, \
        f"median displacement {m['median_km']} km — our positions have moved"
    assert m["agree_within_100km"] > 0.75, \
        f"only {m['agree_within_100km']:.1%} agree within 100 km"
    print("witness.py selftest OK")


if __name__ == "__main__":
    _selftest()
    print()
    measure()
