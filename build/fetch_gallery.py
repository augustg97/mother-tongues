#!/usr/bin/env python3
"""fetch_gallery.py — the artefacts, and the licence gate that lets them in.

A museum of language cannot be only tables. The Rigveda exists as a manuscript; Beowulf
exists as a burnt codex; Hittite exists as clay. Those objects are what make a dead branch of
a tree feel like something people used, and they are almost all long out of copyright.

THE GATE IS THE POINT. Every file is admitted by MACHINE, on the licence Commons reports for
that individual file — never on the assumption that "old work" means "free photograph". A
photograph of a public-domain manuscript can itself be restrictively licensed. So:

  * search Commons for each subject and read `extmetadata` per candidate;
  * ACCEPT public domain, CC0, CC-BY, CC-BY-SA (SCOPE §12 D3 permits ShareAlike);
  * REJECT NonCommercial, NoDerivatives, "fair use", and anything unreadable;
  * record the artist and the exact licence for every accepted file, and ship that with it.

This is the same per-file gate register D3 specifies for audio, built here for images first
because the images are what the room needs.

Run: python3 fetch_gallery.py
"""
from __future__ import annotations

import json
import os
import re
import ssl
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "data", "gallery")
IMG = os.path.join(HERE, "..", "web", "img", "gallery")
API = "https://commons.wikimedia.org/w/api.php"
UA = "MotherTongues/1.0 (research atlas; augustgweon@gmail.com)"

# ⚠ A LICENCE GATE CANNOT CHECK SUBJECT, and this is where that bites. Every
# `Category:<Language> language` on Commons contains `ISO 639 Icon xx.svg`, a Wikimedia project
# icon; several contain word clouds of Wikipedia statistics, community logos, and — in Cebuano's
# case — a population graph of a town in Spain. All correctly licensed, none an artefact of the
# language. So titles are filtered too.
#
# WORD BOUNDARIES MATTER HERE. A substring blocklist on "graph" throws away the Codex
# Zographensis and a photograph of an inscribed Breton sundial hosted at geograph.org.uk; on
# "chart" it throws away a chart of Assamese and Bengali letter differences, which is exactly
# the kind of thing this museum wants. Both directions were checked against the 814 objects
# already fetched: 75 rejected, and every one of the awkward keeps survived.
NOT_AN_ARTEFACT = re.compile(
    r"^ISO 639 Icon"
    r"|\bword ?cloud\b|\blogo\b|\bicon\b|\bfavicon\b"
    r"|\bflag\b|coat of arms|\bemblem\b|\bbarnstar\b|\buserbox\b|\btemplate\b"
    r"|\bmap\b|\bmaps\b|\bmapa\b|\blocator\b|\bblank map\b"
    r"|population growth|\belection\b|\bpie chart\b|\bhistogram\b|\bbar chart\b"
    r"|\bwikipedia\b|\bwikimedia\b|\bwiktionary\b|\bwikisource\b|\bwikidata\b"
    r"|\bscreenshot\b|\bdiagram\b|\bpie ?graph\b"
    r"|\bfamily tree\b|\bcladogram\b|\bvenn\b"
    # Photographs of Wikimedia community events are about the project, not the language.
    r"|\bwikiclub\b|\beditathon\b|\bedit-a-thon\b|\bmeetup\b|\bwikicon\w*"
    r"|\bwikimania\b|\bhackathon\b|\bwiki ?club\b|\bwiki ?camp\b", re.I)

# A junk upload: one token, no words, with a run of the same character. "Fdddd.jpg" was
# admitted as an object illustrating Cebuano.
JUNK_NAME = re.compile(r"^[^ ]{3,14}$")


def junk(stem: str) -> bool:
    return bool(JUNK_NAME.match(stem) and re.search(r"(.)\1{2,}", stem))

OK_PAT = re.compile(r"public domain|^pd|cc0|cc[ -]?by(?!.*(nc|nd))", re.I)
BAD_PAT = re.compile(r"\bnc\b|noncommercial|non-commercial|\bnd\b|noderiv|fair use|"
                     r"all rights reserved", re.I)

