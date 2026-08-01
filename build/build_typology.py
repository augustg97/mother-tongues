#!/usr/bin/env python3
"""build_typology.py — register D5: what each language is LIKE, in a sentence.

A card that says a language is endangered and has 5,413,380 speakers has told you about its
situation and nothing about the language. WALS records how languages actually work — where the
verb goes, whether there are articles, how many vowels — and a handful of those features,
written out, is the difference between a database row and a description.

Only features that are (a) widely coded and (b) meaningful to a non-linguist are used. A
sentence is assembled from whichever of them the language has; nothing is guessed, and a
language WALS never coded simply gets no sentence.

WALS is CC-BY-4.0 and keyed by Glottocode. Run: python3 build_typology.py
"""
from __future__ import annotations

import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
W = os.path.join(ROOT, "data", "wals")

# feature -> (template, {code description substring: phrase})
FEATURES = {
    "81A": ("word order", {
        "SOV": "puts the verb last (subject–object–verb)",
        "SVO": "puts the verb in the middle (subject–verb–object)",
        "VSO": "puts the verb first (verb–subject–object)",
        "VOS": "is verb-initial (verb–object–subject)",
        "OVS": "is object-initial (object–verb–subject)",
        "OSV": "is object-initial (object–subject–verb)",
        "No dominant order": "has no fixed order of subject, object and verb",
    }),
    "87A": ("adjectives", {
        "Adjective-Noun": "puts adjectives before the noun",
        "Noun-Adjective": "puts adjectives after the noun",
        "No dominant order": "has no fixed position for adjectives",
    }),
    "37A": ("articles", {
        "Definite word distinct from demonstrative": "has a definite article",
        "Demonstrative word used as definite article": "uses a demonstrative as its article",
        "Definite affix": "marks definiteness with an affix",
        "No definite, but indefinite article": "has an indefinite article but no definite one",
        "No definite or indefinite article": "has no articles at all",
    }),
    "2A": ("vowels", {
        "Small (2-4)": "gets by on a small vowel inventory",
        "Average (5-6)": "has an average vowel inventory",
        "Large (7-14)": "has a large vowel inventory",
    }),
    "13A": ("tone", {
        "No tones": "is not tonal",
        "Simple tone system": "is tonal",
        "Complex tone system": "has a complex tone system",
    }),
    "49A": ("case", {
        "No morphological case-marking": "does not mark case on nouns",
        "2 cases": "has two noun cases", "3 cases": "has three noun cases",
        "4 cases": "has four noun cases", "5 cases": "has five noun cases",
        "6-7 cases": "has six or seven noun cases",
        "8-9 cases": "has eight or nine noun cases",
        "10 or more cases": "has ten or more noun cases",
    }),
}


def main() -> None:
    if not os.path.isdir(W):
        print("no WALS data")
        return
    gc = {}
    with open(os.path.join(W, "languages.csv"), newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("Glottocode"):
                gc[r["ID"]] = r["Glottocode"]
    codes = {}
    with open(os.path.join(W, "codes.csv"), newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            codes[r["ID"]] = (r["Parameter_ID"], r["Name"])

    per: dict[str, dict[str, str]] = {}
    with open(os.path.join(W, "values.csv"), newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            g = gc.get(r["Language_ID"])
            if not g:
                continue
            pid, cname = codes.get(r["Code_ID"], (None, None))
            if pid not in FEATURES:
                continue
            _, table = FEATURES[pid]
            phrase = next((v for k, v in table.items() if cname and cname.startswith(k)), None)
            if phrase:
                per.setdefault(g, {})[pid] = phrase

    out = {}
    for g, feats in per.items():
        # Order the clauses so the sentence reads: order, adjectives, articles, case,
        # vowels, tone — general shape first, detail after.
        seq = [feats[k] for k in ("81A", "87A", "37A", "49A", "2A", "13A") if k in feats]
        if not seq:
            continue
        if len(seq) == 1:
            sent = "It " + seq[0] + "."
        else:
            sent = "It " + ", ".join(seq[:-1]) + " and " + seq[-1] + "."
        out[g] = sent
    d = os.path.join(ROOT, "web", "data")
    os.makedirs(d, exist_ok=True)
    json.dump({"source": "WALS Online (Dryer & Haspelmath, eds.)", "by_glottocode": out},
              open(os.path.join(d, "typology.json"), "w"), ensure_ascii=False,
              separators=(",", ":"))
    n = sum(len(v) for v in per.values())
    print(f"typology: {len(out):,} languages, {n:,} coded features, "
          f"{os.path.getsize(os.path.join(d,'typology.json'))/1e3:.0f} kB")
    for g in ("finn1318", "hind1269", "mand1415", "nucl1301"):
        if g in out:
            print(f"   {g}: {out[g]}")


if __name__ == "__main__":
    main()
