import json, re, base64
W = '/home/claude/work/'
def silk_lines(fn):
    s = open(fn).read(); out = []
    for m in re.finditer(r'\(gr_line \(start ([\d.\-]+) ([\d.\-]+)\) \(end ([\d.\-]+) ([\d.\-]+)\) \(stroke \(width ([\d.]+)\)[^)]*\)\) \(layer "F.SilkS"\)', s):
        x1, y1, x2, y2, w = map(float, m.groups())
        out.append([round(x1 - 100, 3), round(y1 - 100, 3), round(x2 - 100, 3), round(y2 - 100, 3), w])
    return out
def panel(pj_path, kicad):
    pj = json.load(open(pj_path))
    lines = silk_lines(kicad)
    return dict(text=[[t, round(x, 2), round(y, 2), s] for (t, x, y, s, th) in pj['PANEL_TEXT']],
                lines=lines, holes=[[round(h[0], 2), round(h[1], 2), h[2], h[3]] for h in pj['PANEL_HOLES'] if h[3]],
                logo=[round(v, 3) for v in pj['LOGO']])
def K(id, x, y, s, v, label=''):
    return dict(t='knob', id=id, x=x, y=y, s=s, v=v, label=label)
def J(id, x, y, d):
    return dict(t='jack', id=id, x=x, y=y, d=d)
M = []
p = panel(W + 'vco/panel.json', W + 'out/VCO/panel/octavio-vco-panel.kicad_pcb')
M.append(dict(id='vco', name='VCO', w=60.6, **p, ctl=[
    dict(t='rotary', id='range', label='RANGE', x=30.3, y=21.5, s=1.15, v=3, angles=[-75, -45, -15, 15, 45, 75]),
    K('fine', 13.5, 44.5, 1.0, 0.5, 'FREQUENCY'), K('width', 47.1, 44.5, 1.0, 0.5, 'WIDTH'),
    K('fm', 10.1, 66.0, 0.8, 0.0, 'FM'), K('pwm', 30.3, 66.0, 0.8, 0.0, 'PWM'), K('blend', 50.5, 66.0, 0.8, 0.33, 'BLEND'),
    J('fm', 10.1, 81.5, 'in'), J('pwm', 30.3, 81.5, 'in'), J('blend', 50.5, 81.5, 'out'),
    J('voct', 10.1, 96.0, 'in'), J('sync', 10.1, 109.5, 'in'), J('sine', 30.3, 96.0, 'out'), J('tri', 50.5, 96.0, 'out'),
    J('saw', 30.3, 109.5, 'out'), J('pulse', 50.5, 109.5, 'out')]))
p = panel(W + 'mix/panel.json', W + 'out/MIX/panel/octavio-mix-panel.kicad_pcb')
M.append(dict(id='mix', name='MIX', w=40.3, **p, ctl=[
    K('l1', 10.1, 23.0, 0.8, 0.6, 'LEVEL 1'), K('l2', 30.2, 23.0, 0.8, 0.45, 'LEVEL 2'), K('l3', 10.1, 43.0, 0.8, 0.35, 'LEVEL 3'), K('l4', 30.2, 43.0, 0.8, 0.0, 'LEVEL 4'),
    K('master', 20.15, 68.0, 1.0, 0.08, 'MASTER GAIN'),
    J('in1', 7.6, 91.0, 'in'), J('in2', 20.15, 91.0, 'in'), J('in3', 7.6, 108.0, 'in'), J('in4', 20.15, 108.0, 'in'),
    J('out', 32.7, 91.0, 'out'), J('nout', 32.7, 108.0, 'out')]))
