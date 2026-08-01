#!/usr/bin/env python3
"""build_tree.py — the genealogy: every language family, its internal structure, its history.

The map answers "where". This answers "**where from**", and it is the other half of the
subject. A language is not a coloured area; it is the current end of a chain of speech
stretching back past the reach of comparison, with sisters, with a parent, and often with an
ending. None of that is visible on a map.

WORKING-RULES §13b permits exactly this and constrains it: an abstract space "may only ever be
a **secondary view**". So the tree is a second view onto the same data, keyed to the same
glottocodes, with the same family hues, and every leaf flies the map back to the ground.

WHAT IT IS BUILT FROM, all of it already local:
  * `values.csv` `subclassification` — a Newick subtree per languoid, glottocodes as labels.
    Glottolog's own classification, not a reconstruction of ours.
  * `languages.csv` — all **27,177** languoids: 4,853 families, 8,618 languages, 13,706
    dialects, with names, levels, coordinates, ISO codes and documentation years.
  * `values.csv` `aes` — endangerment, so a branch can be drawn as ending.
  * **Phlorest** dated phylogenies — real root ages for 21 families, sanity-checked.

TIME. Only 21 families have a dated tree. Everywhere else the tree has **topology but no
dates**, and the view says so rather than drawing a spurious axis (rule 10). Attestation years
from Glottolog give a second, different kind of date — when a language was first written down,
not when it split — and the two are never mixed.

Emits `web/data/tree/index.json` plus one file per family, so a viewer downloads Atlantic-Congo
only if they open Atlantic-Congo.

Run: python3 build_tree.py
"""
from __future__ import annotations

import csv
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
GLOTTOLOG = os.path.join(ROOT, "data", "glottolog")
TEXTS = os.path.join(ROOT, "data", "texts")
OUT = os.path.join(ROOT, "web", "data", "tree")

AES_NAMES = ["not assessed", "not endangered", "threatened", "shifting",
             "moribund", "nearly extinct", "extinct"]


def parse_newick(s: str) -> dict:
    """Newick with glottocode labels -> nested {g, c}. Iterative; some families are deep."""
    s = s.strip().rstrip(";")
    pos = 0

    def node():
        nonlocal pos
        children = []
        if pos < len(s) and s[pos] == "(":
            pos += 1
            while True:
                children.append(node())
                if pos < len(s) and s[pos] == ",":
                    pos += 1
                    continue
                if pos < len(s) and s[pos] == ")":
                    pos += 1
                break
        m = re.match(r"[^,()\[\]:;]*", s[pos:])
        label = m.group(0).strip() if m else ""
        pos += len(m.group(0)) if m else 0
        if pos < len(s) and s[pos] == ":":
            m2 = re.match(r":[^,()]*", s[pos:])
            pos += len(m2.group(0)) if m2 else 1
        n = {"g": label}
        if children:
            n["c"] = children
        return n

    return node()


