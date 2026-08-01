/* Mother Tongues — the field engine.
 *
 * WORKING-RULES §13 / CLAUDE.md rule 0: the substrate is composed PER PIXEL in a fragment
 * shader from real fields, of the real Earth, and must be legible. Nothing here draws a dot
 * on flat ground.
 *
 * A TILE PYRAMID, not one global raster. The master grid is 16384x8192 — 2.44 km at the
 * equator, 76% of ETOPO1's native resolution — which is 215 MB as a single elevation PNG and
 * therefore not a thing anyone can load. Level 0 (2048x1024, ~4 MB for all four fields) paints
 * the world immediately; levels 1-3 stream in for whatever the viewer is actually looking at.
 * A tile that has not arrived is drawn from its nearest loaded ancestor, so detail sharpens
 * rather than popping in from nothing.
 *
 * Fields per tile (see build/build_tiles.py):
 *   terrain  R,G = elevation 16-bit  ·  B = snow cover  ·  A = 255
 *   env      R = biome id  ·  G = population, log-companded  ·  B = NDVI greenness  ·  A = 255
 *   lang_c   R = family idx  ·  G = diversity  ·  B = documentation  ·  A = coverage
 *   lang_t   the same, before contact
 *
 * The two snapshots CROSSFADE. The earlier one carries no year, ever — it is a per-region
 * state, not a date (SCOPE §6, rule 15), and the build gate greps for a year next to it.
 */
'use strict';

// TRAPS D2: a static host can serve a stale asset after a successful push, and the app then
// runs perfectly on yesterday's data. Every fetch carries the stamp from <meta>.
const DATA_V = (document.querySelector('meta[name=data-version]') || {}).content || '0';
const V = u => u + (u.includes('?') ? '&' : '?') + 'v=' + DATA_V;
window.V = V;

const Z_LO = -11000.0, Z_HI = 9000.0;
const FIELDS = ['terrain', 'env', 'lang_c', 'lang_t'];

// Indexed by Ecoregions2017 BIOME_NUM. Keeping the source's own ids means the label array and
// the raster cannot drift apart — they did once, and the Sahara reported itself as rock & ice.
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
uniform vec4 uTile;          // lon0, lat0 (top), dLon, dLat
uniform vec2 uCentre;
uniform float uSpan, uAspect;
varying vec2 vA;
varying vec2 vLL;
void main(){
  vA = a;
  float lon = uTile.x + a.x * uTile.z;
  float lat = uTile.y - a.y * uTile.w;
  vLL = vec2(lon, lat);
  float xn = (lon - uCentre.x) / (uSpan * 0.5);
  float yn = (lat - uCentre.y) / (uSpan / uAspect * 0.5);
  gl_Position = vec4(xn, yn, 0.0, 1.0);
}`;

const FS = `
precision highp float;
varying vec2 vA;
varying vec2 vLL;
uniform sampler2D terrain, env, langC, langT;
uniform vec4 uSrc;            // where this tile's core sits inside the bound texture
uniform vec2 uSrcGrid;        // world pixels of the SOURCE level (for ground distances)
uniform float uStep;          // one source texel, in texture coordinates
uniform float mixT, uSpan, uDetail;
uniform float oLang, oDiv, oPop, oGreen, oRelief, oDoc, oCoarse;

vec2 T(vec2 a){ return uSrc.xy + a * uSrc.zw; }

float elevAt(vec2 t){
  vec4 c = texture2D(terrain, t);
  return (c.r * 65280.0 / 65535.0 + c.g * 255.0 / 65535.0) * (Z_HI_ - Z_LO_) + Z_LO_;
}

// Value noise. Cheap, stable under pan, and enough to carry sub-texel structure.
float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453123); }
float vnoise(vec2 p){
  vec2 i = floor(p), f = fract(p);
  vec2 u = f * f * (3.0 - 2.0 * f);
  return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), u.x),
             mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), u.x), u.y);
}
float fbm(vec2 p){
  float s = 0.0, a = 0.5;
  for(int k = 0; k < 5; k++){ s += a * vnoise(p); p *= 2.03; a *= 0.5; }
  return s;
}

vec3 biomeColour(float id){
  int i = int(floor(id * 255.0 + 0.5));
  if(i ==  1) return vec3(0.055,0.235,0.100);
  if(i ==  2) return vec3(0.170,0.290,0.115);
  if(i ==  3) return vec3(0.095,0.245,0.145);
  if(i ==  4) return vec3(0.145,0.300,0.135);
  if(i ==  5) return vec3(0.105,0.240,0.160);
  if(i ==  6) return vec3(0.115,0.200,0.150);
  if(i ==  7) return vec3(0.445,0.440,0.180);
  if(i ==  8) return vec3(0.455,0.440,0.240);
  if(i ==  9) return vec3(0.215,0.355,0.225);
  if(i == 10) return vec3(0.330,0.345,0.250);
  if(i == 11) return vec3(0.355,0.375,0.355);
  if(i == 12) return vec3(0.395,0.360,0.160);
  if(i == 13) return vec3(0.615,0.520,0.320);
  if(i == 14) return vec3(0.105,0.300,0.225);
  if(i == 15) return vec3(0.810,0.830,0.850);
  return vec3(0.300,0.320,0.300);
}
vec3 familyColour(float idx){
  float i = floor(idx * 255.0 + 0.5);
  float h = fract(i * 0.6180339887);
  float s = 0.55 + 0.25 * fract(i * 0.311);
  float v = 0.80 + 0.20 * fract(i * 0.727);
  vec3 k = mod(h * 6.0 + vec3(5.0, 3.0, 1.0), 6.0);
  // 0.62 so the same hue that glowed on black now sits as ink on paper.
  return (v - v * s * clamp(min(k, 4.0 - k), 0.0, 1.0)) * 0.62;
}

