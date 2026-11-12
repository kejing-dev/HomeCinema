// Home Cinema frame lab, revision 4 ("ambient"): wall treatments around the player, real materials, low saturation.
// ?style=<id>&mode=final|cut|view|legacy   final: export GLB + 4 renders + masks; cut: transparent preview cut-outs;
// legacy: load out/<style>.glb from revision 3 and render only the peripheral view + masks (for comparison).
import * as THREE from 'three';
import { GLTFExporter } from 'three/addons/exporters/GLTFExporter.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import * as BGU from 'three/addons/utils/BufferGeometryUtils.js';

const q = new URLSearchParams(location.search);
const STYLE = q.get('style') || 'walnut';
const MODE = q.get('mode') || 'view';
const W = 1600, H = 1000;
const OW = 1.64, OH = 0.94; // sight edge of every frame; the player (1.6 x 0.9 at default scale) sits inside

// ---------- helpers
let seed = 11;
const rnd = () => { seed = (seed * 16807) % 2147483647; return (seed - 1) / 2147483646; };
function hash2(x, y) { const s = Math.sin(x * 127.1 + y * 311.7) * 43758.5453; return s - Math.floor(s); }
function vn(x, y) {
  const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi, u = xf * xf * (3 - 2 * xf), v = yf * yf * (3 - 2 * yf);
  return (hash2(xi, yi) * (1 - u) + hash2(xi + 1, yi) * u) * (1 - v) + (hash2(xi, yi + 1) * (1 - u) + hash2(xi + 1, yi + 1) * u) * v;
}
const fbm = (x, y) => vn(x, y) * .5 + vn(x * 2.03, y * 2.03) * .25 + vn(x * 4.1, y * 4.1) * .15 + vn(x * 8.3, y * 8.3) * .1;
function rrShape(w, h, r) {
  const s = new THREE.Shape(), x = -w / 2, y = -h / 2;
  if (r <= 0) { s.moveTo(x, y); s.lineTo(x + w, y); s.lineTo(x + w, y + h); s.lineTo(x, y + h); s.lineTo(x, y); return s; }
  s.moveTo(x + r, y); s.lineTo(x + w - r, y); s.quadraticCurveTo(x + w, y, x + w, y + r); s.lineTo(x + w, y + h - r);
  s.quadraticCurveTo(x + w, y + h, x + w - r, y + h); s.lineTo(x + r, y + h); s.quadraticCurveTo(x, y + h, x, y + h - r);
  s.lineTo(x, y + r); s.quadraticCurveTo(x, y, x + r, y); return s;
}
// rectangular frame with a hole, real depth and a small bevel/chamfer (metres)
function frameGeo(ow, oh, iw, ih, depth, bevel = .004, r = 0, segs = 1) {
  const s = rrShape(ow, oh, r); s.holes.push(rrShape(iw, ih, r * .5));
  const g = new THREE.ExtrudeGeometry(s, { depth: Math.max(.001, depth - 2 * bevel), bevelEnabled: bevel > 0, bevelSize: bevel, bevelThickness: bevel, bevelSegments: segs, curveSegments: 4 });
  g.translate(0, 0, -depth / 2); return boxUV(g);
}
function box(w, h, d, bevel = .003) { // bevelled box via extrude, centred
  const g = new THREE.ExtrudeGeometry(rrShape(w - 2 * bevel, h - 2 * bevel, 0), { depth: d - 2 * bevel, bevelEnabled: true, bevelSize: bevel, bevelThickness: bevel, bevelSegments: 1 });
  g.translate(0, 0, -(d - 2 * bevel) / 2); return boxUV(g);
}
// wooden/metal frame built from four members (butt joints) so the grain runs along each member
function memberFrame(ow, oh, iw, ih, depth, bevel = .004) {
  const sw = (ow - iw) / 2, sh = (oh - ih) / 2, parts = [];
  parts.push(box(ow, sh, depth, bevel).translate(0, (oh - sh) / 2, 0), box(ow, sh, depth, bevel).translate(0, -(oh - sh) / 2, 0));
  for (const sx of [-1, 1]) parts.push(box(ih, sw, depth, bevel).rotateZ(Math.PI / 2).translate(sx * (ow - sw) / 2, 0, 0));
  return merge(parts);
}
// planar UVs in metres by dominant normal axis, so textures keep a real-world scale on every part
function boxUV(g, k = 1) {
  g = g.index ? g.toNonIndexed() : g; g.computeVertexNormals();
  const p = g.attributes.position, n = g.attributes.normal, uv = new Float32Array(p.count * 2);
  for (let i = 0; i < p.count; i++) {
    const ax = Math.abs(n.getX(i)), ay = Math.abs(n.getY(i)), az = Math.abs(n.getZ(i));
    let u, v; if (az >= ax && az >= ay) { u = p.getX(i); v = p.getY(i); } else if (ax >= ay) { u = p.getZ(i); v = p.getY(i); } else { u = p.getX(i); v = p.getZ(i); }
    uv[i * 2] = u * k; uv[i * 2 + 1] = v * k;
  }
  g.setAttribute('uv', new THREE.BufferAttribute(uv, 2)); return g;
}
function merge(list) { return BGU.mergeGeometries(list.map((g) => (g.index ? g.toNonIndexed() : g)), false); }
function mesh(g, m, name, pos = [0, 0, 0], rot = [0, 0, 0]) { const o = new THREE.Mesh(g, m); o.name = name; o.position.set(...pos); o.rotation.set(...rot); return o; }
// canvas texture helpers. Height canvases become tangent-space normal maps.
function cnv(n, draw) { const c = document.createElement('canvas'); c.width = c.height = n; draw(c.getContext('2d'), n); return c; }
function tex(c, srgb = true, rep = 1) { const t = new THREE.CanvasTexture(c); t.colorSpace = srgb ? THREE.SRGBColorSpace : THREE.NoColorSpace; t.wrapS = t.wrapT = THREE.RepeatWrapping; t.anisotropy = 4; return t; }
function heightToNormal(hc, strength = 2) {
  const n = hc.width, src = hc.getContext('2d').getImageData(0, 0, n, n).data;
  return cnv(n, (c) => {
    const im = c.createImageData(n, n), h = (x, y) => src[(((y + n) % n) * n + ((x + n) % n)) * 4] / 255;
    for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) {
      const dx = (h(x + 1, y) - h(x - 1, y)) * strength, dy = (h(x, y + 1) - h(x, y - 1)) * strength;
      const l = Math.hypot(dx, dy, 1), i = (y * n + x) * 4;
      im.data[i] = (-dx / l * .5 + .5) * 255; im.data[i + 1] = (dy / l * .5 + .5) * 255; im.data[i + 2] = (1 / l * .5 + .5) * 255; im.data[i + 3] = 255;
    }
    c.putImageData(im, 0, 0);
  });
}
function pix(n, f) { return cnv(n, (c) => { const im = c.createImageData(n, n); for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) { const [r, g, b] = f(x / n, y / n), i = (y * n + x) * 4; im.data[i] = r; im.data[i + 1] = g; im.data[i + 2] = b; im.data[i + 3] = 255; } c.putImageData(im, 0, 0); }); }
const mix = (a, b, t) => a.map((v, i) => v + (b[i] - v) * t);
// materials: one texture set per surface, 512 px, tile = metres per texture repeat
function pbr(name, { color = [128, 128, 128], f, hf, tile = 1, rough = .85, metal = 0, normal = 1.5, emissive, emissiveMap } = {}) {
  const o = { roughness: rough, metalness: metal };
  if (f) { o.map = tex(pix(512, f)); o.map.repeat.set(1 / tile, 1 / tile); } else o.color = new THREE.Color(`rgb(${color.join(',')})`);
  if (hf) { o.normalMap = tex(heightToNormal(pix(512, (x, y) => { const v = hf(x, y) * 255; return [v, v, v]; }), normal), false); o.normalMap.repeat.set(1 / tile, 1 / tile); }
  if (emissive) { o.emissive = new THREE.Color(emissive); o.emissiveIntensity = 1; if (emissiveMap) o.emissiveMap = emissiveMap; }
  const m = new THREE.MeshStandardMaterial(o); m.name = name; return m;
}
// UVs are in metres; texture.repeat is not reliable after export, so bake the tile into the UVs instead
function tileUV(g, tile) { const uv = g.attributes.uv; for (let i = 0; i < uv.count; i++) uv.setXY(i, uv.getX(i) / tile, uv.getY(i) / tile); return g; }
function m2(mat) { for (const k of ['map', 'normalMap']) if (mat[k]) mat[k].repeat.set(1, 1); return mat; }
// a soft light wash baked as an emissive map over a whole wall panel (UV 0..1 across the panel); dims with the show
function washMap(kind) {
  return tex(pix(256, (x, y) => {
    let v;
    if (kind === 'top') v = Math.pow(1 - y, 2.2) * .9 + .05;
    else { // bias: glow hugging the opening, fading outward
      const dx = Math.max(0, Math.abs(x - .5) - .27) / .23, dy = Math.max(0, Math.abs(y - .5) - .26) / .24;
      v = Math.exp(-3.2 * Math.hypot(dx, dy)) * .9;
    }
    v = Math.min(1, v); return [v * 255, v * 255, v * 255];
  }));
}
function panelUV01(g, w, h) { const p = g.attributes.position, uv = g.attributes.uv; const uv2 = new Float32Array(p.count * 2); for (let i = 0; i < p.count; i++) { uv2[i * 2] = p.getX(i) / w + .5; uv2[i * 2 + 1] = p.getY(i) / h + .5; } g.setAttribute('uv', new THREE.BufferAttribute(uv2, 2)); return g; }
async function prop(name, height, pos, ry = 0) {
  const gltf = await new GLTFLoader().loadAsync('props/' + name + '-lo.glb');
  let m = null; gltf.scene.traverse((o) => { if (o.isMesh && !m) m = o; });
  const g = m.geometry.clone(); g.computeBoundingBox();
  const bb = g.boundingBox, s = height / (bb.max.y - bb.min.y);
  g.translate(-(bb.max.x + bb.min.x) / 2, -bb.min.y, -(bb.max.z + bb.min.z) / 2); g.scale(s, s, s); g.rotateY(ry);
  const mat = m.material; mat.name = 'prop_' + name; mat.roughness = Math.max(mat.roughness ?? .8, .7); mat.metalness = 0;
  return mesh(g, mat, 'prop-' + name, pos);
}

