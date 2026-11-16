// ocTavio Eurorack - behavioural models of our circuits, run per sample (voltages in volts)
class OctavioEngine {
  constructor(sr) {
    this.sr = sr;
    this.P = {};                 // knob/switch values 'mod.key'
    this.cab = [];               // [srcKey, dstKey]
    this.O = {};                 // outputs (previous sample)
    this.I = {};                 // inputs (summed cables)
    this.key = null; this.seqPh = 0; this.seqStep = 0;
    this.vco = { ph: 0, syncHi: false };
    this.vcf = { y1: 0, y2: 0, y3: 0, y4: 0, hp: 0, hpx: 0 };
    this.ad = { env: 0, latch: 0, trHi: false };
    this.scope = new Float32Array(2048); this.si = 0; this.report = null;
    this.ledMax = 0; this.peak = 0;
    this.seed = 1;
  }
  msg(d) {
    if (d.t === 'p') this.P[d.k] = d.v;
    else if (d.t === 'cables') this.cab = d.list;
    else if (d.t === 'key') { this.key = d.note; }
    else if (d.t === 'note') {
      if (!this.held) this.held = [];
      const i = this.held.indexOf(d.n); if (i >= 0) this.held.splice(i, 1);
      if (d.on) this.held.push(d.n);
      this.key = this.held.length ? this.held[this.held.length - 1] : null;
    }
    else if (d.t === 'state') { this.P = Object.assign({}, d.params); this.cab = d.cables; }
  }
  p(k, def) { const v = this.P[k]; return v === undefined ? def : v; }
  render(L, R, n) {
    const sr = this.sr, P = (k, d) => this.p(k, d);
    const cl = (x, a, b) => x < a ? a : (x > b ? b : x);
    const tanh = Math.tanh;
    const blep = (t, dt) => {
      if (t < dt) { t /= dt; return t + t - t * t - 1; }
      if (t > 1 - dt) { t = (t - 1) / dt; return t * t + t + t + 1; }
      return 0;
    };
    // read knobs once per block
    const vco_r = [-7, -2, -1, 0, 1, 2][P('vco.range', 3)], vco_f = P('vco.fine', 0.5) - 0.5, vco_w = P('vco.width', 0.5),
      vco_fm = P('vco.fm', 0), vco_pwm = P('vco.pwm', 0), vco_b = P('vco.blend', 0);
    const c1 = cl(3 * vco_b, 0, 1), c2 = cl(3 * vco_b - 1, 0, 1), c3 = cl(3 * vco_b - 2, 0, 1);
    const potLoad = a => { const Rb = a, Rt = 1 - a, par = Rb / (Rb + 1 + 1e-9); return par / (Rt + par + 1e-12); };
    const ml = [1, 2, 3, 4].map(k => potLoad(P('mix.l' + k, 0)));
    const mm = P('mix.master', 0), Rf = 10 + 100 * mm, G = Rf / 10, slope = 4.7 / (Rf + 4.7);
    const f_m = P('vcf.mode', 0), f_fr = P('vcf.freq', 0.5), f_e = P('vcf.emph', 0), f_c = P('vcf.contour', 0), f_fc = P('vcf.fcv', 0), f_ec = P('vcf.ecv', 0);
    const fa = f_m < 0.5 ? 1 - 2 * f_m : 0, fc_ = f_m > 0.5 ? 2 * f_m - 1 : 0;
    const a_cv = P('vca.cvlevel', 0.5), a_r = P('vca.response', 0.5), a_fx = P('vca.fixed', 0);
    const d_a = P('ad.attack', 0.2), d_d = P('ad.decay', 0.5), d_acv = P('ad.acv', 0), d_dcv = P('ad.dcv', 0), d_cyc = P('ad.cycle', 0);
    const s_t = P('sim.tempo', 0.45), s_on = P('sim.seq', 1), s_v = P('sim.volume', 0.5);
    const bpm = 50 + 190 * s_t, stepLen = 60 / bpm / 2;
    const SEQ = [0, 12, 0, 7, 3, 0, 10, 7, 0, 12, 3, 5, 7, 0, 15, 10];
    const cab = this.cab, O = this.O, I = this.I;
    const IN = ['vco.voct', 'vco.fm', 'vco.pwm', 'vco.sync', 'mix.in1', 'mix.in2', 'mix.in3', 'mix.in4', 'vcf.in1', 'vcf.in2', 'vcf.contour', 'vcf.fcv', 'vcf.ecv',
      'vca.in1', 'vca.in2', 'vca.cv1', 'vca.cv2', 'vca.cv3', 'ad.trig', 'ad.acv', 'ad.dcv', 'sim.audio', 'sim.scope'];
    const vs = this.vco, f = this.vcf, ad = this.ad;
    const g2 = 1 / (2 * sr);
    for (let i = 0; i < n; i++) {
      for (let k = 0; k < IN.length; k++) I[IN[k]] = 0;
      for (let k = 0; k < cab.length; k++) { const s = O[cab[k][0]]; if (s !== undefined) I[cab[k][1]] += s; }
      // ---------------- SIM : sequencer / keyboard ----------------
      let cv, gate;
      if (this.key !== null) { cv = (this.key - 60) / 12; gate = 5; this.lastCv = cv; }
      else if (s_on) {
        this.seqPh += 1 / sr;
        if (this.seqPh >= stepLen) { this.seqPh -= stepLen; this.seqStep = (this.seqStep + 1) % SEQ.length; }
        cv = -1 + SEQ[this.seqStep] / 12; gate = this.seqPh < stepLen * 0.5 ? 5 : 0; this.lastCv = cv;
      } else { cv = this.lastCv || 0; gate = 0; }
      O['sim.cv'] = cv; O['sim.gate'] = gate;
      // ---------------- VCO (921 core : expo -> saw reset, tri, sine shaper, pulse, blend) ----------------
      let v = vco_r + vco_f + I['vco.voct'] + I['vco.fm'] * vco_fm;
      let fr = 261.63 * Math.pow(2, v); fr = cl(fr, 0.02, 20000);
      const dt = fr / sr;
      const sy = I['vco.sync'];
      if (sy > 1 && !vs.syncHi) { vs.ph = 0; vs.syncHi = true; } else if (sy < 0.5) vs.syncHi = false;
      vs.ph += dt; if (vs.ph >= 1) vs.ph -= 1;
      const ph = vs.ph;
      const saw = (2 * ph - 1 - blep(ph, dt)) * 5;
      const tri = (2 * Math.abs(2 * ph - 1) - 1) * 5;
      const sine = 5 * tanh(1.55 * tri / 5) / tanh(1.55);
      const duty = cl(0.05 + 0.9 * vco_w + I['vco.pwm'] * vco_pwm * 0.09, 0.02, 0.98);
      let pul = ph < duty ? 1 : -1; pul += blep(ph, dt); pul -= blep((ph + 1 - duty) % 1, dt); pul *= 5;
      O['vco.saw'] = saw; O['vco.tri'] = tri; O['vco.sine'] = sine; O['vco.pulse'] = pul;
      O['vco.blend'] = sine + c1 * (tri - sine) + c2 * (saw - tri) + c3 * (pul - saw);
      // ---------------- MIX (CP3 summer + MASTER GAIN with zener soft knee, rails) ----------------
      const x = I['mix.in1'] * ml[0] + I['mix.in2'] * ml[1] + I['mix.in3'] * ml[2] + I['mix.in4'] * ml[3];
      const lin = G * x, ax = Math.abs(lin), w = 0.3;
      const z = (ax - 5.8) / w, sp = z > 30 ? z * w : w * Math.log(1 + Math.exp(z));
      let y = ax - (1 - slope) * sp;
      y = y / Math.pow(1 + Math.pow(y / 10.5, 8), 0.125);
      y = lin < 0 ? -y : y;
      O['mix.out'] = y; O['mix.nout'] = -y;
      // ---------------- VCF (4-pole transistor ladder, taps y0/y1/y2/y4 + LP->BP->HP morph) ----------------
      let fc = 20 * Math.pow(2, 10 * f_fr + I['vcf.fcv'] * f_fc + I['vcf.contour'] * f_c * 0.6);
      fc = cl(fc, 5, Math.min(20000, 0.45 * sr));
      const g = 1 - Math.exp(-2 * Math.PI * fc * g2);
      const kk = 4.3 * cl(f_e + I['vcf.ecv'] * f_ec * 0.1, 0, 1.15);
      this.seed = (this.seed * 16807) % 2147483647;
      const xin = (I['vcf.in1'] + I['vcf.in2']) * 0.18 + (this.seed / 2147483647 - 0.5) * 1e-4;
      let u = 0;
      for (let o = 0; o < 2; o++) {
        u = tanh(xin - kk * f.y4);
        const t1 = tanh(f.y1), t2 = tanh(f.y2), t3 = tanh(f.y3);
        f.y1 += g * (u - t1); f.y2 += g * (t1 - t2); f.y3 += g * (t2 - t3); f.y4 += g * (t3 - tanh(f.y4));
      }
      const LP = f.y4, BP = 2 * f.y1 - 2 * f.y2, HP = u - 2 * f.y1 + f.y2;
      const fo = -(BP + fa * (LP - BP) + fc_ * (HP - BP)) / 0.18;
      f.hp = 0.9993 * (f.hp + fo - f.hpx); f.hpx = fo;              // C20 AC coupling
      O['vcf.out'] = f.hp;
      // ---------------- AD (OTA slew core, expo times, latch, cycle) ----------------
      const tr = I['ad.trig'];
      if (tr > 1 && !ad.trHi) { ad.trHi = true; ad.latch = 1; } else if (tr < 0.5) ad.trHi = false;
      if (d_cyc && !ad.latch && ad.env < 0.2) ad.latch = 1;
      if (ad.latch) {
        const Ta = cl(0.0008 * Math.pow(10, 4 * d_a) * Math.pow(100, I['ad.acv'] * d_acv / 5), 0.0002, 60);
        ad.env += (9.3 / Ta) / sr * tanh((11 - ad.env) / 1.5) / tanh(11 / 1.5);
        if (ad.env >= 9.3) ad.latch = 0;
      } else {
        const Td = cl(0.0008 * Math.pow(10, 4 * d_d) * Math.pow(100, I['ad.dcv'] * d_dcv / 5), 0.0002, 60);
        ad.env -= (9.3 / Td) / sr * tanh(ad.env / 1.5) / tanh(9.3 / 1.5);
        if (ad.env < 0) ad.env = 0;
      }
      O['ad.out'] = ad.env;
      if (ad.env > this.ledMax) this.ledMax = ad.env;
      // ---------------- VCA (902 : diff pair, LIN/EXP blend, soft clip) ----------------
      const Vc = Math.max(0, 6 * a_fx + a_cv * (I['vca.cv1'] + I['vca.cv2'] + I['vca.cv3']));
      let ga = (1 - a_r) * Vc / 3 + a_r * 2 * Math.pow(10, 13 * (Vc - 6) / 20);
      if (ga > 2) ga = 2 + 0.6 * tanh((ga - 2) / 0.6);
      const xd = I['vca.in1'] - I['vca.in2'];
      let ya = ga * 12.6 * tanh(xd / 12.6); ya = 9 * tanh(ya / 9);
      O['vca.outp'] = ya; O['vca.outn'] = -ya;
      // ---------------- SIM : speakers + scope ----------------
      const au = I["sim.audio"] * 0.25 * (2 * s_v) * (2 * s_v);
      const sp_ = Math.tanh(au);
      if (Math.abs(au) > this.peak) this.peak = Math.abs(au);
      L[i] = sp_; if (R) R[i] = sp_;
      this.scope[this.si++] = I['sim.scope'];
      if (this.si >= this.scope.length) {
        this.si = 0;
        if (this.report) this.report({ scope: this.scope.slice(0), led: this.ledMax / 9.3, peak: this.peak });
        this.ledMax = 0; this.peak = 0;
      }
    }
  }
}

class OctavioSim extends AudioWorkletProcessor {
  constructor() { super(); this.e = new OctavioEngine(sampleRate); this.e.report = r => this.port.postMessage(r); this.port.onmessage = ev => this.e.msg(ev.data); }
  process(inputs, outputs) { const o = outputs[0]; this.e.render(o[0], o[1], o[0].length); return true; }
}
registerProcessor('octavio-sim', OctavioSim);
