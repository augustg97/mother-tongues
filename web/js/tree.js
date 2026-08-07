/* Mother Tongues — the genealogy. A tree, on paper.
 *
 * The map answers "where"; this answers "where from". WORKING-RULES §13b allows an abstract
 * space only as a SECONDARY view, so this is that: same glottocodes, same families, and every
 * leaf goes back to the ground it is spoken on.
 *
 * WHY IT IS DRAWN AS A TREE AND NOT A LIST. The first version was an indented index. An index
 * tells you a language has a parent; it does not show you that Indo-Iranian carries a third of
 * Indo-European while Tokharian carries two dead languages, or that a family is mostly extinct.
 * Branch THICKNESS here is the number of living descendants and branch LENGTH is depth of
 * descent, so the shape of a family is visible before a single label is read.
 *
 * WHAT IS AND IS NOT TIME. Phlorest gives a dated ROOT for 19 families — one number for the
 * whole family, not dates for the internal splits. So depth is descent, not years, and the
 * root age is stated in words beside the family rather than drawn as an axis that does not
 * exist (rule 10).
 */
'use strict';

(function () {
  const $ = s => document.querySelector(s);
  const AESN = ['', 'not endangered', 'threatened', 'shifting', 'moribund',
                'nearly extinct', 'extinct'];
  const SERIF = '"Iowan Old Style","Palatino Linotype",Palatino,"Hoefler Text",Georgia,' +
                '"Times New Roman",serif';
  const SANS = '-apple-system,BlinkMacSystemFont,"Segoe UI",Inter,system-ui,sans-serif';

  const T = {
    index: null, family: null, tree: null, rows: [], famIdx: {},
    scale: 1, ox: 0, oy: 0, hover: null, sel: null, showDialects: false, q: '',
    collapsed: new Set(),
    laid: null, W: 0, H: 0
  };
  window.TREE = T;

  // Delegated once, not per render: the exhibit's innerHTML is replaced on every card, and a
  // listener attached inside that HTML would be re-bound every time and leak.
  document.addEventListener('click', e => {
    const b = e.target.closest && e.target.closest('.hplay');
    if (!b) return;
    const el = document.getElementById('exau');
    if (!el) return;
    document.querySelectorAll('.hplay.on').forEach(x => x.classList.remove('on'));
    b.classList.add('on');
    el.src = b.dataset.url;
    el.play().catch(() => {
      // Commons can refuse or the codec can be unsupported; say so rather than doing nothing.
      b.classList.remove('on');
      b.classList.add('hfail');
      b.title = 'This recording would not play. It streams from Wikimedia Commons; open it '
              + 'there if you need it.';
    });
  });
  T.showByCode = (gc) => showByCode(gc);

  // The map's golden-ratio hue, darkened for paper: the same family is recognisably the same
  // colour in both views, but ink on paper needs weight where light on black needed glow.
  function famColour(idx, light) {
    const i = Math.floor(idx || 0);
    const h = (i * 0.6180339887) % 1;
    const s = 0.55 + 0.25 * ((i * 0.311) % 1);
    const v = 0.80 + 0.20 * ((i * 0.727) % 1);
    const f = n => {
      const k = (n + h * 6) % 6;
      return v - v * s * Math.max(0, Math.min(Math.min(k, 4 - k), 1));
    };
    const m = light ? 0.92 : 0.52;
    return `rgb(${Math.round(255 * f(5) * m)},${Math.round(255 * f(3) * m)},${Math.round(255 * f(1) * m)})`;
  }
  const colOf = () => famColour(T.famIdx[T.family]);
  // The index view paints 7,672 cells in family hues and must use THIS function, not a copy of
  // it: two implementations of the same colour drift the moment one of them is touched.
  T.famColour = famColour;

  const _fontOK = new Map();
  function canRender(str) {
    if (!str) return false;
    const k = str.slice(0, 12);
    if (_fontOK.has(k)) return _fontOK.get(k);
    let ok = true;
    try { if (document.fonts && document.fonts.check) ok = document.fonts.check('14px ' + SERIF, k); }
    catch (e) { ok = true; }
    _fontOK.set(k, ok);
    return ok;
  }

  // Artefact vignettes, drawn on the tree itself. A branch that ends in a burnt codex or a
  // clay tablet should look like it does, not merely link to it.
  // gallery.json holds an ARRAY of objects per language. Every read goes through galOf so
  // that a language with four artefacts cannot show one in the card and none on the tree.
  function galOf(gc) {
    const g = window.APP.gallery && window.APP.gallery[gc];
    if (!g) return [];
    return Array.isArray(g) ? g : [g];       // tolerate the old single-object shape
  }

  const _thumbs = new Map();
  function thumb(gc) {
    const g = galOf(gc)[0];
    if (!g) return null;
    if (_thumbs.has(gc)) return _thumbs.get(gc);
    const im = new Image();
    im.onload = () => draw();
    im.src = window.V('img/gallery/' + g.file);
    _thumbs.set(gc, im);
    return im;
  }

  async function loadIndex() {
    if (T.index) return T.index;
    T.index = await fetch(window.V('data/tree/index.json')).then(r => r.json());
    const L = window.APP.langs;
    if (L) for (const r of L.rows) T.famIdx[r[11]] = r[4];
    return T.index;
  }

  /* ---- layout: leaves get equal vertical space, depth gives horizontal position ---- */
  function layout() {
    const q = T.q.toLowerCase();
    const nodes = [];
    let leafN = 0, maxDepth = 0;

    function keep(n) {
      if (!T.showDialects && n.lv === 2) return false;
      if (!q) return true;
      if ((n.n || '').toLowerCase().includes(q)) return true;
      if (n.au && n.au[0].toLowerCase().includes(q)) return true;
      if ((n.i || '').includes(q)) return true;
      return (n.c || []).some(keep);
    }

    function walk(n, depth) {
      if (!keep(n)) return null;
      maxDepth = Math.max(maxDepth, depth);
      // A collapsed node keeps its subtree in the DATA but not in the layout: it becomes a
      // tip you can open. Searching overrides collapse, otherwise a search would only find
      // what you had already opened — the bug this view had once before.
      const shut = !q && T.collapsed.has(n.g);
      const kids = shut ? [] : (n.c || []).map(c => walk(c, depth + 1)).filter(Boolean);
      const rec = { n, depth, kids, y: 0, leaves: 0, living: 0, shut, hasKids: !!(n.c || []).length };
      if (!kids.length) {
        rec.y = leafN++;
        rec.leaves = 1;
        rec.living = (n.a || 0) >= 6 ? 0 : 1;
        if (shut) {
          // a shut branch still shows its weight, so the tree does not look emptier closed
          let L2 = 0, LV = 0;
          (function cnt(m) {
            if (!(m.c || []).length) { L2++; if ((m.a || 0) < 6) LV++; }
            (m.c || []).forEach(cnt);
          })(n);
          rec.leaves = Math.max(1, L2); rec.living = LV;
        }
      } else {
        rec.leaves = kids.reduce((a, k) => a + k.leaves, 0);
        rec.living = kids.reduce((a, k) => a + k.living, 0);
        rec.y = (kids[0].y + kids[kids.length - 1].y) / 2;
      }
      nodes.push(rec);
      return rec;
    }
    const root = walk(T.tree, 0);
    T.laid = { root, nodes, leafN: Math.max(1, leafN), maxDepth: Math.max(1, maxDepth) };
  }

  function fit() {
    const cv = $('#treecv');
    if (!T.laid || !cv) return;
    T.scale = 1;
    T.ox = 0;
    T.oy = 0;
  }

  /* ---- draw ----
   * `draw()` is a DISPATCHER, not the dendrogram. Everything that repaints — a gallery
   * thumbnail finishing its load, a hover, an exhibit opening — calls draw(), and when those
   * called the dendrogram directly the STORY view was painted over a fraction of a second
   * after it appeared. One entry point, one decision about which view is showing.
   */
  function draw() { return T.story ? drawStory() : drawTree(); }

  function drawTree() {
    const cv = $('#treecv');
    if (!cv || !T.laid) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = cv.clientWidth, h = cv.clientHeight;
    if (!w || !h) return;
    // ⚠ Check BOTH dimensions. Only testing width meant that when the canvas got SHORTER
    // (the exhibit column appearing re-flows the grid) the backing store kept its old height
    // and clearRect(0,0,w,h) only wiped the new, smaller area — so the previous family stayed
    // painted in the strip below the fold. Two trees at once, in two different colours.
    const bw = Math.round(w * dpr), bh = Math.round(h * dpr);
    if (cv.width !== bw || cv.height !== bh) { cv.width = bw; cv.height = bh; }
    T.W = w; T.H = h;
    const g = cv.getContext('2d');
    g.setTransform(dpr, 0, 0, dpr, 0, 0);
    g.clearRect(0, 0, w, h);

    const L = T.laid;
    const padL = 26, padR = 300;
    const colW = Math.max(48, (w - padL - padR) / (L.maxDepth + 1));
    const rowH = Math.max(3.2, 15 * T.scale);
    const totalH = L.leafN * rowH;

    T.oy = Math.max(Math.min(T.oy, 0), Math.min(0, h - totalH - 60));
    const X = d => padL + d * colW + T.ox;
    const Y = i => 30 + i * rowH + T.oy;

    const col = colOf();
    // Type size follows the row, so a family that only just fits still reads instead of
    // flipping to an unlabelled diagram at an arbitrary threshold.
    const labelled = rowH >= 9.5;
    const fs = Math.max(9.5, Math.min(14, rowH * 1.15));

    // ---- the depth axis ------------------------------------------------------------
    // "Distance from left is depth of descent, not time" is printed above the tree in words,
    // and until now it was only words: the horizontal axis carried a real quantity with no
    // scale on it, which is the one thing a chart may never do. Faint rules at each column,
    // numbered, so the claim is checkable off the surface.
    g.save();
    g.font = '9.5px ' + SANS;
    g.textBaseline = 'alphabetic';
    for (let d = 0; d <= L.maxDepth; d++) {
      const gx = X(d);
      if (gx < padL - 40 || gx > w - padR + 40) continue;
      g.strokeStyle = d === 0 ? 'rgba(120,112,102,.18)' : 'rgba(120,112,102,.085)';
      g.lineWidth = 1;
      g.beginPath(); g.moveTo(gx + 0.5, 22); g.lineTo(gx + 0.5, h); g.stroke();
      if (colW >= 34) {
        g.fillStyle = 'rgba(140,132,122,.75)';
        g.textAlign = 'center';
        g.fillText(String(d), gx, 16);
      }
    }
    g.textAlign = 'left';
    g.restore();
    g.textBaseline = 'middle';

    // branches, thickest first so thin twigs draw over trunks cleanly
    const sorted = L.nodes.slice().sort((a, b) => b.leaves - a.leaves);
    for (const r of sorted) {
      if (!r.kids.length) continue;
      const x0 = X(r.depth), y0 = Y(r.y);
      for (const k of r.kids) {
        const x1 = X(k.depth), y1 = Y(k.y);
        if (Math.max(y0, y1) < -40 || Math.min(y0, y1) > h + 40) continue;
        // thickness carries the number of LIVING descendants: a family that is mostly
        // extinct visibly thins towards its tips instead of looking as healthy as any other
        // ⚠ THE SLAB. sqrt() at 5.2px put Volta-Congo's 3,093 living languages into a band
        // wide enough to swallow its own children, and at alpha .55 every overlapping curve
        // compounded until the trunk read as one solid mass. A quarter-power ramp keeps the
        // thin twigs visible while capping the trunk at a width you can still see through.
        const tw = 0.7 + 3.6 * Math.pow(k.living / L.leafN, 0.38);
        g.lineWidth = Math.max(0.55, tw);
        g.strokeStyle = k.living === 0 ? 'rgba(120,112,102,.34)' : col;
        g.globalAlpha = k.living === 0 ? 1 : 0.44;
        g.beginPath();
        g.moveTo(x0, y0);
        const mx = x0 + (x1 - x0) * 0.55;
        g.bezierCurveTo(mx, y0, x0 + (x1 - x0) * 0.45, y1, x1, y1);
        g.stroke();
      }
    }
    g.globalAlpha = 1;

    // Labels are drawn in y order with a collision guard: where two tips sit closer than a
    // line of type, the second label is dropped rather than overprinted. A crowded branch
    // should look crowded, not look like a smudge.
    g.textBaseline = 'middle';
    const byY = L.nodes.slice().sort((a, b) => a.y - b.y);
    let lastLeafY = -1e9, lastNodeY = -1e9;
    // ⚠ ONE SET OF BOXES, NOT TWO COUNTERS. lastLeafY and lastNodeY were tracked separately, so
    // a tip label and an internal label could land on the same line and print through each
    // other — "North-Central Atlantic" over "Jaad", "Volta-Congo" over "Kwa Volta-Congo". They
    // are different KINDS of label but they occupy the same canvas. Boxes are compared on both
    // axes because an internal label sits at a different x from the tips beside it.
    const placed = [], forks = [];
    const fits = (y0, y1, x0, x1) => {
      for (const b of placed) {
        if (y0 < b.y1 && y1 > b.y0 && x0 < b.x1 && x1 > b.x0) return false;
      }
      return true;
    };
    for (const r of byY) {
      const x = X(r.depth), y = Y(r.y);
      if (y < -20 || y > h + 20) continue;
      const n = r.n, a = n.a || 0, leaf = !r.kids.length;

      if (leaf) {
        g.beginPath();
        g.arc(x, y, Math.min(4.2, 2.0 + rowH * 0.12), 0, 6.2832);
        if (a >= 6) { g.strokeStyle = 'rgba(120,112,102,.75)'; g.lineWidth = 1.1; g.stroke(); }
        else { g.fillStyle = a >= 3 ? '#b4622f' : col; g.fill(); }
      } else if (rowH >= 8) {
        g.beginPath(); g.arc(x, y, 2.2, 0, 6.2832);
        g.fillStyle = 'rgba(90,84,76,.5)'; g.fill();
      }
      // A shut branch is drawn as a bud with its size on it: the affordance is the shape,
      // not an icon you have to learn.
      r._bud = 0;
      if (r.shut && labelled) {
        const cnt = String(r.leaves);
        g.font = '600 ' + Math.max(8, Math.min(10, (4 + Math.sqrt(r.leaves) * 0.5) * 1.15)).toFixed(1) + 'px ' + SANS;
        // ⚠ THE BUD MUST FIT ITS OWN NUMBER. The radius came only from sqrt(leaves), capped at
        // 9, so a three-digit count — Benue-Congo's 231 — was drawn centred on an 18px bud and
        // spilled out both sides into the name beside it. Size the bud to the text it carries.
        const rad = Math.max(Math.min(9, 4 + Math.sqrt(r.leaves) * 0.5), g.measureText(cnt).width / 2 + 3);
        g.beginPath(); g.arc(x, y, rad, 0, 6.2832);
        g.fillStyle = col; g.globalAlpha = 0.22; g.fill(); g.globalAlpha = 1;
        g.strokeStyle = col; g.lineWidth = 1.3; g.stroke();
        g.fillStyle = col; g.textAlign = 'center';
        g.fillText(cnt, x, y + 0.5);
        g.textAlign = 'left';
        r._bud = rad;
      }

      if (T.sel === n) {
        g.beginPath(); g.arc(x, y, 8, 0, 6.2832);
        g.strokeStyle = '#b4622f'; g.lineWidth = 1.4; g.stroke();
      }

      // the vignette sits at the tip, before the name
      if (labelled && leaf && rowH >= 15) {
        const im = thumb(n.g);
        if (im && im.complete && im.naturalWidth) {
          const hgt = Math.min(46, rowH * 2.6), wid = Math.round(hgt * im.naturalWidth / im.naturalHeight);
          g.save();
          g.beginPath(); g.rect(x + 7, y - hgt / 2, Math.min(wid, 64), hgt); g.clip();
          g.drawImage(im, x + 7, y - hgt / 2, wid, hgt);
          g.restore();
          g.strokeStyle = 'rgba(60,52,42,.35)'; g.lineWidth = 1;
          g.strokeRect(x + 7.5, y - hgt / 2 + 0.5, Math.min(wid, 64) - 1, hgt - 1);
          r._vig = Math.min(wid, 64) + 11;
        } else r._vig = 0;
      } else r._vig = 0;

      if (!labelled) continue;
      const need = fs * 0.95;
      if (leaf) { if (y - lastLeafY < need) continue; lastLeafY = y; }
      else { if (y - lastNodeY < need) continue; lastNodeY = y; }
      let tx = x + Math.max(8, (r._bud || 0) + 4) + (r._vig || 0);
      if (leaf) {
        const au = n.au && canRender(n.au[0]) ? n.au[0] : null;
        g.font = fs.toFixed(1) + 'px ' + SERIF;
        g.fillStyle = a >= 6 ? 'rgba(96,90,82,.85)' : '#20242a';
        const main = au || n.n;
        const mw = g.measureText(main).width;
        if (!fits(y - fs * 0.55, y + fs * 0.55, tx, tx + mw)) continue;
        placed.push({ y0: y - fs * 0.55, y1: y + fs * 0.55,
                      x0: x - Math.max(7, (r._bud || 0) + 1), x1: tx + mw });
        g.fillText(main, tx, y);
        tx += g.measureText(main).width + 8;
        if (au) {
          g.font = Math.max(9, fs * 0.82).toFixed(1) + 'px ' + SANS;
          g.fillStyle = 'rgba(96,90,82,.72)';
          g.fillText(n.n, tx, y);
          tx += g.measureText(n.n).width + 8;
        }
        const bits = [];
        if (a >= 6) bits.push('extinct');
        else if (a >= 3) bits.push(AESN[a]);
        if (n.y) bits.push('attested ' + (n.y < 0 ? (-n.y) + ' BCE' : n.y));
        const tX = window.APP.texts && window.APP.texts.by_glottocode[n.g];
        if (tX && tX.s) bits.push(tX.s);
        if (bits.length && fs >= 11) {
          g.font = Math.max(9, fs * 0.76).toFixed(1) + 'px ' + SANS;
          g.fillStyle = 'rgba(120,112,102,.8)';
          g.fillText(bits.join(' · '), tx, y);
        }
      } else {
        // Deferred. A tip label is a language; an internal label is scaffolding naming a fork.
        // Drawing them in one y-ordered pass let a fork name win a line from a language purely
        // by sitting a few pixels higher — "Volta-Congo 3093" taking the line from "Kwa
        // Volta-Congo". Second pass, so every tip is placed before any fork asks for room.
        forks.push({ r, n, x, y, tx, fs });
      }
    }

    for (const f of forks) {
      const { r, n, tx, fs } = f;
      const ny = f.y - Math.min(9, fs * 0.72);
      g.font = '600 ' + Math.max(9, fs * 0.82).toFixed(1) + 'px ' + SANS;
      // ⚠ MEASURE BEFORE CHANGING THE FONT. This measured the name AFTER switching to the
      // smaller count face, so the width came back short and the count was drawn on top of
      // the name's own tail: "Atlantic-Congo" with 8261 printed through it, "Volta-Congo"
      // through 2093, on every internal node in the atlas.
      const nameW = g.measureText(n.n).width;
      const cntW = 7 + Math.max(9, fs * 0.72) * 0.62 * String(r.leaves).length;
      const y0 = ny - fs * 0.5, y1 = ny + fs * 0.5;
      // Four placements, in order of preference. A fork label wants to sit to the right of its
      // node; when the next column's buds are in the way it can sit to the LEFT instead, in
      // the empty span back towards its parent. Only if neither side has room for the number
      // is the number dropped — a fork with no count still says where you are, a count with
      // no name says nothing.
      const cands = [];
      for (const cnt of [true, false]) {
        const wide = nameW + (cnt ? cntW : 0);
        cands.push({ x0: tx - 4, cnt });                       // right of the fork
        cands.push({ x0: f.x - 7 - wide, cnt, alt: true });    // left of it, back up the branch
      }
      cands.sort((a, b) => (b.cnt - a.cnt) || (a.alt ? 1 : -1));
      let put = null;
      for (const c of cands) {
        const wide = nameW + (c.cnt ? cntW : 0);
        if (c.x0 < 2) continue;
        if (fits(y0, y1, c.x0, c.x0 + wide)) { put = { ...c, wide }; break; }
      }
      if (!put) continue;
      placed.push({ y0, y1, x0: put.x0, x1: put.x0 + put.wide });
      g.fillStyle = 'rgba(58,54,50,.9)';
      g.fillText(n.n, put.x0, ny);
      if (put.cnt) {
        g.font = Math.max(8.5, fs * 0.72).toFixed(1) + 'px ' + SANS;
        g.fillStyle = 'rgba(130,122,112,.8)';
        g.fillText(String(r.leaves), put.x0 + nameW + 7, ny);
      }
    }

    // A name under the cursor, always — at fit zoom the tree is a shape with no labels at
    // all, and a shape you cannot interrogate is decoration.
    if (T.hover && T.hoverXY) {
      const n = T.hover;
      const nm = (n.au && canRender(n.au[0])) ? n.au[0] : n.n;
      const sub = (n.au && canRender(n.au[0])) ? n.n : '';
      g.font = '14px ' + SERIF;
      const w1 = g.measureText(nm).width;
      g.font = '11px ' + SANS;
      const w2 = sub ? g.measureText(sub).width + 8 : 0;
      const bw2 = w1 + w2 + 20, bh2 = 26;
      let bx = Math.min(T.hoverXY[0] + 14, w - bw2 - 6), by = T.hoverXY[1] - bh2 - 8;
      if (by < 2) by = T.hoverXY[1] + 14;
      g.fillStyle = 'rgba(32,36,42,.93)';
      g.fillRect(bx, by, bw2, bh2);
      g.fillStyle = '#f7f3ea';
      g.font = '14px ' + SERIF;
      g.fillText(nm, bx + 10, by + bh2 / 2);
      if (sub) {
        g.font = '11px ' + SANS;
        g.fillStyle = 'rgba(247,243,234,.62)';
        g.fillText(sub, bx + 10 + w1 + 8, by + bh2 / 2 + 1);
      }
    }

    if (!labelled) {
      g.font = '11px ' + SANS;
      g.fillStyle = 'rgba(120,112,102,.9)';
      g.fillText(L.leafN.toLocaleString() + ' branches — scroll to zoom in for names',
                 padL, h - 12);
    }
  }

  /* ---- the exhibit: one language, given room ---- */
  /** Everything under a node: leaf count, deaths, the oldest attested member, extent. */
  /** Walk the DATA, not the layout: a collapsed branch must still report its real size. */
  function summarise(rec) {
    // ALWAYS from the data. The guard used to be `if (rec.shut)`, which rebuilt only when the
    // TOP node was collapsed — but every COLLAPSED DESCENDANT still contributed exactly 1,
    // because a shut node has no kids in the layout. Sinitic has four collapsed children and so
    // reported "4 languages" while its cluster block, computed offline over the real tree, found
    // 18 called Chinese: the card read "18 of the 4". Every branch card with a collapsed child
    // was under-counting, which is most of them.
    rec = fullRec(rec.n);
    let lang = 0, ext = 0, end = 0, oldest = null, oldestN = null, named = [];
    let lo = 999, la = 999, LO = -999, LA = -999;
    (function w(r) {
      const n = r.n;
      // ⚠ A LANGUAGE STOPS THE WALK EVEN WHEN IT HAS DIALECT CHILDREN. Testing `!r.kids.length`
      // counts leaves, and a language with dialects under it is not a leaf — so Sinitic reported
      // "4 languages" while the cluster block, which walks by level, found 18 called Chinese and
      // printed "18 of the 4". The Python cluster walk was fixed for exactly this in
      // build_families.py; the JS summariser still had it, and it under-counted every branch
      // card in the atlas.
      if (n.lv === 1 || !r.kids.length) {
        lang++;
        if ((n.a || 0) >= 6) ext++; else if ((n.a || 0) >= 3) end++;
        if (n.y && (oldest === null || n.y < oldest)) { oldest = n.y; oldestN = n; }
        if (n.p) {
          lo = Math.min(lo, n.p[0]); LO = Math.max(LO, n.p[0]);
          la = Math.min(la, n.p[1]); LA = Math.max(LA, n.p[1]);
        }
        if (named.length < 8 && (n.au || (window.APP.notable &&
            window.APP.notable.by_glottocode[n.g]))) named.push(n);
        return;                       // and do not descend into its dialects
      }
      r.kids.forEach(w);
    })(rec);
    const box = (lo < 900) ? [(lo + LO) / 2, (la + LA) / 2,
                              Math.max(6, Math.min(180, (LO - lo) * 1.3))] : null;
    return { lang, ext, end, oldest, oldestN, named, box };
  }

  function fullRec(n) {
    const kids = (n.c || []).map(fullRec);
    return { n, kids, leaves: kids.length ? kids.reduce((a, k) => a + k.leaves, 0) : 1 };
  }

  // ⚠ #exhibit IS THE SCROLL CONTAINER, and setting innerHTML does not move it. Open a long
  // card, scroll halfway down it, then open another long card and you land halfway down THAT
  // one — reading its middle with no idea you have missed the top. Every write to the card goes
  // through here so the next one cannot forget.
  function setExhibit(html) {
    const ex = $('#exhibit');
    ex.innerHTML = html;
    ex.scrollTop = 0;
    buildSpine(ex);
    return ex;
  }

  // THE CARD'S SPINE. English's card is 6,055 px in a 642 px column — nine and a half screens,
  // eight sections, and nothing on screen says they are there. A reader scrolls blind past
  // Dated, Heard, How it works, Its letters, Written today, Words as spoken, In its own words
  // and Objects, or more likely does not scroll at all.
  //
  // Built here rather than in each renderer, from the <h3>s that are already in the markup, so
  // a section added anywhere gets a spine entry for free and none can be forgotten. It also
  // makes richness legible before a word is read: a card with seven marks looks deep.
  //
  // Short cards do not get one — a spine over two paragraphs is furniture, not navigation.
  function buildSpine(ex) {
    const hs = [...ex.querySelectorAll('h3')];
    if (hs.length < 3 || ex.scrollHeight < ex.clientHeight * 1.8) return;
    hs.forEach((h, i) => { h.id = 'sec' + i; });
    const nav = document.createElement('nav');
    nav.className = 'spine';
    nav.innerHTML = hs.map((h, i) =>
      '<a href="#" data-s="' + i + '">' + esc(h.textContent) + '</a>').join('');
    ex.insertBefore(nav, ex.firstChild);

    nav.addEventListener('click', e => {
      const a = e.target.closest('a'); if (!a) return;
      e.preventDefault();
      const h = ex.querySelector('#sec' + a.dataset.s);
      // scroll the container, not the page: #exhibit is the scrolling element.
      ex.scrollTo({ top: h.offsetTop - nav.offsetHeight - 8, behavior: 'smooth' });
    });

    // scroll-spy, so the spine says where you are as well as what exists
    const links = [...nav.querySelectorAll('a')];
    const spy = () => {
      const y = ex.scrollTop + nav.offsetHeight + 24;
      let cur = -1;
      hs.forEach((h, i) => { if (h.offsetTop <= y) cur = i; });
      links.forEach((a, i) => a.classList.toggle('on', i === cur));
    };
    ex.addEventListener('scroll', spy, { passive: true });
    spy();
  }

  function branchExhibit(n, rec) {
    const A = window.APP, s = summarise(rec);
    const path = [];
    (function find(r, acc) {
      if (r === rec) { path.push(...acc.map(x => x.n)); return true; }
      for (const k of r.kids) if (find(k, acc.concat([r.n]))) return true;
      return false;
    })(T.laid.root, []);
    let h = '<div class="exkicker">' + (path.map(p => esc(p)).join(' › ') || 'a branch') +
      '</div><h2 class="exname" style="font-size:31px">' + esc(n.n) + '</h2>' +
      '<div class="exalt"><span>a branch of the family, not a language · click it again to ' +
      (T.collapsed.has(n.g) ? 'open' : 'close') + '</span></div>';
    // ⚠ THIS IS THE THIRD OF THREE SITES that render a branch description, and it is the one
    // branchExhibit actually uses. Patching the other two left Slavic still reading "A branch of
    // Indo-European" while the authored text sat unused in the data. Three copies of one decision
    // is the defect; the comment stays until they are one function.
    const bt0 = A.families && A.families.branch_text && A.families.branch_text[n.g];
    if (bt0) h += '<p class="exstory" style="font-size:14px">' + emph(esc(bt0)) + '</p>';
    else if (substantiveD(n.d)) h += '<p class="exdesc">' + esc(n.d) + '</p>';
    else {
      const bc = A.descr && A.descr.branches && A.descr.branches[n.g];
      if (bc) h += '<p class="exdesc excomp">' + esc(bc) + '</p>';
    }
    const CL = A.families && A.families.clusters_by_node && A.families.clusters_by_node[n.g];
    const bits = ['<b>' + s.lang + '</b> language' + (s.lang === 1 ? '' : 's')];
    if (s.ext) bits.push('<b>' + s.ext + '</b> extinct');
    if (s.end) bits.push('<b>' + s.end + '</b> endangered');
    h += '<p class="exdesc" style="font-size:13.5px">' + bits.join(' · ') + '.' +
      (s.oldest ? ' The earliest written member is <b>' + esc(s.oldestN.n) + '</b>, attested ' +
        (s.oldest < 0 ? (-s.oldest) + ' BCE' : s.oldest + ' CE') + '.' : '') +
      (s.ext === s.lang && s.lang ? ' <b>Nobody speaks any of them.</b>' : '') + '</p>';
    h += clusterBlock(CL, s.lang, true);
    if (s.box) {
      h += '<div class="exmapwrap"><canvas class="exmapcv"></canvas>' +
        '<canvas class="exworldcv"></canvas><div class="exmapcap">where its languages are ' +
        'recorded · click to open the ground</div></div>';
    }
    if (s.named.length) {
      h += '<h3>Among them</h3><div class="words">' + s.named.map(m =>
        '<div><b>' + esc(m.au && canRender(m.au[0]) ? m.au[0] : m.n) + '</b><span>' +
        esc(m.n) + '</span></div>').join('') + '</div>';
    }
    setExhibit(h);
    $('#exhibit').classList.remove('empty');
    if (s.box) drawMaps(s.box[0], s.box[1], s.box[2], n.g, null);
    T.sel = n; draw();
  }

  function drawMaps(lon, lat, span, gc, p) {
    const mc = $('#exhibit .exmapcv'), wc = $('#exhibit .exworldcv');
    let t = 0;
    const go = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const w = mc ? (mc.clientWidth || mc.getBoundingClientRect().width) : 0;
      if (w < 60 && t++ < 40) { requestAnimationFrame(go); return; }
      if (w < 60) return;
      mc.width = Math.round(w * dpr); mc.height = Math.round((mc.clientHeight || 150) * dpr);
      window.APP.snapshot(mc, lon, lat, span);
      if (wc) {
        wc.width = Math.round(w * dpr); wc.height = Math.round(w * dpr / 2);
        window.APP.worldBox(wc, lon, lat, span);
      }
    };
    requestAnimationFrame(go);
    setTimeout(go, 900);
    if (mc) mc.addEventListener('click', () => window.APP.showCardFor(gc, p || [lon, lat]));
  }

  // ---- dated events ------------------------------------------------------
  // A timeline, not a paragraph. Each row carries its own year so a reader can see the gaps —
  // Korean's 1443 alphabet sitting four and a half centuries before 1894, when it finally
  // became the official script, is a fact you can only see laid out.
  function yearLabel(y, approx) {
    const s = y < 0 ? Math.abs(y) + ' BCE' : String(y);
    return (approx ? 'c. ' : '') + s;
  }

  function milestoneBlock(rows) {
    let h = '<h3>Dated</h3><ol class="mstone">';
    for (const [y, approx, text] of rows) {
      h += '<li><span class="msy">' + esc(yearLabel(y, approx)) + '</span>' +
        '<span class="mst">' + esc(text) + '</span></li>';
    }
    h += '</ol>';
    const nap = rows.filter(r => r[1]).length;
    h += '<p class="exfine">' + rows.length + ' events' +
      (nap ? ' · ' + nap + ' dated only approximately, shown as c.' : '') + '</p>';
    return h;
  }

  // ---- is it being written today -----------------------------------------
  // Article count alone lies: two of the largest Wikipedias in the world were written almost
  // entirely by one bot each. Active editors — people who made five or more edits last month —
  // is the number a script cannot inflate, so both are shown and the ratio is named.
  function wikiBlock(w) {
    const per = w.articles / Math.max(w.active, 1);
    let h = '<h3>Written today</h3><dl class="exfacts">';
    h += '<dt>articles</dt><dd>' + w.articles.toLocaleString() + '</dd>';
    h += '<dt>active editors</dt><dd>' + w.active.toLocaleString() +
      '  ·  five or more edits in the last month</dd>';
    h += '<dt>total edits</dt><dd>' + w.edits.toLocaleString() + '</dd>';
    h += '</dl>';
    if (w.active >= 5 && per > 2000) h += '<p class="exfine">' +
      Math.round(per).toLocaleString() + ' articles for every active editor. A ratio this ' +
      'high means most of the articles were generated by a program rather than written, and ' +
      'the article count says little about how much the language is used.</p>';
    else if (w.active < 3) h += '<p class="exfine">Almost nobody is editing it. An ' +
      'encyclopedia exists in this language; it is not currently being added to.</p>';
    else h += '<p class="exfine">' + Math.round(per).toLocaleString() + ' articles per ' +
      'active editor.</p>';
    h += '<p class="exfine">Wikipedia <b>' + esc(w.code) + '</b>' +
      (w.localname ? ' · ' + esc(w.localname) : '') + ' · Wikimedia site statistics, ' +
      esc(w.retrieved || '') + '.</p>';
    return h;
  }

  // ⚠ MUST MATCH build_descriptions.py's substantive(). Glottolog's description field is
  // frequently the bare words "language" or "language family" — truthy, and useless. A plain
  // `if (n.d)` therefore printed "language family" on a branch card and suppressed the composed
  // description that had been generated precisely because that field says nothing.
  const GENERIC_D = new RegExp('^(a |an |the )?(' +
    'language|language family|dialect|natural language|macrolanguage|human language|' +
    'language group|creole language|pidgin' +
    '|(branch|sub-?family|group|sub-?group|division|cluster|dialect continuum|variety|' +
    'varieties)\\s+of\\b.{0,70}' +
    '|.{0,45}\\slanguage family' +
    '|.{0,45}\\slanguages?' +
    '|language\\s+(of|in|spoken in|from)\\b.{0,45}' +
    '|(extinct|ancient|historical|classical|modern|dead|sign)\\s+language.{0,25}' +
    ')\\.?$', 'i');
  function substantiveD(d) {
    d = (d || '').trim();
    return !!d && d.length > 16 && !GENERIC_D.test(d);
  }

  // ---- why so many of these names look alike ------------------------------
  // The measured answer to the most confusing thing about this tree. Otomanguean shows 181
  // languages of which 56 end in Zapotec and 53 in Mixtec; Quechuan 42 of 43 end in Quechua or
  // Quichua. Those are cover terms, not languages, and the count is computed per node, so the
  // family card and the Mixtec branch card each explain their own naming without either being
  // authored by hand. 24 families and 147 nodes carry one.
  function clusterBlock(cl, total, forBranch) {
    if (!cl || !cl.length) return '';
    const covered = cl.reduce((a, c) => a + c[1], 0);
    // ⚠ Written out per case rather than concatenated. Gluing the clauses together produced
    // "This branch holds 40 of them share the same last word in their name."
    let lead, tail = ' Each of those words is a <b>cover term rather than a single language</b>: ' +
      'the varieties under it are often no more mutually intelligible than Spanish and ' +
      'Portuguese, so each is counted separately, and each is named after the town or the ' +
      'region that speaks it.';
    if (forBranch && cl.length === 1) {
      lead = (covered === total
        ? 'All <b>' + total + '</b> languages in this branch are called <b>'
        : '<b>' + covered + '</b> of the <b>' + total + '</b> languages in this branch are ' +
          'called <b>') + esc(cl[0][0]) + '</b>.';
      tail = ' That is a <b>cover term rather than a single language</b>: the varieties under it ' +
        'are often no more mutually intelligible than Spanish and Portuguese, so each is ' +
        'counted separately, and each is named after the town or the region that speaks it.';
    } else if (forBranch) {
      lead = 'This branch holds <b>' + covered + '</b> languages in <b>' + cl.length +
        '</b> groups whose names each end the same way.';
    } else if (cl.length === 1) {
      lead = '<b>' + covered + '</b> of the <b>' + total + '</b> languages here share the same ' +
        'last word in their name.';
    } else {
      lead = '<b>' + covered + '</b> of <b>' + total + '</b> languages here fall into <b>' +
        cl.length + '</b> groups whose names each end the same way.';
    }
    let h = '<h3>Why so many of these names look alike</h3>';
    h += '<p class="exstory" style="font-size:13.5px">' + lead + tail + '</p>';
    if (!(forBranch && cl.length === 1)) {
      h += '<div class="clus">' + cl.map(c =>
        '<div><b>' + esc(c[0]) + '</b><span>' + c[1] + ' languages</span></div>').join('') +
        '</div>';
    }
    return h;
  }

  // ---- the family card ---------------------------------------------------
  // Opening a family used to say "Choose a language from the tree." and nothing else — the most
  // prominent panel in the room was empty at the moment a visitor arrived in it.
  function familyExhibit(gc) {
    const A = window.APP;
    const FS = A.families && A.families.by_glottocode && A.families.by_glottocode[gc];
    const ex = $('#exhibit');
    if (!FS) {
      setExhibit('<p class="exempty">Choose a language from the tree.</p>');
      ex.classList.add('empty');
      return;
    }
    ex.classList.remove('empty');
    // ⚠ NO TITLE AND NO COUNTS HERE. #treehead already carries the family's name, its language
    // and dialect counts, its extinct and endangered totals, its macroarea and its root age; a
    // card that repeated all of that put "Otomanguean · 181 languages" on the screen twice,
    // sixty pixels apart. The card carries only what the head does not.
    const gal = galOf(gc);
    let h = '<div class="exkicker">' + (FS.isolate ? 'an isolate — one language, with no known '
      + 'relatives anywhere' : 'about this family') + '</div>';
    if (gal.length) {
      const g0 = gal[0];
      h += '<figure class="exfig"><button type="button" class="exfigb" data-lb="0" data-lbg="' +
        esc(gc) + '" aria-label="See this larger"><img src="' +
        window.V('img/gallery/' + g0.file) + '" alt="' + esc(g0.subject || '') +
        '" loading="lazy"></button><figcaption>' + esc(objTitle(g0)) +
        (g0.artist ? ' · ' + esc(g0.artist) : '') + '</figcaption></figure>';
    }
    if (FS.text) h += '<p class="exstory">' + emph(esc(FS.text)) + '</p>';
    else {
      const fc = A.descr && A.descr.families && A.descr.families[gc];
      if (fc) h += '<p class="exstory excomp">' + esc(fc) + '</p>' +
        '<p class="exfine">Composed from the record. 70 of the 421 families here carry a ' +
        'written description; this is not one of them yet.</p>';
    }

    const facts = [];
    if (FS.countries) facts.push(['countries', String(FS.countries)]);
    if (FS.earliest) facts.push(['earliest written',
      FS.earliest[1] + ' · ' + (FS.earliest[0] < 0 ? (-FS.earliest[0]) + ' BCE'
        : FS.earliest[0] + ' CE')]);
    facts.push(['glottocode', gc]);
    h += '<dl class="exfacts">' + facts.map(f =>
      '<dt>' + esc(f[0]) + '</dt><dd>' + esc(f[1]) + '</dd>').join('') + '</dl>';

    h += clusterBlock(FS.clusters, FS.lang, false);

    // What this museum actually holds for the family. A thin family should read as thin rather
    // than as complete, which is the whole point of printing it.
    const cov = FS.coverage || {};
    const ORDER = [['label', 'labels'], ['object', 'objects'], ['prose', 'prose'],
                   ['words', 'word lists'], ['letters', 'letters'], ['heard', 'recordings'],
                   ['dated', 'timelines']];
    const rowsC = ORDER.filter(o => cov[o[0]]);
    if (rowsC.length) {
      h += '<h3>What this museum holds for it</h3><div class="cov">' + rowsC.map(o => {
        const pct = Math.max(2, Math.round(100 * cov[o[0]] / Math.max(FS.lang, 1)));
        return '<div class="covrow"><span class="covn">' + cov[o[0]] + '</span>' +
          '<span class="covl">' + esc(o[1]) + '</span>' +
          '<span class="covbar"><i style="width:' + Math.min(pct, 100) + '%"></i></span></div>';
      }).join('') + '</div>';
      h += '<p class="exfine">Out of ' + FS.lang + ' language' + (FS.lang === 1 ? '' : 's') +
        '. Where a row is short, the record is short — not the family.</p>';
    }

    if (gal.length > 1) {
      h += '<h3>Objects</h3><div class="exgal">' + gal.slice(1).map((o, k) =>
        '<figure><button type="button" data-lb="' + (k + 1) + '" data-lbg="' + esc(gc) +
        '" aria-label="See this larger"><img src="' + window.V('img/gallery/' + o.file) +
        '" alt="' + esc(o.subject || '') + '" loading="lazy"></button><figcaption>' +
        esc(objTitle(o)) + (o.artist ? '<span> · ' + esc(o.artist) + '</span>' : '') +
        '</figcaption></figure>').join('') + '</div>';
    }
    h += '<p class="exfine">Click a language in the tree for its own card, or a fork to open ' +
      'that branch.</p>';
    setExhibit(h);
  }

  // ---- the lightbox ------------------------------------------------------
  // Clicking an object opens it large, in the middle of THIS page. It used to open Wikimedia
  // Commons in a new tab, which threw the visitor out of the museum to look at an exhibit that
  // was already in front of them.
  //
  // Two sources, in order. The local copy appears immediately — it is 460-640 px and already in
  // cache, so the image is on screen the instant you click. The full-resolution file then loads
  // from Commons behind it and swaps in when ready, which is why there is no blank pause and why
  // this still works with no network. The card's whole set is loaded, so arrow keys walk it.
  const LB = { objs: [], i: 0, el: null, prev: null };

  // Commons stores a filename; a museum label is not a filename. Strip the extension and turn
  // underscores into spaces, and stop there — hyphens carry shelfmarks (KBo-14-1) and joining
  // them would destroy the one part of the name that identifies the object.
  // Authored prose marks linguistic examples with *asterisks*, because a form quoted as an
  // example is conventionally italic and a plain sentence cannot show that. Applied AFTER esc(),
  // so the input is already neutralised and this can only ever emit <i>.
  function emph(escaped) {
    return escaped.replace(/\*([^*<>]{1,80})\*/g, '<i>$1</i>');
  }

  function objTitle(o) {
    return String((o && o.title) || '').replace(/\.(jpe?g|png|gif|tiff?|djvu|svg|webp)$/i, '')
      .replace(/_/g, ' ').trim();
  }

  function lbBuild() {
    if (LB.el) return LB.el;
    const d = document.createElement('div');
    d.id = 'lightbox';
    d.setAttribute('role', 'dialog');
    d.setAttribute('aria-modal', 'true');
    d.hidden = true;
    d.innerHTML =
      '<button type="button" class="lbx" aria-label="Close">\u00D7</button>' +
      '<button type="button" class="lbnav lbprev" aria-label="Previous">\u2039</button>' +
      '<button type="button" class="lbnav lbnext" aria-label="Next">\u203A</button>' +
      '<figure class="lbfig"><img alt=""><figcaption></figcaption></figure>';
    document.body.appendChild(d);
    d.addEventListener('click', e => {
      // the scrim closes; the picture and its caption do not
      if (e.target === d) lbClose();
    });
    d.querySelector('.lbx').addEventListener('click', lbClose);
    d.querySelector('.lbprev').addEventListener('click', e => { e.stopPropagation(); lbStep(-1); });
    d.querySelector('.lbnext').addEventListener('click', e => { e.stopPropagation(); lbStep(1); });
    LB.el = d;
    return d;
  }

  function lbShow() {
    const d = lbBuild(), o = LB.objs[LB.i];
    if (!o) return;
    const img = d.querySelector('img'), cap = d.querySelector('figcaption');
    d.classList.add('loading');
    img.alt = o.subject || o.title || '';
    // the local copy first, so something is on screen at once
    img.src = window.V('img/gallery/' + o.file);
    if (o.big) {
      const hi = new Image();
      hi.onload = () => {
        // guard against a slow load arriving after the visitor has moved on
        if (LB.objs[LB.i] === o && !d.hidden) { img.src = hi.src; d.classList.remove('loading'); }
      };
      hi.onerror = () => { if (LB.objs[LB.i] === o) d.classList.remove('loading'); };
      hi.src = o.big;
    } else {
      d.classList.remove('loading');
    }
    const bits = [];
    if (o.title) bits.push('<b>' + esc(objTitle(o)) + '</b>');
    if (o.artist) bits.push(esc(o.artist));
    if (o.licence) bits.push(esc(o.licence));
    cap.innerHTML = bits.join(' &middot; ') +
      (LB.objs.length > 1 ? '<span class="lbn">' + (LB.i + 1) + ' of ' +
        LB.objs.length + '</span>' : '') +
      (o.page ? '<a href="' + esc(o.page) + '" target="_blank" rel="noopener">' +
        'source on Wikimedia Commons</a>' : '');
    const nav = LB.objs.length > 1;
    d.querySelector('.lbprev').hidden = !nav;
    d.querySelector('.lbnext').hidden = !nav;
  }

  function lbOpen(objs, i) {
    if (!objs || !objs.length) return;
    LB.objs = objs;
    LB.i = Math.max(0, Math.min(i | 0, objs.length - 1));
    LB.prev = document.activeElement;
    const d = lbBuild();
    d.hidden = false;
    document.body.classList.add('lbopen');
    lbShow();
    d.querySelector('.lbx').focus();
  }

  function lbStep(n) {
    if (LB.objs.length < 2) return;
    LB.i = (LB.i + n + LB.objs.length) % LB.objs.length;
    lbShow();
  }

  function lbClose() {
    if (!LB.el || LB.el.hidden) return;
    LB.el.hidden = true;
    LB.el.querySelector('img').removeAttribute('src');   // stop a download in flight
    document.body.classList.remove('lbopen');
    if (LB.prev && LB.prev.focus) LB.prev.focus();
  }

  document.addEventListener('keydown', e => {
    if (!LB.el || LB.el.hidden) return;
    if (e.key === 'Escape') { e.preventDefault(); lbClose(); }
    else if (e.key === 'ArrowLeft') { e.preventDefault(); lbStep(-1); }
    else if (e.key === 'ArrowRight') { e.preventDefault(); lbStep(1); }
  });

  // Delegated once. The exhibit's innerHTML is replaced on every card, so a listener written
  // into that HTML would be rebound on every render.
  document.addEventListener('click', e => {
    const t = e.target.closest && e.target.closest('[data-lb]');
    if (!t) return;
    e.preventDefault();
    lbOpen(galOf(t.dataset.lbg), parseInt(t.dataset.lb, 10) || 0);
  });

  // ---- the letters ------------------------------------------------------
  // One block per language, and it renders whatever the data actually is. An alphabet gets
  // its letters; an abugida gets its letters AND its vowel marks as separate rows, because
  // that is the thing that makes it an abugida; a syllabary says so; Han says it is not
  // letters at all. Korean gets the arithmetic: the jamo, and the number of blocks they build.
  function alphaGrid(units, lang, cls) {
    return '<div class="alpha' + (cls ? ' ' + cls : '') + '"' +
      (lang ? ' lang="' + esc(lang) + '"' : '') + '>' +
      units.map(u => '<span>' + esc(u) + '</span>').join('') + '</div>';
  }

  function alphaBlock(v, n, meta) {
    const lang = n.au ? (n.au[1] || '') : '';
    const G = meta.unit_gloss || {};
    let h = '<h3>Its letters</h3>';

    // Name the script once, in the heading. Repeating "Devanagari" on the letters row, the
    // vowel-marks row and the signs row reads as three scripts rather than three kinds of
    // sign in one. Where a language really does use several — Japanese — the rows say which.
    const scripts = [...new Set((v.groups || []).map(g => g.script))];
    const oneScript = scripts.length === 1;
    if (v.kind) h += '<p class="alphakind">' + (oneScript ? '<b>' + esc(scripts[0]) +
      '</b> · ' : '') + '<b>' + esc(v.kind) + '</b> — ' + esc(v.kind_note || '') + '</p>';
    else if (oneScript) h += '<p class="alphakind"><b>' + esc(scripts[0]) + '</b></p>';

    // Korean, and any script whose "letters" in the data are really composed blocks.
    if (v.hangul) {
      const hg = v.hangul;
      h += '<p class="exfine alphalead">' + hg.letters + ' letters, which combine into ' +
        hg.blocks.toLocaleString() + ' syllable blocks — so a font needs ' +
        hg.blocks.toLocaleString() + ' shapes and a reader needs ' + hg.letters + '.</p>';
      h += '<div class="alpharow"><span class="alphatag">' + hg.initial.length +
        ' consonants</span><span class="alphanote">that can open a block</span></div>' +
        alphaGrid(hg.initial, lang);
      h += '<div class="alpharow"><span class="alphatag">' + hg.medial.length +
        ' vowels</span></div>' + alphaGrid(hg.medial, lang);
      h += '<div class="alpharow"><span class="alphatag">' + hg.final.length +
        ' endings</span><span class="alphanote">consonants and clusters that can close one' +
        '</span></div>' + alphaGrid(hg.final, lang);
      if (hg.letters_note) h += '<p class="exfine">' + esc(hg.letters_note) + '</p>';
    } else {
      for (const g of (v.groups || [])) {
        // The gloss arrives as [tag label, explanation] — split in the builder, so nothing
        // here has to slice a sentence on its commas and cut it in the wrong place.
        const gl = G[g.unit] || [g.unit.toLowerCase(), ''];
        h += '<div class="alpharow"><span class="alphatag">' + g.n + ' ' +
          esc((oneScript || g.any) ? gl[0] : g.script + ' ' + gl[0]) + '</span>' +
          (gl[1] ? '<span class="alphanote">' + esc(gl[1]) + '</span>' : '') + '</div>' +
          alphaGrid(g.show, lang, g.n > 200 ? 'dense' : '');
        if (g.truncated) h += '<p class="exfine">' + g.show.length + ' of ' + g.n +
          ' shown.</p>';
      }
    }

    // CLDR's index is the letters a reader recites and looks words up under — but only when
    // it is in the same script as the letters themselves. Chinese is indexed by pinyin, so
    // its index set is the Latin alphabet, and showing that here would say something false.
    if (v.index && v.index.length && !v.hangul && v.index_n !== v.n) {
      const own = new Set();
      for (const g of (v.groups || [])) for (const u of g.show) own.add(u);
      const shared = v.index.filter(u => own.has(u)).length / v.index.length;
      if (shared > 0.6) {
        h += '<div class="alpharow"><span class="alphatag">' + v.index_n +
          ' in order</span><span class="alphanote">the letters as a reader recites them, ' +
          'and looks words up under</span></div>' + alphaGrid(v.index, lang);
      }
    }

    if (v.digits && v.digits.length) h += '<div class="alpharow"><span class="alphatag">' +
      'digits</span><span class="alphanote">its own numerals, alongside 0–9</span></div>' +
      alphaGrid(v.digits, lang);

    if (v.punctuation && v.punctuation.length)
      h += '<div class="alpharow"><span class="alphatag">marks</span>' +
        '<span class="alphanote">punctuation this language uses that English does not' +
        '</span></div>' + alphaGrid(v.punctuation, lang, 'punct');

    for (const alt of (v.also || [])) {
      const sc = alt.label || ((alt.groups && alt.groups[0]) ? alt.groups[0].script
        : 'another script');
      h += '<div class="alpharow alphaalt"><span class="alphatag">also in ' + esc(sc) +
        '</span>' + (alt.note ? '<span class="alphanote">' + esc(alt.note) + '</span>' : '') +
        '</div>';
      for (const g of (alt.groups || [])) h += alphaGrid(g.show, lang,
        g.n > 200 ? 'dense' : '');
    }

    // A language written in two scripts, found by comparing the letters against the script of
    // the prose lower down the card. Uyghur's letters are Arabic; the UDHR translation we hold
    // is in Latin. Both are true, and the reader should not have to notice the mismatch alone.
    if (v.prose_script) h += '<p class="exfine">This language is written in more than one ' +
      'script. The letters above are the ' + esc((v.groups && v.groups[0]) ?
      v.groups[0].script : '') + ' set; the prose further down this card is in ' +
      esc(v.prose_script) + '.</p>';
    if (v.note) h += '<p class="exfine">' + esc(v.note) + '</p>';
    h += '<p class="exfine">' + (v.tier === 'curated'
      ? 'The characters literate writers of this language use. Unicode CLDR.'
      : 'Measured from ' + (v.sample || 0).toLocaleString() + ' characters of ' +
        esc(v.from || 'prose held here') + ' — an <b>observed inventory, not a curated ' +
        'alphabet</b>. A short text misses rare letters and picks up any a loanword brings in.' +
        (v.foreign ? ' ' + v.foreign.toLocaleString() + ' further characters in that text were ' +
          'in another script — quoted names and passages — and are not counted here.' : ''))
      + '</p>';
    return h;
  }

  // Exposed on T so a card can be opened by glottocode without simulating a canvas click.
  // Every round has to look at a card to verify it (rule 1) and hunting for the pixel a node
  // was drawn at is how that verification quietly stops happening.
  function showByCode(gc) {
    if (!T.tree) return false;
    // Open every branch above it first. The laid-out node list holds only what is currently
    // visible, so a language inside a shut branch cannot be found there at all.
    const chain = [];
    // ⚠ The DATA tree uses `c` for children; only the laid-out records use `kids`. Walking
    // `kids` here found one node and silently reported the language as absent.
    (function walk(n, acc) {
      if (n.g === gc) { chain.push(...acc); return true; }
      for (const k of (n.c || [])) if (walk(k, acc.concat([n.g]))) return true;
      return false;
    })(T.tree, []);
    if (!chain.length && T.tree.g !== gc) return false;
    for (const g of chain) T.collapsed.delete(g);
    layout();
    const r = T.laid.nodes.find(z => z.n.g === gc);
    if (!r) return false;
    if (r.n.lv === 0 && r.hasKids) branchExhibit(r.n, r); else exhibit(r.n, r);
    draw();
    return true;
  }

  function exhibit(n, rec) {
    if (rec && rec.kids && rec.kids.length) return branchExhibit(n, rec);
    T.sel = n;
    const A = window.APP;
    const tx = A.texts && A.texts.by_glottocode[n.g];
    const wd = A.words && A.words.by_glottocode[n.g];
    const path = [];
    (function find(r, acc) {
      if (r.n === n) { path.push(...acc.map(x => x.n)); return true; }
      for (const k of r.kids) if (find(k, acc.concat([r.n]))) return true;
      return false;
    })(T.laid.root, []);

    const au = n.au ? n.au[0] : null;
    let h = '';
    h += '<div class="exkicker">' + (path.slice(0, 6).map(p => esc(p)).join(' › ') || '') + '</div>';
    h += '<h2 class="exname"' + (au ? ' lang="' + esc(n.au[1] || '') + '"' : '') + '>' +
         esc(au || n.n) + '</h2>';
    if (au) h += '<div class="exalt">' + esc(n.n) + ' <span>· reference name</span></div>';
    else h += '<div class="exalt"><span>reference name · no autonym recorded</span></div>';

    const gal = galOf(n.g);
    if (gal.length) {
      const g0 = gal[0];
      h += '<figure class="exfig"><button type="button" class="exfigb" data-lb="0" data-lbg="' +
        esc(n.g) + '" aria-label="See this larger"><img src="' +
        window.V('img/gallery/' + g0.file) + '" alt="' + esc(g0.subject) + '" loading="lazy">' +
        '</button><figcaption>' + esc(objTitle(g0)) +
        (g0.artist ? ' · ' + esc(g0.artist) : '') + '</figcaption></figure>';
    }
    // An authored museum label if there is one; otherwise the description composed from this
    // build's own record — and the card says which, because a paragraph someone wrote and a
    // paragraph assembled from database columns are different kinds of claim.
    const story = A.notable && A.notable.by_glottocode && A.notable.by_glottocode[n.g];
    if (story) {
      h += '<p class="exstory">' + emph(esc(story)) + '</p>';
      // What the checkable claims rest on. Only the labels that carry one show a line; the rest
      // say nothing rather than pointing at a source that was never consulted.
      const cite = A.notable.sources && A.notable.sources[n.g];
      if (cite) h += '<p class="excite">' + esc(cite) + '</p>';
    } else {
      const comp = A.descr && A.descr.by_glottocode && A.descr.by_glottocode[n.g];
      if (comp) h += '<p class="exstory excomp">' + esc(comp) + '</p>' +
        '<p class="exfine">Composed from the record — its place in the catalogue, the ' +
        'endangerment assessment, the depth of description published about it, and what this ' +
        'museum holds. Not an authored label.</p>';
      // The nearest branch above it that someone has written about. A composed paragraph says
      // where a language sits; its branch says what happened to the speech, and one branch
      // covers every language under it — Caribbean English Creole explains seventeen at once.
      const nb = A.descr && A.descr.near_branch && A.descr.near_branch[n.g];
      const nbt = nb && A.families && A.families.branch_text
        && A.families.branch_text[nb[0]];
      if (nbt) h += '<h3>Its branch</h3><p class="exstory" style="font-size:13.5px">' +
        '<b>' + esc(nb[1]) + '</b> — ' + emph(esc(nbt)) + '</p>' +
        '<p class="exfine">This describes the branch, not this language on its own.</p>';
    }

    const ms = A.milestones && A.milestones.by_glottocode && A.milestones.by_glottocode[n.g];
    if (ms && ms.length) h += milestoneBlock(ms);

    // HEARD. One shared player and a button per word, rather than six sets of transport
    // controls: the words are the exhibit and the player is furniture. A word marked as being
    // in the passage lower down the card says so, because reading it and then hearing it is
    // the whole point of having both.
    // ⚠ NOT `au` — that is the autonym in this scope, and redeclaring it threw a SyntaxError
    // on load. A redeclared const shipped once here and blanked the whole genealogy view; the
    // build now runs `node --check`, which is what caught this one before it left the machine.
    const snd = A.audio && A.audio.by_glottocode && A.audio.by_glottocode[n.g];
    if (snd && snd.items && snd.items.length) {
      h += '<h3>Heard</h3><div class="heard">' + snd.items.map(it =>
        '<button type="button" class="hplay" data-url="' + esc(it.url) + '">' +
        '<span class="hicon" aria-hidden="true">\u25B6</span>' +
        '<span class="hw"' + (n.au ? ' lang="' + esc(n.au[1] || '') + '"' : '') + '>' +
        esc(it.w) + '</span>' +
        (it.intext ? '<span class="hin">in the passage below</span>' : '') +
        '</button>').join('') + '</div>';
      h += '<audio id="exau" preload="none"></audio>';
      const speakers = [...new Set(snd.items.map(i => i.speaker).filter(Boolean))];
      const lics = [...new Set(snd.items.map(i => i.licence).filter(Boolean))];
      h += '<p class="exfine">' + snd.items.length + ' of <b>' +
        snd.available.toLocaleString() + '</b> recordings this archive holds for the language' +
        (speakers.length ? ', spoken by ' + esc(speakers.slice(0, 3).join(', ')) +
          (speakers.length > 3 ? ' and others' : '') : '') + '. ' +
        esc(lics.join(', ')) + ' · Lingua Libre, streamed from Wikimedia Commons rather than ' +
        'copied here. The language comes from the Commons category the recording is filed ' +
        'under, which carries the ISO code — never from its filename, which is how an earlier ' +
        'attempt returned a Spanish recording as Basque.</p>';
    }

    if (n.p) {
      h += '<div class="exmapwrap"><canvas class="exmapcv"></canvas>' +
        '<canvas class="exworldcv"></canvas>' +
        '<div class="exmapcap">' +
        esc(n.p[1].toFixed(2)) + (n.p[1] >= 0 ? '°N ' : '°S ') +
        esc(Math.abs(n.p[0]).toFixed(2)) + (n.p[0] >= 0 ? '°E' : '°W') +
        ' · click to open the ground</div></div>';
    }
    // Authored branch prose first, then Glottolog's own if it says anything, then the composed
    // floor. "branch of the Indo-European language family" now fails substantiveD and falls
    // through, which is the whole point of tightening it.
    const bt = A.families && A.families.branch_text && A.families.branch_text[n.g];
    if (bt) h += '<p class="exstory" style="font-size:14px">' + emph(esc(bt)) + '</p>';
    else if (substantiveD(n.d)) h += '<p class="exdesc">' + esc(n.d) + '</p>';
    else {
      const bc0 = A.descr && A.descr.branches && A.descr.branches[n.g];
      if (bc0) h += '<p class="exdesc excomp">' + esc(bc0) + '</p>';
    }
    const CL = A.families && A.families.clusters_by_node && A.families.clusters_by_node[n.g];

    const facts = [];
    if (n.a) facts.push(['vitality', AESN[n.a]]);
    if (n.y) facts.push(['first attested', n.y < 0 ? (-n.y) + ' BCE' : String(n.y)]);
    // Rule 14: the count is a TRIPLE. Showing the value and the year without the authority
    // invites the reader to trust a figure that may have been copied forward for decades.
    if (n.sp) facts.push(['speakers', n.sp[0].toLocaleString() + '  ·  as of ' + n.sp[1],
                          n.sp[2] || '']);
    if (n.cc) facts.push(['countries', n.cc]);
    if (n.i) facts.push(['ISO 639-3', n.i]);
    facts.push(['glottocode', n.g]);
    if (tx && tx.s) facts.push(['script', tx.s + (tx.d === 'rtl' ? ', right to left' : '')]);
    // A fact may carry a third element: the authority behind it, set small under the value.
    h += '<dl class="exfacts">' + facts.map(f =>
      '<dt>' + esc(f[0]) + '</dt><dd>' + esc(f[1]) +
      (f[2] ? '<span class="exfine" style="display:block">' + esc(f[2]) + '</span>' : '') +
      '</dd>').join('') + '</dl>';

    const ty = A.typology && A.typology.by_glottocode && A.typology.by_glottocode[n.g];
    if (ty) h += '<h3>How it works</h3><p class="exstory" style="font-size:14px">' +
      esc(ty) + '</p><p class="exfine">WALS Online (Dryer &amp; Haspelmath, eds.).</p>';

    // The letters, before the words — you look at a script before you read it. The set is
    // shown taken apart by script and by unit type, because "how many letters" means three
    // different things in an alphabet, an abugida and a syllabary.
    const AL = A.alphabets && A.alphabets.by_glottocode && A.alphabets.by_glottocode[n.g];
    if (AL) h += alphaBlock(AL, n, A.alphabets);

    const wk = A.wikipedia && A.wikipedia.by_glottocode && A.wikipedia.by_glottocode[n.g];
    if (wk) h += wikiBlock(wk);

    // Authored phrases come FIRST where they exist: for an ancient language they are the
    // only words there are, and they carry the script as well as the meaning.
    const ph = A.phrases && A.phrases.by_glottocode && A.phrases.by_glottocode[n.g];
    if (ph) {
      h += '<h3>Words and phrases</h3>';
      // The note goes ABOVE the list, because it says how to read what follows — which script
      // these are in, or that the forms are a transliteration because the language's own
      // letterforms could not be set with confidence. Below the list it arrives too late.
      if (ph.note) h += '<p class="exfine" style="margin-top:-2px">' + esc(ph.note) + '</p>';
      h += '<dl class="phr">' + ph.items.map(it =>
        '<dt' + (n.au ? ' lang="' + esc(n.au[1] || '') + '"' : '') + '>' + esc(it[0]) + '</dt>' +
        '<dd>' + (it[1] && it[1] !== it[0] ? '<i>' + esc(it[1]) + '</i> · ' : '') +
        esc(it[2]) + '</dd>').join('') + '</dl>';
    }

    // ⚠ NOT BUILT YET. words.json carries `transcription`, `concepts` and `by_glottocode` and
    // no `orth`, so this section has never rendered for any language. The intended source is
    // Wikidata Lexemes (CC0, reachable through the Query Service); until that pipeline exists
    // the gate below is correct — it shows nothing rather than showing IPA under a heading
    // that promises spelling.
    const orth = A.words && A.words.orth && A.words.orth[n.g];
    if (orth) {
      const ks = Object.keys(orth);
      h += '<h3>Words, as written</h3><div class="words">' + ks.map(k =>
        '<div><b lang="' + esc(n.au ? (n.au[1] || '') : '') + '">' + esc(orth[k]) +
        '</b><span>' + esc(k) + '</span></div>').join('') + '</div>' +
        '<p class="exfine">The language\'s own spelling. Wikidata Lexemes.</p>';
    }
    if (wd) {
      const order = ['water', 'fire', 'sun', 'moon', 'star', 'stone', 'mountain', 'tree',
                     'leaf', 'blood', 'bone', 'hand', 'eye', 'ear', 'nose', 'tooth',
                     'tongue', 'skin', 'name', 'person', 'fish', 'bird', 'dog', 'night',
                     'die', 'come', 'see', 'hear', 'drink', 'new', 'full', 'one', 'two'];
      const have = order.filter(k => wd[k]);
      h += '<h3>Words, as spoken</h3><div class="words ipa">' + have.map(k =>
        '<div><b>' + esc(wd[k]) + '</b><span>' + esc(k) + '</span></div>').join('') + '</div>';
      h += '<p class="exfine">' + have.length + ' of ASJP\'s core 40, in the ' +
        '<b>International Phonetic Alphabet</b> — how the word sounds, not how it is spelled. ' +
        'ASJP (Wichmann, Holman &amp; Brown, eds.).</p>';
    }

    if (tx && tx.b && tx.b.length) {
      const missing = (function () {
        try {
          return document.fonts && document.fonts.check
            ? !document.fonts.check('18px ' + SERIF, tx.b[tx.b.length - 1][1].slice(0, 40)) : false;
        } catch (e) { return false; }
      })();
      h += '<h3>In its own words</h3>';
      if (missing) h += '<p class="exwarn">Your device has no font installed for the ' +
        esc(tx.s) + ' script, so some characters below will show as empty boxes. The text is ' +
        'right; the typeface is missing.</p>';
      for (const b of tx.b) {
        h += '<div class="exlabel">' + esc(b[0]) + '</div>' +
          '<blockquote class="exquote" lang="' + esc(tx.l) + '" dir="' + esc(tx.d) + '">' +
          esc(b[1]) + '</blockquote>';
      }
      h += '<p class="exfine">Universal Declaration of Human Rights, UN translations · ' +
        esc(tx.s || '') + ' script.</p>';
    }
    if (!tx && !wd) {
      h += '<p class="exfine">No connected text and no word list have been recorded for this ' +
        'language. That silence is the state of the record, not an omission here.</p>';
    }

    // The rest of the objects. The first one sits at the top of the card as the plate; these
    // are the case behind it. Each carries its own caption and maker, because an object with
    // no attribution is a decoration.
    if (gal.length > 1) {
      h += '<h3>Objects</h3><div class="exgal">' + gal.slice(1).map((o, k) =>
        '<figure><button type="button" data-lb="' + (k + 1) + '" data-lbg="' + esc(n.g) +
        '" aria-label="See this larger"><img src="' + window.V('img/gallery/' + o.file) +
        '" alt="' + esc(o.subject) + '" loading="lazy"></button><figcaption>' + esc(objTitle(o)) +
        (o.artist ? '<span> · ' + esc(o.artist) + '</span>' : '') +
        '</figcaption></figure>').join('') + '</div>';
      h += '<p class="exfine">' + gal.length + ' objects, each admitted on the licence ' +
        'Wikimedia Commons reports for that individual file. Click any one to see it large; ' +
        'arrow keys walk the set.</p>';
    }

    setExhibit(h);
    $('#exhibit').classList.remove('empty');
    const mc = $('#exhibit .exmapcv');
    if (mc && n.p) {
      // The same renderer as the big map, so this really is the ground it is spoken on and
      // not a second, cheaper drawing of it.
      // ⚠ Size it INSIDE a frame: measured straight after innerHTML the element had a
      // clientWidth of 0, so the backing store was 0 wide and the map came out blank.
      let tries = 0;
      const paint = () => {
        const dpr = Math.min(window.devicePixelRatio || 1, 2);
        const w = mc.clientWidth || mc.getBoundingClientRect().width;
        const hh = mc.clientHeight || 150;
        // A width of 2 px is not "laid out yet" any more than 0 is, and it passed a plain
        // truthiness check — the map painted into a 4-pixel canvas and looked empty.
        if (w < 60 && tries++ < 40) { requestAnimationFrame(paint); return; }
        if (w < 60) return;
        mc.width = Math.round(w * dpr);
        mc.height = Math.round(hh * dpr);
        window.APP.snapshot(mc, n.p[0], n.p[1], 26);
      };
      const wc = $('#exhibit .exworldcv');
      const paintWorld = () => {
        if (!wc) return;
        const dpr = Math.min(window.devicePixelRatio || 1, 2);
        const w = wc.clientWidth || wc.getBoundingClientRect().width;
        if (w < 60) { requestAnimationFrame(paintWorld); return; }
        wc.width = Math.round(w * dpr);
        wc.height = Math.round(w * dpr / 2);
        window.APP.worldBox(wc, n.p[0], n.p[1], 26);
      };
      requestAnimationFrame(() => { paint(); paintWorld(); });
      setTimeout(() => { paint(); paintWorld(); }, 900);
      mc.addEventListener('click', () => window.APP.showCardFor(n.g, n.p));
    }
    draw();
  }

  function esc(s) {
    return String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  }

  function hit(ev) {
    const cv = $('#treecv'), b = cv.getBoundingClientRect();
    const mx = ev.clientX - b.left, my = ev.clientY - b.top;
    const L = T.laid;
    if (!L) return null;
    const padL = 26, padR = 300;
    const colW = Math.max(48, (T.W - padL - padR) / (L.maxDepth + 1));
    const rowH = Math.max(3.2, 15 * T.scale);
    let best = null, bd = 1e9;
    for (const r of L.nodes) {
      const x = padL + r.depth * colW + T.ox, y = 30 + r.y * rowH + T.oy;
      const d = Math.abs(y - my) + Math.abs(x - mx) * 0.25;
      if (d < bd && Math.abs(y - my) < Math.max(7, rowH * 0.6) && mx > x - 14) { bd = d; best = r; }
    }
    return best;
  }

  // ONE SEARCH OVER EVERY LANGUAGE. Before this there were two boxes — 429 families, and
  // "within this family" once you had opened one — so a visitor who wanted Warlpiri and did not
  // know it was Pama-Nyungan had no way in. The same field now searches all 7,672 languages by
  // reference name and by autonym, folded, so "Yoruba" finds Yorùbá and "Nahuatl" finds Nāhuatl.
  // ⚠ LOADED LAZILY, ON FIRST KEYSTROKE. tree.js is parsed BEFORE app.js, which is where
  // window.V lives, so fetching at module scope threw ReferenceError into a .catch and left the
  // index permanently null — a search box that silently found nothing.
  let SEARCH = null, SEARCH_ASKED = false;
  function loadSearch() {
    if (SEARCH_ASKED) return;
    SEARCH_ASKED = true;
    fetch(window.V('data/search.json')).then(r => r.json()).then(d => {
      SEARCH = d;
      $('#famq').placeholder = 'search ' + d.rows.length.toLocaleString() + ' languages…';
      renderFamilyList();
    }).catch(() => { SEARCH = null; });
  }

  function foldq(s) {
    return s.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  }

  // Rank: a name that STARTS with the query beats one that merely contains it, and among equals
  // the language with more speakers comes first — otherwise "Ma" leads with something nobody
  // speaks and the list reads as noise.
  function langMatches(q, limit) {
    if (!SEARCH || q.length < 2) return [];
    const f = foldq(q), out = [];
    for (let i = 0; i < SEARCH.folded.length; i++) {
      const at = SEARCH.folded[i].indexOf(f);
      if (at < 0) continue;
      const r = SEARCH.rows[i];
      out.push({ r, score: (at === 0 ? 0 : 1), sp: r[4] });
      if (out.length > 4000) break;
    }
    out.sort((a, b) => a.score - b.score || b.sp - a.sp);
    return out.slice(0, limit).map(x => x.r);
  }

  function renderFamilyList() {
    const q = $('#famq').value.toLowerCase();
    const fams = T.index.families.filter(f => !q || f.n.toLowerCase().includes(q));
    const btn = f =>
      '<button data-g="' + f.g + '"' + (f.g === T.family ? ' class="on"' : '') + '>' +
      '<span class="sw" style="background:' + (f.pseudo ? '#9a938a' : famColour(T.famIdx[f.g])) + '"></span>' +
      '<span class="fn">' + esc(f.n) + '</span>' +
      '<span class="fc">' + (f.isolate ? 'isolate' : f.lang) + '</span></button>';
    const real = fams.filter(f => !f.pseudo && !f.isolate);
    const iso = fams.filter(f => f.isolate);
    const ps = fams.filter(f => f.pseudo);
    const hits = langMatches($('#famq').value.trim(), 40);
    const lbtn = r =>
      '<button class="lang" data-lg="' + r[2] + '" data-fam="' + r[3] + '">' +
      '<span class="sw" style="background:' + famColour(T.famIdx[r[3]] ?? 0) + '"></span>' +
      '<span class="fn">' + esc(r[1] || r[0]) +
      (r[1] ? ' <i>' + esc(r[0]) + '</i>' : '') + '</span>' +
      '<span class="fc">' + esc((SEARCH.famnames[r[3]] || '').slice(0, 18)) + '</span></button>';

    $('#famlist').innerHTML =
      (hits.length ? '<div class="grp">' + hits.length +
        (hits.length === 40 ? '+' : '') + ' language' + (hits.length === 1 ? '' : 's') +
        '</div>' + hits.map(lbtn).join('') +
        (real.length ? '<div class="grp">families</div>' : '') : '') +
      real.slice(0, 400).map(btn).join('') +
      (iso.length ? '<div class="grp">' + iso.length + ' isolates — no known relatives</div>'
        + iso.slice(0, 250).map(btn).join('') : '') +
      (ps.length ? '<div class="grp">not genealogical units</div>' + ps.map(btn).join('') : '');
  }

  function renderHead() {
    const f = T.index.families.find(x => x.g === T.family);
    if (!f) return;
    const bits = [];
    bits.push(f.isolate ? '<b>an isolate</b> — no known relatives'
      : '<b>' + f.lang + '</b> language' + (f.lang === 1 ? '' : 's'));
    if (f.dial) bits.push(f.dial + ' dialects');
    if (f.extinct) bits.push('<b class="dead">' + f.extinct + ' extinct</b>');
    if (f.endangered) bits.push('<b class="warn2">' + f.endangered + ' endangered</b>');
    let age = '';
    if (f.age) {
      age = '<div class="agebar">Root age <b>≈ ' + f.age.toLocaleString() + ' years</b>' +
        (f.ageExplicit ? '' : ' <i>(branch-length unit inferred — treat with caution)</i>') +
        ' · dated phylogeny, Phlorest. <span>Only the root is dated. Distance from left is ' +
        'depth of descent, not time.</span></div>';
    } else if (!f.isolate) {
      age = '<div class="agebar quiet">No dated phylogeny exists for this family: it has ' +
        'topology but no age. 19 of 429 families are dated. Distance from left is depth of ' +
        'descent, not time.</div>';
    }
    $('#treehead').innerHTML = '<h2>' + esc(f.n) + '</h2><div class="sub">' +
      bits.join(' · ') + (f.ma ? ' · mostly ' + esc(f.ma) : '') + '</div>' + age;
  }

  async function openFamily(gc) {
    T.tree = await fetch(window.V('data/tree/' + gc + '.json')).then(r => r.json());
    T.family = gc;
    T.sel = null;
    T.q = '';
    const q = $('#treeq'); if (q) q.value = '';
    familyExhibit(gc);
    // Open shut: a family shows its branches, and the visitor opens the ones they want.
    T.collapsed = new Set();
    (function shut(n, d) {
      if (!(n.c || []).length) return;
      if (d >= 2) { T.collapsed.add(n.g); return; }
      n.c.forEach(c => shut(c, d + 1));
    })(T.tree, 0);
    layout();
    // Fit the whole family in view, then let the visitor zoom in for names.
    const cv = $('#treecv');
    const h = cv.clientHeight || 600;
    T.scale = Math.max(0.16, Math.min(1.6, (h - 70) / (15 * T.laid.leafN)));
    T.ox = 0; T.oy = 0;
    if (T.story) storyTitle();
    draw();
  }

  async function show() {
    await loadIndex();
    renderFamilyList();
    if (!T.family) await openFamily((T.index.families.find(f => !f.pseudo) || T.index.families[0]).g);
    else { layout(); draw(); }
    renderHead();
  }

  /* ---- STORY: the family in broad brushes, on one time axis ----------------------
   * The dendrogram shows every twig and is therefore hard to read at a glance. This is the
   * opposite view: one lane per first-order branch, laid on the years those branches were
   * actually WRITTEN DOWN. It is an attestation axis, not a divergence axis — we have dates
   * for when languages were first recorded, not for when they split, and the caption says so.
   */
  T.story = false;
  function drawStory() {
    const cv = $('#treecv');
    if (!cv || !T.laid) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = cv.clientWidth, h = cv.clientHeight;
    const bw = Math.round(w * dpr), bh = Math.round(h * dpr);
    if (cv.width !== bw || cv.height !== bh) { cv.width = bw; cv.height = bh; }
    const g = cv.getContext('2d');
    g.setTransform(dpr, 0, 0, dpr, 0, 0);
    g.clearRect(0, 0, w, h);

    // ⚠ Do not just take the root's children. Indo-European's root has THREE — Anatolian,
    // "Classical Indo-European" and a residue — so a lane per child would draw three bars and
    // hide Germanic, Slavic, Italic and Celtic one level below. Split the biggest lane
    // repeatedly until the view has a useful number of them.
    const lanes = storyLanes();
    if (!lanes.length) return;
    T.storyLanes = lanes;
    const root = T.laid.root;
    let recs = root.kids.slice();
    if (!recs.length) recs = [root];
    while (recs.length < 9) {
      const big = recs.reduce((a, b) => (b.kids.length && b.leaves > (a ? a.leaves : 0) ? b : a), null);
      if (!big || recs.length - 1 + big.kids.length > 18) break;
      recs = recs.filter(r => r !== big).concat(big.kids);
    }


    const YMIN = -2000, YMAX = 2050;
    const padL = 152, padR = 92, top = 44;
    const X = y => padL + (Math.max(YMIN, Math.min(YMAX, y)) - YMIN) / (YMAX - YMIN) * (w - padL - padR);
    const laneH = Math.min(46, Math.max(20, (h - top - 40) / lanes.length));

    // era rules
    g.font = '10px ' + SANS;
    for (const yr of [-2000, -1500, -1000, -500, 0, 500, 1000, 1500, 2000]) {
      const x = X(yr);
      g.strokeStyle = yr === 0 ? 'rgba(60,52,42,.28)' : 'rgba(60,52,42,.11)';
      g.beginPath(); g.moveTo(x, top - 14); g.lineTo(x, top + lanes.length * laneH); g.stroke();
      g.fillStyle = 'rgba(120,112,102,.9)';
      g.textAlign = 'center';
      g.fillText(yr === 0 ? '1 CE' : (yr < 0 ? (-yr) + ' BCE' : yr), x, top - 22);
    }
    g.textAlign = 'left';

    T.laneY = [];
    lanes.forEach((L, i) => {
      const y = top + i * laneH + laneH / 2;
      T.laneY.push(y);
      if (T.page === L) {                       // the open page is marked on the axis
        g.fillStyle = 'rgba(180,98,47,.09)';
        g.fillRect(0, y - laneH / 2, w, laneH);
      }
      const col = famColour(T.famIdx[T.family]);
      const hue = (i * 47) % 360;
      const band = `hsl(${hue} 42% 46%)`;
      const x0 = L.s.oldest !== null ? X(L.s.oldest) : X(1500);
      const x1 = X(2050);
      // the band: thickness is living languages, and a wholly extinct branch is hollow
      const living = L.s.lang - L.s.ext;
      const th = Math.max(3, Math.min(laneH * 0.56, 3 + 22 * Math.sqrt(living / 400)));
      g.globalAlpha = 0.9;
      if (living === 0) {
        g.strokeStyle = 'rgba(120,112,102,.75)'; g.lineWidth = 1.4;
        g.strokeRect(x0, y - th / 2, Math.max(6, X(L.s.oldest !== null ? 400 : 1600) - x0), th);
      } else {
        const grad = g.createLinearGradient(x0, 0, x1, 0);
        grad.addColorStop(0, band);
        grad.addColorStop(1, `hsl(${hue} 52% 62%)`);
        g.fillStyle = grad;
        g.fillRect(x0, y - th / 2, x1 - x0, th);
      }
      g.globalAlpha = 1;

      // every attested language in this branch, as a mark on the axis
      (function marks(r) {
        const n = r.n;
        if (!r.kids.length && n.y) {
          const mx = X(n.y);
          g.beginPath(); g.arc(mx, y, (n.a || 0) >= 6 ? 3.4 : 4.2, 0, 6.2832);
          if ((n.a || 0) >= 6) { g.strokeStyle = 'rgba(50,44,38,.8)'; g.lineWidth = 1.2; g.stroke(); }
          else { g.fillStyle = '#2a2622'; g.fill(); }
        }
        r.kids.forEach(marks);
      })(L.rec);

      // the branch's oldest written member, named on the axis
      if (L.s.oldestN) {
        g.font = '11px ' + SERIF;
        g.fillStyle = 'rgba(60,52,42,.82)';
        g.textAlign = 'right';
        g.fillText(L.s.oldestN.n, X(L.s.oldest) - 8, y);
        g.textAlign = 'left';
      }
      g.font = '600 12px ' + SANS;
      g.fillStyle = '#20242a';
      g.fillText(L.rec.n.n, 8, y - 4);
      g.font = '10px ' + SANS;
      g.fillStyle = 'rgba(120,112,102,.95)';
      g.fillText(living + ' living · ' + L.s.ext + ' extinct', 8, y + 9);
    });

    g.font = '10.5px ' + SANS;
    g.fillStyle = 'rgba(120,112,102,.95)';
    g.fillText('Horizontal position is when a language was first WRITTEN DOWN, not when it ' +
      'split — we have attestation dates, not divergence dates. Bar thickness is living ' +
      'languages; hollow bars are branches with no living speakers.',
      8, top + lanes.length * laneH + 24);
  }
  T.drawStory = drawStory;

  /** The branches the story shows, chosen once so the drawing and the clicks agree. */
  function storyLanes() {
    const root = T.laid.root;
    let recs = root.kids.slice();
    if (!recs.length) recs = [root];
    while (recs.length < 9) {
      const big = recs.reduce((a, b) => (b.kids.length && b.leaves > (a ? a.leaves : 0) ? b : a), null);
      if (!big || recs.length - 1 + big.kids.length > 18) break;
      recs = recs.filter(r => r !== big).concat(big.kids);
    }
    return recs.map(k => ({ rec: k, s: summarise(k) }))
      .filter(l => l.s.lang > 0)
      .sort((a, b) => (a.s.oldest === null ? 1 : b.s.oldest === null ? -1 : a.s.oldest - b.s.oldest));
  }

  /** The story's opening page: what this family is, before any branch is opened. */
  function storyTitle() {
    const f = T.index.families.find(x => x.g === T.family);
    if (!f) return;
    const lanes = storyLanes();
    const oldest = lanes.filter(l => l.s.oldest !== null)
      .sort((a, b) => a.s.oldest - b.s.oldest)[0];
    const dead = lanes.filter(l => l.s.lang - l.s.ext === 0);
    let h = '<div class="exkicker">the story of a family</div>' +
      '<h2 class="exname" style="font-size:32px">' + esc(f.n) + '</h2>' +
      '<div class="exalt"><span>' + lanes.length + ' branches · read left to right, ' +
      'oldest writing first · click a branch to open its page</span></div>';
    if (f.age) h += '<p class="exdesc">Its root is dated to roughly <b>' +
      f.age.toLocaleString() + ' years</b> ago. Everything below is descended from one ' +
      'community of speakers at about that depth.</p>';
    if (oldest) h += '<p class="exdesc">The first of its languages to be written down was ' +
      '<b>' + esc(oldest.s.oldestN.n) + '</b>, in ' + (oldest.s.oldest < 0 ?
      (-oldest.s.oldest) + ' BCE' : oldest.s.oldest + ' CE') + ' — the branch ' +
      esc(oldest.rec.n.n) + '.</p>';
    if (dead.length) h += '<p class="exdesc"><b>' + dead.length + ' of these branches have ' +
      'no living speakers at all.</b> They are drawn hollow: ' +
      dead.map(d => esc(d.rec.n.n)).join(', ') + '.</p>';
    h += '<p class="exfine">Horizontal position is when a language was first written down, ' +
      'not when it split from its sisters. Those are different kinds of date and only the ' +
      'first one exists for most of these languages.</p>';
    setExhibit(h);
    $('#exhibit').classList.remove('empty');
  }

  /** A page of the storybook: one branch, with its objects and its oldest voice. */
  function storyPage(L) {
    const A = window.APP, s2 = L.s, n = L.rec.n;
    const living = s2.lang - s2.ext;
    let h = '<div class="exkicker">' + esc(T.index.families.find(x => x.g === T.family).n) +
      ' · a branch</div><h2 class="exname" style="font-size:31px">' + esc(n.n) + '</h2>';
    h += '<div class="exalt"><span>' + living + ' living · ' + s2.ext + ' extinct' +
      (s2.oldest !== null ? ' · first written ' + (s2.oldest < 0 ? (-s2.oldest) + ' BCE'
        : s2.oldest + ' CE') : ' · never written') + '</span></div>';
    // Authored branch prose first, then Glottolog's own if it says anything, then the composed
    // floor. "branch of the Indo-European language family" now fails substantiveD and falls
    // through, which is the whole point of tightening it.
    const bt = A.families && A.families.branch_text && A.families.branch_text[n.g];
    if (bt) h += '<p class="exstory" style="font-size:14px">' + emph(esc(bt)) + '</p>';
    else if (substantiveD(n.d)) h += '<p class="exdesc">' + esc(n.d) + '</p>';
    else {
      const bc0 = A.descr && A.descr.branches && A.descr.branches[n.g];
      if (bc0) h += '<p class="exdesc excomp">' + esc(bc0) + '</p>';
    }
    const CL = A.families && A.families.clusters_by_node && A.families.clusters_by_node[n.g];
    if (living === 0) h += '<p class="exdesc"><b>Nobody speaks any of them.</b></p>';

    // the members of this branch that the museum actually has something to show for
    const rich = [];
    (function w(r) {
      const m = r.n;
      if (!r.kids.length) {
        const has = (A.notable && A.notable.by_glottocode[m.g] ? 2 : 0) +
                    Math.min(galOf(m.g).length, 2) +
                    (A.texts && A.texts.by_glottocode[m.g] ? 1 : 0);
        if (has) rich.push([has, m]);
      }
      r.kids.forEach(w);
    })(fullRec(n));
    rich.sort((a, b) => b[0] - a[0]);

    for (const [, m] of rich.slice(0, 3)) {
      const gal = galOf(m.g)[0];
      const story = A.notable && A.notable.by_glottocode[m.g];
      const tx = A.texts && A.texts.by_glottocode[m.g];
      h += '<h3>' + esc(m.au && canRender(m.au[0]) ? m.au[0] + ' · ' + m.n : m.n) + '</h3>';
      if (gal) h += '<figure class="exfig"><button type="button" class="exfigb" data-lb="0" ' +
        'data-lbg="' + esc(m.g) + '" aria-label="See this larger"><img src="' +
        window.V('img/gallery/' + gal.file) + '" alt="' + esc(gal.subject) +
        '" loading="lazy"></button><figcaption>' + esc(objTitle(gal)) +
        '</figcaption></figure>';
      if (story) h += '<p class="exstory" style="font-size:14px">' + esc(story) + '</p>';
      if (tx && tx.b && tx.b.length) {
        const b = tx.b[tx.b.length - 1];
        h += '<blockquote class="exquote" lang="' + esc(tx.l) + '" dir="' + esc(tx.d) + '">' +
          esc(b[1].slice(0, 320)) + '</blockquote>';
      }
    }
    if (!rich.length) h += '<p class="exfine">Nothing in this branch has a recorded text or ' +
      'an object yet. That is the next pass of the enrichment loop, not a statement about ' +
      'the languages.</p>';
    setExhibit(h);
    $('#exhibit').classList.remove('empty');
  }

  function wire() {
    $('#vStory').addEventListener('click', () => {
      T.story = !T.story;
      $('#vStory').classList.toggle('on', T.story);
      // A card from the tree has nothing to do with the story, and leaving it there made the
      // story read as a dead backdrop behind someone else's exhibit.
      T.sel = null;
      T.page = null;
      if (T.story) {
        storyTitle();
      } else {
        setExhibit('<p class="exempty">Choose a language from the tree.</p>');
        $('#exhibit').classList.add('empty');
      }
      draw();
    });
    $('#famlist').addEventListener('click', async e => {
      const b = e.target.closest('button'); if (!b) return;
      if (b.dataset.lg) {                       // a language: open its family, then its card
        if (T.family !== b.dataset.fam) await openFamily(b.dataset.fam);
        renderFamilyList(); renderHead();
        showByCode(b.dataset.lg);
        return;
      }
      await openFamily(b.dataset.g); renderFamilyList(); renderHead();
    });
    // One call for "show me this language", used by the family list and by the index view.
    T.openLang = async (gc, fam) => {
      if (T.family !== fam) await openFamily(fam);
      renderFamilyList(); renderHead();
      showByCode(gc);
    };
    $('#famq').addEventListener('focus', loadSearch, { once: true });
    $('#famq').addEventListener('input', () => { loadSearch(); renderFamilyList(); });
    $('#treeq').addEventListener('input', e => {
      T.q = e.target.value; layout();
      const h = $('#treecv').clientHeight || 600;
      T.scale = Math.max(0.16, Math.min(1.6, (h - 70) / (15 * T.laid.leafN)));
      T.oy = 0; draw();
    });
    $('#dial').addEventListener('change', e => { T.showDialects = e.target.checked; layout(); draw(); });

    const cv = $('#treecv');
    cv.addEventListener('wheel', e => {
      if (T.story) return;
      e.preventDefault();
      if (e.ctrlKey || e.metaKey || Math.abs(e.deltaX) > Math.abs(e.deltaY)) {
        T.ox -= e.deltaX; draw(); return;
      }
      const b = cv.getBoundingClientRect(), my = e.clientY - b.top;
      const before = (my - 30 - T.oy) / Math.max(3.2, 15 * T.scale);
      T.scale = Math.max(0.12, Math.min(6, T.scale * Math.exp(-e.deltaY * 0.0022)));
      T.oy = my - 30 - before * Math.max(3.2, 15 * T.scale);
      draw();
    }, { passive: false });

    let drag = null;
    cv.addEventListener('mousedown', e => { drag = [e.clientX, e.clientY, T.ox, T.oy, false]; });
    window.addEventListener('mouseup', e => {
      if (drag && !drag[4] && T.story) {
        const cv2 = $('#treecv'), b3 = cv2.getBoundingClientRect();
        const my = e.clientY - b3.top;
        if (T.laneY && e.clientX >= b3.left && e.clientX <= b3.right) {
          let bi = -1, bd = 1e9;
          T.laneY.forEach((yy, i) => { const d2 = Math.abs(yy - my); if (d2 < bd) { bd = d2; bi = i; } });
          if (bi >= 0 && bd < 26 && T.storyLanes && T.storyLanes[bi]) {
            T.page = T.storyLanes[bi];
            storyPage(T.page);
            drawStory();
          }
        }
        drag = null;
        return;
      }
      if (drag && !drag[4]) {
        const r = hit(e);
        if (r) {
          // ⚠ ONE pick path. A collapse toggle was added to a `click` listener that this
          // canvas does not have — mouseup is what actually fires — so forks opened a
          // leaf-shaped card and never expanded. A fork now both toggles AND explains itself.
          // ⚠ `hasKids` is the WRONG test for "is this a fork". Glottolog gives most
          // languages dialect children, so clicking Swedish opened a branch card and you had
          // to click again to reach the language. A fork is a node whose LEVEL is family
          // (lv 0); a language (lv 1) is always a language, dialects or not.
          if (r.n.lv === 0 && r.hasKids) {
            T.collapsed.has(r.n.g) ? T.collapsed.delete(r.n.g) : T.collapsed.add(r.n.g);
            layout();
            branchExhibit(r.n, T.laid.nodes.find(z => z.n === r.n) || r);
            draw();
          } else {
            exhibit(r.n, r);
          }
        }
      }
      drag = null;
    });
    window.addEventListener('mousemove', e => {
      if (drag && T.story) return;
      if (drag) {
        const dx = e.clientX - drag[0], dy = e.clientY - drag[1];
        if (Math.abs(dx) + Math.abs(dy) > 4) drag[4] = true;
        T.ox = drag[2] + dx; T.oy = drag[3] + dy; draw();
        return;
      }
      if (T.story) return;                    // no tip-hover in the broad-brush view
      const b2 = cv.getBoundingClientRect();
      const inside = e.clientX >= b2.left && e.clientX <= b2.right &&
                     e.clientY >= b2.top && e.clientY <= b2.bottom;
      const r = inside ? hit(e) : null;
      const nn = r ? r.n : null;
      T.hoverXY = r ? [e.clientX - b2.left, e.clientY - b2.top] : null;
      if (nn !== T.hover) {
        T.hover = nn;
        cv.style.cursor = r && !r.kids.length ? 'pointer' : 'grab';
      }
      if (nn || T.hoverXY) draw();
    });
    window.addEventListener('resize', () => { if (T.laid) T.draw(); });
  }

  T.storyPage = storyPage;
  T.show = show;
  T.draw = draw;
  if (document.readyState !== 'loading') wire();
  else document.addEventListener('DOMContentLoaded', wire);
})();
