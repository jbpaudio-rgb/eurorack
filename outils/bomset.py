"""Move one designator of a JLC BOM to another value line (created if needed) :  bomset.py bom.csv REF "NEW COMMENT" [footprint]"""
import csv, sys, re
def bom_set(path, ref, comment, fp=None):
    rows = list(csv.reader(open(path))); head, body = rows[0], rows[1:]
    src = None
    for r in body:
        d = r[1].split(',')
        if ref in d: src = r; d.remove(ref); r[1] = ','.join(d)
    body = [r for r in body if r[1]]
    fp = fp or (src[2] if src else '')
    key = lambda s: [int(x) if x.isdigit() else x for x in re.split(r'(\d+)', s)]
    for r in body:
        if r[0] == comment and r[2] == fp: r[1] = ','.join(sorted(r[1].split(',') + [ref], key=key)); break
    else:
        new = list(src) if src else [comment, '', fp, '', 'SMT bottom - laisser JLC choisir (Basic de preference)']
        new[0], new[1] = comment, ref
        if len(new) > 3: new[3] = ''
        body.append(new)
    with open(path, 'w', newline='') as fh: w = csv.writer(fh); w.writerow(head); w.writerows(body)
if __name__ == '__main__': bom_set(*sys.argv[1:])
