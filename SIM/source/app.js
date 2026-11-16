const DATA = __DATA__;
const $ = s => document.querySelector(s);
const PH = 128.5, MX = 1.2, MY = 4.5, HPMM = 5.08, ROWHP = 104, GAPY = 5;
const ROWW = ROWHP * HPMM, TW = ROWW + 2 * MX, RH = PH + 2 * MY;
const HP = { vco: 12, mix: 8, vcf: 10, vca: 6, ad: 6, adsr: 8, cx: 30, stg: 30, lfo: 12, sim: 10 };
const DESC = {
  vco: 'Oscillateur façon 921 : RANGE LO à 2′, 4 formes d’onde, FM, PWM, sync et sortie BLEND.',
  mix: 'Mixeur 4 entrées façon CP3, MASTER GAIN avec saturation douce, OUT et −OUT.',
  vcf: 'Filtre en échelle 4 pôles, passage LP → BP → HP, emphasis jusqu’à l’auto-oscillation, entrée CONTOUR.',
  vca: 'VCA façon 902 : entrées différentielles, réponse LIN ↔ EXP, 3 entrées CV.',
  ad: 'Enveloppe AD à cœur OTA, 0,8 ms à 8 s, CV sur attaque et decay, mode CYCLE (LFO).',
  adsr: 'Enveloppe ADSR façon Moog 911 : courbes RC, attaque ≈ 2 ms à 10 s, sustain 0 à 10 V, sorties OUT et −OUT.',
  cx: 'Oscillateur complexe façon Buchla 259 : oscillateur de modulation, MOD INDEX vers AMPL / PITCH / TIMBRE, PHASE LOCK, oscillateur principal et HARMONICS (TIMBRE, SYMMETRY, ORDER).',
  stg: 'Séquenceur 8 étapes façon Verbos Multistage (RP2040) : A, B et TIME par étape, SLIDE, LOOP / ONCE / ENV, entrées SELECT et sorties GATE par étape.',
  lfo: 'QUAD LFO (RP2040) : 4 LFO SINE / SAW / SQUARE, FREE (0,02 à 25 Hz) ou CLOCKED (/16 à ×16 du CLOCK), entrée RESET.',
  sim: 'Outil du simulateur : séquence, CV/GATE du clavier, sortie son et oscilloscope.',
};
const TYPE = {}; DATA.modules.forEach(m => TYPE[m.id] = m);
const svg = $('#rack'), NS = 'http://www.w3.org/2000/svg';
const el = (t, a, p) => { const e = document.createElementNS(NS, t); for (const k in a) e.setAttribute(k, a[k]); if (p) p.appendChild(e); return e; };
let L = null;                 // layout { rows:[[id..]], mods:{id:{type,n}} }
let PARAMS = {}, CTL = {}, JACKS = {}, LAB = {}, POS = {}, PLEDS = [], SLEDS = {};
let cables = [], moveMode = false, nRows = 1, TH = RH;
const DEFV = {}; DATA.modules.forEach(m => m.ctl.forEach(c => { if (c.v !== undefined) DEFV[m.id + '.' + c.id] = c.v; }));
const defaultLayout = () => ({ rows: [['vco', 'mix', 'vcf', 'vca', 'ad', 'adsr', 'sim'], ['cx', 'stg', 'lfo']], mods: { lfo: { type: 'lfo', n: 1 }, stg: { type: 'stg', n: 1 }, adsr: { type: 'adsr', n: 1 }, cx: { type: 'cx', n: 1 }, vco: { type: 'vco', n: 1 }, mix: { type: 'mix', n: 1 }, vcf: { type: 'vcf', n: 1 }, vca: { type: 'vca', n: 1 }, ad: { type: 'ad', n: 1 }, sim: { type: 'sim', n: 1 } } });
const DEFS_SVG = `
<linearGradient id="alu" x1="0" x2="1"><stop offset="0" stop-color="#8d8d8d"/><stop offset=".5" stop-color="#e6e6e6"/><stop offset="1" stop-color="#9c9c9c"/></linearGradient>
<linearGradient id="wood" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#7d4828"/><stop offset=".55" stop-color="#5c331b"/><stop offset="1" stop-color="#45260f"/></linearGradient>
<radialGradient id="cap" cx=".4" cy=".35" r=".7"><stop offset="0" stop-color="#d6d1c3"/><stop offset="1" stop-color="#a39e8f"/></radialGradient>
<radialGradient id="nut" cx=".4" cy=".35" r=".75"><stop offset="0" stop-color="#f0f0eb"/><stop offset=".6" stop-color="#b7b7b1"/><stop offset="1" stop-color="#6f6e68"/></radialGradient>
<radialGradient id="screw" cx=".4" cy=".35" r=".7"><stop offset="0" stop-color="#d2cdc1"/><stop offset="1" stop-color="#6d685e"/></radialGradient>
<radialGradient id="ledg" cx=".4" cy=".35"><stop offset="0" stop-color="#fff3cc"/><stop offset=".45" stop-color="#ff5a4a"/><stop offset="1" stop-color="#9c1d16"/></radialGradient>
<radialGradient id="lamp" cx=".4" cy=".35"><stop offset="0" stop-color="#fff3cc"/><stop offset=".45" stop-color="#ffae3d"/><stop offset="1" stop-color="#b5560e"/></radialGradient>
<pattern id="railp" width="5.08" height="3.4" patternUnits="userSpaceOnUse"><rect width="5.08" height="3.4" fill="#26231f"/><circle cx="2.54" cy="1.7" r=".55" fill="#958e80"/><circle cx="2.54" cy="1.7" r=".75" fill="none" stroke="#36322d" stroke-width=".2"/></pattern>`;
const toastEl = $('#toast'); let toastT;
function toast(t) { toastEl.textContent = t; toastEl.hidden = false; clearTimeout(toastT); toastT = setTimeout(() => toastEl.hidden = true, 2200); }
// ------------------------------------------------------------------ build the whole rack
function knobGfx(g, s) {
  el('circle', { r: 5.4 * s, fill: '#151515', stroke: '#777', 'stroke-width': .25 }, g);
  const rot = el('g', {}, g);
  el('circle', { r: 3.4 * s, fill: 'url(#cap)', stroke: '#666', 'stroke-width': .15 }, rot);
  el('line', { x1: 0, y1: -1.0 * s, x2: 0, y2: -3.1 * s, stroke: '#2a2a2a', 'stroke-width': .45 * s, 'stroke-linecap': 'round' }, rot);
  el('line', { x1: 0, y1: -3.75 * s, x2: 0, y2: -5.15 * s, stroke: '#fff', 'stroke-width': .5, 'stroke-linecap': 'round' }, rot);
  return rot;
}
const rowY = r => r * (RH + GAPY);
let gCables, gPanels;
function build() {
  L.rows = L.rows.filter(r => r.length);
  if (!L.rows.length) L.rows.push([]);
  nRows = L.rows.length + (moveMode ? 1 : 0);
  TH = nRows * RH + (nRows - 1) * GAPY;
  svg.innerHTML = ''; CTL = {}; JACKS = {}; LAB = {}; POS = {}; PLEDS = []; SLEDS = {};
  svg.setAttribute('viewBox', `0 0 ${TW} ${TH}`);
  el('defs', {}, svg).innerHTML = DEFS_SVG;
  for (let r = 0; r < nRows; r++) {
    const y = rowY(r);
    if (r > 0) el('rect', { x: 0, y: y - GAPY, width: TW, height: GAPY, fill: 'url(#wood)' }, svg);
    el('rect', { x: 0, y, width: TW, height: RH, fill: '#0b0a09' }, svg);
    for (let k = 1; k < ROWHP; k++) el('line', { x1: MX + k * HPMM, x2: MX + k * HPMM, y1: y + MY, y2: y + MY + PH, stroke: '#141210', 'stroke-width': .15 }, svg);
    el('rect', { x: 0, y: y + MY - 3.4, width: TW, height: 3.4, fill: 'url(#railp)' }, svg);
    el('rect', { x: 0, y: y + MY + PH, width: TW, height: 3.4, fill: 'url(#railp)' }, svg);
    if (r >= L.rows.length) { const t = el('text', { x: TW / 2, y: y + RH / 2, 'text-anchor': 'middle', 'dominant-baseline': 'central', fill: '#5a5148', 'font-size': 6, 'font-family': 'Barlow Condensed,Arial Narrow,sans-serif', 'letter-spacing': '.3' }, svg); t.textContent = 'GLISSE UN MODULE ICI POUR UNE NOUVELLE RANGÉE'; }
  }
  gPanels = el('g', {}, svg);
  const count = {};
  L.rows.forEach((row, r) => {
    let hp = 0;
    row.forEach(id => {
      const mi = L.mods[id], m = TYPE[mi.type];
      const x = MX + hp * HPMM, y = rowY(r) + MY;
      POS[id] = { x, y, r, w: m.w };
      drawPanel(id, mi, m, x, y);
      hp += HP[mi.type];
    });
  });
  gCables = el('g', { id: 'cables', 'pointer-events': 'none' }, svg);
  svg.querySelectorAll('.ctl,.jack,.pan').forEach(n => n.addEventListener('touchstart', e => { if (!n.classList.contains('pan') || moveMode) e.preventDefault(); }, { passive: false }));
  cables = cables.filter(c => JACKS[c.src] && JACKS[c.dst]);
  Object.keys(PARAMS).forEach(draw);
  renderCables(true);
  fit();
  send(fullState());
}
function drawPanel(id, mi, m, X0, Y0) {
  const g = el('g', { transform: `translate(${X0},${Y0})`, class: 'pan' }, gPanels);
  g.dataset.id = id;
  const name = m.name + (mi.n > 1 ? ' ' + mi.n : '');
  el('rect', { x: .25, y: .6, width: m.w, height: PH, fill: 'rgba(0,0,0,.6)' }, g);
  el('rect', { x: 0, y: 0, width: m.w, height: PH, fill: '#111' }, g);
  el('rect', { x: 0, y: 0, width: 1.6, height: PH, fill: 'url(#alu)' }, g);
  el('rect', { x: m.w - 1.6, y: 0, width: 1.6, height: PH, fill: 'url(#alu)' }, g);
  m.lines.forEach(([x1, y1, x2, y2, w]) => el('line', { x1, y1, x2, y2, stroke: w >= .29 ? '#9a9a9a' : '#fff', 'stroke-width': w >= .29 ? .3 : Math.max(w, .18), 'stroke-linecap': 'round' }, g));
  m.text.forEach(([t, x, y, s], i) => {
    const e = el('text', { x, y: y + s * 0.02, 'font-size': s * 1.38, 'font-weight': 700, fill: '#fff', 'text-anchor': 'middle', 'dominant-baseline': 'central', 'font-family': 'Helvetica Neue,Arial,DejaVu Sans,sans-serif' }, g);
    e.textContent = t;
  });
  if (mi.n > 1) { const t = el('text', { x: m.w - 3.2, y: 9.2, 'font-size': 1.6, fill: '#9a9a9a', 'text-anchor': 'middle', 'font-family': 'JetBrains Mono,monospace' }, g); t.textContent = '#' + mi.n; }
  const Lg = m.logo; el('image', { href: DATA.logo, x: Lg[0], y: Lg[1], width: Lg[2], height: Lg[3], preserveAspectRatio: 'none' }, g);
  m.holes.forEach(([hx, hy]) => {
    el('rect', { x: hx - 2.6, y: hy - 1.6, width: 5.2, height: 3.2, rx: 1.6, fill: '#050505' }, g);
    const s = el('g', { transform: `translate(${hx},${hy})` }, g);
    el('circle', { r: 2.3, fill: 'url(#screw)', stroke: '#2c2a26', 'stroke-width': .25 }, s);
    el('line', { x1: -1.4, y1: -.5, x2: 1.4, y2: .5, stroke: '#3a3733', 'stroke-width': .4 }, s);
  });
  m.ctl.forEach(c => {
    const key = id + '.' + c.id;
    if (c.label) LAB[key] = name + ' · ' + c.label;
    if (c.t === 'knob' || c.t === 'rotary') {
      const cg = el('g', { transform: `translate(${c.x},${c.y})`, class: 'ctl' }, g);
      const rot = knobGfx(cg, c.s);
      el('circle', { r: 5.6 * c.s + 1, fill: 'transparent' }, cg);
      CTL[key] = { c, rot, kind: c.t, def: c.v };
      bindKnob(cg, key);
    } else if (c.t === 'toggle') {
      const cg = el('g', { transform: `translate(${c.x},${c.y})`, class: 'ctl' }, g);
      el('circle', { r: 3.0, fill: 'url(#nut)', stroke: '#555', 'stroke-width': .2 }, cg);
      const lev = el('line', { x1: 0, y1: 0, x2: -3.6, y2: 0, stroke: '#e4e4e4', 'stroke-width': 1.5, 'stroke-linecap': 'round' }, cg);
      const tip = el('circle', { r: 1.0, fill: '#bbb' }, cg);
      el('rect', { x: -6, y: -4, width: 12, height: 8, fill: 'transparent' }, cg);
      CTL[key] = { c, lev, tip, kind: 'toggle', def: c.v };
      cg.addEventListener('pointerdown', e => { e.preventDefault(); const n = c.opts ? c.opts.length : 2; setParam(key, (PARAMS[key] + 1) % n); });
    } else if (c.t === 'button') {
      const cg = el('g', { transform: `translate(${c.x},${c.y})`, class: 'ctl' }, g);
      el('rect', { x: -3.6, y: -3.6, width: 7.2, height: 7.2, rx: 1.2, fill: '#0d0c0b', stroke: '#3b3733', 'stroke-width': .3 }, cg);
      const led = el('circle', { r: 1.4, fill: 'url(#lamp)' }, cg);
      CTL[key] = { c, led, kind: 'button', def: c.v };
      cg.addEventListener('pointerdown', e => { e.preventDefault(); setParam(key, PARAMS[key] ? 0 : 1); });
    } else if (c.t === 'mbutton' || c.t === 'cbutton' || c.t === 'sbutton') {
      const cg = el('g', { transform: `translate(${c.x},${c.y})`, class: 'ctl' }, g);
      el('circle', { r: 3.3, fill: '#1c1c1c', stroke: '#777', 'stroke-width': .25 }, cg);
      el('circle', { r: 2.6, fill: '#2c2c2c', stroke: '#555', 'stroke-width': .15 }, cg);
      el('circle', { r: 4.6, fill: 'transparent' }, cg);
      CTL[key] = { c, kind: c.t, def: c.v };
      let t0 = 0;
      cg.addEventListener('pointerdown', e => { e.preventDefault(); e.stopPropagation(); cg.setPointerCapture(e.pointerId); t0 = performance.now();
        if (c.t === 'mbutton') setParam(key, 1); else if (c.t === 'cbutton') setParam(key, (PARAMS[key] + 1) % c.n); });
      const up = () => { if (!t0) return; const held = performance.now() - t0; t0 = 0;
        if (c.t === 'mbutton') setParam(key, 0);
        else if (c.t === 'sbutton') { if (held >= 600) { setParam(id + '.end', c.idx); toast('Dernière étape : ' + (c.idx + 1)); } else setParam(key, PARAMS[key] ? 0 : 1); } };
      cg.addEventListener('pointerup', up); cg.addEventListener('pointercancel', up);
    } else if (c.t === 'pled') {
      PLEDS.push({ key, val: c.val, e: el('circle', { cx: c.x, cy: c.y, r: 1.6, fill: c.c === 'amber' ? 'url(#lamp)' : 'url(#ledg)', stroke: '#444', 'stroke-width': .2, opacity: .18 }, g) });
    } else if (c.t === 'sled') {
      (SLEDS[id] = SLEDS[id] || [])[c.idx] = el('circle', { cx: c.x, cy: c.y, r: 1.6, fill: 'url(#ledg)', stroke: '#444', 'stroke-width': .2, opacity: .18 }, g);
    } else if (c.t === 'param') {
      CTL[key] = { c, kind: 'param', def: c.v };
    } else if (c.t === 'led') {
      CTL[key] = { c, kind: 'led', e: el('circle', { cx: c.x, cy: c.y, r: 1.6, fill: 'url(#ledg)', stroke: '#444', 'stroke-width': .2, opacity: .2 }, g) };
    } else if (c.t === 'scope') {
      el('rect', { x: c.x, y: c.y, width: c.w, height: c.h, rx: 1.4, fill: '#070806', stroke: '#2b2926', 'stroke-width': .6 }, g);
      for (let k = 1; k < 4; k++) el('line', { x1: c.x, x2: c.x + c.w, y1: c.y + c.h * k / 4, y2: c.y + c.h * k / 4, stroke: '#2a2015', 'stroke-width': .15 }, g);
      for (let k = 1; k < 6; k++) el('line', { y1: c.y, y2: c.y + c.h, x1: c.x + c.w * k / 6, x2: c.x + c.w * k / 6, stroke: '#2a2015', 'stroke-width': .15 }, g);
      CTL[id + '.screen'] = { c, kind: 'scope', path: el('polyline', { fill: 'none', stroke: '#ffae3d', 'stroke-width': .38, 'stroke-linejoin': 'round', points: '' }, g),
        txt: el('text', { x: c.x + 1.2, y: c.y + c.h - 1.4, 'font-size': 1.7, fill: '#b5772a', 'font-family': 'JetBrains Mono,monospace' }, g) };
    } else if (c.t === 'jack') {
      const jg = el('g', { transform: `translate(${c.x},${c.y})`, class: 'jack' }, g);
      el('circle', { r: 3.6, fill: 'url(#nut)', stroke: '#3a3935', 'stroke-width': .25 }, jg);
      el('circle', { r: 2.0, fill: '#292826' }, jg);
      el('circle', { r: 1.6, fill: '#000' }, jg);
      el('circle', { r: 5, fill: 'transparent' }, jg);
      jg.dataset.key = key;
      JACKS[key] = { x: X0 + c.x, y: Y0 + c.y, d: c.d, g: jg };
      bindJack(jg, key);
    }
  });
  if (moveMode) {
    el('rect', { x: .4, y: .4, width: m.w - .8, height: PH - .8, fill: 'rgba(255,174,61,.05)', stroke: '#ffae3d', 'stroke-width': .5, 'stroke-dasharray': '2 1.4' }, g);
    const xb = el('g', { transform: `translate(${m.w / 2},${PH / 2})`, class: 'xbtn' }, g);
    const bg = el('rect', { x: -6, y: -3.2, width: 12, height: 6.4, rx: 3.2, fill: '#1b1916', stroke: '#3a3632', 'stroke-width': .35 }, xb);
    const tx = el('text', { 'text-anchor': 'middle', 'dominant-baseline': 'central', 'font-size': 3.4, fill: '#ece5d3', 'font-family': 'Barlow Condensed,Arial Narrow,sans-serif', 'font-weight': 600 }, xb);
    tx.textContent = '× retirer';
    xb.addEventListener('pointerdown', e => {
      e.stopPropagation(); e.preventDefault();
      if (xb.dataset.arm) { removeModule(id); return; }
      xb.dataset.arm = 1; bg.setAttribute('fill', '#d9483a'); bg.setAttribute('stroke', '#d9483a'); tx.textContent = 'Retirer ?';
      setTimeout(() => { if (xb.isConnected) { delete xb.dataset.arm; bg.setAttribute('fill', '#1b1916'); bg.setAttribute('stroke', '#3a3632'); tx.textContent = '× retirer'; } }, 2500);
    });
    bindPanelDrag(g, id);
  }
}
// ------------------------------------------------------------------ values
const NAMES = ['LO', "32'", "16'", "8'", "4'", "2'"], WAVES = ['SINE', 'TRIANGLE', 'SAW', 'PULSE'];
const tm = s => s < 1 ? (s * 1000).toFixed(s < .01 ? 1 : 0) + ' ms' : s.toFixed(2) + ' s';
const pc = v => Math.round(v * 100) + ' %';
function fmt(key, v) {
  const id = key.split('.')[0], t = L.mods[id] ? L.mods[id].type : id, k = t + '.' + key.split('.')[1];
  switch (k) {
    case 'vco.range': return NAMES[v];
    case 'vco.fine': { const st = (v - .5) * 12; return (st >= 0 ? '+' : '') + st.toFixed(1) + ' demi-tons'; }
    case 'vco.width': return 'rapport ' + Math.round(5 + 90 * v) + ' %';
    case 'vco.blend': { const p = v * 3, i = Math.min(2, Math.floor(p)), f = p - i; return f < .02 ? WAVES[i] : f > .98 ? WAVES[i + 1] : WAVES[i] + ' → ' + WAVES[i + 1] + ' ' + Math.round(f * 100) + ' %'; }
    case 'mix.master': return 'gain ×' + (1 + 10 * v).toFixed(1);
    case 'vcf.mode': return v < .02 ? 'LP 24 dB' : v < .48 ? 'LP → BP ' + Math.round(v * 200) + ' %' : v <= .52 ? 'BP 12 dB' : v < .98 ? 'BP → HP ' + Math.round((v - .5) * 200) + ' %' : 'HP 12 dB';
    case 'vcf.freq': { const f = 20 * Math.pow(2, 10 * v); return f < 1000 ? Math.round(f) + ' Hz' : (f / 1000).toFixed(2) + ' kHz'; }
    case 'vca.response': return v < .02 ? 'LIN' : v > .98 ? 'EXP' : 'LIN ' + Math.round((1 - v) * 100) + ' % · EXP ' + Math.round(v * 100) + ' %';
    case 'vca.fixed': return (6 * v).toFixed(2) + ' V';
    case 'ad.attack': case 'ad.decay': return tm(0.0008 * Math.pow(10, 4 * v));
    case 'adsr.attack': { const R = 320 + 1e6 * (Math.pow(100, v) - 1) / 99; return tm(R * 6e-6 * Math.log(6)); }
    case 'adsr.decay': case 'adsr.release': { const R = 320 + 1e6 * (Math.pow(100, v) - 1) / 99; return tm(R * 6e-6 * Math.log(10)) + ' (à 90 %)'; }
    case 'adsr.sustain': return (10 * v).toFixed(1) + ' V';
    case 'stg.time': return tm(0.01 * Math.pow(1000, v)) + ' par étape';
    case 'stg.tcvatt': return ((v * 2 - 1) * 100).toFixed(0) + ' %';
    case 'stg.analogk': return 'étape ' + (Math.round(v * 7) + 1);
    case 'stg.mode': return ['LOOP', 'ONCE', 'ENV'][v];
    case 'stg.startbtn': return v ? 'appuyé' : 'relâché';
    case 'stg.end': return 'étape ' + (v + 1);
    case 'cx.range': return v ? 'LFO' : 'AUDIO';
    case 'cx.mwave': return ['TRIANGLE', 'SQUARE', 'SAW'][v];
    case 'cx.ampl': case 'cx.pitch': case 'cx.timbresw': return v ? 'OFF' : 'ON';
    case 'cx.mfreq': case 'cx.pfreq': { const f = 440 * Math.pow(2, (v - .5) * 8 + (key.endsWith('mfreq') && PARAMS[id + '.range'] ? -7 : 0)); return f < 10 ? f.toFixed(2) + ' Hz' : f < 1000 ? Math.round(f) + ' Hz' : (f / 1000).toFixed(2) + ' kHz'; }
    case 'cx.mfine': case 'cx.pfine': { const st = (v - .5) * 14; return (st >= 0 ? '+' : '') + st.toFixed(1) + ' demi-tons'; }
    case 'cx.index': case 'cx.mcv': case 'cx.pcv': return ((v * 2 - 1) * 100).toFixed(0) + ' %';
    case 'cx.timbre': case 'cx.sym': case 'cx.order': return (v * 10).toFixed(1);
    case 'ad.cycle': return v ? 'CYCLE (LFO)' : 'ONE';
    case 'lfo.f1': case 'lfo.f2': case 'lfo.f3': case 'lfo.f4': {
      if (PARAMS[id + '.s' + key.slice(-1)] === 0) return ['/16', '/8', '/4', '/3', '/2', '×1', '×2', '×3', '×4', '×8', '×16'][Math.round(v * 10)] + ' du CLOCK';
      const f = 0.02 * Math.pow(2, v * 10.3); return f < 1 ? (1 / f).toFixed(1) + ' s par cycle' : f.toFixed(2) + ' Hz'; }
    case 'lfo.w1': case 'lfo.w2': case 'lfo.w3': case 'lfo.w4': return ['SINE', 'SAW', 'SQUARE'][v < 1 / 3 ? 0 : v < 2 / 3 ? 1 : 2];
    case 'lfo.s1': case 'lfo.s2': case 'lfo.s3': case 'lfo.s4': return v ? 'FREE' : 'CLOCKED';
    case 'sim.tempo': return Math.round(50 + 190 * v) + ' BPM';
    case 'sim.seq': return v ? 'en marche' : 'arrêtée';
  }
  if (/^stg\.[ab]\d$/.test(k)) return (v * 8).toFixed(2) + ' V';
  if (/^stg\.t\d$/.test(k)) return '×' + Math.pow(4, v * 2 - 1).toFixed(2);
  if (/^stg\.sl\d$/.test(k)) return v ? 'glissé' : 'marches';
  if (/\.(l\d|emph)$/.test(k)) return (v * 10).toFixed(1);
  return pc(v);
}
const status = $('#status');
function show(key) { if (LAB[key]) status.textContent = LAB[key] + '  ' + fmt(key, PARAMS[key]); }
function draw(key) {
  const C = CTL[key], v = PARAMS[key];
  for (const L_ of PLEDS) if (L_.key === key && v !== undefined) L_.e.setAttribute('opacity', v === L_.val ? 1 : .18);
  if (!C || v === undefined) return;
  if (C.kind === 'knob') C.rot.setAttribute('transform', `rotate(${-135 + 270 * v})`);
  else if (C.kind === 'rotary') C.rot.setAttribute('transform', `rotate(${C.c.angles[v]})`);
  else if (C.kind === 'toggle') {
    if (C.c.vert) { const n = C.c.opts.length, yy = v === 0 ? -3.6 : v === n - 1 ? 3.6 : 0; C.lev.setAttribute('x2', 0); C.lev.setAttribute('y2', yy); C.tip.setAttribute('r', yy ? 1.0 : 1.7); }
    else C.lev.setAttribute('x2', v ? 3.6 : -3.6);
  }
  else if (C.kind === 'button') C.led.setAttribute('opacity', v ? 1 : .15);
  if (key === 'sim.seq') $('#sled').classList.toggle('on', !!v);
  for (const L_ of PLEDS) if (L_.key === key) L_.e.setAttribute('opacity', v === L_.val ? 1 : .18);
}
function setParam(key, v) { PARAMS[key] = v; draw(key); show(key); send({ t: 'p', k: key, v }); }
function svgPt(e) { const p = svg.createSVGPoint(); p.x = e.clientX; p.y = e.clientY; return p.matrixTransform(svg.getScreenCTM().inverse()); }
function bindKnob(g, key) {
  let y0, v0, moved, lastTap = 0;
  g.addEventListener('pointerdown', e => { e.preventDefault(); e.stopPropagation(); g.setPointerCapture(e.pointerId); y0 = e.clientY; v0 = PARAMS[key]; moved = false; show(key); });
  g.addEventListener('pointermove', e => {
    if (y0 === undefined) return;
    const dy = y0 - e.clientY; if (Math.abs(dy) > 3) moved = true;
    const fine = e.shiftKey ? 0.2 : 1;
    if (CTL[key].kind === 'rotary') { const n = CTL[key].c.angles.length; const v = Math.max(0, Math.min(n - 1, v0 + Math.round(dy / 28))); if (v !== PARAMS[key]) setParam(key, v); }
    else setParam(key, Math.max(0, Math.min(1, v0 + fine * dy / 180)));
  });
  const up = () => {
    if (y0 !== undefined && !moved) {
      const now = performance.now();
      if (CTL[key].kind === 'rotary') setParam(key, (PARAMS[key] + 1) % CTL[key].c.angles.length);
      else if (now - lastTap < 320) setParam(key, CTL[key].def);
      lastTap = now;
    }
    y0 = undefined;
  };
  g.addEventListener('pointerup', up); g.addEventListener('pointercancel', () => { y0 = undefined; });
}
// ------------------------------------------------------------------ cables (M55 look)
const PAL = ['#c8332b', '#e3b23c', '#2f6fb5', '#2f8f5b', '#e9e2cf', '#d26a1e', '#7a4fa0', '#3fb8b0'];
let ci = 0;
function cablePath(a, b) {
  const dx = b.x - a.x, d = Math.hypot(dx, b.y - a.y), sag = 5 + d * 0.16, lim = TH - 2;
  const y1 = Math.min(Math.max(a.y, b.y) + sag, lim), y2 = y1;
  return `M${a.x},${a.y} C${a.x + dx * .15},${Math.min(a.y + sag, lim)} ${b.x - dx * .15},${Math.min(b.y + sag, lim)} ${b.x},${b.y}`;
}
function cableG(a, b, col, parent) {
  const g = el('g', {}, parent), d = cablePath(a, b);
  el('path', { d, fill: 'none', stroke: 'rgba(0,0,0,.45)', 'stroke-width': 2.1, transform: 'translate(.6 1.5)' }, g);
  el('path', { d, fill: 'none', stroke: col, 'stroke-width': 1.5, 'stroke-linecap': 'round' }, g);
  el('path', { d, fill: 'none', stroke: 'rgba(255,255,255,.22)', 'stroke-width': .42, transform: 'translate(-.3 -.3)' }, g);
  for (const p of [a, b]) {
    el('circle', { cx: p.x, cy: p.y, r: 2.6, fill: col, stroke: '#0a0908', 'stroke-width': .6 }, g);
    el('circle', { cx: p.x - .6, cy: p.y - .6, r: .8, fill: 'rgba(255,255,255,.35)' }, g);
  }
  return g;
}
function renderCables(quiet) {
  gCables.innerHTML = '';
  for (const c of cables) cableG(JACKS[c.src], JACKS[c.dst], c.col, gCables);
  if (!quiet) send({ t: 'cables', list: cables.map(c => [c.src, c.dst]) });
}
function connect(a, b, col, quiet) {
  if (a === b) return;
  const A = JACKS[a], B = JACKS[b];
  if (!A || !B) return;
  if (A.d === B.d) { status.textContent = A.d === 'in' ? 'Deux entrées : branche une sortie' : 'Deux sorties : branche une entrée'; return; }
  if (A.d === 'in') [a, b] = [b, a];
  cables = cables.filter(c => c.dst !== b);
  cables.push({ src: a, dst: b, col: col || PAL[ci++ % PAL.length] });
  renderCables(quiet);
}
let drag = null;
function bindJack(g, key) {
  g.addEventListener('pointerdown', e => {
    e.preventDefault(); e.stopPropagation(); g.setPointerCapture(e.pointerId);
    drag = { key, moved: false, x0: e.clientX, y0: e.clientY, col: PAL[ci % PAL.length], tmp: null };
  });
  g.addEventListener('pointermove', e => {
    if (!drag) return;
    if (Math.hypot(e.clientX - drag.x0, e.clientY - drag.y0) > 6) drag.moved = true;
    if (!drag.moved) return;
    if (drag.tmp) drag.tmp.remove();
    drag.tmp = cableG(JACKS[drag.key], svgPt(e), drag.col, svg); drag.tmp.setAttribute('opacity', .85); drag.tmp.setAttribute('pointer-events', 'none');
  });
  g.addEventListener('pointerup', e => {
    if (!drag) return;
    const d = drag; drag = null;
    if (d.tmp) d.tmp.remove();
    if (!d.moved) { const n = cables.length; cables = cables.filter(c => c.src !== d.key && c.dst !== d.key); if (cables.length !== n) renderCables(); return; }
    const t = document.elementFromPoint(e.clientX, e.clientY);
    let jg = t && t.closest && t.closest('.jack');
    if (!jg) {
      const p = svgPt(e); let best = null, bd = 7;
      for (const k in JACKS) { const J = JACKS[k], dd = Math.hypot(J.x - p.x, J.y - p.y); if (dd < bd) { bd = dd; best = J.g; } }
      jg = best;
    }
    if (jg && jg.dataset.key) { ci++; connect(d.key, jg.dataset.key, d.col); }
  });
  g.addEventListener('pointercancel', () => { if (drag && drag.tmp) drag.tmp.remove(); drag = null; });
}
// ------------------------------------------------------------------ modules : add / remove / move
const rowHP = (row, skip) => row.reduce((a, id) => a + (id === skip ? 0 : HP[L.mods[id].type]), 0);
function addModule(type) {
  let n = 1; const used = new Set(Object.values(L.mods).filter(m => m.type === type).map(m => m.n));
  while (used.has(n)) n++;
  const id = n === 1 ? type : type + n;
  L.mods[id] = { type, n };
  TYPE[type].ctl.forEach(c => { if (c.v !== undefined) PARAMS[id + '.' + c.id] = c.v; });
  let r = L.rows.findIndex(row => rowHP(row) + HP[type] <= ROWHP);
  if (r < 0) { L.rows.push([]); r = L.rows.length - 1; }
  L.rows[r].push(id);
  build();
  const P = POS[id]; if (P) { const s = svg.getBoundingClientRect().width / TW; wrap.scrollTo({ left: Math.max(0, P.x * s - 40), top: Math.max(0, P.y * s - 40), behavior: 'smooth' }); }
  toast(TYPE[type].name + (n > 1 ? ' ' + n : '') + ' ajouté');
}
function removeModule(id) {
  L.rows = L.rows.map(r => r.filter(x => x !== id));
  delete L.mods[id];
  for (const k of Object.keys(PARAMS)) if (k.startsWith(id + '.')) delete PARAMS[k];
  cables = cables.filter(c => !c.src.startsWith(id + '.') && !c.dst.startsWith(id + '.'));
  build();
}
let mdrag = null;
function bindPanelDrag(g, id) {
  g.addEventListener('pointerdown', e => {
    if (!moveMode) return;
    e.preventDefault(); g.setPointerCapture(e.pointerId);
    const p = svgPt(e), P = POS[id];
    mdrag = { id, g, dx: p.x - P.x, dy: p.y - P.y, ghost: el('rect', { fill: 'rgba(255,174,61,.08)', stroke: '#ffae3d', 'stroke-width': .6, 'stroke-dasharray': '2.5 1.5', 'pointer-events': 'none', width: P.w, height: PH, x: P.x, y: P.y }, svg), target: null };
    g.parentNode.appendChild(g); g.style.opacity = .85;
  });
  g.addEventListener('pointermove', e => {
    if (!mdrag || mdrag.g !== g) return;
    const p = svgPt(e), x = p.x - mdrag.dx, y = p.y - mdrag.dy;
    g.setAttribute('transform', `translate(${x},${y})`);
    const r = Math.max(0, Math.min(nRows - 1, Math.floor((y + PH / 2) / (RH + GAPY))));
    const row = r < L.rows.length ? L.rows[r].filter(q => q !== id) : [];
    let idx = 0, acc = 0;
    for (const q of row) { const w = HP[L.mods[q].type]; if (x + POS[id].w / 2 > MX + (acc + w / 2) * HPMM) { idx++; acc += w; } else break; }
    const fits = rowHP(row) + HP[L.mods[id].type] <= ROWHP;
    mdrag.target = fits ? { r, idx } : null;
    const gx = MX + acc * HPMM, gy = rowY(r) + MY;
    mdrag.ghost.setAttribute('x', gx); mdrag.ghost.setAttribute('y', gy);
    mdrag.ghost.setAttribute('stroke', fits ? '#ffae3d' : '#d9483a');
    mdrag.ghost.setAttribute('fill', fits ? 'rgba(255,174,61,.08)' : 'rgba(217,72,58,.1)');
  });
  const end = () => {
    if (!mdrag || mdrag.g !== g) return;
    const t = mdrag.target; mdrag = null;
    if (t) {
      L.rows = L.rows.map(r => r.filter(q => q !== id));
      while (L.rows.length <= t.r) L.rows.push([]);
      L.rows[t.r].splice(t.idx, 0, id);
    } else toast('Pas assez de place dans cette rangée (104 HP)');
    build();
  };
  g.addEventListener('pointerup', end); g.addEventListener('pointercancel', end);
}
function setMove(on) { moveMode = on; svg.classList.toggle('move', on); $('#mvled').classList.toggle('on', on); build(); if (on) toast('Glisse un module pour le déplacer'); }
$('#bMove').onclick = () => setMove(!moveMode);
const lib = $('#lib'), libCards = $('#libCards');
['vco', 'cx', 'mix', 'vcf', 'vca', 'ad', 'adsr', 'stg', 'sim'].forEach(t => {
  const b = document.createElement('button'); b.className = 'mc';
  b.innerHTML = `<span class="t"><b>${TYPE[t].name}</b><u>${HP[t]} HP</u></span><p>${DESC[t]}</p>`;
  b.onclick = () => { lib.hidden = true; addModule(t); };
  libCards.appendChild(b);
});
$('#addMod').onclick = () => { lib.hidden = false; };
$('#libClose').onclick = () => { lib.hidden = true; };
function loadPatch() {
  L = defaultLayout(); PARAMS = Object.assign({}, DEFV); cables = []; ci = 0;
  build();
  DATA.patch.forEach(([m1, j1, m2, j2]) => connect(m1 + '.' + j1, m2 + '.' + j2, null, true));
  send(fullState());
}
// ------------------------------------------------------------------ audio
let ctx = null, node = null, engine = null, sp = null, audioOn = false;
function send(d) { if (node) node.port.postMessage(d); else if (engine) engine.msg(d); }
function fullState() {
  const mods = []; L.rows.forEach(r => r.forEach(id => mods.push({ id, type: L.mods[id].type })));
  return { t: 'state', mods, params: Object.assign({}, PARAMS), cables: cables.map(c => [c.src, c.dst]) };
}
function onReport(r) {
  for (const id in r.scopes) {
    const S = CTL[id + '.screen']; if (!S) continue; const c = S.c, sc = r.scopes[id];
    let i0 = 0; for (let i = 1; i < 1024; i++) if (sc[i - 1] <= 0 && sc[i] > 0) { i0 = i; break; }
    const N = 900, pts = [];
    for (let i = 0; i < N; i += 3) { const v = sc[i0 + i]; pts.push((c.x + c.w * i / N).toFixed(2) + ',' + (c.y + c.h / 2 - Math.max(-1.05, Math.min(1.05, v / 10)) * c.h / 2).toFixed(2)); }
    S.path.setAttribute('points', pts.join(' '));
    let mx = 0; for (let i = 0; i < sc.length; i++) mx = Math.max(mx, Math.abs(sc[i]));
    S.txt.textContent = `±10 V · crête ${mx.toFixed(1)} V`;
  }
  if (r.stg) for (const id in r.stg) {
    const st = r.stg[id], Ls = SLEDS[id]; if (!Ls) continue;
    const blink = (performance.now() / 250 | 0) & 1, end = PARAMS[id + '.end'];
    Ls.forEach((e_, i) => e_.setAttribute('opacity', i === st.stage ? 1 : (i === end && blink ? .55 : .15)));
  }
  for (const id in r.leds) { const C = CTL[id.includes('.') ? id : id + '.led']; if (C) C.e.setAttribute('opacity', (0.15 + 0.85 * Math.min(1, r.leds[id])).toFixed(2)); }
}
async function startAudio() {
  if (ctx) { if (ctx.state !== 'running') await ctx.resume(); audioOn = true; $('#pled').classList.add('on'); return; }
  ctx = new (window.AudioContext || window.webkitAudioContext)({ latencyHint: 'interactive' });
  try {
    await ctx.audioWorklet.addModule('dsp.js');
    node = new AudioWorkletNode(ctx, 'octavio-sim', { numberOfInputs: 0, numberOfOutputs: 1, outputChannelCount: [2] });
    node.port.onmessage = e => onReport(e.data);
    node.connect(ctx.destination);
    node.port.postMessage(fullState());
  } catch (err) {
    node = null;
    engine = new OctavioEngine(ctx.sampleRate); engine.msg(fullState());
    engine.report = r => requestAnimationFrame(() => onReport(r));
    sp = ctx.createScriptProcessor(2048, 0, 2);
    sp.onaudioprocess = e => engine.render(e.outputBuffer.getChannelData(0), e.outputBuffer.getChannelData(1), e.outputBuffer.length);
    sp.connect(ctx.destination);
  }
  await ctx.resume();
  audioOn = true; $('#pled').classList.add('on');
}
async function stopAudio() { if (ctx) await ctx.suspend(); audioOn = false; $('#pled').classList.remove('on'); }
$('#startBtn').onclick = () => { $('#startOv').hidden = true; startAudio(); };
$('#power').onclick = () => audioOn ? stopAudio() : startAudio();
$('#bSeq').onclick = () => { const k = Object.keys(PARAMS).find(k => /^sim\d*\.seq$/.test(k)); if (k) setParam(k, PARAMS[k] ? 0 : 1); };
$('#bPatch').onclick = loadPatch;
$('#bClear').onclick = () => { cables = []; renderCables(); };
$('#cabOp').onclick = () => svg.classList.toggle('faded');
$('#help').onclick = () => { $('#helpOv').hidden = false; };
$('#helpClose').onclick = () => { $('#helpOv').hidden = true; };
// ------------------------------------------------------------------ keyboard (M55)
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
kbd.addEventListener('pointermove', e => {
  if (!kbPtr.has(e.pointerId)) return; const cur = kbPtr.get(e.pointerId), n = noteAt(e);
  if (n !== cur) { if (cur != null) noteOff(cur); if (n != null) noteOn(n); kbPtr.set(e.pointerId, n); }
});
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
// ------------------------------------------------------------------ zoom / fit : one row fills the height
const wrap = $('#rackWrap'); let zoom = 1;
function fit() {
  const rowPx = Math.max(160, wrap.clientHeight - 20 - 28) * zoom, s = rowPx / RH;
  svg.style.height = (TH * s) + 'px'; svg.style.width = (TW * s) + 'px';
}
let curRow = 0;
function goRow(r) {
  curRow = ((r % L.rows.length) + L.rows.length) % L.rows.length;
  const s = svg.getBoundingClientRect().height / TH;
  wrap.scrollTo({ top: rowY(curRow) * s, behavior: 'smooth' });
  $('#zRow').textContent = 'Rangée ' + (curRow + 1);
}
$('#zRow').onclick = () => goRow(curRow + 1);
wrap.addEventListener('scroll', () => { const s = svg.getBoundingClientRect().height / TH; const r = Math.round(wrap.scrollTop / s / (RH + GAPY)); if (r !== curRow && r < L.rows.length) { curRow = r; $('#zRow').textContent = 'Rangée ' + (r + 1); } });
$('#zFit').onclick = () => { zoom = 1; fit(); };
$('#zIn').onclick = () => { zoom = Math.min(3, zoom * 1.25); fit(); };
$('#zOut').onclick = () => { zoom = Math.max(.25, zoom / 1.25); fit(); };
window.addEventListener('resize', () => { fit(); buildKbd(); });
buildKbd(); loadPatch();