p = panel(W + 'vcf/panel.json', W + 'out/VCF/panel/octavio-vcf-panel.kicad_pcb')
M.append(dict(id='vcf', name='VCF', w=50.5, **p, ctl=[
    K('mode', 25.25, 17.0, 0.8, 0.0, 'LP · BP · HP'), K('freq', 25.25, 38.6, 1.0, 0.42, 'FREQUENCY'), K('emph', 25.25, 61.8, 1.0, 0.55, 'EMPHASIS'),
    K('contour', 10.1, 81.0, 0.8, 0.6, 'CONTOUR'), K('fcv', 25.25, 81.0, 0.8, 0.0, 'FREQ CV'), K('ecv', 40.4, 81.0, 0.8, 0.0, 'EMPH CV'),
    J('contour', 10.1, 94.5, 'in'), J('fcv', 25.25, 94.5, 'in'), J('ecv', 40.4, 94.5, 'in'),
    J('in1', 10.1, 109.0, 'in'), J('in2', 25.25, 109.0, 'in'), J('out', 40.4, 109.0, 'out')]))
p = panel(W + 'panel.json', W + 'out/octavio-902-vca/panel/octavio-902-vca-panel.kicad_pcb')
M.append(dict(id='vca', name='VCA', w=30.0, **p, ctl=[
    K('cvlevel', 15.0, 15.8, 0.8, 0.6, 'CV LEVEL'), K('response', 15.0, 31.2, 0.8, 0.5, 'RESPONSE'), K('fixed', 15.0, 55.8, 1.0, 0.0, 'FIXED CONTROL VOLTAGE'),
    J('in1', 8.2, 73.4, 'in'), J('in2', 8.2, 85.6, 'in'), J('outn', 21.8, 73.4, 'out'), J('outp', 21.8, 85.6, 'out'),
    J('cv1', 8.2, 98.6, 'in'), J('cv2', 21.8, 98.6, 'in'), J('cv3', 15.0, 109.4, 'in')]))
p = panel(W + 'ad/panel.json', W + 'out/AD/panel/octavio-ad-panel.kicad_pcb')
M.append(dict(id='ad', name='AD', w=30.0, **p, ctl=[
    K('attack', 15.0, 23.0, 1.0, 0.12, 'ATTACK'), K('decay', 15.0, 48.0, 1.0, 0.62, 'DECAY'),
    K('acv', 8.2, 79.1, 0.62, 0.0, 'ATTACK CV'), K('dcv', 21.8, 79.1, 0.62, 0.0, 'DECAY CV'),
    dict(t='toggle', id='cycle', label='ONE / CYCLE', x=15.0, y=65.0, v=0),
    dict(t='led', id='led', x=15.0, y=109.0),
    J('acv', 8.2, 93.0, 'in'), J('dcv', 21.8, 93.0, 'in'), J('trig', 8.2, 109.0, 'in'), J('out', 21.8, 109.0, 'out')]))
p = panel(W + 'adsr/panel.json', W + 'out/ADSR/panel/octavio-adsr-panel.kicad_pcb')
M.append(dict(id='adsr', name='ADSR', w=40.3, **p, ctl=[
    K('attack', 20.15, 19.4, 1.0, 0.12, 'ATTACK'), K('decay', 20.15, 39.2, 1.0, 0.5, 'DECAY'),
    K('sustain', 20.15, 59.0, 1.0, 0.6, 'SUSTAIN'), K('release', 20.15, 78.8, 1.0, 0.45, 'RELEASE'),
    dict(t='led', id='led', x=10.1, y=96.5),
    J('gate', 30.2, 96.5, 'in'), J('out', 10.1, 109.5, 'out'), J('nout', 30.2, 109.5, 'out')]))