// ---------- texture recipes (colours deliberately low-chroma, albedo 0.08-0.45)
const T = {
  walnut: (x, y) => { const g = fbm(x * 1.5, y * 26 + fbm(x * 2, y * 2) * 5) * .8 + fbm(x * 20, y * 140) * .2; return mix([50, 37, 28], [82, 61, 45], g); },
  walnutH: (x, y) => fbm(x * 1.5, y * 26 + fbm(x * 2, y * 2) * 5) * .5 + fbm(x * 20, y * 140) * .5,
  plaster: (x, y) => { const g = fbm(x * 5, y * 5) * .7 + fbm(x * 30, y * 30) * .3; return mix([48, 46, 43], [66, 63, 59], g); },
  plasterH: (x, y) => fbm(x * 6, y * 6) * .5 + fbm(x * 40, y * 40) * .2,
  linen: (x, y) => { const w = (Math.sin(x * 512 * Math.PI / 2) * Math.sin(y * 512 * Math.PI / 2)) * .5 + .5, g = fbm(x * 60, y * 4) * .5 + fbm(x * 4, y * 60) * .5; return mix([86, 81, 74], [106, 100, 91], g * .7 + w * .3); },
  linenH: (x, y) => (Math.abs(Math.sin(x * 256 * Math.PI)) * .5 + Math.abs(Math.sin(y * 256 * Math.PI)) * .5) * .6 + fbm(x * 60, y * 4) * .4,
  linenDark: (x, y) => { const g = fbm(x * 60, y * 4) * .5 + fbm(x * 4, y * 60) * .5; return mix([30, 28, 27], [44, 41, 39], g); },
  concrete: (x, y) => { // 1 tile = 1.2 m: four 0.3 m boards, tie holes at 0.6 m
    let g = fbm(x * 8, y * 8) * .6 + fbm(x * 50, y * 50) * .25 + fbm(x * 3, y * 30) * .15;
    const by = (y * 4) % 1; if (by < .012 || by > .988) g -= .25;
    for (const [hx, hy] of [[.25, .25], [.75, .25], [.25, .75], [.75, .75]]) { const d = Math.hypot(x - hx, y - hy); if (d < .011) g -= .5; else if (d < .02) g -= .12; }
    return mix([50, 49, 47], [76, 74, 71], Math.max(0, g));
  },
  concreteH: (x, y) => { let g = fbm(x * 8, y * 8) * .4 + fbm(x * 50, y * 50) * .3 + fbm(x * 3, y * 30) * .3; const by = (y * 4) % 1; if (by < .012 || by > .988) g -= .5; for (const [hx, hy] of [[.25, .25], [.75, .25], [.25, .75], [.75, .75]]) if (Math.hypot(x - hx, y - hy) < .011) g -= .8; return Math.max(0, g); },
  oakSmoked: (x, y) => { const g = fbm(x * 8, y * 60) * .7 + fbm(x * 40, y * 200) * .3; return mix([44, 34, 26], [72, 57, 43], g); },
  oakSmokedH: (x, y) => fbm(x * 8, y * 60) * .5 + fbm(x * 40, y * 200) * .5,
  oakLight: (x, y) => { const g = fbm(x * 6, y * 50) * .7 + fbm(x * 30, y * 160) * .3; return mix([132, 108, 80], [168, 142, 108], g); },
  felt: (x, y) => { const g = fbm(x * 90, y * 90) * .6 + fbm(x * 8, y * 8) * .4; return mix([22, 21, 20], [32, 31, 30], g); },
  feltH: (x, y) => fbm(x * 90, y * 90),
  bronze: (x, y) => { const g = fbm(x * 12, y * 12) * .7 + fbm(x * 80, y * 3) * .3; return mix([70, 56, 42], [104, 84, 62], g); },
};

