"""Gerber RS-274X X2 + Excellon writer for the boards our generators make (no KiCad needed).
Reads the generated .kicad_pcb (footprints, pads, segments, vias, gr_text, gr_line, gr_rect, zones, Edge.Cuts)
and writes one file per layer.  Ground zones are poured with polarity layers :
  dark board area -> clear (copper of other nets + 0.3 mm) -> dark copper.
Texts are drawn as filled outlines (DejaVu Sans Bold), like the previews.
"""
import math, os, re, sys
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties

FONT = FontProperties(family="DejaVu Sans", weight="bold")

# ------------------------------------------------------------------ s-expression
def parse(s):
    toks = re.findall(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+', s)
    st = [[]]
    for t in toks:
        if t == "(":
            st.append([])
        elif t == ")":
            x = st.pop(); st[-1].append(x)
        else:
            st[-1].append(t[1:-1] if t.startswith('"') else t)
    return st[0][0]

def kids(node, name):
    return [x for x in node if isinstance(x, list) and x and x[0] == name]

def kid(node, name, default=None):
    k = kids(node, name)
    return k[0] if k else default

# ------------------------------------------------------------------ gerber file
class Gerber:
    def __init__(self, func, oy):
        self.func, self.oy = func, oy
        self.ap, self.body, self.cur, self.pol = {}, [], None, "D"
    def X(self, x, y):
        return f"X{int(round((x - 100.0) * 1e6))}Y{int(round((self.oy - y) * 1e6))}"
    def aper(self, kind, *dims):
        key = (kind,) + tuple(round(d, 4) for d in dims)
        if key not in self.ap:
            self.ap[key] = 10 + len(self.ap)
        n = self.ap[key]
        if self.cur != n:
            self.body.append(f"D{n}*"); self.cur = n
    def polarity(self, p):
        if p != self.pol:
            self.body.append(f"%LP{p}*%"); self.pol = p
    def flash(self, x, y, shape, w, h=None):
        h = w if h is None else h
        if shape == "circle" or (shape == "oval" and abs(w - h) < 1e-6):
            self.aper("C", w)
        elif shape == "oval":
            self.aper("O", w, h)
        else:
            self.aper("R", w, h)
        self.body.append(self.X(x, y) + "D03*")
    def line(self, x1, y1, x2, y2, w):
        self.aper("C", max(w, 0.01))
        self.body.append(self.X(x1, y1) + "D02*"); self.body.append(self.X(x2, y2) + "D01*")
    def region(self, pts):
        self.body.append("G36*"); self.body.append(self.X(*pts[0]) + "D02*")
        for p in pts[1:] + [pts[0]]:
            self.body.append(self.X(*p) + "D01*")
        self.body.append("G37*")
    def write(self, path):
        hdr = ["G04 Octavio gerber writer*", f"%TF.FileFunction,{self.func}*%", "%TF.FilePolarity,Positive*%",
               "%FSLAX46Y46*%", "%MOMM*%", "%LPD*%"]
        for key, n in sorted(self.ap.items(), key=lambda kv: kv[1]):
            if key[0] == "C":
                hdr.append(f"%ADD{n}C,{key[1]:.4f}*%")
            elif key[0] == "R":
                hdr.append(f"%ADD{n}R,{key[1]:.4f}X{key[2]:.4f}*%")
            else:
                hdr.append(f"%ADD{n}O,{key[1]:.4f}X{key[2]:.4f}*%")
        hdr.append("G01*")
        open(path, "w").write("\n".join(hdr + self.body + ["M02*"]) + "\n")

# ------------------------------------------------------------------ text as filled outlines
def text(g, t, x, y, size, mirror=False, just="center"):
    em = size / 0.73
    tp = TextPath((0, 0), t, size=em, prop=FONT)
    bb = tp.get_extents()
    if just == "left":
        dx = -bb.x0
    elif just == "right":
        dx = -bb.x1
    else:
        dx = -(bb.x0 + bb.x1) / 2
    dy = -size / 2                                  # vertical centre on the cap height
    polys = [p for p in tp.to_polygons(closed_only=True) if len(p) > 2]
    def area(p):
        return 0.5 * sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p)))
    if not polys:
        return
    big = max(polys, key=lambda p: abs(area(p)))
    sgn = 1 if area(big) > 0 else -1
    outer = [p for p in polys if area(p) * sgn > 0]
    holes = [p for p in polys if area(p) * sgn < 0]
    def tf(p):
        return [((-1 if mirror else 1) * (px + dx) + x, y - (py + dy)) for px, py in p]
    g.polarity("D")
    for p in outer:
        g.region(tf(p))
    if holes:
        g.polarity("C")
        for p in holes:
            g.region(tf(p))
        g.polarity("D")

