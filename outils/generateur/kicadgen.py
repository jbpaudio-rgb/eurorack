"""Minimal KiCad 8 file writer (footprints, symbols, schematic, PCB)."""
import uuid, math

def U():
    return str(uuid.uuid4())

def q(s):
    return '"' + str(s).replace('\\', '\\\\').replace('"', '\\"') + '"'

def f(v):
    s = f"{v:.4f}".rstrip('0').rstrip('.')
    return "0" if s in ("-0", "") else s

# ------------------------------------------------------------------ footprints
# pad: dict(num, kind 'smd'|'thru'|'npth', shape, x, y, w, h, drill, drill_oval=(w,h))
# gfx: list of ('line', x1,y1,x2,y2, layer) / ('rect', x1,y1,x2,y2, layer) / ('circle', cx,cy,r, layer)

def _smd(n, x, y, w, h, shape="roundrect"):
    return dict(num=n, kind="smd", shape=shape, x=x, y=y, w=w, h=h)

def _tht(n, x, y, d, drill, shape="circle", oval=None):
    return dict(num=n, kind="thru", shape=shape, x=x, y=y, w=d if not oval else oval[0] + 0.6,
                h=d if not oval else oval[1] + 0.6, drill=drill, oval=oval)

def _rect(x1, y1, x2, y2, layer="SilkS"):
    return [("line", x1, y1, x2, y1, layer), ("line", x2, y1, x2, y2, layer),
            ("line", x2, y2, x1, y2, layer), ("line", x1, y2, x1, y1, layer)]

FP = {}

def fp_2pad(name, dx, w, h, body):
    FP[name] = dict(pads=[_smd("1", -dx, 0, w, h), _smd("2", dx, 0, w, h)],
                    gfx=_rect(-body[0] / 2, -body[1] / 2, body[0] / 2, body[1] / 2, "Fab"), attr="smd", ref_y=-1.7)

fp_2pad("Resistor_SMD:R_0805_2012Metric", 0.9125, 1.025, 1.4, (2.0, 1.25))
fp_2pad("Capacitor_SMD:C_0805_2012Metric", 0.95, 1.0, 1.45, (2.0, 1.25))
fp_2pad("Resistor_SMD:R_0603_1608Metric", 0.775, 0.9, 0.95, (1.6, 0.8))
fp_2pad("Capacitor_SMD:C_0603_1608Metric", 0.775, 0.9, 0.95, (1.6, 0.8))
fp_2pad("Capacitor_SMD:C_1206_3216Metric", 1.475, 1.05, 1.75, (3.2, 1.6))
FP["Diode_SMD:D_SOD-123"] = dict(pads=[_smd("1", -1.65, 0, 0.9, 1.2), _smd("2", 1.65, 0, 0.9, 1.2)],
                                 gfx=_rect(-1.35, -0.8, 1.35, 0.8, "Fab") + [("line", -2.4, -1.0, -2.4, 1.0, "SilkS")],
                                 attr="smd", ref_y=-1.9)
FP["Diode_SMD:D_SMA"] = dict(pads=[_smd("1", -2.0, 0, 2.5, 1.8), _smd("2", 2.0, 0, 2.5, 1.8)],
                             gfx=_rect(-2.25, -1.4, 2.25, 1.4, "Fab") + [("line", -3.5, -1.5, -3.5, 1.5, "SilkS")],
                             attr="smd", ref_y=-2.5)
FP["Package_TO_SOT_SMD:SOT-23"] = dict(pads=[_smd("1", -1.1375, -0.95, 1.325, 0.6), _smd("2", -1.1375, 0.95, 1.325, 0.6),
                                             _smd("3", 1.1375, 0, 1.325, 0.6)],
                                       gfx=_rect(-0.65, -1.45, 0.65, 1.45, "Fab"), attr="smd", ref_y=-2.4)
