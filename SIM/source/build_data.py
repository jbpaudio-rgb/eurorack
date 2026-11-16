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
    return dict(t='knob', id=id, x=x, y=y, s=s, v=v)
def J(id, x, y, d):
    return dict(t='jack', id=id, x=x, y=y, d=d)
M = []
p = panel(W + 'vco/panel.json', W + 'out/VCO/panel/octavio-vco-panel.kicad_pcb')
M.append(dict(id='vco', name='VCO', w=40.3, **p, ctl=[
    dict(t='rotary', id='range', x=20.15, y=21.5, s=1.15, v=3, angles=[-75, -45, -15, 15, 45, 75]),
    K('fine', 10.0, 43.0, 0.8, 0.5), K('width', 30.3, 43.0, 0.8, 0.5),
    K('fm', 7.6, 60.0, 0.62, 0.0), K('pwm', 20.15, 60.0, 0.62, 0.0), K('blend', 32.7, 60.0, 0.62, 0.33),
    J('fm', 7.6, 73.5, 'in'), J('pwm', 20.15, 73.5, 'in'), J('blend', 32.7, 73.5, 'out'),
    J('voct', 7.6, 89.5, 'in'), J('sync', 7.6, 105.5, 'in'), J('sine', 20.15, 89.5, 'out'), J('tri', 32.7, 89.5, 'out'),
    J('saw', 20.15, 105.5, 'out'), J('pulse', 32.7, 105.5, 'out')]))
p = panel(W + 'mix/panel.json', W + 'out/MIX/panel/octavio-mix-panel.kicad_pcb')
M.append(dict(id='mix', name='MIX', w=40.3, **p, ctl=[
    K('l1', 10.1, 23.0, 0.8, 0.6), K('l2', 30.2, 23.0, 0.8, 0.45), K('l3', 10.1, 43.0, 0.8, 0.35), K('l4', 30.2, 43.0, 0.8, 0.0),
    K('master', 20.15, 68.0, 1.0, 0.08),
    J('in1', 7.6, 91.0, 'in'), J('in2', 20.15, 91.0, 'in'), J('in3', 7.6, 108.0, 'in'), J('in4', 20.15, 108.0, 'in'),
    J('out', 32.7, 91.0, 'out'), J('nout', 32.7, 108.0, 'out')]))
p = panel(W + 'vcf/panel.json', W + 'out/VCF/panel/octavio-vcf-panel.kicad_pcb')
M.append(dict(id='vcf', name='VCF', w=40.3, **p, ctl=[
    K('mode', 20.15, 17.0, 0.8, 0.0), K('freq', 20.15, 38.6, 1.0, 0.42), K('emph', 20.15, 61.8, 1.0, 0.55),
    K('contour', 7.6, 79.6, 0.62, 0.6), K('fcv', 20.15, 79.6, 0.62, 0.0), K('ecv', 32.7, 79.6, 0.62, 0.0),
    J('contour', 7.6, 93.0, 'in'), J('fcv', 20.15, 93.0, 'in'), J('ecv', 32.7, 93.0, 'in'),
    J('in1', 7.6, 109.0, 'in'), J('in2', 20.15, 109.0, 'in'), J('out', 32.7, 109.0, 'out')]))
p = panel(W + 'panel.json', W + 'out/octavio-902-vca/panel/octavio-902-vca-panel.kicad_pcb')
M.append(dict(id='vca', name='VCA', w=30.0, **p, ctl=[
    K('cvlevel', 15.0, 15.8, 0.8, 0.6), K('response', 15.0, 31.2, 0.8, 0.5), K('fixed', 15.0, 55.8, 1.0, 0.0),
    J('in1', 8.2, 73.4, 'in'), J('in2', 8.2, 85.6, 'in'), J('outn', 21.8, 73.4, 'out'), J('outp', 21.8, 85.6, 'out'),
    J('cv1', 8.2, 98.6, 'in'), J('cv2', 21.8, 98.6, 'in'), J('cv3', 15.0, 109.4, 'in')]))
p = panel(W + 'ad/panel.json', W + 'out/AD/panel/octavio-ad-panel.kicad_pcb')
M.append(dict(id='ad', name='AD', w=30.0, **p, ctl=[
    K('attack', 15.0, 23.0, 1.0, 0.12), K('decay', 15.0, 48.0, 1.0, 0.62),
    K('acv', 8.2, 79.1, 0.62, 0.0), K('dcv', 21.8, 79.1, 0.62, 0.0),
    dict(t='toggle', id='cycle', x=15.0, y=65.0, v=0),
    dict(t='led', id='led', x=15.0, y=109.0),
    J('acv', 8.2, 93.0, 'in'), J('dcv', 21.8, 93.0, 'in'), J('trig', 8.2, 109.0, 'in'), J('out', 21.8, 109.0, 'out')]))
# simulator utility panel (not a real module)
SW = 50.5
holes = [[7.5, 3.0, 3.2, [5.2, 3.2]], [7.5, 125.5, 3.2, [5.2, 3.2]], [7.5 + 7 * 5.08, 3.0, 3.2, [5.2, 3.2]], [7.5 + 7 * 5.08, 125.5, 3.2, [5.2, 3.2]]]
M.append(dict(id='sim', name='SIM', w=SW, holes=holes, logo=[SW / 2 - 8, 119.859, 16.0, 2.882],
    text=[['SIM', SW / 2, 3.4, 2.6], ['SCOPE', SW / 2, 9.4, 1.06], ['TEMPO', 11.0, 52.0, 1.06], ['SEQ', SW / 2, 52.0, 1.06], ['VOLUME', 39.5, 52.0, 1.06],
          ['CV', 12.6, 76.4, 0.94], ['GATE', 37.9, 76.4, 0.94], ['AUDIO', 12.6, 96.4, 0.94], ['SCOPE', 37.9, 96.4, 0.94]],
    lines=[[1.2, 70.5, SW - 1.2, 70.5, 0.3], [1.2, 90.5, SW - 1.2, 90.5, 0.3], [SW / 2, 70.5, SW / 2, 113.5, 0.3]],
    ctl=[dict(t='scope', x=4.0, y=12.0, w=SW - 8.0, h=34.0),
         K('tempo', 11.0, 60.0, 0.8, 0.45), dict(t='button', id='seq', x=SW / 2, y=60.0, v=1), K('volume', 39.5, 60.0, 0.8, 0.5),
         J('cv', 12.6, 83.0, 'out'), J('gate', 37.9, 83.0, 'out'), J('audio', 12.6, 103.0, 'in'), J('scope', 37.9, 103.0, 'in')]))
PATCH = [['sim', 'cv', 'vco', 'voct'], ['sim', 'gate', 'ad', 'trig'],
         ['vco', 'saw', 'mix', 'in1'], ['vco', 'pulse', 'mix', 'in2'], ['vco', 'blend', 'mix', 'in3'],
         ['mix', 'out', 'vcf', 'in1'], ['ad', 'out', 'vcf', 'contour'], ['ad', 'out', 'vca', 'cv1'],
         ['vcf', 'out', 'vca', 'in1'], ['vca', 'outp', 'sim', 'audio'], ['vca', 'outp', 'sim', 'scope']]
logo = 'data:image/png;base64,' + base64.b64encode(open(W + 'logo_white.png', 'rb').read()).decode()
json.dump(dict(modules=M, patch=PATCH, logo=logo), open(W + 'sim/data.json', 'w'))
print([ (m['id'], len(m['lines']), len(m['text'])) for m in M])
