# Builds boitier/apercu-3d.html : 3D preview of the sloped SEMI case (three.js), wood or aluminium sides.
# Geometry (mm) : panel 475 x 387 tilted 10 deg, front edge 43 mm high, back edge ~110 mm ; black 2 mm aluminium tray
# (bottom + front + back), panel 2 mm aluminium, walnut cheeks 18 mm (or 4 mm black aluminium).
import base64, json, os
D = os.path.dirname(os.path.abspath(__file__))
b64 = lambda p: base64.b64encode(open(p, 'rb').read()).decode()
face, back = b64('/tmp/face.jpg'), b64('/tmp/back.jpg')
holes = json.load(open(os.path.join(D, 'facade-trous.json')))
html = r"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ocTavio SEMI – boîtier 3D</title>
<style>
html,body{margin:0;height:100%;background:#1b1916;color:#ece5d3;font-family:'Barlow Condensed','Arial Narrow',sans-serif;overflow:hidden}
#ui{position:fixed;top:10px;left:10px;right:10px;display:flex;flex-wrap:wrap;gap:6px;align-items:center;z-index:2}
#ui b{font-size:22px;letter-spacing:.02em;margin-right:6px}
button{font:600 14px 'Barlow Condensed',sans-serif;letter-spacing:.06em;text-transform:uppercase;background:#26231f;color:#ece5d3;border:1px solid #3a352f;border-radius:4px;padding:7px 11px;cursor:pointer}
button.on{border-color:#ffae3d;color:#ffae3d}
#info{position:fixed;left:10px;bottom:10px;font-size:13px;color:#a69c8a;max-width:520px;line-height:1.35}
canvas{display:block}
</style>
</head><body>
<div id="ui"><b>ocTavio SEMI</b>
<button id="wood" class="on">Côtés en noyer</button><button id="alu">Côtés en aluminium</button>
<span style="width:10px"></span>
<button data-v="front">Avant</button><button data-v="side">Côté</button><button data-v="back">Arrière</button><button data-v="top">Dessus</button>
</div>
<div id="info">475 × 387 mm de façade, inclinée de 10°. Hauteur 43 mm devant et 112 mm derrière, profondeur 381 mm. Bac et façade en aluminium 2 mm peint noir (JLCCNC). Joues de 18 mm. Glisse pour tourner, pince ou molette pour zoomer.</div>
<script type="module">
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
const H = __HOLES__;
const W = 475, P = 387, T = 2, ANG = 10 * Math.PI / 180, HF = 43;
const DEP = P * Math.cos(ANG), HB = HF + P * Math.sin(ANG);
const renderer = new THREE.WebGLRenderer({ antialias: true }); renderer.setPixelRatio(Math.min(2, devicePixelRatio));
renderer.setSize(innerWidth, innerHeight); renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.shadowMap.enabled = true;
document.body.appendChild(renderer.domElement);
const scene = new THREE.Scene(); scene.background = new THREE.Color(0x1b1916);
scene.environment = new THREE.PMREMGenerator(renderer).fromScene(new RoomEnvironment(), 0.04).texture;
const cam = new THREE.PerspectiveCamera(32, innerWidth / innerHeight, 10, 5000);
const ctl = new OrbitControls(cam, renderer.domElement); ctl.enableDamping = true; ctl.target.set(0, 60, 0);
const sun = new THREE.DirectionalLight(0xffffff, 1.6); sun.position.set(300, 700, 500); sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048); Object.assign(sun.shadow.camera, { left: -500, right: 500, top: 500, bottom: -500, far: 2000 }); scene.add(sun);
scene.add(new THREE.HemisphereLight(0xffffff, 0x302820, 0.5));
const floor = new THREE.Mesh(new THREE.PlaneGeometry(4000, 4000), new THREE.MeshStandardMaterial({ color: 0x2b2722, roughness: .95 }));
floor.rotation.x = -Math.PI / 2; floor.position.y = -6; floor.receiveShadow = true; scene.add(floor);
const loader = new THREE.TextureLoader();
const tex = (b, flip) => { const t = loader.load('data:image/jpeg;base64,' + b); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; return t; };
const black = new THREE.MeshStandardMaterial({ color: 0x141414, roughness: .55, metalness: .4 });
// ---- tray : bottom, front wall, back wall (2 mm aluminium, black powder coat)
const box = (w, h, d, m, x, y, z) => { const g = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), m); g.position.set(x, y, z); g.castShadow = g.receiveShadow = true; scene.add(g); return g; };
const z0 = DEP / 2, z1 = -DEP / 2;
box(W, T, DEP, black, 0, T / 2, 0);
box(W, HF, T, black, 0, HF / 2, z0 - T / 2);
const backMat = new THREE.MeshStandardMaterial({ map: tex('__BACK__'), roughness: .6, metalness: .3 });
const bw = box(W, HB - 2, T, [black, black, black, black, black, backMat], 0, (HB - 2) / 2, z1 + T / 2);
// ---- panel (texture = the real panel drawing), tilted
const faceMat = new THREE.MeshStandardMaterial({ map: tex('__FACE__'), roughness: .5, metalness: .35 });
const panel = new THREE.Group(); scene.add(panel);
const pm = new THREE.Mesh(new THREE.BoxGeometry(W, T, P), [black, black, faceMat, black, black, black]); pm.castShadow = pm.receiveShadow = true;
pm.position.set(0, T / 2, -P / 2); panel.add(pm);
panel.position.set(0, HF, z0); panel.rotation.x = ANG; panel.rotation.y = 0;
// panel surface coordinates : x = u - W/2, z = v (v from the front edge... the drawing's top is the back)
const onPanel = (u, v, h) => new THREE.Vector3(u - W / 2, T + h, -P + v);
// slider caps, jack nuts, toggles, LEDs, button, speaker
const capMat = new THREE.MeshStandardMaterial({ color: 0x1a1a1a, roughness: .35, metalness: .2 });
const lineMat = new THREE.MeshStandardMaterial({ color: 0xf2f2f2, roughness: .4 });
const nutMat = new THREE.MeshStandardMaterial({ color: 0xc8c8c2, roughness: .3, metalness: .9 });
const holeMat = new THREE.MeshStandardMaterial({ color: 0x050505, roughness: .9 });
const val = {}; // default slider positions from the panel (cap drawn at its default)
for (const [k, x, yT, yB] of H.sliders) {
  const cap = new THREE.Mesh(new THREE.BoxGeometry(9, 9, 12.4), capMat); const v0 = window.SEMI_DEFAULTS ? 0 : 0;
  const p = onPanel(x, yB - 60 * (H.def[k] ?? .5), 4.5); cap.position.copy(p); cap.castShadow = true; panel.add(cap);
  const l = new THREE.Mesh(new THREE.BoxGeometry(8.4, .3, .8), lineMat); l.position.copy(p).add(new THREE.Vector3(0, 4.6, 0)); panel.add(l);
}
for (const [k, x, y, d] of H.jacks) {
  const n = new THREE.Mesh(new THREE.CylinderGeometry(3.6, 3.6, 2.2, 6), nutMat); n.position.copy(onPanel(x, y, 1.1)); n.castShadow = true; panel.add(n);
  const h = new THREE.Mesh(new THREE.CylinderGeometry(1.9, 1.9, 2.4, 20), holeMat); h.position.copy(onPanel(x, y, 1.2)); panel.add(h);
}
for (const [x, y] of H.midi || []) {}
for (const [k, x, y] of H.toggles) {
  const n = new THREE.Mesh(new THREE.CylinderGeometry(3.2, 3.2, 2, 6), nutMat); n.position.copy(onPanel(x, y, 1)); panel.add(n);
  const lev = new THREE.Mesh(new THREE.CylinderGeometry(.9, 1.2, 9, 12), nutMat); lev.position.copy(onPanel(x, y, 5)); lev.rotation.x = .45 * (H.def[k] ? -1 : 1); panel.add(lev);
}
for (const [k, x, y] of H.leds) { const l = new THREE.Mesh(new THREE.SphereGeometry(1.6, 16, 8), new THREE.MeshStandardMaterial({ color: 0x9c1d16, emissive: 0x401010 })); l.position.copy(onPanel(x, y, .6)); panel.add(l); }
for (const [x, y] of H.buttons) { const b = new THREE.Mesh(new THREE.CylinderGeometry(3, 3, 4, 24), capMat); b.position.copy(onPanel(x, y, 2)); panel.add(b); }
// ---- cheeks : wedge with rounded corners, 18 mm walnut or 4 mm black aluminium
function woodTexture() {
  const c = document.createElement('canvas'); c.width = 1024; c.height = 512; const g = c.getContext('2d');
  g.fillStyle = '#5a3a24'; g.fillRect(0, 0, 1024, 512);
  for (let i = 0; i < 260; i++) { const y = Math.random() * 512, a = Math.random() * .25 + .05; g.strokeStyle = Math.random() < .5 ? `rgba(30,16,8,${a})` : `rgba(150,100,60,${a * .6})`;
    g.lineWidth = Math.random() * 3 + .5; g.beginPath(); g.moveTo(0, y); for (let x = 0; x <= 1024; x += 32) g.lineTo(x, y + Math.sin(x / 140 + i) * 6 + Math.sin(x / 37 + i * 3) * 1.5); g.stroke(); }
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.wrapS = t.wrapT = THREE.RepeatWrapping; return t;
}
const woodMat = new THREE.MeshStandardMaterial({ map: woodTexture(), roughness: .55, metalness: 0 });
const cheekProfile = (lip) => {           // side outline in (z, y) : panel edge + lip
  const s = new THREE.Shape(), r = 9, zf = z0 + 6, zb = z1 - 6, yf = HF + T + lip * Math.cos(ANG), yb = HB + T + lip * Math.cos(ANG);
  const pts = [[zb, 0], [zf, 0], [zf, yf], [zb, yb]];
  // rounded polygon
  const n = pts.length;
  for (let i = 0; i < n; i++) {
    const p0 = pts[(i + n - 1) % n], p = pts[i], p1 = pts[(i + 1) % n];
    const a = new THREE.Vector2(p0[0] - p[0], p0[1] - p[1]).normalize(), b = new THREE.Vector2(p1[0] - p[0], p1[1] - p[1]).normalize();
    const rr = i < 2 ? 3 : r;
    const s0 = [p[0] + a.x * rr, p[1] + a.y * rr], s1 = [p[0] + b.x * rr, p[1] + b.y * rr];
    if (i === 0) s.moveTo(...s0); else s.lineTo(...s0);
    s.quadraticCurveTo(p[0], p[1], ...s1);
  }
  s.closePath(); return s;
};
let cheeks = [];
function buildCheeks(wood) {
  cheeks.forEach(c => scene.remove(c)); cheeks = [];
  const th = wood ? 18 : 4, lip = wood ? 9 : 3;
  const geo = new THREE.ExtrudeGeometry(cheekProfile(lip), { depth: th, bevelEnabled: wood, bevelThickness: 1.2, bevelSize: 1.2, bevelSegments: 3, curveSegments: 10 });
  if (wood) { // planar UV : grain along the depth
    const pos = geo.attributes.position, uv = new Float32Array(pos.count * 2);
    for (let i = 0; i < pos.count; i++) { uv[2 * i] = pos.getX(i) / 400; uv[2 * i + 1] = pos.getY(i) / 200 + pos.getZ(i) / 400; }
    geo.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
  }
  for (const side of [-1, 1]) {
    const m = new THREE.Mesh(geo, wood ? woodMat : black); m.castShadow = m.receiveShadow = true;
    m.rotation.y = Math.PI / 2; m.position.x = side < 0 ? -W / 2 - th : W / 2; scene.add(m); cheeks.push(m);
  }
}
// feet
for (const sx of [-1, 1]) for (const sz of [-1, 1]) box(28, 6, 28, new THREE.MeshStandardMaterial({ color: 0x111111, roughness: 1 }), sx * (W / 2 - 30), -3, sz * (DEP / 2 - 30));
buildCheeks(true);
const btnW = document.getElementById('wood'), btnA = document.getElementById('alu');
btnW.onclick = () => { buildCheeks(true); btnW.classList.add('on'); btnA.classList.remove('on'); };
btnA.onclick = () => { buildCheeks(false); btnA.classList.add('on'); btnW.classList.remove('on'); };
const views = { front: [0, 520, 820], side: [900, 300, 120], back: [250, 300, -850], top: [0, 1050, 120] };
function view(v) { cam.position.set(...views[v]); ctl.target.set(0, v === 'top' ? 40 : 60, 0); ctl.update(); }
document.querySelectorAll('[data-v]').forEach(b => b.onclick = () => view(b.dataset.v));
view('front'); cam.position.set(420, 520, 760); ctl.update();
addEventListener('resize', () => { cam.aspect = innerWidth / innerHeight; cam.updateProjectionMatrix(); renderer.setSize(innerWidth, innerHeight); });
(function loop() { ctl.update(); renderer.render(scene, cam); requestAnimationFrame(loop); })();
window.__ready = true;
</script></body></html>"""
# default slider values from the panel definition
import re, subprocess
defs = json.loads(subprocess.run(['node', '-e', "eval(require('fs').readFileSync('" + os.path.join(D, '..', 'source', 'def.js') + "','utf8')+';global.D=SEMI_DEF');const o={};D.tiers.forEach(t=>t.secs.forEach(s=>{s.sl.forEach(a=>o[s.id+'.'+a[0]]=a[2]);(s.sw||[]).forEach(a=>o[s.id+'.'+a[0]]=a[3]);}));console.log(JSON.stringify(o))"], capture_output=True, text=True).stdout)
holes['def'] = defs
import re as _re
m = _re.search(r'<script type="module">(.*?)</script>', html, _re.S)
src = m.group(1).replace('__HOLES__', json.dumps(holes)).replace('__FACE__', face).replace('__BACK__', back)
src = src.replace("'three/addons/", "'three/examples/jsm/")
B = '/home/claude/work/b3d'; open(B + '/main.js', 'w').write(src)
subprocess.run([B + '/node_modules/.bin/esbuild', B + '/main.js', '--bundle', '--minify', '--format=iife', '--outfile=' + B + '/out.js'], check=True, cwd=B)
html = html[:m.start()] + '<script>' + open(B + '/out.js').read().replace('</script', '<\\/script') + '</script>' + html[m.end():]
open(os.path.join(D, 'apercu-3d.html'), 'w').write(html)
print(len(html) // 1024, 'KB')
