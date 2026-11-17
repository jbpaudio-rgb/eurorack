"""Small edits on a routed .kicad_pcb (no KiCad needed) : change a pad's net (and rip up the track that led to it),
add a footprint cloned from an existing one, change a value, find free room on the back side.
Used to apply schematic corrections to a board that is already routed ; finish.py then routes what is left open."""
import re, uuid, math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gerber import load, on

def block(s, i):
    d = 0
    for k in range(i, len(s)):
        if s[k] == '(': d += 1
        elif s[k] == ')':
            d -= 1
            if d == 0: return i, k + 1

def fp_span(txt, ref):
    i = txt.find('(property "Reference" "%s"' % ref)
    if i < 0: raise KeyError(ref)
    j = txt.rfind('(footprint', 0, i)
    return block(txt, j)

def net_id(txt, name):
    m = re.search(r'^\s*\(net (\d+) "%s"\)' % re.escape(name), txt, re.M)
    if m: return txt, int(m.group(1))
    ids = [int(x) for x in re.findall(r'^\s*\(net (\d+) "', txt, re.M)]
    n = max(ids) + 1
    last = list(re.finditer(r'^\s*\(net \d+ "[^"]*"\)\n', txt, re.M))[-1]
    txt = txt[:last.end()] + '  (net %d "%s")\n' % (n, name) + txt[last.end():]
    return txt, n

def pad_xy(txt, ref, pad):
    a, b = fp_span(txt, ref); f = txt[a:b]
    at = re.search(r'\(at ([\d.-]+) ([\d.-]+)(?: ([\d.-]+))?\)', f)
    fx, fy, fr = float(at.group(1)), float(at.group(2)), float(at.group(3) or 0)
    p = re.search(r'\(pad "%s" [^\n]*?\(at ([\d.-]+) ([\d.-]+)' % re.escape(pad), f)
    px, py = float(p.group(1)), float(p.group(2)); t = math.radians(fr)
    return fx + px * math.cos(t) + py * math.sin(t), fy - px * math.sin(t) + py * math.cos(t)

def ripup_from(txt, x, y, net_num, keep_pads):
    """Remove the track branch of net `net_num` that starts at (x, y), up to the first junction / other pad."""
    segs = [(m.start(), m.end(), float(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4)), m.group(5))
            for m in re.finditer(r'  \(segment \(start ([\d.-]+) ([\d.-]+)\) \(end ([\d.-]+) ([\d.-]+)\) \(width [\d.]+\) \(layer "([^"]+)"\) \(net %d\)[^\n]*\n' % net_num, txt)]
    vias = [(float(m.group(1)), float(m.group(2))) for m in re.finditer(r'\(via \(at ([\d.-]+) ([\d.-]+)\)[^\n]*\(net %d\)' % net_num, txt)]
    near = lambda a, b, c, d, tol=0.3: abs(a - c) < tol and abs(b - d) < tol
    gone, pts = set(), [(x, y, 0.8)]
    while pts:
        cx, cy, tol = pts.pop()
        touching = [k for k, s in enumerate(segs) if k not in gone and (near(s[2], s[3], cx, cy, tol) or near(s[4], s[5], cx, cy, tol))]
        for k in touching:
            s = segs[k]; gone.add(k)
            ox, oy = (s[4], s[5]) if near(s[2], s[3], cx, cy, tol) else (s[2], s[3])
            if any(near(ox, oy, px, py, 0.5) for px, py in keep_pads): continue      # reached another pad : stop
            others = [j for j, t in enumerate(segs) if j not in gone and (near(t[2], t[3], ox, oy, 0.01) or near(t[4], t[5], ox, oy, 0.01))]
            if len(others) == 1 and not any(near(ox, oy, vx, vy, 0.01) for vx, vy in vias):
                pts.append((ox, oy, 0.01))                                            # plain bend : keep following
    for k in sorted(gone, key=lambda k: -segs[k][0]):
        txt = txt[:segs[k][0]] + txt[segs[k][1]:]
    return txt, len(gone)

def set_pad_net(txt, ref, pad, name):
    a, b = fp_span(txt, ref); f = txt[a:b]
    m = re.search(r'(\(pad "%s" [^\n]*?)\(net (\d+) "([^"]*)"\)' % re.escape(pad), f)
    old_num, old = int(m.group(2)), m.group(3)
    x, y = pad_xy(txt, ref, pad)
    others = [(p["x"], p["y"]) for p in load_pads(txt) if p["net"] == old and not (abs(p["x"] - x) < 0.01 and abs(p["y"] - y) < 0.01)]
    txt, n = ripup_from(txt, x, y, old_num, others)
    txt, nid = net_id(txt, name)
    a, b = fp_span(txt, ref); f = txt[a:b]
    f = re.sub(r'(\(pad "%s" [^\n]*?)\(net \d+ "[^"]*"\)' % re.escape(pad), lambda q: q.group(1) + '(net %d "%s")' % (nid, name), f, count=1)
    return txt[:a] + f + txt[b:], n

