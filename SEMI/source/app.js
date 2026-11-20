// ocTavio SEMI - panel drawing (mm units), sliders, toggles, cables, keyboard, audio.
const $ = s => document.querySelector(s);
const NS = 'http://www.w3.org/2000/svg';
const el = (t, a, p) => { const e = document.createElementNS(NS, t); for (const k in a) e.setAttribute(k, a[k]); if (p) p.appendChild(e); return e; };
const txt = (s, a, p) => { const e = el('text', a, p); e.textContent = s; return e; };
// ---------------------------------------------------------------- geometry (mm)
const SP = 15, SWCOL = 14, PAD = 5, JP = 12.5, STRIP = 8, TOP = 4, TIERH = 122, BOT = 17, TRAVEL = 60;
const Y_LAB = 12.8, Y_TOP = 21.5, Y_IN = 99, Y_OUT = 114;           // slider label, cap centre at value 1 (value 0 = Y_TOP + 60)
const FONT = "'Barlow Condensed','Arial Narrow',sans-serif";
const secW = s => { const g = s.sl.length * SP + (s.sw ? SWCOL : 0) + (s.midi ? SWCOL + 2 : 0) + (s.spk ? 38 : 0); const cols = Math.max(s.in.length, s.out.length); return 2 * PAD + Math.max(g, cols * JP); };
const tierW = SEMI_DEF.tiers.map(t => t.secs.reduce((a, s) => a + secW(s), 0));
const INW = Math.ceil(Math.max(...tierW)), PW = INW + 2 * STRIP, PH = TOP + 3 * TIERH + BOT;
const svg = $('#panel');
let PARAMS = {}, DEFV = {}, SL = {}, JACKS = {}, LAB = {}, LEDS = {}, cables = [];
const SECS = {}; SEMI_DEF.tiers.forEach(t => t.secs.forEach(s => SECS[s.id] = s));
for (const s of Object.values(SECS)) { for (const [k, , v] of s.sl) DEFV[s.id + '.' + k] = v; for (const [k, , , v] of (s.sw || [])) DEFV[s.id + '.' + k] = v; }
DEFV['kb.seq'] = 1;
PARAMS = Object.assign({}, DEFV);
const toastEl = { textContent: '' };
const status = $('#status');
// ---------------------------------------------------------------- value display
function fmt(key, v) {
  const [id, k] = key.split('.'), s = SECS[id];
  const sw = s && (s.sw || []).find(x => x[0] === k); if (sw) return sw[2][v];
  const sl = s && s.sl.find(x => x[0] === k), sc = sl && sl[3];
  if (k === 'coarse') return ((v - .5) * 6 >= 0 ? '+' : '') + ((v - .5) * 6).toFixed(2) + ' oct';
  if (k === 'fine') return ((v - .5) * 12 >= 0 ? '+' : '') + ((v - .5) * 12).toFixed(1) + ' demi-tons';
  if (sc === 'bi') return '× ' + (2 * v - 1).toFixed(2);
  if (id.startsWith('lfo') && k === 'rate') { const f = 0.02 * Math.pow(2, v * 11.3); return f < 1 ? f.toFixed(2) + ' Hz' : f.toFixed(1) + ' Hz'; }
  if (Array.isArray(sc)) { const n = sc.length - 1, x = v * n, i = Math.min(n - 1, Math.floor(x)), f = x - i, nm = q => sc[q].replace('~up', 'RAMPE ↑').replace('~tri', 'TRI').replace('~dn', 'RAMPE ↓').replace('~sq', 'CARRÉ');
    return f < .02 ? nm(i) : f > .98 ? nm(i + 1) : nm(i) + ' → ' + nm(i + 1) + ' ' + Math.round(f * 100) + ' %'; }
  if (key === 'out.vol') return Math.round(v * 100) + ' %';
  return (v * 10).toFixed(1);
}
function show(key) { if (LAB[key]) status.textContent = LAB[key] + '  ' + fmt(key, PARAMS[key]); }
// ---------------------------------------------------------------- drawing
const DEFS = `
<linearGradient id="alu" x1="0" x2="1"><stop offset="0" stop-color="#8d8d8d"/><stop offset=".5" stop-color="#e6e6e6"/><stop offset="1" stop-color="#9c9c9c"/></linearGradient>
<linearGradient id="capg" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#3b3b3b"/><stop offset=".5" stop-color="#1c1c1c"/><stop offset="1" stop-color="#0d0d0d"/></linearGradient>
<radialGradient id="nut" cx=".4" cy=".35" r=".75"><stop offset="0" stop-color="#f0f0eb"/><stop offset=".6" stop-color="#b7b7b1"/><stop offset="1" stop-color="#6f6e68"/></radialGradient>
<radialGradient id="screw" cx=".4" cy=".35" r=".7"><stop offset="0" stop-color="#d2cdc1"/><stop offset="1" stop-color="#6d685e"/></radialGradient>
<radialGradient id="lamp" cx=".4" cy=".35"><stop offset="0" stop-color="#fff3cc"/><stop offset=".45" stop-color="#ff5a4a"/><stop offset="1" stop-color="#9c1d16"/></radialGradient>`;
let gCables, gNorm;
function waveIcon(kind, x, y, p) {
  const w = 2.6, h = 1.2, d = { up: `M${x - w / 2},${y + h / 2} L${x + w / 2},${y - h / 2} L${x + w / 2},${y + h / 2}`, tri: `M${x - w / 2},${y + h / 2} L${x},${y - h / 2} L${x + w / 2},${y + h / 2}`,
    dn: `M${x - w / 2},${y + h / 2} L${x - w / 2},${y - h / 2} L${x + w / 2},${y + h / 2}`, sq: `M${x - w / 2},${y + h / 2} L${x - w / 2},${y - h / 2} L${x},${y - h / 2} L${x},${y + h / 2} L${x + w / 2},${y + h / 2}` }[kind];
  el('path', { d, fill: 'none', stroke: '#fff', 'stroke-width': .3, 'stroke-linejoin': 'round' }, p);
}
function build() {
  svg.innerHTML = ''; SL = {}; JACKS = {}; LAB = {}; LEDS = {};
  svg.setAttribute('viewBox', `0 0 ${PW} ${PH}`);
  const defs = el('defs', {}, svg); defs.innerHTML = DEFS;
  el('rect', { x: 0, y: 0, width: PW, height: PH, rx: 1.5, fill: '#121212' }, svg);
  el('rect', { x: 0, y: 0, width: STRIP, height: PH, fill: 'url(#alu)' }, svg);
  el('rect', { x: PW - STRIP, y: 0, width: STRIP, height: PH, fill: 'url(#alu)' }, svg);
  for (const x of [STRIP / 2, PW - STRIP / 2]) for (const y of [8, PH / 2, PH - 8]) { el('circle', { cx: x, cy: y, r: 1.6, fill: 'url(#screw)', stroke: '#555', 'stroke-width': .2 }, svg); el('line', { x1: x - 1.1, y1: y, x2: x + 1.1, y2: y, stroke: '#4a4740', 'stroke-width': .35 }, svg); }
  const gP = el('g', {}, svg);
  SEMI_DEF.tiers.forEach((tier, ti) => {
    const y0 = TOP + ti * TIERH, extra = (INW - tierW[ti]) / tier.secs.length; let x = STRIP;
    for (const s of tier.secs) { const w = secW(s) + extra; drawSection(s, x, y0, w, gP); x += w; }
  });
  // bottom strip : logo + name
  const yb = TOP + 3 * TIERH;
  el('line', { x1: STRIP + 1, y1: yb + 1, x2: PW - STRIP - 1, y2: yb + 1, stroke: '#5d5d5d', 'stroke-width': .35 }, svg);
  el('image', { href: LOGO, x: PW - STRIP - 6 - 40, y: yb + 4.5, width: 40, height: 40 * 49 / 273 }, svg);
  txt('3019 SEMI-MODULAR SYNTHESIZER', { x: STRIP + 6, y: yb + 10.4, fill: '#fff', 'font-family': FONT, 'font-weight': 700, 'font-size': 4.2, 'letter-spacing': .9 }, svg);
  gNorm = el('g', { id: 'normals', 'pointer-events': 'none' }, svg);
  gCables = el('g', { id: 'cables' }, svg);
  drawNormals(); renderCables(true);
}
function drawSection(s, X, y0, W, p) {
  const g = el('g', {}, p);
  el('rect', { x: X + .9, y: y0 + .9, width: W - 1.8, height: TIERH - 1.8, fill: 'none', stroke: '#6a6a6a', 'stroke-width': .35, rx: .6 }, g);
  el('line', { x1: X + .9, y1: y0 + 8.4, x2: X + W - .9, y2: y0 + 8.4, stroke: '#6a6a6a', 'stroke-width': .3 }, g);
  el('line', { x1: X + .9, y1: y0 + 90.5, x2: X + W - .9, y2: y0 + 90.5, stroke: '#4a4a4a', 'stroke-width': .3, 'stroke-dasharray': '1 .8' }, g);
  txt(s.title, { x: X + W / 2, y: y0 + 6.1, fill: '#fff', 'font-family': FONT, 'font-weight': 700, 'font-size': 3.3, 'text-anchor': 'middle', 'letter-spacing': .35 }, g);
  if (s.led) { const c = el('circle', { cx: X + W - 5, cy: y0 + 4.7, r: 1.5, fill: 'url(#lamp)', opacity: .15 }, g); el('circle', { cx: X + W - 5, cy: y0 + 4.7, r: 1.9, fill: 'none', stroke: '#888', 'stroke-width': .25 }, g); LEDS[s.id] = c; }
  const gw = s.sl.length * SP + (s.sw ? SWCOL : 0) + (s.midi ? SWCOL + 2 : 0) + (s.spk ? 38 : 0), x0 = X + (W - gw) / 2;
  if (s.spk) drawSpeaker(x0 + 19, y0 + 47, g);
  if (s.midi) drawMidiPanel(x0 + s.sl.length * SP + (SWCOL + 2) / 2, y0, g);
  s.sl.forEach(([k, label, , sc], i) => drawSlider(s.id + '.' + k, label, sc, x0 + SP * (i + .5), y0, g, s.title));
  (s.sw || []).forEach(([k, label, opts], i) => drawToggle(s.id + '.' + k, label, opts, x0 + s.sl.length * SP + (s.spk ? 38 : 0) + SWCOL / 2, y0 + (s.sw.length === 1 ? 46 : 34 + 32 * i), g, s.title));
  const cols = Math.max(s.in.length, s.out.length), pitch = Math.min(15, (W - 2 * PAD) / cols);
  [[s.in, Y_IN, 'in'], [s.out, Y_OUT, 'out']].forEach(([list, yy, d]) => {
    const off = X + W / 2 - pitch * list.length / 2;
    list.forEach(([k, label, t], c) => t === 'midi' ? drawMidiJack(label, d, off + pitch * (c + .5), y0 + yy, g) : drawJack(s.id + '.' + k, label, d, off + pitch * (c + .5), y0 + yy, g, s.title));
  });
}
function drawSlider(key, label, sc, x, y0, p, title) {
  LAB[key] = title + ' · ' + label;
  const lt = txt(label, { x, y: y0 + Y_LAB, fill: '#fff', 'font-family': FONT, 'font-weight': 700, 'font-size': 2.15, 'text-anchor': 'middle', 'letter-spacing': .15 }, p);
  if (label.length > 7) { lt.setAttribute('textLength', Math.min(12.6, label.length * 1.35)); lt.setAttribute('lengthAdjust', 'spacingAndGlyphs'); }
  const yT = y0 + Y_TOP, yB = yT + TRAVEL;
  // scale
  if (Array.isArray(sc)) {
    sc.forEach((nm, q) => { const yy = yB - TRAVEL * q / (sc.length - 1);
      el('line', { x1: x - 5.6, y1: yy, x2: x - 4.4, y2: yy, stroke: '#fff', 'stroke-width': .3 }, p);
      if (nm[0] === '~') waveIcon(nm.slice(1), x - 6.6, yy, p);
      else txt(nm, { x: x - 6.1, y: yy + .6, fill: '#fff', 'font-family': FONT, 'font-weight': 600, 'font-size': 1.7, 'text-anchor': 'end' }, p); });
  } else {
    for (let q = 0; q <= 10; q++) {
      const yy = yB - TRAVEL * q / 10;
      el('line', { x1: x - 5.6, y1: yy, x2: x - (q % 5 ? 4.9 : 4.3), y2: yy, stroke: '#fff', 'stroke-width': q % 5 ? .2 : .32 }, p);
      if (q % 2 === 0) { const n = sc === 'bi' ? q - 5 : sc === 'oct' ? (q - 5) * .6 : q; const s_ = sc === 'oct' ? (q % 5 === 0 ? String((q - 5) * 3 / 5) : '') : (sc === 'bi' && n > 0 ? '+' + n : String(n));
        if (s_) txt(s_, { x: x - 6.1, y: yy + .55, fill: '#fff', 'font-family': FONT, 'font-weight': 600, 'font-size': 1.6, 'text-anchor': 'end' }, p); }
    }
  }
  const g = el('g', { class: 'sl' }, p);
  el('rect', { x: x - 5, y: yT - 7, width: 10, height: TRAVEL + 14, fill: 'transparent' }, g);
  el('rect', { x: x - 1, y: yT - 3.5, width: 2, height: TRAVEL + 7, rx: 1, fill: '#000', stroke: '#3a3a3a', 'stroke-width': .25 }, g);
  const cap = el('g', {}, g);
  el('rect', { x: x - 4.5, y: -6.2, width: 9, height: 12.4, rx: 1.1, fill: 'url(#capg)', stroke: '#000', 'stroke-width': .3 }, cap);
  for (const dy of [-3.6, -2.2, 2.2, 3.6]) el('line', { x1: x - 3.6, y1: dy, x2: x + 3.6, y2: dy, stroke: '#333', 'stroke-width': .35 }, cap);
  el('line', { x1: x - 4.2, y1: 0, x2: x + 4.2, y2: 0, stroke: '#fff', 'stroke-width': .7 }, cap);
  SL[key] = { cap, yT, yB };
  bindSlider(g, key);
  draw(key);
}
function drawToggle(key, label, opts, x, y, p, title) {
  LAB[key] = title + ' · ' + label;
  txt(label, { x, y: y - 9.6, fill: '#fff', 'font-family': FONT, 'font-weight': 700, 'font-size': 2.15, 'text-anchor': 'middle' }, p);
  txt(opts[0], { x, y: y - 5.2, fill: '#fff', 'font-family': FONT, 'font-weight': 600, 'font-size': 1.8, 'text-anchor': 'middle' }, p);
  txt(opts[1], { x, y: y + 7.1, fill: '#fff', 'font-family': FONT, 'font-weight': 600, 'font-size': 1.8, 'text-anchor': 'middle' }, p);
  const g = el('g', { class: 'sw' }, p);
  el('rect', { x: x - 5, y: y - 6, width: 10, height: 12, fill: 'transparent' }, g);
  el('circle', { cx: x, cy: y, r: 2.9, fill: 'url(#nut)', stroke: '#555', 'stroke-width': .2 }, g);
  el('circle', { cx: x, cy: y, r: 1.4, fill: '#222' }, g);
  const lev = el('line', { x1: x, y1: y, x2: x, y2: y - 4.2, stroke: '#ddd', 'stroke-width': 1.3, 'stroke-linecap': 'round' }, g);
  SL[key] = { lev, x, y, toggle: 1 };
  g.addEventListener('pointerdown', e => { e.preventDefault(); setParam(key, PARAMS[key] ? 0 : 1); });
  draw(key);
}
const NSHORT = { 'out.in': 'IN L', 'kb.cv': 'KBD CV', 'kb.gate': 'KBD GATE', 'lfo1.out': 'LFO 1', 'lfo2.out': 'LFO 2', 'vco1.pulse': 'OSC 1 PULSE', 'vco1.saw': 'OSC 1 SAW',
  'vco2.saw': 'OSC 2 SAW', 'vco2.pulse': 'OSC 2 PULSE', 'vco3.saw': 'OSC 3 SAW', 'sh.noise': 'NOISE', 'sh.clock': 'CLOCK', 'sh.sh': 'S&H', 'ring.out': 'RING',
  'mix.out': 'MIX', 'env1.out': 'ENV 1', 'env2.out': 'ENV 2', 'vcf.out': 'LADDER', 'svf.out': 'ST. VAR.', 'vca.out': 'AMP', 'rev.out': 'REVERB' };
