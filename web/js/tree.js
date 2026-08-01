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
    laid: null, W: 0, H: 0
  };
  window.TREE = T;

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
      const kids = (n.c || []).map(c => walk(c, depth + 1)).filter(Boolean);
      const rec = { n, depth, kids, y: 0, leaves: 0, living: 0 };
      if (!kids.length) {
        rec.y = leafN++;
        rec.leaves = 1;
        rec.living = (n.a || 0) >= 6 ? 0 : 1;
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

  /* ---- draw ---- */
  function draw() {
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
        const tw = 0.7 + 5.2 * Math.sqrt(k.living / L.leafN);
        g.lineWidth = Math.max(0.6, tw);
        g.strokeStyle = k.living === 0 ? 'rgba(120,112,102,.34)' : col;
        g.globalAlpha = k.living === 0 ? 1 : 0.55;
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

      if (T.sel === n) {
        g.beginPath(); g.arc(x, y, 8, 0, 6.2832);
        g.strokeStyle = '#b4622f'; g.lineWidth = 1.4; g.stroke();
      }

      if (!labelled) continue;
      const need = fs * 0.95;
      if (leaf) { if (y - lastLeafY < need) continue; lastLeafY = y; }
      else { if (y - lastNodeY < need) continue; lastNodeY = y; }
      let tx = x + 8;
      if (leaf) {
        const au = n.au && canRender(n.au[0]) ? n.au[0] : null;
        g.font = fs.toFixed(1) + 'px ' + SERIF;
        g.fillStyle = a >= 6 ? 'rgba(96,90,82,.85)' : '#20242a';
        const main = au || n.n;
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
        const ny = y - Math.min(9, fs * 0.72);
        g.font = '600 ' + Math.max(9, fs * 0.82).toFixed(1) + 'px ' + SANS;
        g.fillStyle = 'rgba(58,54,50,.9)';
        g.fillText(n.n, tx - 4, ny);
        g.font = Math.max(8.5, fs * 0.72).toFixed(1) + 'px ' + SANS;
        g.fillStyle = 'rgba(130,122,112,.8)';
        g.fillText('  ' + r.leaves, tx - 4 + g.measureText(n.n).width + 4, ny);
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
  function exhibit(n) {
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

    if (n.p) {
      h += '<div class="exmapwrap"><canvas class="exmapcv"></canvas>' +
        '<div class="exmapcap">' +
        esc(n.p[1].toFixed(2)) + (n.p[1] >= 0 ? '°N ' : '°S ') +
        esc(Math.abs(n.p[0]).toFixed(2)) + (n.p[0] >= 0 ? '°E' : '°W') +
        ' · click to open the ground</div></div>';
    }
    if (n.d) h += '<p class="exdesc">' + esc(n.d) + '</p>';

    const facts = [];
    if (n.a) facts.push(['vitality', AESN[n.a]]);
    if (n.y) facts.push(['first attested', n.y < 0 ? (-n.y) + ' BCE' : String(n.y)]);
    if (n.sp) facts.push(['speakers', n.sp[0].toLocaleString() + '  ·  as of ' + n.sp[1]]);
    if (n.cc) facts.push(['countries', n.cc]);
    if (n.i) facts.push(['ISO 639-3', n.i]);
    facts.push(['glottocode', n.g]);
    if (tx && tx.s) facts.push(['script', tx.s + (tx.d === 'rtl' ? ', right to left' : '')]);
    h += '<dl class="exfacts">' + facts.map(f =>
      '<dt>' + esc(f[0]) + '</dt><dd>' + esc(f[1]) + '</dd>').join('') + '</dl>';

    if (wd) {
      const order = ['water', 'fire', 'sun', 'moon', 'star', 'stone', 'mountain', 'tree',
                     'leaf', 'blood', 'bone', 'hand', 'eye', 'ear', 'nose', 'tooth',
                     'tongue', 'skin', 'name', 'person', 'fish', 'bird', 'dog', 'night',
                     'die', 'come', 'see', 'hear', 'drink', 'new', 'full', 'one', 'two'];
      const have = order.filter(k => wd[k]);
      h += '<h3>Words</h3><div class="words">' + have.map(k =>
        '<div><b>' + esc(wd[k]) + '</b><span>' + esc(k) + '</span></div>').join('') + '</div>';
      h += '<p class="exfine">' + have.length + ' of ASJP\'s core 40, in <b>ASJPcode</b> — a ' +
        'coarse ASCII transcription built for comparison across thousands of languages, not ' +
        'this language\'s own orthography. ASJP (Wichmann, Holman &amp; Brown, eds.).</p>';
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

    $('#exhibit').innerHTML = h;
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
      requestAnimationFrame(paint);
      setTimeout(paint, 900);          // again once nearer tiles have streamed in
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
    $('#famlist').innerHTML =
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
    $('#exhibit').innerHTML = '<p class="exempty">Choose a language from the tree.</p>';
    $('#exhibit').classList.add('empty');
    layout();
    // Fit the whole family in view, then let the visitor zoom in for names.
    const cv = $('#treecv');
    const h = cv.clientHeight || 600;
    T.scale = Math.max(0.16, Math.min(1.6, (h - 70) / (15 * T.laid.leafN)));
    T.ox = 0; T.oy = 0;
    draw();
  }

  async function show() {
    await loadIndex();
    renderFamilyList();
    if (!T.family) await openFamily((T.index.families.find(f => !f.pseudo) || T.index.families[0]).g);
    else { layout(); draw(); }
    renderHead();
  }

  function wire() {
    $('#famlist').addEventListener('click', async e => {
      const b = e.target.closest('button'); if (!b) return;
      await openFamily(b.dataset.g); renderFamilyList(); renderHead();
    });
    $('#famq').addEventListener('input', renderFamilyList);
    $('#treeq').addEventListener('input', e => {
      T.q = e.target.value; layout();
      const h = $('#treecv').clientHeight || 600;
      T.scale = Math.max(0.16, Math.min(1.6, (h - 70) / (15 * T.laid.leafN)));
      T.oy = 0; draw();
    });
    $('#dial').addEventListener('change', e => { T.showDialects = e.target.checked; layout(); draw(); });

    const cv = $('#treecv');
    cv.addEventListener('wheel', e => {
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
      if (drag && !drag[4]) { const r = hit(e); if (r && !r.kids.length) exhibit(r.n); }
      drag = null;
    });
    window.addEventListener('mousemove', e => {
      if (drag) {
        const dx = e.clientX - drag[0], dy = e.clientY - drag[1];
        if (Math.abs(dx) + Math.abs(dy) > 4) drag[4] = true;
        T.ox = drag[2] + dx; T.oy = drag[3] + dy; draw();
        return;
      }
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
    window.addEventListener('resize', () => { if (T.laid) draw(); });
  }

  T.show = show;
  T.draw = draw;
  if (document.readyState !== 'loading') wire();
  else document.addEventListener('DOMContentLoaded', wire);
})();