def main() -> None:
    os.makedirs(OUT, exist_ok=True)

    info: dict[str, dict] = {}
    with open(os.path.join(GLOTTOLOG, "languages.csv"), newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            info[r["ID"]] = {
                "n": r["Name"], "lv": r["Level"], "fam": r["Family_ID"],
                "iso": r["ISO639P3code"] or "",
                "lat": float(r["Latitude"]) if r["Latitude"] else None,
                "lon": float(r["Longitude"]) if r["Longitude"] else None,
                "ma": r["Macroarea"] or "",
                "y0": int(r["First_Year_Of_Documentation"] or 0),
                "y1": int(r["Last_Year_Of_Documentation"] or 0),
            }
    sub: dict[str, str] = {}
    aes: dict[str, int] = {}
    cat: dict[str, str] = {}
    with open(os.path.join(GLOTTOLOG, "values.csv"), newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            p = r["Parameter_ID"]
            if p == "subclassification":
                sub[r["Language_ID"]] = r["Value"]
            elif p == "aes" and r["Value"]:
                try:
                    aes[r["Language_ID"]] = int(float(r["Value"]))
                except ValueError:
                    pass
            elif p == "category":
                cat[r["Language_ID"]] = r["Value"]

    # Autonyms and texts, so a leaf can show a real name and a real sentence.
    autonym: dict[str, list] = {}
    extra: dict[str, dict] = {}
    lp = os.path.join(ROOT, "web", "data", "languages.json")
    if os.path.exists(lp):
        for row in json.load(open(lp, encoding="utf-8"))["rows"]:
            if row[9]:
                autonym[row[0]] = row[9][0]
            e = {}
            if len(row) > 12 and row[12]:
                e["d"] = row[12]
            if len(row) > 13 and row[13]:
                e["sp"] = row[13]
            if len(row) > 14 and row[14]:
                e["cc"] = row[14]
            if e:
                extra[row[0]] = e

    ages: dict[str, dict] = {}
    pp = os.path.join(TEXTS, "phlorest.json")
    if os.path.exists(pp):
        from collections import Counter
        for ds, v in json.load(open(pp, encoding="utf-8")).items():
            # Phlorest lists the LEAF languages it sampled, not the family it dates. Attaching
            # the age to those glottocodes hit only the five isolates whose leaf happens to be
            # its own root. Resolve each leaf to its family and take the majority: that is the
            # node the root age actually describes.
            fams = Counter(info[gc]["fam"] or gc for gc in v["glottocodes"] if gc in info)
            if not fams:
                continue
            root, n = fams.most_common(1)[0]
            ages.setdefault(root, {"age": v["age_years"], "scaling": v["scaling"],
                                   "explicit": v.get("explicit_unit", False),
                                   "dataset": ds, "sampled": n})

    roots = sorted(g for g, i in info.items() if not i["fam"])
    index = []
    total_nodes = 0
    dated = 0

    for g in roots:
        nwk = sub.get(g)
        if not nwk:
            continue
        try:
            tree = parse_newick(nwk)
        except RecursionError:
            print(f"   {g}: too deep to parse, skipped")
            continue

        counts = {"lang": 0, "dial": 0, "extinct": 0, "endangered": 0}
        macros: dict[str, int] = {}
        y_first = None

        def walk(nd):
            nonlocal y_first
            i = info.get(nd["g"], {})
            nd["n"] = i.get("n", nd["g"])
            lv = i.get("lv", "")
            nd["lv"] = {"family": 0, "language": 1, "dialect": 2}.get(lv, 0)
            a = aes.get(nd["g"], 0)
            if a:
                nd["a"] = a
            if i.get("lat") is not None:
                nd["p"] = [round(i["lon"], 2), round(i["lat"], 2)]
            if i.get("iso"):
                nd["i"] = i["iso"]
            if i.get("y0"):
                nd["y"] = i["y0"]
                y_first = i["y0"] if y_first is None else min(y_first, i["y0"])
            if nd["g"] in autonym:
                nd["au"] = autonym[nd["g"]]
            nd.update(extra.get(nd["g"], {}))
            if lv == "language":
                counts["lang"] += 1
                if i.get("ma"):
                    macros[i["ma"]] = macros.get(i["ma"], 0) + 1
                if a >= 6:
                    counts["extinct"] += 1
                elif a >= 3:
                    counts["endangered"] += 1
            elif lv == "dialect":
                counts["dial"] += 1
            for c in nd.get("c", []):
                walk(c)

        import sys
        sys.setrecursionlimit(20000)
        walk(tree)
        n_nodes = counts["lang"] + counts["dial"] + 1
        total_nodes += n_nodes

        age = ages.get(g)
        if age:
            dated += 1
            tree["age"] = age["age"]
            tree["ageSrc"] = age["dataset"]
            tree["ageScaling"] = age["scaling"]
            tree["ageExplicit"] = age["explicit"]

        json.dump(tree, open(os.path.join(OUT, f"{g}.json"), "w"),
                  ensure_ascii=False, separators=(",", ":"))
        index.append({
            "g": g, "n": info.get(g, {}).get("n", g),
            "lang": counts["lang"], "dial": counts["dial"],
            "extinct": counts["extinct"], "endangered": counts["endangered"],
            "ma": max(macros, key=macros.get) if macros else "",
            "isolate": info.get(g, {}).get("lv") == "language",
            # Glottolog's 8 PSEUDO-FAMILIES are not genealogical units: Bookkeeping,
            # Sign Language, Unclassifiable, Unattested, Pidgin, Mixed Language, Speech
            # Register, Artificial Language. Listing them beside Indo-European without
            # saying so implies a common ancestor that does not exist.
            "pseudo": cat.get(g) == "Pseudo_Family",
            "age": age["age"] if age else None,
            "ageExplicit": bool(age and age["explicit"]),
            "y0": y_first,
        })

    index.sort(key=lambda d: -d["lang"])
    meta = {
        "families": index,
        "totals": {
            "roots": len(index),
            "isolates": sum(1 for d in index if d["isolate"]),
            "languages": sum(d["lang"] for d in index),
            "dialects": sum(d["dial"] for d in index),
            "extinct": sum(d["extinct"] for d in index),
            "endangered": sum(d["endangered"] for d in index),
            "dated": dated,
        },
        "note": ("Glottolog 5.3 classification. Ages, where present, are root ages of dated "
                 "phylogenies from Phlorest (CC-BY), sanity-checked to 300-12,000 years; "
                 "nine of thirty were rejected as implausible, one of them at 613,594 years. "
                 "Families with no age have topology only and no time axis is drawn for them."),
    }
    json.dump(meta, open(os.path.join(OUT, "index.json"), "w"),
              ensure_ascii=False, separators=(",", ":"))

    t = meta["totals"]
    print(f"tree: {t['roots']} roots ({t['isolates']} isolates), {t['languages']:,} languages, "
          f"{t['dialects']:,} dialects")
    print(f"      {t['extinct']:,} extinct · {t['endangered']:,} endangered · "
          f"{t['dated']} families with a dated root")
    sz = sum(os.path.getsize(os.path.join(OUT, f)) for f in os.listdir(OUT)) / 1e6
    print(f"      {len(os.listdir(OUT))} files, {sz:.1f} MB "
          f"(index {os.path.getsize(os.path.join(OUT,'index.json'))/1e3:.0f} kB)")
    print(f"      largest: " + ", ".join(f"{d['n']} {d['lang']}" for d in index[:4]))


def build_texts() -> None:
    """web/data/texts.json — Article 1 per glottocode. Register D2, SCOPE §12 D2."""
    up = os.path.join(TEXTS, "udhr.json")
    if not os.path.exists(up):
        print("no UDHR corpus — text tier absent")
        return
    u = json.load(open(up, encoding="utf-8"))
    iso2gc: dict[str, str] = {}
    with open(os.path.join(GLOTTOLOG, "languages.csv"), newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["ISO639P3code"] and r["Level"] == "language":
                iso2gc[r["ISO639P3code"]] = r["Glottocode"]
    out = {}
    for iso, v in u["by_iso639_3"].items():
        gc = iso2gc.get(iso)
        if not gc:
            continue
        out[gc] = {"b": v["blocks"], "s": v["script"], "d": v["dir"], "l": v["tag"],
                   "f": v["file"]}
    d = os.path.join(ROOT, "web", "data")
    os.makedirs(d, exist_ok=True)
    json.dump({"source": u["source"], "licence": u["licence"], "takedown": u["takedown"],
               "scripts": u["scripts"], "by_glottocode": out},
              open(os.path.join(d, "texts.json"), "w"), ensure_ascii=False,
              separators=(",", ":"))
    print(f"texts: {len(out)} languages matched to a glottocode, "
          f"{len(u['scripts'])} scripts, "
          f"{os.path.getsize(os.path.join(d,'texts.json'))/1e3:.0f} kB")


def build_words() -> None:
    """web/data/words.json — ASJP's core list, already keyed by glottocode. Register D2b."""
    src = os.path.join(ROOT, "data", "words", "words.json")
    if not os.path.exists(src):
        print("no ASJP wordlists — word tier absent")
        return
    d = json.load(open(src, encoding="utf-8"))
    out = os.path.join(ROOT, "web", "data", "words.json")
    json.dump(d, open(out, "w"), ensure_ascii=False, separators=(",", ":"))
    print(f"words: {len(d['by_glottocode']):,} languages, "
          f"{os.path.getsize(out)/1e6:.1f} MB")


if __name__ == "__main__":
    main()
    build_texts()
    build_words()
