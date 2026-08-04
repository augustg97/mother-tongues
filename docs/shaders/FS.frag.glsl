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
}