p = panel(W + 'cx/panel.json', W + 'out/COMPLEX/panel/octavio-complex-panel.kicad_pcb')
M.append(dict(id='cx', name='COMPLEX', w=152.1, **p, ctl=[
    K('mfreq', 23.1, 27.0, 1.0, 0.35, 'MOD FREQUENCY'), K('index', 57.0, 27.0, 1.0, 0.65, 'MOD INDEX'), K('pfreq', 91.0, 27.0, 1.0, 0.45, 'FREQUENCY'), K('timbre', 132.0, 27.0, 1.0, 0.3, 'TIMBRE'),
    dict(t='toggle', id='range', label='RANGE', x=8.5, y=50.0, v=0, vert=1, opts=['AUDIO', 'LFO']),
    dict(t='toggle', id='mwave', label='WAVE', x=23.1, y=50.0, v=0, vert=1, opts=['TRIANGLE', 'SQUARE', 'SAW']),
    K('mcv', 37.7, 50.0, 0.8, 0.5, 'MOD CV'), K('mfine', 8.5, 69.0, 0.8, 0.5, 'MOD FINE'), K('mfm', 37.7, 69.0, 0.8, 0.0, 'MOD FM'),
    dict(t='toggle', id='ampl', label='AMPL', x=60.0, y=59.0, v=1, opts=['ON', 'OFF']),
    dict(t='toggle', id='pitch', label='PITCH', x=60.0, y=84.0, v=0, opts=['ON', 'OFF']),
    dict(t='toggle', id='timbresw', label='TIMBRE MOD', x=60.0, y=71.5, v=1, opts=['ON', 'OFF']),
    K('plock', 57.0, 45.0, 0.8, 0.0, 'PHASE LOCK'),
    K('pfine', 91.0, 48.0, 0.8, 0.5, 'FINE'), K('pcv', 81.0, 67.0, 0.8, 0.5, 'CV'), K('pfm', 101.0, 67.0, 0.8, 0.0, 'FM'),
    K('sym', 121.0, 67.0, 0.8, 0.5, 'SYMMETRY'), K('tcv', 132.0, 48.0, 0.8, 0.0, 'TIMBRE CV'), K('order', 143.0, 67.0, 0.8, 0.0, 'ORDER'),
    J('mvoct', 8.5, 90.0, 'in'), J('mcv', 23.1, 90.0, 'in'), J('mfm', 37.7, 90.0, 'in'), J('tri', 15.8, 106.0, 'out'), J('signal', 30.4, 106.0, 'out'),
    J('indexcv', 51.0, 106.0, 'in'), J('plock', 63.0, 106.0, 'in'),
    J('pvoct', 76.0, 90.0, 'in'), J('pcv', 91.0, 90.0, 'in'), J('pfm', 106.0, 90.0, 'in'), J('sine', 83.0, 106.0, 'out'), J('square', 99.0, 106.0, 'out'),
    J('symcv', 121.0, 90.0, 'in'), J('timbrecv', 143.0, 90.0, 'in'), J('ordercv', 121.0, 106.0, 'in'), J('final', 143.0, 106.0, 'out')]))
p = panel(W + 'stg/panel.json', W + 'out/STAGES/panel/octavio-stages-panel.kicad_pcb')
SXs = [53.0 + 12.6 * i for i in range(8)]
ctl = [K('time', 23.0, 27.0, 1.0, 0.45, 'TIME'), K('tcvatt', 12.0, 49.0, 0.8, 0.5, 'TIME CV'), K('analogk', 34.0, 49.0, 0.8, 0.5, 'ANALOG'),
       dict(t='mbutton', id='startbtn', label='START', x=12.0, y=64.0, v=0), dict(t='cbutton', id='mode', label='MODE', x=34.0, y=64.0, v=0, n=3),
       dict(t='pled', id='mode', val=0, x=26.0, y=69.5, c='amber'), dict(t='pled', id='mode', val=1, x=32.5, y=69.5, c='amber'), dict(t='pled', id='mode', val=2, x=39.0, y=69.5, c='amber'),
       dict(t='param', id='end', v=7, label='LAST STAGE')]
A0 = [0.0, 0.25, 0.58, 0.42, 0.0, 0.83, 0.58, 0.25]
B0 = [0.6, 0.3, 0.45, 0.2, 0.7, 0.35, 0.5, 0.25]
for i, x in enumerate(SXs):
    n = i + 1
    ctl += [K(f'a{n}', x, 18.5, 0.8, A0[i], f'A {n}'), K(f'b{n}', x, 33.5, 0.8, B0[i], f'B {n}'), K(f't{n}', x, 48.5, 0.8, 0.5, f'TIME {n}'),
            dict(t='sbutton', id=f'sl{n}', idx=i, label=f'SLIDE {n}', x=x, y=61.5, v=1 if i in (3, 6) else 0),
            dict(t='pled', id=f'sl{n}', val=1, x=x, y=68.5, c='amber'), dict(t='sled', idx=i, x=x, y=75.5),
            J(f'sel{n}', x, 96.5, 'in'), J(f'g{n}', x, 109.5, 'out')]