def load_pads(txt):
    tmp = '/tmp/_pcbedit.kicad_pcb'; open(tmp, 'w').write(txt); return load(tmp)["pads"]

def set_value(txt, ref, value):
    a, b = fp_span(txt, ref); f = txt[a:b]
    f = re.sub(r'\(property "Value" "[^"]*"', '(property "Value" "%s"' % value, f, count=1)
    return txt[:a] + f + txt[b:]

def add_fp(txt, template, ref, value, x, y, rot, pads):
    a, b = fp_span(txt, template); f = txt[a:b]
    f = re.sub(r'\(uuid "[^"]+"\)', lambda q: '(uuid "%s")' % uuid.uuid4(), f)
    f = re.sub(r'\(property "Reference" "[^"]*"', '(property "Reference" "%s"' % ref, f, count=1)
    f = re.sub(r'\(property "Value" "[^"]*"', '(property "Value" "%s"' % value, f, count=1)
    f = re.sub(r'^(\(footprint "[^"]+" \(layer "[^"]+"\) \(uuid "[^"]+"\) )\(at [^)]*\)', lambda q: q.group(1) + '(at %g %g %g)' % (x, y, rot), f, count=1)
    # pad local angles follow the footprint rotation
    f = re.sub(r'(\(pad "[^"]+" \w+ \w+ \(at [\d.-]+ [\d.-]+)(?: [\d.-]+)?\)', lambda q: q.group(1) + (' %g)' % rot if rot else ')'), f)
    for num, name in pads.items():
        txt, nid = net_id(txt, name)
        f = re.sub(r'(\(pad "%s" [^\n]*?)\(net \d+ "[^"]*"\)' % re.escape(num), lambda q: q.group(1) + '(net %d "%s")' % (nid, name), f, count=1)
    k = txt.find('\n  (segment')
    if k < 0: k = txt.rstrip().rfind(')')
    return txt[:k] + '\n  ' + f + txt[k:]

def free_spot(txt, w, h, near, side="B", keep=0.35, rmax=14, avoid=()):
    """Closest spot to `near` where a w x h body (plus `keep`) touches no pad, track or via on the back copper."""
    tmp = '/tmp/_pcbedit.kicad_pcb'; open(tmp, 'w').write(txt); M = load(tmp)
    L = side + ".Cu"
    boxes = []
    for p in M["pads"]:
        if on(p["layers"], L) or p["drill"]:
            boxes.append((p["x"] - p["w"] / 2, p["y"] - p["h"] / 2, p["x"] + p["w"] / 2, p["y"] + p["h"] / 2))
    for g in M["gfx"]:
        if g[0] == "line" and g[1] in (side + ".Fab", side + ".CrtYd"):
            boxes.append((min(g[2], g[4]), min(g[3], g[5]), max(g[2], g[4]), max(g[3], g[5])))
    for s in M["segs"]:
        if s["layer"] == L:
            r = s["w"] / 2
            n = max(1, int(math.hypot(s["x2"] - s["x1"], s["y2"] - s["y1"]) / 0.3))
            for k in range(n + 1):
                cx, cy = s["x1"] + (s["x2"] - s["x1"]) * k / n, s["y1"] + (s["y2"] - s["y1"]) * k / n
                boxes.append((cx - r, cy - r, cx + r, cy + r))
    for v in M["vias"]:
        r = v["d"] / 2; boxes.append((v["x"] - r, v["y"] - r, v["x"] + r, v["y"] + r))
    boxes += list(avoid)
    x0, y0, x1, y1 = M["edges"][0]
    best = None
    for i in range(-int(rmax / 0.25), int(rmax / 0.25) + 1):
        for j in range(-int(rmax / 0.25), int(rmax / 0.25) + 1):
            cx, cy = near[0] + i * 0.25, near[1] + j * 0.25
            d = math.hypot(cx - near[0], cy - near[1])
            if best and d >= best[0]: continue
            bx0, by0, bx1, by1 = cx - w / 2 - keep, cy - h / 2 - keep, cx + w / 2 + keep, cy + h / 2 + keep
            if bx0 < x0 + 1 or by0 < y0 + 1 or bx1 > x1 - 1 or by1 > y1 - 1: continue
            if any(not (bx1 < a or bx0 > c or by1 < b or by0 > e) for a, b, c, e in boxes): continue
            best = (d, cx, cy)
    return best
