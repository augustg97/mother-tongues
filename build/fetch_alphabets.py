#!/usr/bin/env python3
"""fetch_alphabets.py — the letters of each language. Register D11.

WHY THIS EXISTS. Until now a card could show a language's words and not its writing system.
That is backwards for a museum: the alphabet is the first thing a visitor can *read* off a
language they do not speak. Khmer has 74 letters; Rotokas has 12; Hindi's vowels are written
twice, once as independent letters and once as marks that hang off a consonant. Those are facts
a viewer can hold, and they were absent.

TWO TIERS, AND THE DIFFERENCE BETWEEN THEM IS THE POINT.

  TIER 1 — CURATED.  Unicode CLDR `exemplarCharacters`: the set of characters a literate
  speaker of that language uses, agreed through the CLDR survey process by people who write
  the language. This is a *claim about the language*, not about a corpus. 766 locales.
  We take four of its sets, because they answer four different questions:
      exemplarCharacters  what letters the language uses
      index               the letters as a reader recites them — the alphabet proper,
                          which is why Spanish index has no `ll` and Hindi index has no
                          vowel signs: an index is what you look words up under
      numbers             the digits, which are frequently NOT 0-9
      punctuation         the marks, where the danda, the Armenian verjaket and the Greek
                          erotimatiko live
  Licence: Unicode-3.0, which permits redistribution.

  TIER 2 — OBSERVED.  For every language CLDR does not reach, the character inventory
  actually used in the prose we already ship (UDHR and other texts). This is a *measurement of
  a document*, not a curated alphabet: a short text will miss rare letters, and it will
  include any letter a loanword drags in. It is labelled as observed, with the character count
  it was drawn from, and it never claims to be the alphabet. Rule 10.

THE JOIN. CLDR is keyed by locale (mostly ISO 639-1, two letters); we are keyed by
glottocode. ISO 639-1 -> ISO 639-3 comes from Wikidata P218/P220 on one item (CC0) rather
than from memory, and ISO 639-3 -> glottocode from our own languages.json `iso` field.
Script-qualified locales (`sr-Latn`, `pa-Arab`, `ks-Deva`) are kept as separate alphabets on
the same language, because a language written in two scripts has two alphabets and showing one
of them would be the error.

Run: python3 fetch_alphabets.py
"""
from __future__ import annotations

import json
import os
import re
import ssl
import sys
import time
import unicodedata
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "data", "alphabets")
WEB = os.path.join(HERE, "..", "web", "data")
RAW = "https://raw.githubusercontent.com/unicode-org/cldr-json/main/cldr-json"
SPARQL = "https://query.wikidata.org/sparql"
UA = "MotherTongues/1.0 (research atlas of human languages; augustgweon@gmail.com)"

# The four CLDR sets we ship, and the question each one answers.
WANT = ["exemplarCharacters", "index", "numbers", "punctuation"]

SCRIPT_NAMES = {
    "Latn": "Latin", "Cyrl": "Cyrillic", "Arab": "Arabic", "Deva": "Devanagari",
    "Grek": "Greek", "Hebr": "Hebrew", "Beng": "Bengali", "Guru": "Gurmukhi",
    "Gujr": "Gujarati", "Orya": "Odia", "Taml": "Tamil", "Telu": "Telugu",
    "Knda": "Kannada", "Mlym": "Malayalam", "Sinh": "Sinhala", "Thai": "Thai",
    "Laoo": "Lao", "Tibt": "Tibetan", "Mymr": "Myanmar", "Khmr": "Khmer",
    "Ethi": "Ethiopic", "Armn": "Armenian", "Geor": "Georgian", "Hang": "Hangul",
    "Jpan": "Japanese", "Hans": "Simplified Han", "Hant": "Traditional Han",
    "Adlm": "Adlam", "Vaii": "Vai", "Nkoo": "N'Ko", "Cher": "Cherokee",
    "Cans": "Canadian Syllabics", "Olck": "Ol Chiki", "Tfng": "Tifinagh",
    "Thaa": "Thaana", "Syrc": "Syriac", "Java": "Javanese", "Bali": "Balinese",
    "Bugi": "Buginese", "Cham": "Cham", "Tale": "Tai Le", "Talu": "New Tai Lue",
    "Lana": "Tai Tham", "Mtei": "Meitei Mayek", "Saur": "Saurashtra",
    "Sund": "Sundanese", "Tirh": "Tirhuta", "Wcho": "Wancho", "Rohg": "Hanifi Rohingya",
    "Yiii": "Yi", "Plrd": "Miao", "Mroo": "Mro", "Bamu": "Bamum", "Medf": "Medefaidrin",
    "Osge": "Osage", "Gonm": "Masaram Gondi", "Gong": "Gunjala Gondi",
    "Kali": "Kayah Li", "Lisu": "Lisu", "Bhks": "Bhaiksuki", "Newa": "Newa",
    "Takr": "Takri", "Modi": "Modi", "Ahom": "Ahom", "Hmnp": "Nyiakeng Puachue Hmong",
    "Toto": "Toto", "Gara": "Garay", "Onao": "Ol Onal", "Sunu": "Sunuwar",
    "Krai": "Kirat Rai", "Tnsa": "Tangsa", "Vith": "Vithkuqi", "Kits": "Khitan",
}