// ---------- styles: each returns { group, light (wash colour), ambience, prop list }
const STYLES = {};

// 1. Walnut gallery: charcoal limewash wall, walnut shadow-box frame, linen slip, brass hairline, low walnut ledge
STYLES.walnut = async () => {
  const g = new THREE.Group();
  const pw = 3.1, ph = 1.85;
  const wallG = panelUV01(frameGeo(pw, ph, 1.9, 1.2, .03, .002), pw, ph);
  const wall = pbr('walnut_limewash', { f: T.plaster, hf: T.plasterH, rough: .97, normal: 1.2, emissive: 0xffd7b0, emissiveMap: washMap('top') });
  wall.emissiveIntensity = .22; wall.name = 'emit_walnut_limewash';
  g.add(mesh(wallG, wall, 'wall-panel', [0, 0, -.08]));
  const wal = pbr('walnut_wood', { f: T.walnut, hf: T.walnutH, rough: .62, normal: 1 });
  g.add(mesh(tileUV(memberFrame(2.04, 1.34, 1.78, 1.08, .1, .008), .9), wal, 'frame', [0, 0, -.01]));
  g.add(mesh(tileUV(frameGeo(1.8, 1.1, OW, OH, .03, .003), .5), pbr('walnut_linen_slip', { f: (x, y) => T.linen(x, y).map((v) => v * .78), hf: T.linenH, rough: .95, normal: 2 }), 'slip', [0, 0, -.04]));
  g.add(mesh(frameGeo(OW + .012, OH + .012, OW, OH, .012, .001), pbr('walnut_brass', { color: [120, 100, 72], rough: .5, metal: 1 }), 'fillet', [0, 0, -.022]));
  g.add(mesh(tileUV(box(2.9, .035, .2, .004), .9), wal, 'ledge', [0, -.84, .05]));
  g.add(await prop('vase', .42, [-1.2, -.8225, .06]));
  g.add(await prop('books', .13, [1.12, -.8225, .06], .25));
  return { group: g, light: 0xffd7b0, ambience: 'Quiet room tone, a far-off clock' };
};

