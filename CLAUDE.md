# Mother Tongues — instructions for Claude sessions

Every human language we know of, on the ground it is spoken on

**Read `README.md` first** — §1 (what this is trying to be), §2 (the working rules), §7 (traps),
§9 (known limits). Then `SCOPE.md` for the contract and `HANDOFF.md` for the live state.

The general protocol lives in `/Users/augustgweon/Modeling Studio`. Its skills apply here:
`/model-research`, `/model-build`, `/model-verify`, `/model-ship`.

---

## Standing rules — these override default behaviour

0. **The surface is the argument, and it must be a legible surface of the real world.** Three
   requirements, all of them: (a) the substrate is **composed per pixel** — relief, texture, light,
   material, weather — never dots and symbols on flat ground; (b) it is a rendered surface **of the
   actual place** the subject occupies, never of an abstract or semantic space, which may only ever
   be a secondary view; (c) it is **legible** — a viewer can name concrete things off it without a
   legend. Every round, screenshot the full frame and answer in writing: *does this read as a
   rendered world rather than a chart*, and *name three facts a viewer can read off it*. Rule 0
   because it is the one the work is judged on. See `Modeling Studio/references/WORKING-RULES.md`
   §13 and `ARCHITECTURE-PATTERNS.md` §0, and SCOPE §3 for this project's stated bar.

1. **Always visually verify.** An update is not done when the data contains the value. It is done
   when it has been **rendered and looked at**. Render the frame, `Read` the image, confirm the
   change is on screen and is correct. "The field has the value" is not confirmation.

2. **Fix the system, not the instance.** When correcting an error, make the change at the level
   that fixes the whole **class** across the whole timeline. A patched instance leaves the same
   bug at every other time and place.

3. **Prefer structural, model-based changes over cosmetic ones.** Ask what the real-world object
   or process is, and model that. Let the appearance fall out of it. Parameter tuning produces
   "modest improvements" and never closes a gap.

4. **Measure before tuning.** Histogram it, spectrum it, or A/B each term behind a debug flag
   before changing a constant.

5. **Track every request each round and address all of them.** If something genuinely cannot be
   done, say so explicitly and say why — do not omit it.

6. **Always deploy, and verify the live artefact.** Every round ends with a build, a commit, a
   push, and a check of the live data-version stamp.

7. **Never ship on an average.** Score every item individually, before and after, and classify
   every regression.

8. **When an audit disagrees with the app, check the audit first.**

9. **Say what is contested**, in the data, as a field.

10. **"Unknown" is a legitimate return**, and where a fallback is unavoidable the UI labels it as
    a fallback.

11. **Autonym first, always.** Every language is named by what its speakers call it, in its own
    script, with the English exonym second and any historical exonym marked as historical. Many
    exonyms are colonial or slurs. Display order is enforced **in code**, not left to data entry.
    This is the ethics of the project and it is not a formatting preference.

12. **No language is mapped against its community's stated wish**, and only openly licensed,
    community-released material is ingested. The audio gap (~6–8% of languages) exists because
    archives withhold recordings **as a condition of consent** — that is the system working. Ship
    what is clean, state the coverage, name the archives, **link out rather than mirror**.

13. **Never one number for how many languages exist.** State the splitting authority, show the
    alternative counts. The count is a political artefact, not a measurement.

14. **Every speaker count is a triple — (value, year, source).** A bare number is not a datum
    here; sources copy each other's decades-old figures forward.

15. **The "before contact" snapshot carries no year.** It is a per-region state; contact ranges from
    the 1490s to the 20th century and never happened in some places. Per-region contact dates go on
    cards. Printing one year on that snapshot would be the frame error of the project.

16. **ShareAlike is permitted (data and images); NonCommercial and NoDerivatives are not**
    (SCOPE §12 D3). Consequence: **our emitted data inherits SA.** Every SA source gets a row in the
    attribution ledger in `Research/SOURCE-SURVEY.md` §1 *before* it is ingested.

---

## The canonical frame

**Glottocode** is the identity key — ISO 639-3 is an alias only, because it has no "ancient" type
(Latin, Sumerian and Akkadian are all coded *historical*) and its coverage differs by hundreds of
entries. **WGS84** coordinates; GHS-POP arrives in **Mollweide** and must be reprojected once at
ingest with the residual recorded — the one live coordinate-frame trap here. **Names**:
autonym-first with an alias table. **Counts**: (value, year, source). **Time**: two snapshots, and
the earlier one is a state, not a year.

Every source is converted into it. The conversions are in `Research/modeling/frames.py`, with selftests. **Never combine
two sources without checking they are in the same frame** — this is the most expensive class of
bug in this kind of project.

## The evidence boundary

Three, each with designed UI behaviour (SCOPE §5): the **linguistic horizon** at ~8–10 ka, past
which the model draws *nothing* while terrain keeps rendering; the **documentation boundary**, drawn
as a field so a thinly surveyed region renders as thinly surveyed rather than as linguistically
uniform; and the **vintage boundary** on speaker counts, carried as the year of each estimate.

Measured coverage limits, from the survey: real polygons for **62.5%** of living languages ·
**nine** pre-Common-Era languages have an area · **38.6%** of extinct languages do · **~12%** can be
animated from a dated tree · population floor **1975** · audio **6–8%**.

Past it, the model is inference and the UI says so.

---

## Commands

```bash
# run the app locally (preview config in ~/.claude/launch.json, port 8146)
python3 -m http.server 8146 --directory "/Users/augustgweon/Mother Tongues/web"

# the research loop
cd Research/modeling && python3 frames.py       # selftests — must pass before any join
python3 audit_all.py                            # the gate

# deploy (only route, once build_site.py exists)
python3 build/build_site.py && git add -A && git commit && git push
# then verify the live data-version stamp
```

## Traps that have each cost real time here

- **The scaffold's own layout bug, already fixed here and upstream:** the app shell belongs in
  `web/` (which `launch.json` serves), and `.gitignore` must anchor `/data/` — an unanchored
  `data/` also matches `web/data/` and silently ships a site that renders nothing.
- **The scaffold shell is dots on flat ground.** That is a placeholder, and replacing it with a
  rendered surface is the whole job. Do not add a feature layer to it (rule 0).
- **Glottolog's three "how many languages" numbers are all correct** — ~27,177 languoids, 8,618
  language-level, 7,674 spoken L1 — and get conflated constantly. Label which one is in use.
- **3 of Glottography's 34 repos are CC-BY-NC.** The platform paper says the whole set is CC-BY.
  It is wrong. Gate per repository licence file, by machine.
- **PanLex is CC-BY-NC-SA, not CC0** — a common and costly assumption.
- **One Phlorest tree's branch-length unit yields 692,970 years.** Do not trust the unit field;
  sanity-check every tree against its source.
- **The parallel-prose corpus has no licence** and ships under a recorded decision (SCOPE §12 D2)
  behind a feature flag. Keep it removable in one commit.

Plus the standing ones: a process backgrounded with `&` inside a tool call dies when that call
ends; a waiter on a `pgrep` pattern can match itself — wait on a **PID**; a static host can serve
stale JSON after a successful push, so stamp the data version before copying the app file and
verify the live value.
