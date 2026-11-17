import os, math, json, csv
from kicadgen import *
import sys, importlib
MD = sys.argv[1]; sys.path.insert(0, f"/home/claude/work/{MD}")
M = importlib.import_module("parts" + MD)
P, BLOCKS, PANEL_W, PANEL_H, HP = M.P, M.BLOCKS, M.PANEL_W, M.PANEL_H, M.HP

OUT = "/home/claude/work/out/" + M.FOLDER
PROJ = M.PROJ
os.makedirs(OUT + "/octavio_mu.pretty", exist_ok=True)
os.makedirs(OUT + "/panel", exist_ok=True)
OX, OY = 100.0, 100.0  # panel top-left in PCB coordinates
parts = {p["ref"]: p for p in P}

# ------------------------------------------------------------------ nets
netnames = ["GND", "+12V", "-12V"]
for p in P:
    for n in p["pins"].values():
        if n and n not in netnames:
            netnames.append(n)
NETS = {"": 0}
for i, n in enumerate(netnames):
    NETS[n] = i + 1

# ------------------------------------------------------------------ placement
PCB_X0, PCB_X1 = OX + 1.5, OX + PANEL_W - 1.5
PCB_Y0, PCB_Y1 = OY + 11.0, OY + 117.5

def rect_overlap(a, b):
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])

back_keep = []   # obstacles for bottom-side SMD placement
front_keep = []  # front bodies (for bottom THT parts whose pins come through)
for p in P:
    if p["pos"] is None:
        continue
    x, y = OX + p["pos"][0], OY + p["pos"][1]
    p["X"], p["Y"] = x, y
    for (_, ax, ay, w, h, kind) in pad_abs(p["fp"], x, y, p["rot"], p["side"]):
        if kind != "smd":
            back_keep.append((ax - w / 2 - 0.5, ay - h / 2 - 0.5, ax + w / 2 + 0.5, ay + h / 2 + 0.5))
    bb = fp_bbox(p["fp"], x, y, p["rot"], p["side"], 0.4)
    if p["side"] == "B":
        back_keep.append(bb)
    else:
        front_keep.append(bb)

ICS = [p["ref"] for p in P if p["ref"].startswith("U") or p["ref"] == "A1"]
GRID = M.GRID
POWER = {"GND", "+12V", "-12V", "+12V_IN", "-12V_IN", None}
def anchor_for(ref):
    p = parts[ref]
    if ref in ICS:
        return GRID[ICS.index(ref) % len(GRID)]
    nets = set(p["pins"].values()) - POWER
    for u in ICS:
        if "X" in parts[u] and nets & set(parts[u]["pins"].values()):
            return (parts[u]["X"] - OX, parts[u]["Y"] - OY)
    if p["kind"] == "C" and p["val"] == "100n":
        k = int(ref[1:]); return (40, 70)
    return (40, 60)

def place(p):
    ax, ay = anchor_for(p["ref"])
    ax += OX; ay += OY
    best = None
    for r in range(0, 120):
        rad = r * 0.5
        steps = max(8, int(2 * math.pi * rad / 0.5))
        for k in range(steps):
            t = 2 * math.pi * k / steps
            x = round((ax + rad * math.cos(t)) * 4) / 4
            y = round((ay + rad * math.sin(t)) * 4) / 4
            for rot in (0, 90):
                bb = fp_bbox(p["fp"], x, y, rot, "B", 0.3)
                if bb[0] < PCB_X0 + 0.8 or bb[2] > PCB_X1 - 0.8 or bb[1] < PCB_Y0 + 0.8 or bb[3] > PCB_Y1 - 0.8:
                    continue
                if any(rect_overlap(bb, o) for o in back_keep):
                    continue
                if FP[p["fp"]]["attr"] == "through_hole" and any(rect_overlap(bb, o) for o in front_keep):
                    continue
                best = (x, y, rot, bb)
                break
            if best:
                break
        if best:
            break
    if not best:
        raise RuntimeError("no place for " + p["ref"])
    p["X"], p["Y"], p["rot"] = best[0], best[1], best[2]
    back_keep.append(best[3])
    if FP[p["fp"]]["attr"] == "through_hole":
        for (_, x, y, w, h, kind) in pad_abs(p["fp"], p["X"], p["Y"], p["rot"], "B"):
            front_keep.append((x - w / 2 - 0.5, y - h / 2 - 0.5, x + w / 2 + 0.5, y + h / 2 + 0.5))