# subject -> (glottocode it illustrates, search terms). Chosen so that every major branch of
# Indo-European has an object, plus the deep-past languages the tree otherwise draws as a
# hollow ring with a date.
import json as _json
_sp = os.path.join(OUT, "subjects.json")
SUBJECTS = [tuple(x) for x in _json.load(open(_sp))] if os.path.exists(_sp) else [
]


def full_size(title: str, width: int = 1400) -> str:
    """A high-resolution URL for the lightbox, served by Commons.

    The shipped copies are downscaled to 460-640 px because the page draws them at 185-380 and
    the site has a size budget. Expanding one to fill the screen needs the real thing, and the
    real thing is already hosted: `Special:FilePath/<name>?width=N` is a documented endpoint
    that redirects to a scaled thumbnail, or to the original when it is smaller than N. Costs
    74-712 kB, paid only when a visitor actually opens an image, and it costs this repository
    nothing (rule 12 — link, do not mirror). Even a .djvu source comes back as image/jpeg.

    Computed from the title, so this needs no extra request and no stored hash.
    """
    return ("https://commons.wikimedia.org/wiki/Special:FilePath/"
            + urllib.parse.quote(title.replace(" ", "_")) + f"?width={width}")


def api(params: dict) -> dict:
    q = dict(params)
    q.update({"action": "query", "format": "json", "formatversion": "2"})
    url = API + "?" + urllib.parse.urlencode(q)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=90,
                                context=ssl.create_default_context()) as r:
        return json.load(r)


def licence_of(meta: dict) -> tuple[str, str, str] | None:
    em = meta.get("extmetadata") or {}

    def val(k):
        return re.sub(r"<[^>]+>", "", str((em.get(k) or {}).get("value", ""))).strip()
    lic = val("LicenseShortName") or val("License")
    artist = val("Artist")[:160]
    credit = val("Credit")[:160]
    if not lic:
        return None
    if BAD_PAT.search(lic):
        return None
    if not OK_PAT.search(lic):
        return None
    return lic, artist, credit


def find(terms: str, want: int = 1, skip: set[str] | None = None,
         skipnorm: set[str] | None = None) -> list[dict]:
    """Up to `want` admissible files for one subject.

    TWO ROUTES, and the second is the better one. A free-text search matches on words, so
    "Tamil manuscript" can return anything with both words near it; the licence gate checks the
    licence and cannot check whether the picture is of the right thing. A Commons CATEGORY is
    curated by people — a file is in Category:Tamil manuscripts because someone put it there —
    so any subject written as `Category:...` is read as category members instead. Prefer them.
    """
    skip = skip or set()
    skipnorm = skipnorm if skipnorm is not None else set()
    common = {"prop": "imageinfo", "iiprop": "url|extmetadata|mime|size",
              "iiurlwidth": "760"}
    try:
        if terms.startswith("Category:"):
            q = dict(common, generator="categorymembers", gcmtitle=terms,
                     gcmtype="file", gcmlimit="80")
        else:
            q = dict(common, generator="search", gsrsearch=terms, gsrnamespace="6",
                     gsrlimit="30")
        j = api(q)
    except Exception as e:                                   # noqa: BLE001
        print(f"   lookup failed for {terms!r}: {e}")
        return []
    hits = []
    for p in (j.get("query", {}) or {}).get("pages", []) or []:
        ii = (p.get("imageinfo") or [{}])[0]
        if not ii.get("thumburl") or "image" not in (ii.get("mime") or ""):
            continue
        if (ii.get("width") or 0) < 400:
            continue
        if p["title"] in skip:
            continue
        t = p["title"][5:]                            # strip the "File:" prefix
        if NOT_AN_ARTEFACT.search(t):
            continue
        stem = t.rsplit(".", 1)[0]
        if junk(stem):
            continue
        # Near-duplicates. Commons numbers a photo series 01, 02, 03; the exact-title dedupe let
        # all three in, so Korean showed the same monument twice and Navajo the same radio set
        # twice. Compare the title with trailing numbering and punctuation removed.
        norm = re.sub(r"[\W_]+", " ", re.sub(r"[\s\-_]*\d+\s*$", "", stem)).strip().lower()
        if norm and norm in skipnorm:
            continue
        skipnorm.add(norm)
        lic = licence_of(ii)
        if not lic:
            continue
        hits.append({"title": p["title"], "thumb": ii["thumburl"],
                     "page": ii.get("descriptionurl", ""), "licence": lic[0],
                     "artist": lic[1], "credit": lic[2]})
        if len(hits) >= want:
            break
    return hits


