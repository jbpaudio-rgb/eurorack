"""Remove the segments of some nets inside a box (to free a trapped pad), e.g. ripup.py board 'FB1' x0 y0 x1 y1"""
import sys, re
pcb, nets, x0, y0, x1, y1 = sys.argv[1], sys.argv[2].split(","), *map(float, sys.argv[3:7])
txt = open(pcb).read()
num = {n: i for i, n in re.findall(r'^\s*\(net (\d+) "([^"]*)"\)', txt, re.M)}
ids = {num[n] for n in nets}
out, k = [], 0
for line in txt.split("\n"):
    m = re.match(r'\s*\(segment \(start ([\d.-]+) ([\d.-]+)\) \(end ([\d.-]+) ([\d.-]+)\).*\(net (\d+)\)', line)
    if m and m.group(5) in ids:
        a, b, c, d = map(float, m.groups()[:4])
        if (x0 <= a <= x1 and y0 <= b <= y1) or (x0 <= c <= x1 and y0 <= d <= y1):
            k += 1; continue
    out.append(line)
open(pcb, "w").write("\n".join(out)); print("removed", k)