// 2. Béton: board-formed concrete wall, deep chamfered reveal, concrete stub shelf with a travertine sculpture
STYLES.beton = async () => {
  const g = new THREE.Group();
  const pw = 3.1, ph = 1.85;
  const conc = pbr('beton_concrete', { f: T.concrete, hf: T.concreteH, rough: .93, normal: 2.2 });
  const wallG = tileUV(frameGeo(pw, ph, 1.9, 1.2, .04, .003), 1.2);
  const wallM = conc.clone(); wallM.name = 'emit_beton_wall'; wallM.emissive = new THREE.Color(0xf3e2cc); wallM.emissiveIntensity = .2;
  // the wash needs panel-space UVs, the concrete needs metre UVs: give the wall a second UV set for the emissive map
  wallG.setAttribute('uv1', panelUV01(wallG.clone(), pw, ph).attributes.uv);
  wallM.emissiveMap = washMap('top'); wallM.emissiveMap.channel = 1;
  g.add(mesh(wallG, wallM, 'wall-panel', [0, 0, -.08]));
  // reveal: a 12 cm deep concrete return with a 2 cm chamfer, like a window cut into a cast wall
  g.add(mesh(tileUV(frameGeo(1.92, 1.22, OW, OH, .14, .02, 0, 1), 1.2), conc, 'reveal', [0, 0, -.03]));
  g.add(mesh(tileUV(box(.56, .07, .26, .01), 1.2), conc, 'shelf', [1.22, -.66, .06]));
  g.add(await prop('travertine', .27, [1.22, -.625, .06], -.4));
  return { group: g, light: 0xf3e2cc, ambience: 'Soft rain on a skylight' };
};

