#!/usr/bin/env python3
"""build_wikipedia.py — resolve each Wikipedia edition onto a glottocode. Register D12.

The join is the alphabets' join. A Wikipedia code is a language code: mostly ISO 639-1, which
reaches ISO 639-3 through the Wikidata mapping cached by fetch_alphabets.py, and thence a
glottocode through our own `iso` field. Codes that are macrolanguages or that Wikipedia invented
(`zh-yue`, `bat-smg`, `roa-tara`) go through WP_BRIDGE in fetch_wikipedia.py, which is keyed by
exact Glottolog NAME and checked by machine — because a Wikipedia attached to the wrong language
would be a claim that people write in a language they do not.

Everything that will not resolve is printed. A silent drop here would look like a language with
no encyclopedia, which is a much stronger statement than "we could not match the code".

Run: python3 build_wikipedia.py
"""
from __future__ import annotations

import csv
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
WEB = os.path.join(ROOT, "web", "data")
ED = os.path.join(ROOT, "data", "wikipedia", "editions.json")
ALPH = os.path.join(ROOT, "data", "alphabets", "cldr_characters.json")
GL = os.path.join(ROOT, "data", "glottolog", "languages.csv")


def main() -> None:
    src = json.load(open(ED, encoding="utf-8"))
    stats = src["by_code"]
    i1to3 = json.load(open(ALPH, encoding="utf-8"))["iso1_to_iso3"]

    langs = json.load(open(os.path.join(WEB, "languages.json"), encoding="utf-8"))
    F = {k: i for i, k in enumerate(langs["fields"])}
    by_iso: dict[str, str] = {}
    name: dict[str, str] = {}
    for r in langs["rows"]:
        name[r[F["code"]]] = r[F["name"]]
        if r[F["iso"]]:
            by_iso.setdefault(r[F["iso"]], r[F["code"]])

    # resolve the authored bridge by exact Glottolog name, refusing anything ambiguous
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "fw", os.path.join(HERE, "fetch_wikipedia.py"))
    fw = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fw)
    gnames: dict[str, list] = {}
    with open(GL, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["Level"] == "language":
                gnames.setdefault(r["Name"], []).append(r["ID"])
    bridge: dict[str, str] = {}
    for code, nm in fw.WP_BRIDGE.items():
        hit = gnames.get(nm) or []
        if len(hit) != 1:
            raise SystemExit(f"WP_BRIDGE {code!r} -> {nm!r} matched {len(hit)} languages")
        bridge[code] = hit[0]

    out: dict[str, dict] = {}
    unresolved: list[str] = []
    for code, v in stats.items():
        gc = bridge.get(code)
        if not gc:
            iso3 = code if len(code) == 3 else i1to3.get(code)
            gc = by_iso.get(iso3) if iso3 else None
        if not gc or gc not in name:
            unresolved.append(code)
            continue
        rec = {"code": code, "articles": v["articles"], "edits": v["edits"],
               "users": v["users"], "active": v["active"],
               "localname": v.get("localname", ""), "url": v.get("url", ""),
               "retrieved": src.get("retrieved", "")}
        # a language can only have one edition; if two codes land on it, keep the larger
        if gc not in out or rec["articles"] > out[gc]["articles"]:
            out[gc] = rec

    json.dump({"note": "Each language's own Wikipedia. Article count alone is misleading — two "
                       "of the largest were written almost entirely by a bot — so active "
                       "editors is carried beside it.",
               "source": "Wikimedia sitematrix and siteinfo/statistics",
               "licence": "CC-BY-SA-4.0", "retrieved": src.get("retrieved", ""),
               "by_glottocode": out},
              open(os.path.join(WEB, "wikipedia.json"), "w"), ensure_ascii=False,
              separators=(",", ":"))

    print(f"{len(out)} languages have a Wikipedia of their own")
    if unresolved:
        print(f"   {len(unresolved)} editions did not resolve to a language in this build: "
              f"{' '.join(sorted(unresolved))}")
    # The fact the tier exists to carry: what the article count hides.
    bots = sorted(((v["articles"] / max(v["active"], 1), gc, v) for gc, v in out.items()
                   if v["articles"] > 50000), reverse=True)[:6]
    print("\n   most articles per active editor — where the count is machine-made:")
    for per, gc, v in bots:
        print(f"      {name.get(gc, gc):22s} {v['articles']:>9,} articles  "
              f"{v['active']:>5,} editors  {per:>9,.0f} each")
    live = sorted(out.items(), key=lambda kv: -kv[1]["active"])[:6]
    print("\n   most active editors — where people are actually writing:")
    for gc, v in live:
        print(f"      {name.get(gc, gc):22s} {v['active']:>7,} editors  "
              f"{v['articles']:>10,} articles")


if __name__ == "__main__":
    main()
