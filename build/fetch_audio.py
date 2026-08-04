#!/usr/bin/env python3
"""fetch_audio.py — recordings of people speaking, keyed by catalogue and not by filename.
Register D3.

WHY THIS IS BUILT THE WAY IT IS. The first attempt at audio in this project matched recordings
to languages by looking at their filenames. It returned a Spanish recording as Basque and a file
called `Japanese toilet.ogg` as Hindi-Urdu. That version was withheld and never shipped, and the
lesson is the reason for the shape of this one: **the language must come from a catalogue key**.

Lingua Libre supplies exactly that. Every recording is filed on Wikimedia Commons under
`Category:Lingua Libre pronunciation-<iso639-3>` — the ISO code is *in the category name*, put
there by the recording pipeline, not inferred by us. There are over 500 such categories holding
around 1.65 million recordings, each made by a speaker who sat down at a recording booth to make
it. That is a catalogue, and it is the join.

WE LINK, WE DO NOT MIRROR. Rule 12: ship what is clean, state the coverage, name the archive,
link out rather than mirror. The audio streams from Commons, so 1.65 million recordings cost this
repository nothing and every play is served by the archive that holds the consent.

THE WORD IS PART OF THE DATUM. A Lingua Libre filename is
`LL-Q<wikidata id> (<iso>)-<speaker>-<word>.wav`, so the word being spoken is recoverable, and a
recording of a known word is worth far more than an unlabelled clip. Better still: where the
spoken word is one this card ALREADY SHOWS in writing, the two are joined, and the visitor can
see the word and hear it. That match is attempted first and reported.

Every file is still admitted on the licence Commons reports for it individually — Lingua Libre is
mostly CC-BY-SA 4.0 with some CC0, and "mostly" is not a licence.

Run: python3 fetch_audio.py
"""
from __future__ import annotations

import json
import os
import re
import ssl
import time
import unicodedata
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
OUT = os.path.join(ROOT, "data", "audio")
WEB = os.path.join(ROOT, "web", "data")
API = "https://commons.wikimedia.org/w/api.php"
UA = "MotherTongues/1.0 (research atlas of human languages; augustgweon@gmail.com)"

PREFIX = "Lingua Libre pronunciation-"
PER_LANGUAGE = 6          # how many recordings a card offers
CANDIDATES = 120          # how many files to look at per language before choosing

# ⚠ SORT ORDER IS A CONTENT DECISION. categorymembers defaults to alphabetical by filename, and
# taking the first six gave English `&`, `'tis`, `'twixt` and `'twere`; Basque six bare suffixes
# (-ak, -ra, -etara); Hindi two Latin-script personal names and a prefix. Ordering by upload time
# instead samples across whole recording sessions, which are word lists rather than a dictionary's
# first page.
SORT = {"gcmsort": "timestamp", "gcmdir": "desc"}

# What is not a word to put in a case. An affix is not a word, a bare number is not a word, and
# a string with no letters at all is punctuation.
AFFIX = re.compile(r"^[-‐‑–—]|[-‐‑–—]$")

# Ordering by upload time samples whole recording sessions, and a session has a theme: English
# came back as six country names, Russian as six botanical binomials. Both correct, both dull, and
# a card leading with "Democratic Republic of the Congo" tells a visitor nothing about English.
# So candidates are RANKED rather than taken in order — lowest score first.
def rank(word: str, in_text: bool) -> tuple:
    if in_text:
        return (0, len(word))          # a word the visitor can also read on this card
    toks = word.split()
    multi = len(toks) > 1
    first = word[0]
    # A capital initial in a cased script usually means a proper noun; a script with no case
    # distinction is unaffected, which is why this tests the character rather than the language.
    proper = first.isupper() and first.lower() != first
    return (1 + (2 if multi else 0) + (1 if proper else 0), len(word))