FP["Package_TO_SOT_SMD:SOT-457"] = dict(pads=[_smd("1", -1.1375, -0.95, 1.325, 0.6), _smd("2", -1.1375, 0, 1.325, 0.6),
                                              _smd("3", -1.1375, 0.95, 1.325, 0.6), _smd("4", 1.1375, 0.95, 1.325, 0.6),
                                              _smd("5", 1.1375, 0, 1.325, 0.6), _smd("6", 1.1375, -0.95, 1.325, 0.6)],
                                        gfx=_rect(-0.8, -1.45, 0.8, 1.45, "Fab") + [("circle", -1.9, -1.6, 0.15, "SilkS")],
                                        attr="smd", ref_y=-2.5)

def soic(name, n):
    half = n // 2
    pads = []
    y0 = -(half - 1) * 1.27 / 2
    for i in range(half):
        pads.append(_smd(str(i + 1), -2.475, y0 + i * 1.27, 1.95, 0.6))
    for i in range(half):
        pads.append(_smd(str(half + i + 1), 2.475, -y0 - i * 1.27, 1.95, 0.6))
    L = half * 1.27 / 2 + 0.6
    FP[name] = dict(pads=pads, gfx=_rect(-1.95, -L, 1.95, L, "Fab") + [("circle", -3.6, y0 - 0.9, 0.2, "SilkS")],
                    attr="smd", ref_y=-L - 1.2)

soic("Package_SO:SOIC-14_3.9x8.7mm_P1.27mm", 14)
soic("Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", 8)
soic("Package_SO:SOIC-16_3.9x9.9mm_P1.27mm", 16)

# 2x5 IDC header, pin1 at origin, rows along +y (pins 1/2 in first row)
_idc = []
for r in range(5):
    _idc.append(_tht(str(2 * r + 1), 0, r * 2.54, 1.7, 1.0, "rect" if r == 0 else "circle"))
    _idc.append(_tht(str(2 * r + 2), 2.54, r * 2.54, 1.7, 1.0))
FP["Connector_IDC:IDC-Header_2x05_P2.54mm_Vertical"] = dict(
    pads=_idc, gfx=_rect(-3.18, -4.83, 5.72, 15.03, "SilkS") + [("line", -3.6, -1, -3.6, 1, "SilkS")],
    attr="through_hole", ref_y=-6.0)
FP["Potentiometer_THT:Potentiometer_Bourns_3362P_Vertical"] = dict(
    pads=[_tht("1", 0, 0, 1.5, 0.8, "rect"), _tht("2", 2.54, -2.54, 1.5, 0.8), _tht("3", 5.08, 0, 1.5, 0.8)],
    gfx=_rect(-0.9, -5.5, 5.98, 1.3, "SilkS"), attr="through_hole", ref_y=-6.6)
FP["LED_THT:LED_D3.0mm"] = dict(
    pads=[_tht("1", 0, 0, 1.8, 0.9, "rect"), _tht("2", 2.54, 0, 1.8, 0.9)],
    gfx=[("circle", 1.27, 0, 1.5, "Fab"), ("line", -0.25, -1.6, -0.25, 1.6, "SilkS")], attr="through_hole", ref_y=-2.5,
    panel_hole=3.2, hole_off=(1.27, 0))
# 1 pole / 12 position PCB rotary switch (Alpha SR16-style): 12 contacts on a circle + common. VERIFY against the chosen part.
import math as _mm
_rp = [_tht(str(i + 1), 7.0 * _mm.sin(_mm.radians(-165 + 30 * i)), 7.0 * _mm.cos(_mm.radians(-165 + 30 * i)) * -1 * -1, 1.8, 1.0) for i in range(12)]
_rp.append(_tht("C", 0, 3.0, 1.8, 1.0, "rect"))
FP["octavio_mu:Rotary_1P12T_Alpha_SR16"] = dict(
    pads=_rp, gfx=[("circle", 0, 0, 8.2, "SilkS"), ("circle", 0, 0, 4.7, "Fab")], attr="through_hole", ref_y=-9.5,
    panel_hole=9.6)
