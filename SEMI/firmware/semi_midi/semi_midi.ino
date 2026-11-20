// ocTavio SEMI - KEYBOARD · MIDI : MIDI (3.5 mm DIN-type jack and USB) -> CV / GATE / TRIG / VEL / MOD, and CV IN / GATE IN -> MIDI OUT
// Board : Raspberry Pi Pico, Arduino core "Raspberry Pi Pico/RP2040" by Earle Philhower (arduino-pico).
// Arduino IDE : Tools > Board > Raspberry Pi Pico ; Tools > USB Stack > "Adafruit TinyUSB" (for USB-MIDI) ; upload over USB.
//
// MIDI IN (UART0 RX, GP1) and USB-MIDI both play the keyboard section ; everything that comes in is copied to MIDI OUT (UART0 TX, GP0)
// and to USB. When a Eurorack sequencer plays CV IN / GATE IN, those notes are sent to MIDI OUT and USB too.
// LEARN : press, then play one note : its channel becomes the channel of the SEMI (kept after power-off). Hold 2 s : back to omni.
// Calibration of the pitch output (1 V/oct) : hold LEARN while powering up. CV = 0 V (note 60) ; play C4 / D4 to move it down / up
// by one DAC step until a voltmeter reads 0.000 V on CV, then E4 : CV = +5 V (note 120) ; C5 / D5 down / up until 5.000 V ; LEARN saves.
// The logic (parser, note priority, legato, bend, learn, CV -> MIDI) is in midicv_core.h and tested on a computer (../test).

#include "semi_app.h"
// setup() and loop() are at the end of semi_app.h
