/* eras.js — narrative chapters for the timeline, and dated event markers.
 *
 * The timeline is the table of contents: era bands and event dots live ON the
 * scrubber, not in a separate list.
 *
 * eras   must be CONTIGUOUS (each `to` is the next `from`) and cover [t0, t1].
 *        An audit should check that, because a gap is invisible until someone
 *        scrubs into it and the chapter panel goes blank.
 * events are moments — anything shorter than `step` cannot be DRAWN on the map
 *        and needs a card or a context panel instead of a marker that would lie
 *        about its duration.
 */
window.DATA = window.DATA || {};

DATA.eras = [
  {
    from: 1750, to: 1763, name: 'First Chapter',
    title: 'A sentence that states what this chapter is about',
    text: 'Two to five sentences. Plain, specific, dated. The chapter text is the ' +
          'model\'s argument in prose; the map is the same argument in pictures.'
  },
  // {from: 1763, to: 1776, name: '…', title: '…', text: '…'},
];

DATA.events = [
  // {t: 1776, name: 'Independence declared',
  //  text: '…', sources: ['National Archives']},
];
