"""Finish the last connections Freerouting left open : a small grid router (0.1 mm, 4 layers, through vias)
that joins every isolated island of a net to its main island, keeping 0.2 mm clearance. GND islands only need
to reach an inner layer (the inner layers are poured ground planes)."""
import sys, math, heapq, uuid, re
import numpy as np
sys.path.insert(0, "/home/claude/work/fab")
from gerber import load, on
from drc import dist

RES = 0.1
LAY = ("F.Cu", "In1.Cu", "In2.Cu", "B.Cu")
import os
TW, CL, VD, VDR = [float(v) for v in os.environ.get("FIN", "0.25,0.2,0.6,0.3").split(",")]

def islands(M, net):
    nodes = []
    for p in M["pads"]:
        if p["net"] == net and p["w"] > 0:
            nodes.append(("pad", [L for L in LAY if on(p["layers"], L)], (p["x"], p["y"], p["w"], p["h"])))
    for s in M["segs"]:
        if s["net"] == net:
            nodes.append(("seg", [s["layer"]], (s["x1"], s["y1"], s["x2"], s["y2"], s["w"])))
    for v in M["vias"]:
        if v["net"] == net:
            nodes.append(("via", list(LAY), (v["x"], v["y"], v["d"])))
    par = list(range(len(nodes)))
    def F(i):
        while par[i] != i:
            par[i] = par[par[i]]; i = par[i]
        return i
    for a in range(len(nodes)):
        for b in range(a + 1, len(nodes)):
            if set(nodes[a][1]) & set(nodes[b][1]) and abs(nodes[a][2][0] - nodes[b][2][0]) < 30 and dist((None, nodes[a][0], nodes[a][2]), (None, nodes[b][0], nodes[b][2])) <= 0.01:
                par[F(a)] = F(b)
    g = {}
    for i, n in enumerate(nodes):
        g.setdefault(F(i), []).append(n)
    return sorted(g.values(), key=len, reverse=True)

