"""Small independent DRC on the routed .kicad_pcb : every net fully connected (pads, tracks, vias),
and copper-to-copper clearance between different nets on each layer."""
import sys, math
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from gerber import load, on

def seg_pt(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))

def seg_seg(a, b):
    def inter(p1, p2, p3, p4):
        d = (p2[0] - p1[0]) * (p4[1] - p3[1]) - (p2[1] - p1[1]) * (p4[0] - p3[0])
        if abs(d) < 1e-12:
            return False
        t = ((p3[0] - p1[0]) * (p4[1] - p3[1]) - (p3[1] - p1[1]) * (p4[0] - p3[0])) / d
        u = ((p3[0] - p1[0]) * (p2[1] - p1[1]) - (p3[1] - p1[1]) * (p2[0] - p1[0])) / d
        return 0 <= t <= 1 and 0 <= u <= 1
    if inter(a[:2], a[2:], b[:2], b[2:]):
        return 0.0
    return min(seg_pt(*a[:2], *b), seg_pt(*a[2:], *b), seg_pt(*b[:2], *a), seg_pt(*b[2:], *a))

def items(M, L):
    out = []   # (net, kind, geom, radius-ish)
    for p in M["pads"]:
        if on(p["layers"], L) and p["w"] > 0 and p["type"] != "np_thru_hole":
            out.append((p["net"], "pad", (p["x"], p["y"], p["w"], p["h"])))
    for s in M["segs"]:
        if s["layer"] == L:
            out.append((s["net"], "seg", (s["x1"], s["y1"], s["x2"], s["y2"], s["w"])))
    for v in M["vias"]:
        out.append((v["net"], "via", (v["x"], v["y"], v["d"])))
    return out

def dist(a, b):
    """approximate edge distance between two copper items (pads treated as rectangles -> sampled segments)"""
    def segs(it):
        k, g = it[1], it[2]
        if k == "seg":
            return [(g[0], g[1], g[2], g[3])], g[4] / 2
        if k == "via":
            return [(g[0], g[1], g[0], g[1])], g[2] / 2
        x, y, w, h = g
        r = min(w, h) / 2
        if w >= h:
            return [(x - w / 2 + r, y, x + w / 2 - r, y)], r
        return [(x, y - h / 2 + r, x, y + h / 2 - r)], r
    sa, ra = segs(a); sb, rb = segs(b)
    return min(seg_seg(p, q) for p in sa for q in sb) - ra - rb

def run(pcb, clear=0.19):
    M = load(pcb)
    # connectivity
    par = {}
    def F(x):
        while par.setdefault(x, x) != x:
            par[x] = par[par[x]]; x = par[x]
        return x
    def U(a, b):
        par[F(a)] = F(b)
    nodes = []
    for i, p in enumerate(M["pads"]):
        if p["net"] and p["w"] > 0:
            nodes.append(("p", i, p["net"], [L for L in ("F.Cu", "In1.Cu", "In2.Cu", "B.Cu") if on(p["layers"], L)], (p["x"], p["y"], p["w"], p["h"])))
    for i, s in enumerate(M["segs"]):
        nodes.append(("s", i, s["net"], [s["layer"]], (s["x1"], s["y1"], s["x2"], s["y2"], s["w"])))
    for i, v in enumerate(M["vias"]):
        nodes.append(("v", i, v["net"], ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"], (v["x"], v["y"], v["d"])))
    bynet = {}
    for n in nodes:
        bynet.setdefault(n[2], []).append(n)
    unconnected = []
    for net, ns in bynet.items():
        for a in range(len(ns)):
            for b in range(a + 1, len(ns)):
                A, B = ns[a], ns[b]
                if not set(A[3]) & set(B[3]):
                    continue
                ka = {"p": "pad", "s": "seg", "v": "via"}
                if dist((None, ka[A[0]], A[4]), (None, ka[B[0]], B[4])) <= 0.01:
                    U((A[0], A[1]), (B[0], B[1]))
        groups = {F((n[0], n[1])) for n in ns if n[0] == "p"}
        if len(groups) > 1:
            unconnected.append((net, len(groups)))
    # clearance
    viol = []
    for L in ("F.Cu", "In1.Cu", "In2.Cu", "B.Cu"):
        its = items(M, L)
        for a in range(len(its)):
            for b in range(a + 1, len(its)):
                A, B = its[a], its[b]
                if A[0] == B[0] and A[0] is not None:
                    continue
                ga, gb = A[2], B[2]
                if abs(ga[0] - gb[0]) > 12 or abs(ga[1] - gb[1]) > 12:
                    continue
                d = dist(A, B)
                if d < clear:
                    viol.append((L, A[0], B[0], round(d, 3), round(ga[0], 2), round(ga[1], 2)))
    return unconnected, viol

if __name__ == "__main__":
    u, v = run(sys.argv[1])
    print("unconnected nets", len(u), u[:15])
    print("clearance violations", len(v))
    for x in v[:15]:
        print(" ", x)
