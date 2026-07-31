/* Mother Tongues — the field engine.
 *
 * WORKING-RULES §13 / CLAUDE.md rule 0: the substrate is composed PER PIXEL in a
 * fragment shader from real fields, of the real Earth, and must be legible. Nothing here
 * draws a dot on flat ground.
 *
 * Fields (see build/build_fields.py):
 *   terrain.png  R,G = elevation 16-bit  ·  B = biome id  ·  A = population, log-companded
 *   lang_c.png   R = family idx  ·  G = diversity  ·  B = documentation  ·  A = coverage
 *   lang_t.png   the same, before contact
 *
 * The two snapshots CROSSFADE. The earlier one carries no year, ever — it is a per-region
 * state, not a date (SCOPE §6). The slider's left end says "before contact" and nothing
 * in the UI prints a year for it.
 */
'use strict';

// TRAPS D2: a static host can serve a stale asset after a successful push, and the app
// then runs perfectly on yesterday's data. Every fetch carries the stamp from <meta>.
const DATA_V = (document.querySelector('meta[name=data-version]') || {}).content || '0';
const V = u => u + (u.includes('?') ? '&' : '?') + 'v=' + DATA_V;

const GRID_W = 4096, GRID_H = 2048;
const Z_LO = -11000.0, Z_HI = 9000.0;

// Indexed by Ecoregions2017 BIOME_NUM, unchanged. Keeping the source's own ids means the
// label array and the raster cannot drift apart.
const BIOMES = [
  'unclassified',                    //  0
  'tropical moist broadleaf forest', //  1
  'tropical dry broadleaf forest',   //  2
  'tropical coniferous forest',      //  3
  'temperate broadleaf forest',      //  4
  'temperate conifer forest',        //  5
  'boreal forest / taiga',           //  6
  'tropical grassland & savanna',    //  7
  'temperate grassland & steppe',    //  8
  'flooded grassland',               //  9
  'montane grassland & shrubland',   // 10
  'tundra',                          // 11
  'mediterranean woodland & scrub',  // 12
  'desert & xeric shrubland',        // 13
  'mangrove',                        // 14
  'rock & ice'                       // 15
];
const AES = ['not assessed', 'not endangered', 'threatened', 'shifting',
             'moribund', 'nearly extinct', 'extinct'];
const MED = ['long grammar', 'grammar', 'grammar sketch', 'phonology or wordlist',
             'minimal or none'];

const VS = `
attribute vec2 a;
varying vec2 uv;
void main(){ uv = a*0.5+0.5; gl_Position = vec4(a,0.0,1.0); }`;

