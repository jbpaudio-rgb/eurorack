const fs=require('fs');
eval(fs.readFileSync('/home/claude/work/sim/engine.js','utf8')+';global.OctavioEngine=OctavioEngine;global.OCT_TYPES=OCT_TYPES;');
const D=JSON.parse(fs.readFileSync('/home/claude/work/sim/data.json'));
const sr=48000, e=new OctavioEngine(sr), params={};
D.modules.forEach(m=>m.ctl.forEach(c=>{ if(c.v!==undefined) params[m.id+'.'+c.id]=c.v; }));
const over=JSON.parse(process.argv[2]||'{}'); Object.assign(params,over);
const cables=D.patch.map(([a,b,c,d])=>[a+'.'+b,c+'.'+d]);
e.msg({t:'state',params,cables,mods:D.modules.map(m=>({id:m.id,type:m.id}))});
const pk2={};
const N=sr*4, L=new Float32Array(N), pk={};
const B=256; const l=new Float32Array(B);
for(let i=0;i<N;i+=B){ e.render(l,null,B); L.set(l,i); for(const m of e.list){ m.o.forEach((v,ix)=>{const k=m.id+'.'+OCT_TYPES[m.type].outs[ix]; pk[k]=Math.max(pk[k]||0,Math.abs(v));}); } }
console.log(JSON.stringify(Object.fromEntries(Object.entries(pk).map(([k,v])=>[k,+v.toFixed(2)]))));
let mx=0,rms=0; for(const v of L){mx=Math.max(mx,Math.abs(v)); rms+=v*v;} console.log('speaker peak',mx.toFixed(3),'rms',Math.sqrt(rms/N).toFixed(3), 'nan', L.some(isNaN));
// wav
const buf=Buffer.alloc(44+N*2); buf.write('RIFF',0); buf.writeUInt32LE(36+N*2,4); buf.write('WAVEfmt ',8); buf.writeUInt32LE(16,16); buf.writeUInt16LE(1,20); buf.writeUInt16LE(1,22); buf.writeUInt32LE(sr,24); buf.writeUInt32LE(sr*2,28); buf.writeUInt16LE(2,32); buf.writeUInt16LE(16,34); buf.write('data',36); buf.writeUInt32LE(N*2,40);
for(let i=0;i<N;i++) buf.writeInt16LE(Math.round(Math.max(-1,Math.min(1,L[i]))*32000),44+i*2);
fs.writeFileSync(process.argv[3]||'/home/claude/work/out/SIM/test.wav',buf);