void main(){
  vec2 ll = vLL;
  if(ll.y > 90.0 || ll.y < -90.0){ gl_FragColor = vec4(0.945,0.926,0.894,1.0); return; }
  vec2 t = T(vA);
  vec4 E = texture2D(env, t);          // R biome · G population · B NDVI
  vec4 TT = texture2D(terrain, t);     // B snow cover
  float z = elevAt(t);

  // ---- ground normal, from the field's own gradient, in real metres -------------------
  float zE = elevAt(t + vec2(uStep,0.0)), zW = elevAt(t - vec2(uStep,0.0));
  float zN = elevAt(t - vec2(0.0,uStep)), zS = elevAt(t + vec2(0.0,uStep));
  float mLat = 111320.0;
  // ⚠ POLAR SINGULARITY. A degree of longitude shrinks to nothing at the pole, so dividing by
  // cos(lat) sends the east-west gradient to infinity there: slope pinned at 1.0 across the
  // last rows of Antarctica, which suppressed the snow term and left a tan band along the
  // bottom of the world. Past ~81 degrees the longitudinal gradient carries no information at
  // this grid spacing, so clamp it rather than compute a number that is not meaningful.
  float mLon = mLat * max(cos(radians(ll.y)), 0.15);
  float dx = (zE - zW) / (2.0 * (360.0/uSrcGrid.x) * mLon);
  float dy = (zN - zS) / (2.0 * (180.0/uSrcGrid.y) * mLat);
  float slope = clamp(length(vec2(dx,dy)) * 4.0, 0.0, 1.0);

  // Vertical exaggeration falls as you zoom in: at 360 deg the relief must read at all, at
  // 2 deg the true gradient is already legible and exaggeration turns hills into spikes.
  float exg = mix(26.0, 3.2, clamp((360.0 - uSpan)/358.0, 0.0, 1.0));

  // ---- procedural sub-grid detail (register B5) ---------------------------------------
  // uDetail rises above zero only once a screen pixel is FINER than a source texel, i.e.
  // only where the data has genuinely run out. It never overrides measured relief; it adds
  // texture at a scale the data cannot describe, and its character is keyed to the material
  // so dunes appear in sand and mottle in forest. Nothing here invents a landform.
  vec2 wp = vec2(ll.x, ll.y) * 220.0;
  float det = 0.0, nrough = 0.0;
  if(uDetail > 0.01){
    float b = floor(E.r * 255.0 + 0.5);
    float f1 = fbm(wp);
    det = f1;
    if(b > 12.5 && b < 13.5){
      // Sand carries a weak directional grain. An earlier version gave it half the
      // amplitude of the whole detail term and it read as diagonal corduroy across the
      // Great Basin — a pattern, not a texture. Keep it as a small perturbation of the
      // noise, never as a wave in its own right.
      det = mix(f1, f1 * 0.82 + 0.18 * (0.5 + 0.5 * sin(wp.x * 1.7 + wp.y * 0.6 + f1 * 9.0)), 0.6);
    }
    nrough = (det - 0.5) * uDetail * (0.18 + 0.42 * slope);
  }

  vec3 nrm = normalize(vec3(-dx*exg - nrough*0.9, dy*exg + nrough*0.9, 1.0));
  vec3 sun = normalize(vec3(-0.45, 0.55, 0.70));
  float lam = clamp(dot(nrm, sun), 0.0, 1.0);
  // A sky term as well as a sun term: pure Lambert makes every north face pitch black, which
  // is not what ground looks like under an atmosphere.
  float sky = 0.5 + 0.5 * nrm.z;
  // A LIGHT atlas, not a night render: the sun term is halved and a large ambient added, so
  // relief still reads as relief but nothing goes to black on a paper-white page.
  float shade = mix(1.0, 0.74 + 0.30*lam + 0.14*sky, oRelief);

  vec3 col;
  if(z <= 0.0){
    float d = clamp(-z/6000.0, 0.0, 1.0);
    col = mix(vec3(0.784,0.855,0.878), vec3(0.435,0.573,0.663), pow(d,0.42));
    col += 0.050 * smoothstep(0.03, 0.0, d);             // the shelf edge
    // Sea floor relief, faint: the ocean is not a flat blue plate.
    col *= 1.0 + 0.16 * (lam - 0.5) * smoothstep(0.9, 0.15, d);
  } else {
    // ---- land material ----------------------------------------------------------------
    // Biome says WHAT this is; NDVI says how much is actually growing. Flat biome colour
    // alone is a choropleth. Measured greenness varies per pixel, so the ground does too.
    // Biome hues were authored for a dark ground. On paper they read as mud, so every one
    // is lifted toward the page before it is used — the hierarchy between biomes survives,
    // the key changes.
    vec3 bc = mix(biomeColour(E.r), vec3(0.960,0.940,0.890), 0.42);
    float ndvi = E.b;                                     // PEAK greenness over the year
    // Unvegetated ground is THIS biome's ground, darker — not a single desert-soil colour.
    // A fixed warm soil put sand-coloured ground under Siberian taiga and Arctic tundra
    // wherever NDVI was low or missing: 5.1% of all land. The biome classification already
    // says what the ground is made of, so bare ground keeps its own material and only loses
    // the green. Greenness then modulates WITHIN the biome instead of replacing it.
    vec3 bare = bc * (0.86 + 0.16 * det);
    vec3 lush = bc * (0.74 + 0.42 * ndvi);
    vec3 mat  = mix(bare, lush, clamp((ndvi - 0.06) * 2.4, 0.0, 1.0));
    // Steep ground sheds soil and vegetation. This is why mountains have grey faces.
    mat = mix(mat, vec3(0.70,0.665,0.625) * (0.9 + 0.2*det), slope * 0.45);
    col = mix(vec3(0.870,0.850,0.812), mat, oGreen);

    // Measured snow cover, not an invented snowline.
    float snow = TT.b;
    float sn = clamp(snow * 1.25 - 0.10, 0.0, 1.0) * (1.0 - 0.35 * slope);
    col = mix(col, vec3(0.985,0.990,1.0), sn * 0.92);

    col *= shade;
    col *= 1.0 + 0.07 * (det - 0.5) * uDetail;           // micro variation in albedo

    vec4 LC = texture2D(langC, t), LT = texture2D(langT, t);
    float wT = 1.0 - mixT;
    float covSharp = max(LC.a*mixT, LT.a*wT);
    float famIdx = (mixT >= 0.5) ? LC.r : LT.r;
    float divv = ((mixT >= 0.5) ? LC.g : LT.g) * 255.0;
    float docv = ((mixT >= 0.5) ? LC.b : LT.b) * 255.0;

    if(oLang > 0.5 && covSharp > 0.15){
      vec3 fc = familyColour(famIdx);
      float pop = mix(1.00, 0.72 + 0.85*E.g, oPop);
      float grain = 0.0;
      if(oDiv > 0.5 && divv > 1.0){
        float f = 7.0 + 34.0 * clamp(divv/14.0, 0.0, 1.0);
        vec2 q = vec2(ll.x, -ll.y) * (uSrcGrid.x / 360.0);
        grain = (sin(q.x*f)*sin(q.y*f) + 0.6*sin((q.x+q.y)*f*0.61)) * 0.5;
        grain *= 0.13 * clamp(divv/6.0, 0.0, 1.0);
      }
      float a = clamp(0.26 + 0.36*clamp(divv/8.0, 0.0, 1.0), 0.0, 0.74) * covSharp;
      col = mix(col, fc*pop*shade*(1.0+grain), a);

      if(oDoc > 0.5 && docv >= 4.0){
        float s = sin((ll.x + ll.y) * 30.0);
        col = mix(col, vec3(0.72,0.38,0.16), 0.22*step(0.55, s));
      }
    } else if(oCoarse > 0.5){
      float s = sin((ll.x - ll.y) * 24.0);
      col = mix(col, vec3(0.72,0.30,0.26), 0.20*step(0.65, s));
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
  meta: null, langs: null, ready: false, level: 0, loaded: 0, pending: 0
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
gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([0,0, 1,0, 0,1, 1,1]), gl.STATIC_DRAW);
const aloc = gl.getAttribLocation(prog, 'a');
gl.enableVertexAttribArray(aloc);
gl.vertexAttribPointer(aloc, 2, gl.FLOAT, false, 0, 0);

const _u = {};
const U = n => (n in _u) ? _u[n] : (_u[n] = gl.getUniformLocation(prog, n));

// ---------------------------------------------------------------------------------------
// the tile cache
// ---------------------------------------------------------------------------------------
const tiles = new Map();                 // "lvl/tx/ty" -> {n, tex:{}, img:{}, ready}
const MAXTILES = 220;                    // ~220 * 4 textures; well inside a mobile GL budget

function tileKey(l, x, y) { return l + '/' + x + '/' + y; }
function exists(l, x, y) {
  const m = state.meta && state.meta.tiles && state.meta.tiles[String(l)];
  return !!m && m.indexOf(x + '_' + y) >= 0;
}

function makeTex(im, linear) {
  const t = gl.createTexture();
  gl.bindTexture(gl.TEXTURE_2D, t);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
  // LINEAR only on elevation. Interpolating a family index or a biome id invents categories
  // that do not exist — a blend of taiga and steppe is not a third biome.
  const f = linear ? gl.LINEAR : gl.NEAREST;
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, f);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, f);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, im);
  return t;
}