# SR16-type mini rotary switch, 1 pole 8 positions, PCB pins (16 mm body, M9x0.75 bushing, 10.5 mm deep).
# From the maker's drawing : 8 contacts on a 16 mm circle, 45 deg apart, first one 22.5 deg from the locating tab
# (tab side = +y), common 2.65 mm from the centre ; holes 1.2 mm ; panel hole 9.3 mm + 2.5 mm hole for the tab 7.5 mm below.
_sr = [_tht(str(k + 1), -8.0 * _mm.sin(_mm.radians(22.5 + 45 * k)), 8.0 * _mm.cos(_mm.radians(22.5 + 45 * k)), 2.0, 1.3) for k in range(8)]
_sr.append(_tht("C", -2.65, 0.0, 1.9, 1.3, "rect"))
FP["octavio_mu:Rotary_SR16_1P8T"] = dict(
    pads=_sr, gfx=[("circle", 0, 0, 8.0, "SilkS"), ("circle", 0, 0, 4.65, "Fab")], attr="through_hole", ref_y=-9.5,
    panel_hole=9.4, panel_extra=[(0.0, 7.5, 2.6)])
FP["octavio_mu:Trim_SMD_Bourns_3314J"] = dict(
    pads=[_smd("1", -1.25, 2.0, 1.0, 1.4), _smd("2", 0, -2.0, 1.4, 1.4), _smd("3", 1.25, 2.0, 1.0, 1.4)],
    gfx=_rect(-2.25, -2.4, 2.25, 2.4, "Fab"), attr="smd", ref_y=-3.4)
# Panel parts: origin = shaft / jack centre (aligned with panel holes)
FP["octavio_mu:Jack_3.5mm_Thonkiconn_PJ398SM"] = dict(
    pads=[_tht("S", 0, -4.92, 2.0, 1.3, "rect"), _tht("TN", 0, 3.38, 2.0, 1.3), _tht("T", 0, 6.48, 2.0, 1.3)],
    gfx=_rect(-4.5, -6.0, 4.5, 4.5, "SilkS") + [("circle", 0, 0, 3.0, "Fab")], attr="through_hole", ref_y=-7.0,
    panel_hole=6.2)
FP["octavio_mu:Pot_Alpha_9mm_Vertical"] = dict(
    pads=[_tht("1", -2.5, 7.0, 1.8, 1.0, "rect"), _tht("2", 0, 7.0, 1.8, 1.0), _tht("3", 2.5, 7.0, 1.8, 1.0),
          _tht("MP", -4.4, 0, 0, 0, "oval", oval=(1.2, 2.2)), _tht("MP", 4.4, 0, 0, 0, "oval", oval=(1.2, 2.2))],
    gfx=_rect(-4.9, -5.0, 4.9, 6.0, "SilkS") + [("circle", 0, 0, 3.5, "Fab")], attr="through_hole", ref_y=-6.2,
    panel_hole=7.2)
FP["octavio_mu:Toggle_SPDT_Dailywell_2MS1"] = dict(
    pads=[_tht("1", 0, -2.54, 1.8, 1.1, "rect"), _tht("2", 0, 0, 1.8, 1.1), _tht("3", 0, 2.54, 1.8, 1.1)],
    gfx=_rect(-4.0, -6.5, 4.0, 6.5, "SilkS") + [("circle", 0, 0, 3.0, "Fab")], attr="through_hole", ref_y=-7.5,
    panel_hole=6.5)

# Raspberry Pi Pico on 2x20 female headers (pin 1 top-left, USB up), rows 17.78 mm apart
_pk = []
for i in range(20):
    _pk.append(_tht(str(i + 1), -8.89, -24.13 + i * 2.54, 1.7, 1.0, "rect" if i == 0 else "circle"))
    _pk.append(_tht(str(40 - i), 8.89, -24.13 + i * 2.54, 1.7, 1.0))
FP["octavio_mu:RaspberryPi_Pico_Headers"] = dict(pads=_pk, gfx=_rect(-10.5, -25.5, 10.5, 25.5, "SilkS") + _rect(-4.0, -27.0, 4.0, -23.5, "SilkS"),
                                              attr="through_hole", ref_y=-27.5)