const pitchOf = () => 11.5;
// MIDI : 3.5 mm TRS jacks (type A), drawn with a dark nut and a frame : they carry MIDI, not CV
function drawMidiJack(label, d, x, y, p) {
  el('rect', { x: x - 5.6, y: y - 8.4, width: 11.2, height: 13.2, rx: 1, fill: 'none', stroke: '#9a9a9a', 'stroke-width': .3, 'stroke-dasharray': '.8 .5' }, p);
  txt(label, { x, y: y - 5.45, fill: '#ffae3d', 'font-family': FONT, 'font-weight': 700, 'font-size': 1.9, 'text-anchor': 'middle' }, p);
  el('polygon', { points: [0, 1, 2, 3, 4, 5].map(a => (x + 3.3 * Math.cos(a * Math.PI / 3 + Math.PI / 6)) + ',' + (y + 3.3 * Math.sin(a * Math.PI / 3 + Math.PI / 6))).join(' '), fill: '#3a3a3a', stroke: '#777', 'stroke-width': .2 }, p);
  el('circle', { cx: x, cy: y, r: 2.0, fill: '#060606', stroke: '#444', 'stroke-width': .2 }, p);
}
// LEARN button (MIDI channel = channel of the next note) and MIDI activity LED ; MIDI IN / OUT and USB are on the back panel
function drawMidiPanel(x, y0, p) {
  txt('MIDI', { x, y: y0 + 36, fill: '#fff', 'font-family': FONT, 'font-weight': 700, 'font-size': 2.15, 'text-anchor': 'middle' }, p);
  const c = el('circle', { cx: x, cy: y0 + 40, r: 1.5, fill: 'url(#lamp)', opacity: .15 }, p); el('circle', { cx: x, cy: y0 + 40, r: 1.9, fill: 'none', stroke: '#888', 'stroke-width': .25 }, p); LEDS.midi = c;
  txt('LEARN', { x, y: y0 + 56, fill: '#fff', 'font-family': FONT, 'font-weight': 700, 'font-size': 2.15, 'text-anchor': 'middle' }, p);
  el('circle', { cx: x, cy: y0 + 62, r: 3.4, fill: 'url(#nut)', stroke: '#555', 'stroke-width': .2 }, p);
  el('circle', { cx: x, cy: y0 + 62, r: 2.3, fill: '#1b1b1b', stroke: '#000', 'stroke-width': .2 }, p);
}
// 40 mm speaker behind a grille of holes
function drawSpeaker(x, y, p) {
  el('circle', { cx: x, cy: y, r: 18, fill: '#0b0b0b', stroke: '#6a6a6a', 'stroke-width': .35 }, p);
  for (let r = 2.6; r < 16.5; r += 2.6) { const n = Math.max(1, Math.round(2 * Math.PI * r / 2.6));
    for (let k = 0; k < n; k++) { const a = 2 * Math.PI * k / n + r; el('circle', { cx: x + r * Math.cos(a), cy: y + r * Math.sin(a), r: .75, fill: '#2a2a2a' }, p); } }
  el('circle', { cx: x, cy: y, r: .75, fill: '#2a2a2a' }, p);
}
function drawJack(key, label, d, x, y, p, title) {
  LAB[key] = title + ' · ' + (label || 'MULT') + (d === 'out' ? ' (sortie)' : ' (entrée)');
  if (label) {
    const w = Math.max(7.5, label.length * 1.15 + 2.2);
    if (d === 'out') { el('rect', { x: x - w / 2, y: y - 7.6, width: w, height: 2.9, rx: .5, fill: '#e9e9e9' }, p); txt(label, { x, y: y - 5.45, fill: '#111', 'font-family': FONT, 'font-weight': 700, 'font-size': 2, 'text-anchor': 'middle' }, p); }
    else txt(label, { x, y: y - 5.45, fill: '#fff', 'font-family': FONT, 'font-weight': 700, 'font-size': 2, 'text-anchor': 'middle' }, p);
  } else if (d === 'out') el('rect', { x: x - 3.75, y: y - 7.6, width: 7.5, height: 2.9, rx: .5, fill: '#e9e9e9' }, p);
  const nsrc = d === 'in' ? SEMI_DEF.normals[key] : undefined;
  if (nsrc !== undefined) {                                   // printed normal : what this input receives with nothing plugged
    const nm = typeof nsrc === 'number' ? '+' + nsrc + ' V' : (NSHORT[nsrc] || nsrc);
    const t = txt(nm, { x, y: y + 5.1, fill: '#a8a8a8', 'font-family': FONT, 'font-weight': 600, 'font-size': 1.55, 'text-anchor': 'middle', 'letter-spacing': .05 }, p);
    if (nm.length > 8) { t.setAttribute('textLength', Math.min(pitchOf(x), nm.length * 0.95)); t.setAttribute('lengthAdjust', 'spacingAndGlyphs'); }
  }
  const g = el('g', { class: 'jack' }, p); g.dataset.key = key;
  el('circle', { cx: x, cy: y, r: 4.6, fill: 'transparent' }, g);
  el('polygon', { points: [0, 1, 2, 3, 4, 5].map(a => (x + 3.3 * Math.cos(a * Math.PI / 3 + Math.PI / 6)) + ',' + (y + 3.3 * Math.sin(a * Math.PI / 3 + Math.PI / 6))).join(' '), fill: 'url(#nut)', stroke: '#666', 'stroke-width': .2 }, g);
  el('circle', { cx: x, cy: y, r: 2.0, fill: '#060606', stroke: '#444', 'stroke-width': .2 }, g);
  JACKS[key] = { x, y, d, g };
  bindJack(g, key);
}
function draw(key) {
  const S = SL[key]; if (!S) return; const v = PARAMS[key];
  if (S.toggle) S.lev.setAttribute('y2', S.y + (v ? 4.2 : -4.2));
  else S.cap.setAttribute('transform', `translate(0 ${S.yB - TRAVEL * v})`);
}
// ---------------------------------------------------------------- sliders
function svgPt(e) { const p = svg.createSVGPoint(); p.x = e.clientX; p.y = e.clientY; return p.matrixTransform(svg.getScreenCTM().inverse()); }
function setParam(key, v) { PARAMS[key] = v; draw(key); show(key); send({ t: 'p', k: key, v }); }
function bindSlider(g, key) {
  let st = null, lastTap = 0;
  g.addEventListener('pointerdown', e => {
    e.preventDefault(); e.stopPropagation(); g.setPointerCapture(e.pointerId);
    const now = performance.now(); if (now - lastTap < 320) { setParam(key, DEFV[key]); lastTap = 0; st = null; return; } lastTap = now;
    st = { y: svgPt(e).y, v: PARAMS[key] }; show(key);
  });
  g.addEventListener('pointermove', e => { if (!st) return; const v = Math.min(1, Math.max(0, st.v - (svgPt(e).y - st.y) / TRAVEL)); setParam(key, Math.round(v * 1000) / 1000); });
  const up = () => { st = null; }; g.addEventListener('pointerup', up); g.addEventListener('pointercancel', up);
}
// ---------------------------------------------------------------- normals overlay and cables
function drawNormals() {
  gNorm.innerHTML = '';
  for (const [dst, src] of Object.entries(SEMI_DEF.normals)) {
    if (typeof src !== 'string') continue; const A = JACKS[src], B = JACKS[dst]; if (!A || !B) continue;
    const plugged = cables.some(c => c.dst === dst);
    el('path', { d: cablePath(A, B, 3), fill: 'none', stroke: plugged ? '#555' : '#ffae3d', 'stroke-width': .45, 'stroke-dasharray': '1.4 1', opacity: .8 }, gNorm);
    el('circle', { cx: B.x, cy: B.y, r: .9, fill: plugged ? '#555' : '#ffae3d' }, gNorm);
  }
}
const PAL = ['#c8332b', '#e3b23c', '#2f6fb5', '#2f8f5b', '#e9e2cf', '#d26a1e', '#7a4fa0', '#3fb8b0'];
let ci = 0;
function cablePath(a, b, sagMin = 6) {
  const dx = b.x - a.x, d = Math.hypot(dx, b.y - a.y), sag = sagMin + d * 0.14, lim = PH - 2;
  return `M${a.x},${a.y} C${a.x + dx * .15},${Math.min(a.y + sag, lim)} ${b.x - dx * .15},${Math.min(b.y + sag, lim)} ${b.x},${b.y}`;
}
function cableG(a, b, col, parent) {
  const g = el('g', {}, parent), d = cablePath(a, b);
  el('path', { d, fill: 'none', stroke: 'rgba(0,0,0,.45)', 'stroke-width': 2.4, transform: 'translate(.6 1.5)' }, g);
  el('path', { d, fill: 'none', stroke: col, 'stroke-width': 1.7, 'stroke-linecap': 'round' }, g);
  el('path', { d, fill: 'none', stroke: 'rgba(255,255,255,.22)', 'stroke-width': .45, transform: 'translate(-.3 -.3)' }, g);
  for (const p of [a, b]) { el('circle', { cx: p.x, cy: p.y, r: 2.9, fill: col, stroke: '#0a0908', 'stroke-width': .6 }, g); el('circle', { cx: p.x - .7, cy: p.y - .7, r: .9, fill: 'rgba(255,255,255,.35)' }, g); }
  return g;
}
function renderCables(quiet) {
  gCables.innerHTML = '';
  for (const c of cables) cableG(JACKS[c.src], JACKS[c.dst], c.col, gCables);
  drawNormals();
  if (!quiet) send({ t: 'cables', list: cables.map(c => [c.src, c.dst]) });
}
function connect(a, b, col) {
  if (a === b) return; const A = JACKS[a], B = JACKS[b]; if (!A || !B) return;
  if (A.d === B.d) { status.textContent = A.d === 'in' ? 'Deux entrées : branche une sortie' : 'Deux sorties : branche une entrée'; return; }
  if (A.d === 'in') [a, b] = [b, a];
  cables = cables.filter(c => c.dst !== b);
  cables.push({ src: a, dst: b, col: col || PAL[ci++ % PAL.length] });
  status.textContent = LAB[a].replace(' (sortie)', '') + '  →  ' + LAB[b].replace(' (entrée)', '');
  renderCables();
}
let drag = null;
function bindJack(g, key) {
  g.addEventListener('pointerdown', e => { e.preventDefault(); e.stopPropagation(); g.setPointerCapture(e.pointerId); drag = { key, moved: false, x0: e.clientX, y0: e.clientY, col: PAL[ci % PAL.length], tmp: null }; status.textContent = LAB[key]; });
  g.addEventListener('pointermove', e => {
    if (!drag) return; if (Math.hypot(e.clientX - drag.x0, e.clientY - drag.y0) > 6) drag.moved = true; if (!drag.moved) return;
    if (drag.tmp) drag.tmp.remove(); drag.tmp = cableG(JACKS[drag.key], svgPt(e), drag.col, svg); drag.tmp.setAttribute('opacity', .85); drag.tmp.setAttribute('pointer-events', 'none');
  });
  g.addEventListener('pointerup', e => {
    if (!drag) return; const d = drag; drag = null; if (d.tmp) d.tmp.remove();
    if (!d.moved) { const n = cables.length; cables = cables.filter(c => c.src !== d.key && c.dst !== d.key); if (cables.length !== n) renderCables(); return; }
    const t = document.elementFromPoint(e.clientX, e.clientY); let jg = t && t.closest && t.closest('.jack');
    if (!jg) { const p = svgPt(e); let best = null, bd = 8; for (const k in JACKS) { const J = JACKS[k], dd = Math.hypot(J.x - p.x, J.y - p.y); if (dd < bd) { bd = dd; best = J.g; } } jg = best; }
    if (jg && jg.dataset.key) { ci++; connect(d.key, jg.dataset.key, d.col); }
  });
  g.addEventListener('pointercancel', () => { if (drag && drag.tmp) drag.tmp.remove(); drag = null; });
}
// ---------------------------------------------------------------- audio
let ctx = null, node = null, engine = null, sp = null, audioOn = false;
function send(d) { if (node) node.port.postMessage(d); else if (engine) engine.msg(d); }
const fullState = () => ({ t: 'state', params: PARAMS, cables: cables.map(c => [c.src, c.dst]) });
const scope = $('#scope'), sctx = scope.getContext('2d');
function onReport(r) {
  for (const id in r.leds) if (LEDS[id]) LEDS[id].setAttribute('opacity', (0.15 + 0.85 * Math.min(1, r.leds[id])).toFixed(2));
  if (r.scope && scope.offsetParent) {
    const W = scope.width, H = scope.height, s = r.scope; sctx.clearRect(0, 0, W, H);
    sctx.strokeStyle = '#2a2622'; sctx.beginPath(); sctx.moveTo(0, H / 2); sctx.lineTo(W, H / 2); sctx.stroke();
    let z = 1; while (z < 400 && !(s[z - 1] < 0 && s[z] >= 0)) z++;
    sctx.strokeStyle = '#ffae3d'; sctx.lineWidth = 2; sctx.beginPath();
    for (let x = 0; x < W; x++) { const v = s[(z + x * 2) % 1024] || 0, y = H / 2 - v / 10 * (H / 2 - 2); x ? sctx.lineTo(x, y) : sctx.moveTo(x, y); }
    sctx.stroke();
  }
}
async function startAudio() {
  if (ctx) { if (ctx.state !== 'running') await ctx.resume(); audioOn = true; $('#pled').classList.add('on'); return; }
  ctx = new (window.AudioContext || window.webkitAudioContext)({ latencyHint: 'interactive' });
  try {
    const url = URL.createObjectURL(new Blob([WORKLET_SRC], { type: 'application/javascript' }));
    await ctx.audioWorklet.addModule(url);
    node = new AudioWorkletNode(ctx, 'semi-sim', { numberOfInputs: 0, numberOfOutputs: 1, outputChannelCount: [2] });
    node.port.onmessage = e => onReport(e.data); node.connect(ctx.destination); node.port.postMessage(fullState());
  } catch (err) {
    node = null; engine = new SemiEngine(ctx.sampleRate); engine.msg(fullState()); engine.report = r => requestAnimationFrame(() => onReport(r));
    sp = ctx.createScriptProcessor(2048, 0, 2);
    sp.onaudioprocess = e => engine.render(e.outputBuffer.getChannelData(0), e.outputBuffer.getChannelData(1), e.outputBuffer.length);
    sp.connect(ctx.destination);
  }
  await ctx.resume(); audioOn = true; $('#pled').classList.add('on'); initMidi();
}
// ---------------------------------------------------------------- Web MIDI : a real controller plays the KEYBOARD · MIDI section (CV, GATE, VEL, MOD)
let midiOn = false;
function midiBlink() { if (LEDS.midi) { LEDS.midi.setAttribute('opacity', 1); clearTimeout(midiBlink.t); midiBlink.t = setTimeout(() => LEDS.midi.setAttribute('opacity', .15), 80); } }
function onMidi(e) {
  const [st, d1, d2] = e.data, c = st & 0xf0; midiBlink();
  if (c === 0x90 && d2 > 0) { send({ t: 'note', on: 1, n: d1, v: d2 }); keyEls[d1] && keyEls[d1].classList.add('on'); }
  else if (c === 0x80 || (c === 0x90 && d2 === 0)) { send({ t: 'note', on: 0, n: d1 }); if (!noteCnt[d1] && keyEls[d1]) keyEls[d1].classList.remove('on'); }
  else if (c === 0xb0 && d1 === 1) send({ t: 'cc1', v: d2 });
}
async function initMidi() {
  if (midiOn || !navigator.requestMIDIAccess) return; midiOn = true;
  try {
    const m = await navigator.requestMIDIAccess();
    const hook = () => { const names = []; m.inputs.forEach(inp => { inp.onmidimessage = onMidi; names.push(inp.name); }); if (names.length) status.textContent = 'MIDI : ' + names.join(', '); };
    hook(); m.onstatechange = hook;
  } catch (err) { /* no MIDI permission here : the on-screen keyboard still works */ }
}
async function stopAudio() { if (ctx) await ctx.suspend(); audioOn = false; $('#pled').classList.remove('on'); }
$('#startBtn').onclick = () => { $('#startOv').hidden = true; startAudio(); };
$('#power').onclick = () => audioOn ? stopAudio() : startAudio();
$('#bSeq').onclick = () => { PARAMS['kb.seq'] = PARAMS['kb.seq'] ? 0 : 1; send({ t: 'p', k: 'kb.seq', v: PARAMS['kb.seq'] }); $('#sled').classList.toggle('on', !!PARAMS['kb.seq']); };
$('#bNorm').onclick = () => { const on = svg.classList.toggle('norm'); $('#nled').classList.toggle('on', on); };
$('#bClear').onclick = () => { cables = []; renderCables(); };
$('#bReset').onclick = () => { const seq = PARAMS['kb.seq']; PARAMS = Object.assign({}, DEFV, { 'kb.seq': seq }); for (const k in SL) draw(k); send(fullState()); };
$('#cabOp').onclick = () => svg.classList.toggle('faded');
$('#help').onclick = () => { $('#helpOv').hidden = false; };
$('#helpClose').onclick = () => { $('#helpOv').hidden = true; };
// ---------------------------------------------------------------- keyboard (same as the Eurorack simulator)
const kbd = $('#kbd'); let kbBase = 48, keyEls = {}; const kbPtr = new Map(), noteCnt = {};
const elh = (t, c, h) => { const e = document.createElement(t); if (c) e.className = c; if (h != null) e.innerHTML = h; return e; };
const clamp = (v, a, b) => v < a ? a : v > b ? b : v;
function buildKbd() {
  kbd.innerHTML = ''; keyEls = {}; const w = kbd.clientWidth || 300; const nW = clamp(Math.floor(w / 36), 8, 36), kw = w / nW, WS = [0, 2, 4, 5, 7, 9, 11];
  for (let i = 0; i < nW; i++) {
    const s = WS[i % 7], n = kbBase + Math.floor(i / 7) * 12 + s; const e = elh('div', 'wk', s === 0 ? `<span>C${Math.floor(n / 12) - 1}</span>` : '');
    e.style.left = i * kw + 'px'; e.style.width = kw + 'px'; e.dataset.n = n; kbd.appendChild(e); keyEls[n] = e;
    if ([0, 2, 5, 7, 9].includes(s) && i < nW - 1) { const b = elh('div', 'bk'); b.style.left = (i + 1) * kw - kw * 0.31 + 'px'; b.style.width = kw * 0.62 + 'px'; b.dataset.n = n + 1; kbd.appendChild(b); keyEls[n + 1] = b; }
  }
  $('#kOct').textContent = 'C' + (Math.floor(kbBase / 12) - 1);
  for (const n in noteCnt) if (noteCnt[n] > 0 && keyEls[n]) keyEls[n].classList.add('on');
}
let hold = false, physTotal = 0; const phys = {}, latched = new Set();
function releaseLatched() { for (const l of latched) rawOff(l); latched.clear(); }
function setHold(on) { hold = on; $('#kHold').classList.toggle('on', on); $('#hled').classList.toggle('on', on); if (!hold) releaseLatched(); }
$('#kHold').onclick = () => setHold(!hold);
function showKbd(on) { $('#kbdWrap').hidden = !on; $('#kled').classList.toggle('on', on); if (on) buildKbd(); fit(); }
$('#kbToggle').onclick = () => showKbd($('#kbdWrap').hidden);
function noteOn(n) { if (hold && physTotal === 0 && latched.size) releaseLatched(); if (latched.has(n)) { latched.delete(n); rawOff(n); } phys[n] = (phys[n] || 0) + 1; physTotal++; rawOn(n); }
function noteOff(n) { if (!phys[n]) return; phys[n]--; physTotal--; if (hold) latched.add(n); else rawOff(n); }
function rawOn(n) { if (!audioOn) { $('#startOv').hidden = true; startAudio(); } noteCnt[n] = (noteCnt[n] || 0) + 1; if (noteCnt[n] === 1) { send({ t: 'note', on: 1, n }); keyEls[n] && keyEls[n].classList.add('on'); } }
function rawOff(n) { if (!noteCnt[n]) return; noteCnt[n]--; if (noteCnt[n] === 0) { send({ t: 'note', on: 0, n }); keyEls[n] && keyEls[n].classList.remove('on'); } }
function noteAt(e) { const t = document.elementFromPoint(e.clientX, e.clientY); const k = t && t.closest && t.closest('.wk,.bk'); return k && kbd.contains(k) ? +k.dataset.n : null; }
kbd.addEventListener('pointerdown', e => { e.preventDefault(); try { kbd.setPointerCapture(e.pointerId); } catch (_) { } const n = noteAt(e); if (n != null) { kbPtr.set(e.pointerId, n); noteOn(n); } });
kbd.addEventListener('pointermove', e => { if (!kbPtr.has(e.pointerId)) return; const cur = kbPtr.get(e.pointerId), n = noteAt(e); if (n !== cur) { if (cur != null) noteOff(cur); if (n != null) noteOn(n); kbPtr.set(e.pointerId, n); } });
const kUp = e => { if (!kbPtr.has(e.pointerId)) return; const n = kbPtr.get(e.pointerId); if (n != null) noteOff(n); kbPtr.delete(e.pointerId); };
kbd.addEventListener('pointerup', kUp); kbd.addEventListener('pointercancel', kUp);
$('#kUp').onclick = () => { kbBase = Math.min(84, kbBase + 12); buildKbd(); }; $('#kDn').onclick = () => { kbBase = Math.max(24, kbBase - 12); buildKbd(); };
const KEYMAP = { a: 0, w: 1, s: 2, e: 3, d: 4, f: 5, t: 6, g: 7, y: 8, h: 9, u: 10, j: 11, k: 12, o: 13, l: 14, p: 15 }; const qwHeld = {};
window.addEventListener('keydown', e => {
  if (e.repeat || e.metaKey || e.ctrlKey) return; const k = e.key.toLowerCase();
  if (k === 'z') { kbBase = Math.max(24, kbBase - 12); buildKbd(); return; } if (k === 'x') { kbBase = Math.min(84, kbBase + 12); buildKbd(); return; }
  if (k in KEYMAP && !qwHeld[k]) { const n = kbBase + 12 + KEYMAP[k]; qwHeld[k] = n; noteOn(n); }
});
window.addEventListener('keyup', e => { const k = e.key.toLowerCase(); if (qwHeld[k] != null) { noteOff(qwHeld[k]); delete qwHeld[k]; } });
// ---------------------------------------------------------------- zoom : fit the panel width by default
const wrap = $('#wrap'); let zoom = 1;
function fit() { const w = Math.max(320, wrap.clientWidth - 56) * zoom; svg.style.width = w + 'px'; svg.style.height = (w * PH / PW) + 'px'; }
$('#zFit').onclick = () => { zoom = 1; fit(); };
$('#zIn').onclick = () => { zoom = Math.min(4, zoom * 1.25); fit(); };
$('#zOut').onclick = () => { zoom = Math.max(.3, zoom / 1.25); fit(); };
window.addEventListener('resize', () => { fit(); buildKbd(); });
if (new URLSearchParams(location.search).has('norm')) { svg.classList.add('norm'); $('#nled').classList.add('on'); }
if (new URLSearchParams(location.search).has('noov')) $('#startOv').hidden = true;
build(); buildKbd(); fit();
window.SEMI_SIZE = { PW, PH };
