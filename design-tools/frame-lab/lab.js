// Home Cinema frame lab: builds each frame style as real 3D (meters), exports GLB, renders shots.
// ?style=<id>&mode=parts|final|view   parts: export hi-res organic parts for bin/glb_decimate.py; final: build with decimated parts, export GLB + 3 renders.
import * as THREE from 'three';
import { GLTFExporter } from 'three/addons/exporters/GLTFExporter.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import * as BGU from 'three/addons/utils/BufferGeometryUtils.js';

const q = new URLSearchParams(location.search);
const STYLE = q.get('style') || 'gallery';
const MODE = q.get('mode') || 'view';
const W = 1600, H = 1000;
const OPEN_W = 1.6, OPEN_H = 0.9; // hollow opening, 16:9, meters (scaled with the Volume at runtime)

// ---------- helpers
let seed = 7;
const rnd = () => { seed = (seed * 16807) % 2147483647; return (seed - 1) / 2147483646; };
function hash3(x, y, z) { const s = Math.sin(x * 127.1 + y * 311.7 + z * 74.7) * 43758.5453; return s - Math.floor(s); }
function vnoise(x, y, z) {
  const xi = Math.floor(x), yi = Math.floor(y), zi = Math.floor(z), xf = x - xi, yf = y - yi, zf = z - zi;
  const u = xf * xf * (3 - 2 * xf), v = yf * yf * (3 - 2 * yf), w = zf * zf * (3 - 2 * zf);
  let r = 0;
  for (let a = 0; a < 2; a++) for (let b = 0; b < 2; b++) for (let c = 0; c < 2; c++)
    r += hash3(xi + a, yi + b, zi + c) * (a ? u : 1 - u) * (b ? v : 1 - v) * (c ? w : 1 - w);
  return r;
}
const fbm = (x, y, z) => vnoise(x, y, z) * .5 + vnoise(x * 2.1, y * 2.1, z * 2.1) * .3 + vnoise(x * 4.3, y * 4.3, z * 4.3) * .2;
function rrShape(w, h, r) {
  const s = new THREE.Shape(), x = -w / 2, y = -h / 2;
  s.moveTo(x + r, y); s.lineTo(x + w - r, y); s.quadraticCurveTo(x + w, y, x + w, y + r); s.lineTo(x + w, y + h - r);
  s.quadraticCurveTo(x + w, y + h, x + w - r, y + h); s.lineTo(x + r, y + h); s.quadraticCurveTo(x, y + h, x, y + h - r);
  s.lineTo(x, y + r); s.quadraticCurveTo(x, y, x + r, y); return s;
}
function frameGeo(ow, oh, orr, iw, ih, ir, depth, bevel = 0.008) {
  const s = rrShape(ow, oh, orr); s.holes.push(rrShape(iw, ih, ir));
  const g = new THREE.ExtrudeGeometry(s, { depth, bevelEnabled: bevel > 0, bevelSize: bevel, bevelThickness: bevel, bevelSegments: 2, curveSegments: 8 });
  g.translate(0, 0, -depth / 2); return g;
}
function tubeRect(w, h, r, tr, z = 0, seg = 200) {
  const pts = rrShape(w, h, r).getSpacedPoints(seg).map((p) => new THREE.Vector3(p.x, p.y, z));
  pts.pop();
  return new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts, true, 'centripetal'), seg, tr, 8, true);
}
function tubeLine(a, b, tr) { return new THREE.TubeGeometry(new THREE.LineCurve3(new THREE.Vector3(...a), new THREE.Vector3(...b)), 1, tr, 10, false); }
const std = (name, color, o = {}) => { const m = new THREE.MeshStandardMaterial({ color, roughness: .7, metalness: 0, ...o }); m.name = name; return m; };
const emit = (name, color, intensity = 3) => { const m = new THREE.MeshStandardMaterial({ color: 0x000000, emissive: color, emissiveIntensity: intensity, roughness: .4 }); m.name = 'emit_' + name; return m; };
function mesh(g, m, name, pos = [0, 0, 0], rot = [0, 0, 0]) { const o = new THREE.Mesh(g, m); o.name = name; o.position.set(...pos); o.rotation.set(...rot); return o; }
function merge(list) { return BGU.mergeGeometries(list.map((g) => (g.index ? g.toNonIndexed() : g)), false); }
function displace(g, amp, freq, flat = [1, 1, 1], off = 0) {
  g = BGU.mergeVertices(g.deleteAttribute('normal') && g.deleteAttribute('uv') ? g : g);
  g.computeVertexNormals();
  const p = g.attributes.position, n = g.attributes.normal, v = new THREE.Vector3();
  for (let i = 0; i < p.count; i++) {
    v.fromBufferAttribute(p, i);
    const d = (fbm(v.x * freq + off, v.y * freq, v.z * freq) - .5) * amp;
    p.setXYZ(i, (v.x + n.getX(i) * d) * flat[0], (v.y + n.getY(i) * d) * flat[1], (v.z + n.getZ(i) * d) * flat[2]);
  }
  g.computeVertexNormals(); return g;
}
async function loadPart(name) {
  const gltf = await new GLTFLoader().loadAsync('out/' + name + '-lo.glb');
  let g = null, mat = null;
  gltf.scene.traverse((o) => { if (o.isMesh && !g) { g = o.geometry; mat = o.material; } });
  g = BGU.mergeVertices(g.deleteAttribute('normal') ? g : g, 1e-4); g.computeVertexNormals();
  return { g, mat };
}
function canvasTex(w, h, draw) { const c = document.createElement('canvas'); c.width = w; c.height = h; draw(c.getContext('2d'), w, h); const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t; }