function request(l, x, y) {
  const k = tileKey(l, x, y);
  if (tiles.has(k)) { tiles.get(k).used = state.frame; return tiles.get(k); }
  if (!exists(l, x, y)) return null;
  const rec = { n: 0, tex: {}, img: {}, ready: false, used: state.frame, l, x, y };
  tiles.set(k, rec);
  state.pending++;
  FIELDS.forEach(f => {
    const im = new Image();
    im.onload = () => {
      rec.tex[f] = makeTex(im, f === 'terrain');
      rec.img[f] = im;
      if (++rec.n === FIELDS.length) {
        rec.ready = true; state.loaded++; state.pending--;
        scheduleRender();
      }
    };
    im.onerror = () => {                     // a missing tile must not wedge the pyramid
      if (++rec.n === FIELDS.length) { rec.ready = true; state.loaded++; state.pending--; scheduleRender(); }
    };
    im.src = V('fields/z' + l + '/' + f + '_' + x + '_' + y + '.png');
  });
  return rec;
}

function evict() {
  if (tiles.size <= MAXTILES) return;
  const arr = [...tiles.entries()].filter(e => e[1].l > 0)
    .sort((a, b) => a[1].used - b[1].used);
  for (let i = 0; i < arr.length && tiles.size > MAXTILES; i++) {
    const [k, r] = arr[i];
    if (!r.ready) continue;
    FIELDS.forEach(f => { if (r.tex[f]) gl.deleteTexture(r.tex[f]); });
    tiles.delete(k);
  }
}

