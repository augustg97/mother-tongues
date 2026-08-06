#!/usr/bin/env python3
"""build_site.py — the ONLY route to publication.

1. run the research selftests and REFUSE TO PUBLISH on any failure;
2. verify the field rasters exist and are registered to the real Earth;
3. stamp the data version BEFORE the app file is copied;
4. copy web/ -> docs/, which GitHub Pages serves from main:/docs.

Step 3's ordering is not cosmetic. A static host serves an asset with a cache lifetime and
an ETag, so a returning viewer can sit on a cached copy well past it: the app runs
perfectly and shows yesterday's data (TRAPS §D2). This already bit us in local development
— a cached app.js kept a fixed 320x240 canvas alive across three rebuilds.

Relative paths throughout, so the project directory can move. It will.

Run:  python3 build_site.py
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
WEB = os.path.join(ROOT, "web")
DOCS = os.path.join(ROOT, "docs")
MODELING = os.path.join(ROOT, "Research", "modeling")

REQUIRED_FIELDS = ["fields.json"]
# TWO budgets, because they answer different questions. What the viewer waits for before the
# world appears is level 0 — that is the one that must stay small. The pyramid as a whole is
# only ever fetched a few tiles at a time, so its ceiling is about what a static host and a
# git repository can carry, not about page weight.
BUDGET_L0_MB = 9.0
BUDGET_TOTAL_MB = 420.0


def die(msg: str) -> None:
    print(f"\nREFUSING TO PUBLISH: {msg}")
    sys.exit(1)


def gate_selftests() -> None:
    print("1. research selftests")
    p = subprocess.run([sys.executable, os.path.join(MODELING, "audit_all.py")],
                       capture_output=True, text=True)
    print("   " + "\n   ".join(p.stdout.strip().splitlines()[-6:]))
    if p.returncode != 0:
        print(p.stderr[-1500:])
        die("a research selftest failed")


def gate_fields() -> None:
    print("2. field rasters")
    fd = os.path.join(WEB, "fields")
    missing = [f for f in REQUIRED_FIELDS if not os.path.exists(os.path.join(fd, f))]
    if missing:
        die(f"missing field files: {missing} — run build_fields.py")
    meta = json.load(open(os.path.join(fd, "fields.json")))
    n = sum(len(v) for v in meta["tiles"].values())
    for lvl, keys in meta["tiles"].items():
        for k in keys:
            for f in ("terrain", "env", "lang_c", "lang_t"):
                p = os.path.join(fd, f"z{lvl}", f"{f}_{k}.png")
                if not os.path.exists(p):
                    die(f"manifest lists z{lvl}/{k} but {f} is missing — retile")
    l0 = sum(os.path.getsize(os.path.join(fd, "z0", f))
             for f in os.listdir(os.path.join(fd, "z0"))) / 1e6
    print(f"   {n} tiles across {len(meta['tiles'])} levels, all present · "
          f"level 0 is {l0:.2f} MB (budget {BUDGET_L0_MB:.0f} MB)")
    if l0 > BUDGET_L0_MB:
        die(f"level 0 is {l0:.2f} MB — first paint would block on it")
    # The SIZE check lives in publish(), not here: later gates WRITE files into web/, so
    # measuring the budget at this point would check a directory that does not exist yet.


def _web_size_mb() -> float:
    return sum(os.path.getsize(os.path.join(r, f))
               for r, _, fs in os.walk(WEB) for f in fs) / 1e6


def gate_js() -> None:
    """Parse every shipped script before publishing it.

    A redeclared `const` in tree.js shipped live: the file threw on load, the genealogy view
    came up completely empty, and nothing in the build noticed because every other gate
    checks DATA. `node --check` is one subprocess and would have caught it before the push.
    """
    print("2b. javascript parses")
    import shutil as _sh
    node = _sh.which("node")
    if not node:
        print("   no node on PATH — SKIPPED (install node to enable this gate)")
        return
    for f in sorted(os.listdir(os.path.join(WEB, "js"))):
        if not f.endswith(".js"):
            continue
        p = subprocess.run([node, "--check", os.path.join(WEB, "js", f)],
                           capture_output=True, text=True)
        if p.returncode != 0:
            print(p.stderr[:600])
            die(f"js/{f} does not parse")
    print(f"   {len([f for f in os.listdir(os.path.join(WEB, 'js')) if f.endswith('.js')])} "
          f"files parse")


def gate_labels() -> None:
    """Every authored label must sit on the language it is about.

    Seven of thirty did not. `nucl1301` is Turkish, not Standard Arabic, so a paragraph about
    the Qur'an was displayed on Turkish; the Maya codex image was on Classical Syriac and the
    Kojiki on Sinitic. Glottocodes are opaque eight-character strings and I guessed several of
    them from memory. Nothing caught it because no gate compared authored text against the
    catalogue — so this one does, on the one word each label is unmistakably about.
    """
    print("2c. museum labels sit on the right languages")
    import csv as _csv
    np_ = os.path.join(WEB, "data", "notable.json")
    if not os.path.exists(np_):
        print("   no labels"); return
    N = json.load(open(np_, encoding="utf-8"))
    expect = N.get("expect", {})
    names = {}
    gl = os.path.join(ROOT, "data", "glottolog", "languages.csv")
    if not os.path.exists(gl):
        print("   Glottolog not present — SKIPPED"); return
    levels = {}
    with open(gl, newline="", encoding="utf-8") as f:
        for r in _csv.DictReader(f):
            names[r["ID"]] = r["Name"]
            levels[r["ID"]] = r["Level"]
    bad = []
    for gc in N["by_glottocode"]:
        want = expect.get(gc)
        got = names.get(gc)
        if got is None:
            bad.append(f"{gc} is not a language in Glottolog")
        elif want and want.lower() not in got.lower():
            bad.append(f"{gc} label is about {want!r} but the glottocode is {got!r}")
    gp = os.path.join(WEB, "data", "gallery.json")
    if os.path.exists(gp):
        # Objects hang off FAMILIES as well as languages now — a family card carries its own
        # plate and wall — so the test is that the key is a real Glottolog node, not that it is
        # specifically a language. It must still be a node: a typo'd key is still refused.
        for gc in json.load(open(gp, encoding="utf-8")):
            if gc not in names:
                bad.append(f"gallery image keyed to {gc}, which is not in Glottolog at all")
            elif levels.get(gc) not in ("language", "family"):
                bad.append(f"gallery image keyed to {gc}, a {levels.get(gc)} rather than a "
                           f"language or family")
    if bad:
        for b in bad:
            print("   " + b)
        die(f"{len(bad)} authored label(s) sit on the wrong language")
    print(f"   {len(N['by_glottocode'])} labels checked against Glottolog, all correct")


def gate_alphabets() -> None:
    """The letters must be in the script the language is actually written in.

    Scored against an independent witness: the ISO 15924 code recorded for the UDHR
    translation we ship for that same language. The two come from unrelated places — the CLDR
    survey process and the UN's translators — so agreement is evidence and disagreement is a
    lead. The first run of this check found 206 Canadian syllabics characters being reported
    as a Latin alphabet, which had put a Latin letter-chart on Inuktitut, Swampy Cree and
    Northwestern Ojibwa. Three languages still disagree and all three are genuine: Sorani,
    Uyghur and Hmong Njua are each written in two scripts, and the card says so.
    """
    print("2d. the letters are in the right script")
    ap = os.path.join(WEB, "data", "alphabets.json")
    if not os.path.exists(ap):
        print("   no alphabets — SKIPPED"); return
    A = json.load(open(ap, encoding="utf-8"))
    w = A.get("witness") or {}
    n = w.get("agree", 0) + w.get("disagree", 0)
    if not n:
        die("alphabets.json carries no witness score; rerun build_alphabets.py")
    rate = w["agree"] / n
    if rate < 0.98:
        die(f"only {rate*100:.1f}% of alphabets agree with the script of their own prose "
            f"({w['disagree']} of {n} disagree) — that is a classification bug, not "
            f"biscriptal languages")
    # Every entry must say which tier it came from, and an observed one must carry its sample.
    for gc, v in A["by_glottocode"].items():
        if v.get("tier") not in ("curated", "observed"):
            die(f"{gc} alphabet has no tier")
        if v["tier"] == "observed" and not v.get("sample"):
            die(f"{gc} is an observed inventory with no sample size — rule 10 requires that "
                f"a measurement state what it was measured from")
        if not v.get("groups"):
            die(f"{gc} alphabet has no characters in it")
    print(f"   {A['curated']} curated + {A['observed']} observed · {rate*100:.1f}% agree "
          f"with the script of their own prose ({w['disagree']} biscriptal, disclosed) · "
          f"{w.get('no_witness', 0)} have no witness")


def gate_gallery() -> None:
    """Every object on a card must be a file that exists, with a licence recorded for it.

    gallery.json changed shape from one object per language to a list, and a half-adopted shape
    change is the kind of thing that shows four artefacts in the card and none on the tree. So
    the shape is asserted here, and so is the thing the licence gate exists for: no object may
    ship without the licence Commons reported for that individual file.
    """
    print("2e. gallery objects exist and carry their licence")
    gp = os.path.join(WEB, "data", "gallery.json")
    if not os.path.exists(gp):
        print("   no gallery — SKIPPED"); return
    G = json.load(open(gp, encoding="utf-8"))
    bad, n, mb = [], 0, 0.0
    for gc, objs in G.items():
        if not isinstance(objs, list):
            die(f"gallery entry for {gc} is not a list — the multi-object shape change was "
                f"only half applied")
        for o in objs:
            n += 1
            f = os.path.join(WEB, "img", "gallery", o["file"])
            if not os.path.exists(f):
                bad.append(f"{gc}: {o['file']} is in the manifest but not on disk")
                continue
            mb += os.path.getsize(f) / 1e6
            if not o.get("licence"):
                bad.append(f"{gc}: {o['file']} has no licence recorded")
            # The lightbox shows a full-resolution copy served by Commons; the local file is
            # downscaled to 460-640 px and would look poor filling a screen. Without this
            # field an object opens at thumbnail size and the expanded view is pointless.
            if not str(o.get("big", "")).startswith("https://commons.wikimedia.org/"):
                bad.append(f"{gc}: {o['file']} has no full-resolution URL for the lightbox")
    if bad:
        for b in bad[:20]:
            print("   " + b)
        die(f"{len(bad)} gallery problem(s)")
    multi = sum(1 for v in G.values() if len(v) > 1)
    print(f"   {n} objects across {len(G)} languages ({multi} with more than one) · "
          f"{mb:.1f} MB · every one licence-verified and openable full-size")


def gate_audio() -> None:
    """No recording may claim a language it was not filed under.

    The first audio attempt in this project matched recordings to languages by FILENAME and
    returned a Spanish recording as Basque and `Japanese toilet.ogg` as Hindi-Urdu. It was
    withheld and never shipped. This gate exists so that mistake cannot come back: every
    recording must sit under a Commons category whose ISO 639-3 code is the one recorded for
    the language it is displayed on, every one must carry a licence, and every URL must point at
    the archive rather than at this repository — because we link and do not mirror (rule 12).
    """
    print("2f. every recording is filed under the language it plays on")
    ap = os.path.join(WEB, "data", "audio.json")
    if not os.path.exists(ap):
        print("   no audio — SKIPPED"); return
    A = json.load(open(ap, encoding="utf-8"))
    if "by_glottocode" not in A:
        die("audio.json is in the old single-recording shape; rerun fetch_audio.py")
    lp = os.path.join(WEB, "data", "languages.json")
    L = json.load(open(lp, encoding="utf-8"))
    F = {k: i for i, k in enumerate(L["fields"])}
    iso_of = {r[F["code"]]: r[F["iso"]] for r in L["rows"]}
    bad, n, intext = [], 0, 0
    for gc, v in A["by_glottocode"].items():
        if gc not in iso_of:
            bad.append(f"{gc} is not a language in this build")
            continue
        cat = v.get("category", "")
        if not cat.endswith("-" + v.get("iso", "\x00")):
            bad.append(f"{gc}: category {cat!r} does not end in its own ISO code")
        for it in v.get("items", []):
            n += 1
            if it.get("intext"):
                intext += 1
            if not it.get("licence"):
                bad.append(f"{gc}: a recording of {it.get('w')!r} has no licence")
            u = it.get("url", "")
            if not u.startswith("https://upload.wikimedia.org/"):
                bad.append(f"{gc}: {u[:60]!r} is not streamed from the archive")
            if not it.get("w"):
                bad.append(f"{gc}: a recording has no word attached")
    if bad:
        for b in bad[:20]:
            print("   " + b)
        die(f"{len(bad)} audio problem(s)")
    print(f"   {n:,} recordings across {len(A['by_glottocode'])} languages, all streamed from "
          f"Commons and licence-verified · {intext} are of a word that also appears in that "
          f"language's own passage here · the archive holds {A.get('available', 0):,}")


def gate_phrases() -> None:
    """The authored word-and-phrase tier, and the one claim it has to keep honest.

    Some of these languages were written in scripts whose letterforms could not be set here with
    confidence — Oscan and Umbrian in Old Italic, Sogdian, Khotanese in Brahmi. Their forms are
    transliterations, which is the right answer, but only if the card SAYS SO. An entry whose
    forms carry no separate transliteration and no note reads as if the forms were the language's
    own writing. That is the failure this gate exists to catch.
    """
    print("2h. the authored phrases are filed and their script is disclosed")
    pp = os.path.join(WEB, "data", "phrases.json")
    if not os.path.exists(pp):
        die("phrases.json is missing; run build_phrases.py")
    P = json.load(open(pp, encoding="utf-8"))["by_glottocode"]
    L = json.load(open(os.path.join(WEB, "data", "languages.json"), encoding="utf-8"))
    known = {r[0] for r in L["rows"]}
    bad, translit_only = [], 0
    for gc, rec in P.items():
        if gc not in known:
            bad.append(f"{gc} is not a language in this atlas")
            continue
        items = rec.get("items") or []
        if not items:
            bad.append(f"{gc} has no forms")
        for f, t, gl in items:
            if not f.strip() or not gl.strip():
                bad.append(f"{gc} has a form or gloss that is empty")
        if items and not any((t or "").strip() for _, t, _ in items):
            translit_only += 1
            if not (rec.get("note") or "").strip():
                bad.append(f"{gc} shows bare forms with no note saying what script they are in")
    for b in bad:
        die(b)
    n = sum(len(r["items"]) for r in P.values())
    print(f"   {len(P)} languages, {n} forms, every one filed under a real language · "
          f"{translit_only} are transliterations, each saying so on the card")


def gate_descriptions() -> None:
    """Every language must have something said about it, and a composed sentence must be
    distinguishable from an authored one.

    The measurement that made this necessary: 7,970 of 8,618 language nodes carried a
    description field, which reads as 92% coverage until you look at it — 4,627 of them said the
    single word "language". Real coverage was 36%. Compositions close that to 100%, and the gate
    holds it there so a later change cannot quietly reopen the hole.
    """
    print("2g. every language has a description, and its kind is disclosed")
    dp = os.path.join(WEB, "data", "descriptions.json")
    fp = os.path.join(WEB, "data", "families.json")
    if not os.path.exists(dp) or not os.path.exists(fp):
        print("   not built — SKIPPED"); return
    D = json.load(open(dp, encoding="utf-8"))
    FAM = json.load(open(fp, encoding="utf-8"))
    comp = D.get("by_glottocode") or {}
    labels = set(json.load(open(os.path.join(WEB, "data", "notable.json"),
                                encoding="utf-8"))["by_glottocode"])
    import glob as _glob
    import re as _re
    GEN = _re.compile(r"^(language|language family|dialect|extinct language|natural language|"
                      r"macrolanguage|dead language|human language|ancient language|"
                      r"sign language|creole language|pidgin|language group)\.?$", _re.I)
    missing, total = [], 0
    for f in _glob.glob(os.path.join(WEB, "data", "tree", "*.json")):
        if f.endswith("index.json"):
            continue
        def walk(n):
            nonlocal total
            if n.get("lv") == 1:
                total += 1
                gc = n["g"]
                d = (n.get("d") or "").strip()
                own = bool(d) and len(d) > 16 and not GEN.match(d)
                if gc not in labels and gc not in comp and not own:
                    missing.append(gc)
            for k in (n.get("c") or []):
                walk(k)
        walk(json.load(open(f, encoding="utf-8")))
    if missing:
        print("   " + " ".join(missing[:12]))
        die(f"{len(missing)} of {total} languages have nothing said about them")
    # The composed text must never be presented as authored: a glottocode cannot be in both.
    both = set(comp) & labels
    if both:
        die(f"{len(both)} languages carry both an authored label and a composed description "
            f"({' '.join(sorted(both)[:6])}) — the card would show two different kinds of claim "
            f"as one")
    nf = len(FAM.get("by_glottocode") or {})
    nd = len(FAM.get("clusters_by_node") or {})
    print(f"   {total:,} languages, every one described · {len(comp):,} composed from the "
          f"record, {len(labels)} authored, the rest their own · {nf} family cards · "
          f"{nd} nodes explain their own naming")


def gate_registration() -> None:
    """Re-check the shipped raster, not the pipeline's memory of it (TRAPS §D5)."""
    print("3. registration, read back from the shipped PNG")
    try:
        import numpy as np
        from PIL import Image
    except Exception as e:
        die(f"cannot verify the shipped raster: {e}")
    fd = os.path.join(WEB, "fields")
    meta = json.load(open(os.path.join(fd, "fields.json")))
    T, S, L = meta["tile"], meta["skirt"], meta["maxLevel"]
    cols, rows = 2 << L, 1 << L
    have = set(meta["tiles"][str(L)])
    cache = {}

    def at(la, lo):
        """Read the DEEPEST shipped tile covering this place — the highest-resolution bytes
        the viewer will actually be served, not a convenient overview."""
        u = ((lo + 180.0) % 360.0) / 360.0
        v = (90.0 - la) / 180.0
        for lvl in range(L, -1, -1):
            c2, r2 = 2 << lvl, 1 << lvl
            tx, ty = min(c2 - 1, int(u * c2)), min(r2 - 1, int(v * r2))
            if f"{tx}_{ty}" not in set(meta["tiles"][str(lvl)]):
                continue
            k = (lvl, tx, ty)
            if k not in cache:
                cache[k] = np.asarray(Image.open(
                    os.path.join(fd, f"z{lvl}", f"terrain_{tx}_{ty}.png")).convert("RGBA"))
            a = cache[k]
            px = S + min(T - 1, int((u * c2 - tx) * T))
            py = S + min(T - 1, int((v * r2 - ty) * T))
            return ((int(a[py, px, 0]) * 256 + int(a[py, px, 1])) / 65535.0) * 20000.0 - 11000.0
        return float("nan")
    cases = [("Everest", 27.99, 86.93, 6000, None), ("Dead Sea", 31.5, 35.5, None, 0),
             ("North China Plain", 35.5, 116.5, 0, 300), ("Gabon", -0.5, 12.5, 0, 900),
             ("mid-Atlantic", 0.0, -30.0, None, -2000),
             ("East Antarctica", -75.0, 0.0, 1500, None)]
    bad = [f"{n}={at(la, lo):.0f}m" for n, la, lo, lob, hib in cases
           if (lob is not None and at(la, lo) < lob) or (hib is not None and at(la, lo) > hib)]
    if bad:
        die("the SHIPPED raster is not registered to the real Earth: " + "; ".join(bad))
    print(f"   {len(cases)}/{len(cases)} named places in range "
          f"(Everest {at(27.99,86.93):.0f} m, Dead Sea {at(31.5,35.5):.0f} m)")