// ---------- styles (each returns { group, parts: {name: geometry} for MODE=parts })
const STYLES = {};

STYLES.gallery = async () => {
  const g = new THREE.Group();
  g.add(mesh(frameGeo(2.2, 1.42, .02, 1.7, 1.0, .012, .16, .012), std('gallery_plaster', 0xeceae5, { roughness: .92 }), 'frame'));
  g.add(mesh(frameGeo(1.7, 1.0, .012, 1.64, .94, .008, .05, .004), std('gallery_reveal', 0xcfcbc4, { roughness: .8 }), 'reveal', [0, 0, -.07]));
  g.add(mesh(tubeRect(1.67, .97, .01, .0055, 0, 240), emit('gallery_led', 0xffd2a0, 7), 'led', [0, 0, -.045]));
  g.add(mesh(new THREE.BoxGeometry(1.3, .035, .24), std('gallery_oak', 0xb88654, { roughness: .55 }), 'shelf', [0, -.97, .1]));
  const prof = [[0, 0], [.055, 0], [.075, .04], [.07, .12], [.045, .2], [.04, .24], [.05, .26], [0, .26]].map(([x, y]) => new THREE.Vector2(x, y));
  g.add(mesh(new THREE.LatheGeometry(prof, 40), std('gallery_terracotta', 0xc0674a, { roughness: .85 }), 'vase', [-.38, -.952, .1]));
  g.add(mesh(new THREE.BoxGeometry(.12, .12, .12), std('gallery_stone', 0x9a978f, { roughness: .9 }), 'plinth', [.34, -.892, .1]));
  g.add(mesh(new THREE.TorusKnotGeometry(.05, .016, 120, 12), std('gallery_brass', 0xc9a25a, { metalness: 1, roughness: .25 }), 'sculpture', [.34, -.77, .1]));
  return { group: g, light: 0xffd2a0, ambience: 'Quiet gallery room tone' };
};