const FS = `
precision highp float;
varying vec2 uv;
uniform sampler2D terrain, env, langC, langT;
uniform vec2 res, grid, centre;
uniform float span, mixT;
uniform float oLang, oDiv, oPop, oGreen, oRelief, oDoc, oCoarse;

vec2 lonlat(vec2 frag){
  float aspect = res.x / res.y;
  vec2 d = (frag - 0.5) * vec2(span, span / aspect);
  return vec2(centre.x + d.x, centre.y + d.y);   // uv.y=0 is the BOTTOM in GL
}
vec2 texcoord(vec2 ll){
  return vec2(fract((ll.x + 180.0) / 360.0), (90.0 - ll.y) / 180.0);
}
float elevAt(vec2 t){
  vec4 c = texture2D(terrain, t);
  float v = c.r * 65280.0 / 65535.0 + c.g * 255.0 / 65535.0;
  return v * (Z_HI_ - Z_LO_) + Z_LO_;
}
vec3 biomeColour(float id){
  int i = int(floor(id * 255.0 + 0.5));
  if(i ==  1) return vec3(0.055,0.235,0.100);   // tropical moist broadleaf
  if(i ==  2) return vec3(0.170,0.290,0.115);   // tropical dry broadleaf
  if(i ==  3) return vec3(0.095,0.245,0.145);   // tropical conifer
  if(i ==  4) return vec3(0.145,0.300,0.135);   // temperate broadleaf
  if(i ==  5) return vec3(0.105,0.240,0.160);   // temperate conifer
  if(i ==  6) return vec3(0.115,0.200,0.150);   // boreal / taiga
  if(i ==  7) return vec3(0.445,0.440,0.180);   // tropical grassland & savanna
  if(i ==  8) return vec3(0.455,0.440,0.240);   // temperate grassland
  if(i ==  9) return vec3(0.215,0.355,0.225);   // flooded grassland
  if(i == 10) return vec3(0.330,0.345,0.250);   // montane grassland
  if(i == 11) return vec3(0.355,0.375,0.355);   // tundra
  if(i == 12) return vec3(0.395,0.360,0.160);   // mediterranean
  if(i == 13) return vec3(0.615,0.520,0.320);   // desert & xeric
  if(i == 14) return vec3(0.105,0.300,0.225);   // mangrove
  if(i == 15) return vec3(0.810,0.830,0.850);   // rock & ice
  return vec3(0.300,0.320,0.300);
}
vec3 familyColour(float idx){
  float i = floor(idx * 255.0 + 0.5);
  float h = fract(i * 0.6180339887);
  float s = 0.55 + 0.25 * fract(i * 0.311);
  float v = 0.80 + 0.20 * fract(i * 0.727);
  vec3 k = mod(h * 6.0 + vec3(5.0, 3.0, 1.0), 6.0);
  return v - v * s * clamp(min(k, 4.0 - k), 0.0, 1.0);
}

void main(){
  vec2 ll = lonlat(uv);
  if(ll.y > 90.0 || ll.y < -90.0){ gl_FragColor = vec4(0.035,0.045,0.055,1.0); return; }
  vec2 t = texcoord(ll);
  vec4 E = texture2D(env, t);          // R = biome, G = population
  float z = elevAt(t);

  vec2 px = 1.0 / grid;
  float zE = elevAt(t + vec2(px.x,0.0)), zW = elevAt(t - vec2(px.x,0.0));
  float zN = elevAt(t - vec2(0.0,px.y)), zS = elevAt(t + vec2(0.0,px.y));
  float mLat = 111320.0;
  float mLon = mLat * max(cos(radians(ll.y)), 0.02);
  float dx = (zE - zW) / (2.0 * (360.0/grid.x) * mLon);
  float dy = (zN - zS) / (2.0 * (180.0/grid.y) * mLat);
  float exg = mix(30.0, 4.0, clamp((360.0 - span)/358.0, 0.0, 1.0));
  vec3 nrm = normalize(vec3(-dx*exg, dy*exg, 1.0));
  vec3 sun = normalize(vec3(-0.45, 0.55, 0.70));
  float lam = clamp(dot(nrm, sun), 0.0, 1.0);
  float shade = mix(1.0, 0.40 + 0.85*lam, oRelief);

  vec3 col;
  if(z <= 0.0){
    float d = clamp(-z/6000.0, 0.0, 1.0);
    col = mix(vec3(0.075,0.180,0.235), vec3(0.016,0.043,0.082), pow(d,0.45));
    col += 0.045 * smoothstep(0.03, 0.0, d);
  } else {
    col = mix(vec3(0.34,0.33,0.29), biomeColour(E.r), oGreen) * shade;

    vec4 LC = texture2D(langC, t), LT = texture2D(langT, t);
    float wT = 1.0 - mixT;
    float covSharp = max(LC.a*mixT, LT.a*wT);
    float famIdx = (mixT >= 0.5) ? LC.r : LT.r;
    float divv = ((mixT >= 0.5) ? LC.g : LT.g) * 255.0;
    float docv = ((mixT >= 0.5) ? LC.b : LT.b) * 255.0;

    if(oLang > 0.5 && covSharp > 0.15){
      vec3 fc = familyColour(famIdx);
      float pop = mix(0.60, 0.28 + 1.30*E.g, oPop);
      float grain = 0.0;
      if(oDiv > 0.5 && divv > 1.0){
        float f = 7.0 + 34.0 * clamp(divv/14.0, 0.0, 1.0);
        vec2 q = t * grid;
        grain = (sin(q.x*f)*sin(q.y*f) + 0.6*sin((q.x+q.y)*f*0.61)) * 0.5;
        grain *= 0.13 * clamp(divv/6.0, 0.0, 1.0);
      }
      float a = clamp(0.32 + 0.44*clamp(divv/8.0, 0.0, 1.0), 0.0, 0.86) * covSharp;
      col = mix(col, fc*pop*shade*(1.0+grain), a);

      if(oDoc > 0.5 && docv >= 4.0){
        float s = sin((t.x + t.y) * grid.x * 0.5);
        col = mix(col, vec3(0.88,0.55,0.32), 0.22*step(0.55, s));
      }
    } else if(oCoarse > 0.5){
      float s = sin((t.x - t.y) * grid.x * 0.35);
      col = mix(col, vec3(0.60,0.20,0.20), 0.16*step(0.65, s));
    }
  }

  gl_FragColor = vec4(pow(clamp(col,0.0,1.0), vec3(0.92)), 1.0);
}`.replace(/Z_HI_/g, Z_HI.toFixed(1)).replace(/Z_LO_/g, '(' + Z_LO.toFixed(1) + ')');

