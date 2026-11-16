"""Specctra DSN export of an Octavio board (parts file + placement.json) for Freerouting, and SES import back
into the .kicad_pcb as segments and vias.  Usage :
    python3 dsn.py export <parts_module_dir> <parts_module> <placement.json> <out.dsn> <hp>
    python3 dsn.py import <parts_module_dir> <parts_module> <placement.json> <in.ses> <board.kicad_pcb>
"""
import sys, json, math, re, importlib
sys.path.insert(0, "/home/claude/work")
from kicadgen import FP, pad_abs

OX, OY = 100.0, 100.0
TRACK, CLEAR, PWR_TRACK = 0.25, 0.2, 0.45
VIA_D, VIA_DR = 0.6, 0.3
POWER = {"GND", "+12V", "-12V", "+12V_IN", "-12V_IN", "+5V", "3V3", "VSYS"}

def um(v):
    return int(round(v * 1000))

def load(mdir, mod, plp):
    sys.path.insert(0, mdir)
    m = importlib.import_module(mod)
    return m, json.load(open(plp))

def pads_of(p, d):
    fp = FP[d["fp"]]
    out = []
    for raw, (num, ax, ay, w, h, kind) in zip(fp["pads"], pad_abs(d["fp"], d["X"], d["Y"], d["rot"], d["side"])):
        net = p["pins"].get(num)
        shape = raw.get("shape", "rect")
        drill = raw.get("drill")
        out.append(dict(num=num, x=ax, y=ay, w=w, h=h, smd=kind == "smd", side=d["side"], shape=shape, drill=drill, net=net))
    return out

LAYERS = ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"]

def export(mdir, mod, plp, out, hp, nlayers="4"):
    LY = LAYERS if str(nlayers) == "4" else ["F.Cu", "B.Cu"]
    m, pl = load(mdir, mod, plp)
    W = float(hp) * 5.08 - 0.3
    x0, x1, y0, y1 = OX + 1.5, OX + W - 1.5, OY + 11.0, OY + 117.5
    stacks = {}
    def stack(pd):
        if pd["smd"]:
            lay = "B.Cu" if pd["side"] == "B" else "F.Cu"
            key = f"SMD_{lay}_{um(pd['w'])}x{um(pd['h'])}"
            stacks[key] = f'(padstack "{key}" (shape (rect {lay} {-um(pd["w"]/2)} {-um(pd["h"]/2)} {um(pd["w"]/2)} {um(pd["h"]/2)})) (attach off))'
        else:
            d = max(min(pd["w"], pd["h"]), 0.1)
            key = f"THT_{um(pd['w'])}x{um(pd['h'])}"
            if abs(pd["w"] - pd["h"]) < 1e-6 and pd["shape"] == "circle":
                shp = "".join(f"(shape (circle {L} {um(d)}))" for L in LY)
            else:
                shp = "".join(f'(shape (rect {L} {-um(pd["w"]/2)} {-um(pd["h"]/2)} {um(pd["w"]/2)} {um(pd["h"]/2)}))' for L in LY)
            stacks[key] = f'(padstack "{key}" {shp} (attach off))'
        return key
    images, places, nets = [], [], {}
    for p in m.P:
        d = pl[p["ref"]]
        pins = []
        for i, pd in enumerate(pads_of(p, d)):
            k = stack(pd)
            pid = f"{pd['num']}@{i}"
            pins.append(f'(pin "{k}" "{pid}" {um(pd["x"] - OX)} {-um(pd["y"] - OY)})')
            if pd["net"]:
                nets.setdefault(pd["net"], []).append(f'"{p["ref"]}"-"{pid}"')
        images.append(f'(image "IMG_{p["ref"]}" {" ".join(pins)})')
        places.append(f'(component "IMG_{p["ref"]}" (place "{p["ref"]}" 0 0 front 0))')
    vk = f"Via[0-1]_{um(VIA_D)}:{um(VIA_DR)}_um"
    stacks[vk] = f'(padstack "{vk}" ' + "".join(f"(shape (circle {L} {um(VIA_D)}))" for L in LY) + ' (attach off))'
    netl = [f'(net "{n}" (pins {" ".join(v)}))' for n, v in nets.items() if len(v) >= 2]
    pw = [f'"{n}"' for n in nets if n in POWER and len(nets[n]) >= 2]
    sig = [f'"{n}"' for n in nets if n not in POWER and len(nets[n]) >= 2]
    bx0, bx1, by0, by1 = um(x0 - OX), um(x1 - OX), -um(y0 - OY), -um(y1 - OY)
    dsn = f'''(pcb "octavio"
  (parser (string_quote ") (space_in_quoted_tokens on) (host_cad "KiCad's Pcbnew") (host_version "8.0"))
  (resolution um 10)
  (unit um)
  (structure
    {" ".join(f"(layer {L} (type signal) (property (index {i})))" for i, L in enumerate(LY))}
    (boundary (path pcb 0 {bx0} {by0} {bx1} {by0} {bx1} {by1} {bx0} {by1} {bx0} {by0}))
    (via "{vk}")
    (rule (width {um(TRACK)}) (clearance {um(CLEAR)}) (clearance {um(CLEAR)} (type smd_smd)))
  )
  (placement {" ".join(places)})
  (library {" ".join(images)} {" ".join(stacks.values())})
  (network {" ".join(netl)}
    (class "kicad_default" {" ".join(sig)} (circuit (use_via "{vk}")) (rule (width {um(TRACK)}) (clearance {um(CLEAR)})))
    (class "power" {" ".join(pw)} (circuit (use_via "{vk}")) (rule (width {um(PWR_TRACK)}) (clearance {um(CLEAR)})))
  )
  (wiring)
)
'''
    open(out, "w").write(dsn)
    print("dsn", len(netl), "nets", len(m.P), "parts")

