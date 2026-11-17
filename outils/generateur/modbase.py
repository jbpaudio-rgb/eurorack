# Shared helpers for the parts lists of the newer ocTavio modules (one module per process).
import math as _m
P = []
SEC = ["POWER"]
R0603 = "Resistor_SMD:R_0603_1608Metric"
C0603 = "Capacitor_SMD:C_0603_1608Metric"
C0805 = "Capacitor_SMD:C_0805_2012Metric"
C1206 = "Capacitor_SMD:C_1206_3216Metric"
SOD = "Diode_SMD:D_SOD-123"
POT = "octavio_mu:Pot_Alpha_9mm_Vertical"
TRIM = "octavio_mu:Trim_SMD_Bourns_3314J"
JFP = "octavio_mu:Jack_3.5mm_Thonkiconn_PJ398SM"
JMPN = "QingPu WQP-PJ301M-12 (Thonkiconn)"
TOG = "octavio_mu:Toggle_SPDT_Dailywell_2MS1"
LED = "LED_THT:LED_D3.0mm"
SOIC8 = "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm"
SOIC14 = "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm"
SOIC16 = "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm"
SOT23 = "Package_TO_SOT_SMD:SOT-23"
SOT457 = "Package_TO_SOT_SMD:SOT-457"
JST2 = "Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical"
TOGMPN = "Dailywell 2MS1T1B1M2QES (SPDT ON-ON)"

def add(ref, val, kind, fp, side, pos, rot, pins, mpn=""):
    P.append(dict(ref=ref, val=val, kind=kind, fp=fp, side=side, pos=pos, rot=rot, pins=pins, mpn=mpn, sec=SEC[0]))

cnt = {}
def nxt(p):
    cnt[p] = cnt.get(p, 0) + 1
    return f"{p}{cnt[p]}"
def R(val, a, b, mpn=""):
    add(nxt("R"), val, "R", R0603, "B", None, 0, {"1": a, "2": b}, mpn)
def C(val, a, b, mpn="", fp=None):
    add(nxt("C"), val, "C", fp or C0603, "B", None, 0, {"1": a, "2": b}, mpn)
def D(a, k):
    add(nxt("D"), "1N4148W", "D", SOD, "B", None, 0, {"1": k, "2": a}, "1N4148W")
def pot(ref, val, pos, p1, w, p3, mpn):
    add(ref, val, "POT", POT, "F", pos, 0, {"1": p1, "2": w, "3": p3}, mpn)
def jack(ref, lab, pos, t, tn=None, rot=0):
    add(ref, lab, "JACK", JFP, "F", pos, rot, {"T": t, "TN": tn, "S": "GND"}, JMPN)
def led(ref, pos, drv, mpn, rv="2k2"):
    add(ref, "LED", "D", LED, "F", (pos[0] - 1.27, pos[1]), 0, {"1": "GND", "2": drv + "_A"}, mpn)
    R(rv, drv, drv + "_A")

TL = []
SECT = [("3", "2", "1"), ("5", "6", "7"), ("10", "9", "8"), ("12", "13", "14")]
free = []
def opamp(plus, minus, out):
    if not free:
        TL.append({"4": "+12V", "11": "-12V"})
        free.extend((len(TL) - 1, s) for s in range(4))
    i, s = free.pop(0)
    p, m, o = SECT[s]
    TL[i][p] = plus; TL[i][m] = minus; TL[i][o] = out

def power():
    add("J1", "Eurorack 2x5", "EURO10", "Connector_IDC:IDC-Header_2x05_P2.54mm_Vertical", "B", None, 0,
        {"1": "-12V_IN", "2": "-12V_IN", "3": "GND", "4": "GND", "5": "GND", "6": "GND", "7": "GND", "8": "GND", "9": "+12V_IN", "10": "+12V_IN"},
        "Shrouded header 2x5 2.54 mm")
    cnt["J"] = 1
    add(nxt("D"), "SS14", "D", "Diode_SMD:D_SMA", "B", None, 0, {"1": "+12V", "2": "+12V_IN"}, "SS14 (40 V 1 A Schottky)")
    add(nxt("D"), "SS14", "D", "Diode_SMD:D_SMA", "B", None, 0, {"1": "-12V_IN", "2": "-12V"}, "SS14 (40 V 1 A Schottky)")
    C("10u 25V", "+12V", "GND", "X5R/X7R 1206", C1206); C("10u 25V", "GND", "-12V", "X5R/X7R 1206", C1206)

def finish(first_u=1):
    SEC[0] = "OP-AMPS + DECOUPLING"
    for i, pins in enumerate(TL):
        for s, (p, m, o) in enumerate(SECT):
            if p not in pins:
                pins[p] = "GND"; pins[m] = f"UNUSED{i}{s}"; pins[o] = f"UNUSED{i}{s}"
        add(f"U{first_u + i}", "TL074", "TL074", SOIC14, "B", None, 0, pins, "TL074CDR")
        C("100n", "+12V", "GND"); C("100n", "GND", "-12V")
    blocks = []
    for p in P:
        b = next((b for b in blocks if b[0] == p["sec"]), None)
        if not b:
            b = (p["sec"], []); blocks.append(b)
        b[1].append(p["ref"])
    return blocks

def scale(T, TICKS, kx, ky, labels, r_num=9.6, r1=6.0, r2=7.0, size=0.8):
    n = len(labels)
    for k, lab in enumerate(labels):
        ang = _m.radians(-135 + k * 270 / (n - 1))
        if lab: T(lab, kx + r_num * _m.sin(ang), ky - r_num * _m.cos(ang) + 0.1, size, 0.14)
        TICKS.append((kx + r1 * _m.sin(ang), ky - r1 * _m.cos(ang), kx + r2 * _m.sin(ang), ky - r2 * _m.cos(ang), 0.2))
