# Handoff — Mother Tongues

Paste this whole file as the first message of a new session.

---

## What you are working on

**Mother Tongues** — Every human language we know of, on the ground it is spoken on

- Repo: `/Users/augustgweon/Mother Tongues` · GitHub: not yet created (first ship makes `augustg97/mother-tongues`)`
- Live: none yet. First ship enables Pages on `main:/docs` → https://augustg97.github.io/mother-tongues/
- **Read `README.md` first.** It documents the goals, the standing working rules (§2), every
  subsystem, the traps that have cost time (§7), and the known limits (§9).
- `SCOPE.md` is the contract: the claim, the layer table, the canonical frame, the evidence
  boundary, the card contract, the standard for done, the non-goals.

## The current task

**Round 1 — the datum-and-substrate round** (`Research/README.md` has the full ordering).
It is not negotiable: **frames before joins, substrate before layers, spine before polish.**

1. **A1 — `Research/modeling/frames.py` with selftests.** Glottocode as key, ISO 639-3 as alias
   only, autonym-first name resolution with alias tables, (value, year, source) for counts.
   *Nothing may be joined until this passes.*
2. **A2 + A3 — the ingest gates.** Reproject GHS-POP Mollweide→WGS84 once, record the residual.
   Gate the Glottography ingest per-repo so the three CC-BY-NC sets are excluded by machine.
3. **B3 → B1 — measure, then build the substrate.** Histogram quantisation levels in the *land*
   relief band before choosing an encoding. Then the lit-terrain substrate, screenshotted against
   the SCOPE §3 sentence. **This is the round's gate.**
4. **B2 — the language field**, composed per pixel.
5. **C1 + C2 — the diversity model and its per-cell residual audit.**
6. **E1 — the census witness**, early, because it settles later disputes.

<!-- If the user set an explicit loop, state it verbatim and state its stopping condition,
     because a loop overrides the standing "always deploy every round" rule:

> "keep going and making improvements until <condition>. After making updates, compare against
>  <reference>, then assess honestly. If yes, deploy; if no, continue and repeat."
-->

## Reference material and the measurement harness

The comparison is only meaningful at **matched scale**, and getting there takes a while — reuse
this rather than rebuilding it.

- **Tectonic Earth** (`~/Tectonic Plate Model`) is the standing architectural reference and the
  *only* exemplar in the house set — read its FRAG shader, its lazy loader and its `window.APP`
  verification harness before building the field engine. Territorial US and Aztec Conquest are
  **deprecated as references**; the AI Atlas is a cautionary case (a rendered abstract space still
  reads as a chart).
- **Plate 01 of `~/Modeling Studio/CANDIDATE-PROJECTS.md`** is this project's pre-filled scope, and
  its appendix §01 is the full source survey with every count and licence.

None yet. Round 1 adds the `frames.py` selftest and the diversity residual audit; the app should
expose a console handle (`APP.jumpTo`, `APP.state`) so visual verification is scriptable.

## State right now

- Last live deploy: **none — never deployed** (commit `—`)
- Committed and not deployed: everything; three commits exist and nothing has shipped
- Uncommitted: nothing (check `git status`)
- App: the scaffold's hybrid shell at `web/`, serving on port 8146 — **verified rendering**
  (title, chapters, layers, timeline, one placeholder dot). `web/fields/` is empty; `build/` has
  only a README. **The field engine does not exist yet**, and the shell is deliberately the
  dots-on-flat-ground placeholder that rule 0 exists to replace.

## What this round found

All measured, none guessed.

1. **The polygon problem is solved, and recently.** A CC-BY global language-polygon dataset
   published in 2025 covers **5,297 glottocodes = 62.5% of living languages in 3.9 MB gzipped**.
   This was the plate's largest stated risk and it is closed.
2. **The real risks are audio and method.** Openly licensed audio covers **6–8%** of languages,
   and the reason is community consent, not oversight. And **no global continuous linguistic
   surface has ever been built** — only regional dialectometry by kriging. We own the method risk.
3. **The deep past is nine languages.** Of ~217 with attestation dates, 82 have a polygon; nine are
   pre-Common-Era. Hence SCOPE §12 D1: v1 builds the surface, not the time axis.
4. **Population is floored at 1975**, because the deep-time gridded population dataset is
   NonCommercial.
5. **Two scaffold bugs were found and fixed** here and upstream in `Modeling Studio/scaffold/` —
   the shell landed outside the directory `launch.json` serves, and an unanchored `data/` in
   `.gitignore` silently excluded the app's own data from the first commit.

## Traps that have each cost real time

See `CLAUDE.md` §Traps and `README.md` §7 — the ones that will bite first:

- **the scaffold shell is dots on flat ground**; do not add a feature layer to it (rule 0);
- **Glottolog's three language counts are all correct** and get conflated — label which is in use;
- **3 of Glottography's 34 repos are CC-BY-NC** although its platform paper says otherwise;
- **GHS-POP is Mollweide** — reproject once, record the residual;
- **PanLex is CC-BY-NC-SA, not CC0**;
- **one Phlorest tree's unit field yields 692,970 years** — sanity-check every tree;
- **the parallel-prose corpus has no licence** and ships under SCOPE §12 D2 behind a feature flag.

Plus the standing ones:

- a process backgrounded with `&` inside a tool call dies when that call ends; `nohup` does not
  save it. The tell is a log that stops after one line.
- `pgrep -f <script>` matches the waiter's own command line. **Wait on a PID** —
  `until ! kill -0 "$PID"`.
- a static host can serve stale JSON after a successful push. Stamp the data version **before**
  copying the app file, and verify the live value.

## The work queue

Ranked by how much of the remaining gap each closes.

1. **A1 frames.py** — nothing may be joined before it.
2. **B1 + B2** — the lit substrate and the language field. Until the frame reads as a rendered
   world, no other item counts.
3. **C1** — the diversity model with its per-cell residual audit (the spine).
4. **A2** — the Mollweide→WGS84 reprojection with a recorded residual.
5. **E1** — the census witness.
6. **F1** — two emails: the UDHR maintainer (retires the D2 risk) and the NC-by-default audio
   archive (would multiply coverage severalfold).

## Commands

```bash
# run the app locally (port 8146; registered in ~/.claude/launch.json)
python3 -m http.server 8146 --directory "/Users/augustgweon/Mother Tongues/web"
# or: preview_start name="mother-tongues"

# the research loop
cd Research/modeling && python3 frames.py && python3 audit_all.py

# deploy (only route, once build_site.py exists)
python3 build/build_site.py && git add -A && git commit && git push
# then verify the live data-version stamp
```

## How the user wants this done

Read the working rules in `README.md` §2 — each came from a specific failure. The ones that
matter most:

- **Visually verify.** Render it and look. Statistics are not confirmation.
- **Fix the system, not the instance.**
- **Measure before tuning.**
- **Address every item raised**, and say so explicitly when something cannot be done.
- **Be honest in the assessment** — the user has asked for a truthful yes/no against the
  reference, not an optimistic one.
