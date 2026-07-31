#!/usr/bin/env python3
"""fetch_autonyms.py — acquire autonyms, and the script each one is written in. Register D6.

WHY THIS EXISTS. Glottolog's `Name` is a *reference name*: a stable, unique, English-language
identifier for a languoid. It is excellent at being that and it is not a name in any other
sense. Of the 7,672 languages in this build it gives us strings like "Paku Karen", "South
Marquesan", "San Francisco del Mar Huave" and "Southern Awu (Lope)" — compound catalogue keys
built from an exonym plus a geographic qualifier plus a parenthetical disambiguator, in Latin
script, in English. No speaker calls their language any of those. Some of the exonyms inside
them are colonial and a few are slurs.

CLAUDE.md rule 11 requires the autonym first, in its own script. Glottolog cannot supply it.

Wikidata can: **P1705 "native label"** is defined as the name in the local language, carried
with a language tag, in its own script — and Wikidata is **CC0**, so there is no licence
question. It joins to us on **P1394 (Glottolog code)**, our own identity key, with **P220
(ISO 639-3)** as the fallback alias-join for items that carry no glottocode.

We also take **P282 (writing system)**, because a name in Devanagari rendered in a Latin font
is not a name in Devanagari, and the app must know which script it is holding (register D4).

Coverage will be partial. That is fine and it is the point: a language with an autonym gets
its autonym, a language without one is shown as "reference name" and says so. What is NOT
acceptable is the current state, where every language silently shows an exonym.

Run: python3 fetch_autonyms.py
"""
from __future__ import annotations

import json
import os
import ssl
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "data", "autonyms")
ENDPOINT = "https://query.wikidata.org/sparql"
UA = "MotherTongues/1.0 (research atlas of human languages; contact augustgweon@gmail.com)"

# Two queries rather than one: the join key differs, and a single OPTIONAL-heavy query times
# out on the public endpoint. Each is small enough to complete inside the 60 s budget.
Q_GLOTTO = """
SELECT ?glotto ?native ?scriptLabel WHERE {
  ?item wdt:P1394 ?glotto .
  ?item wdt:P1705 ?native .
  OPTIONAL { ?item wdt:P282 ?script .
             ?script rdfs:label ?scriptLabel . FILTER(LANG(?scriptLabel) = "en") }
}
"""

Q_ISO = """
SELECT ?iso ?native ?scriptLabel WHERE {
  ?item wdt:P220 ?iso .
  ?item wdt:P1705 ?native .
  OPTIONAL { ?item wdt:P282 ?script .
             ?script rdfs:label ?scriptLabel . FILTER(LANG(?scriptLabel) = "en") }
}
"""


def sparql(q: str, tries: int = 4) -> list:
    url = ENDPOINT + "?" + urllib.parse.urlencode({"query": q, "format": "json"})
    ctx = ssl.create_default_context()
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA,
                                                       "Accept": "application/sparql-results+json"})
            with urllib.request.urlopen(req, timeout=180, context=ctx) as r:
                return json.load(r)["results"]["bindings"]
        except Exception as e:                     # noqa: BLE001 — retry any transport error
            last = e
            print(f"   attempt {i+1} failed: {type(e).__name__}: {e}")
            time.sleep(6 * (i + 1))
    raise RuntimeError(f"Wikidata query failed after {tries} attempts: {last}")


def collect(rows: list, key: str) -> dict:
    """Keep every distinct native label per key, with its language tag and script.

    A language legitimately has more than one autonym — different orthographies, different
    dialects, a pre- and post-reform spelling. We keep them all and let the app show the
    first and count the rest, rather than picking a winner here where the evidence is thin.
    """
    out: dict = {}
    for b in rows:
        k = b[key]["value"]
        lit = b["native"]["value"]
        tag = b["native"].get("xml:lang", "")
        scr = b.get("scriptLabel", {}).get("value", "")
        rec = out.setdefault(k, {"names": [], "scripts": []})
        if not any(n[0] == lit for n in rec["names"]):
            rec["names"].append([lit, tag])
        if scr and scr not in rec["scripts"]:
            rec["scripts"].append(scr)
    return out


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    print("Wikidata P1705 native labels (CC0)")

    print("1. by Glottolog code (P1394) — the identity key")
    g = collect(sparql(Q_GLOTTO), "glotto")
    print(f"   {len(g):,} glottocodes with at least one native label")

    print("2. by ISO 639-3 (P220) — the fallback alias join")
    i = collect(sparql(Q_ISO), "iso")
    print(f"   {len(i):,} ISO codes with at least one native label")

    json.dump({"by_glottocode": g, "by_iso639_3": i,
               "source": "Wikidata P1705 (native label), P282 (writing system)",
               "licence": "CC0-1.0",
               "retrieved": time.strftime("%Y-%m-%d")},
              open(os.path.join(OUT, "autonyms.json"), "w"), ensure_ascii=False)
    n = sum(len(v["names"]) for v in g.values()) + sum(len(v["names"]) for v in i.values())
    print(f"\nwrote data/autonyms/autonyms.json — {n:,} distinct native labels")