const $ = s => document.querySelector(s);
const cv = $('#gl');
const gl = cv.getContext('webgl', { antialias: false, preserveDrawingBuffer: true });
if (!gl) { $('#loading').textContent = 'This browser has no WebGL.'; throw new Error('no webgl'); }

const state = {
  centre: [12, 0], span: 360, mixT: 1,
  layers: { lang: 1, div: 1, pop: 1, green: 1, relief: 1, doc: 0, coarse: 0 },
  meta: null, langs: null, ready: false
};
window.APP = state;

function compile(type, src) {
  const s = gl.createShader(type);
  gl.shaderSource(s, src); gl.compileShader(s);
  if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s));
  return s;
}
const prog = gl.createProgram();
gl.attachShader(prog, compile(gl.VERTEX_SHADER, VS));
gl.attachShader(prog, compile(gl.FRAGMENT_SHADER, FS));
gl.linkProgram(prog);
if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(prog));
gl.useProgram(prog);

const vbo = gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER, vbo);
gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1, 1,-1, -1,1, 1,1]), gl.STATIC_DRAW);
const aloc = gl.getAttribLocation(prog, 'a');
gl.enableVertexAttribArray(aloc);
gl.vertexAttribPointer(aloc, 2, gl.FLOAT, false, 0, 0);

const U = n => gl.getUniformLocation(prog, n);
const tex = {};
function loadTex(name, url, unit) {
  return new Promise((res, rej) => {
    const im = new Image();
    im.onload = () => {
      const t = gl.createTexture();
      gl.activeTexture(gl.TEXTURE0 + unit);
      gl.bindTexture(gl.TEXTURE_2D, t);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.REPEAT);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      // NEAREST on the language field: interpolating a family INDEX would invent families
      // NEAREST on anything carrying an ID or a count; LINEAR only on elevation.
      const f = (name === 'terrain') ? gl.LINEAR : gl.NEAREST;
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, f);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, f);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, im);
      tex[name] = { t, unit, im };
      res();
    };
    im.onerror = () => rej(new Error('failed to load ' + url));
    im.src = V(url);
  });
}

// Never let the drawing buffer collapse to zero: a 0x0 canvas renders nothing and, worse,
// makes every screen->world conversion NaN. Seen for real when the embedding context
// reported innerWidth === 0.
// A <canvas> is a REPLACED element: `position:fixed; inset:0` does NOT stretch it, because
// `width:auto` resolves to its intrinsic (attribute) width. So the CSS size must be set
// explicitly — and it must be measured from the VIEWPORT, never from the canvas itself.
// Measuring cv.clientWidth created a feedback loop: buffer = client*dpr grew the element,
// which grew client, which grew the buffer: 1280 -> 2560 -> 5120 -> 19200 px.
function viewportSize() {
  // Safe to read the canvas here: CSS sizes it in viewport units, so clientWidth does NOT
  // depend on cv.width. Never write cv.style.width from this — that is the loop.
  return [cv.clientWidth || window.innerWidth || 0, cv.clientHeight || window.innerHeight || 0];
}
let sizeRetry = 0;
function resize() {
  const [w, h] = viewportSize();
  if (w < 2 || h < 2) {
    if (sizeRetry++ < 120) requestAnimationFrame(() => { resize(); render(); });
    return false;
  }
  sizeRetry = 0;
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  const cw = Math.round(w * dpr), ch = Math.round(h * dpr);
  if (cv.width !== cw || cv.height !== ch) { cv.width = cw; cv.height = ch; }
  return true;
}