def gate_attribution() -> None:
    """A5. The shipped ledger must BE the module's output, byte for byte.

    A hand-written sources list in an About panel is not an attribution ledger: it drifts from
    the ingest the first time a source is added, and nobody notices, because nothing checks it.
    So the module is the authority and this regenerates the shipped file from it. If they ever
    differ, that difference is the bug — publish the regenerated one and fail loudly.
    """
    print("3b. attribution ledger")
    sys.path.insert(0, MODELING)
    import attribution
    attribution._selftest()
    want = attribution.to_json()
    p = os.path.join(WEB, "data", "attribution.json")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    got = open(p, encoding="utf-8").read() if os.path.exists(p) else None
    if got != want:
        open(p, "w", encoding="utf-8").write(want)
        if got is not None:
            die("web/data/attribution.json had drifted from attribution.py. It has been "
                "REGENERATED — inspect the diff, then re-run. (A stale ledger means the app "
                "was crediting sources it no longer uses, or failing to credit ones it does.)")
        print("   generated web/data/attribution.json")
    sa = attribution.share_alike_ingested()
    print(f"   {len(attribution.ingested())} sources ingested, all licence-verified · "
          f"{len(sa)} ShareAlike{' — our emitted data inherits SA' if sa else ''}")


def gate_coverage() -> None:
    """B4/D8. Recompute coverage from the SHIPPED rasters every build, so the number in the
    About panel is a measurement of the artefact rather than a remembered figure."""
    print("3c. coverage, measured from the shipped rasters")
    p = subprocess.run([sys.executable, os.path.join(MODELING, "coverage.py")],
                       capture_output=True, text=True)
    if p.returncode != 0:
        print(p.stdout[-1200:]); print(p.stderr[-1200:])
        die("coverage.py failed against the shipped rasters")
    for ln in p.stdout.strip().splitlines():
        if ln.startswith(("land", "today", "before")):
            print("   " + ln)