# CLDR and Wikipedia needed the same bridge and for the same reason: Lingua Libre files some
# recordings under an ISO MACROLANGUAGE (`ara`, `fas`, `aze`, `est`, `hrv`, `mlg`, `mon`, `msa`,
# `nep`, `nob`, `kur`, `kok`, `ful`), which Glottolog does not have. Keyed by exact Glottolog NAME
# and checked by machine, so a recording cannot land on a language nobody made it in.
AUDIO_BRIDGE = {
    "ara": "Standard Arabic", "fas": "Western Farsi", "aze": "North Azerbaijani",
    "est": "Estonian", "hrv": "Serbian-Croatian-Bosnian", "srp": "Serbian-Croatian-Bosnian",
    "bos": "Serbian-Croatian-Bosnian", "mlg": "Plateau Malagasy", "mon": "Halh Mongolian",
    "msa": "Standard Malay", "nep": "Nepali", "nob": "Norwegian", "nno": "Norwegian",
    "kur": "Northern Kurdish", "kok": "Goan Konkani", "ful": "Pular",
    "swa": "Swahili", "uzb": "Northern Uzbek", "orm": "West Central Oromo",
    "pus": "Northern Pashto", "yid": "Eastern Yiddish", "grn": "Paraguayan Guaraní",
    "que": "Cusco Quechua", "zha": "Yongbei Zhuang", "gsc": "Occitan",
    "auv": "Occitan", "lnc": "Occitan", "prv": "Occitan",
    "sqi": "Northern Tosk Albanian", "zho": "Mandarin Chinese", "zza": "Dimli",
    "kom": "Komi-Zyrian", "bik": "Coastal-Naga Bikol", "twi": "Akan",
    "ajp": "Levantine Arabic",
}

OK_PAT = re.compile(r"public domain|^pd|cc0|cc[ -]?by(?!.*(nc|nd))", re.I)
BAD_PAT = re.compile(r"\bnc\b|noncommercial|non-commercial|\bnd\b|noderiv|fair use|"
                     r"all rights reserved", re.I)

# LL-Q9176 (kor)-HappyMidnight-1978(천구백칠십팔).wav
NAME = re.compile(r"^LL-Q\d+\s*\((?P<iso>[a-z]{2,3})\)-(?P<speaker>.+?)-(?P<word>.+)$")


def api(params: dict, tries: int = 4) -> dict:
    q = dict(params)
    q.update({"action": "query", "format": "json", "formatversion": "2"})
    url = API + "?" + urllib.parse.urlencode(q)
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=90,
                                        context=ssl.create_default_context()) as r:
                return json.load(r)
        except Exception as e:                               # noqa: BLE001
            last = e
            # Commons answers 429 to a fast loop; backing off is part of using the archive
            # politely, and the first version of this script tripped it.
            time.sleep(3 * (i + 1))
    print(f"   API failed: {last}")
    return {}


def licence_of(ii: dict):
    em = ii.get("extmetadata") or {}

    def val(k):
        return re.sub(r"<[^>]+>", "", str((em.get(k) or {}).get("value", ""))).strip()
    lic = val("LicenseShortName") or val("License")
    if not lic or BAD_PAT.search(lic) or not OK_PAT.search(lic):
        return None
    return lic, val("Artist")[:120]


def fold(s: str) -> str:
    """Compare words without being defeated by case or by combining marks."""
    s = unicodedata.normalize("NFC", s).strip().lower()
    return re.sub(r"[\s​-‏]+", "", s)


def all_categories() -> list[tuple[str, str, int]]:
    """(category, iso639-3, file count) for every Lingua Libre language category."""
    out, cont = [], None
    while True:
        q = {"list": "allcategories", "acprefix": PREFIX, "aclimit": "500",
             "acprop": "size"}
        if cont:
            q["acfrom"] = cont
        j = api(q)
        rows = (j.get("query", {}) or {}).get("allcategories", []) or []
        if not rows:
            break
        for c in rows:
            name = c.get("category", "")
            n = int(c.get("files") or 0)
            suffix = name[len(PREFIX):] if name.startswith(PREFIX) else ""
            # ONLY a bare three-letter code. Commons also holds
            # "Lingua Libre pronunciation-Baleswari Odia pronunciation", which is a variety
            # rather than a language and has no ISO code to join on.
            if re.fullmatch(r"[a-z]{3}", suffix) and n > 0:
                out.append((name, suffix, n))
        nxt = (j.get("continue") or {}).get("accontinue")
        if not nxt:
            break
        cont = nxt
        time.sleep(0.2)
    return out


