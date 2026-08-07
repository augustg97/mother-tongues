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
import sys
import unicodedata
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
    # A world map captioned "orthographic projection" contains the word "map" nowhere.
    r"|orthographic projection|\bprojection\b.*\bregions?\b|\bdistribution area\b"
    r"|population growth|\belection\b|\bpie chart\b|\bhistogram\b|\bbar chart\b"
    r"|\bwikipedia\b|\bwikimedia\b|\bwiktionary\b|\bwikisource\b|\bwikidata\b"
    # Wikivoyage banners are named "<Language> phrasebook banner" and "banner" is in the
    # WRITING_TITLE allowlist, so they walked straight through it.
    r"|\bwikivoyage\b|phrasebook banner|wikimedians|user group"
    # ⚠ AN ADVERTISEMENT IS NOT AN ARTEFACT, even when it advertises books. "Books offered for
    # sale by the kilo, in Goa" is a hoarding with a phone number on it, and the text on it is
    # MARATHI, in Kolhapur, which is not Goa and not Konkani. It was the plate for Goan
    # Konkani twice over because "Books" scored it into the BEST plate class.
    r"|for sale|\bfor sale\b|\bsale\b|\bprice\b|\bper kg\b|\brs\.? ?\d|discount|shop ?front|storefront|hoarding|billboard"
    r"|\bscreenshot\b|\bdiagram\b|\bpie ?graph\b"
    # A KEYBOARD IS A PICTURE OF A COMPUTER. `WRITING_TITLE` lists "keyboard" as a writing
    # word, which let layouts through as though they were letterforms; they are not, and
    # August named them specifically. Rejected outright rather than demoted.
    r"|\bkeyboard\b|\bkeypad\b|\bklaviatur\b|\btastatur\b|key layout"
    r"|\bfamily tree\b|\bcladogram\b|\bvenn\b"
    # Photographs of Wikimedia community events are about the project, not the language.
    # Digitisation wrappers: the scanning service's own front matter, not the book.
    r"|early journal content|\bjstor\b|\bhathitrust\b|\bgoogle books\b|internet archive"
    # ⚠ A MULTI-VOLUME WORK DEFEATS A TITLE REJECTION. "The Sacred Books and Early Literature
    # of the East" is a 1917 English anthology; volumes 02 and 03 were rejected by eye and
    # Commons served volume 06 to the same card. Block the series, not the volume. These are
    # English books ABOUT a language, which is the class August named first of all.
    r"|sacred books and early literature|a history of the .* people by"
    r"|\bwikiclub\b|\beditathon\b|\bedit-a-thon\b|\bmeetup\b|\bwikicon\w*"
    r"|\bwikimania\b|\bhackathon\b|\bwiki ?club\b|\bwiki ?camp\b", re.I)

# THE GRAB-BAG NEEDS A SECOND TEST. `Category:<Language> language` is the only broad category
# still admitted, because it genuinely holds a Visayan-script page and a Book of Mormon in
# Cebuano — and also, as the contact sheets showed, a British police car, an office interior, a
# man at a laptop, a tattoo and a photograph of an egg. The category cannot be judged; the FILE
# can. So a file admitted through it must either name something written, or have a filename in
# the language's own script — a filename in Devanagari is not going to be a landscape.
WRITING_TITLE = re.compile(
    r"(script|text|inscription|manuscript|alphabet|letter|writing|written|book|page|"
    r"newspaper|poster|sign|signage|dictionar|grammar|bible|qur|gospel|codex|charter|"
    r"stele|stela|tablet|calligraph|typewriter|font|orthograph|syllabar|"
    r"primer|abecedar|plaque|epitaph|papyrus|scroll|parchment|cuneiform|hieroglyph|"
    r"lettering|banner|label|menu|placard|monument|memorial|gravestone|tombstone|"
    r"title page|cover|leaflet|poem|verse|psalm|catechism|testament|schrift|"
    r"\u00e9criture|escritura|scrittura|"
    # Commons filenames are in the uploader's language, and this filter reads filenames.
    # "Lo Batifel de la Gisen - premi\u00e9ri p\u00e1gina" is the first page of a printed work in
    # Arpitan and it failed because the English word "page" is not inside "p\u00e1gina".
    r"p[\u00e1a]gina|seite|blatt|folha|sida|blad|"
    r"livre|libro|libru|buch|kniga|kitab|"
    r"lettre|carta|brief|lettera)", re.I)