STYLES.neon = async () => {
  const g = new THREE.Group();
  g.add(mesh(frameGeo(2.0, 1.22, .06, 1.7, .98, .04, .05, .006), std('neon_gunmetal', 0x1a1c24, { metalness: .8, roughness: .32 }), 'frame'));
  g.add(mesh(tubeRect(1.92, 1.15, .07, .011), emit('neon_magenta', 0xff2bd6, 3.2), 'tube-outer', [0, 0, .045]));
  g.add(mesh(tubeRect(1.76, 1.04, .05, .008), emit('neon_cyan', 0x2de2ff, 3.2), 'tube-inner', [0, 0, .04]));
  const slash = [];
  for (let i = 0; i < 3; i++) { slash.push(tubeLine([-1.16 + i * .05, -.72, .03], [-1.04 + i * .05, -.52, .03], .006)); slash.push(tubeLine([1.04 - i * .05, .52, .03], [1.16 - i * .05, .72, .03], .006)); }
  g.add(mesh(merge(slash), emit('neon_amber', 0xffa21f, 3), 'slashes'));
  const clips = [];
  for (const [x, y] of [[-.6, .575], [0, .575], [.6, .575], [-.6, -.575], [0, -.575], [.6, -.575], [-.96, 0], [.96, 0]]) clips.push(new THREE.BoxGeometry(.04, .03, .03).translate(x, y, .035));
  g.add(mesh(merge(clips), std('neon_clip', 0x55585f, { metalness: .9, roughness: .3 }), 'clips'));
  g.add(mesh(new THREE.BoxGeometry(1.9, .008, .016), emit('neon_floorline', 0x2de2ff, 3), 'floor-line', [0, -.72, .06]));
  return { group: g, light: 0xff2bd6, ambience: 'Rain on a city street, distant traffic hum' };
};

STYLES.wa = async () => {
  const g = new THREE.Group();
  const wood = std('wa_hinoki', 0xd9b47e, { roughness: .62 }), dark = std('wa_kumiko', 0xa77b4a, { roughness: .6 });
  const posts = [new THREE.BoxGeometry(.09, 1.62, .09).translate(-.98, -.07, 0), new THREE.BoxGeometry(.09, 1.62, .09).translate(.98, -.07, 0)];
  const beams = [new THREE.BoxGeometry(2.56, .08, .13).translate(0, .8, 0), new THREE.BoxGeometry(2.24, .05, .09).translate(0, .66, 0), new THREE.BoxGeometry(2.0, .05, .08).translate(0, -.56, 0)];
  g.add(mesh(merge([...posts, ...beams]), wood, 'torii'));
  // shoji panels left and right, outside the opening
  for (const sx of [-1, 1]) {
    const cx = sx * 1.34, pw = .56, ph = 1.18, cy = .02;
    g.add(mesh(new THREE.PlaneGeometry(pw, ph), Object.assign(emit('wa_paper', 0xffe6bf, .9), { side: THREE.DoubleSide }), 'paper' + sx, [cx, cy, -.005]));
    const k = [];
    k.push(new THREE.BoxGeometry(pw + .04, .03, .03).translate(cx, cy + ph / 2, 0), new THREE.BoxGeometry(pw + .04, .03, .03).translate(cx, cy - ph / 2, 0));
    k.push(new THREE.BoxGeometry(.03, ph, .03).translate(cx - pw / 2, cy, 0), new THREE.BoxGeometry(.03, ph, .03).translate(cx + pw / 2, cy, 0));
    for (let i = 1; i < 3; i++) k.push(new THREE.BoxGeometry(.012, ph, .02).translate(cx - pw / 2 + i * pw / 3, cy, 0));
    for (let j = 1; j < 6; j++) k.push(new THREE.BoxGeometry(pw, .012, .02).translate(cx, cy - ph / 2 + j * ph / 6, 0));
    g.add(mesh(merge(k), dark, 'kumiko' + sx));
    g.add(mesh(new THREE.BoxGeometry(pw + .1, .04, .2), std('wa_stone', 0x8d8a83, { roughness: .95 }), 'base' + sx, [cx, cy - ph / 2 - .04, .03]));
  }
  // round paper lantern hanging from the top beam (outside the opening, above-left)
  const lat = new THREE.SphereGeometry(.09, 24, 16); lat.scale(1, 1.15, 1);
  g.add(mesh(lat, emit('wa_lantern', 0xffc77a, 2.6), 'lantern', [-.62, .57 + .02, .12]));
  g.add(mesh(new THREE.CylinderGeometry(.003, .003, .1), dark, 'cord', [-.62, .74, .12]));
  return { group: g, light: 0xffc77a, ambience: 'Soft rain on a roof, a wind chime now and then' };
};