function render() {
  if (!state.ready) return;
  if (cv.width < 2 || cv.height < 2) { resize(); if (cv.width < 2) return; }
  gl.viewport(0, 0, cv.width, cv.height);
  gl.uniform2f(U('res'), cv.width, cv.height);
  gl.uniform2f(U('grid'), GRID_W, GRID_H);
  gl.uniform2f(U('centre'), state.centre[0], state.centre[1]);
  gl.uniform1f(U('span'), state.span);
  gl.uniform1f(U('mixT'), state.mixT);
  const L = state.layers;
  gl.uniform1f(U('oLang'), L.lang); gl.uniform1f(U('oDiv'), L.div);
  gl.uniform1f(U('oPop'), L.pop); gl.uniform1f(U('oGreen'), L.green);
  gl.uniform1f(U('oRelief'), L.relief); gl.uniform1f(U('oDoc'), L.doc);
  gl.uniform1f(U('oCoarse'), L.coarse);
  // binding tolerates absence: a missing language field keeps the world rendering
  for (const [uni, nm] of [['terrain','terrain'], ['env','env'], ['langC','lang_c'], ['langT','lang_t']]) {
    const e = tex[nm] || tex['terrain'];
    if (!e) continue;
    gl.activeTexture(gl.TEXTURE0 + e.unit);
    gl.bindTexture(gl.TEXTURE_2D, e.t);
    gl.uniform1i(U(uni), e.unit);
  }
  gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
}
state.render = render;
state.jumpTo = (lon, lat, span) => { state.centre = [lon, lat]; if (span) state.span = span; render(); };

const probe = document.createElement('canvas');
const pctx = probe.getContext('2d', { willReadFrequently: true });
function sample(name, lon, lat) {
  const e = tex[name]; if (!e) return null;
  // "Unknown" is a legitimate return; a fabricated one is not (CLAUDE.md rule 10). A
  // non-finite coordinate previously drew nothing and read back as zeros, which the
  // readout then rendered as a confident "11000 m below sea level".
  if (!isFinite(lon) || !isFinite(lat)) return null;
  const x = Math.min(GRID_W - 1, Math.floor(((((lon + 180) % 360) + 360) % 360) / 360 * GRID_W));
  const y = Math.min(GRID_H - 1, Math.max(0, Math.floor((90 - lat) / 180 * GRID_H)));
  probe.width = 1; probe.height = 1;
  pctx.clearRect(0, 0, 1, 1);
  pctx.drawImage(e.im, x, y, 1, 1, 0, 0, 1, 1);
  return pctx.getImageData(0, 0, 1, 1).data;
}

function fmtLL(lon, lat) {
  const la = Math.abs(lat).toFixed(2) + '°' + (lat >= 0 ? 'N' : 'S');
  const w = ((lon + 540) % 360) - 180;
  return la + ' ' + Math.abs(w).toFixed(2) + '°' + (w >= 0 ? 'E' : 'W');
}
function famName(idx) {
  if (!state.meta || !idx) return '—';
  const f = state.meta.families.find(f => f.idx === idx);
  return f ? f.name : 'family #' + idx;
}