// 3. Linen acoustic: fabric-wrapped acoustic tiles, light oak trim, oak ledge with a linen lamp and books
STYLES.linen = async () => {
  const g = new THREE.Group();
  const lin = pbr('linen_fabric', { f: (x, y) => T.linen(x, y).map((v) => v * .7), hf: T.linenH, rough: .97, normal: 2.4 });
  const tiles = [], tw = .5, th = .45, gap = .01, cols = 6, rows = 4;
  for (let i = 0; i < cols; i++) for (let j = 0; j < rows; j++) {
    const x = (i - (cols - 1) / 2) * (tw + gap), y = (j - (rows - 1) / 2) * (th + gap) + .02;
    // full tiles outside the opening; tiles crossing it are cut to an L-free strip above/below/side
    const x0 = x - tw / 2, x1 = x + tw / 2, y0 = y - th / 2, y1 = y + th / 2, hx = .9, hy = .53;
    if (x1 > -hx && x0 < hx && y1 > -hy && y0 < hy) {
      if (y0 >= -hy && y1 <= hy) continue; // tile fully inside the opening band
      const ny0 = y0 < -hy ? y0 : hy, ny1 = y0 < -hy ? -hy : y1, h2 = ny1 - ny0;
      if (h2 > .06) tiles.push(box(tw, h2 - gap, .045, .006).translate(x, (ny0 + ny1) / 2, 0));
      continue;
    }
    tiles.push(box(tw, th, .045, .006).translate(x, y, 0));
  }
  g.add(mesh(tileUV(merge(tiles), .35), lin, 'acoustic-tiles', [0, 0, -.06]));
  g.add(mesh(new THREE.PlaneGeometry(3.1, 1.92), pbr('linen_backing', { color: [24, 23, 22], rough: 1 }), 'backing', [0, .02, -.085]));
  const oak = pbr('linen_walnut', { f: T.walnut, hf: T.walnutH, rough: .62 });
  g.add(mesh(tileUV(memberFrame(1.8, 1.1, OW, OH, .06, .004), .9), oak, 'trim', [0, 0, -.02]));
  // warm LED line tucked under the top of the trim, washing down the fabric only a little
  const led = new THREE.MeshStandardMaterial({ color: 0x000000, emissive: 0xffd9b8, emissiveIntensity: .55, roughness: .5 }); led.name = 'emit_linen_led';
  g.add(mesh(new THREE.BoxGeometry(1.6, .006, .006), led, 'led', [0, .556, .012]));
  g.add(mesh(tileUV(box(.7, .03, .2, .004), .9), oak, 'ledge-l', [-1.22, -.72, .04]));
  g.add(mesh(tileUV(box(.6, .03, .2, .004), .9), oak, 'ledge-r', [1.2, -.72, .04]));
  g.add(await prop('lamp', .4, [-1.26, -.705, .05]));
  g.add(await prop('books', .1, [1.18, -.705, .05], -.2));
  return { group: g, light: 0xffd9b8, ambience: 'Fireplace crackle, very low' };
};