def soicw(name, n):
    half = n // 2
    pads = []
    y0 = -(half - 1) * 1.27 / 2
    for i in range(half):
        pads.append(_smd(str(i + 1), -4.65, y0 + i * 1.27, 2.0, 0.6))
    for i in range(half):
        pads.append(_smd(str(half + i + 1), 4.65, -y0 - i * 1.27, 2.0, 0.6))
    L = half * 1.27 / 2 + 0.6
    FP[name] = dict(pads=pads, gfx=_rect(-3.75, -L, 3.75, L, "Fab") + [("circle", -5.9, y0 - 0.9, 0.2, "SilkS")], attr="smd", ref_y=-L - 1.2)
soicw("Package_SO:SOIC-24W_7.5x15.4mm_P1.27mm", 24)
FP["Package_TO_SOT_SMD:SOT-223-3_TabPin2"] = dict(
    pads=[_smd("1", -2.3, 3.15, 1.0, 2.0), _smd("2", 0, 3.15, 1.0, 2.0), _smd("3", 2.3, 3.15, 1.0, 2.0), _smd("2", 0, -3.15, 3.3, 2.0)],
    gfx=_rect(-3.35, -1.8, 3.35, 1.8, "Fab"), attr="smd", ref_y=-4.8)
# 6 mm tactile switch, tall actuator through the panel (pins 1-2 / 3-4 connected inside)
FP["octavio_mu:Tactile_6mm_THT_Panel"] = dict(
    pads=[_tht("1", -3.25, -2.25, 1.8, 1.0, "rect"), _tht("2", 3.25, -2.25, 1.8, 1.0), _tht("3", -3.25, 2.25, 1.8, 1.0), _tht("4", 3.25, 2.25, 1.8, 1.0)],
    gfx=_rect(-3.1, -3.1, 3.1, 3.1, "SilkS") + [("circle", 0, 0, 1.75, "Fab")], attr="through_hole", ref_y=-4.5, panel_hole=5.0)


def _layers(side, pad):
    s = "F" if side == "F" else "B"
    if pad["kind"] == "smd":
        return f'"{s}.Cu" "{s}.Paste" "{s}.Mask"'
    if pad["kind"] == "npth":
        return '"*.Cu" "*.Mask"'
    return '"*.Cu" "*.Mask"'


def _pad_sexpr(p, side, rot, net=None, nets=None, mirror=False):
    y = -p["y"] if mirror else p["y"]
    if p["kind"] == "smd":
        s = f'(pad {q(p["num"])} smd {p["shape"]} (at {f(p["x"])} {f(y)} {f(rot)}) (size {f(p["w"])} {f(p["h"])}) (layers {_layers(side, p)})'
        if p["shape"] == "roundrect":
            s += " (roundrect_rratio 0.25)"
    else:
        dr = f'(drill oval {f(p["oval"][0])} {f(p["oval"][1])})' if p.get("oval") else f'(drill {f(p["drill"])})'
        shape = "oval" if p.get("oval") else p["shape"]
        s = f'(pad {q(p["num"])} thru_hole {shape} (at {f(p["x"])} {f(y)} {f(rot)}) (size {f(p["w"])} {f(p["h"])}) {dr} (layers "*.Cu" "*.Mask") (remove_unused_layers no)'
    if net:
        s += f' (net {nets[net]} {q(net)})'
    s += f' (uuid {q(U())}))'
    return s


def _gfx_sexpr(g, side, mirror=False):
    s = "F" if side == "F" else "B"
    def Y(v):
        return -v if mirror else v
    if g[0] == "line":
        _, x1, y1, x2, y2, L = g
        return f'(fp_line (start {f(x1)} {f(Y(y1))}) (end {f(x2)} {f(Y(y2))}) (stroke (width {0.12 if L=="SilkS" else 0.1}) (type solid)) (layer "{s}.{L}") (uuid {q(U())}))'
    if g[0] == "circle":
        _, cx, cy, r, L = g
        return f'(fp_circle (center {f(cx)} {f(Y(cy))}) (end {f(cx + r)} {f(Y(cy))}) (stroke (width 0.12) (type solid)) (fill none) (layer "{s}.{L}") (uuid {q(U())}))'
    raise ValueError(g)