def get(url: str, tries: int = 3):
    ctx = ssl.create_default_context()
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=90, context=ctx) as r:
                return json.load(r)
        except Exception as e:                       # noqa: BLE001 — retry any transport error
            last = e
            time.sleep(2 * (i + 1))
    print(f"   fetch failed {url.rsplit('/', 2)[-2:]}: {last}")
    return None


def sparql(q: str, tries: int = 4) -> list:
    url = SPARQL + "?" + urllib.parse.urlencode({"query": q, "format": "json"})
    ctx = ssl.create_default_context()
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": UA,
                              "Accept": "application/sparql-results+json"})
            with urllib.request.urlopen(req, timeout=180, context=ctx) as r:
                return json.load(r)["results"]["bindings"]
        except Exception as e:                       # noqa: BLE001
            last = e
            print(f"   attempt {i+1} failed: {type(e).__name__}: {e}")
            time.sleep(6 * (i + 1))
    raise RuntimeError(f"Wikidata query failed after {tries} attempts: {last}")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)

    print("\n1. Unicode CLDR exemplar characters (Unicode-3.0)")
    al = get(RAW + "/cldr-core/availableLocales.json")
    if not al:
        sys.exit("could not read availableLocales")
    # "modern" is EMPTY in cldr-json; "full" is the populated key. Reading the wrong one
    # returns zero locales and looks like a coverage problem.
    locales = al["availableLocales"]["full"]
    print(f"   {len(locales)} locales in the 'full' list")

    # Keep the base language and any script-qualified variant; drop region-only variants
    # (en-GB has the same letters as en), and drop `root`.
    keep = []
    for loc in locales:
        if loc == "root":
            continue
        parts = loc.split("-")
        if len(parts) == 1:
            keep.append(loc)
        elif len(parts) == 2 and len(parts[1]) == 4 and parts[1][0].isupper():
            keep.append(loc)                   # script variant: sr-Latn, pa-Arab
    print(f"   {len(keep)} distinct language/script combinations to read")

    cldr: dict[str, dict] = {}
    for k, loc in enumerate(keep):
        j = get(f"{RAW}/cldr-misc-full/main/{loc}/characters.json")
        if not j:
            continue
        ch = (((j.get("main") or {}).get(loc) or {}).get("characters") or {})
        # Cache the RAW UnicodeSet strings. Interpreting them here once cost a whole tier:
        # a bad guard in the parser silently dropped every punctuation set, and because the
        # parsed output was what got cached, finding it meant refetching 383 locales. The
        # fetcher acquires; the builder interprets; a parser fix is now a rebuild.
        rec = {w: ch[w] for w in WANT if (ch.get(w) or "").strip() not in ("", "[]")}
        # CLDR ships some locales with a literally empty exemplar set — the locale exists but
        # nobody has filled its letters in. "[]" is a truthy string, so an existence check
        # admitted it, and it then blocked the observed inventory that WAS available.
        if rec.get("exemplarCharacters"):
            cldr[loc] = rec
        if (k + 1) % 100 == 0:
            print(f"   {k+1}/{len(keep)} … {len(cldr)} with letters")
        time.sleep(0.05)
    print(f"   {len(cldr)} locales carry an exemplar set")

    print("\n2. ISO 639-1 -> ISO 639-3, from Wikidata P218/P220 (CC0)")
    rows = sparql("SELECT ?p1 ?p3 WHERE { ?i wdt:P218 ?p1 . ?i wdt:P220 ?p3 }")
    one_to_three = {}
    for b in rows:
        one_to_three.setdefault(b["p1"]["value"], b["p3"]["value"])
    print(f"   {len(one_to_three)} two-letter codes resolved to three")

    json.dump({"cldr": cldr, "iso1_to_iso3": one_to_three,
               "source": "Unicode CLDR exemplarCharacters/index/numbers/punctuation; "
                         "ISO 639-1 to 639-3 via Wikidata P218/P220",
               "licence": "Unicode-3.0 (CLDR); CC0-1.0 (Wikidata)",
               "retrieved": time.strftime("%Y-%m-%d")},
              open(os.path.join(OUT, "cldr_characters.json"), "w"), ensure_ascii=False)
    print(f"\nwrote data/alphabets/cldr_characters.json")
