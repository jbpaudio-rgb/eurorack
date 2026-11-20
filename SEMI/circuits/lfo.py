"""ocTavio SEMI - LFO (one of the two ; the second is identical and uses the other half of the LM13700).

Core : OTA current into C1, Schmitt trigger reverses the direction at +/-4.9 V.
  Symmetry with a constant period : the Schmitt output S (+/-10.5 V) reaches the OTA input through two diode-steered paths,
  each through one side of the WAVE slider (RV2 100k B) : falling slope ~ 1/(R4 + w.RV2), rising slope ~ 1/(R5 + (1-w).RV2).
  The sum of both times only depends on R4 + R5 + RV2 : WAVE goes RAMP UP -> TRIANGLE -> RAMP DOWN at the same speed.
  R6 47 ohm turns the current into a few mV for the OTA (linear range), R7 47 ohm on the other input.
  RV3 (100k trimmer between -12 and +12) -> R25 120k -> OTA + input : cancels the LM13700 offset (+/-4.7 mV range).
  Set once : WAVE in the middle, turn RV3 until rise and fall take the same time (clean triangle).
  OTA (LM13700 A) -> C1 470n -> U1B follower = OUT (+/-4.9 V through R11 1k)
  U1C Schmitt : R8 47k from the triangle, R9 100k from S -> thresholds +/-4.9 V
  U1D follower of S / 2 (R12 10k, R13 10k) -> R14 1k -> SQ
Rate : U2A summer (RATE slider RV1 10k B 0..12 V via R1 140k, RATE CV 1 V/oct via R2 133k, offset R3 453k from -12 V, R10 100k feedback)
  -> R15 4.12k / R16 100 -> base of Q1b (BCM857DS) ; Q1a reference, collector held at 0 V by U2B, R17 1.2M to -12 V (Iref 10 uA)
  ; U2B drives the emitters through R18 1k, C2 100p ; Q1b collector -> IABC.
TRIG : S -> C3 47n -> TN (R19 47k to GND, R20 470k to +12) -> R21 10k -> U2C - input (D5 / D6 clamps to the rails), + input GND
  -> U2C high for ~5 ms when S falls (start of the rising part of the cycle) -> D7 -> R22 1k -> TRIG (R23 100k to GND) : 0 / ~10 V
LED : triangle (before R11) -> R24 2.2k -> red LED -> GND (lights on the positive half)
"""
import os, sys
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(H, '..', '..', 'outils', 'spice'))
from kicad2spice import MODELS
from svf import pot

def netlist(rate=0.5, wave=0.34, vcv='DC 0', analysis='', r3='453k'):
    n = MODELS + "\n.model LEDR D(IS=1e-19 N=1.8 RS=5)\n* ---- LFO\nVP P12 0 DC 12\nVM M12 0 DC -12\nVRCV RCV 0 " + vcv + "\n"
    # core
    n += "D3 S SD3 D1N4148\nR4 SD3 W1 1k\n" + pot('RV2', 'W1', 'SW', 'W3', 100e3, wave) + "R5 W3 SD4 1k\nD4 SD4 S D1N4148\n"
    n += pot('RV3', 'M12', 'TW', 'P12', 100e3, 0.5) + "R25 TW OP 120k\n"
    n += "R6 SW 0 47\nR7 OP 0 47\nXOTA OP SW IABC NC1 NC2 NC3 TRI P12 M12 LM13700H\nC1 TRI 0 470n\nXU1B TRI TRIB TRIB P12 M12 TL07X\n"
    n += "R8 TRIB SP 47k\nR9 S SP 100k\nXU1C SP 0 S P12 M12 TL07X\n"
    n += "R11 TRIB OUT 1k\nRLO OUT 0 100k\nR12 S SQH 10k\nR13 SQH 0 10k\nXU1D SQH SQB SQB P12 M12 TL07X\nR14 SQB SQ 1k\nRLS SQ 0 100k\n"
    # rate
    n += pot('RV1', '0', 'RW', 'P12', 10e3, rate)
    n += f"R1 RW CVN 140k\nR2 RCV CVN 133k\nR3 M12 CVN {r3}\nR10 CVN CVO 100k\nXU2A 0 CVN CVO P12 M12 TL07X\nR15 CVO QB 4.12k\nR16 QB 0 100\n"
    n += "Q1a QRC 0 QE BC857\nQ1b IABC QB QE BC857\nR17 QRC M12 1.2Meg\nC2 QE_D QRC 100p\nXU2B 0 QRC QE_D P12 M12 TL07X\nR18 QE_D QE 1k\n"
    # trig
    n += "C3 S TN 47n\nR19 TN 0 47k\nR20 TN P12 470k\nR21 TN TNI 10k\nD5 TNI P12 D1N4148\nD6 M12 TNI D1N4148\nXU2C 0 TNI TRO P12 M12 TL07X\n"
    n += "D7 TRO TRD D1N4148\nR22 TRD TRIG 1k\nR23 TRIG 0 100k\n"
    # led
    n += "R24 TRIB LA 2.2k\nDLED LA 0 LEDR\n"
    n += analysis + "\n.options method=gear reltol=1e-4 abstol=1e-12 vntol=1e-6 itl4=200\n.end\n"
    return n