// 4. Smoked oak slats on black felt, matte black steel sight frame, bias light hugging the opening
STYLES.slats = async () => {
  const g = new THREE.Group();
  const pw = 3.1, ph = 1.85;
  const feltG = panelUV01(frameGeo(pw, ph, 1.7, 1.0, .02, .001), pw, ph);
  const felt = pbr('slats_felt', { f: T.felt, rough: 1 }); felt.name = 'emit_slats_felt'; felt.emissive = new THREE.Color(0xe9ecef); felt.emissiveMap = washMap('bias'); felt.emissiveIntensity = .14;
  g.add(mesh(feltG, felt, 'felt', [0, 0, -.09]));
  const sl = [], sw = .034, pitch = .068, n = Math.floor(pw / pitch);
  for (let i = 0; i < n; i++) {
    const x = (i - (n - 1) / 2) * pitch;
    if (Math.abs(x) + sw / 2 < .86) { // above and below the opening
      sl.push(box(.4, sw, .026, .002).rotateZ(Math.PI / 2).translate(x, .725, 0), box(.4, sw, .026, .002).rotateZ(Math.PI / 2).translate(x, -.725, 0));
    } else sl.push(box(ph, sw, .026, .002).rotateZ(Math.PI / 2).translate(x, 0, 0));
  }
  g.add(mesh(tileUV(merge(sl), .8), pbr('slats_oak', { f: T.oakSmoked, hf: T.oakSmokedH, rough: .7, normal: 1.2 }), 'slats', [0, 0, -.065]));
  g.add(mesh(frameGeo(1.72, 1.02, OW, OH, .045, .003), pbr('slats_steel', { color: [26, 26, 27], rough: .55, metal: .9 }), 'steel', [0, 0, -.03]));
  g.add(mesh(tileUV(box(.5, .028, .18, .004), .8), pbr('slats_oak2', { f: T.oakSmoked, rough: .7 }), 'shelf', [1.22, -.62, -.01]));
  g.add(await prop('vase', .36, [1.22, -.606, -.01]));
  return { group: g, light: 0xe9ecef, ambience: 'Distant city at night, muffled' };
};

// 5. Bronze hairline: a museum mat in black linen and a 3 cm darkened-bronze frame. Nothing else.
STYLES.bronze = async () => {
  const g = new THREE.Group();
  const mw = 2.5, mh = 1.55;
  const matG = panelUV01(frameGeo(mw, mh, OW, OH, .02, .002), mw, mh);
  const matM = pbr('bronze_mat', { f: T.linenDark, rough: .98 }); matM.name = 'emit_bronze_mat'; matM.emissive = new THREE.Color(0xf0dcc4); matM.emissiveMap = washMap('bias'); matM.emissiveIntensity = .1;
  g.add(mesh(matG, matM, 'mat', [0, 0, -.05]));
  const br = pbr('bronze_metal', { f: T.bronze, rough: .48, metal: 1 });
  g.add(mesh(tileUV(frameGeo(mw + .06, mh + .06, mw - .004, mh - .004, .05, .004, 0, 2), .6), br, 'frame', [0, 0, -.035]));
  g.add(mesh(tileUV(frameGeo(OW + .016, OH + .016, OW, OH, .03, .002), .6), br, 'fillet', [0, 0, -.03]));
  return { group: g, light: 0xf0dcc4, ambience: 'None (silence)' };
};

