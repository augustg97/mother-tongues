# Handoff — Mother Tongues

Paste this whole file as the first message of a new session.

---

## What you are working on

**Mother Tongues** — Every human language we know of, on the ground it is spoken on

- Repo: `/Users/augustgweon/Mother Tongues` · GitHub: `augustg97/mother-tongues`
- Live: https://augustg97.github.io/mother-tongues/ — Pages on `main:/docs`, served locally on 8146
- **Read `README.md` first.** It documents the goals, the standing working rules (§2), every
  subsystem, the traps that have cost time (§7), and the known limits (§9).
- `SCOPE.md` is the contract: the claim, the layer table, the canonical frame, the evidence
  boundary, the card contract, the standard for done, the non-goals.

## The current task

**LIVE.** 90 rounds. Deep research passes closed for Indo-European, Sino-Tibetan and
Pama-Nyungan, and the atlas-wide fixable gap — a language with a published grammar and nothing
here — is at zero.

**THREE views**, and GENEALOGY is the default:

- **GENEALOGY** — 429 families, 8,618 languages, dated roots for 19. A global search over all
  7,672 rows by reference name and autonym (diacritics folded). Tip labels win their line over
  fork labels; forks fall back to the left of their node and drop their count before their
  name; a numbered depth axis; collapsed buds sized to the number they carry.
- **GROUND** — 16384×8192 tile pyramid, measured surface. Two chrome panels, not four; the
  cursor readout is a fact table on a plate; the legend folds.
- **INDEX** — the whole atlas as one squarified treemap, 7,672 cells. Area is one-cell-each or
  by-speakers; colour is by-family or by-vitality. Clicking a cell hands you to the genealogy.

Moving between places is a Van Wijk flight (`state.flyTo`), not a cut, and pressing GROUND with
a language selected in the genealogy flies you to it at span 26.

Cards lead with the autonym, carry Article 1 of the UDHR in the language's own script, and long
ones grow a sticky section spine. Every card write goes through `setExhibit()`, which resets
scroll — do not write `#exhibit.innerHTML` directly.

**Next, in priority order:**

**E1 and A7 are CLOSED (round 7).** The witness lives in `Research/modeling/witness.py` and
runs in the build gate; the ingest goes through `frames.Registry`. **D5 is CLOSED** (WALS prose, 1,668 languages). **D3 was attempted and WITHHELD** — the licence
gate works, language identification does not; see the register. **C4 RESOLVED and C8 CLOSED (negative result) in round 9. THE ORIGINAL REGISTER IS NOW EMPTY.**
**C10 CLOSED** (block bootstrap: every SE was ~3x too narrow, all four predictors still exclude
zero). **D3 SHIPPING** (Lingua Libre, 15 recordings, language from the catalogue key).
**D9 CLOSED. THE REGISTER IS EMPTY — original items and everything the work raised since.**
Autonyms: 918 languages (12.0%) but **93.4% of speakers**. Anything from here is new scope. **The enrichment loop RAN AND FINISHED: 242 labels, 158 objects across 8 passes** — IE depth,
Sino-Tibetan, Afro-Asiatic, Austronesian, Uralic, Atlantic-Congo/Mande, Trans-New-Guinea, the
Americas. The next passes are (a) more IE depth —
Middle English, Old Prussian, Umbrian, Oscan, Sogdian, Bactrian, Prakrit, Kashmiri, Sorbian;
(b) then the same treatment family by family, starting with Sino-Tibetan, Afro-Asiatic,
Austronesian and Uralic. Author labels ONLY through `build/build_notable.py`, which resolves
glottocodes by exact Glottolog name and refuses anything ambiguous. D3's per-file licence gate now exists in `build/fetch_gallery.py` and is the
pattern to copy for audio.

**1. D3 — audio.** Planned for round 1, still not built after four rounds. It is
now by far the oldest debt and the only major instrument missing.

**2. A7 — wire `frames.py` into the ingest.** Still applied by hand.

**3. D9 — autonym coverage (9.3%).** CLDR is the next source; Unicode licence, permitted.

**4. D3 — audio**, with a per-file licence gate, and **D5 — typological prose** from Grambank.

**5. C4 / C8** — the literature check and settlement time-depth. Neither started.

**Do not repeat these:**
- A source is not what its name says; assert the **physical range** of the quantity.
- Ask what a count is counting. "Diversity" counted datasets, not languages.
- Any index packed into a byte needs defined overflow (175 families vanished for two rounds).
- A negative proportion is the arithmetic telling you two numbers are not comparable.
- Do not trust a phylogeny's scaling field: four are in substitutions, one gives 613,594 years.

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

- Last live deploy: **stamp 1785701549**, verified live (tree, texts and tiles confirmed)
- Committed and deployed: all of it. Pages serves `main:/docs`
- Uncommitted: nothing (check `git status`)
- App: **unchanged** — still the scaffold's hybrid shell at `web/`, port 8146, verified rendering.
  `web/fields/` is empty; `build/` has only a README. **The field engine does not exist yet.** That
  is correct: round 1 was a research round and the research folder does not change the app.
- Research: **four self-testing modules, all passing** — `frames.py`, `licences.py`, `encoding.py`,
  `diversity.py`, plus `audit_all.py` which runs all four (4/4 PASS). One white paper (`WP-01`), two
  authored figures in `Research/figures/authored/`, four changes staged in `STAGED-CHANGES.md`.
- Source data in `data/` (gitignored, ~750 MB): Glottolog 5.3 CLDF, the polygon collection's licence
  classification, ETOPO1 ice-surface 1-arc-minute.

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