# ------------------------------------------------------------------ board model
def rot(px, py, a):
    t = math.radians(a)
    return px * math.cos(t) + py * math.sin(t), -px * math.sin(t) + py * math.cos(t)

def load(path):
    b = parse(open(path).read())
    nets = {x[1]: x[2] for x in kids(b, "net")}
    pads, gfx, texts, segs, vias, rects, zones, edges = [], [], [], [], [], [], [], []
    for fp in kids(b, "footprint"):
        at = kid(fp, "at"); fx, fy = float(at[1]), float(at[2]); fr = float(at[3]) if len(at) > 3 else 0.0
        side = "B" if kid(fp, "layer")[1].startswith("B") else "F"
        for p in kids(fp, "pad"):
            pat = kid(p, "at"); px, py = float(pat[1]), float(pat[2])
            ox, oy = rot(px, py, fr)
            sz = kid(p, "size"); w, h = float(sz[1]), float(sz[2])
            pa = float(pat[3]) if len(pat) > 3 else 0.0
            if round(pa) % 180 == 90:
                w, h = h, w
            dr = kid(p, "drill"); drill = None
            if dr:
                if dr[1] == "oval":
                    dw, dh = float(dr[2]), float(dr[3])
                    if round(pa) % 180 == 90:
                        dw, dh = dh, dw
                    drill = ("slot", dw, dh)
                else:
                    drill = ("hole", float(dr[1]))
            layers = kid(p, "layers")[1:]
            net = kid(p, "net"); net = net[2] if net else None
            pads.append(dict(x=fx + ox, y=fy + oy, w=w, h=h, type=p[2], shape=p[3], drill=drill, layers=layers, net=net, side=side))
        for gl in kids(fp, "fp_line"):
            s, e = kid(gl, "start"), kid(gl, "end")
            L = kid(gl, "layer")[1]
            a = rot(float(s[1]), float(s[2]), fr); c = rot(float(e[1]), float(e[2]), fr)
            gfx.append(("line", L, fx + a[0], fy + a[1], fx + c[0], fy + c[1], float(kid(kid(gl, "stroke"), "width")[1])))
        for gc in kids(fp, "fp_circle"):
            c, e = kid(gc, "center"), kid(gc, "end")
            L = kid(gc, "layer")[1]
            a = rot(float(c[1]), float(c[2]), fr)
            r = math.hypot(float(e[1]) - float(c[1]), float(e[2]) - float(c[2]))
            gfx.append(("circle", L, fx + a[0], fy + a[1], r, float(kid(kid(gc, "stroke"), "width")[1])))
    for s in kids(b, "segment"):
        st, en = kid(s, "start"), kid(s, "end")
        segs.append(dict(x1=float(st[1]), y1=float(st[2]), x2=float(en[1]), y2=float(en[2]), w=float(kid(s, "width")[1]),
                         layer=kid(s, "layer")[1], net=nets.get(kid(s, "net")[1])))
    for v in kids(b, "via"):
        a = kid(v, "at")
        vias.append(dict(x=float(a[1]), y=float(a[2]), d=float(kid(v, "size")[1]), drill=float(kid(v, "drill")[1]), net=nets.get(kid(v, "net")[1])))
    for t in kids(b, "gr_text"):
        a = kid(t, "at"); L = kid(t, "layer")[1]
        eff = kid(t, "effects"); font = kid(eff, "font"); size = float(kid(font, "size")[1])
        j = kid(eff, "justify") or []
        texts.append(dict(t=t[1], x=float(a[1]), y=float(a[2]), layer=L, size=size, mirror="mirror" in j,
                          just="left" if "left" in j else ("right" if "right" in j else "center")))
    for l in kids(b, "gr_line"):
        s, e = kid(l, "start"), kid(l, "end")
        gfx.append(("line", kid(l, "layer")[1], float(s[1]), float(s[2]), float(e[1]), float(e[2]), float(kid(kid(l, "stroke"), "width")[1])))
    for r in kids(b, "gr_rect"):
        s, e = kid(r, "start"), kid(r, "end"); L = kid(r, "layer")[1]
        fill = kid(r, "fill"); filled = fill is not None and fill[1] in ("solid", "yes")
        x0, y0, x1, y1 = float(s[1]), float(s[2]), float(e[1]), float(e[2])
        if L == "Edge.Cuts":
            edges.append((x0, y0, x1, y1))
        elif filled:
            rects.append((L, x0, y0, x1, y1))
        else:
            w = float(kid(kid(r, "stroke"), "width")[1])
            for (a, c, d, e2) in ((x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0)):
                gfx.append(("line", L, a, c, d, e2, w))
    for z in kids(b, "zone"):
        zones.append(dict(net=z[2] if False else kid(z, "net_name")[1], layer=kid(z, "layer")[1],
                          pts=[(float(p[1]), float(p[2])) for p in kids(kid(kid(z, "polygon"), "pts"), "xy")]))
    return dict(pads=pads, gfx=gfx, texts=texts, segs=segs, vias=vias, rects=rects, zones=zones, edges=edges)