/** The nearest loaded ancestor of (l,x,y), and where this tile sits inside it. */
function resolve(l, x, y) {
  for (let li = l; li >= 0; li--) {
    const s = 1 << (l - li);
    const ax = Math.floor(x / s), ay = Math.floor(y / s);
    const r = tiles.get(tileKey(li, ax, ay));
    if (r && r.ready && r.tex.terrain) {
      const T = state.meta.tile, S = state.meta.skirt, N = T + 2 * S;
      // fraction of the ancestor's CORE that this tile covers
      const fx = (x - ax * s) / s, fy = (y - ay * s) / s, fs = 1 / s;
      return {
        rec: r, level: li,
        src: [(S + fx * T) / N, (S + fy * T) / N, (fs * T) / N, (fs * T) / N],
        grid: [2048 << li, 1024 << li]
      };
    }
  }
  return null;
}

function levelFor() {
  // Pick the level whose texel is no coarser than a screen pixel, then stop at the top.
  const worldPx = cv.width * 360 / state.span;
  const l = Math.ceil(Math.log2(Math.max(1, worldPx) / 2048));
  return Math.max(0, Math.min(state.meta ? state.meta.maxLevel : 0, l));
}

// Never let the drawing buffer collapse to zero: a 0x0 canvas renders nothing and makes every
// screen->world conversion NaN. A <canvas> is a REPLACED element — `inset:0` does NOT stretch
// it — so CSS sizes it in viewport units and we only ever read that. Measuring cv.clientWidth
// to SET cv.width was a feedback loop that grew the buffer 1280 -> 19200 px.
function viewportSize() {
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

let _raf = 0;
function scheduleRender() {
  if (_raf) return;
  _raf = requestAnimationFrame(() => { _raf = 0; render(); });
}
state.frame = 0;

function render() {
  if (!state.ready || !state.meta) return;
  if (cv.width < 2 || cv.height < 2) { resize(); if (cv.width < 2) return; }
  state.frame++;
  gl.viewport(0, 0, cv.width, cv.height);
  gl.clearColor(0.945, 0.926, 0.894, 1.0);
  gl.clear(gl.COLOR_BUFFER_BIT);

  const aspect = cv.width / cv.height;
  const halfLon = state.span / 2, halfLat = state.span / aspect / 2;
  const lon0 = state.centre[0] - halfLon, lon1 = state.centre[0] + halfLon;
  const lat0 = state.centre[1] - halfLat, lat1 = state.centre[1] + halfLat;

  const L = levelFor();
  state.level = L;
  const cols = 2 << L, rows = 1 << L;
  const dLon = 360 / cols, dLat = 180 / rows;

  const ty0 = Math.max(0, Math.floor((90 - Math.min(90, lat1)) / dLat));
  const ty1 = Math.min(rows - 1, Math.floor((90 - Math.max(-90, lat0)) / dLat));
  const tx0 = Math.floor((lon0 + 180) / dLon);
  const tx1 = Math.floor((lon1 + 180) / dLon);

  const lay = state.layers;
  gl.uniform2f(U('uCentre'), state.centre[0], state.centre[1]);
  gl.uniform1f(U('uSpan'), state.span);
  gl.uniform1f(U('uAspect'), aspect);
  gl.uniform1f(U('mixT'), state.mixT);
  gl.uniform1f(U('oLang'), lay.lang); gl.uniform1f(U('oDiv'), lay.div);
  gl.uniform1f(U('oPop'), lay.pop); gl.uniform1f(U('oGreen'), lay.green);
  gl.uniform1f(U('oRelief'), lay.relief); gl.uniform1f(U('oDoc'), lay.doc);
  gl.uniform1f(U('oCoarse'), lay.coarse);

  const N = state.meta.tile + 2 * state.meta.skirt;
  gl.uniform1f(U('uStep'), 1 / N);

  for (let ty = ty0; ty <= ty1; ty++) {
    for (let txw = tx0; txw <= tx1; txw++) {
      const tx = ((txw % cols) + cols) % cols;
      request(L, tx, ty);
      const r = resolve(L, tx, ty);
      if (!r) continue;
      // Draw at the wrapped longitude so a view crossing the antimeridian is continuous.
      const tLon = -180 + txw * dLon;
      const tLat = 90 - ty * dLat;
      gl.uniform4f(U('uTile'), tLon, tLat, dLon, dLat);
      gl.uniform4f(U('uSrc'), r.src[0], r.src[1], r.src[2], r.src[3]);
      gl.uniform2f(U('uSrcGrid'), r.grid[0], r.grid[1]);
      // Detail only where the SOURCE texel is coarser than a screen pixel — i.e. where the
      // data has run out. Never where measured data would be overwritten by noise.
      const texelPx = (cv.width * 360 / state.span) / r.grid[0];
      gl.uniform1f(U('uDetail'), Math.max(0, Math.min(1, (texelPx - 1) / 3)));
      FIELDS.forEach((f, i) => {
        gl.activeTexture(gl.TEXTURE0 + i);
        gl.bindTexture(gl.TEXTURE_2D, r.rec.tex[f] || r.rec.tex.terrain);
        gl.uniform1i(U(['terrain', 'env', 'langC', 'langT'][i]), i);
      });
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    }
  }
  evict();
}
state.render = render;

/** Draw the rendered world, centred on one language, into a 2D canvas.
 *  Reuses the real shader rather than a second cheaper renderer, so the little map in a
 *  card is the same Earth as the big one — same relief, same biome, same language field. */
state.worldBox = function (out, lon, lat, span) {
  // A 2:1 canvas at span 360 centred on (0,0) is exactly the whole equirectangular world:
  // the crop is 360 deg wide and 360/2 = 180 deg tall. That lets the box below be placed by
  // plain arithmetic instead of by reading back the renderer's framing.
  if (!state.snapshot(out, 0, 0, 360)) return false;
  const ctx = out.getContext('2d');
  const W = out.width, H = out.height;
  const x = ((((lon + 180) % 360) + 360) % 360) / 360 * W;
  const y = (90 - lat) / 180 * H;
  const bw = Math.max(10, span / 360 * W), bh = Math.max(7, (span / 2) / 180 * H);
  ctx.lineWidth = Math.max(2, W / 220);
  ctx.strokeStyle = 'rgba(20,22,26,.85)';
  ctx.strokeRect(x - bw / 2, y - bh / 2, bw, bh);
  ctx.strokeStyle = '#e8a06a';
  ctx.lineWidth = Math.max(1, W / 420);
  ctx.strokeRect(x - bw / 2, y - bh / 2, bw, bh);
  return true;
};

state.snapshot = function (out, lon, lat, span) {
  if (!state.ready) return false;
  const c0 = state.centre.slice(), s0 = state.span;
  state.centre = [lon, lat];
  state.span = span;
  render();
  const ctx = out.getContext('2d');
  const ar = out.width / out.height;
  let sw = cv.width, sh = Math.round(cv.width / ar);
  if (sh > cv.height) { sh = cv.height; sw = Math.round(cv.height * ar); }
  ctx.drawImage(cv, (cv.width - sw) / 2, (cv.height - sh) / 2, sw, sh,
                0, 0, out.width, out.height);
  state.centre = c0; state.span = s0;
  render();
  return true;
};
state.jumpTo = (lon, lat, span) => {
  state.centre = [lon, lat]; if (span) state.span = span; render();
};

// ---------------------------------------------------------------------------------------
// CPU sampling — the readout and the cards read the same pixels the shader does
// ---------------------------------------------------------------------------------------
const probe = document.createElement('canvas');
const pctx = probe.getContext('2d', { willReadFrequently: true });
function sample(name, lon, lat) {
  // "Unknown" is a legitimate return; a fabricated one is not (rule 10). A non-finite
  // coordinate once read back as zeros, which the readout printed as a confident
  // "11000 m below sea level".
  if (!isFinite(lon) || !isFinite(lat) || !state.meta) return null;
  const w = ((((lon + 180) % 360) + 360) % 360) / 360;      // 0..1 east from -180
  const v = Math.min(0.999999, Math.max(0, (90 - lat) / 180));
  for (let l = Math.min(state.level, state.meta.maxLevel); l >= 0; l--) {
    const cols = 2 << l, rows = 1 << l;
    const tx = Math.min(cols - 1, Math.floor(w * cols));
    const ty = Math.min(rows - 1, Math.floor(v * rows));
    const rec = tiles.get(tileKey(l, tx, ty));
    if (!rec || !rec.ready || !rec.img[name]) continue;
    const T = state.meta.tile, S = state.meta.skirt;
    const px = S + Math.min(T - 1, Math.floor((w * cols - tx) * T));
    const py = S + Math.min(T - 1, Math.floor((v * rows - ty) * T));
    probe.width = 1; probe.height = 1;
    pctx.clearRect(0, 0, 1, 1);
    pctx.drawImage(rec.img[name], px, py, 1, 1, 0, 0, 1, 1);
    return pctx.getImageData(0, 0, 1, 1).data;
  }
  return null;
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
  const autonyms = r[9] || [], scripts = r[10] || [], famid = r[11];
  const FN = (state.langs && state.langs.familyNames) || {};

  // CLAUDE.md rule 11: the autonym leads, in its own script, and the reference name is
  // labelled as what it is. Glottolog's `Name` is a unique English catalogue key — "Paku
  // Karen", "San Francisco del Mar Huave" — built from an exonym plus a geographic
  // qualifier. Some of those exonyms are colonial and a few are slurs. Where no autonym is
  // recorded we say so, rather than promoting the catalogue key to a name (rule 10).
  let head, sub;
  if (autonyms.length) {
    const a = autonyms[0];
    head = '<span lang="' + esc(a[1] || '') + '">' + esc(a[0]) + '</span>';
    sub = '<div class="eyebrow" style="margin-top:3px">' + esc(r[1]) +
      ' <span style="opacity:.6">· reference name</span>' +
      (autonyms.length > 1 ? ' · also ' + autonyms.slice(1).map(n =>
        '<span lang="' + esc(n[1] || '') + '">' + esc(n[0]) + '</span>').join(', ') : '') +
      '</div>';
  } else {
    head = esc(r[1]);
    sub = '<div class="eyebrow" style="margin-top:3px">reference name · no autonym recorded</div>';
  }

  $('#cardBody').innerHTML =
    '<div class="eyebrow">language · nearest recorded point, ' + km + ' km away</div>' +
    '<h2>' + head + '</h2>' + sub +
    '<table>' +
    '<tr><td>family</td><td>' + esc(FN[famid] || famid || '—') + '</td></tr>' +
    (scripts.length ? '<tr><td>written in</td><td>' + scripts.map(esc).join(', ') + '</td></tr>' : '') +
    '<tr><td>glottocode</td><td><code>' + r[0] + '</code></td></tr>' +
    '<tr><td>ISO 639-3</td><td>' + (r[7] ? '<code>' + r[7] + '</code> <i>alias, not the key</i>' : '—') + '</td></tr>' +
    '<tr><td>vitality</td><td>' + (AES[r[6]] || 'not assessed') + '</td></tr>' +
    '<tr><td>description</td><td>' + (r[5] >= 0 ? MED[Math.min(4, r[5])] : 'unknown') + '</td></tr>' +
    '<tr><td>first attested</td><td>' + (r[8] ? r[8] : 'no date recorded') + '</td></tr>' +
    '<tr><td>biome at its point</td><td>' + (E ? (BIOMES[E[0]] || '—') : '—') + '</td></tr>' +
    (r[13] ? '<tr><td>speakers</td><td>' + r[13][0].toLocaleString() + ' <i>as of ' +
      esc(String(r[13][1])) + ', Wikidata</i></td></tr>' : '') +
    (r[14] ? '<tr><td>countries</td><td>' + esc(r[14]) + '</td></tr>' : '') +
    '</table>' +
    (r[12] ? '<p style="margin:9px 0 0;color:#cfd8d4;font-size:12.5px">' + esc(r[12]) + '</p>' : '') +
    '<div class="tier">Glottolog 5.3' +
    (autonyms.length ? ' · autonym from Wikidata' : '') +
    (r[12] ? ' · description from Wikidata' : '') + '</div>' +
    wordsHtml(r[0]) + sampleHtml(r[0]);
  $('#card').classList.remove('hidden');
}

/** ASJP's core word list for this language. Register D2b. */
function wordsHtml(gc) {
  const W = state.words && state.words.by_glottocode && state.words.by_glottocode[gc];
  if (!W) return '';
  const order = ['water', 'fire', 'sun', 'moon', 'star', 'stone', 'tree', 'leaf', 'blood',
                 'bone', 'hand', 'eye', 'ear', 'nose', 'tooth', 'tongue', 'skin', 'name',
                 'person', 'fish', 'bird', 'dog', 'night', 'die', 'come', 'see', 'drink',
                 'new', 'full', 'one', 'two'];
  const have = order.filter(k => W[k]).slice(0, 12);
  if (!have.length) return '';
  return '<div class="tier" style="margin-top:12px">' +
    '<div class="eyebrow">words</div><div class="wordsrow">' +
    have.map(k => '<span><b>' + esc(W[k]) + '</b> ' + esc(k) + '</span>').join('') +
    '</div><div class="fine">IPA — how the words sound, not how they are spelled. ASJP.</div></div>';
}

/** The UDHR in this language, in its own script and orthography. */
function sampleHtml(gc) {
  const T = state.texts && state.texts.by_glottocode && state.texts.by_glottocode[gc];
  if (!T || !T.b || !T.b.length) return '';
  const blocks = T.b.slice(0, 3).map(b =>
    '<div class="eyebrow" style="margin-top:8px">' + esc(b[0]) + '</div>' +
    '<p class="sample" lang="' + esc(T.l) + '" dir="' + esc(T.d) + '">' + esc(b[1]) + '</p>'
  ).join('');
  return '<div class="tier" style="margin-top:12px">' + blocks +
    '<div class="fine">' + esc(T.s || '') + ' script · Universal Declaration of Human ' +
    'Rights, UN translations.</div></div>';
}

/** Open a card from a glottocode — the genealogy view's way back to the ground. */
state.showCardFor = function (gc, p) {
  if (!state.langs) return;
  const r = state.langs.rows.find(x => x[0] === gc);
  const lonlat = r ? [r[2], r[3]] : (p || null);
  if (lonlat) {
    state.centre = [lonlat[0], lonlat[1]];
    state.span = Math.min(state.span, 12);
    setView('map');
    render();
    updateReadout(lonlat[0], lonlat[1]);
    showCard(lonlat[0], lonlat[1]);
  }
};

function setView(v) {
  const tree = v === 'tree';
  document.body.classList.toggle('tree', tree);
  $('#treeview').classList.toggle('hidden', !tree);
  $('#vMap').classList.toggle('on', !tree);
  $('#vTree').classList.toggle('on', tree);
  ['#leftrail', '#rightrail', '#readout'].forEach(id => {
    const e = $(id); if (e) e.style.display = tree ? 'none' : '';
  });
  if (tree && window.TREE) window.TREE.show();
}
state.setView = setView;

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
  '<div><b>grain</b> — languages with territory within 20 km</div>' +
  '<div><b>ground colour</b> — biome and measured greenness (peak NDVI)</div>' +
  '<div><b>relief</b> — lit per pixel from the elevation field</div>';

function waitTile(l, x, y) {
  return new Promise(res => {
    const rec = request(l, x, y);
    if (!rec) return res(null);
    if (rec.ready) return res(rec);
    const iv = setInterval(() => { if (rec.ready) { clearInterval(iv); res(rec); } }, 30);
    // A tile that never arrives must not hold the whole app hostage behind a spinner.
    setTimeout(() => { clearInterval(iv); res(null); }, 25000);
  });
}

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
  // The text tier (register D2). One artefact, so the whole thing is removable in one commit
  // exactly as SCOPE §12 D2 requires; if it is absent the cards simply carry no passage.
  fetch(V('data/texts.json')).then(r => r.json()).then(d => { state.texts = d; })
    .catch(() => { state.texts = null; });
  // The word tier: ASJP's core list for 6,110 languages — fourteen times the reach of the
  // UDHR passage, and for many languages the only text that exists at all.
  fetch(V('data/words.json')).then(r => r.json()).then(d => { state.words = d; })
    .catch(() => { state.words = null; });
  fetch(V('data/notable.json')).then(r => r.json()).then(d => { state.notable = d; })
    .catch(() => { state.notable = null; });
  fetch(V('data/gallery.json')).then(r => r.json()).then(d => { state.gallery = d; })
    .catch(() => { state.gallery = null; });
  fetch(V('data/typology.json')).then(r => r.json()).then(d => { state.typology = d; })
    .catch(() => { state.typology = null; });
  fetch(V('data/audio.json')).then(r => r.json()).then(d => { state.audio = d; })
    .catch(() => { state.audio = null; });
  // Level 0 is the whole world in 5 MB and it is the fallback every other level falls back
  // TO, so it is the one thing worth blocking first paint on. Everything above it streams.
  const base = [];
  for (let x = 0; x < 2; x++) base.push(waitTile(0, x, 0));
  await Promise.all(base);
  state.ready = true;
  render();
  $('#loading').style.display = 'none';
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
  '<p><b>We measured it, and it changed the claim.</b> An earlier version of this project ' +
  'asserted terrain was "most of the explanation". It is not. Across 7,672 spoken-L1 ' +
  'languages and 4,600 land cells, rank correlation with language density:</p>' +
  '<table style="width:100%;margin:6px 0"><tbody>' +
  '<tr><td>growing season (months ≥ 5 °C)</td><td style="text-align:right"><b>+0.470</b></td></tr>' +
  '<tr><td>absolute latitude</td><td style="text-align:right"><b>−0.527</b></td></tr>' +
  '<tr><td>peak greenness (NDVI)</td><td style="text-align:right"><b>+0.347</b></td></tr>' +
  '<tr><td>terrain ruggedness</td><td style="text-align:right"><b>+0.155</b></td></tr>' +
  '</tbody></table>' +
  '<p>Climate beats terrain by roughly three to one, which is why this map paints greenness ' +
  'and not just relief. But the honest caveat is on our own side of the argument: <b>holding ' +
  'latitude constant, growing season adds nothing</b> (−0.091), while holding growing season ' +
  'constant still leaves latitude at −0.284. Growing season is largely what latitude was ' +
  'standing for. A Poisson count model with land area as an offset says the same: latitude ' +
  'alone explains 25.6% of deviance, growing season 15.4%, ruggedness 7.8%, all three plus ' +
  'greenness 39.4%. Poisson\'s dispersion was 8–20, so its intervals would have been about ' +
  'four times too narrow; refitting as a <b>negative binomial</b> gives intervals that mean ' +
  'something, and every term survives: growing season <b>+1.67 ± 0.05</b>, latitude ' +
  '<b>−1.48 ± 0.04</b>, ruggedness <b>+0.48 ± 0.02</b>, and all three plus greenness explain ' +
  '<b>49%</b> of deviance.</p>' +
  '<p><b>And those intervals were still too narrow.</b> Neighbouring cells are not independent ' +
  'observations — Moran\'s I on the model\'s own residuals is <b>+0.386</b> — so a spatial ' +
  'block bootstrap was run, resampling 10° blocks so that neighbours stay together. It widens ' +
  'every standard error by about <b>three times</b>, and worst of all for latitude (3.8×), ' +
  'which is smooth across the whole planet and gained most from the pretence. All four ' +
  'predictors still exclude zero. Climate over terrain is the robust finding; the exact rank ' +
  'of latitude against growing season is not, and is not claimed here.</p>' +
  '<p>Terrain is small but it is <i>real</i>, and it survives changing the definition: ' +
  'relief per kilometre gives +0.192 where standard deviation of elevation gives +0.155, ' +
  'same sign, same order. In <b>Papunesia (+0.024)</b> and <b>Africa (+0.006)</b> it is ' +
  'indistinguishable from zero.</p>' +
  '<h3>What it does not know</h3><ul>' +
  '<li><b>Real polygons exist for 62.5% of living languages.</b> Turn on "Mark land with no ' +
  'polygon": absence of colour is absence of data, not absence of language.</li>' +
  '<li><b>Autonyms cover ' + (state.langs ? Math.round(state.langs.rows.filter(r => (r[9]||[]).length).length / state.langs.rows.length * 100) : '—') +
  '% of languages.</b> Where a native label exists (Wikidata P1705, CC0) the card leads with ' +
  'it, in its own script. Where none does, the card shows Glottolog\'s reference name and ' +
  'says that is what it is. A reference name is an English catalogue key — "Paku Karen", ' +
  '"San Francisco del Mar Huave" — and some of the exonyms inside them are colonial.</li>' +
  '<li><b>No speaker counts.</b> We require (value, year, source); the catalogue carries none.</li>' +
  '<li><b>The earlier snapshot has no year.</b> "Before contact" is a per-region state — contact ' +
  'ranges from the 1490s to the twentieth century, and never happened in some places.</li>' +
  '<li><b>The deep past is nine languages.</b> Of ~217 with an attestation date, 82 have a mapped ' +
  'area and nine are pre-Common-Era. There is no deep-time surface here yet.</li>' +
  '<li><b>Population is floored at 1975</b>, because the only deep-time gridded population ' +
  'dataset is NonCommercial. This build uses the 2020 epoch.</li>' +
  '<li><b>"Languages here" counts territories within about 20 km</b>, not overlapping ' +
  'polygons. An earlier build counted overlaps, which measured how many SOURCE DATASETS ' +
  'covered a place: it read 1 across the New Guinea highlands, the densest linguistic region ' +
  'on Earth, and 43 in India — where 22 official languages were stacked on one cell. The ' +
  'measured maximum now is <b>' + (s.c ? s.c.max_div : '—') + '</b> today and <b>' +
  (s.t ? s.t.max_div : '—') + '</b> before contact.</li>' +
  '<li><b>Official languages are excluded.</b> One source mapped 158 country-shaped polygons ' +
  'of state-official languages. That is a map of policy, not of where anyone speaks: it put ' +
  'French across Gabon and inflated every count. The other 25 datasets are real language ' +
  'areas.</li>' +
  '<li><b>The grid is 16384 × 8192 — 2.4 km at the equator</b>, streamed as a four-level tile ' +
  'pyramid. That is 76% of the elevation source\'s own resolution, so zooming past it shows ' +
  'procedural texture, never invented landforms: the relief you see is measured.</li>' +
  '<li><b>No global continuous linguistic surface has been built before.</b> The method here is ' +
  'ours, and so is the method risk.</li></ul>' +
  '<h3>How the count works</h3>' +
  '<p>This build uses <b>Glottolog 5.3</b>\'s spoken-L1 languages: <b>7,674</b>, of which 7,672 ' +
  'have coordinates. Other authorities count differently — about 7,100, or 7,927 ISO codes — ' +
  'because the language/dialect line is drawn for non-linguistic reasons as often as linguistic ' +
  'ones. There is no single correct number and this atlas does not pretend there is.</p>' +
  '<h3>The genealogy</h3>' +
  '<p>The map answers <i>where</i>. <b>GENEALOGY</b>, top left, answers <i>where from</i>: ' +
  'Glottolog\'s full classification — <b>429</b> top-level groups, of which <b>183 are ' +
  'isolates</b> with no known relatives, holding <b>8,618</b> languages and <b>13,706</b> ' +
  'dialects. <b>1,239 are extinct</b> and <b>2,573</b> are endangered. Click any language to ' +
  'come back to the ground it was spoken on.</p>' +
  '<p>It is drawn as a <b>tree</b>, not a list: branch thickness is the number of <i>living</i> ' +
  'descendants and distance from the left is depth of descent, so a family that is mostly ' +
  'extinct visibly thins toward its tips before you read a single name. Hollow tips are ' +
  'extinct languages.</p>' +
  '<p><b>Only 19 families have a date.</b> Root ages come from published Bayesian phylogenies ' +
  '(Phlorest, CC-BY) and are stated for the family as a whole — the internal splits are not ' +
  'dated and are not drawn as if they were. Eleven of thirty datasets were rejected: four are ' +
  'scaled in substitutions rather than years, and one gives a root age of <b>613,594 years</b> ' +
  'for a language family. Where there is no date the view says there is no date.</p>' +
  '<h3>The gallery</h3>' +
  '<p>Notable languages carry an object: a Hittite tablet from Boğazköy, the Codex ' +
  'Argenteus, a Linear B inventory from Pylos, the Rosetta Stone. Every image is admitted ' +
  'by machine on the licence Wikimedia Commons reports for that individual file — public ' +
  'domain, CC0, CC-BY and CC-BY-SA pass — and each is shown beside its own title, licence ' +
  'and author. Some are ShareAlike; they are reproduced unmodified, which is what that ' +
  'licence asks. The age of the object is never the test, because a photograph of a ' +
  'thousand-year-old manuscript can be new.</p>' +
  '<h3>The words</h3>' +
  '<p>Every card and every exhibit carries <b>ASJP\'s core word list</b> where one exists — ' +
  '<i>water, fire, sun, blood, hand, name, two</i> — for <b>6,110 languages</b>, fourteen ' +
  'times the reach of the passage below, and for many of them the only text that exists at ' +
  'all. The forms are in <b>ASJPcode</b>, a deliberately coarse ASCII transcription built for ' +
  'comparison across thousands of languages; it is not any language\'s own orthography and ' +
  'is never presented as one. ASJP (Wichmann, Holman &amp; Brown, eds.), CC-BY-4.0.</p>' +
  '<h3>The text</h3>' +
  '<p>Cards carry <b>Article 1 of the Universal Declaration of Human Rights</b> in the ' +
  'language itself, in its own script, where a translation exists: <b>432 languages, 38 ' +
  'scripts</b>. <b>That corpus carries no licence statement</b> — not a permissive one, none ' +
  'at all. It ships under a recorded decision, one paragraph per language, with the source ' +
  'file named on every card, and it can be removed in a single commit. If you hold rights in ' +
  'one of these translations and want it gone, the takedown address is on the card.</p>' +
  '<h3>How much of the ground is data</h3>' + coverageHtml() +
  '<h3>Sources</h3>' + sourcesHtml() +
  '<p class="fine">Elevation is encoded 16-bit linear over −11000…+9000 m. That was measured, not ' +
  'inherited: an 8-bit signed-square-root encoding tuned for sea level would have created relief ' +
  'steps of 1.95° against a true median slope of 1.34° in the New Guinea highlands — steeper than ' +
  'the terrain it was drawing.</p>';
}

$('#vMap').addEventListener('click', () => setView('map'));
$('#vTree').addEventListener('click', () => setView('tree'));

boot().catch(e => {
  $('#loading').textContent = 'Failed to load: ' + e.message;
  console.error(e);
});
