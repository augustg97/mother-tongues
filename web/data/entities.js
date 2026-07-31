/* entities.js — the addressable things. One file per kind in a real project
 * (cities.js, treaties.js, features.js …); this shell keeps one file for clarity.
 *
 * Every entity carries the universal fields. See Modeling Studio/templates/DATA-SCHEMA.md.
 *
 *   id          stable slug, referenced by other records — NEVER recycled
 *   name        display name
 *   kind        drives the card eyebrow
 *   layer       which layer toggle governs it — must be an id in meta.layers
 *   lon, lat    position in the CANONICAL frame (SCOPE.md §5)
 *   from, to    the drawing window; must sit inside the entity's real lifetime
 *   confidence  'good' | 'moderate' | 'contested' — a FIELD, not a footnote
 *   facts       2–4 [label, value] rows
 *   eras        time-aware prose: must tile the entity's life, no gaps or overlaps
 *   sources     named. A card without a source is an assertion.
 *   curated     optional: a hand-written list the model must never speak over.
 *               Pair with `exception: true` where the entry is atypical BY DESIGN.
 */
window.DATA = window.DATA || {};

DATA.entities = [
  {
    id: 'example', name: 'Example Place', kind: 'City', layer: 'places',
    lon: -71.06, lat: 42.36,
    from: 1750, to: null,
    confidence: 'good',
    facts: [
      ['Founded', '1630'],
      ['Role', 'What it was for, in six words'],
    ],
    eras: [
      {from: 1750, to: 1830, text: 'What this place was during this span, in plain ' +
        'sentences with real dates and numbers.'},
      {from: 1830, to: 2026, text: 'What it became. The card in 1849 is not the card ' +
        'in 1950 — that is the point of this array.'},
    ],
    sources: ['Author (year), Title'],
  },
];