def tok(s):
    return re.findall(r'\(|\)|"[^"]*"|[^\s()]+', s)

def parse(s):
    st = [[]]
    for t in tok(s):
        if t == "(":
            st.append([])
        elif t == ")":
            x = st.pop(); st[-1].append(x)
        else:
            st[-1].append(t.strip('"'))
    return st[0][0]

def find(node, name):
    for x in node:
        if isinstance(x, list) and x and x[0] == name:
            yield x

def importses(mdir, mod, plp, ses, board):
    s = parse(open(ses).read())
    routes = next(find(s, "routes"))
    res = next(find(routes, "resolution")); scale = {"um": 1000.0, "mm": 1.0, "mil": 1000 / 25.4}[res[1]] * float(res[2])
    no = next(find(routes, "network_out"))
    pcb = open(board).read()
    netnum = {n: int(i) for i, n in re.findall(r'^\s*\(net (\d+) "([^"]*)"\)', pcb, re.M)}
    out, nseg, nvia = [], 0, 0
    def P(x, y):
        return OX + float(x) / scale, OY - float(y) / scale
    import uuid
    for net in find(no, "net"):
        name = net[1]; nn = netnum.get(name, 0)
        for w in find(net, "wire"):
            path = next(find(w, "path"))
            lay, width = path[1], float(path[2]) / scale
            pts = [P(path[i], path[i + 1]) for i in range(3, len(path) - 1, 2)]
            for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                out.append(f'  (segment (start {ax:.4f} {ay:.4f}) (end {bx:.4f} {by:.4f}) (width {width:.3f}) (layer "{lay}") (net {nn}) (uuid "{uuid.uuid4()}"))'); nseg += 1
        for v in find(net, "via"):
            x, y = P(v[2], v[3])
            out.append(f'  (via (at {x:.4f} {y:.4f}) (size {VIA_D}) (drill {VIA_DR}) (layers "F.Cu" "B.Cu") (net {nn}) (uuid "{uuid.uuid4()}"))'); nvia += 1
    if "In1.Cu" not in pcb and any('"In1.Cu"' in o or '"In2.Cu"' in o for o in out):
        pcb = pcb.replace('(0 "F.Cu" signal) (31 "B.Cu" signal)', '(0 "F.Cu" signal) (1 "In1.Cu" signal) (2 "In2.Cu" signal) (31 "B.Cu" signal)', 1)
    pcb = re.sub(r'\n\s*\((segment|via) [^\n]*', '', pcb)          # drop an older routing
    i = pcb.rstrip().rfind(")")
    pcb = pcb[:i] + "\n".join(out) + "\n)\n"
    open(board, "w").write(pcb)
    print("imported", nseg, "segments", nvia, "vias")

if __name__ == "__main__":
    if sys.argv[1] == "export":
        export(*sys.argv[2:8])
    else:
        importses(*sys.argv[2:7])