ctl += [J('clock', 9.0, 82.5, 'in'), J('start', 23.0, 82.5, 'in'), J('strobe', 37.0, 82.5, 'in'), J('tcv', 9.0, 96.5, 'in'), J('analog', 23.0, 96.5, 'in'),
        J('end', 37.0, 96.5, 'out'), J('cva', 9.0, 109.5, 'out'), J('cvb', 23.0, 109.5, 'out'), J('gate', 37.0, 109.5, 'out')]
M.append(dict(id='stg', name='STAGES', w=152.1, **p, ctl=ctl))
p = panel(W + 'lfo/panel.json', W + 'out/QUADLFO/panel/octavio-quadlfo-panel.kicad_pcb')
LX = [9.33 + 14.0 * i for i in range(4)]
F0 = [0.3, 0.45, 0.6, 0.2]; W0 = [0.0, 0.5, 0.9, 0.0]
ctl = []
for i, x in enumerate(LX):
    n = i + 1
    ctl += [K(f'f{n}', x, 22.5, 0.8, F0[i], f'FREQ {n}'), K(f'w{n}', x, 42.5, 0.8, W0[i], f'WAVE {n}'),
            dict(t='led', id=f'l{n}', x=x, y=54.5),
            dict(t='toggle', id=f's{n}', label=f'CLOCKED / FREE {n}', x=x, y=67.5, v=1, vert=1, opts=['CLOCKED', 'FREE']),
            J(f'o{n}', x, 90.0, 'out')]
ctl += [J('clock', 16.33, 106.0, 'in'), J('reset', 44.33, 106.0, 'in'), dict(t='led', id='lc', x=30.33, y=106.0)]
M.append(dict(id='lfo', name='LFOs', w=60.66, **p, ctl=ctl))
p = panel(W + 'nt/panel.json', W + 'out/NOISETOOLS/panel/octavio-noisetools-panel.kicad_pcb')
ctl = [K('rate', 12.6, 24.0, 1.0, 0.55, 'PULSE RATE'), K('slew', 37.9, 24.0, 1.0, 0.3, 'SLEW RATE'),
       dict(t='toggle', id='mode', label='CLK / RND', x=12.6, y=45.0, v=0, vert=1, opts=['CLK', 'RND']),
       dict(t='toggle', id='shmode', label='S&H / T&H', x=37.9, y=45.0, v=0, vert=1, opts=['S&H', 'T&H']),
       dict(t='led', id='lp', x=9.0, y=57.0), dict(t='led', id='ls', x=25.25, y=57.0), dict(t='led', id='ll', x=41.5, y=57.0),
       J('pulse', 9.0, 76.0, 'out'), J('white', 25.25, 76.0, 'out'), J('pink', 41.5, 76.0, 'out'),
       J('shin', 9.0, 93.0, 'in'), J('trig', 25.25, 93.0, 'in'), J('sh', 41.5, 93.0, 'out'),
       J('slin', 9.0, 109.5, 'in'), J('slew', 41.5, 109.5, 'out')]
M.append(dict(id='nt', name='NOISE TOOLS', w=50.5, **p, ctl=ctl))
p = panel(W + 'att/panel.json', W + 'out/ATTINV/panel/octavio-attinv-panel.kicad_pcb')
ROWa = [14.5, 30.3, 46.1, 61.9]; JYa = [76.5, 87.5, 98.5, 109.5]
ctl = []
for i in range(4):
    n = i + 1
    ctl += [K(f'a{n}', 12.0, ROWa[i], 0.8, 0.75, f'NIVEAU {n}'), dict(t='led', id=f'l{n}', x=20.6, y=ROWa[i]),
            dict(t='toggle', id=f's{n}', label=f'INV / ATT {n}', x=30.4, y=ROWa[i], v=0, opts=['INV', 'ATT']),
            J(f'in{n}', 10.1, JYa[i], 'in'), J(f'o{n}', 30.2, JYa[i], 'out')]