# How many files one subject may contribute, and the ceiling per language. A card with four
# objects on it is a room; a card with twenty is a contact sheet.
PER_SUBJECT = 3
PER_LANGUAGE = 5

# CATEGORIES ONLY TOP UP LANGUAGES THAT ARE SHORT. `Category:English inscriptions` contains a
# 1969 ski race photograph and a USAF fighter-wing insignia — both correctly categorised,
# because both have English words on them, and both useless in a museum of language. For a
# well-photographed Latin-script language "inscriptions" means "anything with writing on it";
# for Breton it means writing cut into stone. There is no way to tell those apart by name, so
# the rule is about sufficiency instead: once a language has this many objects from AUTHORED
# artefact queries, its categories are not queried at all. English then shows its three Beowulf
# images and stops. Languages with nothing authored still get topped up, which is the whole
# reason the categories were probed.
ENOUGH_AUTHORED = 3

# Commons serves a 760 px thumb; at 814 objects that is 179 MB, which put the site 23 MB over
# its 420 MB budget. The card's main figure renders about 380 px wide and the plate-wall thumbs
# about 185, so these caps are retina-sharp at the size they are actually drawn and nothing
# more. Downscaling here rather than by hand afterwards means the next fetch cannot reintroduce
# the problem.
WIDE_MAX = 640          # the object at the top of the card
THUMB_MAX = 460         # the plate wall


