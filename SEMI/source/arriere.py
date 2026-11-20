# Back panel of the SEMI (preview) : MAIN OUT L / R (6.35 mm, line level), IEC power inlet (switch + fuse), MIDI IN / MIDI OUT (5-pin DIN, 180 deg, panel mount), USB-C (USB-MIDI).
# python3 source/arriere.py -> arriere.svg (then rendered to apercu-arriere.png)
import base64, io, os
from PIL import Image
D = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(os.path.dirname(D))
W, H = 475, 110   # back wall height of the sloped case (see boitier/)
im = Image.open(os.path.join(R, 'logo-ocTavio.png')).convert('RGBA'); w = Image.new('RGBA', im.size, (255, 255, 255, 0)); w.putalpha(im.getchannel('A'))
b = io.BytesIO(); w.save(b, 'PNG'); logo = 'data:image/png;base64,' + base64.b64encode(b.getvalue()).decode()
FF = "font-family=\"'Barlow Condensed','Arial Narrow',sans-serif\" font-weight=\"700\""
F = FF + ' fill="#fff" text-anchor="middle"'
G = FF + ' fill="#9a9a9a" text-anchor="middle"'
L = FF + ' fill="#fff" text-anchor="start"'
def din(x, y, lab, sub):
    import math
    pins = ''.join(f'<circle cx="{x + 3.5 * math.cos(math.radians(a)):.2f}" cy="{y - 3.5 * math.sin(math.radians(a)):.2f}" r=".55" fill="#b8a66a"/>' for a in (180, 135, 90, 45, 0))
    return (f'<text x="{x}" y="{y - 12}" {F} font-size="3.2">{lab}</text>'
            f'<circle cx="{x}" cy="{y}" r="9.6" fill="#c9c9c3" stroke="#666" stroke-width=".3"/>'
            f'<circle cx="{x - 8.2}" cy="{y}" r=".9" fill="#555"/><circle cx="{x + 8.2}" cy="{y}" r=".9" fill="#555"/>'
            f'<circle cx="{x}" cy="{y}" r="6.8" fill="#151515" stroke="#888" stroke-width=".3"/>'
            f'<rect x="{x - .9}" y="{y + 5.2}" width="1.8" height="1.8" fill="#c9c9c3"/>' + pins +
            f'<text x="{x}" y="{y + 14}" {G} font-size="2.2">{sub}</text>')
def jack(x, y, lab, sub):
    return (f'<text x="{x}" y="{y - 8}" {F} font-size="3.2">{lab}</text>'
            f'<polygon points="{" ".join(f"{x + 4.2 * __import__("math").cos(a * 1.0472 + .5236):.2f},{y + 4.2 * __import__("math").sin(a * 1.0472 + .5236):.2f}" for a in range(6))}" fill="#c9c9c3" stroke="#666" stroke-width=".25"/>'
            f'<circle cx="{x}" cy="{y}" r="2.5" fill="#050505"/>'
            f'<text x="{x}" y="{y + 10}" {G} font-size="2.2">{sub}</text>')
x0 = 330
s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W * 4}" height="{H * 4}">',
     f'<rect width="{W}" height="{H}" rx="1.5" fill="#121212"/>',
     f'<rect width="8" height="{H}" fill="#9a9a9a"/><rect x="{W - 8}" width="8" height="{H}" fill="#9a9a9a"/>',
     '<g transform="translate(0 20)">',
     f'<image href="{logo}" x="20" y="{35 - 4}" width="44" height="{44 * 49 / 273}"/>',
     f'<text x="70" y="{35 + 3}" {L} font-size="3.4">3019 SEMI-MODULAR SYNTHESIZER</text>']
# vents
for k in range(9): s.append(f'<rect x="{196 + k * 9}" y="18" width="4" height="34" rx="2" fill="#050505"/>')
# MAIN OUT L / R (6.35 mm TRS jacks, line level, mono L -> both when R is empty on the panel)
import math
def big(x, y, lab):
    return (f'<text x="{x}" y="{y - 11}" {F} font-size="3.2">{lab}</text>'
            f'<polygon points="{" ".join(f"{x + 7 * math.cos(a * 1.0472 + .5236):.2f},{y + 7 * math.sin(a * 1.0472 + .5236):.2f}" for a in range(6))}" fill="#c9c9c3" stroke="#666" stroke-width=".3"/>'
            f'<circle cx="{x}" cy="{y}" r="3.4" fill="#050505"/>')
s += [big(152, 35, 'L'), big(174, 35, 'R'), f'<text x="163" y="16" {F} font-size="3.2">MAIN OUT</text>', f'<text x="163" y="49" {G} font-size="2.2">LIGNE · 6,35 mm</text>']
# MIDI + USB
x0 = 300
s += [din(x0, 35, 'MIDI IN', 'DIN 5 broches'), din(x0 + 30, 35, 'MIDI OUT', 'DIN 5 broches')]
x0 += 14
s += [f'<text x="{x0 + 42}" y="28" {F} font-size="3.2">USB</text>',
      f'<rect x="{x0 + 36.5}" y="33.6" width="11" height="4.8" rx="2.3" fill="#bdbdbd" stroke="#666" stroke-width=".3"/>',
      f'<rect x="{x0 + 38}" y="34.9" width="8" height="2.2" rx="1" fill="#111"/>',
      f'<text x="{x0 + 42}" y="46" {G} font-size="2.2">USB-MIDI</text>']
# IEC inlet with switch and fuse
ix = x0 + 62
s += [f'<rect x="{ix}" y="20" width="50" height="30" rx="2" fill="#1d1d1d" stroke="#777" stroke-width=".4"/>',
      f'<path d="M{ix + 5},27 h20 v12 l-3,4 h-14 l-3,-4 z" fill="#050505" stroke="#555" stroke-width=".3"/>']
for dx in (9.5, 15, 20.5): s.append(f'<rect x="{ix + dx - .9}" y="30" width="1.8" height="{6 if dx != 15 else 4}" fill="#888"/>')
s += [f'<rect x="{ix + 30}" y="25" width="14" height="9" rx="1" fill="#0a0a0a" stroke="#555" stroke-width=".3"/>',
      f'<text x="{ix + 33.5}" y="31.2" {F} font-size="3">I</text><text x="{ix + 40.5}" y="31.2" {F} font-size="3">O</text>',
      f'<rect x="{ix + 30}" y="38" width="14" height="6" rx="1" fill="#2a2a2a" stroke="#555" stroke-width=".3"/>',
      f'<text x="{ix + 37}" y="42.3" {F} font-size="2.2">FUSE</text>',
      f'<text x="{ix + 25}" y="16" {F} font-size="3.2">POWER</text>',
      f'<text x="{ix + 25}" y="56" {G} font-size="2.2">100–240 V ~ 50/60 Hz · T 1 A</text>', '</g></svg>']
open(os.path.join(os.path.dirname(D), 'arriere.svg'), 'w').write(''.join(s))
print('ok')
