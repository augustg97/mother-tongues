#!/usr/bin/env python3
"""fetch_texts.py — the text tier: one real passage per language, in its own script.

Register **D2**, and the licence position is a recorded decision, not an oversight.

THE UDHR CORPUS HAS NO LICENCE FILE. The Universal Declaration itself is a UN document and
the UN's own terms are restrictive; this compilation of translations (Eric Muller's UDHR in
XML, the successor to the Unicode UDHR project) carries no licence statement at all. SCOPE
§12 **D2** records the user's decision to ship it anyway on the "commons" claim, knowingly,
with three mitigations that are part of the decision and must not be dropped:

  1. **per-block provenance** — every passage carries its source and its language tag;
  2. **a single feature flag** — `web/data/texts.json` is the only artefact, so the whole
     tier is removable in one commit;
  3. **a takedown path** stated in the About panel.

Article 1 only. One paragraph per language is the minimum that demonstrates a script and a
sentence, and taking less of a work is the cheaper position if anyone ever objects.

Also fetches **Phlorest** root ages where they exist: dated phylogenies for ~30 families,
CC-BY, which is the only real time depth this project can honestly draw.

Run: python3 fetch_texts.py
"""
from __future__ import annotations

import io
import json
import os
import re
import ssl
import urllib.request
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "data", "texts")
UA = "MotherTongues/1.0 (research atlas; augustgweon@gmail.com)"
UDHR_ZIP = "https://codeload.github.com/eric-muller/udhr/zip/refs/heads/main"


def _get(url: str, timeout: int = 300) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout,
                                context=ssl.create_default_context()) as r:
        return r.read()


def fetch_udhr() -> dict:
    """Article 1 per language, keyed by ISO 639-3, with its script and direction.

    ⚠ The XML uses SINGLE-quoted attributes and names the script `iso15924`, not `script`.
    A double-quote-only regex silently matched 99 of 529 files and reported zero scripts —
    a partial parse that looks like a partial corpus rather than like a bug. Quote style is
    not semantic in XML; never anchor on it.
    """
    print("UDHR in XML")
    cache = os.path.join(OUT, "udhr.zip")
    if os.path.exists(cache):
        raw = open(cache, "rb").read()
        print(f"   {len(raw)/1e6:.1f} MB (cached)")
    else:
        raw = _get(UDHR_ZIP)
        os.makedirs(OUT, exist_ok=True)
        open(cache, "wb").write(raw)
        print(f"   {len(raw)/1e6:.1f} MB")
    out: dict[str, dict] = {}
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names = [n for n in z.namelist()
                 if re.search(r"/udhr_[a-z0-9_\-]+\.xml$", n) and "/retired/" not in n]
        print(f"   {len(names)} translation files")
        for n in names:
            try:
                x = z.read(n).decode("utf-8", "replace")
            except Exception:                                   # noqa: BLE001
                continue
            q = "[\"']"
            iso = re.search(r"\biso639-3=" + q + r"([a-z]{3})" + q, x)
            if not iso:
                continue
            script = re.search(r"\biso15924=" + q + r"([A-Za-z]+)" + q, x)
            direction = "rtl" if re.search(r"\bdir=" + q + r"rtl" + q, x) else "ltr"
            tag = re.search(r"\bxml:lang=" + q + r"([A-Za-z0-9\-]+)" + q, x)
            # Article 1 is <article number="1"> with <title> and <para>. Take the paras.
            art = re.search(r"<article[^>]*number=" + q + r"1" + q + r".*?</article>", x, re.S)
            if not art:
                continue
            paras = re.findall(r"<para>(.*?)</para>", art.group(0), re.S)
            body = " ".join(re.sub(r"<[^>]+>", "", p) for p in paras)
            body = re.sub(r"\s+", " ", body).strip()
            if len(body) < 20:
                continue
            k = iso.group(1)
            # Prefer the longest rendering when a language has several orthographies.
            if k not in out or len(body) > len(out[k]["text"]):
                out[k] = {"text": body[:600], "script": script.group(1) if script else "",
                          "dir": direction, "tag": tag.group(1) if tag else k,
                          "file": os.path.basename(n)}
    scripts = sorted({v["script"] for v in out.values() if v["script"]})
    print(f"   {len(out)} languages, {len(scripts)} scripts")
    return {"source": "UDHR in XML (E. Muller), UN translations of the Universal "
                      "Declaration of Human Rights, Article 1",
            "licence": "NO LICENCE STATEMENT — ships under SCOPE §12 D2",
            "takedown": "augustgweon@gmail.com",
            "scripts": scripts, "by_iso639_3": out}


