#!/usr/bin/env python3
"""fetch_wikitext.py — prose from a language's own Wikipedia, for the observed letter tier.
Register D11b.

WHY, AND WHAT THE CEILING IS. Letters reach 7.1% of the 7,672 languages here, and that is not a
backlog item — it is the amount of orthographic material that exists in machine-readable form.
CLDR curates exemplar characters for about 300 languages. This build holds connected prose for
430. Beyond those, most languages in this atlas have never been typed.

But 316 have their own Wikipedia, and 77 of those had no letters — 75 of them with three or more
active editors last month, so the articles are prose written by people rather than a bot's
skeleton. A few thousand characters of it yields an observed character inventory on exactly the
same footing as the UDHR-derived one: a measurement of a document, labelled as one, with its
sample size, never called the alphabet.

Text comes from each edition's own API (`prop=extracts`, plain text, intro sections of random
articles), so it is the language writing about whatever it chose to write about. CC-BY-SA, which
SCOPE §12 D3 permits.

Run: python3 fetch_wikitext.py
"""
from __future__ import annotations

import json
import os
import ssl
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
WEB = os.path.join(ROOT, "web", "data")
OUT = os.path.join(ROOT, "data", "wikipedia")
UA = "MotherTongues/1.0 (research atlas of human languages; augustgweon@gmail.com)"

WANT_CHARS = 4000       # enough to see a language's letters; a page or two of prose
MIN_ACTIVE = 3          # below this the edition may be bot-built rather than written


def get(url: str, tries: int = 3):
    ctx = ssl.create_default_context()
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60, context=ctx) as r:
                return json.load(r)
        except Exception as e:                               # noqa: BLE001
            last = e
            time.sleep(2 * (i + 1))
    print(f"   failed: {last}")
    return None


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    wp = json.load(open(os.path.join(WEB, "wikipedia.json"), encoding="utf-8"))["by_glottocode"]
    al = set(json.load(open(os.path.join(WEB, "alphabets.json"),
                            encoding="utf-8"))["by_glottocode"])
    langs = json.load(open(os.path.join(WEB, "languages.json"), encoding="utf-8"))
    F = {k: i for i, k in enumerate(langs["fields"])}
    name = {r[F["code"]]: r[F["name"]] for r in langs["rows"]}

    todo = [(gc, v) for gc, v in wp.items()
            if gc not in al and v.get("active", 0) >= MIN_ACTIVE]
    todo.sort(key=lambda t: -t[1]["articles"])
    print(f"{len(todo)} languages have their own Wikipedia, no letters yet, and "
          f"{MIN_ACTIVE}+ active editors")

    out: dict[str, dict] = {}
    thin = 0
    for k, (gc, v) in enumerate(todo):
        # Random articles rather than the front page: a main page is navigation furniture and
        # its character inventory is menus, not the language.
        u = (v["url"] + "/w/api.php?action=query&format=json&formatversion=2"
             "&generator=random&grnnamespace=0&grnlimit=12"
             "&prop=extracts&exintro=1&explaintext=1&exlimit=20")
        j = get(u)
        if not j:
            continue
        body = " ".join((p.get("extract") or "")
                        for p in ((j.get("query") or {}).get("pages") or []))
        body = " ".join(body.split())
        if len(body) < 600:
            thin += 1
            continue
        out[gc] = {"text": body[:WANT_CHARS * 2], "code": v["code"],
                   "url": v["url"], "articles": v["articles"], "active": v["active"]}
        if (k + 1) % 20 == 0:
            print(f"   {k+1}/{len(todo)} … {len(out)} with usable prose")
        time.sleep(0.2)

    json.dump({"note": "Intro text from random articles in each language's own Wikipedia, for "
                       "the observed letter tier. Not a curated alphabet.",
               "source": "Wikipedia, per-edition API (prop=extracts)",
               "licence": "CC-BY-SA-4.0", "retrieved": time.strftime("%Y-%m-%d"),
               "by_glottocode": out},
              open(os.path.join(OUT, "wikitext.json"), "w"), ensure_ascii=False)
    chars = sum(len(v["text"]) for v in out.values())
    print(f"\n{len(out)} languages, {chars:,} characters of prose "
          f"({thin} returned too little to measure)")
    for gc in list(out)[:6]:
        print(f"   {name.get(gc, gc)[:22]:24s} {out[gc]['code']:8s} "
              f"{len(out[gc]['text']):6,} chars")
