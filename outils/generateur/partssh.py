# Octavio S&H / LAG - sample & hold with its own noise and clock, plus a rise / fall lag. Eurorack 8 HP, all analog.
# S&H IN is normalled to the internal white noise, TRIG to the internal clock -> random voltages with nothing patched.
# GATE = S&H output above 0 V (random gates). LAG IN is normalled to the S&H output (smooth random).
import sys; sys.path.insert(0, "/home/claude/work")
from modbase import *

HP = 8
PANEL_W = 40.3
PANEL_H = 128.5
NAME = "S&H / LAG"; TITLE = "S&H / LAG"; REV = "0.1"; FOLDER = "SHLAG"; PROJ = "octavio-shlag"; SHORT = "shlag"
DESC = "Sample and hold (noise + clock normalled), random gate, rise / fall lag"
GRID = [(20, y) for y in (34, 58, 82)]
J1A = (20.15, 40.0)

cx = PANEL_W / 2
RATE = (12.0, 22.0)
CLKLED = (30.2, 12.6)
SWP = (30.2, 27.4)
RISE, FALL = (11.0, 52.5), (29.3, 52.5)
LAGLED = (cx, 45.6)
JX = (10.1, 30.2)
JY = (76.5, 87.5, 98.5, 109.5)

power()

# ---------------- NOISE : avalanche junction -> amplifier (level trimmer) ----------------
SEC[0] = "NOISE"
add(nxt("Q"), "BC847", "NPN", SOT23, "B", None, 0, {"1": "GND", "2": "NZ", "3": None}, "BC847C (jonction base-émetteur en avalanche = source de bruit)")
R("100k", "+12V", "NZ"); C("1u", "NZ", "NA", "X7R 0603 25 V"); R("100k", "NA", "GND")
opamp("NA", "NG", "WN_O")
add("RV4", "200k", "TRIM", TRIM, "B", None, 0, {"1": "WN_O", "2": "NG", "3": "NG"}, "Bourns 3314J-1-204E (niveau du bruit : 10 V crête à crête)")
R("1k", "NG", "NGC"); C("10u 25V", "NGC", "GND", "X5R/X7R 1206", C1206); C("22p", "WN_O", "NG")
R("1k", "WN_O", "NOISEJ")

# ---------------- CLOCK : triangle / square oscillator, RATE = A-taper pot (about 0.5 Hz .. 100 Hz) ----------------
SEC[0] = "CLOCK"
pot("RV1", "10k A", RATE, "GND", "RATEW", "SQ", "POT-R09V-10K A (9 mm vertical, log)")
opamp("GND", "INTN", "TRI")
R("100k", "RATEW", "INTN"); C("47n C0G", "INTN", "TRI", "C0G/NP0 0805", C0805)
R("22M", "SQ", "INTN")
opamp("SCH", "GND", "SQ")
R("100k", "TRI", "SCH"); R("200k", "SQ", "SCH")
R("10k", "SQ", "CLKL"); D("CLKL", "+12V"); D("GND", "CLKL")
opamp("CLKL", "CB", "CB")
R("1k", "CB", "CLOCKJ")
led("D10", CLKLED, "CB", "LED 3 mm ambre (CLOCK)")

# ---------------- S&H / T&H (JFET switch, C0G hold capacitor, JFET-input buffer) ----------------
SEC[0] = "SAMPLE & HOLD / TRACK & HOLD"
R("100k", "+12V", "REF"); R("15k", "REF", "GND"); C("100n", "REF", "GND")
R("10k", "TRIGJ", "TRGR"); R("100k", "TRGR", "GND")
opamp("TRGR", "REF", "TRC")
C("1n C0G", "TRC", "SHP", "C0G/NP0 0603"); R("100k", "SHP", "-12V"); D("-12V", "SHP")
opamp("SHP", "GND", "SHC")
add("SW1", "S&H / T&H", "SPDT", TOG, "F", SWP, 0, {"1": "SHC", "2": "SHCTL", "3": "TRC"}, TOGMPN + " : haut = S&H, bas = T&H")
opamp("SHINJ", "SHIN_B", "SHIN_B")
add(nxt("Q"), "MMBFJ112", "NPN", SOT23, "B", None, 0, {"1": "SHIN_B", "2": "HOLD", "3": "JG"}, "MMBFJ112 (JFET N, D-S-G)")
D("JG", "SHCTL"); R("1M", "JG", "HOLD")
C("100n C0G", "HOLD", "GND", "C0G/NP0 1206 (condensateur de maintien, très faible fuite)", C1206)
opamp("HOLD", "SH_O", "SH_O")
R("1k", "SH_O", "SHOUTJ")

