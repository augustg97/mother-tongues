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


def find(terms: str) -> dict | None:
    try:
        j = api({"generator": "search", "gsrsearch": terms, "gsrnamespace": "6",
                 "gsrlimit": "8", "prop": "imageinfo",
                 "iiprop": "url|extmetadata|mime|size", "iiurlwidth": "760"})
    except Exception as e:                                   # noqa: BLE001
        print(f"   search failed for {terms!r}: {e}")
        return None
    for p in (j.get("query", {}) or {}).get("pages", []) or []:
        ii = (p.get("imageinfo") or [{}])[0]
        if not ii.get("thumburl") or "image" not in (ii.get("mime") or ""):
            continue
        if (ii.get("width") or 0) < 400:
            continue
        lic = licence_of(ii)
        if not lic:
            continue
        return {"title": p["title"], "thumb": ii["thumburl"],
                "page": ii.get("descriptionurl", ""), "licence": lic[0],
                "artist": lic[1], "credit": lic[2]}
    return None


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(IMG, exist_ok=True)
    manifest: dict[str, dict] = {}
    rejected = 0
    for gc, terms in SUBJECTS:
        hit = find(terms)
        if not hit:
            rejected += 1
            print(f"   no cleanly licensed image for {terms!r}")
            continue
        dest = os.path.join(IMG, gc + ".jpg")
        if not os.path.exists(dest):
            try:
                req = urllib.request.Request(hit["thumb"], headers={"User-Agent": UA})
                with urllib.request.urlopen(req, timeout=120,
                                            context=ssl.create_default_context()) as r:
                    open(dest, "wb").write(r.read())
            except Exception as e:                           # noqa: BLE001
                print(f"   download failed {gc}: {e}")
                continue
        manifest[gc] = {"file": gc + ".jpg", "title": hit["title"][5:],
                        "licence": hit["licence"], "artist": hit["artist"],
                        "credit": hit["credit"], "page": hit["page"],
                        "subject": terms}
        print(f"   {gc:10s} {hit['licence']:22s} {hit['title'][5:60]}")
        time.sleep(0.4)
    json.dump(manifest, open(os.path.join(OUT, "gallery.json"), "w"), ensure_ascii=False,
              indent=1)
    mb = sum(os.path.getsize(os.path.join(IMG, v["file"])) for v in manifest.values()) / 1e6
    print(f"\n{len(manifest)} images admitted, {rejected} subjects had none that passed the "
          f"gate · {mb:.1f} MB")
