"""ocTavio SEMI - KEYBOARD · MIDI section and speaker : analog parts around the RP2040 (Raspberry Pi Pico).

MIDI IN (3.5 mm TRS type A : tip = MIDI pin 5, ring = pin 4)
  ring -> R1 220 -> H11L1 LED anode (pin 1) ; LED cathode (pin 2) -> tip ; D1 1N4148 reverse across the LED
  H11L1 (Schmitt-trigger opto, works from 3 V) : pin 6 = +3.3 V (100n), pin 4 (out) R3 1k pull-up to +3.3 V -> Pico GP1 (UART0 RX)
MIDI OUT (3.5 mm TRS type A) : +3.3 V -> R4 33 -> ring ; Pico GP0 (UART0 TX) -> R5 10 -> tip   (MIDI 1.0 3.3 V specification)
USB-C : Pico USB (USB-MIDI, class compliant) ; 5.1k CC pull-downs ; VBUS -> Pico VBUS (power from the computer is not needed)
Power : +12 V -> 78L05 -> Pico VSYS (through the Pico's own Schottky), 3.3 V from the Pico regulator
DACs : 2 x MCP4822 (12 bit, internal 2.048 V reference, gain x2 = 0..4.095 V), SPI0 (GP2 SCK, GP3 MOSI, GP5 / GP6 CS)
  pitch : U3A  CV = 2.441 x VDAC - 3.6 V   (R6 10k, R7 14.4k, LM4040-2.5 reference through R8 10k)  -> -3.6 .. +6.4 V ;
          the firmware stores a 2-point calibration (notes C1 and C6) in flash
  VEL, MOD : U3B / U3C non-inverting x2.441 (R9 / R11 10k, R10 / R12 14.4k)  -> 0 .. 10 V
  GATE : Pico GP7 -> U3D x1.515 (R13 10k, R14 5.1k) -> 0 / 5 V ; TRIG : GP8 -> U4A x3.03 (R15 10k, R16 20.5k) -> 0 / 10 V (2 ms)
  every output -> 1k -> its jack ; GATE and CV also feed the normals of GATE IN / CV IN (the keyboard's own signal path)
Sensing for CV -> MIDI (what really drives the keyboard section, after the CV IN / GATE IN switching jacks) :
  KB CV -> R17 100k ; +3.3 V -> R18 30k ; R19 43k to GND ; C1 100n ; BAT54S clamp to 3.3 V / GND -> Pico ADC0 (GP26) :
          VADC = 1.65 V + 0.15 x CV  (-10 .. +10 V -> 0.15 .. 3.15 V)
  KB GATE -> R20 47k -> Q1 BC847 base (R21 47k to GND), collector R22 10k to 3.3 V -> GP9 (low = gate on, threshold ~1.3 V)
LEARN button -> GP10 (internal pull-up) ; MIDI LED -> GP11 -> R23 330 -> LED
Speaker (SPEAKER · MULT section) : OUTPUT (after VOLUME) -> PHONES jack switch (opens when headphones are in) -> SPEAKER switch
  -> R24 47k / R25 1k -> C2 1u -> LM386 (gain 20, +12 V, C3 220u out, Zobel R26 10 + C4 47n) -> 40 mm 8 ohm 1 W speaker (up to ~0.8 W at full level)
"""
import os, sys
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(H, '..', '..', 'outils', 'spice'))
from kicad2spice import MODELS

EXTRA = r"""
.model LEDIR D(IS=1e-18 N=1.6 RS=3 CJO=20p)
* H11L1 : LED + Schmitt-trigger open-collector output (turn-on at IF ~1.6 mA max, ~1 us), pins : a k vcc vo gnd
.subckt H11L1 a k vcc vo gnd
DL a ka LEDIR
Vsense ka k 0
Bs s 0 V = 0.5*(1+tanh((i(Vsense)-1.0m)/0.15m))
Rs s sf 1k
Cs sf 0 0.6n
Swo vo gnd sf 0 SWO
.model SWO SW(VT=0.5 VH=0.05 RON=30 ROFF=1e9)
.ends
* LM386 (behavioural) : gain 20, input 50k to ground, output centred on Vs/2, 1 V from the rails, 0.3 ohm
.subckt LM386 inp vs out
Rin inp 0 50k
Bo o1 0 V = min(max(v(vs)/2 + 20*v(inp), 1.0), v(vs)-1.0)
Ro o1 out 0.3
.ends
"""