# ---------------- GATE : S&H output > 0 V -> 0 / +11 V ----------------
SEC[0] = "RANDOM GATE"
opamp("SH_O", "GND", "GTC")
R("10k", "GTC", "GTL"); D("GTL", "+12V"); D("GND", "GTL")
opamp("GTL", "GB", "GB")
R("1k", "GB", "GATEJ")

# ---------------- LAG : comparator drives the cap through a diode + RISE or FALL pot, stops exactly on the input ----------------
SEC[0] = "LAG (RISE / FALL)"
opamp("LAGINJ", "LO", "LCMP")
D("LCMP", "LR1")
pot("RV2", "1M A", RISE, "LR1", "LR2", "LR2", "POT-R09V-1M A (9 mm vertical, log)")
R("1k", "LR2", "LAGC")
D("LF1", "LCMP")
pot("RV3", "1M A", FALL, "LF1", "LF2", "LF2", "POT-R09V-1M A (9 mm vertical, log)")
R("1k", "LF2", "LAGC")
C("2u2", "LAGC", "GND", "X7R 1206 25 V", C1206)
opamp("LAGC", "LO", "LO")
R("1k", "LO", "LAGOUTJ")
led("D11", LAGLED, "LO", "LED 3 mm rouge (LAG, positif)")

# ---------------- Jacks : 2 x 4 at the bottom, turned sideways (lugs inward) ----------------
SEC[0] = "JACKS"
jack("J2", "S&H IN", (JX[0], JY[0]), "SHINJ", "WN_O", 90); jack("J3", "TRIG", (JX[1], JY[0]), "TRIGJ", "CB", 270)
jack("J4", "NOISE", (JX[0], JY[1]), "NOISEJ", None, 90); jack("J5", "CLOCK", (JX[1], JY[1]), "CLOCKJ", None, 270)
jack("J6", "S&H OUT", (JX[0], JY[2]), "SHOUTJ", None, 90); jack("J7", "GATE", (JX[1], JY[2]), "GATEJ", None, 270)
jack("J8", "LAG IN", (JX[0], JY[3]), "LAGINJ", "SH_O", 90); jack("J9", "LAG OUT", (JX[1], JY[3]), "LAGOUTJ", None, 270)

BLOCKS = finish()

NOTES = ["- Bruit : jonction base-emetteur d'un BC847 en avalanche, amplifiee (RV4 = niveau, 10 V crete a crete).",
         "- Horloge : integrateur + bascule de Schmitt, RATE = pot 10k A sur le carre (environ 0,5 a 100 Hz), sortie 0 / +11 V.",
         "- S&H : impulsion d'environ 70 us a chaque front montant de TRIG ; T&H : suit tant que TRIG est haut. JFET MMBFJ112 + 100n C0G + tampon TL074.",
         "- Entrees vides : S&H IN = bruit blanc, TRIG = horloge interne, LAG IN = sortie S&H.",
         "- GATE : 0 / +11 V quand la sortie S&H est positive (porte aleatoire a 50 %).",
         "- LAG : comparateur -> diode -> RISE ou FALL (1M A) -> 2u2 ; s'arrete exactement sur l'entree (1 ms a quelques secondes).",
         "- -12V = bande rouge du cable."]

def panel_art(T, knob_scale, TICKS):
    T("SAMPLE & HOLD", cx, 8.6, 0.85, 0.15)
    T("RATE", RATE[0], RATE[1] - 9.4, 0.75, 0.13)
    scale(T, TICKS, RATE[0], RATE[1], ["0", "2", "4", "6", "8", "10"])
    T("CLOCK", CLKLED[0], CLKLED[1] + 3.6, 0.6, 0.12)
    T("S&H", SWP[0], SWP[1] - 5.6, 0.75, 0.13); T("T&H", SWP[0], SWP[1] + 5.6, 0.75, 0.13)
    T("LAG", cx, 40.2, 0.85, 0.15)
    T("RISE", RISE[0], RISE[1] - 9.4, 0.75, 0.13); T("FALL", FALL[0], FALL[1] - 9.4, 0.75, 0.13)
    scale(T, TICKS, RISE[0], RISE[1], ["0", "", "4", "6", "", "10"])
    scale(T, TICKS, FALL[0], FALL[1], ["0", "", "4", "6", "", "10"])
    
    for (lab, x, y) in (("S&H IN", JX[0], JY[0]), ("TRIG", JX[1], JY[0]), ("NOISE", JX[0], JY[1]), ("CLOCK", JX[1], JY[1]),
                        ("S&H OUT", JX[0], JY[2]), ("GATE", JX[1], JY[2]), ("LAG IN", JX[0], JY[3]), ("LAG OUT", JX[1], JY[3])):
        T(lab, x, y - 5.5, 0.75, 0.13)

DIV = [(1.2, 35.0, PANEL_W - 1.2, 35.0), (1.2, 69.4, PANEL_W - 1.2, 69.4), (cx, 69.4, cx, 116.5)]