GRAB_BAG = re.compile(r"\blanguages?$", re.I)
# A category that IS about writing needs no title filter — its whole contents are the subject.
_WRITING_CAT = re.compile(r"(script|alphabet|inscription|manuscript|calligraph|literature|"
                          r"syllabar|orthograph|epigraph|codex|typograph)", re.I)
# Cultural artefacts, which August's rule admits: an object made by the people who speak it.
ARTEFACT_TITLE = re.compile(
    # ⚠ WORD BOUNDARIES, EVERY ONE OF THEM. Without them "harp" matched "harpiste" and Breton's
    # plate became a photograph of a harpist. 56 objects were admitted by substring alone.
    #
    # ⚠ AND "museum" IS NOT AN ARTEFACT WORD. It let in every "COLLECTIE TROPENMUSEUM …" file,
    # which is a colonial photographic archive: weddings, riders fording a river, a rickshaw
    # puller, portraits of groups of men. A photograph taken IN a museum is not an object.
    #
    # Non-English words are here for the same reason the writing list has them — Commons
    # filenames are in the uploader's language, and the genuine Tropenmuseum artefacts are
    # labelled "houten beeld", "aardewerk", "muziekinstrument".
    r"\b(pottery|pots?|vessels?|bowls?|jars?|urns?|carvings?|carved|sculptures?|statues?|"
    r"statuettes?|figurines?|masks?|textiles?|weaving|woven|embroider\w*|baskets?|beadwork|"
    r"amulets?|talismans?|drums?|flutes?|horns?|lyres?|harps?|coins?|seals?|jewell?ery|"
    r"pendants?|brooch(?:es)?|looms?|shields?|artefacts?|artifacts?|relics?|regalia|"
    # postage stamps carry the language on them; rings and ornaments are worked objects. Both
    # were lost when "museum" went, and both are exactly what August's rule admits.
    r"stamps?|rings?|(?:hals|oor|pols|arm|neck|ear|wrist|finger)ring|ornaments?|bracelets?|"
    r"necklaces?|earrings?|beads?|"
    r"headdress(?:es)?|"
    r"beeld|aardewerk|muziekinstrument|weefsel|mand|masker|"
    r"skulptur|keramik|gef\u00e4\u00df|schmuck|"
    r"c\u00e9ramique|poterie|sculpture|masque|"
    r"cer\u00e1mica|escultura|m\u00e1scara|tejido)\b", re.I)


def mostly_non_latin(t: str) -> bool:
    ls = [c for c in t if unicodedata.category(c)[0] == "L"]
    return bool(ls) and sum(1 for c in ls if not c.isascii()) / len(ls) > 0.3


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
# TWO queues, written independently by build_notable.py (languages) and build_families.py
# (families). One shared file made them order-dependent, and the wrong order silently deleted
# every family plate from the manifest.
SUBJECTS = []
for _f in ("subjects_languages.json", "subjects_families.json"):
    _p = os.path.join(OUT, _f)
    if os.path.exists(_p):
        SUBJECTS += [tuple(x) for x in _json.load(open(_p))]
# --part i/n runs one slice of the queue. A full pass is ~1,500 Commons queries at the backed-off
# rate, which is longer than a single foreground run survives here; the title-keyed cache makes
# slices safe, because a slice writes no manifest and no slot files.
if "--part" in sys.argv:
    _i, _n = (int(x) for x in sys.argv[sys.argv.index("--part") + 1].split("/"))
    SUBJECTS = [s for k, s in enumerate(SUBJECTS) if k % _n == _i - 1]
    print(f"part {_i}/{_n}: {len(SUBJECTS)} subjects")

if not SUBJECTS:
    raise SystemExit("fetch_gallery: no subject queue — run build_notable.py and "
                     "build_families.py first")


