#!/usr/bin/env python3
"""fetch_words.py — the word tier. Real words, in real languages, for thousands of them.

Register **D2b**. The UDHR passage is one paragraph of twentieth-century legal prose, it exists
for 432 languages, and it is the same sentence every time. That is one exhibit. It is not a
museum.

ASJP is the other kind of exhibit and it is far wider: a short, deliberately basic word list —
*water*, *hand*, *sun*, *name*, *to die* — collected on one comparable scale for **thousands**
of languages, including a great many that have never had a paragraph of anything translated
into them. Where the UDHR gives one language a voice, ASJP gives a language a handful of its
most ordinary words, which is often the only text that exists at all.

ASJP is **CC-BY-4.0** (Wichmann, Holman & Brown, eds.), joined to us on **Glottocode**, which
is ASJP's own key too — no alias hop.

The forms are in ASJP's transcription (ASJPcode), a deliberately coarse ASCII scheme. That is
what the source contains and the card says so: presenting it as an orthography would be a
different kind of lie from presenting an exonym as an autonym, but the same kind of mistake.

Run: python3 fetch_words.py
"""
from __future__ import annotations

import csv
import io
import json
import os
import ssl
import urllib.request
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "data", "words")
UA = "MotherTongues/1.0 (research atlas; augustgweon@gmail.com)"
BASE = "https://raw.githubusercontent.com/lexibank/asjp/master/cldf/"

# The concepts a visitor can feel the meaning of without a gloss, chosen from ASJP's 40.
WANT_CONCEPTS = ["water", "fire", "sun", "moon", "star", "stone", "mountain", "tree", "leaf",
                 "blood", "bone", "hand", "eye", "ear", "nose", "tooth", "tongue", "skin",
                 "name", "person", "man", "woman", "child", "fish", "bird", "dog", "louse",
                 "horn", "knee", "breast", "liver", "path", "night", "die", "come", "see",
                 "hear", "drink", "new", "full", "one", "two"]


def get(name: str) -> bytes:
    p = os.path.join(OUT, name.replace("/", "_"))
    if os.path.exists(p) and os.path.getsize(p) > 1024:
        return open(p, "rb").read()
    req = urllib.request.Request(BASE + name, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=600,
                                context=ssl.create_default_context()) as r:
        b = r.read()
    os.makedirs(OUT, exist_ok=True)
    open(p, "wb").write(b)
    return b


def rows(name: str):
    return csv.DictReader(io.StringIO(get(name).decode("utf-8", "replace")))


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    print("ASJP wordlists (CC-BY-4.0)")

    # languages.csv: ASJP doculect -> Glottocode
    gc_of: dict[str, str] = {}
    for r in rows("languages.csv"):
        g = (r.get("Glottocode") or "").strip()
        if g and len(g) == 8:
            gc_of[r["ID"]] = g
    print(f"   {len(gc_of):,} doculects carry a glottocode")

    # parameters.csv: concept id -> english gloss
    # ⚠ ASJP marks its 40-item core subset with a LEADING ASTERISK — "*water", "*person".
    # Matching the raw Name against a plain word list found 4 of 100 concepts and produced a
    # file with zero usable languages, which looks like a coverage problem and is a parsing
    # problem. Strip the marker; keep the fact that it marked the core list.
    concept: dict[str, str] = {}
    core: set[str] = set()
    for r in rows("parameters.csv"):
        nm = (r.get("Name") or "").strip().lower()
        if nm.startswith("*"):
            nm = nm[1:]
            core.add(r["ID"])
        concept[r["ID"]] = nm
    want = {k: v for k, v in concept.items() if v in WANT_CONCEPTS}
    print(f"   {len(concept)} concepts ({len(core)} in ASJP's core 40), "
          f"{len(want)} of them wanted")

    per: dict[str, dict[str, str]] = defaultdict(dict)
    n = 0
    for r in rows("forms.csv"):
        pid = r.get("Parameter_ID")
        if pid not in want:
            continue
        gc = gc_of.get(r.get("Language_ID", ""))
        if not gc:
            continue
        form = (r.get("Form") or "").strip()
        if not form or form in ("?", "-"):
            continue
        gloss = want[pid]
        # Keep the FIRST attestation per (language, concept): ASJP often has several
        # doculects per language and averaging or concatenating them would invent a form
        # nobody said.
        per[gc].setdefault(gloss, form)
        n += 1
    print(f"   {n:,} forms kept across {len(per):,} languages")

    out = {gc: v for gc, v in per.items() if len(v) >= 5}
    json.dump({"source": "ASJP — Wichmann, Holman & Brown (eds.), Automated Similarity "
                         "Judgment Program",
               "licence": "CC-BY-4.0",
               "transcription": "ASJPcode, a deliberately coarse ASCII scheme — not the "
                                "language's own orthography",
               "concepts": sorted(WANT_CONCEPTS),
               "by_glottocode": out},
              open(os.path.join(OUT, "words.json"), "w"), ensure_ascii=False,
              separators=(",", ":"))
    print(f"   wrote data/words/words.json — {len(out):,} languages with 5+ words, "
          f"{os.path.getsize(os.path.join(OUT,'words.json'))/1e6:.1f} MB")
