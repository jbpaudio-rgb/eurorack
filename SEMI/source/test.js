// node test.js '{"param":value}' '[["out","in"]]' out.wav  -> renders 4 s, prints peaks of every output
const fs = require('fs'), path = require('path');
eval(fs.readFileSync(path.join(__dirname, 'def.js'), 'utf8') + fs.readFileSync(path.join(__dirname, 'engine.js'), 'utf8') + ';global.SemiEngine=SemiEngine;global.SEMI_DEF=SEMI_DEF;');
const sr = 48000, e = new SemiEngine(sr);
e.msg({ t: 'state', params: JSON.parse(process.argv[2] || '{}'), cables: JSON.parse(process.argv[3] || '[]') });
const N = sr * 4, L = new Float32Array(N), B = 256, l = new Float32Array(B), pk = {};
for (let i = 0; i < N; i += B) { e.render(l, null, B); L.set(l, i); e.outs.forEach((n, k) => pk[n] = Math.max(pk[n] || 0, Math.abs(e.O[k]))); }
console.log(Object.entries(pk).map(([k, v]) => k + ' ' + v.toFixed(2)).join('  '));
let mx = 0, rms = 0; for (const v of L) { mx = Math.max(mx, Math.abs(v)); rms += v * v; }
console.log('speaker peak', mx.toFixed(3), 'rms', Math.sqrt(rms / N).toFixed(3), 'nan', L.some(isNaN));
const out = process.argv[4]; if (out) {
  const buf = Buffer.alloc(44 + N * 2); buf.write('RIFF', 0); buf.writeUInt32LE(36 + N * 2, 4); buf.write('WAVEfmt ', 8); buf.writeUInt32LE(16, 16); buf.writeUInt16LE(1, 20); buf.writeUInt16LE(1, 22);
  buf.writeUInt32LE(sr, 24); buf.writeUInt32LE(sr * 2, 28); buf.writeUInt16LE(2, 32); buf.writeUInt16LE(16, 34); buf.write('data', 36); buf.writeUInt32LE(N * 2, 40);
  for (let i = 0; i < N; i++) buf.writeInt16LE(Math.round(Math.max(-1, Math.min(1, L[i])) * 32000), 44 + i * 2);
  fs.writeFileSync(out, buf);
}
