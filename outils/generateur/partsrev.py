# Octavio SPRING REVERB - driver + recovery for an Accutronics / Belton 3-spring tank, Eurorack 10 HP.
# DRIVE sets how hard the springs are hit (PEAK LED), TONE darkens the return, MIX crossfades dry / wet and is
# voltage controlled (MIX CV with attenuator) through a PNP pair splitting one current between two OTAs (LM13700).
# SEND / RETURN : effects loop on the wet path (RETURN is normalled to the tank).
import sys; sys.path.insert(0, "/home/claude/work")
from modbase import *

HP = 10
PANEL_W = 50.5
PANEL_H = 128.5
NAME = "SPRING REVERB"; TITLE = "REVERB"; REV = "0.1"; FOLDER = "SPRINGREVERB"; PROJ = "octavio-springreverb"; SHORT = "springreverb"
DESC = "Spring reverb (tank 4FB3C1B), DRIVE, TONE, voltage-controlled MIX, send / return"
GRID = [(x, y) for y in (32, 58) for x in (14, 37)]
J1A = (25.25, 70.0)

cx = PANEL_W / 2
DRK, TNK = (12.6, 22.0), (37.9, 22.0)
MXK, CVK = (12.6, 53.0), (37.9, 53.0)
PEAK = (cx, 21.0)
JX = (9.0, cx, 41.5)
JY = (95.5, 109.5)
POT100B = "POT-R09V-100K (9 mm vertical, B100k)"

power()

SEC[0] = "INPUT + DRIVE"
opamp("GND", "INN", "DRY")                              # DRY = -IN, 100k input
R("100k", "INJ", "INN"); R("100k", "DRY", "INN")
C("1u", "DRY", "DA", "X7R 0603 25 V"); R("22k", "DA", "DN")
opamp("GND", "DN", "DRV")                               # gain 0.2 .. 4.8
R("4k7", "DN", "DF")
pot("RV1", "100k A", DRK, "DF", "DRV", "DRV", "POT-R09V-100K A (9 mm vertical, log)")
C("22p C0G", "DRV", "DN", "C0G/NP0 0603")
R("1k", "DRV", "SENDJ")
led("D10", PEAK, "DRV", "LED 3 mm rouge (PEAK : s'allume quand les ressorts sont bien attaqués)")

SEC[0] = "TANK DRIVER + RECOVERY (NE5532)"
add("U3", "NE5532", "TL072", SOIC8, "B", None, 0,
    {"3": "DRV", "2": "TKD", "1": "TKD", "5": "TANKOUT", "6": "RN", "7": "REC", "8": "+12V", "4": "-12V"}, "NE5532DR (double ampli bas bruit, sortie 30 mA)")
C("100n", "+12V", "GND"); C("100n", "GND", "-12V")
R("47R", "TKD", "TANKIN")
add("J10", "TANK IN", "CONN2", JST2, "B", None, 0, {"1": "TANKIN", "2": "GND"}, "JST PH 2 broches (câble blindé vers la fiche RCA IN de la cuve)")
add("J11", "TANK OUT", "CONN2", JST2, "B", None, 0, {"1": "TANKOUT", "2": "GND"}, "JST PH 2 broches (câble blindé vers la fiche RCA OUT de la cuve)")
R("47k", "TANKOUT", "GND")
R("100k", "REC", "RN"); C("100p C0G", "REC", "RN", "C0G/NP0 0603")
R("1k", "RN", "RNC"); C("10u 25V", "RNC", "GND", "X5R/X7R 1206", C1206)

SEC[0] = "TONE + RETURN"
C("1u", "REC", "RA", "X7R 0603 25 V"); R("10k", "RA", "TN")
opamp("GND", "TN", "WETA")
R("22k", "WETA", "TN"); C("4n7 C0G", "TN", "TC", "C0G/NP0 0603")
pot("RV2", "100k B", TNK, "TC", "WETA", "WETA", POT100B)
R("1M", "RETJ", "GND")
opamp("RETJ", "WB", "WB")
R("1k", "WB", "WETJ")

SEC[0] = "MIX CONTROL (PNP PAIR)"
pot("RV3", "10k B", MXK, "-12V", "MXW", "+12V", "POT-R09V-10K B (9 mm vertical)")
pot("RV4", "100k B", CVK, "GND", "CVW", "MIXCVJ", POT100B)
opamp("GND", "MSN", "MCTL")
R("100k", "MXW", "MSN"); R("100k", "CVW", "MSN"); R("47k", "MCTL", "MSN")
R("100k", "MCTL", "PB1"); R("2k2", "PB1", "GND"); R("2k2", "PB2", "GND")
add("Q1", "BCM857DS", "DUALPNP", SOT457, "B", None, 0,
    {"1": "TAIL", "2": "PB1", "3": "IAD", "4": "TAIL", "5": "PB2", "6": "IAW"}, "BCM857DS,115 (Nexperia, paire PNP appairée)")
