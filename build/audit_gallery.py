#!/usr/bin/env python3
"""audit_gallery.py — contact sheets of the gallery, so the objects can actually be looked at.

WHY. The licence gate admits a file on its licence. The title filter rejects project icons, flags
and word clouds by name. Neither can tell whether a photograph is of the thing it claims to
illustrate, and August found the consequence: portraits of people with no visible connection to
the language, irrelevant graphics, and the covers of academic works *about* a language rather than
anything written *in* it.

There is no rule that fixes that. The only honest audit is to look, so this lays the collection out
as numbered contact sheets — plates first, because the plate is what a visitor sees before they
have read a word — and writes an index mapping every cell to its glottocode, title and subject.
Verdicts go back in as a keep/drop list, and the drops are refetched from a different subject.

Run: python3 audit_gallery.py [--all | --walls] [--from people]
"""
from __future__ import annotations

import json
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
WEB = os.path.join(ROOT, "web", "data")
IMG = os.path.join(ROOT, "web", "img", "gallery")
OUT = os.path.join(ROOT, "data", "gallery", "audit")

COLS, ROWS = 8, 6            # 48 to a sheet: small enough to see, few enough sheets to read
CELL = 190
LABEL = 16


def sheet(items: list[dict], path: str, start: int) -> None:
    """⚠ THE LABEL GOES ABOVE ITS OWN IMAGE, and a rule separates the cells.

    The first version put the caption UNDERNEATH each picture. Reading the sheet, I attached
    every caption to the picture above it instead of the one below it, which shifted the whole
    verdict list by one row — eight languages — and I nearly rejected the Adinkra alphabet chart
    as a blank and a Cheyenne pictographic account as junk. Label first, then the thing it names.
    """
    w, h = COLS * CELL, ROWS * (CELL + LABEL)
    im = Image.new("RGB", (w, h), (247, 243, 234))
    d = ImageDraw.Draw(im)
    for k, it in enumerate(items):
        cx, cy = (k % COLS) * CELL, (k // COLS) * (CELL + LABEL)
        d.line([cx, cy, cx + CELL, cy], fill=(190, 178, 158))
        d.text((cx + 5, cy + 3), f"{start + k}  {it['n'][:26]}", fill=(30, 26, 20))
        try:
            with Image.open(os.path.join(IMG, it["file"])) as src:
                src = src.convert("RGB")
                src.thumbnail((CELL - 8, CELL - 8), Image.LANCZOS)
                im.paste(src, (cx + (CELL - src.width) // 2,
                               cy + LABEL + (CELL - src.height) // 2))
        except Exception:                                    # noqa: BLE001
            d.rectangle([cx + 4, cy + LABEL + 4, cx + CELL - 4, cy + LABEL + CELL - 4],
                        outline=(180, 60, 60))
    im.save(path, "JPEG", quality=82, optimize=True)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    G = json.load(open(os.path.join(WEB, "gallery.json"), encoding="utf-8"))
    langs = json.load(open(os.path.join(WEB, "languages.json"), encoding="utf-8"))
    F = {k: i for i, k in enumerate(langs["fields"])}
    name = {r[F["code"]]: r[F["name"]] for r in langs["rows"]}
    fams = json.load(open(os.path.join(WEB, "families.json"), encoding="utf-8"))
    for gc, v in fams["by_glottocode"].items():
        name.setdefault(gc, v["n"])

    only_from = None
    if "--from" in sys.argv:
        only_from = sys.argv[sys.argv.index("--from") + 1]
    # --langs restricts the sheet to a comma-separated list of glottocodes. This is what a new
    # batch of labels needs: the whole gallery is 873 objects and re-auditing all of it to look at
    # twenty new ones is how a batch goes unlooked-at.
    only_langs = None
    if "--langs" in sys.argv:
        only_langs = set(sys.argv[sys.argv.index("--langs") + 1].split(","))

    items = []
    for gc, objs in sorted(G.items()):
        if only_langs and gc not in only_langs:
            continue
        for i, o in enumerate(objs):
            if only_from and not o["subject"].endswith(only_from):
                continue
            if only_langs:
                items.append({"gc": gc, "i": i, "file": o["file"], "n": name.get(gc, gc),
                              "title": o["title"], "subject": o["subject"]})
                continue
            if "--walls" in sys.argv and i == 0:
                continue                    # the plates are audited; these are the cases behind
            if (not only_from and "--all" not in sys.argv and "--walls" not in sys.argv
                    and i != 0):
                continue                                     # plates only, by default
            items.append({"gc": gc, "i": i, "file": o["file"], "n": name.get(gc, gc),
                          "title": o["title"], "subject": o["subject"]})

    idx = []
    for s in range(0, len(items), COLS * ROWS):
        chunk = items[s:s + COLS * ROWS]
        p = os.path.join(OUT, f"sheet{s // (COLS * ROWS):02d}.jpg")
        sheet(chunk, p, s)
        for k, it in enumerate(chunk):
            idx.append(dict(it, cell=s + k, sheet=os.path.basename(p)))
        print(f"   {os.path.basename(p)}  cells {s}–{s + len(chunk) - 1}")
    json.dump(idx, open(os.path.join(OUT, "index.json"), "w"), ensure_ascii=False, indent=1)
    print(f"\n{len(items)} objects across {len(idx) and (len(items) - 1) // (COLS * ROWS) + 1} "
          f"sheets · index written to data/gallery/audit/index.json")
