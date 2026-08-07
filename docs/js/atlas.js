/* INDEX — the whole atlas as one image.
 *
 * WHY. The ground shows where languages are and the genealogy shows how they are related, and
 * neither answers "how many, and how unevenly". You can open 7,672 cards one at a time and never
 * see the shape of the collection. This view is the collection: one cell per language, grouped
 * into its family, on one screen.
 *
 * TWO THINGS IT IS FOR, and they are switches rather than separate views, because the whole
 * argument is that the same 7,672 languages look completely different depending on what you
 * measure them by:
 *
 *   area   ONE CELL EACH  every language the same size — the atlas as a census
 *          BY SPEAKERS    area is people, and 6,485 languages vanish because nobody has
 *                         published a count for them, while eight carry half the world
 *   colour BY FAMILY      the same hue the family has on the ground and in the tree
 *          BY VITALITY    the AES scale, so the endangerment is a shape and not a number
 *
 * The layout is a squarified treemap (Bruls, Huizing & van Wijk 2000) at two levels: families
 * within the frame, languages within their family. Cells are laid out once per resize and kept,
 * so hover is a lookup and not a re-layout.
 */
(() => {
  const $ = s => document.querySelector(s);

  const IX = {
    built: false, ready: false, cells: [], fams: [],
    area: 'count', colour: 'family', hot: null, W: 0, H: 0, waits: 0,
  };
  window.IX = IX;

  const SANS = '"Inter", "Helvetica Neue", system-ui, sans-serif';
  const SERIF = '"Spectral", "Iowan Old Style", Georgia, serif';

  const AES = ['not assessed', 'not endangered', 'threatened', 'shifting',
               'moribund', 'nearly extinct', 'extinct'];
  // A ramp from living green through the fires to stone. Extinct is deliberately NOT the hottest
  // colour: a language that is gone is not in danger, it is finished, and reading it as the
  // extreme of an alarm scale misstates what happened to it.
  const AESCOL = ['#c3bcb2', '#5f8168', '#8d9455', '#c39538', '#bd6f30', '#a2452b', '#6e665c'];

  // THE SAME HUE, LESS SHOUTING. The tree and the ground show one family's colour at a time and
  // can afford full chroma. Here 421 of them are on screen together, and at the tree's
  // saturation the page stops being a cream-paper atlas and becomes a pitch deck. Same
  // golden-ratio hue — a family is recognisably itself across all three views — laid down at
  // the weight of a wash rather than a marker pen.
  function famColour(i) {
    const n = Math.floor(i || 0);
    const h = (n * 0.6180339887) % 1;
    const s = 0.30 + 0.17 * ((n * 0.311) % 1);
    const v = 0.80 + 0.11 * ((n * 0.727) % 1);
    const f = k0 => {
      const k = (k0 + h * 6) % 6;
      return v - v * s * Math.max(0, Math.min(Math.min(k, 4 - k), 1));
    };
    return `rgb(${Math.round(255 * f(5))},${Math.round(255 * f(3))},${Math.round(255 * f(1))})`;
  }

  /* ---- squarified treemap ------------------------------------------------------------- */
  function worst(row, len, scale) {
    let s = 0, mx = 0, mn = Infinity;
    for (const r of row) { s += r.w; if (r.w > mx) mx = r.w; if (r.w < mn) mn = r.w; }
    s *= scale; mx *= scale; mn *= scale;
    if (s <= 0 || mn <= 0) return Infinity;
    return Math.max(len * len * mx / (s * s), (s * s) / (len * len * mn));
  }

  // items: [{w, ...}] — returns the same objects with x/y/w/h set as {x,y,dw,dh}.
  function squarify(items, x, y, w, h, out) {
    const list = items.filter(i => i.w > 0).sort((a, b) => b.w - a.w);
    let total = 0; for (const i of list) total += i.w;
    let i = 0;
    while (i < list.length && w > 0.4 && h > 0.4 && total > 0) {
      const scale = (w * h) / total;
      const vertical = w >= h;
      const len = vertical ? h : w;
      let row = [], best = Infinity, j = i;
      while (j < list.length) {
        const cand = row.concat([list[j]]);
        const wr = worst(cand, len, scale);
        if (row.length && wr > best) break;
        row = cand; best = wr; j++;
      }
      let rowW = 0; for (const r of row) rowW += r.w;
      const thick = (rowW * scale) / len;
      let off = 0;
      for (const it of row) {
        const side = (it.w * scale) / thick;
        if (vertical) out.push({ it, x, y: y + off, dw: thick, dh: side });
        else out.push({ it, x: x + off, y, dw: side, dh: thick });
        off += side;
      }
      if (vertical) { x += thick; w -= thick; } else { y += thick; h -= thick; }
      total -= rowW;
      i = j;
    }
  }

  /* ---- layout ------------------------------------------------------------------------- */
  function build() {
    const A = window.APP;
    if (!A || !A.langs) return false;
    const F = {}; A.langs.fields.forEach((k, i) => (F[k] = i));
    const famNames = (A.families && A.families.by_glottocode) || {};

    const byFam = new Map();
    for (const r of A.langs.rows) {
      const fid = r[F.famid];
      let f = byFam.get(fid);
      if (!f) { f = { g: fid, ci: r[F.fam], langs: [], w: 0 }; byFam.set(fid, f); }
      f.langs.push({
        code: r[F.code], n: r[F.name], ci: r[F.fam], aes: r[F.aes] || 0,
        sp: (r[F.sp] && r[F.sp][0]) || 0, spy: (r[F.sp] && r[F.sp][1]) || '',
        au: (r[F.autonyms] && r[F.autonyms][0] && r[F.autonyms][0][0]) || '',
        fam: fid,
      });
    }
    for (const f of byFam.values()) {
      f.name = (famNames[f.g] && famNames[f.g].n) || f.g;
      f.count = f.langs.length;
    }
    IX.fams = [...byFam.values()];
    IX.total = A.langs.rows.length;
    IX.counted = IX.fams.reduce((a, f) => a + f.langs.filter(l => l.sp > 0).length, 0);
    IX.people = IX.fams.reduce((a, f) => a + f.langs.reduce((b, l) => b + l.sp, 0), 0);
    IX.built = true;
    return true;
  }

  function layout() {
    const cv = $('#ixcv');
    if (!cv || !IX.built) return;
    const w = cv.clientWidth, h = cv.clientHeight;
    // ⚠ A ZERO-SIZED CANVAS IS NOT A REASON TO GIVE UP. Measuring the canvas in the same task
    // that unhid its container can return 0×0, and the old code simply returned — leaving no
    // cells, a legend of nothing and a caption reading "0 of the languages drawn here". Come
    // back next frame instead; the view will have a size by then.
    if (!w || !h) {
      if (IX.waits++ > 20) return;              // bounded: a pane that never gets a size is not
      requestAnimationFrame(() => {             // a reason to burn frames forever
        if (!$('#indexview').classList.contains('hidden')) IX.show();
      });
      return;
    }
    IX.waits = 0;
    IX.W = w; IX.H = h;
    const byPeople = IX.area === 'sp';

    for (const f of IX.fams) {
      f.w = byPeople ? f.langs.reduce((a, l) => a + l.sp, 0) : f.count;
    }
    const boxes = [];
    squarify(IX.fams, 0, 0, w, h, boxes);

    const cells = [];
    for (const b of boxes) {
      const f = b.it;
      // The family keeps a hairline of its own, so a one-language family is still a family
      // rather than a stray cell, and its name has somewhere to sit.
      f.box = b;
      const px = b.x + 1, py = b.y + 1, pw = Math.max(0, b.dw - 2), ph = Math.max(0, b.dh - 2);
      if (pw < 0.6 || ph < 0.6) continue;
      if (byPeople) {
        const ls = f.langs.map(l => ({ w: l.sp, l }));
        const out = [];
        squarify(ls, px, py, pw, ph, out);
        for (const o of out) cells.push({ l: o.it.l, x: o.x, y: o.y, w: o.dw, h: o.dh, f });
      } else {
        // Equal cells: a grid whose column count is chosen to keep the cells near square.
        const n = f.count;
        const cols = Math.max(1, Math.round(Math.sqrt(n * pw / Math.max(0.001, ph))) || 1);
        const rows = Math.ceil(n / cols);
        const cw = pw / cols, ch = ph / rows;
        const last = n % cols || cols;
        f.langs.forEach((l, i) => {
          const row = Math.floor(i / cols), col = i % cols;
          // The final row is centred, so a family ends in a short line rather than a ragged
          // white sliver that reads as missing data.
          const inset = (row === rows - 1) ? (cols - last) * cw / 2 : 0;
          cells.push({ l, x: px + inset + col * cw, y: py + row * ch, w: cw, h: ch, f });
        });
      }
    }
    IX.cells = cells;
    IX.ready = true;
  }

  /* ---- draw ---------------------------------------------------------------------------- */
  function colourOf(c) {
    return IX.colour === 'aes' ? AESCOL[c.l.aes] || AESCOL[0] : famColour(c.l.ci);
  }

  function draw() {
    const cv = $('#ixcv');
    if (!cv || !IX.ready) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = cv.clientWidth, h = cv.clientHeight;
    if (!w || !h) return;
    const bw = Math.round(w * dpr), bh = Math.round(h * dpr);
    if (cv.width !== bw || cv.height !== bh) { cv.width = bw; cv.height = bh; }
    const g = cv.getContext('2d');
    g.setTransform(dpr, 0, 0, dpr, 0, 0);
    g.clearRect(0, 0, w, h);

    // cells
    for (const c of IX.cells) {
      if (c.w < 0.35 || c.h < 0.35) continue;
      g.fillStyle = colourOf(c);
      // A gap only where there is room for one. Below about 3px the gaps eat the cell and the
      // block turns to paper; a dense family should read as dense, not as empty.
      const gap = Math.min(1, Math.min(c.w, c.h) * 0.16);
      g.fillRect(c.x, c.y, Math.max(0.35, c.w - gap), Math.max(0.35, c.h - gap));
    }

    // family frames and names
    g.textBaseline = 'top';
    for (const f of IX.fams) {
      const b = f.box;
      if (!b || b.dw < 2 || b.dh < 2) continue;
      g.strokeStyle = 'rgba(58,52,44,.16)';
      g.lineWidth = 1;
      g.strokeRect(b.x + 0.5, b.y + 0.5, b.dw - 1, b.dh - 1);
      const area = b.dw * b.dh;
      if (area < 2600 || b.dw < 54) continue;
      let fs = Math.max(9.5, Math.min(15, Math.sqrt(area) * 0.14));
      g.font = '600 ' + fs.toFixed(1) + 'px ' + SANS;
      // Shrink to fit before giving up. Nuclear Trans New Guinea is 317 languages and the
      // sixth-largest block on the page, and it went unnamed purely because its name is long.
      while (g.measureText(f.name).width > b.dw - 10 && fs > 8.6) {
        fs -= 0.5; g.font = '600 ' + fs.toFixed(1) + 'px ' + SANS;
      }
      if (g.measureText(f.name).width > b.dw - 10) continue;
      // A plate behind the name, because the name has to read over whatever hue the family is.
      g.fillStyle = 'rgba(250,247,241,.74)';
      g.fillRect(b.x + 3, b.y + 3, g.measureText(f.name).width + 8, fs + 6);
      g.fillStyle = 'rgba(40,36,32,.9)';
      g.fillText(f.name, b.x + 7, b.y + 6);
      if (area > 12000) {
        const sub = IX.area === 'sp'
          ? fmt(f.langs.reduce((a, l) => a + l.sp, 0)) + ' speakers'
          : f.count.toLocaleString() + ' language' + (f.count === 1 ? '' : 's');
        g.font = (fs * 0.78).toFixed(1) + 'px ' + SANS;
        g.fillStyle = 'rgba(250,247,241,.7)';
        g.fillRect(b.x + 3, b.y + fs + 9, g.measureText(sub).width + 8, fs * 0.78 + 5);
        g.fillStyle = 'rgba(70,64,58,.85)';
        g.fillText(sub, b.x + 7, b.y + fs + 11);
      }
    }

    // the cell under the cursor
    if (IX.hot) {
      const c = IX.hot;
      g.strokeStyle = '#20242a'; g.lineWidth = 1.6;
      g.strokeRect(c.x - 0.8, c.y - 0.8, Math.max(2, c.w) + 1.6, Math.max(2, c.h) + 1.6);
    }
    g.textBaseline = 'alphabetic';
  }

  function fmt(n) {
    if (!n) return 'none published';
    if (n >= 1e9) return (n / 1e9).toFixed(2) + ' bn';
    if (n >= 1e6) return (n / 1e6).toFixed(n >= 1e7 ? 0 : 1) + ' m';
    if (n >= 1e3) return Math.round(n / 1e3) + ' k';
    return String(n);
  }

  /* ---- head, legend, tooltip ------------------------------------------------------------ */
  function renderHead() {
    const byPeople = IX.area === 'sp';
    const missing = IX.total - IX.counted;
    let cap = byPeople
      ? 'Area is <b>people</b>. Only <b>' + IX.counted.toLocaleString() + '</b> of ' +
        IX.total.toLocaleString() + ' languages have a published count of living speakers, so ' +
        missing.toLocaleString() + ' of them are not drawn at all — that absence is the ' +
        'commonest fact about a language. Among the counted, <b>eight</b> carry half of ' +
        fmt(IX.people) + '.'
      : 'Area is <b>one cell per language</b>, every one the same size, grouped into its ' +
        'family. This is the atlas as a census: <b>' + IX.total.toLocaleString() +
        '</b> languages in <b>' + IX.fams.length + '</b> families and isolates.';
    // Only when there is something laid out. The counts describe the cells on screen, and with
    // no cells the sentence reads "0 of the languages drawn here", which is true and useless.
    if (IX.colour === 'aes' && IX.cells.length) {
      const gone = IX.cells.filter(c => c.l.aes >= 5).length;
      const safe = IX.cells.filter(c => c.l.aes === 1).length;
      cap += ' Colour is the <b>AES vitality scale</b>: of the <b>' +
        IX.cells.length.toLocaleString() + '</b> drawn here, <b>' + gone.toLocaleString() +
        '</b> are nearly extinct or already gone and <b>' + safe.toLocaleString() +
        '</b> are assessed as not endangered.';
    }
    $('#ixcap').innerHTML = cap;

    // The legend follows the area mode. Ranking families by language count under a treemap
    // whose areas are people would name the blocks in the wrong order.
    const rank = byPeople
      ? (a, b) => (b.langs.reduce((s, l) => s + l.sp, 0)) - (a.langs.reduce((s, l) => s + l.sp, 0))
      : (a, b) => b.count - a.count;
    const val = f => byPeople ? fmt(f.langs.reduce((s, l) => s + l.sp, 0))
                              : f.count.toLocaleString();
    $('#ixlegend').innerHTML = IX.colour === 'aes'
      ? AES.map((a, i) => {
          const n = IX.cells.filter(c => c.l.aes === i).length;
          return !n ? '' : '<span class="ixk"><i style="background:' + AESCOL[i] + '"></i>' +
            a + ' <b>' + n.toLocaleString() + '</b></span>';
        }).join('')
      : IX.fams.slice().sort(rank).slice(0, 12)
          .map(f => '<span class="ixk"><i style="background:' + famColour(f.ci) + '"></i>' +
            f.name + ' <b>' + val(f) + '</b></span>').join('') +
        '<span class="ixk quiet">' + (IX.fams.length - 12) + ' more families and isolates</span>';

    for (const [id, on] of [['ixCount', IX.area === 'count'], ['ixSp', IX.area === 'sp'],
                            ['ixFam', IX.colour === 'family'], ['ixAes', IX.colour === 'aes']]) {
      const e = $('#' + id); if (e) e.classList.toggle('on', on);
    }
  }

  function hit(x, y) {
    for (const c of IX.cells) {
      if (x >= c.x && x < c.x + c.w && y >= c.y && y < c.y + c.h) return c;
    }
    return null;
  }

  function tip(c, ev) {
    const t = $('#ixtip');
    if (!c) { t.classList.add('hidden'); return; }
    const l = c.l;
    t.innerHTML = '<b>' + (l.au || l.n) + '</b>' + (l.au ? '<i>' + l.n + '</i>' : '') +
      '<span>' + c.f.name + '</span>' +
      '<span>' + (l.sp ? fmt(l.sp) + ' speakers' + (l.spy ? ' · ' + l.spy : '')
                       : 'no published speaker count') + '</span>' +
      '<span class="a" style="color:' + AESCOL[l.aes] + '">' + AES[l.aes] + '</span>';
    t.classList.remove('hidden');
    // Measure the tip AFTER writing it. A fixed 110px guess let a four-line tip run off the
    // bottom and sit over the legend; an autonym in a tall script makes it taller still.
    const b = $('#indexview').getBoundingClientRect();
    const tw = t.offsetWidth, th = t.offsetHeight;
    let x = ev.clientX - b.left + 15, y = ev.clientY - b.top + 15;
    if (x + tw + 8 > b.width) x = ev.clientX - b.left - tw - 15;
    if (y + th + 8 > b.height) y = ev.clientY - b.top - th - 15;
    t.style.left = Math.max(4, x) + 'px'; t.style.top = Math.max(4, y) + 'px';
  }

  /* ---- wiring ---------------------------------------------------------------------------- */
  IX.show = () => {
    if (!IX.built && !build()) return;
    layout(); renderHead(); draw();
  };

  IX.resize = () => { if (IX.built) { layout(); draw(); } };

  function setArea(a) { IX.area = a; IX.hot = null; layout(); renderHead(); draw(); }
  function setColour(c) { IX.colour = c; renderHead(); draw(); }
  IX.setArea = setArea; IX.setColour = setColour;

  window.addEventListener('DOMContentLoaded', () => {
    $('#ixCount').addEventListener('click', () => setArea('count'));
    $('#ixSp').addEventListener('click', () => setArea('sp'));
    $('#ixFam').addEventListener('click', () => setColour('family'));
    $('#ixAes').addEventListener('click', () => setColour('aes'));

    const cv = $('#ixcv');
    cv.addEventListener('mousemove', ev => {
      const b = cv.getBoundingClientRect();
      const c = hit(ev.clientX - b.left, ev.clientY - b.top);
      if (c !== IX.hot) { IX.hot = c; draw(); }
      tip(c, ev);
    });
    cv.addEventListener('mouseleave', () => { IX.hot = null; tip(null); draw(); });
    cv.addEventListener('click', ev => {
      const b = cv.getBoundingClientRect();
      const c = hit(ev.clientX - b.left, ev.clientY - b.top);
      if (!c) return;
      // The index is a way in, not a destination: a cell hands you to the tree, which is where
      // the card lives.
      if (window.APP && window.APP.setView) window.APP.setView('tree');
      if (window.TREE && window.TREE.openLang) window.TREE.openLang(c.l.code, c.l.fam);
    });
    window.addEventListener('resize', () => { if (!$('#indexview').classList.contains('hidden')) IX.resize(); });
  });
})();