def _newick_depth(nwk: str) -> float:
    """Maximum root-to-tip branch-length sum. Written by hand; the trees are small."""
    best = 0.0
    stack = [0.0]
    depth = 0.0
    i = 0
    n = len(nwk)
    while i < n:
        c = nwk[i]
        if c == "(":
            stack.append(depth)
            i += 1
        elif c in ",)":
            best = max(best, depth)
            if c == ")":
                depth = stack.pop()
            else:
                depth = stack[-1]
            i += 1
        elif c == ":":
            m = re.match(r":(-?[0-9.eE+]+)", nwk[i:])
            if m:
                try:
                    depth += float(m.group(1))
                except ValueError:
                    pass
                i += m.end()
            else:
                i += 1
        else:
            i += 1
    return max(best, depth)


def fetch_phlorest_ages() -> dict:
    """Root age per family from the dated MCC summary tree.

    ⚠ CLAUDE.md's standing trap: **do not trust the scaling field**. One Phlorest tree's
    stated unit yields 692,970 years for a language family. Every age here is therefore
    sanity-checked against the linguistic horizon — comparative reconstruction does not
    reach past roughly 10,000 years, and nothing shallower than ~300 years is a family —
    and anything outside that band is recorded as REJECTED with its number, not silently
    dropped and not silently used.
    """
    print("\nPhlorest dated phylogenies")
    try:
        repos = json.loads(_get("https://api.github.com/orgs/phlorest/repos?per_page=100", 120))
    except Exception as e:                                      # noqa: BLE001
        print(f"   cannot list phlorest: {e}")
        return {}
    out: dict[str, dict] = {}
    rejected = []
    for repo in repos:
        name = repo["name"]
        base = f"https://raw.githubusercontent.com/phlorest/{name}/main/cldf"
        try:
            tre = _get(base + "/summary.trees", 90).decode("utf8", "replace")
        except Exception:                                       # noqa: BLE001
            continue
        try:
            tcsv = _get(base + "/trees.csv", 60).decode("utf8", "replace")
        except Exception:                                       # noqa: BLE001
            tcsv = ""
        scaling = ""
        m = re.search(r"\b(years|centuries|millennia|change|substitutions)\b", tcsv, re.I)
        if m:
            scaling = m.group(1).lower()
        # The Nexus "tree ... = " line carries the Newick.
        tm = re.search(r"=\s*(\[[^\]]*\])?\s*(\(.*;)", tre, re.S)
        if not tm:
            continue
        depth = _newick_depth(tm.group(2))
        # "substitutions" and "change" are not units of TIME — they are units of amount of
        # linguistic change. A tree scaled that way has no date in it at all, and reading its
        # depth as years is the same category error as the 613,594-year root, just quieter:
        # it produced a plausible-looking 409 years for a family thousands of years old.
        if scaling in ("substitutions", "change"):
            rejected.append((name, "not a time unit: " + scaling))
            continue
        mult = {"years": 1.0, "centuries": 100.0, "millennia": 1000.0}.get(scaling)
        if mult is None:
            # No usable unit. Infer: a plausible family root is 300..12000 years, so pick
            # the power of ten that lands the depth inside it, and mark it inferred.
            mult = 1.0
            for cand in (1.0, 100.0, 1000.0):
                if 300 <= depth * cand <= 12000:
                    mult = cand
                    break
        age = depth * mult
        gcs = re.findall(r"\b([a-z]{4}[0-9]{4})\b", _get(base + "/languages.csv", 60)
                         .decode("utf8", "replace")) if True else []
        if not (300 <= age <= 12000):
            rejected.append((name, f"{round(age):,}y implausible"))
            continue
        out[name] = {"age_years": round(age), "scaling": scaling or "inferred",
                     "explicit_unit": scaling in ("years", "centuries", "millennia"),
                     "glottocodes": sorted(set(gcs))}
    ex = sum(1 for v in out.values() if v["explicit_unit"])
    print(f"   {len(out)} families dated ({ex} with an explicit time unit, "
          f"{len(out)-ex} inferred), {len(rejected)} rejected: "
          + "; ".join(f"{n} {a}" for n, a in rejected[:8]))
    return out


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    u = fetch_udhr()
    json.dump(u, open(os.path.join(OUT, "udhr.json"), "w"), ensure_ascii=False)
    p = fetch_phlorest_ages()
    json.dump(p, open(os.path.join(OUT, "phlorest.json"), "w"), ensure_ascii=False)
    print(f"\nwrote data/texts/udhr.json ({len(u['by_iso639_3'])} languages) "
          f"and phlorest.json ({len(p)})")