# ⚠ IMAGES ARE CACHED UNDER THEIR TITLE, NOT UNDER THE POSITIONAL SLOT THEY WILL OCCUPY.
# Slot names — gc.jpg, gc-1.jpg — move whenever an audit retires an object or the plate ordering
# changes, and a download written straight into a slot has twice now left the wrong picture under
# a caption. Worse, a run REFUSED by the shrink guard still downloaded: the manifest stayed put
# while the files under it changed, so Hakka Chinese was captioned as a remittance letter and
# showing a migration map. The cache is keyed to what the file IS; slots are assigned only when
# the manifest is actually written, and a refused run therefore changes nothing a reader sees.
CACHE = os.path.join(OUT, "cache")
os.makedirs(CACHE, exist_ok=True)
_served_from_cache = False
QCACHE = os.path.join(OUT, "qcache")
os.makedirs(QCACHE, exist_ok=True)


def _cache_name(title: str) -> str:
    import hashlib
    return hashlib.sha1(title.encode("utf-8")).hexdigest()[:20] + ".jpg"


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


# Titles rejected BY EYE, from data/gallery/audit/. The rules above catch classes — project
# icons, flags, maps, people categories, files with no writing word in their name. What they
# cannot catch is a correctly-licensed, correctly-categorised photograph of a pile of fossils
# standing in for the Afar language, a Kushan-empire map for Bactrian, or a JSTOR cover page for
# Bai. Those were found by laying the collection out as contact sheets and looking at it, and the
# verdicts live in a file so the next fetch does not undo the audit.
_rj = os.path.join(HERE, "..", "data", "gallery", "rejected.json")
_rjd = _json.load(open(_rj, encoding="utf-8")) if os.path.exists(_rj) else {}

# What each image file on disk is currently a copy of, read from the last manifest. Any slot whose
# occupant has changed since then must be downloaded again rather than trusted.
_gp = os.path.join(OUT, "gallery.json")
PREV_TITLE = {}
if os.path.exists(_gp):
    for _objs in _json.load(open(_gp, encoding="utf-8")).values():
        for _o in _objs:
            PREV_TITLE[_o["file"]] = _o["title"]
REJECTED = set(_rjd.get("titles") or {})
# (glottocode, subject) pairs where an object was rejected by eye. Handing back the NEXT
# photograph from the same category is how Inari Saami went from a snowy roadside to a
# photograph of Kobe Bryant: the pool is weak, not the individual file. A retired pair is not
# queried again, and the slot simply stays empty.
EXHAUSTED = {tuple(x) for x in (_rjd.get("exhausted") or [])}
# ⚠ KEYED BY GLOTTOCODE. 13 of these were once written with the language's DISPLAY NAME,
# because that is what the audit contact sheet prints, and they matched nothing at all —
# so a rejected subject went straight back to Commons and returned the next thing in it,
# which is the exact failure retirement exists to prevent. A bad key is now fatal.
# Shape, not membership: a retired pair whose language has since dropped out of the queue is
# harmless, but 'Cameroon Pidgin' where 'came1254' belongs is a silent no-op.
_GC = re.compile(r'^[a-z]{4}\d{4}$')
_bad_keys = sorted({a for a, _ in EXHAUSTED if not _GC.match(a)})
if _bad_keys:
    raise SystemExit("fetch_gallery: rejected.json['exhausted'] keys are display names, "
                     "not glottocodes: " + ", ".join(_bad_keys))


def api(params: dict) -> dict:
    q = dict(params)
    q.update({"action": "query", "format": "json", "formatversion": "2"})
    url = API + "?" + urllib.parse.urlencode(q)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=90,
                                context=ssl.create_default_context()) as r:
        return json.load(r)