def footprint_mod(name):
    """Standalone .kicad_mod (library form, front side)."""
    d = FP[name]
    short = name.split(":")[1]
    out = [f'(footprint {q(short)} (version 20240108) (generator "octavio_gen") (generator_version "8.0") (layer "F.Cu")',
           f'  (property "Reference" "REF**" (at 0 {f(d["ref_y"])} 0) (layer "F.SilkS") (uuid {q(U())}) (effects (font (size 1 1) (thickness 0.15))))',
           f'  (property "Value" {q(short)} (at 0 {f(-d["ref_y"])} 0) (layer "F.Fab") (uuid {q(U())}) (effects (font (size 1 1) (thickness 0.15))))',
           f'  (attr {d["attr"]})']
    for g in d["gfx"]:
        out.append("  " + _gfx_sexpr(g, "F"))
    for p in d["pads"]:
        out.append("  " + _pad_sexpr(p, "F", 0))
    out.append(")")
    return "\n".join(out) + "\n"


def footprint_pcb(name, ref, val, x, y, rot, side, pinnets, nets):
    d = FP[name]
    mirror = side == "B"
    L = "F" if side == "F" else "B"
    just = " (justify mirror)" if mirror else ""
    ry = -d["ref_y"] if mirror else d["ref_y"]
    out = [f'(footprint {q(name)} (layer "{L}.Cu") (uuid {q(U())}) (at {f(x)} {f(y)} {f(rot)})',
           f'  (property "Reference" {q(ref)} (at 0 {f(ry)} {f(rot)}) (layer "{L}.SilkS") (uuid {q(U())}) (effects (font (size 0.8 0.8) (thickness 0.12)){just}))',
           f'  (property "Value" {q(val)} (at 0 {f(-ry)} {f(rot)}) (layer "{L}.Fab") (uuid {q(U())}) (effects (font (size 0.8 0.8) (thickness 0.12)){just}))',
           f'  (attr {d["attr"]})']
    for g in d["gfx"]:
        out.append("  " + _gfx_sexpr(g, side, mirror))
    for p in d["pads"]:
        out.append("  " + _pad_sexpr(p, side, rot, pinnets.get(p["num"]), nets, mirror))
    out.append(")")
    return "\n".join(out)


def pad_abs(name, x, y, rot, side):
    """Absolute pad centres (for previews / checks)."""
    res = []
    t = math.radians(rot)
    for p in FP[name]["pads"]:
        px, py = p["x"], (-p["y"] if side == "B" else p["y"])
        ax = x + px * math.cos(t) + py * math.sin(t)
        ay = y - px * math.sin(t) + py * math.cos(t)
        w, h = (p["w"], p["h"]) if rot % 180 == 0 else (p["h"], p["w"])
        res.append((p["num"], ax, ay, w, h, p["kind"]))
    return res


def fp_bbox(name, x, y, rot, side, margin=0.25):
    pts = []
    for (_, ax, ay, w, h, _) in pad_abs(name, x, y, rot, side):
        pts += [(ax - w / 2, ay - h / 2), (ax + w / 2, ay + h / 2)]
    for g in FP[name]["gfx"]:
        if g[0] in ("line",) and g[5] in ("Fab", "SilkS"):
            for (gx, gy) in ((g[1], g[2]), (g[3], g[4])):
                gy = -gy if side == "B" else gy
                t = math.radians(rot)
                pts.append((x + gx * math.cos(t) + gy * math.sin(t), y - gx * math.sin(t) + gy * math.cos(t)))
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return (min(xs) - margin, min(ys) - margin, max(xs) + margin, max(ys) + margin)

# JST PH 2-pin vertical (spring tank cables : shielded wire soldered to an RCA plug)
FP["Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical"] = dict(
    pads=[_tht("1", 0, 0, 1.4, 0.75, "rect"), _tht("2", 2.0, 0, 1.4, 0.75)],
    gfx=_rect(-1.95, -1.7, 3.95, 2.8, "SilkS"), attr="through_hole", ref_y=-2.8)