R("56k", "+12V", "TAIL")

SEC[0] = "VCA CROSSFADE (LM13700)"
add("U4", "LM13700", "LM13700", SOIC16, "B", None, 0,
    {"1": "IAW", "2": None, "3": "OWP", "4": "OWM", "5": "OTAS", "6": "-12V", "7": "-12V", "8": None,
     "9": None, "10": "-12V", "11": "+12V", "12": "OTAS", "13": "ODM", "14": "ODP", "15": None, "16": "IAD"}, "LM13700MX/NOPB")
C("100n", "+12V", "GND"); C("100n", "GND", "-12V")
R("220k", "WB", "OWP"); R("470R", "OWP", "GND"); R("470R", "OWM", "GND")
R("220k", "DRY", "ODP"); R("470R", "ODP", "GND"); R("470R", "ODM", "GND")
opamp("GND", "OTAS", "MIXO")
R("120k", "MIXO", "OTAS"); C("22p C0G", "MIXO", "OTAS", "C0G/NP0 0603")
R("1k", "MIXO", "OUTJ")

SEC[0] = "JACKS"
jack("J2", "IN", (JX[0], JY[0]), "INJ"); jack("J3", "SEND", (JX[1], JY[0]), "SENDJ"); jack("J4", "RETURN", (JX[2], JY[0]), "RETJ", "WETA")
jack("J5", "MIX CV", (JX[0], JY[1]), "MIXCVJ"); jack("J6", "WET", (JX[1], JY[1]), "WETJ"); jack("J7", "OUT", (JX[2], JY[1]), "OUTJ")

BLOCKS = finish()

NOTES = ["- Cuve conseillee : Accutronics 4FB3C1B (longue, 3 ressorts, entree 1475 ohms, sortie 2250 ohms, entree isolee / sortie a la masse).",
         "- Driver : NE5532 en suiveur, 47 ohms -> bobine d'entree (jusqu'a ~7 mA). Recuperation : NE5532 gain x101.",
         "- TONE : passe-bas variable (22k // 4n7 + pot 100k) ; a fond = brillant, au minimum = sombre (~1,5 kHz).",
         "- MIX : la paire PNP BCM857DS partage ~200 uA entre les deux OTA du LM13700 (sec / humide) ; MIX + MIX CV (attenuateur) pilotent les bases.",
         "- SEND = signal qui attaque la cuve ; RETURN remplace le retour de la cuve (normalise dessus) -> boucle d'effet.",
         "- La cuve se fixe dans le boitier (pas sur le module) ; deux cables blindes RCA -> JST PH.",
         "- -12V = bande rouge du cable."]

def panel_art(T, knob_scale, TICKS):
    T("SPRING TANK", cx, 8.4, 0.85, 0.15)
    T("DRIVE", DRK[0], DRK[1] - 9.4, 0.75, 0.13); T("TONE", TNK[0], TNK[1] - 9.4, 0.75, 0.13)
    scale(T, TICKS, DRK[0], DRK[1], ["0", "", "4", "6", "", "10"])
    scale(T, TICKS, TNK[0], TNK[1], [""] * 6)
    T("DARK", TNK[0] - 7.4, TNK[1] + 8.6, 0.6, 0.12); T("BRIGHT", TNK[0] + 7.0, TNK[1] + 8.6, 0.6, 0.12)
    T("PEAK", PEAK[0], PEAK[1] + 3.6, 0.6, 0.12)
    T("MIX", MXK[0], MXK[1] - 9.4, 0.75, 0.13); T("MIX CV", CVK[0], CVK[1] - 9.4, 0.75, 0.13)
    scale(T, TICKS, MXK[0], MXK[1], [""] * 11, r1=6.0, r2=6.8)
    T("DRY", MXK[0] - 7.2, MXK[1] + 8.6, 0.6, 0.12); T("WET", MXK[0] + 7.2, MXK[1] + 8.6, 0.6, 0.12)
    scale(T, TICKS, CVK[0], CVK[1], ["0", "", "4", "6", "", "10"])
    for (lab, x, y) in (("IN", JX[0], JY[0]), ("SEND", JX[1], JY[0]), ("RETURN", JX[2], JY[0]),
                        ("MIX CV", JX[0], JY[1]), ("WET", JX[1], JY[1]), ("OUT", JX[2], JY[1])):
        T(lab, x, y - 6.0, 0.75, 0.13)

DIV = [(1.2, 36.0, PANEL_W - 1.2, 36.0), (1.2, 82.5, PANEL_W - 1.2, 82.5)]