def shrink(path: str, cap: int) -> None:
    try:
        from PIL import Image
    except ImportError:
        return
    try:
        im = Image.open(path)
        im.load()
    except Exception as e:                                   # noqa: BLE001
        print(f"   unreadable, left as downloaded: {os.path.basename(path)} ({e})")
        return
    if im.mode not in ("RGB", "L"):
        im = im.convert("RGB")
    if im.width > cap:
        im = im.resize((cap, max(1, round(im.height * cap / im.width))), Image.LANCZOS)
    im.save(path, "JPEG", quality=76, optimize=True, progressive=True)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(IMG, exist_ok=True)
    manifest: dict[str, list] = {}
    seen: dict[str, set[str]] = {}
    seennorm: dict[str, set[str]] = {}
    empty = 0
    for gc, terms in SUBJECTS:
        have = manifest.setdefault(gc, [])
        if len(have) >= PER_LANGUAGE:
            continue
        # A `people` or `culture` category is context, not an artefact of the language, so it
        # contributes ONE object at most. CONTEXT_MAX in build_notable caps how many such
        # CATEGORIES are queried; without this, one of them still returned three portraits.
        if terms.startswith("Category:"):
            authored = sum(1 for o in have if not o["subject"].startswith("Category:"))
            if authored >= ENOUGH_AUTHORED:
                continue
        ctx = terms.startswith("Category:") and (terms.endswith(" people")
                                                 or terms.endswith(" culture"))
        room = min(1 if ctx else PER_SUBJECT, PER_LANGUAGE - len(have))
        hits = find(terms, want=room, skip=seen.setdefault(gc, set()),
                    skipnorm=seennorm.setdefault(gc, set()))
        if not hits:
            empty += 1
            print(f"   nothing admissible for {terms!r}")
            continue
        for hit in hits:
            seen[gc].add(hit["title"])
            idx = len(have)
            name = f"{gc}.jpg" if idx == 0 else f"{gc}-{idx}.jpg"
            dest = os.path.join(IMG, name)
            if not os.path.exists(dest):
                try:
                    req = urllib.request.Request(hit["thumb"],
                                                 headers={"User-Agent": UA})
                    with urllib.request.urlopen(
                            req, timeout=120,
                            context=ssl.create_default_context()) as r:
                        open(dest, "wb").write(r.read())
                except Exception as e:                       # noqa: BLE001
                    print(f"   download failed {name}: {e}")
                    continue
                shrink(dest, WIDE_MAX)     # ordered and re-shrunk once all are in
            have.append({"file": name, "title": hit["title"][5:],
                         "big": full_size(hit["title"][5:]),
                         "licence": hit["licence"], "artist": hit["artist"],
                         "credit": hit["credit"], "page": hit["page"],
                         "subject": terms})
            print(f"   {gc:10s} {hit['licence']:20s} {hit['title'][5:58]}")
        time.sleep(0.35)
    # THE PLATE IS CHOSEN BY SUBJECT FIRST, AND SHAPE ONLY BREAKS AN UNUSABLE ONE.
    #
    # A first attempt sorted each language's objects purely by how close they were to 4:3, and it
    # was clearly wrong the moment it was looked at: it moved the Codex Argenteus — the silver
    # Gothic Bible, the oldest substantial text in any Germanic language — out of Gothic's plate
    # position in favour of a photograph of street art, and swapped a Hittite cuneiform tablet
    # for a book illustration. The queued order already encodes the best subject signal there is:
    # the authored artefact queries run before the Commons categories.
    #
    # So the order is left alone, and shape is allowed to do exactly one thing: if the leading
    # object is a banner or a tall scroll (wider than 3:1 or narrower than 1:3) it swaps with the
    # first object that is not. On 243 languages that demoted two. Nothing is discarded, because a
    # palm-leaf manuscript is genuinely long and thin and belongs on the wall.
    def extreme(o) -> bool:
        try:
            from PIL import Image
            with Image.open(os.path.join(IMG, o["file"])) as im:
                w, h = im.size
        except Exception:                                    # noqa: BLE001
            return True
        if not w or not h:
            return True
        return (w / h) > 3.0 or (w / h) < 0.34
    demoted = 0
    for gc, objs in manifest.items():
        if len(objs) > 1 and extreme(objs[0]):
            alt = next((i for i, o in enumerate(objs) if i and not extreme(o)), None)
            if alt is not None:
                manifest[gc] = [objs[alt]] + [o for i, o in enumerate(objs) if i != alt]
                demoted += 1
        for i, o in enumerate(manifest[gc]):
            if i:
                shrink(os.path.join(IMG, o["file"]), THUMB_MAX)
    print(f"\n   {demoted} plates swapped out for being a banner or a tall scroll")

    manifest = {k: v for k, v in manifest.items() if v}
    json.dump(manifest, open(os.path.join(OUT, "gallery.json"), "w"), ensure_ascii=False,
              indent=1)
    # ⚠ AND the shipped copy. Nothing in the build ever copied the manifest out of the
    # acquisition cache into web/data — it had been done by hand once, so the site kept serving
    # a manifest from an earlier round while 814 new objects sat on disk unreferenced. Every
    # other builder writes web/data directly; this one now does too.
    json.dump(manifest, open(os.path.join(HERE, "..", "web", "data", "gallery.json"), "w"),
              ensure_ascii=False, separators=(",", ":"))
    n = sum(len(v) for v in manifest.values())
    mb = sum(os.path.getsize(os.path.join(IMG, o["file"]))
             for v in manifest.values() for o in v) / 1e6
    multi = sum(1 for v in manifest.values() if len(v) > 1)
    print(f"\n{n} objects admitted across {len(manifest)} languages "
          f"({multi} with more than one) · {empty} subjects had nothing that passed the "
          f"gate · {mb:.1f} MB")
