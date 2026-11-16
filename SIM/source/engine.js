// ocTavio Eurorack - behavioural models of our circuits, run per sample (voltages in volts).
// Several instances of each module; ports are indexed per type.
const OCT_TYPES = {
  vco: { ins: ['voct', 'fm', 'pwm', 'sync'], outs: ['sine', 'tri', 'saw', 'pulse', 'blend'] },
  mix: { ins: ['in1', 'in2', 'in3', 'in4'], outs: ['out', 'nout'] },
  vcf: { ins: ['in1', 'in2', 'contour', 'fcv', 'ecv'], outs: ['out'] },
  vca: { ins: ['in1', 'in2', 'cv1', 'cv2', 'cv3'], outs: ['outp', 'outn'] },
  ad: { ins: ['trig', 'acv', 'dcv'], outs: ['out'] },
  sim: { ins: ['audio', 'scope'], outs: ['cv', 'gate'] },
};
class OctavioEngine {
  constructor(sr) {
    this.sr = sr; this.P = {}; this.mods = new Map(); this.list = []; this.cabs = []; this.rawCab = [];
    this.held = []; this.key = null; this.cnt = 0; this.seed = 1;
  }
  msg(d) {
    if (d.t === 'p') { this.P[d.k] = d.v; }
    else if (d.t === 'cables') { this.rawCab = d.list; this.resolve(); }
    else if (d.t === 'state') {
      if (d.params) this.P = Object.assign({}, d.params);
      if (d.mods) this.setMods(d.mods);
      if (d.cables) this.rawCab = d.cables;
      this.resolve();
    } else if (d.t === 'note') {
      const i = this.held.indexOf(d.n); if (i >= 0) this.held.splice(i, 1);
      if (d.on) this.held.push(d.n);
      this.key = this.held.length ? this.held[this.held.length - 1] : null;
    }
  }
  setMods(list) {
    const nm = new Map();
    for (const { id, type } of list) {
      let m = this.mods.get(id);
      if (!m || m.type !== type) {
        const T = OCT_TYPES[type];
        m = { id, type, i: new Float64Array(T.ins.length), o: new Float64Array(T.outs.length), s: {} };
        this.init(m);
      }
      nm.set(id, m);
    }
    this.mods = nm; this.list = [...nm.values()];
  }
  init(m) {
    const s = m.s;
    if (m.type === 'vco') { s.ph = Math.random(); s.syncHi = false; }
    else if (m.type === 'vcf') { s.y1 = s.y2 = s.y3 = s.y4 = s.hp = s.hpx = 0; }
    else if (m.type === 'ad') { s.env = 0; s.latch = 0; s.trHi = false; s.ledMax = 0; }
    else if (m.type === 'sim') { s.seqPh = 0; s.step = 0; s.lastCv = 0; s.scope = new Float32Array(2048); }
  }
  resolve() {
    this.cabs = [];
    for (const [a, b] of this.rawCab) {
      const [am, ap] = a.split('.'), [bm, bp] = b.split('.');
      const A = this.mods.get(am), B = this.mods.get(bm);
      if (!A || !B) continue;
      const oi = OCT_TYPES[A.type].outs.indexOf(ap), ii = OCT_TYPES[B.type].ins.indexOf(bp);
      if (oi >= 0 && ii >= 0) this.cabs.push([A.o, oi, B.i, ii]);
    }
  }
  render(L, R, n) {
    const sr = this.sr, P = this.P, tanh = Math.tanh;
    const cl = (x, a, b) => x < a ? a : (x > b ? b : x);
    const blep = (t, dt) => { if (t < dt) { t /= dt; return t + t - t * t - 1; } if (t > 1 - dt) { t = (t - 1) / dt; return t * t + t + t + 1; } return 0; };
    const potLoad = a => { const par = a / (a + 1 + 1e-9); return par / (1 - a + par + 1e-12); };
    const SEQ = [0, 12, 0, 7, 3, 0, 10, 7, 0, 12, 3, 5, 7, 0, 15, 10];
    const g2 = 1 / (2 * sr);
    const K = this.list.map(m => {
      const p = k => { const v = P[m.id + '.' + k]; return v === undefined ? 0 : v; }, t = m.type;
      if (t === 'vco') { const b = p('blend'), rg = P[m.id + '.range']; return { r: [-7, -2, -1, 0, 1, 2][rg === undefined ? 3 : rg], f: p('fine') - 0.5, w: p('width'), fm: p('fm'), pwm: p('pwm'), c1: cl(3 * b, 0, 1), c2: cl(3 * b - 1, 0, 1), c3: cl(3 * b - 2, 0, 1) }; }
      if (t === 'mix') { const mm = p('master'), Rf = 10 + 100 * mm; return { l: [1, 2, 3, 4].map(k => potLoad(p('l' + k))), G: Rf / 10, slope: 4.7 / (Rf + 4.7) }; }
      if (t === 'vcf') { const md = p('mode'); return { a: md < 0.5 ? 1 - 2 * md : 0, c: md > 0.5 ? 2 * md - 1 : 0, fr: p('freq'), e: p('emph'), co: p('contour'), fc: p('fcv'), ec: p('ecv') }; }
      if (t === 'vca') return { cv: p('cvlevel'), r: p('response'), fx: p('fixed') };
      if (t === 'ad') return { a: p('attack'), d: p('decay'), acv: p('acv'), dcv: p('dcv'), cyc: p('cycle') };
      if (t === 'sim') { const bpm = 50 + 190 * p('tempo'), on = P[m.id + '.seq']; return { on: on === undefined ? 1 : on, v: p('volume'), step: 60 / bpm / 2 }; }
      return {};
    });
    const list = this.list, nm = list.length, cabs = this.cabs, nc = cabs.length;
    for (let i = 0; i < n; i++) {
      for (let j = 0; j < nm; j++) list[j].i.fill(0);
      for (let c = 0; c < nc; c++) { const q = cabs[c]; q[2][q[3]] += q[0][q[1]]; }
      let spk = 0;
      for (let j = 0; j < nm; j++) {
        const m = list[j], I = m.i, O = m.o, s = m.s, k = K[j];
        switch (m.type) {
          case 'vco': { // 921 core : expo -> saw reset, tri, sine shaper, pulse, blend
            let fr = 261.63 * Math.pow(2, k.r + k.f + I[0] + I[1] * k.fm); fr = cl(fr, 0.02, 20000);
            const dt = fr / sr;
            if (I[3] > 1 && !s.syncHi) { s.ph = 0; s.syncHi = true; } else if (I[3] < 0.5) s.syncHi = false;
            s.ph += dt; if (s.ph >= 1) s.ph -= 1;
            const ph = s.ph, saw = (2 * ph - 1 - blep(ph, dt)) * 5, tri = (2 * Math.abs(2 * ph - 1) - 1) * 5;
            const sine = 5 * tanh(1.55 * tri / 5) / tanh(1.55);
            const duty = cl(0.05 + 0.9 * k.w + I[2] * k.pwm * 0.09, 0.02, 0.98);
            let pul = ph < duty ? 1 : -1; pul += blep(ph, dt); pul -= blep((ph + 1 - duty) % 1, dt); pul *= 5;
            O[0] = sine; O[1] = tri; O[2] = saw; O[3] = pul;
            O[4] = sine + k.c1 * (tri - sine) + k.c2 * (saw - tri) + k.c3 * (pul - saw);
            break;
          }
          case 'mix': { // CP3 summer + MASTER GAIN, zener soft knee, rails
            const x = I[0] * k.l[0] + I[1] * k.l[1] + I[2] * k.l[2] + I[3] * k.l[3];
            const lin = k.G * x, ax = Math.abs(lin), z = (ax - 5.8) / 0.3, sp = z > 30 ? z * 0.3 : 0.3 * Math.log(1 + Math.exp(z));
            let y = ax - (1 - k.slope) * sp; y = y / Math.pow(1 + Math.pow(y / 10.5, 8), 0.125);
            O[0] = lin < 0 ? -y : y; O[1] = -O[0];
            break;
          }
          case 'vcf': { // 4-pole ladder, taps y0/y1/y2/y4, LP->BP->HP morph
            let fc = 20 * Math.pow(2, 10 * k.fr + I[3] * k.fc + I[2] * k.co * 0.6); fc = cl(fc, 5, Math.min(20000, 0.45 * sr));
            const g = 1 - Math.exp(-2 * Math.PI * fc * g2), kk = 4.3 * cl(k.e + I[4] * k.ec * 0.1, 0, 1.15);
            this.seed = (this.seed * 16807) % 2147483647;
            const xin = (I[0] + I[1]) * 0.18 + (this.seed / 2147483647 - 0.5) * 1e-4;
            let u = 0;
            for (let o = 0; o < 2; o++) {
              u = tanh(xin - kk * s.y4);
              const t1 = tanh(s.y1), t2 = tanh(s.y2), t3 = tanh(s.y3);
              s.y1 += g * (u - t1); s.y2 += g * (t1 - t2); s.y3 += g * (t2 - t3); s.y4 += g * (t3 - tanh(s.y4));
            }
            const LP = s.y4, BP = 2 * s.y1 - 2 * s.y2, HP = u - 2 * s.y1 + s.y2;
            const fo = -(BP + k.a * (LP - BP) + k.c * (HP - BP)) / 0.18;
            s.hp = 0.9993 * (s.hp + fo - s.hpx); s.hpx = fo; O[0] = s.hp;
            break;
          }
          case 'vca': { // 902 : diff pair, LIN/EXP blend, soft clip
            const Vc = Math.max(0, 6 * k.fx + k.cv * (I[2] + I[3] + I[4]));
            let ga = (1 - k.r) * Vc / 3 + k.r * 2 * Math.pow(10, 13 * (Vc - 6) / 20);
            if (ga > 2) ga = 2 + 0.6 * tanh((ga - 2) / 0.6);
            let ya = ga * 12.6 * tanh((I[0] - I[1]) / 12.6); ya = 9 * tanh(ya / 9);
            O[0] = ya; O[1] = -ya;
            break;
          }
          case 'ad': { // OTA slew core, expo times, latch, cycle
            if (I[0] > 1 && !s.trHi) { s.trHi = true; s.latch = 1; } else if (I[0] < 0.5) s.trHi = false;
            if (k.cyc && !s.latch && s.env < 0.2) s.latch = 1;
            if (s.latch) {
              const Ta = cl(0.0008 * Math.pow(10, 4 * k.a) * Math.pow(100, I[1] * k.acv / 5), 0.0002, 60);
              s.env += (9.3 / Ta) / sr * tanh((11 - s.env) / 1.5) / tanh(11 / 1.5);
              if (s.env >= 9.3) s.latch = 0;
            } else {
              const Td = cl(0.0008 * Math.pow(10, 4 * k.d) * Math.pow(100, I[2] * k.dcv / 5), 0.0002, 60);
              s.env -= (9.3 / Td) / sr * tanh(s.env / 1.5) / tanh(9.3 / 1.5);
              if (s.env < 0) s.env = 0;
            }
            O[0] = s.env; if (s.env > s.ledMax) s.ledMax = s.env;
            break;
          }
          case 'sim': { // sequencer / keyboard, speakers, scope
            let cv, gate;
            if (this.key !== null) { cv = (this.key - 60) / 12; gate = 5; s.lastCv = cv; }
            else if (k.on) {
              s.seqPh += 1 / sr; if (s.seqPh >= k.step) { s.seqPh -= k.step; s.step = (s.step + 1) % SEQ.length; }
              cv = -1 + SEQ[s.step] / 12; gate = s.seqPh < k.step * 0.5 ? 5 : 0; s.lastCv = cv;
            } else { cv = s.lastCv; gate = 0; }
            O[0] = cv; O[1] = gate;
            spk += I[0] * 0.25 * (2 * k.v) * (2 * k.v);
            s.scope[this.cnt] = I[1];
            break;
          }
        }
      }
      const out = tanh(spk); L[i] = out; if (R) R[i] = out;
      if (++this.cnt >= 2048) {
        this.cnt = 0;
        if (this.report) {
          const r = { scopes: {}, leds: {} };
          for (const m of list) {
            if (m.type === 'sim') r.scopes[m.id] = m.s.scope.slice(0);
            else if (m.type === 'ad') { r.leds[m.id] = m.s.ledMax / 9.3; m.s.ledMax = 0; }
          }
          this.report(r);
        }
      }
    }
  }
}