# place big ones first, then by block order
def place_pico():
    p = parts["A1"]; best = None
    thr = [(x, y, w, h) for (x0, y0, x1, y1) in back_keep for (x, y, w, h) in [((x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0)] if w < 4 and h < 4]
    for rot in (90, 0):
        for yy in range(20, 110):
            for xx in range(20, 150):
                X, Y = OX + xx, OY + yy
                bb = fp_bbox(p["fp"], X, Y, rot, "B", 0.0)
                if bb[0] < PCB_X0 + 0.5 or bb[2] > PCB_X1 - 0.5 or bb[1] < PCB_Y0 + 0.5 or bb[3] > PCB_Y1 - 0.5:
                    continue
                ok = True
                for (_, ax, ay, w, h, kind) in pad_abs(p["fp"], X, Y, rot, "B"):
                    r = (ax - 1.3, ay - 1.3, ax + 1.3, ay + 1.3)
                    if any(rect_overlap(r, o) for o in back_keep):
                        ok = False; break
                if ok:
                    best = (X, Y, rot); break
            if best: break
        if best: break
    if not best:
        raise RuntimeError("no place for the Pico")
    p["X"], p["Y"], p["rot"] = best
    for (_, x, y, w, h, kind) in pad_abs(p["fp"], p["X"], p["Y"], p["rot"], "B"):
        back_keep.append((x - w / 2 - 0.4, y - h / 2 - 0.4, x + w / 2 + 0.4, y + h / 2 + 0.4))
        front_keep.append((x - w / 2 - 0.4, y - h / 2 - 0.4, x + w / 2 + 0.4, y + h / 2 + 0.4))
def place_j1():
    p = parts["J1"]; fpn = p["fp"]
    for rr in range(0, 200):
        for (dx, dy) in [(0, 0)] + [(rr * 0.5 * math.cos(t), rr * 0.5 * math.sin(t)) for t in [k * math.pi / 12 for k in range(24)]]:
            for rot in (0, 90):
                X, Y = OX + M.J1A[0] + dx, OY + M.J1A[1] + dy
                bb = fp_bbox(fpn, X, Y, rot, "B", 0.3)
                if bb[0] < PCB_X0 + 0.8 or bb[2] > PCB_X1 - 0.8 or bb[1] < PCB_Y0 + 0.8 or bb[3] > PCB_Y1 - 0.8:
                    continue
                if any(rect_overlap(bb, o) for o in back_keep):
                    continue
                pads = [(ax - w / 2 - 0.4, ay - h / 2 - 0.4, ax + w / 2 + 0.4, ay + h / 2 + 0.4) for (_, ax, ay, w, h, k) in pad_abs(fpn, X, Y, rot, "B")]
                if any(rect_overlap(a, b) for a in pads for b in front_keep):
                    continue
                p["X"], p["Y"], p["rot"] = X, Y, rot
                back_keep.append(bb); front_keep.extend(pads)
                return
    raise RuntimeError("no place for J1")
place_j1()
order = ICS + ["D1", "D2", "C1", "C2"]
for _, refs in BLOCKS:
    for r in refs:
        if r not in order:
            order.append(r)
for r in order:
    if parts[r]["pos"] is None and "X" not in parts[r]:
        place(parts[r])

# ------------------------------------------------------------------ footprint library
for name in FP:
    if name.startswith("octavio_mu:"):
        open(f"{OUT}/octavio_mu.pretty/{name.split(':')[1]}.kicad_mod", "w").write(footprint_mod(name))

# ------------------------------------------------------------------ main PCB
def pcb_header(thick=1.6):
    return f'''(kicad_pcb (version 20240108) (generator "octavio_gen") (generator_version "8.0")
  (general (thickness {thick}) (legacy_teardrops no))
  (paper "A4")
  (title_block (title "Octavio {M.NAME} (Eurorack)") (company "Octavio / Sinecraft") (rev "{M.REV}"))
  (layers
    (0 "F.Cu" signal) (31 "B.Cu" signal)
    (32 "B.Adhes" user "B.Adhesive") (33 "F.Adhes" user "F.Adhesive")
    (34 "B.Paste" user) (35 "F.Paste" user)
    (36 "B.SilkS" user "B.Silkscreen") (37 "F.SilkS" user "F.Silkscreen")
    (38 "B.Mask" user) (39 "F.Mask" user)
    (40 "Dwgs.User" user "User.Drawings") (41 "Cmts.User" user "User.Comments")
    (42 "Eco1.User" user "User.Eco1") (43 "Eco2.User" user "User.Eco2")
    (44 "Edge.Cuts" user) (45 "Margin" user)
    (46 "B.CrtYd" user "B.Courtyard") (47 "F.CrtYd" user "F.Courtyard")
    (48 "B.Fab" user) (49 "F.Fab" user)
  )
  (setup (pad_to_mask_clearance 0) (allow_soldermask_bridges_in_footprints no))
'''

def gr_rect(x1, y1, x2, y2, layer, w=0.1):
    return f'  (gr_rect (start {f(x1)} {f(y1)}) (end {f(x2)} {f(y2)}) (stroke (width {w}) (type default)) (fill none) (layer {q(layer)}) (uuid {q(U())}))'

def gr_line(x1, y1, x2, y2, layer, w=0.15):
    return f'  (gr_line (start {f(x1)} {f(y1)}) (end {f(x2)} {f(y2)}) (stroke (width {w}) (type default)) (layer {q(layer)}) (uuid {q(U())}))'

def gr_text(t, x, y, layer, size=1.0, th=0.15, just="", mirror=False):
    j = ""
    if just or mirror:
        j = " (justify" + (" " + just if just else "") + (" mirror" if mirror else "") + ")"
    return f'  (gr_text {q(t)} (at {f(x)} {f(y)} 0) (layer {q(layer)}) (uuid {q(U())}) (effects (font (size {f(size)} {f(size)}) (thickness {f(th)})){j}))'

def zone(net, layer, x0, y0, x1, y1):
    return f'''  (zone (net {NETS[net]}) (net_name {q(net)}) (layer {q(layer)}) (uuid {q(U())}) (hatch edge 0.5)
    (connect_pads (clearance 0.3)) (min_thickness 0.25) (filled_areas_thickness no)
    (fill (thermal_gap 0.4) (thermal_bridge_width 0.4))
    (polygon (pts (xy {f(x0)} {f(y0)}) (xy {f(x1)} {f(y0)}) (xy {f(x1)} {f(y1)}) (xy {f(x0)} {f(y1)}))))'''

pcb = [pcb_header()]
for n, i in NETS.items():
    pcb.append(f"  (net {i} {q(n)})")
for p in P:
    pn = {k: v for k, v in p["pins"].items() if v}
    pcb.append("  " + footprint_pcb(p["fp"], p["ref"], p["val"], p["X"], p["Y"], p["rot"], p["side"], pn, NETS).replace("\n", "\n  "))
pcb.append(gr_rect(PCB_X0, PCB_Y0, PCB_X1, PCB_Y1, "Edge.Cuts", 0.1))
# panel outline + rails for reference
pcb.append(gr_rect(OX, OY, OX + PANEL_W, OY + PANEL_H, "Dwgs.User", 0.1))
pcb.append(gr_line(OX, OY + 10, OX + PANEL_W, OY + 10, "Dwgs.User", 0.1))
pcb.append(gr_line(OX, OY + PANEL_H - 10, OX + PANEL_W, OY + PANEL_H - 10, "Dwgs.User", 0.1))
pcb.append(gr_text(f"Panel {HP}HP outline / rails", OX + 1, OY + 8.5, "Dwgs.User", 1.0, 0.12, "left"))
pcb.append(gr_text("OCTAVIO " + M.NAME, OX + PANEL_W / 2, OY + 20.0, "B.SilkS", 1.5, 0.25, "", True))
pcb.append(gr_text(f"rev {M.REV}  {HP}HP  SINECRAFT", OX + PANEL_W / 2, OY + 22.0, "B.SilkS", 0.9, 0.15, "", True))
pcb.append(gr_text("-12V = RED STRIPE (pin 1)", OX + PANEL_W / 2, OY + 50.0, "B.SilkS", 0.8, 0.12, "", True))
pcb.append(zone("GND", "F.Cu", PCB_X0, PCB_Y0, PCB_X1, PCB_Y1))
pcb.append(zone("GND", "B.Cu", PCB_X0, PCB_Y0, PCB_X1, PCB_Y1))
pcb.append(")")
open(f"{OUT}/{PROJ}.kicad_pcb", "w").write("\n".join(pcb) + "\n")

# ------------------------------------------------------------------ panel PCB (aluminium)
pan = [pcb_header(1.6).replace(f"Octavio {M.NAME} (Eurorack)", f"Octavio {M.NAME} - front panel {HP}HP")]
pan.append('  (net 0 "")')
def npth(x, y, d, oval=None):
    if oval:
        return f'''  (footprint "octavio_mu:Hole" (layer "F.Cu") (uuid {q(U())}) (at {f(x)} {f(y)})
    (property "Reference" "H" (at 0 0 0) (layer "F.Fab") (uuid {q(U())}) (effects (font (size 0.5 0.5) (thickness 0.08)) hide))
    (property "Value" "hole" (at 0 0 0) (layer "F.Fab") (uuid {q(U())}) (effects (font (size 0.5 0.5) (thickness 0.08)) hide))
    (attr exclude_from_pos_files exclude_from_bom)
    (pad "" np_thru_hole oval (at 0 0) (size {f(oval[0])} {f(oval[1])}) (drill oval {f(oval[0])} {f(oval[1])}) (layers "*.Cu" "*.Mask") (uuid {q(U())})))'''
    return f'''  (footprint "octavio_mu:Hole" (layer "F.Cu") (uuid {q(U())}) (at {f(x)} {f(y)})
    (property "Reference" "H" (at 0 0 0) (layer "F.Fab") (uuid {q(U())}) (effects (font (size 0.5 0.5) (thickness 0.08)) hide))
    (property "Value" "hole" (at 0 0 0) (layer "F.Fab") (uuid {q(U())}) (effects (font (size 0.5 0.5) (thickness 0.08)) hide))
    (attr exclude_from_pos_files exclude_from_bom)
    (pad "" np_thru_hole circle (at 0 0) (size {f(d)} {f(d)}) (drill {f(d)}) (layers "*.Cu" "*.Mask") (uuid {q(U())})))'''

PANEL_HOLES = []
for hx in (7.5, 7.5 + (HP - 3) * 5.08):
    for hy in (3.0, PANEL_H - 3.0):
        PANEL_HOLES.append((hx, hy, 3.2, (5.2, 3.2)))
for p in P:
    if p["side"] == "F" and "panel_hole" in FP[p["fp"]]:
        _o = FP[p["fp"]].get("hole_off", (0, 0))
        PANEL_HOLES.append((p["pos"][0] + _o[0], p["pos"][1] + _o[1], FP[p["fp"]]["panel_hole"], None))
for (hx, hy, d, ov) in PANEL_HOLES:
    pan.append(npth(OX + hx, OY + hy, d, ov))
pan.append(gr_rect(OX, OY, OX + PANEL_W, OY + PANEL_H, "Edge.Cuts", 0.1))
# Bare-metal side strips (look of the bent aluminium flanges of the Moog panel):
# exposed copper, no solder mask -> silver with lead-free HASL finish
STRIP = (0.3, 1.6)
for x0, x1 in ((STRIP[0], STRIP[1]), (PANEL_W - STRIP[1], PANEL_W - STRIP[0])):
    for L in ("F.Cu", "F.Mask"):
        pan.append(f'  (gr_rect (start {f(OX + x0)} {f(OY + 0.3)}) (end {f(OX + x1)} {f(OY + PANEL_H - 0.3)}) (stroke (width 0)) (fill solid) (layer {q(L)}) (uuid {q(U())}))')

PANEL_TEXT = []  # (text, x, y, size, thickness) in panel coords
def T(t, x, y, s=1.2, th=0.2):
    s = 2.6 if t == M.TITLE else round(s * 1.25, 3)   # bigger, bold (stroke = size/5), still smaller than the logo
    PANEL_TEXT.append((t, x, y, s, round(s * 0.2, 3)))
cx = PANEL_W / 2
import math as _m
TICKS = []   # (x1,y1,x2,y2,width) panel coords, also exported for previews
def knob_scale(kx, ky, labels, r_num=10.5, r1=6.0, r2=7.0, size=0.8):
    n = len(labels)
    for k, lab in enumerate(labels):
        ang = _m.radians(-135 + k * 270 / (n - 1))
        if lab: T(lab, kx + r_num * _m.sin(ang), ky - r_num * _m.cos(ang) + 0.1, size, 0.14)
        TICKS.append((kx + r1 * _m.sin(ang), ky - r1 * _m.cos(ang), kx + r2 * _m.sin(ang), ky - r2 * _m.cos(ang), 0.2))
T(M.TITLE, cx, 3.4, 2.6, 0.5)
M.panel_art(T, knob_scale, TICKS)
for (t, x, y, s, th) in PANEL_TEXT:
    pan.append(gr_text(t, OX + x, OY + y, "F.SilkS", s, th))
for (x1, y1, x2, y2, w_) in TICKS:
    pan.append(gr_line(OX + x1, OY + y1, OX + x2, OY + y2, "F.SilkS", w_))
# ocTavio logo (bitmap -> filled silkscreen runs)
import numpy as _np
_LM = _np.load("/home/claude/work/logo_mask.npy")
LOGO_W = 16.0; _px = LOGO_W / _LM.shape[1]; LOGO_H = _LM.shape[0] * _px
LOGO_X0 = cx - LOGO_W / 2; LOGO_Y0 = 121.3 - LOGO_H / 2
for _r in range(_LM.shape[0]):
    _row = _LM[_r]; _c = 0
    while _c < len(_row):
        if _row[_c]:
            _s = _c
            while _c < len(_row) and _row[_c]: _c += 1
            pan.append(f'  (gr_rect (start {f(OX + LOGO_X0 + _s*_px)} {f(OY + LOGO_Y0 + _r*_px)}) (end {f(OX + LOGO_X0 + _c*_px)} {f(OY + LOGO_Y0 + (_r+1)*_px)}) (stroke (width 0)) (fill solid) (layer "F.SilkS") (uuid {q(U())}))')
        else:
            _c += 1
LOGO = [LOGO_X0, LOGO_Y0, LOGO_W, LOGO_H]
# Moog frame lines between channels
DIV = M.DIV
for (x1, y1, x2, y2) in DIV:
    pan.append(gr_line(OX + x1, OY + y1, OX + x2, OY + y2, "F.SilkS", 0.3))
pan.append(gr_text("Octavio " + M.NAME + " panel - black mask, white silk, aluminium 1.6 mm", OX, OY + PANEL_H + 4, "Cmts.User", 1.0, 0.15, "left"))
pan.append(")")
open(f"{OUT}/panel/{PROJ}-panel.kicad_pcb", "w").write("\n".join(pan) + "\n")
open(f"{OUT}/panel/{PROJ}-panel.kicad_pro", "w").write(json.dumps({"meta": {"filename": f"{PROJ}-panel.kicad_pro", "version": 1}}, indent=2))

# ------------------------------------------------------------------ symbols
G = 2.54
SYM = {}
def box(name, left, right, width, show_names=True, label=""):
    n = max(len(left), len(right), 1)
    H = (n + 1) * G
    top = H / 2
    pins = []
    for i, (num, nm) in enumerate(left):
        pins.append((num, nm, -(width / 2 + G), top - G * (i + 1), 0))
    for i, (num, nm) in enumerate(right):
        pins.append((num, nm, (width / 2 + G), top - G * (i + 1), 180))
    SYM[name] = dict(W=width, H=H, pins=pins, names=show_names, label=label)

box("R", [("1", "~")], [("2", "~")], 5.08, False, "R")
box("C", [("1", "~")], [("2", "~")], 5.08, False, "C")
box("D", [("2", "A")], [("1", "K")], 5.08, True, "D")
box("NPN", [("1", "B")], [("3", "C"), ("2", "E")], 5.08, True)
box("DUALNPN", [("2", "B1"), ("5", "B2")], [("6", "C1"), ("1", "E1"), ("3", "C2"), ("4", "E2")], 7.62, True)
box("TL074", [("3", "+A"), ("2", "-A"), ("5", "+B"), ("6", "-B"), ("10", "+C"), ("9", "-C"), ("12", "+D"), ("13", "-D")],
    [("1", "OA"), ("7", "OB"), ("8", "OC"), ("14", "OD"), ("4", "V+"), ("11", "V-")], 10.16, True)
box("TL072", [("3", "+A"), ("2", "-A"), ("5", "+B"), ("6", "-B")], [("1", "OA"), ("7", "OB"), ("8", "V+"), ("4", "V-")], 10.16, True)
box("POT", [("1", "CCW"), ("3", "CW")], [("2", "W")], 7.62, True)
box("TRIM", [("1", "1"), ("3", "3")], [("2", "W")], 7.62, True)
box("JACK", [("T", "T"), ("TN", "TN"), ("S", "S")], [], 7.62, True)
box("SPDT", [("2", "COM")], [("1", "1"), ("3", "3")], 7.62, True)
box("ROT12", [("C", "C")], [(str(i), str(i)) for i in range(1, 13)], 7.62, True)
box("LM13700", [("3", "+IN1"), ("4", "-IN1"), ("1", "IABC1"), ("2", "DB1"), ("7", "BIN1"), ("14", "+IN2"), ("13", "-IN2"), ("16", "IABC2"), ("15", "DB2"), ("10", "BIN2")],
    [("5", "OUT1"), ("8", "BOUT1"), ("12", "OUT2"), ("9", "BOUT2"), ("11", "V+"), ("6", "V-")], 10.16, True)
box("LDO", [("3", "IN")], [("2", "OUT"), ("1", "GND")], 7.62, True)
box("PICO", [(str(i), n) for i, n in ((1, "GP0"), (2, "GP1"), (4, "GP2"), (5, "GP3"), (6, "GP4"), (7, "GP5"), (9, "GP6"), (10, "GP7"), (11, "GP8"), (12, "GP9"), (14, "GP10"), (15, "GP11"), (16, "GP12"), (17, "GP13"), (19, "GP14"), (20, "GP15"), (3, "GND"), (8, "GND"), (13, "GND"), (18, "GND"))],
    [(str(i), n) for i, n in ((21, "GP16"), (22, "GP17"), (24, "GP18"), (25, "GP19"), (26, "GP20"), (27, "GP21"), (29, "GP22"), (30, "RUN"), (31, "GP26_A0"), (32, "GP27_A1"), (34, "GP28_A2"), (35, "ADC_VREF"), (36, "3V3"), (37, "3V3_EN"), (39, "VSYS"), (40, "VBUS"), (23, "GND"), (28, "GND"), (33, "AGND"), (38, "GND"))], 15.24, True)
box("CD4013", [("5", "D1"), ("3", "CLK1"), ("4", "R1"), ("6", "S1"), ("9", "D2"), ("11", "CLK2"), ("10", "R2"), ("8", "S2")],
    [("1", "Q1"), ("2", "~Q1"), ("13", "Q2"), ("12", "~Q2"), ("14", "VDD"), ("7", "VSS")], 10.16, True)
box("MUX8", [("13", "Y0"), ("14", "Y1"), ("15", "Y2"), ("12", "Y3"), ("1", "Y4"), ("5", "Y5"), ("2", "Y6"), ("4", "Y7"), ("11", "S0"), ("10", "S1"), ("9", "S2")],
    [("3", "Z"), ("6", "~E"), ("16", "VCC"), ("7", "VEE"), ("8", "GND")], 12.7, True)
box("MUX16", [("9", "I0"), ("8", "I1"), ("7", "I2"), ("6", "I3"), ("5", "I4"), ("4", "I5"), ("3", "I6"), ("2", "I7"), ("23", "I8"), ("22", "I9"), ("21", "I10"), ("20", "I11"), ("19", "I12"), ("18", "I13"), ("17", "I14"), ("16", "I15")],
    [("1", "COM"), ("10", "S0"), ("11", "S1"), ("14", "S2"), ("13", "S3"), ("15", "~E"), ("24", "VCC"), ("12", "GND")], 12.7, True)
box("HC165", [("11", "A"), ("12", "B"), ("13", "C"), ("14", "D"), ("3", "E"), ("4", "F"), ("5", "G"), ("6", "H"), ("10", "SER")],
    [("9", "QH"), ("7", "~QH"), ("1", "SH/~LD"), ("2", "CLK"), ("15", "CLK_INH"), ("16", "VCC"), ("8", "GND")], 12.7, True)
box("HC595", [("14", "SER"), ("11", "SRCLK"), ("12", "RCLK"), ("10", "~SRCLR"), ("13", "~OE")],
    [("15", "QA"), ("1", "QB"), ("2", "QC"), ("3", "QD"), ("4", "QE"), ("5", "QF"), ("6", "QG"), ("7", "QH"), ("9", "QH'"), ("16", "VCC"), ("8", "GND")], 12.7, True)
box("MCP4822", [("2", "~CS"), ("3", "SCK"), ("4", "SDI"), ("5", "~LDAC")], [("8", "VOUTA"), ("6", "VOUTB"), ("1", "VDD"), ("7", "VSS")], 10.16, True)
box("TACT", [("1", "1"), ("2", "2")], [("3", "3"), ("4", "4")], 7.62, True)
box("BAT54S", [("1", "A1"), ("2", "K2")], [("3", "COM")], 7.62, True)
box("MC1496", [("1", "SIG+"), ("4", "SIG-"), ("8", "CAR+"), ("10", "CAR-"), ("2", "GADJ"), ("3", "GADJ"), ("5", "BIAS")], [("6", "OUT+"), ("12", "OUT-"), ("14", "V-")], 10.16, True)
box("CONN2", [("1", "1"), ("2", "2")], [], 7.62, True)
box("DUALPNP", [("2", "B1"), ("5", "B2")], [("6", "C1"), ("1", "E1"), ("3", "C2"), ("4", "E2")], 7.62, True)
box("EURO10", [("1", "1"), ("3", "3"), ("5", "5"), ("7", "7"), ("9", "9")], [("2", "2"), ("4", "4"), ("6", "6"), ("8", "8"), ("10", "10")], 7.62, True)

def sym_def(name, prefix=""):
    s = SYM[name]
    W, H = s["W"], s["H"]
    full = (prefix + ":" if prefix else "") + name
    out = [f'(symbol {q(full)} (pin_names (offset 0.508){"" if s["names"] else " hide"}) (pin_numbers{"" if s["names"] else " hide"}) (exclude_from_sim no) (in_bom yes) (on_board yes)',
           f'  (property "Reference" "X" (at 0 {f(H/2 + 1.27)} 0) (effects (font (size 1.27 1.27))))',
           f'  (property "Value" {q(name)} (at 0 {f(-H/2 - 1.27)} 0) (effects (font (size 1.27 1.27))))',
           f'  (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
           f'  (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
           f'  (property "Description" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
           f'  (symbol "{name}_0_1" (rectangle (start {f(-W/2)} {f(H/2)}) (end {f(W/2)} {f(-H/2)}) (stroke (width 0.254) (type default)) (fill (type background))))',
           f'  (symbol "{name}_1_1"']
    for (num, nm, x, y, ang) in s["pins"]:
        out.append(f'    (pin passive line (at {f(x)} {f(y)} {ang}) (length 2.54) (name {q(nm)} (effects (font (size 1.0 1.0)))) (number {q(num)} (effects (font (size 1.0 1.0)))))')
    out.append("  )")
    out.append(")")
    return "\n".join(out)

lib = ['(kicad_symbol_lib (version 20231120) (generator "octavio_gen") (generator_version "8.0")']
for k in SYM:
    lib.append("  " + sym_def(k).replace("\n", "\n  "))
lib.append(")")
open(f"{OUT}/octavio_mu.kicad_sym", "w").write("\n".join(lib) + "\n")

# ------------------------------------------------------------------ schematic
SCH_UUID = U()
sch = [f'(kicad_sch (version 20231120) (generator "eeschema") (generator_version "8.0") (uuid {q(SCH_UUID)}) (paper "A2")',
       f'  (title_block (title "Octavio {M.NAME} - Eurorack") (company "Octavio / Sinecraft") (rev "{M.REV}") (comment 1 "{M.DESC}"))',
       '  (lib_symbols']
for k in SYM:
    sch.append("    " + sym_def(k, "octavio_mu").replace("\n", "\n    "))
sch.append("  )")

def snap(v):
    return round(v / 1.27) * 1.27

COLW = 30 * G
x_cur, y_cur = 20 * G, 16 * G
YMAX = 160 * G
for title, refs in BLOCKS:
    hb = sum(SYM[parts[r]["kind"]]["H"] + 3 * G for r in refs) + 4 * G
    if y_cur + min(hb, 60 * G) > YMAX:
        x_cur += COLW; y_cur = 16 * G
    sch.append(f'  (text {q(title)} (exclude_from_sim no) (at {f(x_cur - 6*G)} {f(y_cur)} 0) (effects (font (size 2.0 2.0) (thickness 0.4) bold) (justify left bottom)) (uuid {q(U())}))')
    y_cur += 3 * G
    for r in refs:
        p = parts[r]; s = SYM[p["kind"]]
        if y_cur + s["H"] > YMAX:
            x_cur += COLW; y_cur = 16 * G
        sx = snap(x_cur); sy = snap(y_cur + s["H"] / 2)
        sch.append(f'  (symbol (lib_id "octavio_mu:{p["kind"]}") (at {f(sx)} {f(sy)} 0) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid {q(U())})')
        sch.append(f'    (property "Reference" {q(r)} (at {f(sx)} {f(sy - s["H"]/2 - 1.27)} 0) (effects (font (size 1.27 1.27))))')
        sch.append(f'    (property "Value" {q(p["val"])} (at {f(sx)} {f(sy + s["H"]/2 + 1.27)} 0) (effects (font (size 1.27 1.27))))')
        sch.append(f'    (property "Footprint" {q(p["fp"])} (at {f(sx)} {f(sy)} 0) (effects (font (size 1.27 1.27)) hide))')
        sch.append(f'    (property "Datasheet" "" (at {f(sx)} {f(sy)} 0) (effects (font (size 1.27 1.27)) hide))')
        sch.append(f'    (property "Description" {q(p["mpn"])} (at {f(sx)} {f(sy)} 0) (effects (font (size 1.27 1.27)) hide))')
        sch.append(f'    (property "MPN" {q(p["mpn"])} (at {f(sx)} {f(sy)} 0) (effects (font (size 1.27 1.27)) hide))')
        for (num, nm, px, py, ang) in s["pins"]:
            sch.append(f'    (pin {q(num)} (uuid {q(U())}))')
        sch.append(f'    (instances (project {q(PROJ)} (path "/{SCH_UUID}" (reference {q(r)}) (unit 1))))')
        sch.append("  )")
        for (num, nm, px, py, ang) in s["pins"]:
            cxp, cyp = sx + px, sy - py
            net = p["pins"].get(num)
            if not net:
                sch.append(f'  (no_connect (at {f(cxp)} {f(cyp)}) (uuid {q(U())}))')
                continue
            if ang == 0:   # left-side pin, label to the left
                sch.append(f'  (label {q(net)} (at {f(cxp)} {f(cyp)} 180) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify right bottom)) (uuid {q(U())}))')
            else:
                sch.append(f'  (label {q(net)} (at {f(cxp)} {f(cyp)} 0) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify left bottom)) (uuid {q(U())}))')
        y_cur += s["H"] + 3 * G
    y_cur += 3 * G

NOTES = ["NOTES"] + M.NOTES
for i, t in enumerate(NOTES):
    sch.append(f'  (text {q(t)} (exclude_from_sim no) (at {f(x_cur + COLW)} {f(16*G + i*2*G)} 0) (effects (font (size 1.5 1.5)) (justify left bottom)) (uuid {q(U())}))')
sch.append('  (sheet_instances (path "/" (page "1")))')
sch.append(")")
open(f"{OUT}/{PROJ}.kicad_sch", "w").write("\n".join(sch) + "\n")

# ------------------------------------------------------------------ project + lib tables
open(f"{OUT}/{PROJ}.kicad_pro", "w").write(json.dumps({"meta": {"filename": f"{PROJ}.kicad_pro", "version": 1}}, indent=2))
open(f"{OUT}/sym-lib-table", "w").write('(sym_lib_table\n  (version 7)\n  (lib (name "octavio_mu")(type "KiCad")(uri "${KIPRJMOD}/octavio_mu.kicad_sym")(options "")(descr "Octavio MU symbols"))\n)\n')
open(f"{OUT}/fp-lib-table", "w").write('(fp_lib_table\n  (version 7)\n  (lib (name "octavio_mu")(type "KiCad")(uri "${KIPRJMOD}/octavio_mu.pretty")(options "")(descr "Octavio panel parts"))\n)\n')

# ------------------------------------------------------------------ BOM (JLCPCB format)
LCSC = {  # verified on jlcpcb.com / lcsc.com
    "TL074": "C12594", "BC847DS,115 (Nexperia, paire double)": "C549489",
    "QingPu WQP-PJ301M-12 (Thonkiconn)": "C9900080080", "POT-R09V-100K (9 mm vertical, B100k)": "C9900018037", "TL072CDR": "",
    "C&K T101MH9ABE (SPDT ON-ON, PC pin)": "C668578", "TL074CDR": "C12594",
}
rows = {}
for p in P:
    key = (p["val"], p["fp"], p["mpn"])
    rows.setdefault(key, []).append(p["ref"])
with open(f"{OUT}/{PROJ}-BOM-JLCPCB.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #", "Notes"])
    for (val, fp, mpn), refs in sorted(rows.items(), key=lambda kv: kv[1][0]):
        lc = LCSC.get(mpn) or LCSC.get(val, "")
        side = parts[refs[0]]["side"]
        tech = "THT (wave soldering)" if FP[fp]["attr"] == "through_hole" else "SMT bottom"
        note = (mpn + " - " if mpn else "") + tech
        if not lc:
            note += " - laisser JLC choisir (Basic de preference)"
        base = mpn.split(' (')[0] if mpn else ""
        comment = base if (FP[fp]["attr"] == "smd" and base and base.replace(",115","").startswith(val)) else (f"{val} {base}" if FP[fp]["attr"] == "smd" and base else val)
        if fp.startswith("Resistor"):
            comment = f"{val} 1% 0805"
        w.writerow([comment, ",".join(refs), fp.split(":")[1], lc, note])

json.dump({r: dict(X=p["X"], Y=p["Y"], rot=p["rot"], side=p["side"], fp=p["fp"]) for r, p in parts.items()},
          open(f"/home/claude/work/{MD}/placement.json", "w"), indent=1)
json.dump(dict(LOGO=LOGO, STRIP=STRIP, PANEL_HOLES=PANEL_HOLES, PANEL_TEXT=PANEL_TEXT, DIV=DIV, TICKS=TICKS), open(f"/home/claude/work/{MD}/panel.json", "w"))
print("ok", len(P), "parts", len(NETS) - 1, "nets")