def gate_no_year_on_before_contact() -> None:
    """A4, enforced rather than trusted.

    Rule 15: the earlier snapshot is a per-region STATE, not a year. Contact runs from the
    1490s to the twentieth century and never happened in some places, so printing one year on
    that snapshot would be the frame error of the project. `frames.snapshot_label` refuses it
    in Python — but the app's labels are authored in HTML and JS, where nothing was checking.
    This greps the shipped surfaces for a four-digit year near the snapshot control.
    """
    print("3d. no year on the before-contact snapshot")
    import re as _re
    bad = []
    for f in ("index.html", os.path.join("js", "app.js"), os.path.join("js", "tree.js")):
        s = open(os.path.join(WEB, f), encoding="utf-8").read()
        for m in _re.finditer(r"before[ _]?contact", s, _re.I):
            window = s[max(0, m.start() - 90):m.end() + 90]
            for y in _re.finditer(r"\b1[4-9]\d\d\b|\b20[0-2]\d\b", window):
                # A century range in prose ("the 1490s to the twentieth century") is the
                # honest statement, not the error; a bare year label is the error.
                if "s to the" not in window and "ranges from" not in window:
                    bad.append(f"{f}: '{y.group()}' next to '{m.group()}'")
    if bad:
        die("a year is rendered on the before-contact snapshot (rule 15): " + "; ".join(bad))
    print("   clean — the earlier snapshot is labelled as a state, not a date")