function updateReadout(lon, lat) {
  const T = sample('terrain', lon, lat);
  const E = sample('env', lon, lat);
  if (!T) {                       // say so, rather than print a number we do not have
    ['roPlace','roFam','roDiv','roBiome','roPop','roElev']
      .forEach(id => { $('#' + id).textContent = '—'; });
    return;
  }
  const L = sample(state.mixT >= 0.5 ? 'lang_c' : 'lang_t', lon, lat);
  const z = ((T[0] * 256 + T[1]) / 65535) * (Z_HI - Z_LO) + Z_LO;
  const dens = E ? Math.pow(10, (E[1] / 255) * 4) - 1 : 0;
  $('#roPlace').textContent = fmtLL(lon, lat);
  $('#roElev').textContent = z <= 0 ? Math.round(-z) + ' m below sea level' : Math.round(z) + ' m';
  $('#roBiome').textContent = z <= 0 ? 'sea' : (E ? (BIOMES[E[0]] || '—') : '—');
  $('#roPop').textContent = dens < 0.5 ? 'nobody recorded' : Math.round(dens).toLocaleString() + ' / km²';
  if (L && L[3] > 40) {
    $('#roFam').textContent = famName(L[0]);
    $('#roDiv').textContent = L[1] === 0 ? '—' : (L[1] + (L[1] >= 255 ? '+' : ''));
  } else {
    $('#roFam').textContent = z > 0 ? 'no polygon here' : '—';
    $('#roDiv').textContent = '—';
  }
}

function nearestLanguage(lon, lat) {
  if (!state.langs) return null;
  const R = state.langs.rows;
  let best = null, bd = 1e9;
  const cl = Math.cos(lat * Math.PI / 180);
  for (let i = 0; i < R.length; i++) {
    const r = R[i];
    let dl = r[2] - lon;
    if (dl > 180) dl -= 360; if (dl < -180) dl += 360;
    const d = (dl * cl) * (dl * cl) + (r[3] - lat) * (r[3] - lat);
    if (d < bd) { bd = d; best = r; }
  }
  return best ? { row: best, deg: Math.sqrt(bd) } : null;
}

function showCard(lon, lat) {
  const hit = nearestLanguage(lon, lat);
  if (!hit) return;
  const r = hit.row;
  const km = Math.round(hit.deg * 111);
  const E = sample('env', r[2], r[3]);
  $('#cardBody').innerHTML =
    '<div class="eyebrow">language · nearest recorded point, ' + km + ' km away</div>' +
    '<h2>' + r[1] + '</h2>' +
    '<div class="warn">Glottolog <b>reference name, not the autonym</b>. This project\'s own ' +
    'rules require the autonym first; no autonym source is wired yet (register D6).</div>' +
    '<table>' +
    '<tr><td>family</td><td>' + famName(r[4]) + '</td></tr>' +
    '<tr><td>glottocode</td><td><code>' + r[0] + '</code></td></tr>' +
    '<tr><td>ISO 639-3</td><td>' + (r[7] ? '<code>' + r[7] + '</code> <i>alias, not the key</i>' : '—') + '</td></tr>' +
    '<tr><td>vitality</td><td>' + (AES[r[6]] || 'not assessed') + '</td></tr>' +
    '<tr><td>description</td><td>' + (r[5] >= 0 ? MED[Math.min(4, r[5])] : 'unknown') + '</td></tr>' +
    '<tr><td>first attested</td><td>' + (r[8] ? r[8] : 'no date recorded') + '</td></tr>' +
    '<tr><td>biome at its point</td><td>' + (E ? (BIOMES[E[0]] || '—') : '—') + '</td></tr>' +
    '</table>' +
    '<div class="tier">Recorded for this language — Glottolog 5.3, CC-BY 4.0. ' +
    '<b>No speaker count is shown:</b> this project requires (value, year, source) and the ' +
    'catalogue carries none, so "unknown" is the honest return.</div>';
  $('#card').classList.remove('hidden');
}

function toLonLat(ev) {
  const r = cv.getBoundingClientRect();
  const [vw, vh] = viewportSize();
  const w = r.width || vw, h = r.height || vh;
  const u = (ev.clientX - r.left) / w, v = (ev.clientY - r.top) / h;
  // v is measured from the TOP of the element, so north is -v here (the shader uses
  // GL's bottom-origin uv and therefore the opposite sign — they must not be "unified").
  return [state.centre[0] + (u - 0.5) * state.span,
          state.centre[1] - (v - 0.5) * (state.span / (w / h))];
}
let drag = null;
cv.addEventListener('mousedown', e => {
  drag = { x: e.clientX, y: e.clientY, c: state.centre.slice(), moved: 0 };
});
addEventListener('mouseup', e => {
  if (drag && drag.moved < 5) { const p = toLonLat(e); showCard(p[0], p[1]); }
  drag = null;
});
addEventListener('mousemove', e => {
  const p = toLonLat(e);
  if (!drag) { updateReadout(p[0], p[1]); return; }
  drag.moved += Math.abs(e.movementX || 0) + Math.abs(e.movementY || 0);
  const r = cv.getBoundingClientRect();
  const [vw, vh] = viewportSize();
  const w = r.width || vw, h = r.height || vh;
  state.centre[0] = drag.c[0] - (e.clientX - drag.x) / w * state.span;
  state.centre[1] = drag.c[1] + (e.clientY - drag.y) / h * (state.span / (w / h));
  state.centre[1] = Math.max(-85, Math.min(85, state.centre[1]));
  render();
});
cv.addEventListener('wheel', e => {
  e.preventDefault();
  state.span = Math.max(1.2, Math.min(360, state.span * Math.exp(e.deltaY * 0.0016)));
  render();
}, { passive: false });