M.append(dict(id='att', name='ATT / INV', w=40.3, **p, ctl=ctl))
p = panel(W + 'mult/panel.json', W + 'out/MULT/panel/octavio-mult-panel.kicad_pcb')
MY = [15.5 + i * 13.29 for i in range(8)]
ctl = [J('a', 10.01, MY[0], 'in'), J('a2', 10.01, MY[1], 'out'), J('a3', 10.01, MY[2], 'out'), J('a4', 10.01, MY[3], 'out'),
       J('b', 10.01, MY[4], 'in'), J('b2', 10.01, MY[5], 'out'), J('b3', 10.01, MY[6], 'out'), J('b4', 10.01, MY[7], 'out')]
M.append(dict(id='mult', name='MULT', w=20.02, **p, ctl=ctl))
# simulator utility panel (not a real module)
SW = 40.3   # 8 HP
holes = [[7.5, 3.0, 3.2, [5.2, 3.2]], [7.5, 125.5, 3.2, [5.2, 3.2]], [7.5 + 5 * 5.08, 3.0, 3.2, [5.2, 3.2]], [7.5 + 5 * 5.08, 125.5, 3.2, [5.2, 3.2]]]
M.append(dict(id='sim', name='SIM', w=SW, holes=holes, logo=[SW / 2 - 8, 119.859, 16.0, 2.882],
    text=[['SIM', SW / 2, 3.4, 2.6], ['SCOPE', SW / 2, 9.4, 1.06], ['TEMPO', 8.6, 52.0, 0.94], ['SEQ', SW / 2, 52.0, 0.94], ['VOLUME', 31.7, 52.0, 0.94],
          ['CV', 10.1, 76.4, 0.94], ['GATE', 30.2, 76.4, 0.94], ['AUDIO', 10.1, 96.4, 0.94], ['SCOPE', 30.2, 96.4, 0.94]],
    lines=[[1.2, 70.5, SW - 1.2, 70.5, 0.3], [1.2, 90.5, SW - 1.2, 90.5, 0.3], [SW / 2, 70.5, SW / 2, 113.5, 0.3]],
    ctl=[dict(t='scope', x=3.0, y=12.0, w=SW - 6.0, h=34.0),
         K('tempo', 8.6, 60.0, 0.8, 0.45, 'TEMPO'), dict(t='button', id='seq', label='SEQ', x=SW / 2, y=60.0, v=1), K('volume', 31.7, 60.0, 0.8, 0.5, 'VOLUME'),
         J('cv', 10.1, 83.0, 'out'), J('gate', 30.2, 83.0, 'out'), J('audio', 10.1, 103.0, 'in'), J('scope', 30.2, 103.0, 'in')]))
# ---- default rack : two rows of 104 HP, every module, 3 VCO, 2 AD, 1 ADSR
LAYOUT = [['vco', 'vco2', 'vco3', 'mix', 'vcf', 'vca', 'ad', 'adsr', 'att', 'mult', 'sim', 'mix2'],
          ['cx', 'stg', 'lfo', 'nt', 'vcf2', 'vca2', 'ad2']]
