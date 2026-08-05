#!/usr/bin/env python3
"""probe_categories.py — find which Wikimedia Commons categories actually exist for our
languages, before anything is authored against them.

WHY. The licence gate admits a file on its licence and cannot check whether the picture is of
the right thing. A free-text search for "Tamil manuscript" matches words; a category is curated
by people, so a file in Category:Tamil manuscripts is there because someone put it there. That
makes categories the better source — but only the ones that exist. Guessing category names and
authoring 500 subjects against them produces a fetch run where most queries return nothing and
the failures are indistinguishable from a digitisation gap.

So: generate candidate names from a small set of patterns, ask Commons which exist and how many
files each holds, and print only the ones worth authoring. Measure, then author.

Run: python3 probe_categories.py > ../data/gallery/categories.txt
"""
from __future__ import annotations

import json
import os
import ssl
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.join(HERE, "..", "web", "data")
API = "https://commons.wikimedia.org/w/api.php"
UA = "MotherTongues/1.0 (research atlas; augustgweon@gmail.com)"

# Patterns that Commons actually uses for language material. {L} is the English language name
# as Glottolog gives it, with any parenthetical stripped.
PATTERNS = [
    "{L} language",
    "{L} manuscripts",
    "{L} inscriptions",
    "{L} calligraphy",
    "{L} alphabet",
    "{L} script",
    "Books in {L}",
    "Newspapers in {L}",
    "Inscriptions in {L}",
    "Manuscripts in {L}",
    "Texts in {L}",
    "{L} literature",
    "{L} culture",
    "{L} people",
]

MIN_FILES = 3          # below this a category is not worth a query


def api(params: dict) -> dict:
    q = dict(params)
    q.update({"action": "query", "format": "json", "formatversion": "2"})
    url = API + "?" + urllib.parse.urlencode(q)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=90,
                                context=ssl.create_default_context()) as r:
        return json.load(r)


def file_counts(titles: list[str]) -> dict[str, int]:
    """How many FILES each category holds. Commons reports this directly."""
    out: dict[str, int] = {}
    for i in range(0, len(titles), 40):
        chunk = titles[i:i + 40]
        try:
            j = api({"titles": "|".join(chunk), "prop": "categoryinfo"})
        except Exception as e:                               # noqa: BLE001
            print(f"# probe failed: {e}", file=sys.stderr)
            continue
        for p in (j.get("query", {}) or {}).get("pages", []) or []:
            ci = p.get("categoryinfo") or {}
            if p.get("missing"):
                continue
            out[p["title"]] = int(ci.get("files") or 0)
        time.sleep(0.25)
    return out


if __name__ == "__main__":
    langs = json.load(open(os.path.join(WEB, "languages.json")))
    F = {k: i for i, k in enumerate(langs["fields"])}
    name = {r[F["code"]]: r[F["name"]] for r in langs["rows"]}
    # WIDER THAN THE LABELS. The first pass probed only the 283 languages with an authored
    # museum label, which is why 7,430 languages had no objects at all. The target set is now
    # every language documented enough that Commons plausibly holds something: it has its own
    # Wikipedia, or a text here, or a recording, or a curated alphabet, or a label. 818 of them,
    # of which 578 had nothing.
    def keys(path, sub=None):
        pp = os.path.join(WEB, path)
        if not os.path.exists(pp):
            return set()
        d = json.load(open(pp, encoding="utf-8"))
        return set((d.get(sub) or d) if sub else d)
    notable = (keys("notable.json", "by_glottocode") | keys("wikipedia.json", "by_glottocode")
               | keys("texts.json", "by_glottocode") | keys("audio.json", "by_glottocode")
               | keys("alphabets.json", "by_glottocode")) & set(name)

    # candidate -> the glottocode it would serve
    cand: dict[str, str] = {}
    for gc in notable:
        nm = name.get(gc)
        if not nm:
            continue
        base = nm.split(" (")[0].strip()
        for pat in PATTERNS:
            cand["Category:" + pat.format(L=base)] = gc

    print(f"# probing {len(cand)} candidate categories for {len(notable)} languages",
          file=sys.stderr)
    counts = file_counts(sorted(cand))
    keep = {t: n for t, n in counts.items() if n >= MIN_FILES}
    print(f"# {len(keep)} exist with {MIN_FILES}+ files", file=sys.stderr)

    per: dict[str, list] = {}
    for t, n in sorted(keep.items(), key=lambda kv: -kv[1]):
        per.setdefault(cand[t], []).append([t, n])
    json.dump(per, open(os.path.join(HERE, "..", "data", "gallery",
                                     "categories.json"), "w"), ensure_ascii=False, indent=1)
    langs_hit = len(per)
    print(f"# {langs_hit} of {len(notable)} languages have at least one usable category",
          file=sys.stderr)
    for gc, rows in sorted(per.items(), key=lambda kv: -sum(r[1] for r in kv[1]))[:25]:
        print(f"{name.get(gc, gc):26s} " +
              " · ".join(f"{t[9:]} ({n})" for t, n in rows[:4]), file=sys.stderr)
