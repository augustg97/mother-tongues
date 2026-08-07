#!/usr/bin/env python3
"""D18 — one search index over every language, so a visitor can find one.

WHY. The atlas had two search boxes: 429 families, and "within this family" once you had opened
one. A visitor who wants Warlpiri and does not know it is Pama-Nyungan had no way in. For 8,618
languages that is the largest usability gap in the project, larger than anything on the surface.

WHAT IT HOLDS, per language, as a flat array to keep the file small:
    [name, autonym or "", glottocode, family glottocode, speakers or 0, vitality]
Names are searched as typed AND folded to plain ASCII, because a reader looking for Nahuatl
should not have to produce "Nāhuatl" and one looking for Yoruba should find Yorùbá.

Run: python3 build_search.py
"""
from __future__ import annotations

import json
import os
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
WEB = os.path.join(ROOT, "web", "data")


def fold(s: str) -> str:
    """Strip diacritics and case so 'Yoruba' finds 'Yorùbá' and 'Nahuatl' finds 'Nāhuatl'."""
    return "".join(c for c in unicodedata.normalize("NFD", s.lower())
                   if unicodedata.category(c) != "Mn")


def main() -> None:
    L = json.load(open(os.path.join(WEB, "languages.json"), encoding="utf-8"))
    F = {k: i for i, k in enumerate(L["fields"])}
    fams = json.load(open(os.path.join(WEB, "families.json"), encoding="utf-8"))["by_glottocode"]

    rows, folded = [], []
    for r in L["rows"]:
        au = ""
        a = r[F["autonyms"]]
        if a:
            au = a[0][0]
        sp = r[F["sp"]]
        sp = int(sp[0]) if isinstance(sp, list) and sp else 0
        rows.append([r[F["name"]], au, r[F["code"]], r[F["famid"]], sp, r[F["aes"]] or 0])
        # one folded haystack per row: reference name + autonym, so both are searchable
        folded.append(fold(r[F["name"]] + " " + au))

    famnames = {g: v.get("n", g) for g, v in fams.items()}

    json.dump({"note": "Every language, searchable by reference name and by autonym. Folded "
                       "forms are precomputed so the page does no normalisation at keystroke "
                       "time. Row shape: [name, autonym, glottocode, family, speakers, aes].",
               "fields": ["name", "autonym", "code", "famid", "sp", "aes"],
               "rows": rows, "folded": folded, "famnames": famnames},
              open(os.path.join(WEB, "search.json"), "w"),
              ensure_ascii=False, separators=(",", ":"))

    kb = os.path.getsize(os.path.join(WEB, "search.json")) / 1024
    withau = sum(1 for r in rows if r[1])
    print(f"search: {len(rows):,} languages, {withau} with an autonym, "
          f"{len(famnames)} family names · {kb:,.0f} KB")


if __name__ == "__main__":
    main()