PATCH = [
    # voice 1 : keyboard / SIM sequence -> 3 VCO (8', detuned 8', sub 16') -> MIX -> VCF -> VCA (ADSR)
    ['sim', 'cv', 'vco', 'voct'], ['sim', 'cv', 'vco2', 'voct'], ['sim', 'cv', 'vco3', 'voct'],
    ['vco', 'saw', 'mix', 'in1'], ['vco2', 'pulse', 'mix', 'in2'], ['vco3', 'sine', 'mix', 'in3'],
    ['mix', 'out', 'vcf', 'in1'], ['sim', 'gate', 'ad', 'trig'], ['ad', 'out', 'vcf', 'contour'],
    ['vcf', 'out', 'vca', 'in1'], ['sim', 'gate', 'adsr', 'gate'], ['adsr', 'out', 'vca', 'cv1'],
    # voice 2 : STAGES -> COMPLEX -> VCF 2 -> VCA 2, AD 2 shared through the MULT
    ['stg', 'cva', 'cx', 'pvoct'], ['stg', 'cvb', 'cx', 'timbrecv'], ['cx', 'final', 'vcf2', 'in1'],
    ['stg', 'gate', 'ad2', 'trig'], ['ad2', 'out', 'mult', 'a'], ['mult', 'a2', 'vca2', 'cv1'], ['mult', 'a3', 'vcf2', 'contour'],
    ['vcf2', 'out', 'vca2', 'in1'],
    # modulation : LFOs clocked by STAGES, NOISE TOOLS random, ATT / INV scaling
    ['stg', 'gate', 'lfo', 'clock'], ['lfo', 'o1', 'cx', 'symcv'], ['lfo', 'o2', 'vcf', 'fcv'],
    ['lfo', 'o4', 'mult', 'b'], ['mult', 'b2', 'vco', 'pwm'], ['mult', 'b3', 'vco2', 'pwm'],
    ['lfo', 'o3', 'att', 'in2'], ['att', 'o2', 'vcf', 'ecv'],
    ['nt', 'slew', 'vcf2', 'fcv'], ['nt', 'sh', 'att', 'in1'], ['att', 'o1', 'cx', 'ordercv'],
    # master : MIX 2 -> speaker + scope
    ['vca', 'outp', 'mix2', 'in1'], ['vca2', 'outp', 'mix2', 'in2'], ['nt', 'pink', 'mix2', 'in3'],
    ['mix2', 'out', 'sim', 'audio'], ['mix2', 'out', 'sim', 'scope']]
PARAMS = {'vco.range': 3, 'vco2.range': 3, 'vco2.fine': 0.53, 'vco2.width': 0.3, 'vco3.range': 2, 'vco.pwm': 0.3, 'vco2.pwm': 0.25,
          'mix.l1': 0.55, 'mix.l2': 0.45, 'mix.l3': 0.6, 'mix.l4': 0.0,
          'vcf.freq': 0.38, 'vcf.emph': 0.5, 'vcf.contour': 0.55, 'vcf.fcv': 0.25, 'vcf.ecv': 0.2,
          'vcf2.freq': 0.45, 'vcf2.emph': 0.35, 'vcf2.contour': 0.5, 'vcf2.fcv': 0.3, 'vcf2.mode': 0.25,
          'vca2.cvlevel': 0.7, 'ad2.attack': 0.05, 'ad2.decay': 0.45,
          'mix2.l1': 0.6, 'mix2.l2': 0.5, 'mix2.l3': 0.06, 'mix2.l4': 0.0,
          'lfo.s1': 0, 'lfo.s2': 0, 'lfo.s3': 0, 'lfo.s4': 0, 'lfo.f1': 0.5, 'lfo.f2': 0.2, 'lfo.f3': 0.7, 'lfo.f4': 0.1,
          'lfo.w1': 0.0, 'lfo.w2': 0.25, 'lfo.w3': 0.5, 'lfo.w4': 0.0,
          'att.s1': 1, 'att.a1': 0.8, 'att.s2': 0, 'att.a2': 0.65, 'nt.rate': 0.45, 'nt.slew': 0.55}
logo = 'data:image/png;base64,' + base64.b64encode(open(W + 'logo_white.png', 'rb').read()).decode()
json.dump(dict(modules=M, patch=PATCH, layout=LAYOUT, params=PARAMS, logo=logo), open(W + 'sim/data.json', 'w'))
print([ (m['id'], len(m['lines']), len(m['text'])) for m in M])
