// ocTavio SEMI - behavioural models, one sample at a time, voltages in volts (Eurorack levels).
// Same models as the ocTavio Eurorack simulator (SIM/source/engine.js) where the circuit is the same
// (921 VCO, ladder, 902 VCA, 911 ADSR, S&H / LAG, MC1496 ring, spring reverb) + the new state-variable filter and LFOs.
class SemiEngine {
  constructor(sr) {
    this.sr = sr; this.P = {}; this.held = []; this.key = null; this.seed = 7; this.cnt = 0;
    const outs = [], ins = [];
    for (const t of SEMI_DEF.tiers) for (const s of t.secs) {
      for (const [j, , t] of s.out) if (t !== 'midi') outs.push(s.id + '.' + j);   // MIDI jacks are not CV
      for (const [j, , t] of s.in) if (t !== 'midi') ins.push(s.id + '.' + j);
      for (const [k, , v] of s.sl) this.P[s.id + '.' + k] = v;
      for (const [k, , , v] of (s.sw || [])) this.P[s.id + '.' + k] = v;
    }
    this.P['kb.seq'] = 1;
    this.outs = outs; this.ins = ins;
    this.O = new Float64Array(outs.length); this.I = new Float64Array(ins.length);
    this.o = {}; outs.forEach((n, i) => this.o[n] = i);
    this.i = {}; ins.forEach((n, i) => this.i[n] = i);
    this.pat = new Uint8Array(ins.length);
    this.cab = [];                       // [outIndex, inIndex]
    this.nrm = ins.map(n => { const v = SEMI_DEF.normals[n]; return v === undefined ? null : v; });
    this.resolve([]);
    this.s = {
      vco: [0, 1, 2].map(() => ({ ph: Math.random(), syncHi: false, dr: 0, lp: [0, 0, 0, 0] })), drift: [0, 0], dph: 0,
      vcf: { y1: 0, y2: 0, y3: 0, y4: 0, hp: 0, hpx: 0 }, svf: { a: 0, b: 0 },
      env: [0, 1].map(() => ({ env: 0, att: 0, g: false, led: 0 })),
      lfo: [0, 1].map(() => ({ ph: 0, tr: 0, led: 0 })),
      sh: { tri: 0, sq: 1, th: false, hold: 0, lag: 0, b: [0, 0, 0, 0, 0, 0, 0], g2: null },
      rev: null, kb: { cv: 0, cvT: 0, gHi: false, tr: 0, seqPh: 0, step: 0, lastCv: -1 }, vel: 8, cc1: 0, spk: [0, 0, 0],
      scope: new Float32Array(1024),
    };
    const sp = [0.0371, 0.0433, 0.0517].map((d, k) => ({ buf: new Float32Array(Math.ceil(d * sr) + 2), w: 0, len: Math.round(d * sr), ap: new Float32Array(24), lp: 0, mod: k * 2.1 }));
    this.s.rev = { sp, hp: 0, hpx: 0, lpIn: 0, tone: 0, t: 0 };
  }
  msg(d) {
    if (d.t === 'p') this.P[d.k] = d.v;
    else if (d.t === 'cables') this.resolve(d.list);
    else if (d.t === 'state') { Object.assign(this.P, d.params || {}); this.resolve(d.cables || []); }
    else if (d.t === 'note') {
      const i = this.held.indexOf(d.n); if (i >= 0) this.held.splice(i, 1);
      if (d.on) this.held.push(d.n);
      this.key = this.held.length ? this.held[this.held.length - 1] : null;
      if (d.on && d.v !== undefined) this.s.vel = 10 * d.v / 127;           // VEL output : 0..10 V (MIDI velocity)
    }
    else if (d.t === 'cc1') this.s.cc1 = 10 * d.v / 127;                     // MOD output : 0..10 V (mod wheel)
  }
  resolve(list) {
    this.cab = []; this.pat.fill(0);
    for (const [a, b] of list) { const oi = this.o[a], ii = this.i[b]; if (oi !== undefined && ii !== undefined) { this.cab.push([oi, ii]); this.pat[ii] = 1; } }
    // normalled inputs that are not plugged : [inIndex, outIndex] or a fixed voltage
    this.nOut = []; this.nCst = [];
    this.nrm.forEach((v, ii) => { if (v === null || this.pat[ii]) return; if (typeof v === 'number') this.nCst.push([ii, v]); else this.nOut.push([ii, this.o[v]]); });
  }
  rnd() { this.seed = (this.seed * 16807) % 2147483647; return this.seed / 2147483647; }
  gauss() { let u, v, q; do { u = 2 * this.rnd() - 1; v = 2 * this.rnd() - 1; q = u * u + v * v; } while (q >= 1 || q === 0); return u * Math.sqrt(-2 * Math.log(q) / q); }
  render(L, R, n) {
    const sr = this.sr, P = this.P, tanh = Math.tanh, S = this.s, O = this.O, I = this.I, o = this.o, i = this.i, pat = this.pat;
    const cl = (x, a, b) => x < a ? a : (x > b ? b : x);
    const blep = (t, dt) => { if (t < dt) { t /= dt; return t + t - t * t - 1; } if (t > 1 - dt) { t = (t - 1) / dt; return t * t + t + t + 1; } return 0; };
    const p = k => P[k];
    const A = x => (Math.pow(10, 2 * x) - 1) / 99;           // audio-taper slide pot
    const SEQ = [0, 12, 0, 7, 3, 0, 10, 7, 0, 12, 3, 5, 7, 0, 15, 10];
    // ---- per-block constants (slider positions)
    const V = [1, 2, 3].map(n => { const id = 'vco' + n; return {
      base: (p(id + '.coarse') - .5) * 6 + (p(id + '.fine') - .5) + (p(id + '.range') ? -7 : 0),
      w: p(id + '.width'), fm: p(id + '.fm') * p(id + '.fm'), pwm: p(id + '.pwm'),
      vo: o[id + '.sine'], iv: i[id + '.voct'], ifm: i[id + '.fm'], ipw: i[id + '.pwm'] }; });
    const kVlp = 1;   // SPICE of the 921 core : linear ramp, flat to well above 20 kHz -> no extra roll-off
    const sync2 = p('vco2.sync') === 1, kbd3 = p('vco3.kbd') === 0, stab = p('vco3.stab'), isy = i['vco2.sync'];
    const ml = [1, 2, 3, 4, 5].map(k => { const v = p('mix.l' + k); return v * v; });
    const md = p('vcf.mode'), fa = md < 0.5 ? 1 - 2 * md : 0, fc_ = md > 0.5 ? 2 * md - 1 : 0;
    const fFr = p('vcf.freq'), fE = p('vcf.emph'), fK = p('vcf.kbd'), fEnv = p('vcf.env'), fMod = p('vcf.mod');
    // SEM style (SPICE of SEMI/circuits/svf.py) : MODE slider = divider between LP and HP (middle = notch), BP switch ; resonance up to self-oscillation
    const sFr = p('svf.freq'), sK = 2 * (1 - p('svf.reso')) - 0.03, sEnv = p('svf.env'), sMod = p('svf.mod'), sm = p('svf.mode'), sbp = p('svf.bp') === 1;
    const va1 = p('vca.l1') ** 2, va2 = p('vca.l2') ** 2, vcv = p('vca.cv'), vfx = p('vca.initial'), vr = p('vca.response');
    const tc = (x, C) => { const Rr = 320 + 1e6 * (Math.pow(100, x) - 1) / 99; return 1 - Math.exp(-1 / (sr * Rr * C)); };
    const E = [1, 2].map(n => { const id = 'env' + n, C = p(id + '.speed') ? 150e-6 : 6e-6;
      return { ka: tc(p(id + '.a'), C), kd: tc(p(id + '.d'), C), kr: tc(p(id + '.r'), C), S: 10 * p(id + '.s'), ig: i[id + '.gate'], oo: o[id + '.out'] }; });
    // WAVE = constant-period symmetry (SPICE of SEMI/circuits/lfo.py) : the rising part goes from 92 % (RAMP UP) to 8 % (RAMP DOWN) of the cycle
    const LF = [1, 2].map(n => { const id = 'lfo' + n; return { r: p(id + '.rate'), rise: 0.918 - 0.836 * p(id + '.wave'), ic: i[id + '.rcv'], oo: o[id + '.out'], osq: o[id + '.sq'], otr: o[id + '.trig'] }; });
    const shf = 106 * (A(p('sh.rate')) + 0.0045), C2 = 2.2e-6, kRise = 1 / ((1e3 + 1e6 * A(p('sh.rise'))) * C2 * sr), kFall = 1 / ((1e3 + 1e6 * A(p('sh.fall'))) * C2 * sr), col = p('sh.color');
    const rx = p('ring.xl'), ry = p('ring.yl');
    const fcR = 1500 + 9000 * p('rev.tone') * p('rev.tone');
    const R_ = { gd: (4.7 + 100 * A(p('rev.drive'))) / 22, kt: 1 - Math.exp(-2 * Math.PI * fcR / sr), mw: (2 * p('rev.mix') - 1) * 12,
      kd: 1 - Math.exp(-2 * Math.PI * 4200 / sr), kh: Math.exp(-2 * Math.PI * 120 / sr), ki: 1 - Math.exp(-2 * Math.PI * 5000 / sr) };
    const spkOn = p('mult.spk') === 0, kS1 = 1 - Math.exp(-2 * Math.PI * 180 / sr), kS2 = 1 - Math.exp(-2 * Math.PI * 6000 / sr);
    const vol = p('out.vol'), gl = p('kb.glide'), kgl = gl < 0.005 ? 1 : 1 - Math.exp(-1 / (sr * 0.002 * Math.pow(1000, gl)));
    const seqOn = p('kb.seq'), step = 60 / 120 / 2, a1 = p('att.a1') * 2 - 1, a2 = p('att.a2') * 2 - 1;
    const g2 = 1 / (2 * sr), cab = this.cab, nc = cab.length, nO = this.nOut, nCs = this.nCst, nI = I.length;
    for (let t = 0; t < n; t++) {
      // ---- inputs : user cables add up, unplugged inputs get their normal (previous sample)
      for (let k = 0; k < nI; k++) I[k] = 0;
      for (let k = 0; k < nc; k++) I[cab[k][1]] += O[cab[k][0]];
      for (let k = 0; k < nO.length; k++) I[nO[k][0]] = O[nO[k][1]];
      for (let k = 0; k < nCs.length; k++) I[nCs[k][0]] = nCs[k][1];
      // ---- KEYBOARD : on-screen keys / demo sequence, CV IN and GATE IN override, glide, trig
      const kb = S.kb; let kcv, kg;
      if (this.key !== null) { kcv = (this.key - 60) / 12; kg = 5; kb.lastCv = kcv; }
      else if (seqOn) { kb.seqPh += 1 / sr; if (kb.seqPh >= step) { kb.seqPh -= step; kb.step = (kb.step + 1) % SEQ.length; }
        kcv = -1 + SEQ[kb.step] / 12; kg = kb.seqPh < step * 0.5 ? 5 : 0; kb.lastCv = kcv; }
      else { kcv = kb.lastCv; kg = 0; }
      if (pat[i['kb.cvin']]) kcv = I[i['kb.cvin']];
      if (pat[i['kb.gatein']]) kg = Math.max(kg, I[i['kb.gatein']] > 1.5 ? 5 : 0);
      kb.cv += (kcv - kb.cv) * kgl;
      const gHi = kg > 2.5; if (gHi && !kb.gHi) kb.tr = 0.002 * sr; kb.gHi = gHi;
      O[o['kb.vel']] = S.vel; O[o['kb.mod']] = S.cc1;
      O[o['kb.cv']] = kb.cv; O[o['kb.gate']] = kg; O[o['kb.trig']] = kb.tr > 0 ? 10 : 0; if (kb.tr > 0) kb.tr--;
      // ---- LFO 1 / 2 : triangle core, WAVE = symmetry (RAMP UP -> TRI -> RAMP DOWN), SQ = Schmitt output, TRIG at the start of each rise
      for (let q = 0; q < 2; q++) {
        const l = S.lfo[q], k = LF[q];
        l.ph += 0.02 * Math.pow(2, k.r * 11.3 + I[k.ic]) / sr; let tr = false;
        if (l.ph >= 1) { l.ph -= Math.floor(l.ph); tr = true; }
        const ph = l.ph, rising = ph < k.rise;
        const v = rising ? -1 + 2 * ph / k.rise : 1 - 2 * (ph - k.rise) / (1 - k.rise);
        if (tr) l.tr = 0.0056 * sr;
        O[k.oo] = 4.9 * v; O[k.osq] = rising ? -5.2 : 5.2; O[k.otr] = l.tr > 0 ? 10 : 0; if (l.tr > 0) l.tr--;
        const b = 0.5 * (v + 1); if (b * b > l.led) l.led = b * b;
      }
      // ---- NOISE / S&H / LAG
      const sh = S.sh; let wn; if (sh.g2 !== null) { wn = sh.g2; sh.g2 = null; } else { wn = this.gauss(); sh.g2 = this.gauss(); }
      const W = cl(1.7 * wn, -5.5, 5.5), b = sh.b;
      b[0] = 0.99886 * b[0] + W * 0.0555179; b[1] = 0.99332 * b[1] + W * 0.0750759; b[2] = 0.96900 * b[2] + W * 0.1538520;
      b[3] = 0.86650 * b[3] + W * 0.3104856; b[4] = 0.55000 * b[4] + W * 0.5329522; b[5] = -0.7616 * b[5] - W * 0.0168980;
      const pk = (b[0] + b[1] + b[2] + b[3] + b[4] + b[5] + b[6] + W * 0.5362) * 0.24; b[6] = W * 0.115926;
      O[o['sh.noise']] = W + col * (1.25 * pk - W);
      sh.tri -= sh.sq * 4 * 5.5 * shf / sr;
      if (sh.tri <= -5.5 && sh.sq > 0) sh.sq = -1; else if (sh.tri >= 5.5 && sh.sq < 0) sh.sq = 1;
      O[o['sh.clock']] = sh.sq > 0 ? 11 : 0;
      const hi = I[i['sh.clk']] > 1.57; if (hi && !sh.th) sh.hold = cl(I[i['sh.shin']], -11, 11); sh.th = hi;
      O[o['sh.sh']] = sh.hold;
      const tg = I[i['sh.lagin']];
      if (tg > sh.lag) { sh.lag += (10.4 - sh.lag) * kRise; if (sh.lag > tg) sh.lag = tg; } else { sh.lag += (-10.4 - sh.lag) * kFall; if (sh.lag < tg) sh.lag = tg; }
      O[o['sh.lag']] = sh.lag;
      // ---- ENVELOPES (911 style RC, FAST / SLOW = timing capacitor x25)
      for (let q = 0; q < 2; q++) {
        const e = S.env[q], k = E[q], gi = I[k.ig];
        if (!e.g && gi > 3.1) { e.g = true; e.att = 1; } else if (e.g && gi < 2.6) { e.g = false; e.att = 0; }
        if (e.att) { e.env += (12 - e.env) * k.ka; if (e.env >= 10) { e.env = 10; e.att = 0; } }
        else if (e.g) e.env += (k.S - e.env) * k.kd; else e.env -= e.env * k.kr;
        O[k.oo] = e.env; O[k.oo + 1] = -e.env; if (e.env > e.led) e.led = e.env;
      }
      // ---- 3 VCO (921 core). VCO 3 : STABILITY = slow drift, KBD OFF = ignores the keyboard
      S.dph += 1 / sr; const nz = this.gauss(); S.drift[0] += 0.00002 * (nz - S.drift[0] * 0.05); S.drift[1] = 0.6 * Math.sin(S.dph * 0.41) + 0.4 * Math.sin(S.dph * 0.173 + 1) + S.drift[0];
      for (let q = 0; q < 3; q++) {
        const k = V[q], s = S.vco[q];
        let voct = I[k.iv]; if (q === 2 && !kbd3 && !pat[k.iv]) voct = 0;
        s.dr += 0.00004 * (this.gauss() - s.dr * 0.02);              // every core drifts a little (~±2 cents), like the real 921
        let ex = k.base + voct + I[k.ifm] * k.fm + 0.0016 * s.dr; if (q === 2) ex += stab * 0.035 * S.drift[1];
        const fr = cl(261.63 * Math.pow(2, ex), 0.02, 20000), dt = fr / sr;
        if (q === 1) { const sv = (sync2 || pat[isy]) ? I[isy] : 0; if (sv > 1 && !s.syncHi) { s.ph = 0; s.syncHi = true; } else if (sv < 0.5) s.syncHi = false; }
        s.ph += dt; if (s.ph >= 1) s.ph -= 1;
        const ph = s.ph;
        const saw = (2 * ph - 1 - blep(ph, dt)) * 5, tri = (2 * Math.abs(2 * ph - 1) - 1) * 5;
        const duty = cl(0.05 + 0.9 * k.w + I[k.ipw] * k.pwm * 0.09, 0.02, 0.98);
        let pul = ph < duty ? 1 : -1; pul += blep(ph, dt); pul -= blep((ph + 1 - duty) % 1, dt);
        const W4 = [5 * tanh(1.55 * tri / 5) / tanh(1.55), tri, saw, 5 * pul];
        for (let w = 0; w < 4; w++) O[k.vo + w] = W4[w];
      }
      // ---- RING MOD (MC1496)
      O[o['ring.out']] = cl(1.0636 * cl(I[i['ring.x']] * rx, -10.4, 10.4) * tanh(I[i['ring.y']] * ry * 0.5656), -11, 11);
      // ---- AUDIO MIXER : 5 slide pots into a summing amp, soft rails
      const mx = I[i['mix.in1']] * ml[0] + I[i['mix.in2']] * ml[1] + I[i['mix.in3']] * ml[2] + I[i['mix.in4']] * ml[3] + I[i['mix.in5']] * ml[4];
      O[o['mix.out']] = 7.5 * tanh(mx / 7.5 + 0.04) - 7.5 * tanh(0.04);
      // ---- LADDER FILTER (same model as the VCF module)
      { const f = S.vcf;
        // FREQUENCY range and EMPHASIS curve fitted on the SPICE run of the VCF board (outils/spice) : 20 Hz -> 13 kHz, self-oscillation near 9
        let fc = 20.4 * Math.pow(2, 9.3 * fFr + I[i['vcf.kbd']] * fK + I[i['vcf.env']] * fEnv * 0.8 + I[i['vcf.mod']] * fMod * 0.5); fc = 16000 * tanh(cl(fc, 5, 40000) / 16000);
        const g = 1 - Math.exp(-2 * Math.PI * fc * g2), kk = 4.3 * Math.pow(fE, 1.4) / (1 + (fc / 9000) * (fc / 9000));   // fade near the top = simulation limit (no aliasing scream), not the circuit
        const xin = I[i['vcf.in']] * 0.18 + (this.rnd() - 0.5) * 1e-4; let u = 0;
        for (let r = 0; r < 2; r++) { u = tanh(xin - kk * f.y4); const t1 = tanh(f.y1), t2 = tanh(f.y2), t3 = tanh(f.y3);
          f.y1 += g * (u - t1); f.y2 += g * (t1 - t2); f.y3 += g * (t2 - t3); f.y4 += g * (t3 - tanh(f.y4)); }
        const q1 = tanh(f.y1), q2 = tanh(f.y2), LP = f.y4, BP = 2 * q1 - 2 * q2, HP = u - 2 * q1 + q2;
        const fo = -0.67 * (BP + fa * (LP - BP) + fc_ * (HP - BP)) / 0.18;   // SPICE : passband -3.5 dB
        f.hp = 0.9993 * (f.hp + fo - f.hpx); f.hpx = fo; O[o['vcf.out']] = f.hp; }
      // ---- STATE VARIABLE FILTER 12 dB (TPT, soft-clipped integrators), MODE LP -> NOTCH -> HP, BP switch
      { const f = S.svf;
        let fc = 20 * Math.pow(2, 10 * sFr + I[i['svf.env']] * sEnv * 0.8 + I[i['svf.mod']] * sMod * 0.5); fc = cl(fc, 10, 0.42 * sr);
        const g = Math.tan(Math.PI * fc / sr), a1_ = 1 / (1 + g * (g + sK)), a2_ = g * a1_, a3_ = g * a2_;
        const x = I[i['svf.in']] * 0.2 + (this.rnd() - 0.5) * 1e-5, v3 = x - f.b, v1 = a1_ * f.a + a2_ * v3, v2 = f.b + a2_ * f.a + a3_ * v3;
        f.a = 2.2 * tanh((2 * v1 - f.a) / 2.2); f.b = 2 * v2 - f.b;
        const lp = v2, bp = v1, hp = x - sK * v1 - v2, nt = lp + hp;
        O[o['svf.out']] = 10.5 * tanh((sbp ? bp : (1 - sm) * lp + sm * hp) / 0.2 / 10.5); }
      // ---- AMPLIFIER (902 : LIN <-> EXP, soft clip), 2 inputs with level sliders
      { const Vc = Math.max(0, 6 * vfx + 0.6 * vcv * I[i['vca.cv']]);
        let ga = (1 - vr) * Vc / 3 + vr * 2 * Math.pow(10, 13 * (Vc - 6) / 20); if (ga > 2) ga = 2 + 0.6 * tanh((ga - 2) / 0.6);
        let ya = ga * 12.6 * tanh((I[i['vca.in1']] * va1 + I[i['vca.in2']] * va2) / 12.6); O[o['vca.out']] = 9 * tanh(ya / 9); }
      // ---- SPRING REVERB (same model as the SPRING REVERB module, MIX on a slider)
      { const r = S.rev, dry = -I[i['rev.in']], drv = cl(-dry * R_.gd, -10.8, 10.8);
        r.lpIn += R_.ki * (drv - r.lpIn); const x = 0.3 * tanh(r.lpIn / 6) * 6; let wet = 0; r.t++;
        for (let q = 0; q < 3; q++) {
          const sp = r.sp[q], Lb = sp.buf.length;
          let rr = sp.w - sp.len - 1.5 - 1.5 * Math.sin(r.t * 0.00021 + sp.mod); while (rr < 0) rr += Lb;
          const i0 = Math.floor(rr), fr = rr - i0, y = sp.buf[i0 % Lb] * (1 - fr) + sp.buf[(i0 + 1) % Lb] * fr;
          sp.lp += R_.kd * (y - sp.lp); let v = x + 0.9 * sp.lp; const ap = sp.ap;
          for (let a = 0; a < 24; a++) { const oo = -0.62 * v + ap[a]; ap[a] = v + 0.62 * oo; v = oo; }
          sp.buf[sp.w] = v; sp.w = (sp.w + 1) % Lb; wet += y;
        }
        const hp = wet - r.hpx + R_.kh * r.hp; r.hpx = wet; r.hp = hp; r.tone += R_.kt * (hp * 1.6 - r.tone);
        const wb = cl(r.tone, -11, 11), fw = 1 / (1 + Math.exp(cl(-0.47 * R_.mw, -10.5, 10.5) * 0.0215 / 0.02585));
        O[o['rev.out']] = cl(-1.0045 * 0.0517 * (fw * tanh(wb * 0.002132 / 0.0517) + (1 - fw) * tanh(dry * 0.002132 / 0.0517)) / 0.002132, -11, 11); }
      // ---- ATTENUVERTERS (empty input = +5 V) and MULTIPLE
      O[o['att.o1']] = cl(I[i['att.in1']] * a1, -11, 11); O[o['att.o2']] = cl(I[i['att.in2']] * a2, -11, 11);
      O[o['mult.o1']] = O[o['mult.o2']] = O[o['mult.o3']] = I[i['mult.in']];
      // ---- OUTPUT : VOLUME, MAIN (Eurorack level) and PHONES
      const main = cl(I[i['out.in']] * vol * 1.4, -10, 10); O[o['out.main']] = main; O[o['out.phones']] = main;
      let y = tanh(main * 0.2);
      if (spkOn) { const z = S.spk; z[0] += kS1 * (y - z[0]); const hpo = y - z[0]; z[1] += kS2 * (hpo - z[1]); z[2] += kS2 * (z[1] - z[2]); y = tanh(1.6 * z[2]) * 0.8; }   // little 40 mm speaker : ~180 Hz -> ~6 kHz
      L[t] = y; if (R) R[t] = y;
      S.scope[this.cnt % 1024] = main;
      if (++this.cnt >= 2048) {
        this.cnt = 0;
        if (this.report) {
          const leds = { env1: S.env[0].led / 10, env2: S.env[1].led / 10, lfo1: S.lfo[0].led, lfo2: S.lfo[1].led };
          S.env[0].led = S.env[1].led = S.lfo[0].led = S.lfo[1].led = 0;
          this.report({ leds, scope: S.scope.slice(0) });
        }
      }
    }
  }
}