$('#snap').addEventListener('input', e => {
  state.mixT = +e.target.value;
  $('#snapNote').textContent = state.mixT > 0.98 ? 'today'
    : state.mixT < 0.02 ? 'before contact — a per-region state, not a year'
    : 'blending — ' + Math.round(state.mixT * 100) + '% today';
  render();
});
const TOGGLES = { lLang:'lang', lDiv:'div', lPop:'pop', lGreen:'green',
                  lRelief:'relief', lDoc:'doc', lCoarse:'coarse' };
Object.keys(TOGGLES).forEach(id => {
  $('#' + id).addEventListener('change', e => {
    state.layers[TOGGLES[id]] = e.target.checked ? 1 : 0; render();
  });
});
$('#cardX').addEventListener('click', () => $('#card').classList.add('hidden'));
$('#aboutX').addEventListener('click', () => $('#about').classList.add('hidden'));
$('#aboutBtn').addEventListener('click', () => $('#about').classList.remove('hidden'));
addEventListener('resize', () => { resize(); render(); });
// NB: observe documentElement, not cv — observing the canvas closes the feedback loop.
if (window.ResizeObserver) new ResizeObserver(() => { resize(); render(); })
  .observe(document.documentElement);

// a console-scriptable probe, so verification does not depend on synthetic mouse events
state.probe = (lon, lat) => {
  const T = sample('terrain', lon, lat), E = sample('env', lon, lat);
  const L = sample(state.mixT >= 0.5 ? 'lang_c' : 'lang_t', lon, lat);
  if (!T) return null;
  return {
    elev_m: Math.round(((T[0] * 256 + T[1]) / 65535) * (Z_HI - Z_LO) + Z_LO),
    biome: E ? (BIOMES[E[0]] || null) : null,
    pop_per_km2: E ? Math.round(Math.pow(10, (E[1] / 255) * 4) - 1) : null,
    family: (L && L[3] > 40) ? famName(L[0]) : null,
    languages_here: (L && L[3] > 40) ? L[1] : null
  };
};

const TOUR = [
  ['The world', 12, 0, 360],
  ['New Guinea highlands', 142, -5.5, 16],
  ['Vanuatu & the Solomons', 166, -14, 20],
  ['The Caucasus', 44.5, 42.5, 12],
  ['Nigerian middle belt', 9, 8.5, 20],
  ['Amazon & the Andean flank', -68, -8, 34],
  ['Northern Australia', 133, -14, 28],
  ['Himalayan valleys', 88, 28, 22],
  ['Mesoamerica', -95, 17, 16],
  ['Pacific Northwest coast', -126, 50, 16],
  ['The North China Plain', 116.5, 35.5, 14],
  ['Bantu — one family, a continent', 22, -6, 70],
  ['Austronesian — half the planet', 150, 0, 200]
];
$('#tour').innerHTML = TOUR.map((t, i) => '<button data-i="' + i + '">' + t[0] + '</button>').join('');
$('#tour').addEventListener('click', e => {
  const b = e.target.closest('button'); if (!b) return;
  const t = TOUR[+b.dataset.i];
  state.jumpTo(t[1], t[2], t[3]);
  updateReadout(t[1], t[2]);
});