STYLES.portal = async () => {
  const g = new THREE.Group();
  g.add(mesh(tubeRect(1.78, 1.06, .26, .018), emit('portal_cyan', 0x6ff6ff, 3.2), 'ring-1'));
  g.add(mesh(tubeRect(1.98, 1.22, .34, .01, -.09), emit('portal_violet', 0xa77bff, 2.8), 'ring-2'));
  g.add(mesh(tubeRect(2.18, 1.38, .42, .006, -.18), emit('portal_blue', 0x5ad8ff, 2.2), 'ring-3'));
  const glass = new THREE.MeshPhysicalMaterial({ color: 0xcff6ff, roughness: .08, metalness: 0, transmission: .9, thickness: .02, transparent: true, opacity: .55 }); glass.name = 'portal_glass';
  g.add(mesh(frameGeo(1.9, 1.16, .3, 1.72, 1.02, .24, .016, .004), glass, 'halo'));
  const nodes = [], ring = rrShape(1.98, 1.22, .34).getSpacedPoints(14); ring.pop();
  for (const p of ring) nodes.push(new THREE.SphereGeometry(.016, 8, 6).translate(p.x, p.y, -.09));
  g.add(mesh(merge(nodes), emit('portal_node', 0xffffff, 4), 'nodes'));
  g.add(mesh(new THREE.CylinderGeometry(.32, .36, .035, 48), std('portal_base', 0x15171d, { metalness: .85, roughness: .3 }), 'puck', [0, -.86, 0]));
  g.add(mesh(new THREE.TorusGeometry(.33, .006, 6, 64), emit('portal_cyan2', 0x6ff6ff, 3), 'puck-rim', [0, -.842, 0], [Math.PI / 2, 0, 0]));
  return { group: g, light: 0x6ff6ff, ambience: 'Low synth pad with a slow shimmer' };
};

STYLES.moss = async (parts) => {
  const g = new THREE.Group();
  const slabs = [];
  const add = (w, h, d, x, y, z, ry = 0) => { const b = new THREE.BoxGeometry(w, h, d, 18, 8, 8); slabs.push(displace(b, .05, 5, [1, 1, 1], x * 3).rotateY(ry).translate(x, y, z)); };
  add(2.3, .2, .34, 0, -.6, .02); add(1.5, .14, .3, -.25, -.76, .1, .05); add(.9, .12, .26, .7, -.74, .14, -.08);
  add(.26, .5, .3, -.98, -.25, 0); add(.3, .44, .32, -1.0, .22, .02, .1); add(.22, .5, .3, .97, -.24, .01); add(.28, .42, .3, 1.0, .22, 0, -.1);
  add(2.4, .16, .34, .02, .58, 0, .02); add(1.2, .12, .3, -.4, .71, .02, -.04);
  let stones = merge(slabs);
  const blobs = [];
  const blob = (r, x, y, z, sy = .45) => { const s = new THREE.IcosahedronGeometry(r, 5); blobs.push(displace(s, r * .5, 9 / r * .05 * 10, [1, sy, 1]).translate(x, y, z)); };
  blob(.16, -.95, .5, .08); blob(.12, -.72, .69, .1); blob(.2, .82, -.63, .12); blob(.14, 1.06, -.42, .08); blob(.1, .3, .8, .08); blob(.13, -.6, -.68, .16);
  let moss = merge(blobs);
  if (parts) { parts['moss-stone'] = stones; parts['moss-moss'] = moss; return { group: g }; }
  const st = await loadPart('moss-stone'), ms = await loadPart('moss-moss');
  g.add(mesh(st.g, std('moss_stone', 0x8b8880, { roughness: .95 }), 'stones'));
  g.add(mesh(ms.g, std('moss_moss', 0x4f7d2a, { roughness: 1 }), 'moss'));
  // fern fronds: curved strips at the bottom-right and top-left corners
  const fr = [];
  for (let i = 0; i < 9; i++) {
    const len = .22 + rnd() * .14, pts = [];
    for (let t = 0; t <= 1; t += .125) pts.push(new THREE.Vector3(0, t * len, Math.sin(t * 1.6) * len * .5));
    const geo = new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 8, .012, 5, false);
    geo.scale(1.6, 1, .4);
    const a = -1.0 + i * .25, base = i < 5 ? [.95, -.52, .14] : [-1.02, .66, .1];
    geo.rotateZ(a).translate(...base); fr.push(geo);
  }
  g.add(mesh(merge(fr), std('moss_fern', 0x6a9a3a, { roughness: .8 }), 'ferns'));
  return { group: g, light: 0xd8f0b0, ambience: 'Forest stream and distant birds' };
};