def route(pcb):
    M = load(pcb)
    x0, y0, x1, y1 = M["edges"][0]
    W, H = int((x1 - x0) / RES) + 1, int((y1 - y0) / RES) + 1
    def cell(x, y):
        return int(round((x - x0) / RES)), int(round((y - y0) / RES))
    def paint(grid, kind, g, infl, val=1):
        if kind == "seg":
            ax, ay, bx, by, w = g
            r = w / 2 + infl
            n = max(1, int(math.hypot(bx - ax, by - ay) / (RES * 0.5)))
            for k in range(n + 1):
                cx, cy = ax + (bx - ax) * k / n, ay + (by - ay) * k / n
                disc(grid, cx, cy, r, val)
        elif kind == "via":
            disc(grid, g[0], g[1], g[2] / 2 + infl, val)
        else:
            x, y, w, h = g
            i0, j0 = cell(x - w / 2 - infl, y - h / 2 - infl); i1, j1 = cell(x + w / 2 + infl, y + h / 2 + infl)
            grid[max(0, j0):j1 + 1, max(0, i0):i1 + 1] = val
    def disc(grid, cx, cy, r, val):
        i0, j0 = cell(cx - r, cy - r); i1, j1 = cell(cx + r, cy + r)
        for j in range(max(0, j0), min(H, j1 + 1)):
            for i in range(max(0, i0), min(W, i1 + 1)):
                if (x0 + i * RES - cx) ** 2 + (y0 + j * RES - cy) ** 2 <= r * r:
                    grid[j, i] = val
    added_s, added_v = [], []
    todo = []
    nets = sorted({p["net"] for p in M["pads"] if p["net"]})
    for net in nets:
        isl = islands(M, net)
        if len(isl) > 1:
            todo.append((net, isl))
    prio = [x for x in os.environ.get('PRIO', '').split(',') if x]
    todo.sort(key=lambda t: (0 if t[0] in prio else 1))
    print("to finish:", [(n, len(i)) for n, i in todo])
    for net, isl in todo:
        # obstacles for this net : every other-net copper, inflated
        obs = {L: np.zeros((H, W), bool) for L in LAY}
        infl = CL + TW / 2
        for p in M["pads"]:
            if p["net"] != net:
                for L in LAY:
                    if (p["w"] > 0 and on(p["layers"], L)) or p["drill"]:
                        g = (p["x"], p["y"], max(p["w"], (p["drill"][1] if p["drill"] else 0)), max(p["h"], (p["drill"][-1] if p["drill"] else 0)))
                        paint(obs[L], "pad", g, infl)
        for s in M["segs"] + added_s:
            if s["net"] != net:
                paint(obs[s["layer"]], "seg", (s["x1"], s["y1"], s["x2"], s["y2"], s["w"]), infl)
        for v in M["vias"] + added_v:
            if v["net"] != net:
                for L in LAY:
                    paint(obs[L], "via", (v["x"], v["y"], v["d"]), infl)
        for L in LAY:                                     # board edge keep-out 0.5 mm
            m = int(0.5 / RES) + 2
            obs[L][:m, :] = obs[L][-m:, :] = True; obs[L][:, :m] = obs[L][:, -m:] = True
        viaok = np.ones((H, W), bool)
        grow = int(math.ceil((VD / 2 - TW / 2) / RES))
        for L in LAY:
            o = obs[L]
            ov = o.copy()
            for d in range(1, grow + 1):
                ov[d:, :] |= o[:-d, :]; ov[:-d, :] |= o[d:, :]; ov[:, d:] |= o[:, :-d]; ov[:, :-d] |= o[:, d:]
            viaok &= ~ov
        main = isl[0]
        for small in isl[1:]:
            def cells_of(group, gnd_plane=False):
                out = set()
                for (kind, layers, g) in group:
                    pts = []
                    if kind == "pad" or kind == "via":
                        pts = [(g[0], g[1])]
                    else:
                        n = max(1, int(math.hypot(g[2] - g[0], g[3] - g[1]) / RES))
                        pts = [(g[0] + (g[2] - g[0]) * k / n, g[1] + (g[3] - g[1]) * k / n) for k in range(n + 1)]
                    for (x, y) in pts:
                        i, j = cell(x, y)
                        for L in layers:
                            out.add((LAY.index(L), j, i))
                return out
            src = cells_of(small)
            if net == "GND":
                tgt = None                                   # any free cell on an inner (plane) layer
            else:
                tgt = cells_of(main)
            # A*
            dirs = [(1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1), (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414)]
            tx = np.mean([c[2] for c in tgt]) if tgt else None
            ty = np.mean([c[1] for c in tgt]) if tgt else None
            def h(c):
                return 0 if tgt is None else 0.5 * math.hypot(c[2] - tx, c[1] - ty)
            pq = [(h(c), 0, c) for c in src]
            heapq.heapify(pq)
            best, prev = {c: 0 for c in src}, {}
            found = None
            while pq:
                f, gc, c = heapq.heappop(pq)
                if gc > best.get(c, 1e18):
                    continue
                l, j, i = c
                if (tgt is not None and c in tgt) or (tgt is None and l in (1, 2)):
                    found = c; break
                for di, dj, w in dirs:
                    n = (l, j + dj, i + di)
                    if 0 <= n[1] < H and 0 <= n[2] < W and not obs[LAY[l]][n[1], n[2]]:
                        ng = gc + w
                        if ng < best.get(n, 1e18):
                            best[n] = ng; prev[n] = c; heapq.heappush(pq, (ng + h(n), ng, n))
                if viaok[j, i]:
                    for l2 in range(4):
                        if l2 != l:
                            n = (l2, j, i)
                            ng = gc + 15
                            if ng < best.get(n, 1e18):
                                best[n] = ng; prev[n] = c; heapq.heappush(pq, (ng + h(n), ng, n))
            if not found:
                print("  could not finish", net); continue
            path = [found]
            while path[-1] in prev:
                path.append(prev[path[-1]])
            path.reverse()
            P = lambda c: (round(x0 + c[2] * RES, 3), round(y0 + c[1] * RES, 3))
            k = 0
            while k < len(path) - 1:
                a = path[k]
                if path[k + 1][0] != a[0]:
                    x, y = P(a)
                    added_v.append(dict(x=x, y=y, d=VD, drill=VDR, net=net))
                    k += 1; continue
                e = k + 1
                d0 = (path[e][1] - a[1], path[e][2] - a[2])
                while e + 1 < len(path) and path[e + 1][0] == a[0] and (path[e + 1][1] - path[e][1], path[e + 1][2] - path[e][2]) == d0:
                    e += 1
                (ax, ay), (bx, by) = P(a), P(path[e])
                added_s.append(dict(x1=ax, y1=ay, x2=bx, y2=by, w=TW, layer=LAY[a[0]], net=net))
                k = e
            if net == "GND" and path[-1][0] in (1, 2):
                pass
            print("  finished", net, "path", len(path), "cells")
    txt = open(pcb).read()
    nn = {n: i for i, n in re.findall(r'^\s*\(net (\d+) "([^"]*)"\)', txt, re.M)}
    out = []
    for s in added_s:
        out.append(f'  (segment (start {s["x1"]} {s["y1"]}) (end {s["x2"]} {s["y2"]}) (width {s["w"]}) (layer "{s["layer"]}") (net {nn[s["net"]]}) (uuid "{uuid.uuid4()}"))')
    for v in added_v:
        out.append(f'  (via (at {v["x"]} {v["y"]}) (size {v["d"]}) (drill {v["drill"]}) (layers "F.Cu" "B.Cu") (net {nn[v["net"]]}) (uuid "{uuid.uuid4()}"))')
    i = txt.rstrip().rfind(")")
    open(pcb, "w").write(txt[:i] + "\n".join(out) + "\n)\n")
    print("added", len(added_s), "segments", len(added_v), "vias")

if __name__ == "__main__":
    route(sys.argv[1])