$('#legend').innerHTML =
  '<div><b>hue</b> — language family</div>' +
  '<div><b>brightness</b> — speaker density, from a population raster</div>' +
  '<div><b>grain</b> — how many languages overlap here</div>' +
  '<div><b>ground colour</b> — biome, the variable that actually predicts the pattern</div>' +
  '<div><b>relief</b> — lit per pixel from the elevation field</div>';

async function boot() {
  resize();
  const meta = await fetch(V('fields/fields.json')).then(r => r.json());
  state.meta = meta;
  fetch(V('data/languages.json')).then(r => r.json()).then(d => { state.langs = d; })
    .catch(() => { state.langs = null; });
  // Credits and coverage are small; fetch them alongside and let About render whatever
  // arrived. If either fails the panel says so rather than quietly crediting nobody.
  fetch(V('data/attribution.json')).then(r => r.json()).then(d => { state.attribution = d; })
    .catch(() => { state.attribution = null; });
  fetch(V('data/coverage.json')).then(r => r.json()).then(d => { state.coverage = d; })
    .catch(() => { state.coverage = null; });
  await loadTex('terrain', 'fields/terrain.png', 0);
  state.ready = true; render();                    // a usable world as soon as terrain lands
  $('#loading').style.display = 'none';
  await loadTex('env', 'fields/env.png', 1);
  render();
  await loadTex('lang_c', 'fields/lang_c.png', 2);
  render();
  await loadTex('lang_t', 'fields/lang_t.png', 3);
  render();
  buildAbout();
  // B4: the coverage limit belongs on the frame, not only in the About panel. A viewer must be
  // able to tell mapped ground from unmapped without opening anything.
  if (state.coverage) {
    $('#legend').insertAdjacentHTML('beforeend',
      '<div style="margin-top:5px;border-top:1px solid rgba(140,160,152,.16);padding-top:5px">' +
      '<b>' + (state.coverage.today.frac_of_land_area * 100).toFixed(0) + '% of land</b> has a ' +
      'mapped language area. Unpainted land is missing data, not empty ground.</div>');
  }
  updateReadout(state.centre[0], state.centre[1]);
}

// The Sources list is GENERATED from the shipped attribution ledger, never typed here.
// A hand-written credits list drifts from the ingest the first time a source changes and
// nothing catches it; the build refuses to publish unless the shipped ledger is byte-identical
// to `Research/modeling/attribution.py`. Register item A5.
function sourcesHtml() {
  const L = state.attribution && state.attribution.ledger;
  if (!L) return '<p class="warn">The attribution ledger failed to load. ' +
    'Sources are credited in <code>web/data/attribution.json</code>.</p>';
  const rows = L.filter(s => s.ingested).map(s =>
    '<li><b>' + esc(s.title) + '</b> — ' + esc(s.layer) + '. <i>' + esc(s.licence) + '</i>' +
    (s.share_alike ? ' <b>(ShareAlike: our data inherits it)</b>' : '') +
    '<div class="fine" style="margin-top:2px">' + esc(s.attribution) +
    (s.note ? ' <span style="opacity:.72">' + esc(s.note) + '</span>' : '') + '</div></li>'
  ).join('');
  const carried = L.filter(s => !s.ingested);
  return '<ul>' + rows + '</ul>' + (carried.length
    ? '<p class="fine">Held but not in this build, with their rows already written and ' +
      'checked: ' + carried.map(s => esc(s.title) + ' (' + esc(s.licence) + ')').join(' · ') +
      '.</p>' : '');
}

// Measured from the shipped rasters at build time, not from the catalogue. "62.5% of languages
// have a polygon" is a fact about Glottography; a viewer looking at the map wants to know
// whether the ground under their eye is data or absence, which is a different number.
function coverageHtml() {
  const c = state.coverage;
  if (!c) return '';
  const t = c.today, b = c.before_contact;
  const pc = x => (x * 100).toFixed(0) + '%';
  const win = Object.entries(c.by_window_today).sort((p, q) => q[1] - p[1])
    .map(([k, v]) => esc(k) + ' ' + (v == null ? '—' : pc(v))).join(' · ');
  return '<p><b>' + pc(t.frac_of_land_area) + ' of the world\'s land area</b> has a mapped ' +
    'language area under it, and <b>' + pc(t.frac_of_population) + ' of the world\'s people</b> ' +
    'stand on that ground — coverage is best exactly where people are. Before contact: ' +
    pc(b.frac_of_land_area) + ' of land, ' + pc(b.frac_of_population) + ' of people. ' +
    'Both are measured from the rasters this page just loaded.</p>' +
    '<p class="fine">By window (today, bounding boxes rather than regions): ' + win + '. ' +
    'The gaps are real gaps in the record — Siberia is the worst of them — not gaps in the ' +
    'languages. Turn on “Mark land with no polygon” to see them on the map.</p>';
}

