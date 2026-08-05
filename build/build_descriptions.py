#!/usr/bin/env python3
"""build_descriptions.py — a description for every language, composed from the record.
Register D15.

THE MEASUREMENT THAT FORCED THIS. 8,618 language nodes; 7,970 carry a description field, which
looks like 92% coverage until you read them. 4,627 of them say the single word "language". 648
say nothing. Filtering for anything longer than sixteen characters that is not a bare
classification leaves 3,090 — 36%. So most cards had no description at all, and the ones that
did often had "language in Papua".

Authoring 8,000 paragraphs is not possible and guessing them is not acceptable. But this build
already holds, per language: its family and the exact branch path down to it, the naming cluster
it belongs to, the countries it is spoken in, its vitality, how well it has been described, its
first attestation, a (value, year) speaker count where one is defensible, its scripts, its
nearest relatives in the tree, and which parts of this museum hold something for it.

That composes into a paragraph that is entirely true and says something useful:

    One of the 53 languages called Mixtec, spoken in Mexico. Glottolog places it in
    Mixtec-Cuicatec, inside Otomanguean — 181 languages. Its nearest relatives here are
    Tidaá Mixtec, Yucuañe Mixtec and Diuxi-Tilantongo Mixtec. Vitality is recorded as
    shifting: children are learning another language instead. The fullest description of
    it is a grammar sketch. This museum holds a word list for it.

EVERY CLAUSE IS CONDITIONAL and none is invented. A language with no speaker count gets no
speaker sentence; rule 10 says "unknown" is a legitimate return, and a composed paragraph that
padded itself with guesses would be worse than the blank it replaces.

IT IS LABELLED AS COMPOSED, in the card, every time. An authored museum label and a sentence
assembled from database columns are different kinds of claim and the visitor is told which one
they are reading. Where an authored label exists it is shown and this is not: 283 languages have
one, and it is better.

Run: python3 build_descriptions.py
"""
from __future__ import annotations

import glob
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
WEB = os.path.join(ROOT, "web", "data")
TERR = os.path.join(ROOT, "data", "territories", "en.json")

# Glottolog's Agglomerated Endangerment Status, and what each level means for a reader. The
# index order is the app's AESN array and must not be reordered independently of it.
AES = [None,
       ("not endangered", "children are still learning it as a first language"),
       ("threatened", "it is still being learned, but the community is shrinking"),
       ("shifting", "children are learning another language instead"),
       ("moribund", "only the grandparent generation still speaks it"),
       ("nearly extinct", "a handful of elderly speakers remain"),
       ("extinct", "nobody speaks it")]

# Glottolog's Most Extensive Description, worst-first in the app's MED array.
MED = ["a long grammar", "a grammar", "a grammar sketch",
       "a phonology or a word list", "almost nothing"]

HOLDS = [("letters", "its letters"), ("words", "a word list"), ("prose", "connected prose"),
         ("heard", "recordings of people speaking it"), ("object", "objects"),
         ("dated", "a timeline"), ("phrases", "words and phrases")]

GENERIC = re.compile(r"^(language|language family|dialect|extinct language|natural language|"
                     r"macrolanguage|dead language|human language|ancient language|"
                     r"sign language|creole language|pidgin|language group)\.?$", re.I)


def substantive(d: str) -> bool:
    d = (d or "").strip()
    return bool(d) and not GENERIC.match(d) and len(d) > 16


# A territory name that needs a definite article. Derived rather than listed: CLDR's English
# names take "the" exactly when they are plural or contain a state-form word, which covers
# "the United States", "the Netherlands", "the Philippines", "the Solomon Islands" and
# "the Democratic Republic of the Congo" without an authored list of 264 exceptions.
NEEDS_THE = re.compile(r"\b(States|Kingdom|Republic|Islands|Emirates|Federation|Netherlands|"
                       r"Philippines|Bahamas|Maldives|Comoros|Gambia|Seychelles|Vatican)\b")


def territory(name: str) -> str:
    return ("the " + name) if NEEDS_THE.search(name) else name


def join(items: list[str]) -> str:
    items = [i for i in items if i]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


