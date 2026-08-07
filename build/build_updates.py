#!/usr/bin/env python3
"""build_updates.py — the update log, generated from git history.

WHY GENERATED. A hand-written changelog drifts from the build the first time somebody ships
without editing it, and nothing catches the drift. This reads `git log`, so a round appears in
the log if and only if it was actually committed. Same discipline as the attribution ledger and
the coverage figures: the page states what the repository can prove.

WHAT IT TAKES. The commit subject is the round's headline. The body's first paragraph is its
summary — these commit messages are written as round notes, so the body is already the right
prose. Merge commits and mechanical commits are skipped.

Run: python3 build_updates.py
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
WEB = os.path.join(ROOT, "web", "data")

SEP = "\x1e"        # record separator; commit bodies contain every printable character
FLD = "\x1f"

# Commits that are not rounds: no reader wants "fix typo" in a museum's update log.
SKIP = re.compile(r"^(merge |wip\b|fixup|typo|amend|revert )", re.I)


def main() -> None:
    fmt = FLD.join(["%H", "%aI", "%s", "%b"]) + SEP
    p = subprocess.run(["git", "log", "--no-merges", f"--pretty=format:{fmt}"],
                       cwd=ROOT, capture_output=True, text=True)
    if p.returncode != 0:
        sys.exit("build_updates: git log failed\n" + p.stderr[-800:])

    out = []
    for rec in p.stdout.split(SEP):
        rec = rec.strip("\n")
        if not rec.strip():
            continue
        parts = rec.split(FLD)
        if len(parts) < 3:
            continue
        sha, when, subject = parts[0], parts[1], parts[2]
        body = parts[3] if len(parts) > 3 else ""
        if SKIP.match(subject):
            continue
        # The first paragraph of the body is the round's summary. Strip the trailer.
        body = re.sub(r"\n*Co-Authored-By:.*$", "", body, flags=re.S).strip()
        para = body.split("\n\n")[0].replace("\n", " ").strip() if body else ""
        out.append({"sha": sha[:9], "date": when[:10], "title": subject, "summary": para})

    json.dump({"note": "Generated from git history by build_updates.py. A round is here if and "
                       "only if it was committed; this log cannot drift from what shipped.",
               "rounds": out},
              open(os.path.join(WEB, "updates.json"), "w"), ensure_ascii=False,
              separators=(",", ":"))
    dated = out[-1]["date"] if out else "?"
    print(f"updates: {len(out)} rounds, {dated} to {out[0]['date'] if out else '?'}")


if __name__ == "__main__":
    main()