function esc(s) {
  return String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
}

function buildAbout() {
  const s = state.meta.snapshots || {};
  $('#aboutBody').innerHTML =
  '<h2>About, and what this model does not know</h2>' +
  '<p><b>The claim.</b> Linguistic diversity is not spread evenly, and the first thing that ' +
  'explains it is <b>climate</b> — how long the growing season is, and how many people a ' +
  'landscape can feed year-round. Terrain matters too, but less, and unevenly.</p>' +
  '<p><b>We measured that, and it changed the claim.</b> An earlier version of this project ' +
  'asserted terrain was "most of the explanation". Measured across 7,672 spoken-L1 languages ' +
  'and 6,143 land cells: ruggedness↔richness Spearman <b>+0.141</b> (<b>+0.108</b> controlling ' +
  'for latitude) against <b>−0.582</b> for latitude itself. In <b>Papunesia +0.024</b> and ' +
  '<b>Africa +0.006</b>, terrain explains essentially nothing. Robust at 1°, 2°, 4° and 6°.</p>' +
  '<h3>What it does not know</h3><ul>' +
  '<li><b>Real polygons exist for 62.5% of living languages.</b> Turn on "Mark land with no ' +
  'polygon": absence of colour is absence of data, not absence of language.</li>' +
  '<li><b>These are reference names, not autonyms.</b> This project\'s rules require the ' +
  'autonym first. No autonym source is wired yet — a known defect, not a choice.</li>' +
  '<li><b>No speaker counts.</b> We require (value, year, source); the catalogue carries none.</li>' +
  '<li><b>The earlier snapshot has no year.</b> "Before contact" is a per-region state — contact ' +
  'ranges from the 1490s to the twentieth century, and never happened in some places.</li>' +
  '<li><b>The deep past is nine languages.</b> Of ~217 with an attestation date, 82 have a mapped ' +
  'area and nine are pre-Common-Era. There is no deep-time surface here yet.</li>' +
  '<li><b>Population is floored at 1975</b>, because the only deep-time gridded population ' +
  'dataset is NonCommercial. This build uses the 2020 epoch.</li>' +
  '<li><b>Diversity is capped at 255</b> per cell; the measured maximum in this build is ' +
  (s.c ? s.c.max_div : '—') + ' today and ' + (s.t ? s.t.max_div : '—') + ' before contact.</li>' +
  '<li><b>No global continuous linguistic surface has been built before.</b> The method here is ' +
  'ours, and so is the method risk.</li></ul>' +
  '<h3>How the count works</h3>' +
  '<p>This build uses <b>Glottolog 5.3</b>\'s spoken-L1 languages: <b>7,674</b>, of which 7,672 ' +
  'have coordinates. Other authorities count differently — about 7,100, or 7,927 ISO codes — ' +
  'because the language/dialect line is drawn for non-linguistic reasons as often as linguistic ' +
  'ones. There is no single correct number and this atlas does not pretend there is.</p>' +
  '<h3>How much of the ground is data</h3>' + coverageHtml() +
  '<h3>Sources</h3>' + sourcesHtml() +
  '<p class="fine">Elevation is encoded 16-bit linear over −11000…+9000 m. That was measured, not ' +
  'inherited: an 8-bit signed-square-root encoding tuned for sea level would have created relief ' +
  'steps of 1.95° against a true median slope of 1.34° in the New Guinea highlands — steeper than ' +
  'the terrain it was drawing.</p>';
}

boot().catch(e => {
  $('#loading').textContent = 'Failed to load: ' + e.message;
  console.error(e);
});
