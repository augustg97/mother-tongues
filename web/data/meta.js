/* meta.js — the model's spine: extent, step, layer table, live statistics.
 *
 * Data ships as .js literals rather than fetched .json so the app runs from file://.
 * If the project does not need offline operation, switch to .json + fetch.
 *
 * Schema is documented here and in Modeling Studio/templates/DATA-SCHEMA.md.
 */
window.DATA = window.DATA || {};

DATA.meta = {

  // ---- extent, from SCOPE.md §2 -------------------------------------------
  t0:   1750,          // start of the model
  t1:   2026,          // end
  step: 1,             // one keyboard/button step, in domain units
  unit: 'yr',

  speeds: [1, 2, 4, 10, 25, 60],        // playback, units per second

  // How a time value is written for a reader. Deep-time models want "300 Ma";
  // historical ones want "1848"; a model of a day wants "14:05".
  fmt: t => String(Math.round(t)),

  // ---- the layer table, from SCOPE.md §3 ----------------------------------
  // Keep this in the same order as SCOPE.md, and keep the ids stable — they are
  // referenced by every entity's `layer` field and by the URL.
  layers: [
    {id: 'places',  label: 'Places',            on: true},
    {id: 'events',  label: 'Events',            on: true},
    {id: 'routes',  label: 'Routes & networks', on: false},
  ],

  // ---- the live readout ---------------------------------------------------
  // Either a `series` ([[t, v], …], interpolated) or an `at(t)` function.
  stats: [
    // {label: 'Population', series: [[1750, 1_170_000], [1800, 5_308_483]],
    //  fmt: v => v == null ? '—' : Math.round(v).toLocaleString()},
  ],

  // ---- the generic fallback tier -----------------------------------------
  // Returns what is typical of this period WORLDWIDE. The card renders it under a
  // heading that says so — see extraSections() in js/app.js. A generic list
  // presented as local is a lie; the heading is what makes it useful instead.
  genericAt: /* t => [...] */ null,
};
