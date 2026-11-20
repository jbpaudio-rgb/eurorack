"""ocTavio SEMI - STATE VARIABLE 12 dB (Oberheim SEM style mode : LP -> NOTCH -> HP, BP switch).
SPICE netlist of the circuit, with the sliders as parameters. Used by test_circuits.py.

Signal (all levels Eurorack) :
  U1A  inverting summer : HP = -(IN + LP + d*BP)          R1 20k (IN), R2 20k (LP), R3 10k (damping), R4 20k feedback,
                          D1/D2 BZT52C5V1 back to back + R25 4.7k from BP : extra damping above ~5.7 V = the self-oscillation stays near +/-6 V
  OTA1 (LM13700 A) + C1 470p + U1B follower : BP = integral of HP     input divider R5 22k / R6 220, R7 220 on the - input
  OTA2 (LM13700 B) + C2 470p + U1C follower : LP = integral of BP     R8 22k / R9 220, R10 220
  RESONANCE slider RV2 10k B : BP on the bottom end, GND on the top, wiper -> R3 : damping 2 (Q 0.5) -> 0
  R23 20k / R24 100 : a little BP on the + input of U1A = slightly negative damping at the top of RESONANCE -> sure self-oscillation
  MODE slider RV3 10k B between LP (bottom) and HP (top), wiper = LP / NOTCH / HP ; SW1 BP switch picks BP instead
  U1D inverting x1 (R11 20k, R12 20k) -> R13 1k -> OUT
Frequency :
  U2A summer : FREQ slider RV1 10k B (0..12 V) via R14 158k, ENV (jack -> ENV slider RV4 100k A) via R15 165k,
               MOD (jack -> MOD slider RV5 100k B) via R16 267k, offset R17 357k from -12 V, R18 100k feedback
  R19 4.12k / R20 100 divider -> base of Q1b (BCM857DS) ; Q1a reference : base GND, collector held at 0 V by U2B,
  R21 1.2M to -12 V -> Iref 10 uA ; U2B drives the common emitters through R22 1k, C3 100p
  Q1b collector -> IABC of both OTAs tied together (same die : the current splits evenly)
  -> about 20 Hz (FREQ 0) to 20 kHz (FREQ 10), ENV 0.8 oct/V and MOD 0.5 oct/V at full slider.
"""
import os, sys
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(H, '..', '..', 'outils', 'spice'))
from kicad2spice import MODELS

def pot(name, a, w, b, R, x, log=False):
    x = min(max(x, 0.001), 0.999)
    if log: x = min(max((100 ** x - 1) / 99, 0.0005), 0.999)
    return f"R{name}a {a} {w} {R * x:.6g}\nR{name}b {w} {b} {R * (1 - x):.6g}\n"

def netlist(freq=0.5, reso=0.0, mode=0.0, bp=False, env_amt=0.0, mod_amt=0.0, vin='DC 0', venv='DC 0', vmod='DC 0', analysis='', probes=''):
    n = MODELS + "\n* ---- SVF\nVP P12 0 DC 12\nVM M12 0 DC -12\n"
    n += f"VIN IN 0 {vin}\nVENV ENVJ 0 {venv}\nVMOD MODJ 0 {vmod}\n"
    # summer / damping
    n += "R1 IN SUMN 20k\nR2 LP SUMN 20k\nR3 DW SUMN 10k\nR4 SUMN HP 20k\nD1 ZK BP DZ5V1\nD2 ZK ZL DZ5V1\nR25 ZL SUMN 4.7k\n"
    n += "R23 BP SUMP 20k\nR24 SUMP 0 100\nXU1A SUMP SUMN HP P12 M12 TL07X\n"
    n += pot('RV2', 'BP', 'DW', '0', 10e3, reso)
    # integrators (LM13700 pins : inp inn iabc db bin bout out vp vn)
    n += "R5 HP O1P 22k\nR6 O1P 0 220\nR7 O1N 0 220\nXOTA1 O1P O1N IABC NC1 NC2 NC3 C1N P12 M12 LM13700H\nC1 C1N 0 470p\nXU1B C1N BP BP P12 M12 TL07X\n"
    n += "R8 BP O2P 22k\nR9 O2P 0 220\nR10 O2N 0 220\nXOTA2 O2P O2N IABC NC4 NC5 NC6 C2N P12 M12 LM13700H\nC2 C2N 0 470p\nXU1C C2N LP LP P12 M12 TL07X\n"
    # mode
    n += pot('RV3', 'LP', 'MW', 'HP', 10e3, mode)
    n += f"RSW1 {'BP' if bp else 'MW'} SEL 0.01\nR11 SEL ON 20k\nR12 ON OB 20k\nXU1D 0 ON OB P12 M12 TL07X\nR13 OB OUT 1k\nRL OUT 0 100k\n"
    # frequency CV
    n += pot('RV1', '0', 'FW', 'P12', 10e3, freq)
    n += pot('RV4', '0', 'EW', 'ENVJ', 100e3, env_amt, log=True) + pot('RV5', '0', 'MW5', 'MODJ', 100e3, mod_amt)
    n += "R14 FW CVN 158k\nR15 EW CVN 165k\nR16 MW5 CVN 267k\nR17 M12 CVN 357k\nR18 CVN CVO 100k\nXU2A 0 CVN CVO P12 M12 TL07X\n"
    n += "R19 CVO QB 4.12k\nR20 QB 0 100\n"
    n += "Q1a QRC 0 QE BC857\nQ1b IABC QB QE BC857\nR21 QRC M12 1.2Meg\nC3 QE_D QRC 100p\nXU2B 0 QRC QE_D P12 M12 TL07X\nR22 QE_D QE 1k\n"
    n += analysis + "\n" + probes + "\n.options method=gear reltol=1e-4 abstol=1e-12 vntol=1e-6 itl4=200\n.end\n"
    return n