def head():
    return MODELS + EXTRA + "\nVP P12 0 DC 12\nVM M12 0 DC -12\nV33 P33 0 DC 3.3\n"

def midi_in(sender='5V', data='PULSE(0 1 0 1n 1n 32u 64u)'):
    """sender : '5V' (classic : +5 V through 220 on pin 4, UART through 220 on pin 5) or '3V3' (33 / 10 ohm)"""
    v, ra, rb = (5.0, 220, 220) if sender == '5V' else (3.3, 33, 10)
    n = head() + f"VS SVCC 0 DC {v}\nRA SVCC RING {ra}\n"
    # sender's UART : logic 1 = idle = line high (no current) ; 0 = pulls pin 5 low ; 'data' is 1 when the bit is 0
    n += f"VD DB 0 {data}\nBsw TIPS 0 V = {v}*(1-v(DB))\nRB TIPS TIP {rb}\n"
    n += "R1 RING LA 220\nD1 TIP LA D1N4148\nXO LA TIP P33 RX 0 H11L1\nR3 RX P33 1k\nCRX RX 0 10p\n"
    return n

def outputs(code_pitch=0, code_vel=0, gate=0.0, trig=0.0):
    vd = lambda c: 2 * 2.048 * c / 4096
    n = head() + "DREF REF25 M12_REFK DZ5V1\n"
    # LM4040-2.5 shunt reference : modelled as an ideal 2.5 V source with 1 ohm
    n = head() + "VREF REF25 0 DC 2.5\n"
    n += f"VDA DACA 0 DC {vd(code_pitch)}\nVDB DACB 0 DC {vd(code_vel)}\nVG GP7 0 DC {gate}\nVT GP8 0 DC {trig}\n"
    n += "R6 REF25 PN 10k\nR7 PN PO 14.4k\nXU3A DACA PN PO P12 M12 TL07X\nRO1 PO CV 1k\nRL1 CV 0 100k\n"
    n += "R9 VN 0 10k\nR10 VN VO 14.4k\nXU3B DACB VN VO P12 M12 TL07X\nRO2 VO VEL 1k\nRL2 VEL 0 100k\n"
    n += "R13 GN 0 10k\nR14 GN GO 5.1k\nXU3D GP7 GN GO P12 M12 TL07X\nRO3 GO GATE 1k\nRL3 GATE 0 100k\n"
    n += "R15 TN 0 10k\nR16 TN TO 20.5k\nXU4A GP8 TN TO P12 M12 TL07X\nRO4 TO TRIG 1k\nRL4 TRIG 0 100k\n"
    return n

def sense(cv=0.0, gate=0.0):
    n = head() + f"VCV KBCV 0 DC {cv}\nVGT KBGATE 0 DC {gate}\n"
    n += "R17 KBCV ADC 100k\nR18 P33 ADC 30k\nR19 ADC 0 43k\nC1 ADC 0 100n\nDC1 ADC P33 DSCH\nDC2 0 ADC DSCH\n"
    n += "R20 KBGATE GB 47k\nR21 GB 0 47k\nQ1 GP9 GB 0 BC847\nR22 P33 GP9 10k\n"
    return n

def speaker(amp=5.0, f=1000, phones=False, spk_on=True):
    n = head() + f"VIN MAIN 0 SIN(0 {amp} {f})\n"
    n += ("RPH MAIN PH 0.01\n" if not phones else "RPH MAIN PH 1e9\n") + ("RSW PH SW 0.01\n" if spk_on else "RSW PH SW 1e9\n")
    n += "R24 SW DIV 47k\nR25 DIV 0 1k\nC2 DIV AIN 1u\nRB AIN 0 10k\nXA AIN P12 AO LM386\nC3 AO SPK 220u\nRSPK SPK 0 8\nR26 AO ZB 10\nC4 ZB 0 47n\n"
    return n