def on(layers, L):
    return L in layers or ("*.Cu" in layers and L.endswith(".Cu")) or ("*.Mask" in layers and L.endswith(".Mask"))

# ------------------------------------------------------------------ writers
def copper(M, L, oy, path, side, clear=0.3, pour=True):
    nL = 4 if any(s_["layer"].startswith("In") for s_ in M["segs"]) else 2
    idx = {"F.Cu": 1, "In1.Cu": 2, "In2.Cu": 3, "B.Cu": nL}[L]
    g = Gerber(f"Copper,L{idx},{'Top' if L == 'F.Cu' else ('Bot' if L == 'B.Cu' else 'Inr')}", oy)
    pads = [p for p in M["pads"] if on(p["layers"], L) and p["type"] != "np_thru_hole" and p["w"] > 0]
    segs = [s for s in M["segs"] if s["layer"] == L]
    zones = [z for z in M["zones"] if z["layer"] == L] if pour else []
    for z in zones:
        g.polarity("D"); g.region(z["pts"])
        g.polarity("C")
        for p in pads:
            if p["net"] != z["net"]:
                g.flash(p["x"], p["y"], p["shape"] if p["shape"] in ("circle", "oval") else "rect", p["w"] + 2 * clear, p["h"] + 2 * clear)
        for s in segs:
            if s["net"] != z["net"]:
                g.line(s["x1"], s["y1"], s["x2"], s["y2"], s["w"] + 2 * clear)
        for v in M["vias"]:
            if v["net"] != z["net"]:
                g.flash(v["x"], v["y"], "circle", v["d"] + 2 * clear)
        for p in M["pads"]:                                  # holes without copper (mounting slots, NPTH)
            if p["drill"] and (p["type"] == "np_thru_hole" or p["w"] <= 0):
                d = p["drill"]
                g.flash(p["x"], p["y"], "oval" if d[0] == "slot" else "circle", (d[1] if d[0] == "slot" else d[1]) + 2 * clear, (d[2] if d[0] == "slot" else d[1]) + 2 * clear)
    g.polarity("D")
    for (Lr, x0, y0, x1, y1) in M["rects"]:
        if Lr == L:
            g.region([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
    for s in segs:
        g.line(s["x1"], s["y1"], s["x2"], s["y2"], s["w"])
    for v in M["vias"]:
        g.flash(v["x"], v["y"], "circle", v["d"])
    for p in pads:
        g.flash(p["x"], p["y"], p["shape"] if p["shape"] in ("circle", "oval") else "rect", p["w"], p["h"])
    g.write(path)

def mask(M, L, oy, path, exp=0.05):
    g = Gerber(f"Soldermask,{'Top' if L == 'F.Mask' else 'Bot'}", oy)
    for (Lr, x0, y0, x1, y1) in M["rects"]:
        if Lr == L:
            g.region([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
    for p in M["pads"]:
        if on(p["layers"], L):
            if p["w"] > 0:
                g.flash(p["x"], p["y"], p["shape"] if p["shape"] in ("circle", "oval") else "rect", p["w"] + 2 * exp, p["h"] + 2 * exp)
            elif p["drill"]:
                d = p["drill"]
                g.flash(p["x"], p["y"], "oval" if d[0] == "slot" else "circle", d[1] + 2 * exp, (d[2] if d[0] == "slot" else d[1]) + 2 * exp)
    g.write(path)

def paste(M, L, oy, path):
    g = Gerber(f"Paste,{'Top' if L == 'F.Paste' else 'Bot'}", oy)
    for p in M["pads"]:
        if p["type"] == "smd" and L in p["layers"]:
            g.flash(p["x"], p["y"], "rect", p["w"], p["h"])
    g.write(path)

def silk(M, L, oy, path, side):
    g = Gerber(f"Legend,{'Top' if L == 'F.SilkS' else 'Bot'}", oy)
    for (Lr, x0, y0, x1, y1) in M["rects"]:
        if Lr == L:
            g.region([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
    for gf in M["gfx"]:
        if gf[1] != L:
            continue
        if gf[0] == "line":
            g.line(gf[2], gf[3], gf[4], gf[5], gf[6])
        else:
            _, _, cx, cy, r, w = gf
            n = 48
            pts = [(cx + r * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n)) for k in range(n + 1)]
            for a, b in zip(pts, pts[1:]):
                g.line(a[0], a[1], b[0], b[1], w)
    for t in M["texts"]:
        if t["layer"] == L:
            text(g, t["t"], t["x"], t["y"], t["size"], t["mirror"], t["just"])
    g.write(path)

def edge(M, oy, path):
    g = Gerber("Profile,NP", oy)
    for (x0, y0, x1, y1) in M["edges"]:
        for a, b, c, d in ((x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0)):
            g.line(a, b, c, d, 0.1)
    g.write(path)

def drill(M, oy, path_pth, path_npth):
    def write(items, path, plated):
        tools = {}
        for it in items:
            tools.setdefault(round(it[1], 3), []).append(it)
        out = ["M48", "; Octavio drill file, " + ("plated" if plated else "non plated"), "FMAT,2", "METRIC,TZ"]
        for i, d in enumerate(sorted(tools)):
            out.append(f"T{i + 1}C{d:.3f}")
        out.append("%"); out.append("G90"); out.append("G05")
        for i, d in enumerate(sorted(tools)):
            out.append(f"T{i + 1}")
            for it in tools[d]:
                if it[0] == "hole":
                    out.append(f"X{it[2] - 100.0:.3f}Y{oy - it[3]:.3f}")
                else:                                          # slot : routed between the two end centres
                    _, wd, x, y, L, vert = it
                    a = (L - wd) / 2
                    x1, y1, x2, y2 = (x, y - a, x, y + a) if vert else (x - a, y, x + a, y)
                    out.append(f"X{x1 - 100.0:.3f}Y{oy - y1:.3f}G85X{x2 - 100.0:.3f}Y{oy - y2:.3f}")
        out.append("M30")
        open(path, "w").write("\n".join(out) + "\n")
    pth, npth = [], []
    for v in M["vias"]:
        pth.append(("hole", v["drill"], v["x"], v["y"]))
    for p in M["pads"]:
        d = p["drill"]
        if not d:
            continue
        plated = p["type"] == "thru_hole" and p["w"] > 0
        if d[0] == "hole":
            (pth if plated else npth).append(("hole", d[1], p["x"], p["y"]))
        else:
            wd, L, vert = (d[1], d[2], True) if d[2] >= d[1] else (d[2], d[1], False)
            (pth if plated else npth).append(("slot", wd, p["x"], p["y"], L, vert))
    write(pth, path_pth, True)
    write(npth, path_npth, False)
    return len(pth), len(npth)

def board(pcb, outdir, name, oy, pour=True):
    os.makedirs(outdir, exist_ok=True)
    M = load(pcb)
    files = []
    CU = [("F.Cu", "GTL"), ("B.Cu", "GBL")]
    if any(s_["layer"].startswith("In") for s_ in M["segs"]):
        CU += [("In1.Cu", "G1"), ("In2.Cu", "G2")]
        if pour and M["edges"]:
            x0, y0, x1, y1 = M["edges"][0]
            for L_ in ("In1.Cu", "In2.Cu"):            # ground planes poured around the inner tracks
                if not any(z["layer"] == L_ for z in M["zones"]):
                    M["zones"].append(dict(net="GND", layer=L_, pts=[(x0 + 0.5, y0 + 0.5), (x1 - 0.5, y0 + 0.5), (x1 - 0.5, y1 - 0.5), (x0 + 0.5, y1 - 0.5)]))
    for L, ext in CU:
        copper(M, L, oy, f"{outdir}/{name}-{L.replace('.', '_')}.{ext.lower()}", L[0], pour=pour); files.append(ext)
    for L, ext in (("F.Mask", "gts"), ("B.Mask", "gbs")):
        mask(M, L, oy, f"{outdir}/{name}-{L.replace('.', '_')}.{ext}")
    for L, ext in (("F.Paste", "gtp"), ("B.Paste", "gbp")):
        paste(M, L, oy, f"{outdir}/{name}-{L.replace('.', '_')}.{ext}")
    for L, ext in (("F.SilkS", "gto"), ("B.SilkS", "gbo")):
        silk(M, L, oy, f"{outdir}/{name}-{L.replace('.', '_')}.{ext}", L[0])
    edge(M, oy, f"{outdir}/{name}-Edge_Cuts.gm1")
    n = drill(M, oy, f"{outdir}/{name}-PTH.drl", f"{outdir}/{name}-NPTH.drl")
    return M, n

if __name__ == "__main__":
    pcb, outdir, name = sys.argv[1:4]
    M, n = board(pcb, outdir, name, float(sys.argv[4]) if len(sys.argv) > 4 else 228.5)
    print("pads", len(M["pads"]), "segments", len(M["segs"]), "vias", len(M["vias"]), "texts", len(M["texts"]), "drills", n)