// ---------- scene: a plain, normally lit living room stands in for passthrough (Home Cinema cannot dim it)
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true, alpha: true });
renderer.setSize(W, H); renderer.setPixelRatio(1);
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.0;
renderer.outputColorSpace = THREE.SRGBColorSpace;
document.body.appendChild(renderer.domElement);
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x8c857c);
scene.environment = new THREE.PMREMGenerator(renderer).fromScene(new RoomEnvironment(), .04).texture;
scene.environmentIntensity = .55;
scene.add(new THREE.HemisphereLight(0xfff6ea, 0x5c4f44, .45));
const key = new THREE.DirectionalLight(0xfff1e0, 1.4); key.position.set(-2.5, 3, 3.5); scene.add(key);
const wallTex = tex(pix(256, (x, y) => mix([168, 160, 150], [180, 173, 163], fbm(x * 6, y * 6))));
const wall = mesh(new THREE.PlaneGeometry(14, 7), new THREE.MeshStandardMaterial({ map: wallTex, roughness: 1 }), 'room-wall', [0, 1.2, -.6]);
const floorTex = tex(pix(256, (x, y) => mix([104, 82, 62], [128, 102, 78], fbm(x * 2, y * 30))));
const floor = mesh(new THREE.PlaneGeometry(14, 8), new THREE.MeshStandardMaterial({ map: floorTex, roughness: .8 }), 'room-floor', [0, -1.3, 2], [-Math.PI / 2, 0, 0]);
const sofa = mesh(new THREE.BoxGeometry(2.4, .5, .9), new THREE.MeshStandardMaterial({ color: 0x6b6f72, roughness: .95 }), 'room-sofa', [-3.4, -1.05, .8]);
scene.add(wall, floor, sofa);
// the other app's player window (not ours): a bright, saturated film still
const playerTex = tex(cnv(1024, (c, n) => {
  const w = n, h = n * 9 / 16; c.canvas.height = h;
  const gr = c.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, '#3a6ea8'); gr.addColorStop(.5, '#f0a05e'); gr.addColorStop(1, '#3a2a36'); c.fillStyle = gr; c.fillRect(0, 0, w, h);
  c.fillStyle = '#ffe2a0'; c.beginPath(); c.arc(w * .63, h * .52, 52, 0, 7); c.fill();
  c.fillStyle = '#20202c'; c.beginPath(); c.moveTo(0, h); c.bezierCurveTo(w * .3, h * .55, w * .6, h * .8, w, h * .62); c.lineTo(w, h); c.fill();
  c.fillStyle = 'rgba(230,230,230,.85)'; c.beginPath(); c.roundRect(w * .22, h - 58, w * .56, 36, 18); c.fill();
  c.fillStyle = '#333'; c.fillRect(w * .32, h - 42, w * .36, 4); c.fillStyle = '#111'; c.fillRect(w * .32, h - 42, w * .14, 4);
}));
// the user scales the player to sit in the opening with about 2 cm to spare on each side
const pg = new THREE.ShapeGeometry(rrShape(1.6, .9, .04), 6);
{ const p = pg.attributes.position, uv = pg.attributes.uv; for (let i = 0; i < p.count; i++) uv.setXY(i, p.getX(i) / 1.6 + .5, p.getY(i) / .9 + .5); }
const player = mesh(pg, new THREE.MeshBasicMaterial({ map: playerTex, toneMapped: false }), 'other-app-player', [0, 0, .0]);
scene.add(player);
const cam = new THREE.PerspectiveCamera(36, W / H, .05, 50);

