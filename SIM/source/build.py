import json
W='/home/claude/work/'
eng=open(W+'sim/engine.js').read()
data=open(W+'sim/data.json').read()
app=open(W+'sim/app.js').read().replace('__DATA__',data)
page=open(W+'sim/page.html').read().replace('__ENGINE__',eng).replace('__APP__',app)
open(W+'out/SIM/index.html','w').write(page)
open(W+'out/SIM/dsp.js','w').write(eng+'''
class OctavioSim extends AudioWorkletProcessor {
  constructor() { super(); this.e = new OctavioEngine(sampleRate); this.e.report = r => this.port.postMessage(r); this.port.onmessage = ev => this.e.msg(ev.data); }
  process(inputs, outputs) { const o = outputs[0]; this.e.render(o[0], o[1], o[0].length); return true; }
}
registerProcessor('octavio-sim', OctavioSim);
''')
print(len(page)//1024,'KB')
