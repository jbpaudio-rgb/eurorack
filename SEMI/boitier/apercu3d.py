# Builds boitier/apercu-3d.html : 3D preview of the upright SEMI case, ARP 2600 style (three.js).
# Geometry (mm) : panel 475 x 387 leaning back 10 deg from vertical, flush with the front of a wooden box
# (12 mm plywood, tolex or walnut), sloped front, depth 170 mm at the base, ~100 mm at the top,
# carry handle on top, rear connector plate (IEC, MIDI, USB) at the bottom of the back.
import base64, json, os, re, subprocess
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
<button id="tolex" class="on">Tolex noir</button><button id="wood">Noyer</button>
<span style="width:10px"></span>
<button data-v="front">Avant</button><button data-v="side">Côté</button><button data-v="back">Arrière</button><button data-v="top">Dessus</button>
</div>
<div id="info">Debout comme le ARP 2600 : façade 475 × 387 mm penchée de 10° vers l'arrière. Façade à fleur du boîtier. Boîte en contreplaqué 12 mm recouverte de tolex, environ 499 × 412 × 170 mm, poignée sur le dessus, connecteurs en bas à l'arrière. Glisse pour tourner, pince ou molette pour zoomer.</div>
<script type="module">
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
const H = __HOLES__;
const W = 475, P = 387, T = 2, LEAN = 10 * Math.PI / 180, TH = 12;      // panel, plywood
const RB = 22, RT = 12, REC = 0, DB = 170;  // panel flush with the box front, top board right on the panel edge                                // bottom/top rails, recess, base depth
const PH = P * Math.cos(LEAN), PD = P * Math.sin(LEAN);                   // panel rise / setback
const HT = RB + PH + RT;                                                  // total height
const zf = DB / 2, zb = -DB / 2;                                          // front / back of the base
const zTop = zf - REC - PD - RT * Math.tan(LEAN);                         // front edge of the top
const renderer = new THREE.WebGLRenderer({ antialias: true }); renderer.setPixelRatio(Math.min(2, devicePixelRatio));
renderer.setSize(innerWidth, innerHeight); renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.shadowMap.enabled = true;
document.body.appendChild(renderer.domElement);
const scene = new THREE.Scene(); scene.background = new THREE.Color(0x1b1916);
scene.environment = new THREE.PMREMGenerator(renderer).fromScene(new RoomEnvironment(), 0.04).texture;
const cam = new THREE.PerspectiveCamera(32, innerWidth / innerHeight, 10, 6000);
const ctl = new OrbitControls(cam, renderer.domElement); ctl.enableDamping = true;
const sun = new THREE.DirectionalLight(0xffffff, 1.5); sun.position.set(400, 900, 700); sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048); Object.assign(sun.shadow.camera, { left: -600, right: 600, top: 600, bottom: -600, far: 2500 }); scene.add(sun);
scene.add(new THREE.HemisphereLight(0xffffff, 0x302820, 0.5));
const floor = new THREE.Mesh(new THREE.PlaneGeometry(5000, 5000), new THREE.MeshStandardMaterial({ color: 0x2b2722, roughness: .95 }));
floor.rotation.x = -Math.PI / 2; floor.position.y = -8; floor.receiveShadow = true; scene.add(floor);
const loader = new THREE.TextureLoader();
const tex = b => { const t = loader.load('data:image/jpeg;base64,' + b); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; return t; };
const black = new THREE.MeshStandardMaterial({ color: 0x141414, roughness: .55, metalness: .4 });
const chrome = new THREE.MeshStandardMaterial({ color: 0xd0d0cc, roughness: .25, metalness: 1 });
const add = (m, x, y, z) => { m.position.set(x, y, z); m.castShadow = m.receiveShadow = true; scene.add(m); return m; };
// ---- surface textures
function canvasTex(draw, w = 1024, h = 512) { const c = document.createElement('canvas'); c.width = w; c.height = h; draw(c.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.wrapS = t.wrapT = THREE.RepeatWrapping; return t; }
const woodTex = canvasTex((g, w, h) => { g.fillStyle = '#5a3a24'; g.fillRect(0, 0, w, h);
  for (let i = 0; i < 260; i++) { const y = Math.random() * h, a = Math.random() * .25 + .05; g.strokeStyle = Math.random() < .5 ? `rgba(30,16,8,${a})` : `rgba(150,100,60,${a * .6})`;
    g.lineWidth = Math.random() * 3 + .5; g.beginPath(); g.moveTo(0, y); for (let x = 0; x <= w; x += 32) g.lineTo(x, y + Math.sin(x / 140 + i) * 6 + Math.sin(x / 37 + i * 3) * 1.5); g.stroke(); } });
const tolexTex = canvasTex((g, w, h) => { g.fillStyle = '#1d1c1b'; g.fillRect(0, 0, w, h); const d = g.getImageData(0, 0, w, h);
  for (let i = 0; i < d.data.length; i += 4) { const n = (Math.random() - .5) * 26 + ((i / 4 % w) % 3 === 0 ? 6 : 0) + (((i / 4 / w) | 0) % 3 === 0 ? -5 : 0); d.data[i] += n; d.data[i + 1] += n; d.data[i + 2] += n; }
  g.putImageData(d, 0, 0); }, 512, 512);
tolexTex.repeat.set(1, 1);
const mats = { tolex: new THREE.MeshStandardMaterial({ map: tolexTex, roughness: .92, metalness: 0 }), wood: new THREE.MeshStandardMaterial({ map: woodTex, roughness: .55, metalness: 0 }) };
let skin = mats.tolex;
const planarUV = (geo, s = 300) => { const p = geo.attributes.position, uv = new Float32Array(p.count * 2);
  for (let i = 0; i < p.count; i++) { uv[2 * i] = (p.getX(i) + p.getZ(i)) / s; uv[2 * i + 1] = (p.getY(i) + p.getZ(i) * .3) / (s / 2); } geo.setAttribute('uv', new THREE.BufferAttribute(uv, 2)); return geo; };
// ---- the box : two sloped sides, top, bottom, front bottom rail, back
const box = new THREE.Group(); scene.add(box); const skinned = [];
const part = (geo, x, y, z) => { const m = new THREE.Mesh(planarUV(geo), skin); m.position.set(x, y, z); m.castShadow = m.receiveShadow = true; box.add(m); skinned.push(m); return m; };
function sideShape() {
  const s = new THREE.Shape(), pts = [[zb, 0], [zf, 0], [zf, RB], [zTop, HT], [zb, HT]], rr = [6, 6, 2, 10, 10], n = pts.length;
  for (let i = 0; i < n; i++) {
    const p0 = pts[(i + n - 1) % n], p = pts[i], p1 = pts[(i + 1) % n];
    const a = new THREE.Vector2(p0[0] - p[0], p0[1] - p[1]).normalize(), b = new THREE.Vector2(p1[0] - p[0], p1[1] - p[1]).normalize();
    const s0 = [p[0] + a.x * rr[i], p[1] + a.y * rr[i]], s1 = [p[0] + b.x * rr[i], p[1] + b.y * rr[i]];
    if (i === 0) s.moveTo(...s0); else s.lineTo(...s0); s.quadraticCurveTo(p[0], p[1], ...s1);
  } s.closePath(); return s;
}
const sideGeo = new THREE.ExtrudeGeometry(sideShape(), { depth: TH, bevelEnabled: true, bevelThickness: 1, bevelSize: 1, bevelSegments: 2, curveSegments: 8 });
for (const sx of [-1, 1]) { const m = part(sideGeo.clone(), sx < 0 ? -W / 2 : W / 2 + TH, 0, 0); m.rotation.y = -Math.PI / 2; }
part(new THREE.BoxGeometry(W, TH, zTop - zb), 0, HT - TH / 2, (zTop + zb) / 2);                 // top
part(new THREE.BoxGeometry(W, TH, DB), 0, TH / 2, 0);                                            // bottom
part(new THREE.BoxGeometry(W, RB, TH), 0, RB / 2, zf - TH / 2);                                  // front rail under the panel
const backMat = new THREE.MeshStandardMaterial({ map: tex('__BACK__'), roughness: .6, metalness: .3 });
part(new THREE.BoxGeometry(W, HT - 2 * TH - 110, TH), 0, TH + 110 + (HT - 2 * TH - 110) / 2, zb + TH / 2); // back board
const plate = new THREE.Mesh(new THREE.BoxGeometry(W, 110, 2), [black, black, black, black, black, backMat]); // rear connector plate (alu)
plate.position.set(0, TH + 55, zb + 1); box.add(plate);
// ---- carry handle (leather strap on two chrome brackets), feet, chrome corners
const hc = new THREE.CatmullRomCurve3([[-90, 0, 0], [-80, 22, 0], [-40, 34, 0], [40, 34, 0], [80, 22, 0], [90, 0, 0]].map(p => new THREE.Vector3(...p)));
const handle = new THREE.Mesh(new THREE.TubeGeometry(hc, 40, 7, 12), new THREE.MeshStandardMaterial({ color: 0x151312, roughness: .6 }));
handle.scale.z = .6; add(handle, 0, HT, (zTop + zb) / 2);
for (const sx of [-1, 1]) add(new THREE.Mesh(new THREE.BoxGeometry(22, 6, 26), chrome), sx * 90, HT + 2, (zTop + zb) / 2);
for (const sx of [-1, 1]) for (const z of [zf - 20, zb + 20]) add(new THREE.Mesh(new THREE.CylinderGeometry(12, 14, 8, 24), new THREE.MeshStandardMaterial({ color: 0x111111, roughness: 1 })), sx * (W / 2 - 15), -4, z);
for (const sx of [-1, 1]) for (const [y, z] of [[HT, zb], [0, zb], [0, zf], [HT, zTop]]) {
  const c = new THREE.Mesh(new THREE.SphereGeometry(9, 16, 12), chrome); c.scale.set(1, .9, .9); add(c, sx * (W / 2 + TH - 3), y + (y ? -4 : 4), z + (z === zb ? 4 : -4));
}
// ---- panel (texture = the real panel drawing), leaning back 10 deg, set REC mm into the box
const faceMat = new THREE.MeshStandardMaterial({ map: tex('__FACE__'), roughness: .5, metalness: .35 });
const panel = new THREE.Group(); scene.add(panel);
const pm = new THREE.Mesh(new THREE.BoxGeometry(W, T, P), [black, black, faceMat, black, black, black]); pm.castShadow = pm.receiveShadow = true;
pm.position.set(0, -T / 2, -P / 2); panel.add(pm);
panel.position.set(0, RB, zf - REC); panel.rotation.x = Math.PI / 2 - LEAN;
const onPanel = (u, v, h) => new THREE.Vector3(u - W / 2, h, -P + v);
const capMat = new THREE.MeshStandardMaterial({ color: 0x1a1a1a, roughness: .35, metalness: .2 });
const lineMat = new THREE.MeshStandardMaterial({ color: 0xf2f2f2, roughness: .4 });
const holeMat = new THREE.MeshStandardMaterial({ color: 0x050505, roughness: .9 });
for (const [k, x, yT, yB] of H.sliders) {
  const p = onPanel(x, yB - 60 * (H.def[k] ?? .5), 4.5);
  const cap = new THREE.Mesh(new THREE.BoxGeometry(9, 9, 12.4), capMat); cap.position.copy(p); cap.castShadow = true; panel.add(cap);
  const l = new THREE.Mesh(new THREE.BoxGeometry(8.4, .3, .8), lineMat); l.position.copy(p).add(new THREE.Vector3(0, 4.6, 0)); panel.add(l);
}
for (const [k, x, y] of H.jacks) {
  const n = new THREE.Mesh(new THREE.CylinderGeometry(3.6, 3.6, 2.2, 6), chrome); n.position.copy(onPanel(x, y, 1.1)); n.castShadow = true; panel.add(n);
  const h = new THREE.Mesh(new THREE.CylinderGeometry(1.9, 1.9, 2.4, 20), holeMat); h.position.copy(onPanel(x, y, 1.2)); panel.add(h);
}
for (const [k, x, y] of H.toggles) {
  const n = new THREE.Mesh(new THREE.CylinderGeometry(3.2, 3.2, 2, 6), chrome); n.position.copy(onPanel(x, y, 1)); panel.add(n);
  const lev = new THREE.Mesh(new THREE.CylinderGeometry(.9, 1.2, 9, 12), chrome); lev.position.copy(onPanel(x, y, 5)); lev.rotation.x = .45 * (H.def[k] ? -1 : 1); panel.add(lev);
}
for (const [k, x, y] of H.leds) { const l = new THREE.Mesh(new THREE.SphereGeometry(1.6, 16, 8), new THREE.MeshStandardMaterial({ color: 0x9c1d16, emissive: 0x401010 })); l.position.copy(onPanel(x, y, .6)); panel.add(l); }
for (const [x, y] of H.buttons) { const b = new THREE.Mesh(new THREE.CylinderGeometry(3, 3, 4, 24), capMat); b.position.copy(onPanel(x, y, 2)); panel.add(b); }
// ---- UI
function setSkin(k) { skin = mats[k]; skinned.forEach(m => m.material = skin); document.querySelectorAll('#tolex,#wood').forEach(b => b.classList.toggle('on', b.id === k)); }
document.getElementById('tolex').onclick = () => setSkin('tolex'); document.getElementById('wood').onclick = () => setSkin('wood');
const views = { front: [380, 420, 1050], side: [1150, 330, 250], back: [-450, 420, -1000], top: [0, 1300, 300] };
function view(v) { cam.position.set(...views[v]); ctl.target.set(0, HT / 2 - 10, 0); ctl.update(); }
document.querySelectorAll('[data-v]').forEach(b => b.onclick = () => view(b.dataset.v));
view('front');
addEventListener('resize', () => { cam.aspect = innerWidth / innerHeight; cam.updateProjectionMatrix(); renderer.setSize(innerWidth, innerHeight); });
(function loop() { ctl.update(); renderer.render(scene, cam); requestAnimationFrame(loop); })();
window.__ready = true;
</script></body></html>"""
defs = json.loads(subprocess.run(['node', '-e', "eval(require('fs').readFileSync('" + os.path.join(D, '..', 'source', 'def.js') + "','utf8')+';global.D=SEMI_DEF');const o={};D.tiers.forEach(t=>t.secs.forEach(s=>{s.sl.forEach(a=>o[s.id+'.'+a[0]]=a[2]);(s.sw||[]).forEach(a=>o[s.id+'.'+a[0]]=a[3]);}));console.log(JSON.stringify(o))"], capture_output=True, text=True).stdout)
holes['def'] = defs
m = re.search(r'<script type="module">(.*?)</script>', html, re.S)
src = m.group(1).replace('__HOLES__', json.dumps(holes)).replace('__FACE__', face).replace('__BACK__', back)
src = src.replace("'three/addons/", "'three/examples/jsm/")
B = '/home/claude/work/b3d'; open(B + '/main.js', 'w').write(src)
subprocess.run([B + '/node_modules/.bin/esbuild', B + '/main.js', '--bundle', '--minify', '--format=iife', '--outfile=' + B + '/out.js'], check=True, cwd=B)
html = html[:m.start()] + '<script>' + open(B + '/out.js').read().replace('</script', '<\\/script') + '</script>' + html[m.end():]
open(os.path.join(D, 'apercu-3d.html'), 'w').write(html)
print(len(html) // 1024, 'KB')
