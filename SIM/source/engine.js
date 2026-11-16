// ocTavio Eurorack - behavioural models of our circuits, run per sample (voltages in volts).
// Several instances of each module; ports are indexed per type.
const OCT_TYPES = {
  vco: { ins: ['voct', 'fm', 'pwm', 'sync'], outs: ['sine', 'tri', 'saw', 'pulse', 'blend'] },
  mix: { ins: ['in1', 'in2', 'in3', 'in4'], outs: ['out', 'nout'] },
  vcf: { ins: ['in1', 'in2', 'contour', 'fcv', 'ecv'], outs: ['out'] },
  vca: { ins: ['in1', 'in2', 'cv1', 'cv2', 'cv3'], outs: ['outp', 'outn'] },
  ad: { ins: ['trig', 'acv', 'dcv'], outs: ['out'] },
  adsr: { ins: ['gate'], outs: ['out', 'nout'] },
  stg: { ins: ['clock', 'start', 'strobe', 'tcv', 'analog', 'sel1', 'sel2', 'sel3', 'sel4', 'sel5', 'sel6', 'sel7', 'sel8'],
         outs: ['cva', 'cvb', 'gate', 'end', 'g1', 'g2', 'g3', 'g4', 'g5', 'g6', 'g7', 'g8'] },
  cx: { ins: ['mvoct', 'mcv', 'mfm', 'indexcv', 'plock', 'pvoct', 'pcv', 'pfm', 'symcv', 'timbrecv', 'ordercv'], outs: ['tri', 'signal', 'sine', 'square', 'final'] },
  lfo: { ins: ['clock', 'reset'], outs: ['o1', 'o2', 'o3', 'o4'] },
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
    else if (m.type === 'cx') { s.pm = Math.random(); s.pc = Math.random(); s.plPrev = 0; }
    else if (m.type === 'stg') { s.stage = 0; s.pos = 0; s.run = true; s.held = false; s.pA = 0; s.pB = 0; s.inHi = new Array(13).fill(false); s.lastClk = -1; s.per = 0.5 * this.sr; s.n = 0; s.endUntil = 0; s.btn = 0; }
    else if (m.type === 'lfo') { s.ph = [0, 0, 0, 0]; s.y1 = [0, 0, 0, 0]; s.y2 = [0, 0, 0, 0]; s.led = [0, 0, 0, 0]; s.ledc = 0; s.t = 0; s.n = 0; s.last = -1; s.per = 0; s.ch = false; s.rh = false; }
    else if (m.type === 'adsr') { s.env = 0; s.att = 0; s.g = false; s.ledMax = 0; }
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
      if (t === 'stg') { const g = (k, d) => { const v = P[m.id + '.' + k]; return v === undefined ? d : v; };
        const A = [], B = [], T = [], SL = [];
        for (let i = 1; i <= 8; i++) { A.push(g('a' + i, 0)); B.push(g('b' + i, 0)); T.push(g('t' + i, .5)); SL.push(g('sl' + i, 0)); }
        return { A, B, T, SL, time: g('time', .4), tatt: g('tcvatt', .5) * 2 - 1, an: g('analogk', 0), end: g('end', 7), mode: g('mode', 0), sb: g('startbtn', 0) }; }
      if (t === 'cx') { const g = (k, d) => { const v = P[m.id + '.' + k]; return v === undefined ? d : v; };
        return { mf: (g('mfreq', .35) - .5) * 8 + (g('mfine', .5) - .5) * 1.16 + (g('range', 0) ? -7 : 0), mcv: g('mcv', .5) * 2 - 1, mfm: g('mfm', 0), mw: g('mwave', 0),
                 ix: g('index', .65) * 2 - 1, am: !g('ampl', 1), pm: !g('pitch', 0), tm: !g('timbresw', 1), pl: g('plock', 0),
                 pf: (g('pfreq', .45) - .5) * 8 + (g('pfine', .5) - .5) * 1.16, pcv: g('pcv', .5) * 2 - 1, pfm: g('pfm', 0),
                 tb: g('timbre', .3) * 10, tcv: g('tcv', 0), sy: g('sym', .5) * 10, or: g('order', 0) * 10 }; }
      if (t === 'lfo') { const g = (q, d) => { const v = P[m.id + '.' + q]; return v === undefined ? d : v; };
        return { F: [1, 2, 3, 4].map(i => g('f' + i, .4)), W: [1, 2, 3, 4].map(i => g('w' + i, 0)), C: [1, 2, 3, 4].map(i => g('s' + i, 1) === 0), a: 1 - Math.exp(-2 * Math.PI * 159 / sr) }; }
      if (t === 'adsr') { // RC through switch (~320 ohm) + 1M log pot into 10 uF X7R (~6 uF at 10 V)
        const tc = x => { const R = 320 + 1e6 * (Math.pow(100, x) - 1) / 99; return 1 - Math.exp(-1 / (sr * R * 6e-6)); };
        return { ka: tc(p('attack')), kd: tc(p('decay')), kr: tc(p('release')), S: 10 * p('sustain') }; }
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
            const q1 = tanh(s.y1), q2 = tanh(s.y2); // taps after the stage tanh: exact cancellation at low freq, like the real ladder
            const LP = s.y4, BP = 2 * q1 - 2 * q2, HP = u - 2 * q1 + q2;
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
          case 'lfo': { // same logic as the RP2040 firmware (octavio_quadlfo.ino), PWM + 2 RC poles at 159 Hz
            s.t++;
            const ch = I[0] > 1.5 ? true : I[0] < 0.8 ? false : s.ch;
            if (ch && !s.ch) { if (s.last >= 0 && s.t - s.last > 0.002 * sr) s.per = s.t - s.last; s.last = s.t; s.n++; s.ledc = s.t + 0.03 * sr; }
            s.ch = ch;
            const rh = I[1] > 1.5 ? true : I[1] < 0.8 ? false : s.rh;
            if (rh && !s.rh) { s.n = 0; s.last = s.t; s.ph = [0, 0, 0, 0]; }
            s.rh = rh;
            const frac = s.per ? cl((s.t - s.last) / s.per, 0, 1) : 0, cpos = (s.n % 48) + frac;
            const RAT = [1 / 16, 1 / 8, 1 / 4, 1 / 3, 1 / 2, 1, 2, 3, 4, 8, 16];
            for (let c = 0; c < 4; c++) {
              const x2 = Math.min(2, Math.max(0, k.W[c] * 2));
              let p;
              if (k.C[c] && s.per) { const x = cpos * RAT[Math.round(k.F[c] * 10)]; p = x - Math.floor(x); s.ph[c] = p; }
              else { s.ph[c] += 0.02 * Math.pow(2, k.F[c] * 10.3) / sr; if (s.ph[c] >= 1) s.ph[c] -= Math.floor(s.ph[c]); p = s.ph[c]; }
              const sn = Math.sin(2 * Math.PI * p), sw = 2 * p - 1, sq = p < 0.5 ? 1 : -1, v = x2 < 1 ? sn + x2 * (sw - sn) : sw + (x2 - 1) * (sq - sw);
              s.y1[c] += k.a * (v - s.y1[c]); s.y2[c] += k.a * (s.y1[c] - s.y2[c]);
              O[c] = 4.9 * s.y2[c];
              const b = 0.5 * (v + 1); s.led[c] = b * b;
            }
            break;
          }
          case 'stg': { // same logic as the RP2040 firmware (octavio_stages.ino)
            const enter = n => { s.pA = k.A[s.stage]; s.pB = k.B[s.stage]; s.stage = n; s.pos = 0; };
            const endSeq = () => { s.endUntil = s.n + 0.005 * sr; if (k.mode === 0) enter(0); else { s.run = false; s.pos = 1; } };
            const startEv = up => { if (up) { s.held = true; if (k.mode === 0) s.run = !s.run; else { enter(0); s.run = true; } } else s.held = false; };
            const aStage = Math.round(cl(k.an + I[4] / 8, 0, 1) * 7);
            s.n++;
            let clk = false;
            for (let q = 0; q < 13; q++) {
              const hi = s.inHi[q] ? I[q] > 0.8 : I[q] > 1.5;
              if (hi !== s.inHi[q]) {
                s.inHi[q] = hi;
                if (q === 0 && hi) { if (s.lastClk >= 0) s.per = s.n - s.lastClk; s.lastClk = s.n; clk = true; }
                else if (q === 1) startEv(hi);
                else if (q === 2 && hi) { enter(aStage); if (k.mode !== 0) s.run = true; }
                else if (q >= 5 && hi) { enter(q - 5); if (k.mode !== 0) s.run = true; }
              }
            }
            if (k.sb !== s.btn) { s.btn = k.sb; startEv(!!k.sb); }
            const ext = s.lastClk >= 0 && s.n - s.lastClk < 3 * sr;
            const hold = k.mode === 2 && s.held && s.stage === aStage && s.run;
            if (s.run) {
              if (ext) { s.pos = Math.min(1, s.pos + 1 / s.per); if (clk && !hold) { if (s.stage === k.end) endSeq(); else enter((s.stage + 1) & 7); } }
              else {
                const tg = 0.01 * Math.pow(1000, k.time) * Math.pow(2, -k.tatt * I[3]);
                const dur = cl(tg * Math.pow(4, k.T[s.stage] * 2 - 1), 0.001, 60);
                s.pos += 1 / (dur * sr);
                if (s.pos >= 1) { if (hold) s.pos = 1; else if (s.stage === k.end) endSeq(); else enter((s.stage + 1) & 7); }
              }
            }
            const st = s.stage, p = Math.min(1, s.pos);
            let a = k.A[st], b = k.B[st];
            if (k.SL[st]) { a = s.pA + (a - s.pA) * p; b = s.pB + (b - s.pB) * p; }
            O[0] = a * 8; O[1] = b * 8;
            const nx = st === k.end ? (k.mode === 0 ? 0 : st) : (st + 1) & 7, act = s.run || hold;
            O[2] = act && (s.pos < .5 || k.SL[nx] || hold) ? 10 : 0;
            O[3] = s.n < s.endUntil ? 10 : 0;
            for (let q = 0; q < 8; q++) O[4 + q] = act && q === st ? 10 : 0;
            break;
          }
          case 'cx': { // after the Buchla 259 : modulation osc, MOD INDEX -> AMPL / PITCH / TIMBRE, principal osc, HARMONICS (fold, saw, M, ORDER)
            let f = cl(440 * Math.pow(2, k.mf + I[0] + k.mcv * I[1] + k.mfm * I[2]), 0.01, 18000), dt = f / sr;
            s.pm += dt; if (s.pm >= 1) s.pm -= 1;
            let ph = s.pm;
            const msaw = (2 * ph - 1 - blep(ph, dt)) * 5, mtri = (2 * Math.abs(2 * ph - 1) - 1) * 5;
            let msq = ph < .5 ? 1 : -1; msq += blep(ph, dt); msq -= blep((ph + .5) % 1, dt); msq *= 5;
            const mw = k.mw === 0 ? mtri : k.mw === 1 ? msq : msaw;
            const MIN = -(k.ix * mw + cl(I[3], 0, 10) / 10 * mw);
            f = cl(440 * Math.pow(2, k.pf + I[5] + k.pcv * I[6] + k.pfm * I[7] + (k.pm ? MIN / 2 : 0)), 0.01, 18000); dt = f / sr;
            s.pc += dt;
            const plv = I[4] * k.pl;                                   // PHASE LOCK : injection into the reset threshold
            if (k.pl > 0 && plv > 0.5 && s.plPrev <= 0.5 && s.pc > 1 - 0.35 * k.pl) s.pc = 1;
            s.plPrev = plv;
            if (s.pc >= 1) s.pc -= 1;
            ph = s.pc;
            const tri = (2 * Math.abs(2 * ph - 1) - 1) * 5, S = 5 * tanh(1.55 * tri / 5) / tanh(1.55);
            const saw = (2 * ph - 1 - blep(ph, dt)) * 5;
            let sq = ph < .5 ? 1 : -1; sq += blep(ph, dt); sq -= blep((ph + .5) % 1, dt); sq *= 5;
            const dz = (v, T) => v > T ? v - T : v < -T ? v + T : 0;
            const tbv = cl(k.tb + k.tcv * I[9] + (k.tm ? MIN : 0), 0, 10.5), syv = cl(k.sy + I[8], 0, 10.5), orv = cl(k.or + I[10], 0, 10.5);
            const x = cl(-(S / 2) * (1 + 3 * tbv / 10) - (2.5 - syv / 2), -10.5, 10.5);
            const F = -2 * (x - 2 * dz(x, 2.6) + 2 * dz(x, 7.8));
            const xm = -0.7 * S, M = 2 * (xm - 2 * dz(xm, 2.5));
            const X = saw + syv / 10 * (M - saw), Y = S + tbv / 10 * (X - S), Z = F + orv / 10 * (Y - F);
            const amv = cl(4.93 - (k.am ? MIN : 0), 0, 10.5);
            O[0] = mtri; O[1] = mw; O[2] = S; O[3] = sq; O[4] = Z * amv / 4.93;
            break;
          }
          case 'adsr': { // Moog 911-style : attack toward +12 V until 10 V, decay toward SUSTAIN, release toward 0
            const gi = I[0];
            if (!s.g && gi > 3.1) { s.g = true; s.att = 1; } else if (s.g && gi < 2.6) { s.g = false; s.att = 0; }
            if (s.att) { s.env += (12 - s.env) * k.ka; if (s.env >= 10) { s.env = 10; s.att = 0; } }
            else if (s.g) s.env += (k.S - s.env) * k.kd;
            else s.env -= s.env * k.kr;
            O[0] = s.env; O[1] = -s.env; if (s.env > s.ledMax) s.ledMax = s.env;
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
            else if (m.type === 'adsr') { r.leds[m.id] = m.s.ledMax / 10; m.s.ledMax = 0; }
            else if (m.type === 'lfo') { for (let c = 0; c < 4; c++) r.leds[m.id + '.l' + (c + 1)] = m.s.led[c]; r.leds[m.id + '.lc'] = m.s.t < m.s.ledc ? 1 : 0; }
            else if (m.type === 'stg') { r.stg = r.stg || {}; r.stg[m.id] = { stage: m.s.stage, run: m.s.run }; }
          }
          this.report(r);
        }
      }
    }
  }
}