def files_in(cat: str, limit: int) -> list[dict]:
    q = {"generator": "categorymembers", "gcmtitle": "Category:" + cat,
         "gcmtype": "file", "gcmlimit": str(min(limit, 500)), "prop": "imageinfo",
         "iiprop": "url|extmetadata|mime|size"}
    q.update(SORT)
    j = api(q)
    return (j.get("query", {}) or {}).get("pages", []) or []


def word_ok(w: str, latin_ok: bool) -> bool:
    """Is this a word a museum would put in a case?"""
    if not w or len(w) > 44:
        return False
    if AFFIX.search(w):
        return False                          # -ak, -etara: an affix, not a word
    letters = [c for c in w if unicodedata.category(c)[0] == "L"]
    if len(letters) < 2:
        return False                          # &, (NHC), 1978: not a word
    if not latin_ok and all(c.isascii() for c in letters):
        return False                          # a Latin-script name inside a Devanagari language
    return True


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    langs = json.load(open(os.path.join(WEB, "languages.json"), encoding="utf-8"))
    F = {k: i for i, k in enumerate(langs["fields"])}
    by_iso, name = {}, {}
    for r in langs["rows"]:
        name[r[F["code"]]] = r[F["name"]]
        if r[F["iso"]]:
            by_iso.setdefault(r[F["iso"]], r[F["code"]])

    # THE MATCH TARGET: the words each card already shows in the language's OWN SPELLING.
    # words.json cannot serve — it holds IPA transcriptions of ASJP's core concepts, and
    # Lingua Libre filenames carry spellings. (words.json also has no `orth` key at all: the
    # "Words, as written" tier that tree.js renders was never built, so that branch has never
    # fired. Recorded here as a real gap rather than worked around silently.)
    #
    # texts.json does serve. It holds the UDHR in each language's own script, so a recording of
    # a word that appears in the passage on the card can be joined to it, and the visitor can
    # read the word in context and then hear it.
    import html as _html
    tpath = os.path.join(WEB, "texts.json")
    intext: dict[str, set] = {}
    if os.path.exists(tpath):
        for gc, rec in (json.load(open(tpath, encoding="utf-8"))
                        .get("by_glottocode") or {}).items():
            body = " ".join(_html.unescape(v) for _, v in (rec.get("b") or []))
            toks = re.split(r"[^\w\u0080-\uffff]+", body)
            intext[gc] = {fold(t) for t in toks if len(t) > 2}

    # Which script each language actually writes in, so a Latin-script personal name can be
    # refused for a language that does not use Latin letters.
    scripts: dict[str, str] = {}
    if os.path.exists(tpath):
        for gc, rec in (json.load(open(tpath, encoding="utf-8"))
                        .get("by_glottocode") or {}).items():
            if rec.get("s"):
                scripts[gc] = rec["s"]

    # the bridge, resolved by exact Glottolog name and refused if it does not match exactly one
    import csv as _csv
    gnames: dict[str, list] = {}
    with open(os.path.join(ROOT, "data", "glottolog", "languages.csv"),
              newline="", encoding="utf-8") as f:
        for r in _csv.DictReader(f):
            if r["Level"] == "language":
                gnames.setdefault(r["Name"], []).append(r["ID"])
    for iso3, nm in AUDIO_BRIDGE.items():
        hit = gnames.get(nm) or []
        if len(hit) != 1:
            raise SystemExit(f"AUDIO_BRIDGE {iso3!r} -> {nm!r} matched {len(hit)} languages")
        by_iso.setdefault(iso3, hit[0])

    # RESUMABLE. A full pass is 298 category queries and takes most of an hour; adding one
    # bridged language should not cost that again. Pass --fresh to ignore what is already there.
    import sys as _sys
    prior: dict[str, dict] = {}
    apath = os.path.join(WEB, "audio.json")
    if "--fresh" not in _sys.argv and os.path.exists(apath):
        prior = (json.load(open(apath, encoding="utf-8")).get("by_glottocode") or {})
        if prior:
            print(f"resuming: {len(prior)} languages already have recordings "
                  f"(pass --fresh to redo them)")

    print("1. Lingua Libre language categories on Commons")
    cats = all_categories()
    tot = sum(n for _, _, n in cats)
    print(f"   {len(cats)} categories keyed by ISO 639-3 · {tot:,} recordings")
    reach = [(c, iso, n) for c, iso, n in cats if iso in by_iso]
    print(f"   {len(reach)} of them are a language in this build "
          f"({sum(n for _, _, n in reach):,} recordings)")
    missing = sorted(iso for _, iso, _ in cats if iso not in by_iso)
    if missing:
        print(f"   {len(missing)} ISO codes have recordings but no language-level match here: "
              f"{' '.join(missing[:30])}" + (" …" if len(missing) > 30 else ""))

    print("\n2. admitting recordings, licence by licence")
    out: dict[str, dict] = {}
    matched_langs = 0
    rejected = 0
    skipped_words = 0
    reach.sort(key=lambda t: -t[2])
    for k, (cat, iso, n) in enumerate(reach):
        gc = by_iso[iso]
        if gc in prior:
            out[gc] = prior[gc]
            continue
        want = intext.get(gc) or set()
        latin_ok = scripts.get(gc, "Latn") == "Latn"
        picked: list[dict] = []
        matched: list[dict] = []
        seen_words: set[str] = set()
        for p in files_in(cat, CANDIDATES):
            ii = (p.get("imageinfo") or [{}])[0]
            if "audio" not in (ii.get("mime") or "") and \
               not (ii.get("url") or "").lower().endswith((".wav", ".ogg", ".mp3", ".flac")):
                continue
            lic = licence_of(ii)
            if not lic:
                rejected += 1
                continue
            stem = p["title"][5:].rsplit(".", 1)[0]
            m = NAME.match(stem)
            if not m:
                continue
            # ⚠ The category says which language this is. The filename is used ONLY for the
            # word and the speaker — never to decide the language, which is the mistake that
            # returned a Spanish recording as Basque the first time this was attempted.
            if m.group("iso") != iso:
                continue
            word = m.group("word").strip()
            if not word_ok(word, latin_ok):
                skipped_words += 1
                continue
            if fold(word) in seen_words:
                continue
            seen_words.add(fold(word))
            rec = {"w": word, "url": ii["url"], "speaker": m.group("speaker")[:60],
                   "licence": lic[0], "artist": lic[1],
                   "page": ii.get("descriptionurl", "")}
            if fold(word) in want:
                rec["intext"] = True          # this word appears in the passage on the card
                matched.append(rec)
            else:
                picked.append(rec)
        chosen = sorted(matched + picked,
                        key=lambda r: rank(r["w"], bool(r.get("intext"))))[:PER_LANGUAGE]
        if not chosen:
            continue
        if matched:
            matched_langs += 1
        out[gc] = {"items": chosen, "available": n, "category": cat, "iso": iso}
        if (k + 1) % 40 == 0:
            print(f"   {k+1}/{len(reach)} … {len(out)} languages")
        time.sleep(0.15)

    n_rec = sum(len(v["items"]) for v in out.values())
    json.dump({"note": "Recordings made by speakers at Lingua Libre booths, streamed from "
                       "Wikimedia Commons rather than mirrored here. The language of each "
                       "recording comes from the Commons category it is filed under, which "
                       "carries the ISO 639-3 code; the filename is used only for the word "
                       "and the speaker.",
               "source": "Lingua Libre via Wikimedia Commons",
               "retrieved": time.strftime("%Y-%m-%d"),
               "languages": len(out), "recordings": n_rec,
               "available": sum(v["available"] for v in out.values()),
               "by_glottocode": out},
              open(os.path.join(WEB, "audio.json"), "w"), ensure_ascii=False,
              separators=(",", ":"))
    json.dump(out, open(os.path.join(OUT, "audio.json"), "w"), ensure_ascii=False)

    print(f"\n{n_rec:,} recordings across {len(out)} languages "
          f"(was 15) · {rejected} files rejected on licence · {skipped_words:,} candidates "
          f"rejected as affixes, numbers, punctuation or wrong-script names")
    print(f"   {matched_langs} languages have at least one recording of a word that appears "
          f"in the passage shown on their card")
    top = sorted(out.items(), key=lambda kv: -kv[1]["available"])[:8]
    for gc, v in top:
        print(f"   {name.get(gc, gc):26s} {len(v['items'])} shown of "
              f"{v['available']:,} in the archive")
