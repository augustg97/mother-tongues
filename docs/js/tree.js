/* Mother Tongues — the genealogy view.
 *
 * The map answers "where". This answers "where from". WORKING-RULES §13b allows an abstract
 * space only as a SECONDARY view, so this is exactly that: same glottocodes, same family
 * hues as the map, and every leaf flies the map back to the ground it is spoken on.
 *
 * WHAT IS AND IS NOT DRAWN AS TIME. Phlorest gives a dated ROOT for 19 families — one number,
 * the age of the whole family. It does not give us dates for the internal splits. So this
 * draws a cladogram (topology, indented by depth) and states the root age as a fact beside
 * the family name. It does NOT spread the internal nodes along a time axis, because those
 * dates do not exist and drawing them would be invention (rule 10). Two of the nineteen ages
 * come from a tree whose unit had to be inferred, and those are marked.
 *
 * Attestation years are a DIFFERENT kind of date — when a language was first written down,
 * not when it split — and they are never mixed into the same axis.
 */
'use strict';

(function () {
  const $ = s => document.querySelector(s);
  const AESN = ['', 'not endangered', 'threatened', 'shifting', 'moribund',
                'nearly extinct', 'extinct'];

  const T = {
    index: null, family: null, tree: null, open: new Set(), rows: [],
    scroll: 0, hover: -1, famIdx: {}, showDialects: false, q: ''
  };
  window.TREE = T;

  // The same golden-ratio walk the shader uses, so a family is the same colour in both views.
  function familyColour(idx) {
    const i = Math.floor(idx);
    const h = (i * 0.6180339887) % 1;
    const s = 0.55 + 0.25 * ((i * 0.311) % 1);
    const v = 0.80 + 0.20 * ((i * 0.727) % 1);
    const f = n => {
      const k = (n + h * 6) % 6;
      return Math.round(255 * (v - v * s * Math.max(0, Math.min(Math.min(k, 4 - k), 1))));
    };
    return `rgb(${f(5)},${f(3)},${f(1)})`;
  }

  // D10. A canvas cannot warn about a missing typeface, it just draws empty boxes — and a
  // row of boxes is not "the language in its own script", it is a worse lie than the exonym
  // would have been. Where the device has no font for the script, fall back to the reference
  // name in the tree and leave the autonym to the card, which CAN say what is wrong.
  const _fontOK = new Map();
  function canRender(str) {
    if (!str) return false;
    const k = str.slice(0, 12);
    if (_fontOK.has(k)) return _fontOK.get(k);
    let ok = true;
    try {
      if (document.fonts && document.fonts.check) ok = document.fonts.check('13px system-ui', k);
    } catch (e) { ok = true; }
    _fontOK.set(k, ok);
    return ok;
  }

  function famColourFor(gc) {
    const idx = T.famIdx[gc];
    return idx ? familyColour(idx) : '#8fa39c';
  }

  async function loadIndex() {
    if (T.index) return T.index;
    T.index = await fetch(window.V('data/tree/index.json')).then(r => r.json());
    const L = window.APP.langs;
    if (L) for (const r of L.rows) T.famIdx[r[11]] = r[4];
    return T.index;
  }

  async function openFamily(gc) {
    T.tree = await fetch(window.V('data/tree/' + gc + '.json')).then(r => r.json());
    T.family = gc;
    T.open = new Set([gc]);
    // Open the first two levels so the shape of the family is visible immediately rather
    // than as a single unhelpful root row.
    (function seed(n, d) {
      if (d >= 2) return;
      if (n.c) { T.open.add(n.g); n.c.forEach(c => seed(c, d + 1)); }
    })(T.tree, 0);
    T.scroll = 0;
    layout(); draw();
  }

  function layout() {
    const rows = [];
    const q = T.q.toLowerCase();
    (function walk(n, depth) {
      if (!T.showDialects && n.lv === 2) return;
      const match = !q || (n.n || '').toLowerCase().includes(q) ||
        (n.au && n.au[0].toLowerCase().includes(q)) || (n.i || '').includes(q);
      rows.push({ n, depth, match });
      // While searching, descend the WHOLE family regardless of what is expanded — a search
      // that only looks inside the branches you already opened finds nothing, which is what
      // it did: "Hindi" returned zero rows in a family that contains it.
      if (n.c && (q || T.open.has(n.g))) n.c.forEach(c => walk(c, depth + 1));
    })(T.tree, 0);
    if (q) {
      // When searching, keep only matches and the ancestors that lead to them, so the
      // result stays a tree rather than becoming a flat list with no context.
      const keep = new Set();
      rows.forEach((r, i) => {
        if (!r.match) return;
        keep.add(i);
        let d = r.depth;
        for (let j = i - 1; j >= 0 && d > 0; j--) {
          if (rows[j].depth < d) { keep.add(j); d = rows[j].depth; }
        }
      });
      T.rows = rows.filter((_, i) => keep.has(i));
    } else {
      T.rows = rows;
    }
  }

  const ROW = 22;

  function draw() {
    const cv = $('#treecv');
    if (!cv || !T.tree) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = cv.clientWidth, h = cv.clientHeight;
    if (cv.width !== Math.round(w * dpr)) { cv.width = Math.round(w * dpr); cv.height = Math.round(h * dpr); }
    const g = cv.getContext('2d');
    g.setTransform(dpr, 0, 0, dpr, 0, 0);
    g.clearRect(0, 0, w, h);

    const maxScroll = Math.max(0, T.rows.length * ROW - h + 40);
    T.scroll = Math.max(0, Math.min(T.scroll, maxScroll));
    const first = Math.max(0, Math.floor(T.scroll / ROW) - 1);
    const last = Math.min(T.rows.length, first + Math.ceil(h / ROW) + 2);

    g.font = '12px -apple-system,BlinkMacSystemFont,Inter,system-ui,sans-serif';
    g.textBaseline = 'middle';

    // connectors first, so text sits on top
    g.strokeStyle = 'rgba(140,170,160,.26)';
    g.lineWidth = 1;
    for (let i = first; i < last; i++) {
      const r = T.rows[i];
      const y = Math.round(i * ROW - T.scroll + ROW / 2) + 0.5;
      const x = 16 + r.depth * 17;
      if (r.depth > 0) {
        g.beginPath(); g.moveTo(x - 9, y); g.lineTo(x - 2, y); g.stroke();
        // vertical stub up to the parent row
        let p = i - 1;
        while (p >= 0 && T.rows[p].depth >= r.depth) p--;
        if (p >= 0) {
          const py = Math.round(p * ROW - T.scroll + ROW / 2) + 0.5;
          g.beginPath(); g.moveTo(x - 9, py); g.lineTo(x - 9, y); g.stroke();
        }
      }
    }

    for (let i = first; i < last; i++) {
      const r = T.rows[i], n = r.n;
      const y = i * ROW - T.scroll + ROW / 2;
      const x = 16 + r.depth * 17;
      if (i === T.hover) {
        g.fillStyle = 'rgba(111,208,189,.10)';
        g.fillRect(0, y - ROW / 2, w, ROW);
      }
      const isLeaf = !n.c || n.lv === 1;
      const col = famColourFor(T.family);

      if (n.c) {
        g.fillStyle = 'rgba(190,205,200,.75)';
        g.fillText(T.open.has(n.g) ? '▾' : '▸', x - 1, y);
      }
      const dot = x + (n.c ? 13 : 4);
      if (n.lv >= 1) {
        const a = n.a || 0;
        g.beginPath(); g.arc(dot, y, 3.4, 0, 6.2832);
        if (a >= 6) { g.strokeStyle = 'rgba(180,190,186,.85)'; g.lineWidth = 1.2; g.stroke(); }
        else { g.fillStyle = a >= 3 ? '#d9825f' : col; g.fill(); }
      }

      let tx = dot + 10, bits0 = false;
      if (n.au && canRender(n.au[0])) {   // rule 11: the autonym leads here too
        g.fillStyle = '#eef3f1';
        g.font = '12.5px -apple-system,BlinkMacSystemFont,Inter,system-ui,sans-serif';
        g.fillText(n.au[0], tx, y);
        tx += g.measureText(n.au[0]).width + 7;
        g.font = '11.5px -apple-system,BlinkMacSystemFont,Inter,system-ui,sans-serif';
        g.fillStyle = 'rgba(200,214,208,.55)';
        g.fillText(n.n, tx, y);
        tx += g.measureText(n.n).width + 8;
      } else {
        if (n.au) bits0 = true;
        g.font = (n.lv === 0 ? '600 12.5px' : '12px') +
          ' -apple-system,BlinkMacSystemFont,Inter,system-ui,sans-serif';
        g.fillStyle = n.lv === 0 ? '#dfe8e4' : (n.a >= 6 ? 'rgba(196,206,202,.62)' : '#cfdad6');
        g.fillText(n.n, tx, y);
        tx += g.measureText(n.n).width + 8;
      }

      g.font = '10.5px -apple-system,BlinkMacSystemFont,Inter,system-ui,sans-serif';
      const bits = [];
      if (n.c) {
        let k = 0;
        (function cnt(m) { if (m.lv === 1) k++; (m.c || []).forEach(cnt); })(n);
        if (k) bits.push(k + (k === 1 ? ' language' : ' languages'));
      }
      if (bits0) bits.push('autonym needs a font this device lacks');
      if (n.a >= 6) bits.push('extinct');
      else if (n.a >= 3) bits.push(AESN[n.a]);
      if (n.y) bits.push('attested ' + (n.y < 0 ? (-n.y) + ' BCE' : n.y));
      if (window.APP.texts && window.APP.texts.by_glottocode[n.g]) {
        const s = window.APP.texts.by_glottocode[n.g].s;
        if (s) bits.push(s + ' script');
      }
      if (bits.length) {
        g.fillStyle = 'rgba(150,168,161,.72)';
        g.fillText(bits.join(' · '), tx, y);
      }
    }

    // scrollbar
    if (maxScroll > 0) {
      const fh = Math.max(24, h * h / (T.rows.length * ROW));
      const fy = (h - fh) * (T.scroll / maxScroll);
      g.fillStyle = 'rgba(140,170,160,.22)';
      g.fillRect(w - 5, fy, 3, fh);
    }
  }

  function rowAt(ev) {
    const cv = $('#treecv'), r = cv.getBoundingClientRect();
    const i = Math.floor((ev.clientY - r.top + T.scroll) / ROW);
    return (i >= 0 && i < T.rows.length) ? i : -1;
  }

  function renderFamilyList() {
    const q = $('#famq').value.toLowerCase();
    const fams = T.index.families.filter(f => !q || f.n.toLowerCase().includes(q));
    const btn = f =>
      '<button data-g="' + f.g + '"' + (f.g === T.family ? ' class="on"' : '') + '>' +
      '<span class="sw" style="background:' + (f.pseudo ? '#4a5450' : famColourFor(f.g)) + '"></span>' +
      '<span class="fn">' + f.n + '</span>' +
      '<span class="fc">' + (f.isolate ? 'isolate' : f.lang) + '</span></button>';
    // Real families first, then isolates, then Glottolog's pseudo-families under a heading
    // that says they are not genealogical units — otherwise "Sign Language" and "Pidgin"
    // read as branches of the human family tree, which they are not.
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
    if (f.extinct) bits.push('<b style="color:#c9d2ce">' + f.extinct + ' extinct</b>');
    if (f.endangered) bits.push('<b style="color:#d9825f">' + f.endangered + ' endangered</b>');
    let age = '';
    if (f.age) {
      age = '<div class="agebar">Root age <b>≈ ' + f.age.toLocaleString() + ' years</b>' +
        (f.ageExplicit ? '' : ' <i>(branch-length unit inferred — treat with caution)</i>') +
        ' · dated phylogeny, Phlorest. <span style="opacity:.7">The internal splits below are ' +
        '<b>not</b> dated: this is a classification, not a timeline.</span></div>';
    } else if (!f.isolate) {
      age = '<div class="agebar" style="opacity:.72">No dated phylogeny exists for this ' +
        'family, so it has topology but no age. 19 of 429 families are dated.</div>';
    }
    $('#treehead').innerHTML = '<h2>' + f.n + '</h2><div class="sub">' +
      bits.join(' · ') + (f.ma ? ' · mostly ' + f.ma : '') + '</div>' + age;
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
    $('#treeq').addEventListener('input', e => { T.q = e.target.value; layout(); T.scroll = 0; draw(); });
    $('#dial').addEventListener('change', e => { T.showDialects = e.target.checked; layout(); draw(); });
    const cv = $('#treecv');
    cv.addEventListener('wheel', e => { e.preventDefault(); T.scroll += e.deltaY; draw(); }, { passive: false });
    cv.addEventListener('mousemove', e => { const i = rowAt(e); if (i !== T.hover) { T.hover = i; draw(); } });
    cv.addEventListener('mouseleave', () => { T.hover = -1; draw(); });
    cv.addEventListener('click', e => {
      const i = rowAt(e); if (i < 0) return;
      const n = T.rows[i].n;
      if (n.c) {
        T.open.has(n.g) ? T.open.delete(n.g) : T.open.add(n.g);
        layout(); draw();
        return;
      }
      if (n.lv >= 1) window.APP.showCardFor(n.g, n.p);
    });
    window.addEventListener('resize', () => { if (T.tree) draw(); });
  }

  T.show = show;
  T.draw = draw;
  if (document.readyState !== 'loading') wire();
  else document.addEventListener('DOMContentLoaded', wire);
})();
