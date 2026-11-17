"""JLCPCB CPL + BOM straight from a .kicad_pcb (back-side SMD parts), keeping the comments / notes of an existing BOM.
   jlcfrompcb.py board.kicad_pcb old_bom.csv out_bom.csv out_cpl.csv"""
import re, sys, csv
pcb, old_bom, out_bom, out_cpl = sys.argv[1:5]
t = open(pcb).read()
parts = []
for m in re.finditer(r'\(footprint "([^"]+)" \(layer "([^"]+)"\) \(uuid "[^"]+"\) \(at ([\d.-]+) ([\d.-]+)(?: ([\d.-]+))?\)', t):
    blk = t[m.start():t.find('\n  (footprint', m.end()) if t.find('\n  (footprint', m.end()) > 0 else len(t)]
    if '(attr smd)' not in blk or m.group(2) != 'B.Cu': continue
    ref = re.search(r'"Reference" "([^"]+)"', blk).group(1); val = re.search(r'"Value" "([^"]+)"', blk).group(1)
    parts.append(dict(ref=ref, val=val, fp=m.group(1).split(':')[1], x=float(m.group(3)), y=float(m.group(4)), r=float(m.group(5) or 0)))
key = lambda s: [int(x) if x.isdigit() else x for x in re.split(r'(\d+)', s)]
with open(out_cpl, 'w', newline='') as fh:
    w = csv.writer(fh); w.writerow(['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation'])
    for p in sorted(parts, key=lambda p: key(p['ref'])):
        w.writerow([p['ref'], '%.3fmm' % (p['x'] - 100), '%.3fmm' % (228.5 - p['y']), 'Bottom', int(round(p['r'])) % 360])
rows = list(csv.reader(open(old_bom)))
head, old = rows[0], rows[1:]
by_ref = {}
for r in old:
    for d in r[1].split(','): by_ref[d] = r
val = {p['ref']: p for p in parts}
def same_val(a, b):
    a, b = a.split()[0].split(',')[0], b.split()[0].split(',')[0]
    return a == b or (len(b) > 3 and a.startswith(b)) or (len(a) > 3 and b.startswith(a))
out, left = [], []
for r in old:                                    # keep every old line, minus parts whose value changed or that left the board
    keep = [d for d in r[1].split(',') if d in val and same_val(r[0], val[d]['val'])]
    if keep: out.append([r[0], keep] + r[2:])
done = {d for r in out for d in r[1]}
for p in parts:
    if p['ref'] in done: continue
    same = [r for r in out if same_val(r[0], p['val']) and r[2] == p['fp']]
    if same: same[0][1].append(p['ref']); continue
    kind = p['fp'][0]
    com = p['val'] + (' 1% 0603' if kind == 'R' else ' C0G 0603' if kind == 'C' else '')
    out.append([com, [p['ref']], p['fp'], '', 'SMT bottom - laisser JLC choisir (Basic de preference)'])
with open(out_bom, 'w', newline='') as fh:
    w = csv.writer(fh); w.writerow(head)
    for r in out: w.writerow([r[0], ','.join(sorted(r[1], key=key))] + r[2:])
print(len(parts), 'parts,', len(out), 'BOM lines,', sum(len(r[1]) for r in out), 'placed')
