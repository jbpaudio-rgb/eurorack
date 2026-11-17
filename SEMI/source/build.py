# Assembles SEMI/index.html (one self-contained file) from def.js + engine.js + app.js + page.html.
import base64, io, json, os
from PIL import Image
D = os.path.dirname(os.path.abspath(__file__))
R = os.path.dirname(os.path.dirname(D))
rd = lambda f: open(os.path.join(D, f), encoding='utf-8').read()
DEF, ENG, APP = rd('def.js'), rd('engine.js'), rd('app.js')
WORKLET = DEF + ENG + '''
class SemiSim extends AudioWorkletProcessor {
  constructor() { super(); this.e = new SemiEngine(sampleRate); this.e.report = r => this.port.postMessage(r); this.port.onmessage = ev => this.e.msg(ev.data); }
  process(inputs, outputs) { const o = outputs[0]; this.e.render(o[0], o[1], o[0].length); return true; }
}
registerProcessor('semi-sim', SemiSim);
'''
# white logo from the black logo of the repo
im = Image.open(os.path.join(R, 'logo-ocTavio.png')).convert('RGBA')
w = Image.new('RGBA', im.size, (255, 255, 255, 0)); w.putalpha(im.getchannel('A'))
buf = io.BytesIO(); w.save(buf, 'PNG')
logo = 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()
page = rd('page.html').replace('__DEF__', DEF).replace('__ENGINE__', ENG).replace('__WORKLET__', json.dumps(WORKLET)).replace('__LOGO__', logo).replace('__APP__', APP)
open(os.path.join(os.path.dirname(D), 'index.html'), 'w', encoding='utf-8').write(page)
print(len(page) // 1024, 'KB')