def main() -> None:
    terr = json.load(open(TERR, encoding="utf-8"))["by_code"]
    langs = json.load(open(os.path.join(WEB, "languages.json"), encoding="utf-8"))
    F = {k: i for i, k in enumerate(langs["fields"])}
    if "cc" not in F:
        raise SystemExit("languages.json still names only 12 of its 15 columns; "
                         "rerun build_fields.py")
    row = {r[F["code"]]: r for r in langs["rows"]}

    fams = json.load(open(os.path.join(WEB, "families.json"), encoding="utf-8"))
    famrec = fams["by_glottocode"]
    node_clusters = fams.get("clusters_by_node") or {}

    def keys(path, sub=None):
        p = os.path.join(WEB, path)
        if not os.path.exists(p):
            return set()
        d = json.load(open(p, encoding="utf-8"))
        return set((d.get(sub) or d) if sub else d)
    have = {
        "letters": keys("alphabets.json", "by_glottocode"),
        "words": keys("words.json", "by_glottocode"),
        "prose": keys("texts.json", "by_glottocode"),
        "heard": keys("audio.json", "by_glottocode"),
        "object": keys("gallery.json"),
        "dated": keys("milestones.json", "by_glottocode"),
        "phrases": keys("phrases.json", "by_glottocode"),
    }
    labelled = keys("notable.json", "by_glottocode")

    out: dict[str, str] = {}
    branch: dict[str, str] = {}
    bstats = {"own": 0, "composed": 0}
    stats = {"authored": 0, "composed": 0, "own": 0, "nothing": 0,
             "clause": {k: 0 for k in ("cluster", "where", "placed", "kin", "speakers",
                                       "vitality", "med", "first", "holds")}}

    for f in sorted(glob.glob(os.path.join(WEB, "tree", "*.json"))):
        if f.endswith("index.json"):
            continue
        tree = json.load(open(f, encoding="utf-8"))
        fam_gc = tree["g"]
        frec = famrec.get(fam_gc) or {}
        fam_name = frec.get("n") or tree.get("n") or ""
        fam_lang = frec.get("lang") or 0

        # walk once, carrying the branch path and the parent node so siblings are reachable
        def walk(n, path, parent):
            kids = n.get("c") or []
            if n.get("lv") == 1:
                describe(n, path, parent)
            elif n.get("lv") == 0 and path:
                describe_branch(n, path)
            for k in kids:
                walk(k, path + [n], n)

        def members(n) -> list:
            """The LANGUAGES under a node. A language stops the walk even if it has dialects."""
            if n.get("lv") == 1:
                return [n]
            acc = []
            for k in (n.get("c") or []):
                acc.extend(members(k))
            return acc

        def describe_branch(n, path):
            """A branch card already prints its counts, its earliest written member and its
            naming cluster. This adds only what it does not have: where the branch is, and which
            of its languages has the most speakers — so the composed text never repeats the card
            it sits inside."""
            if substantive(n.get("d")):
                bstats["own"] += 1
                return
            mem = members(n)
            if not mem:
                return
            bits = ["A branch of " + fam_name + "."]
            cs: dict[str, int] = {}
            for m in mem:
                r2 = row.get(m["g"])
                for c in ((r2[F["cc"]] if r2 else "") or "").split(";"):
                    if c:
                        cs[c] = cs.get(c, 0) + 1
            if cs:
                top = sorted(cs, key=lambda c: -cs[c])[:3]
                bits.append("Its languages are spoken in " +
                            join([territory(terr.get(c, c)) for c in top]) +
                            (" and elsewhere" if len(cs) > 3 else "") + ".")
            spk = [(row[m["g"]][F["sp"]], m.get("n")) for m in mem
                   if row.get(m["g"]) and row[m["g"]][F["sp"]]]
            if spk:
                (v, y), nm2 = max(spk, key=lambda t: t[0][0])
                bits.append("The most spoken of them is " + nm2 + ", with " + f"{int(v):,}" +
                            " speakers as of " + str(y) + ".")
            alive = [m for m in mem if str(m.get("a")) not in ("6",)]
            if len(mem) > 1 and not alive:
                bits.append("Nobody speaks any of them.")
            branch[n["g"]] = " ".join(bits)
            bstats["composed"] += 1

        def describe(n, path, parent):
            gc = n["g"]
            if gc in labelled:
                stats["authored"] += 1
                return
            if substantive(n.get("d")):
                stats["own"] += 1
                return
            r = row.get(gc)
            bits: list[str] = []

            # 1. identity, and the cluster if it is in one — the Mixtec case
            cl = None
            for anc in path:
                c = node_clusters.get(anc.get("g"))
                if c:
                    last = (n.get("n") or "").split("(")[0].strip().split()
                    if last and any(w == last[-1] for w, _ in c):
                        cl = next(x for x in c if x[0] == last[-1])
                        break
            where = ""
            if r and r[F["cc"]]:
                cs = [territory(terr.get(c, c)) for c in r[F["cc"]].split(";") if c]
                if cs:
                    where = "spoken in " + join(cs[:3]) + \
                            (" and elsewhere" if len(cs) > 3 else "")
            if cl:
                bits.append("One of the " + str(cl[1]) + " languages called " + cl[0] +
                            (", " + where if where else "") + ".")
                stats["clause"]["cluster"] += 1
            elif where:
                bits.append("A " + fam_name + " language, " + where + ".")
            elif fam_name:
                bits.append("A " + fam_name + " language.")
            if where:
                stats["clause"]["where"] += 1

            # 2. where the catalogue puts it
            if parent is not None and parent.get("n") and parent.get("g") != fam_gc:
                bits.append("Glottolog places it in " + parent["n"] + ", inside " + fam_name +
                            (" — " + f"{fam_lang:,}" + " languages." if fam_lang > 1 else "."))
                stats["clause"]["placed"] += 1
            elif fam_lang == 1:
                bits.append("It is an isolate: no relationship to any other language has been "
                            "demonstrated.")

            # 3. nearest relatives — its siblings under the same node
            if parent is not None:
                sibs = [k.get("n") for k in (parent.get("c") or [])
                        if str(k.get("lv")) == "1" and k.get("g") != gc and k.get("n")]
                if sibs:
                    bits.append("Its nearest relative" + ("s here are " if len(sibs) > 1
                                                          else " here is ") +
                                join(sibs[:3]) + ".")
                    stats["clause"]["kin"] += 1

            # 4. speakers — only as the (value, year) triple rule 14 requires
            if r and r[F["sp"]]:
                v, y = r[F["sp"]][0], r[F["sp"]][1]
                bits.append(f"{int(v):,} speakers, as of {y}.")
                stats["clause"]["speakers"] += 1

            # 5. vitality, with what the label means
            a = n.get("a")
            try:
                ai = int(a)
            except (TypeError, ValueError):
                ai = 0
            if 1 <= ai < len(AES) and AES[ai]:
                lab, gloss = AES[ai]
                bits.append("Vitality is recorded as " + lab + ": " + gloss + ".")
                stats["clause"]["vitality"] += 1

            # 6. how well anyone has described it — the documentation boundary, per language
            if r and isinstance(r[F["med"]], int) and 0 <= r[F["med"]] < len(MED):
                bits.append("The fullest description of it anyone has published is " +
                            MED[r[F["med"]]] + ".")
                stats["clause"]["med"] += 1

            # 7. first attestation
            if r and r[F["first"]]:
                y = int(r[F["first"]])
                bits.append("First written down in " +
                            (f"{-y} BCE" if y < 0 else str(y)) + ".")
                stats["clause"]["first"] += 1

            # 8. what this museum actually holds for it
            got = [lab for k, lab in HOLDS if gc in have[k]]
            if got:
                bits.append("This museum holds " + join(got) + " for it.")
                stats["clause"]["holds"] += 1
            else:
                bits.append("This museum holds nothing for it beyond its position in the tree "
                            "and the ground it is spoken on — which is the state of the record, "
                            "not an omission here.")

            out[gc] = " ".join(bits)
            stats["composed"] += 1

        walk(tree, [], None)

    json.dump({"note": "Composed from this build's own record, one clause per datum, nothing "
                       "invented. Shown only where no authored museum label exists, and always "
                       "labelled in the card as composed rather than written.",
               "by_glottocode": out, "branches": branch},
              open(os.path.join(WEB, "descriptions.json"), "w"), ensure_ascii=False,
              separators=(",", ":"))

    tot = stats["authored"] + stats["own"] + stats["composed"]
    print(f"{tot:,} language nodes")
    print(f"   {stats['authored']:,} already carry an authored museum label — left alone")
    print(f"   {stats['own']:,} already carry a substantive description of their own")
    print(f"   {stats['composed']:,} newly composed from the record")
    covered = stats["authored"] + stats["own"] + stats["composed"]
    print(f"   every language now has a description: {covered:,} of {tot:,} "
          f"({covered/tot*100:.1f}%)")
    print("   clauses actually emitted:")
    for k, v in stats["clause"].items():
        print(f"      {k:10s} {v:6,}")
    print(f"   branches: {bstats['own']:,} had a description of their own, "
          f"{bstats['composed']:,} newly composed")
    kb = os.path.getsize(os.path.join(WEB, 'descriptions.json')) / 1024
    print(f"   descriptions.json {kb:,.0f} KB")
    sample = [g for g in out if g.startswith("sila")] or list(out)[:1]
    for g in sample[:2]:
        print(f"\n   {g}: {out[g]}")


if __name__ == "__main__":
    main()