def dedupe_twice(s: str) -> str:
    """The Commons Artist field is HTML, and a common pattern is the same name in two spans.

    Stripping the tags then leaves "Unknown authorUnknown author" on the caption. Only an exact
    doubling is collapsed, so a genuine two-name credit is untouched.
    """
    s = re.sub(r"\s+", " ", s).strip()
    n = len(s)
    if n > 3 and n % 2 == 0 and s[:n // 2] == s[n // 2:]:
        return s[:n // 2].strip()
    return s


def licence_of(meta: dict) -> tuple[str, str, str] | None:
    em = meta.get("extmetadata") or {}

    def val(k):
        return re.sub(r"<[^>]+>", "", str((em.get(k) or {}).get("value", ""))).strip()
    lic = val("LicenseShortName") or val("License")
    artist = dedupe_twice(val("Artist"))[:160]
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
    # THE SEARCH RESULT IS CACHED TOO, keyed by subject. A full pass is ~1,560 Commons queries at
    # the backed-off rate, which is longer than one run survives here, and repeating them to
    # rebuild a manifest is both slow and rude to the source. The cache holds the raw API reply,
    # so the filtering below still runs fresh against the current reject list. Delete
    # data/gallery/qcache to force real queries.
    global _served_from_cache
    _qp = os.path.join(QCACHE, _cache_name("Q:" + terms)[:-4] + ".json")
    j = None
    if os.path.exists(_qp):
        try:
            j = json.load(open(_qp, encoding="utf-8"))
        except Exception:                                    # noqa: BLE001
            j = None
    _served_from_cache = j is not None
    if j is None:
        try:
            if terms.startswith("Category:"):
                q = dict(common, generator="categorymembers", gcmtitle=terms,
                         gcmtype="file", gcmlimit="80")
            else:
                q = dict(common, generator="search", gsrsearch=terms, gsrnamespace="6",
                         gsrlimit="30")
            j = api(q)
        except Exception as e:                               # noqa: BLE001
            print(f"   lookup failed for {terms!r}: {e}")
            return []
        json.dump(j, open(_qp, "w"), ensure_ascii=False)
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
        if t in REJECTED:
            continue
        if NOT_AN_ARTEFACT.search(t):
            continue
        stem = t.rsplit(".", 1)[0]
        if junk(stem):
            continue
        # THE GRAB-BAG TEST, and it now covers the language's own bare category too.
        # `Category:<Language> languages` was always a grab-bag. `Category:Akha` is worse: it is
        # a category about the Akha PEOPLE, and it returned three portraits. `Category:Cheyenne`
        # returned two nineteenth-century battle paintings; `Category:Haitian Creole` returned
        # three photographs of individuals; `Category:Kabyle` returned a map. So a file admitted
        # through a category that is not explicitly about writing must name something written,
        # or carry a filename in the language's own script.
        #
        # Cultural artefacts survive this by name — pots, carvings, instruments read as objects
        # and August's rule allows them; a photograph of a person or a town does not.
        bare_cat = terms.startswith("Category:") and not _WRITING_CAT.search(terms)
        if (GRAB_BAG.search(terms) or bare_cat) and not (WRITING_TITLE.search(stem)
                                                         or ARTEFACT_TITLE.search(stem)
                                                         or mostly_non_latin(stem)):
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
    # ⚠ COMPOSITE ON WHITE, do not just convert. A transparent PNG or SVG converted straight to
    # RGB gets black wherever it was transparent, and every one of the 39 images this destroyed
    # was among the best in the collection: the Cherokee syllabary chart, the Rohingya alphabet,
    # "Nepali" written in Devanagari, the Shang oracle-bone glyph for tiger. They rendered as
    # solid black rectangles on their cards. Alphabet charts are drawn as dark strokes on
    # nothing, which is exactly the case a naive convert ruins.
    if im.mode in ("RGBA", "LA", "PA") or (im.mode == "P" and "transparency" in im.info):
        im = im.convert("RGBA")
        bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
        im = Image.alpha_composite(bg, im).convert("RGB")
    elif im.mode not in ("RGB", "L"):
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
        if (gc, terms) in EXHAUSTED:
            continue
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
            dest = os.path.join(CACHE, _cache_name(hit["title"][5:]))
            # ⚠ THE CACHE IS KEYED TO THE SLOT, AND THE SLOT'S OCCUPANT CHANGES. File names are
            # positional — gc.jpg, gc-1.jpg — so the moment an audit retires an object, the next
            # object slides into its slot and `os.path.exists` says "already have it". The card
            # then shows the REJECTED image under the replacement's caption, which is worse than
            # either of them alone. Tunisian Arabic was captioned as a film festival poster and
            # displaying a tiled Arabic inscription that had been rejected minutes earlier.
            # So: cache on the TITLE the slot currently holds, not on the slot.
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
                # the cache keeps a generous copy; slots are shrunk when written, below
            have.append({"file": name, "title": hit["title"][5:],
                         "big": full_size(hit["title"][5:]),
                         "licence": hit["licence"], "artist": hit["artist"],
                         "credit": hit["credit"], "page": hit["page"],
                         "subject": terms})
            print(f"   {gc:10s} {hit['licence']:20s} {hit['title'][5:58]}")
        # Commons rate-limits, and a long queue is exactly when it does. 1,802 subjects at
        # 0.35s got 429s and doubled the number of subjects returning nothing, which cost 43
        # languages their objects. Back off as the queue grows.
        if not _served_from_cache:
            time.sleep(0.35 if len(SUBJECTS) < 1000 else 0.6)
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
    # AND THE PLATE HAS A HIGHER BAR THAN THE WALL. August's rule, and it is the right one: the
    # main image for a language should be WRITING, a book, a cultural artefact or a landmark
    # associated with it. A street sign or an advertisement is real evidence of a language in use
    # and belongs in the card — but not as the first thing a visitor sees, because it says
    # "somebody printed this here" rather than "this is what the language looks like".
    #
    # So a plate is scored, and a lower score wins the front position. Nothing is discarded.
    PLATE_BEST = re.compile(
        r"(manuscript|inscription|codex|tablet|stele|stela|papyrus|scroll|palm.?leaf|"
        r"alphabet|syllabar|script|abecedar|primer|dictionar|grammar|gospel|bible|qur|"
        r"testament|charter|epitaph|calligraph|folio|page|book|letter|poem|verse)", re.I)
    PLATE_WEAK = re.compile(
        r"(sign|signage|signboard|billboard|placard|poster|advert|banner|plaque|label|"
        r"menu|shopfront|storefront|graffiti|mural|sticker|keyboard|layout|logo)", re.I)

    def plate_rank(o) -> int:
        # ⚠ WEAK IS TESTED FIRST. Checking PLATE_BEST first meant one writing word anywhere in a
        # title outranked everything else in it, so a billboard reading "Books offered for sale
        # by the kilo" scored as a book and led the card.
        ttl = o.get("title", "")
        if PLATE_WEAK.search(ttl):
            return 2
        if PLATE_BEST.search(ttl):
            return 0
        return 1

    def extreme(o) -> bool:
        # ⚠ READ THE CACHE, NOT THE SLOT. Slot names are assigned during the fetch loop and the
        # subject reorder above moves objects without renaming them, so o["file"] points at
        # wherever this object USED to sit. This check was opening a different image entirely:
        # for Udmurt it reordered the 1882 alphabet to the front, then measured a 3.43-ratio
        # chart still sitting in slot -4, declared the leader a banner, and swapped the alphabet
        # back out for a photograph of a media-school class. Slots are only truthful after the
        # manifest is written; the cache is truthful throughout.
        try:
            from PIL import Image
            src = os.path.join(CACHE, _cache_name(o["title"]))
            if not os.path.exists(src):
                src = os.path.join(IMG, o["file"])
            with Image.open(src) as im:
                w, h = im.size
        except Exception:                                    # noqa: BLE001
            return True
        if not w or not h:
            return True
        return (w / h) > 3.0 or (w / h) < 0.34
    demoted = 0
    for gc, objs in manifest.items():
        if len(objs) < 2:
            continue
        # 1. subject: writing and artefacts to the front, signs and adverts to the back.
        best = min(range(len(objs)), key=lambda i: (plate_rank(objs[i]), i))
        if best:
            objs = [objs[best]] + [o for i, o in enumerate(objs) if i != best]
            manifest[gc] = objs
            demoted += 1
        # 2. shape: only ever breaks an unusable leader, AND ONLY FOR AN EQUALLY GOOD SUBJECT.
        # A wide crop of the Book of Henryków — the first sentence written in Polish — is 3.99:1
        # and was being swapped out for a photograph of a MONUMENT to the Book of Henryków.
        # A strip of the manuscript is still the manuscript; a statue of it is not. So a shape
        # swap may only promote something whose subject rank is no worse than the leader's.
        if extreme(objs[0]):
            lead_rank = plate_rank(objs[0])
            alt = next((i for i, o in enumerate(objs)
                        if i and not extreme(o) and plate_rank(o) <= lead_rank), None)
            if alt is not None:
                manifest[gc] = [objs[alt]] + [o for i, o in enumerate(objs) if i != alt]
                demoted += 1
        # shrinking happens when the slot is written, below — the cache keeps full size.
    print(f"\n   {demoted} plates swapped out for being a banner or a tall scroll")

    manifest = {k: v for k, v in manifest.items() if v}

    # ⚠ THE MANIFEST IS REBUILT FROM SCRATCH EVERY RUN, so anything that falls out of the subject
    # queue disappears from the site even though its file is still on disk, licence-verified and
    # already audited by eye. That is how 22 family plates — the Rosetta Stone, the Nsibidi
    # scroll, the Kedukan Bukit inscription — vanished in one run when two builders ran in the
    # wrong order. The queue is split in two now so that particular cause is gone, but a
    # transient Commons failure would do the same thing just as quietly.
    #
    # So: a run that LOSES ground stops and says what it lost. --shrink to accept it (an audit
    # pass that retires bad objects is a legitimate shrink and passes it deliberately).
    # A SLICE NEVER WRITES. It exists only to warm the title-keyed cache, so it must stop before
    # the guard, before the manifest and before the slot files — a partial queue always looks
    # like a catastrophic shrink, because it is one.
    if "--part" in sys.argv:
        print("   slice complete — cache warmed, manifest and slots untouched")
        sys.exit(0)

    # A CEILING ON WHAT --shrink WILL ACCEPT. The flag exists for an audit that retires a
    # handful of bad objects. It was once passed for an expected loss of 6 languages and then
    # left on for a run that lost 43, because a throttled fetch looks exactly like a small
    # intended shrink until you read the list. Past the ceiling, --shrink is not enough.
    SHRINK_CEILING = 15
    prev_p = os.path.join(OUT, "gallery.json")
    if os.path.exists(prev_p) and "--shrink" not in sys.argv:
        prev = json.load(open(prev_p, encoding="utf-8"))
        gone = sorted(set(prev) - set(manifest))
        n_prev, n_now = sum(len(v) for v in prev.values()), sum(len(v) for v in manifest.values())
        if gone or n_now < n_prev:
            print(f"\n   REFUSING TO WRITE: {n_prev} objects across {len(prev)} languages became "
                  f"{n_now} across {len(manifest)}.")
            if gone:
                print(f"   {len(gone)} languages lost every object: {', '.join(gone[:12])}"
                      + (" …" if len(gone) > 12 else ""))
            print("   The old manifest is untouched. Re-run once more in case Commons was "
                  "flaking; pass --shrink if the loss is intended.")
            sys.exit(1)
    elif os.path.exists(prev_p):
        prev = json.load(open(prev_p, encoding="utf-8"))
        gone = sorted(set(prev) - set(manifest))
        if len(gone) > SHRINK_CEILING and "--force-shrink" not in sys.argv:
            print(f"\n   REFUSING TO WRITE even with --shrink: {len(gone)} languages lost every "
                  f"object, over the ceiling of {SHRINK_CEILING}.")
            print(f"   {', '.join(gone[:14])}" + (" …" if len(gone) > 14 else ""))
            print("   That is the shape of a throttled fetch, not an audit. Re-run; pass "
                  "--force-shrink only if it really is intended.")
            sys.exit(1)

    # ONLY NOW are slot files written, from the title-keyed cache, with the ordering settled.
    # Everything above this point has touched nothing a reader sees.
    import shutil as _sh
    for gc, objs in manifest.items():
        for i, o in enumerate(objs):
            slot = f"{gc}.jpg" if i == 0 else f"{gc}-{i}.jpg"
            src = os.path.join(CACHE, _cache_name(o["title"]))
            if os.path.exists(src):
                _sh.copyfile(src, os.path.join(IMG, slot))
                shrink(os.path.join(IMG, slot), WIDE_MAX if i == 0 else THUMB_MAX)
            o["file"] = slot
    live = {f"{gc}.jpg" if i == 0 else f"{gc}-{i}.jpg"
            for gc, objs in manifest.items() for i in range(len(objs))}
    for f in os.listdir(IMG):
        if f not in live:
            os.remove(os.path.join(IMG, f))

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