def stamp() -> str:
    """Bump the data version in web/index.html BEFORE anything is copied."""
    print("4. data-version stamp")
    v = str(int(time.time()))
    p = os.path.join(WEB, "index.html")
    s = open(p, encoding="utf-8").read()
    if 'name="data-version"' not in s:
        die("web/index.html has no data-version meta tag")
    s = re.sub(r'(name="data-version" content=")\d+(")', rf"\g<1>{v}\g<2>", s)
    s = re.sub(r"\?v=\d+", f"?v={v}", s)
    open(p, "w", encoding="utf-8").write(s)
    print(f"   stamped {v}")
    return v


def publish(v: str) -> None:
    print("5. web/ -> docs/")
    total = _web_size_mb()
    print(f"   web/ total {total:.1f} MB (budget {BUDGET_TOTAL_MB:.0f} MB)")
    if total > BUDGET_TOTAL_MB:
        die(f"web/ is {total:.1f} MB, over the {BUDGET_TOTAL_MB:.0f} MB budget in SCOPE §11")
    if os.path.exists(DOCS):
        shutil.rmtree(DOCS)
    shutil.copytree(WEB, DOCS)
    open(os.path.join(DOCS, ".nojekyll"), "w").close()
    n = sum(len(fs) for _, _, fs in os.walk(DOCS))
    got = open(os.path.join(DOCS, "index.html"), encoding="utf-8").read()
    if v not in got:
        die("the copied index.html does not carry the stamp — copy order is wrong")
    print(f"   {n} files, stamp {v} present in docs/index.html")
    print(f"\nPublished locally. After pushing, verify the LIVE stamp:")
    print(f'   curl -s https://augustg97.github.io/mother-tongues/ | grep data-version')
    print(f"   expect: {v}")


if __name__ == "__main__":
    print("build_site.py — the only route to publication\n")
    gate_selftests()
    gate_fields()
    gate_js()
    gate_labels()
    gate_alphabets()
    gate_gallery()
    gate_audio()
    gate_phrases()
    gate_descriptions()
    gate_registration()
    gate_attribution()
    gate_coverage()
    gate_no_year_on_before_contact()
    publish(stamp())
