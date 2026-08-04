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
}
