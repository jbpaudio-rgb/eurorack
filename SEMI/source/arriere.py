# Back panel of the SEMI (preview) : IEC power inlet (switch + fuse), MIDI IN / MIDI OUT (3.5 mm TRS type A), USB-C (USB-MIDI).
# python3 source/arriere.py -> arriere.svg (then rendered to apercu-arriere.png)
import base64, io, os
from PIL import Image
D = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(os.path.dirname(D))
W, H = 475, 70
im = Image.open(os.path.join(R, 'logo-ocTavio.png')).convert('RGBA'); w = Image.new('RGBA', im.size, (255, 255, 255, 0)); w.putalpha(im.getchannel('A'))
b = io.BytesIO(); w.save(b, 'PNG'); logo = 'data:image/png;base64,' + base64.b64encode(b.getvalue()).decode()
FF = "font-family=\"'Barlow Condensed','Arial Narrow',sans-serif\" font-weight=\"700\""
F = FF + ' fill="#fff" text-anchor="middle"'
G = FF + ' fill="#9a9a9a" text-anchor="middle"'
L = FF + ' fill="#fff" text-anchor="start"'
def jack(x, y, lab, sub):
    return (f'<text x="{x}" y="{y - 8}" {F} font-size="3.2">{lab}</text>'
            f'<polygon points="{" ".join(f"{x + 4.2 * __import__("math").cos(a * 1.0472 + .5236):.2f},{y + 4.2 * __import__("math").sin(a * 1.0472 + .5236):.2f}" for a in range(6))}" fill="#c9c9c3" stroke="#666" stroke-width=".25"/>'
            f'<circle cx="{x}" cy="{y}" r="2.5" fill="#050505"/>'
            f'<text x="{x}" y="{y + 10}" {G} font-size="2.2">{sub}</text>')
x0 = 330
s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W * 4}" height="{H * 4}">',
     f'<rect width="{W}" height="{H}" rx="1.5" fill="#121212"/>',
     f'<rect width="8" height="{H}" fill="#9a9a9a"/><rect x="{W - 8}" width="8" height="{H}" fill="#9a9a9a"/>',
     f'<image href="{logo}" x="20" y="{H / 2 - 4}" width="44" height="{44 * 49 / 273}"/>',
     f'<text x="70" y="{H / 2 + 3}" {L} font-size="3.4">SEMI-MODULAR SYNTHESIZER</text>']
# vents
for k in range(14): s.append(f'<rect x="{150 + k * 9}" y="18" width="4" height="34" rx="2" fill="#050505"/>')
# MIDI + USB
s += [jack(x0, 36, 'MIDI IN', 'TRS type A'), jack(x0 + 20, 36, 'MIDI OUT', 'TRS type A')]
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
      f'<text x="{ix + 25}" y="56" {G} font-size="2.2">100–240 V ~ 50/60 Hz · T 1 A</text>', '</svg>']
open(os.path.join(os.path.dirname(D), 'arriere.svg'), 'w').write(''.join(s))
print('ok')
