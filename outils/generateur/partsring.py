# Octavio RING MOD - four-quadrant multiplier (MC1496 Gilbert cell), Eurorack 8 HP.
# X = signal, Y = carrier. Y LEVEL goes from clean multiplication (low) to switching / square-ish ring tone (high).
# Y IN is normalled to +5 V : with nothing in Y the module is a plain amplifier / VCA for X (Y LEVEL = gain).
# MIX crossfades the dry X and the ring product ; RING is the product alone.
import sys; sys.path.insert(0, "/home/claude/work")
from modbase import *

HP = 8
PANEL_W = 40.3
PANEL_H = 128.5
NAME = "RING MOD"; TITLE = "RING MOD"; REV = "0.1"; FOLDER = "RINGMOD"; PROJ = "octavio-ringmod"; SHORT = "ringmod"
DESC = "Four-quadrant ring modulator (MC1496), X / Y levels, dry / ring mix, Y normalled to +5 V"
GRID = [(20, y) for y in (40, 66)]
J1A = (20.15, 30.0)

cx = PANEL_W / 2
XK, YK = (11.0, 22.0), (29.3, 22.0)
MIXK = (cx, 54.0)
OUTLED = (33.2, 66.0)
JX = (10.1, 30.2)
JY = (95.5, 109.5)
POT100 = "POT-R09V-100K (9 mm vertical, B100k)"

power()

SEC[0] = "+5 V NORMAL + CARRIER BIAS"
R("14k", "+12V", "REF5"); R("10k", "REF5", "GND"); C("1u", "REF5", "GND", "X7R 0603 25 V")
R("1k3", "+12V", "VB"); R("1k", "VB", "GND"); C("10u 25V", "VB", "GND", "X5R/X7R 1206", C1206)

SEC[0] = "X (SIGNAL) INPUT"
pot("RV1", "100k B", XK, "GND", "XW", "XINJ", POT100)
opamp("XW", "XB", "XB")
R("10k", "XB", "SIGP"); R("1k", "SIGP", "GND")
R("1k", "SIGM", "GND")
add("RV4", "100k", "TRIM", TRIM, "B", None, 0, {"1": "+12V", "2": "CNW", "3": "-12V"}, "Bourns 3314J-1-104E (CARRIER NULL : Y passe sans X)")
R("470k", "CNW", "SIGM")

SEC[0] = "Y (CARRIER) INPUT"
pot("RV2", "100k B", YK, "GND", "YW", "YINJ", POT100)
opamp("YW", "YB", "YB")
R("33k", "YB", "CARP"); R("1k", "CARP", "VB")
R("33k", "CARM", "GND"); R("1k", "CARM", "VB")
add("RV5", "100k", "TRIM", TRIM, "B", None, 0, {"1": "+12V", "2": "SNW", "3": "-12V"}, "Bourns 3314J-1-104E (SIGNAL NULL : X passe sans Y)")
R("1M", "SNW", "CARM")

SEC[0] = "MULTIPLIER (MC1496)"
add("U2", "MC1496", "MC1496", SOIC14, "B", None, 0,
    {"1": "SIGP", "2": "GA", "3": "GB", "4": "SIGM", "5": "BIAS", "6": "OP", "7": None, "8": "CARP", "9": None,
     "10": "CARM", "11": None, "12": "OM", "13": None, "14": "-12V"}, "MC1496DR2G (onsemi, SOIC-14)")
R("1k", "GA", "GB")
R("10k", "BIAS", "GND")
R("3k9", "+12V", "OP"); R("3k9", "+12V", "OM")
C("100n", "-12V", "GND")
opamp("DP", "DN", "RINGO")
R("10k", "OM", "DP"); R("15k", "DP", "GND")
R("10k", "OP", "DN"); R("15k", "RINGO", "DN"); C("100p C0G", "RINGO", "DN", "C0G/NP0 0603")
R("1k", "RINGO", "RINGJ")

SEC[0] = "MIX + OUT"
pot("RV3", "10k B", MIXK, "XB", "MXW", "RINGO", "POT-R09V-10K B (9 mm vertical)")
opamp("MXW", "MXO", "MXO")
R("1k", "MXO", "OUTJ")
led("D10", OUTLED, "MXO", "LED 3 mm bicolore 2 pattes rouge / vert (rouge = +, vert = -)")

SEC[0] = "JACKS"
jack("J2", "X IN", (JX[0], JY[0]), "XINJ")
jack("J3", "Y IN", (JX[1], JY[0]), "YINJ", "REF5")
jack("J4", "RING", (JX[0], JY[1]), "RINGJ")
jack("J5", "OUT", (JX[1], JY[1]), "OUTJ")

BLOCKS = finish(first_u=3)

NOTES = ["- Multiplicateur MC1496 : paire basse = X (gain 1k entre 2 et 3), paire haute = Y (porteuse) polarisee a +5,2 V, courant 1 mA (10k sur la broche 5).",
         "- Y LEVEL bas : multiplication propre ; Y LEVEL haut : la paire haute commute (son plus dur, facon modulateur a diodes).",
         "- Y IN vide = +5 V : le module devient un ampli / VCA pour X (Y LEVEL = gain).",
         "- Reglage : RV4 CARRIER NULL (Y seul, X a zero -> minimum en sortie), RV5 SIGNAL NULL (X seul, Y debranche et Y LEVEL a zero -> minimum).",
         "- MIX : fondu sec (X) -> produit ; RING = produit seul ; LED bicolore sur OUT.",
         "- -12V = bande rouge du cable."]

def panel_art(T, knob_scale, TICKS):
    T("LEVELS", cx, 8.6, 0.85, 0.15)
    T("X", XK[0], XK[1] - 9.4, 0.75, 0.13); T("Y", YK[0], YK[1] - 9.4, 0.75, 0.13)
    scale(T, TICKS, XK[0], XK[1], ["0", "", "4", "6", "", "10"])
    scale(T, TICKS, YK[0], YK[1], ["0", "", "4", "6", "", "10"])
    T("SIGNAL", XK[0], XK[1] + 9.6, 0.6, 0.12); T("CARRIER", YK[0], YK[1] + 9.6, 0.6, 0.12)
    T("MIX", cx, 40.2, 0.85, 0.15)
    scale(T, TICKS, MIXK[0], MIXK[1], [""] * 11, r1=6.0, r2=6.8)
    T("DRY", MIXK[0] - 9.0, MIXK[1] + 8.4, 0.75, 0.13); T("RING", MIXK[0] + 9.0, MIXK[1] + 8.4, 0.75, 0.13)
    T("OUT", OUTLED[0], OUTLED[1] + 3.6, 0.6, 0.12)
    for (lab, x, y) in (("X IN", JX[0], JY[0]), ("Y IN", JX[1], JY[0]), ("RING", JX[0], JY[1]), ("OUT", JX[1], JY[1])):
        T(lab, x, y - 6.0, 0.75, 0.13)

DIV = [(1.2, 35.0, PANEL_W - 1.2, 35.0), (1.2, 82.5, PANEL_W - 1.2, 82.5), (cx, 82.5, cx, 116.5)]