STYLES.cosmos = async (parts) => {
  const g = new THREE.Group();
  const planetTex = canvasTex(512, 256, (c, w, h) => {
    for (let y = 0; y < h; y++) { const t = y / h, b = Math.sin(t * 38) * .5 + Math.sin(t * 13 + 1) * .5; c.fillStyle = `hsl(${24 + b * 10},${45 + b * 15}%,${48 + b * 12}%)`; c.fillRect(0, y, w, 1); }
  });
  if (parts) {
    const s = new THREE.SphereGeometry(.2, 128, 96);
    parts['cosmos-planet'] = new THREE.Mesh(s, new THREE.MeshStandardMaterial({ map: planetTex }));
    return { group: g };
  }
  g.add(mesh(frameGeo(2.04, 1.24, .12, 1.66, .96, .04, .07, .01), std('cosmos_navy', 0x0e1433, { metalness: .35, roughness: .38 }), 'frame'));
  const stars = [];
  for (let i = 0; i < 220; i++) {
    let x, y; do { x = (rnd() - .5) * 2.9; y = (rnd() - .5) * 1.9; } while (Math.abs(x) < .86 && Math.abs(y) < .51);
    const r = .003 + rnd() ** 3 * .012; stars.push(new THREE.IcosahedronGeometry(r, 0).translate(x, y, (rnd() - .3) * .25));
  }
  g.add(mesh(merge(stars), emit('cosmos_star', 0xdfe8ff, 4), 'stars'));
  const pl = await loadPart('cosmos-planet');
  { const p = pl.g.attributes.position, n = pl.g.attributes.normal, v = new THREE.Vector3(); for (let i = 0; i < p.count; i++) { v.fromBufferAttribute(p, i).normalize(); n.setXYZ(i, v.x, v.y, v.z); } }
  const pm = new THREE.MeshStandardMaterial({ map: pl.mat.map || planetTex, roughness: .8 }); pm.name = 'cosmos_planet';
  g.add(mesh(pl.g, pm, 'planet', [1.02, .6, .14], [.3, 0, .35]));
  const ringM = std('cosmos_ring', 0xd9c7a0, { roughness: .6, side: THREE.DoubleSide, transparent: true, opacity: .8 });
  g.add(mesh(new THREE.RingGeometry(.27, .4, 96, 1), ringM, 'planet-ring', [1.02, .6, .14], [-1.15, .3, .35]));
  const orbit = new THREE.EllipseCurve(0, 0, 1.25, .78, 0, Math.PI * 2).getSpacedPoints(240).map((p) => new THREE.Vector3(p.x, p.y, .06)); orbit.pop();
  g.add(mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(orbit, true), 200, .003, 5, true), emit('cosmos_orbit', 0x8fb4ff, 1.6), 'orbit'));
  g.add(mesh(new THREE.SphereGeometry(.035, 24, 16), std('cosmos_moon', 0xcfd3dc, { roughness: .9 }), 'moon', [-1.18, -.26, .06]));
  return { group: g, light: 0x8fb4ff, ambience: 'Deep space drone, very low' };
};