async function post(name, body) { await fetch('/save?name=' + encodeURIComponent(name), { method: 'POST', body }); }
const png = () => new Promise((r) => renderer.domElement.toBlob(r, 'image/png'));
function stats(group) {
  let tris = 0; const mats = new Set(), texs = [];
  group.traverse((o) => { if (!o.isMesh) return; const gg = o.geometry; tris += (gg.index ? gg.index.count : gg.attributes.position.count) / 3; if (!mats.has(o.material.name)) { mats.add(o.material.name); for (const k of ['map', 'normalMap', 'emissiveMap']) if (o.material[k]) texs.push(o.material[k].image.width + 'x' + o.material[k].image.height); } });
  return { tris: Math.round(tris), materials: [...mats], textures: texs };
}
// front / angled / detail as before, plus "peripheral": seated eye 2.3 m back, ~100 deg horizontal FOV like the headset,
// eyes on the player (1.5 m wide at 1.45 m, about 55 deg), so the frame lands in the outer part of the view. Rendered in the Showing state.
const SHOTS = { front: [[0, .02, 3.9], [0, 0, 0], 36], angled: [[2.6, .45, 2.9], [0, -.05, 0], 36], detail: [[1.7, -.25, 1.15], [1.0, -.62, 0], 36], peripheral: [[0, .05, 1.45], [0, 0, 0], 79] };
function setShow(group, state) {
  group.traverse((o) => { if (o.isMesh && o.material.name.startsWith('emit_')) { o.material.userData.base ??= o.material.emissiveIntensity; o.material.emissiveIntensity = o.material.userData.base * (state === 'up' ? 1 : .12); } });
}
async function masks(group, name) {
  // white = our frame, grey = player, black = room; read by design-tools/ambient_check.py
  const saved = new Map(), white = new THREE.MeshBasicMaterial({ color: 0xffffff }), grey = new THREE.MeshBasicMaterial({ color: 0x808080 }), black = new THREE.MeshBasicMaterial({ color: 0x000000 });
  scene.traverse((o) => { if (o.isMesh) { saved.set(o, o.material); let in_ = false; o.traverseAncestors((a) => { if (a === group) in_ = true; }); o.material = in_ ? white : o === player ? grey : black; } });
  const bg = scene.background, tm = renderer.toneMapping; scene.background = new THREE.Color(0); renderer.toneMapping = THREE.NoToneMapping;
  renderer.render(scene, cam); await post(name, await png());
  scene.background = bg; renderer.toneMapping = tm; for (const [o, m] of saved) o.material = m;
}

async function main() {
  let group, light = 0xffffff, ambience = '';
  if (MODE === 'legacy') { const gl = await new GLTFLoader().loadAsync('out/' + STYLE + '.glb'); group = gl.scene; }
  else ({ group, light, ambience } = await STYLES[STYLE]());
  group.name = 'frame-' + STYLE; scene.add(group);
  if (MODE === 'cut') {
    renderer.setSize(1700, 1000); scene.background = null; renderer.setClearColor(0x000000, 0);
    wall.visible = floor.visible = player.visible = sofa.visible = false;
    const oc = new THREE.OrthographicCamera(-1.7, 1.7, 1.0, -1.0, .1, 20); oc.position.set(0, 0, 5); oc.lookAt(0, 0, 0);
    for (const state of ['up', 'showing']) { setShow(group, state); renderer.render(scene, oc); await post(`${STYLE}-cut-${state}.png`, await png()); }
    done(); return;
  }
  if (MODE === 'final' || MODE === 'legacy') {
    if (MODE === 'final') {
      const glb = await new GLTFExporter().parseAsync(group, { binary: true });
      await post(STYLE + '.glb', glb);
      await post(STYLE + '.json', JSON.stringify({ style: STYLE, ...stats(group), ambience, light: '#' + new THREE.Color(light).getHexString() }));
    }
    for (const [shot, [p, t, fov]] of Object.entries(SHOTS)) {
      if (MODE === 'legacy' && shot !== 'peripheral') continue;
      setShow(group, shot === 'peripheral' ? 'showing' : 'up');
      cam.fov = fov; cam.position.set(...p); cam.lookAt(...t); cam.updateProjectionMatrix();
      renderer.render(scene, cam); await post(`${STYLE}-${shot}.png`, await png());
      if (shot === 'peripheral') { await masks(group, `${STYLE}-peripheral-mask.png`); setShow(group, 'up'); renderer.render(scene, cam); await post(`${STYLE}-peripheral-up.png`, await png()); }
    }
    done(); return;
  }
  cam.position.set(...SHOTS.angled[0]); cam.lookAt(0, 0, 0); cam.updateProjectionMatrix();
  const tick = () => { renderer.render(scene, cam); requestAnimationFrame(tick); }; tick();
}
async function done() { await post(`${STYLE}-${MODE}.done`, 'ok'); document.title = 'LAB-DONE'; document.body.insertAdjacentHTML('beforeend', '<pre id="lab-done">LAB-DONE</pre>'); }
main().catch(async (e) => { await post(`${STYLE}-${MODE}.done`, 'ERROR ' + (e.stack || e)); document.body.insertAdjacentHTML('beforeend', '<pre id="lab-done">LAB-ERROR ' + (e.stack || e) + '</pre>'); });
