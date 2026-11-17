"""Checks that every schematic pin label matches the net of the same pad on the board.  schpcbcheck.py board.kicad_pcb sheet.kicad_sch"""
import re, sys, os
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here); sys.path.insert(0, os.path.join(here, 'spice'))
import schedit, kicad2spice
pcb, sch = sys.argv[1], sys.argv[2]
parts = kicad2spice.load(pcb, sch); s = open(sch).read()
labels = {}
for m in re.finditer(r'\(label "([^"]+)" \(at ([\d.-]+) ([\d.-]+)', s): labels[(round(float(m.group(2)), 2), round(float(m.group(3)), 2))] = m.group(1)
bad = n = 0; libcache = {}
for m in re.finditer(r'\(symbol \(lib_id "([^"]+)"\) \(at ([\d.-]+) ([\d.-]+) 0\)[^\n]*\n\s*\(property "Reference" "([^"]+)"', s):
    lib, X, Y, ref = m.group(1), float(m.group(2)), float(m.group(3)), m.group(4)
    if ref not in parts: print('only in schematic:', ref); bad += 1; continue
    pins = libcache.setdefault(lib, schedit.lib_pins(s, lib))
    for pin, (px, py) in pins.items():
        lab = labels.get((round(X + px, 2), round(Y - py, 2)))
        net = parts[ref]['pads'].get(pin)
        n += 1
        if lab is not None and net is not None and lab != net: print('MISMATCH', ref, pin, 'sch', lab, 'pcb', net); bad += 1
refs = set(re.findall(r'\(property "Reference" "([^"]+)"', s))
for r in parts:
    if r not in refs: print('only on board:', r); bad += 1
print(n, 'pins checked,', bad, 'problems')