// ---------- scene
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true, alpha: true });
renderer.setSize(W, H); renderer.setPixelRatio(1);
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = .9;
renderer.outputColorSpace = THREE.SRGBColorSpace;
document.body.appendChild(renderer.domElement);
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x4a443e);
scene.environment = new THREE.PMREMGenerator(renderer).fromScene(new RoomEnvironment(), .04).texture;
scene.environmentIntensity = .35;
scene.add(new THREE.HemisphereLight(0xfff6ea, 0x5c4f44, .35));
const key = new THREE.DirectionalLight(0xfff1e0, 1.1); key.position.set(-2, 3, 3); scene.add(key);
// passthrough stand-in: a plain wall and floor (Home Cinema cannot dim or change them)
const wall = mesh(new THREE.PlaneGeometry(14, 7), std('room_wall', 0x7a7168, { roughness: 1 }), 'wall', [0, 1.2, -.9]);
const floor = mesh(new THREE.PlaneGeometry(14, 8), std('room_floor', 0x5a4636, { roughness: .9 }), 'floor', [0, -1.12, 2], [-Math.PI / 2, 0, 0]);
scene.add(wall, floor);
// the other app's player window (not ours)
const playerTex = canvasTex(1280, 720, (c, w, h) => {
  const gr = c.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, '#203a5c'); gr.addColorStop(.55, '#d9895a'); gr.addColorStop(1, '#2a1e2c'); c.fillStyle = gr; c.fillRect(0, 0, w, h);
  c.fillStyle = '#f6d38a'; c.beginPath(); c.arc(w * .64, h * .5, 70, 0, 7); c.fill();
  c.fillStyle = '#1c1a26'; c.beginPath(); c.moveTo(0, h); c.bezierCurveTo(w * .3, h * .55, w * .6, h * .8, w, h * .62); c.lineTo(w, h); c.fill();
  c.fillStyle = 'rgba(225,225,225,.82)'; c.beginPath(); c.roundRect(w * .22, h - 74, w * .56, 46, 23); c.fill();
  c.fillStyle = '#333'; c.fillRect(w * .32, h - 53, w * .36, 5); c.fillStyle = '#111'; c.fillRect(w * .32, h - 53, w * .14, 5);
});
const pg = new THREE.ShapeGeometry(rrShape(1.5, .844, .045), 6);
{ const p = pg.attributes.position, uv = pg.attributes.uv; for (let i = 0; i < p.count; i++) uv.setXY(i, p.getX(i) / 1.5 + .5, p.getY(i) / .844 + .5); }
const player = mesh(pg, new THREE.MeshBasicMaterial({ map: playerTex, toneMapped: false }), 'other-app-player', [0, 0, -.01]);
scene.add(player);

const composer = new EffectComposer(renderer);
const cam = new THREE.PerspectiveCamera(38, W / H, .05, 50);
composer.addPass(new RenderPass(scene, cam));
composer.addPass(new UnrealBloomPass(new THREE.Vector2(W, H), .5, .4, 1.8));
composer.addPass(new OutputPass());

async function post(name, body) { await fetch('/save?name=' + encodeURIComponent(name), { method: 'POST', body }); }
function stats(group) {
  let tris = 0; const mats = new Set(), tex = new Set();
  group.traverse((o) => { if (!o.isMesh) return; const gg = o.geometry; tris += (gg.index ? gg.index.count : gg.attributes.position.count) / 3; mats.add(o.material.name); if (o.material.map) tex.add(o.material.map.image.width + 'x' + o.material.map.image.height); });
  return { tris: Math.round(tris), materials: [...mats], textures: [...tex] };
}
const SHOTS = { front: [[0, .05, 3.6], [0, 0, 0]], angled: [[2.5, .55, 2.75], [0, -.02, 0]], detail: [[1.55, .95, 1.25], [.7, .42, 0]] };

async function main() {
  const builder = STYLES[STYLE];
  if (MODE === 'parts') {
    const parts = {}; await builder(parts);
    for (const [name, obj] of Object.entries(parts)) {
      const m = obj.isMesh ? obj : new THREE.Mesh(obj, new THREE.MeshStandardMaterial());
      const glb = await new GLTFExporter().parseAsync(m, { binary: true });
      await post(name + '-hi.glb', glb);
    }
    document.title = 'LAB-DONE'; document.body.insertAdjacentHTML('beforeend', '<pre id="lab-done">LAB-DONE</pre>'); return;
  }
  const { group, light, ambience } = await builder(null);
  group.name = 'frame-' + STYLE;
  scene.add(group);
  // accent light from the theme colour, as the app's light strip would cast on the wall (inside our Volume only)
  const acc = new THREE.PointLight(light, 1.2, 4, 2); acc.position.set(0, .2, -.3); scene.add(acc);
  if (MODE === 'cut') {
    // transparent front orthographic cut-outs for the design Preview: 3.4 x 2.0 m at 500 px/m, lights up and showing (emissive x0.12)
    renderer.setSize(1700, 1000); scene.background = null; renderer.setClearColor(0x000000, 0);
    wall.visible = floor.visible = player.visible = false;
    const oc = new THREE.OrthographicCamera(-1.7, 1.7, 1.0, -1.0, .1, 20); oc.position.set(0, 0, 5); oc.lookAt(0, 0, 0);
    for (const state of ['up', 'showing']) {
      group.traverse((o) => { if (o.isMesh && o.material.name.startsWith('emit_')) { o.material.userData.base ??= o.material.emissiveIntensity; o.material.emissiveIntensity = o.material.userData.base * (state === 'up' ? 1 : .12); } });
      acc.intensity = state === 'up' ? 1.2 : .15;
      renderer.render(scene, oc);
      const blob = await new Promise((r) => renderer.domElement.toBlob(r, 'image/png'));
      await post(`${STYLE}-cut-${state}.png`, blob);
    }
    document.title = 'LAB-DONE'; document.body.insertAdjacentHTML('beforeend', '<pre id="lab-done">LAB-DONE</pre>'); return;
  }
  if (MODE === 'final') {
    const glb = await new GLTFExporter().parseAsync(group, { binary: true });
    await post(STYLE + '.glb', glb);
    await post(STYLE + '.json', JSON.stringify({ style: STYLE, ...stats(group), ambience, light: '#' + new THREE.Color(light).getHexString() }));
    for (const [shot, [p, t]] of Object.entries(SHOTS)) {
      cam.position.set(...p); cam.lookAt(...t); cam.updateProjectionMatrix();
      composer.render();
      const blob = await new Promise((r) => renderer.domElement.toBlob(r, 'image/png'));
      await post(`${STYLE}-${shot}.png`, blob);
    }
    document.title = 'LAB-DONE'; document.body.insertAdjacentHTML('beforeend', '<pre id="lab-done">LAB-DONE</pre>'); return;
  }
  cam.position.set(...SHOTS.angled[0]); cam.lookAt(0, 0, 0);
  const tick = () => { composer.render(); requestAnimationFrame(tick); }; tick();
}
main().catch((e) => { document.body.insertAdjacentHTML('beforeend', '<pre id="lab-done">LAB-ERROR ' + (e.stack || e) + '</pre>'); });
