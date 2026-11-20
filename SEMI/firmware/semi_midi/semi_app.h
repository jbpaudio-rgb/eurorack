// ocTavio SEMI - KEYBOARD · MIDI firmware body (kept out of the .ino so that the Arduino builder does not touch it)
#pragma once
#include <Arduino.h>
#include <SPI.h>
#include <EEPROM.h>
#include <Adafruit_TinyUSB.h>
#include "midicv_core.h"

// ---------------- pins (SEMI/circuits/midi.py) ----------------
const int PIN_TX = 0, PIN_RX = 1;                       // UART0 : MIDI OUT / MIDI IN (H11L1)
const int PIN_SCK = 2, PIN_MOSI = 3, PIN_CS_A = 5, PIN_CS_B = 6;   // SPI0 -> 2 x MCP4822
const int PIN_GATE = 7, PIN_TRIG = 8;                   // -> TL074 x1.515 (5 V) / x3.03 (10 V)
const int PIN_GATE_SENSE = 9;                            // BC847 : LOW = gate on the keyboard section
const int PIN_LEARN = 10, PIN_MIDI_LED = 11;
const int PIN_CV_SENSE = 26;                             // ADC0 : 1.65 V + 0.15 x CV

const uint32_t TRIG_US = 2000;
static Adafruit_USBD_MIDI usbMidi;
static semi::Parser parseDin, parseUsb;
static semi::Voice voice;
static semi::CvToMidi cv2midi;
static uint32_t trigUntil = 0, ledUntil = 0;
static float adcAvg = 1.65f;

// ---------------- DAC ----------------
inline void dac(int cs, int ch, uint16_t code) {               // MCP4822 : ch 0 = A, 1 = B ; gain x2 (bit 13 = 0), active (bit 12 = 1)
  uint16_t w = (ch ? 0x8000 : 0) | 0x1000 | (code & 0x0FFF);
  SPI.beginTransaction(SPISettings(16000000, MSBFIRST, SPI_MODE0));
  digitalWrite(cs, LOW); SPI.transfer16(w); digitalWrite(cs, HIGH);
  SPI.endTransaction();
}
inline void writeOutputs() {
  semi::Out o = voice.out();
  dac(PIN_CS_A, 0, o.pitch);                            // A : pitch
  dac(PIN_CS_A, 1, o.vel);                              // B : VEL
  dac(PIN_CS_B, 0, o.mod);                              // C : MOD
  digitalWrite(PIN_GATE, o.gate);
  if (o.trig) { digitalWrite(PIN_TRIG, HIGH); trigUntil = micros() + TRIG_US; }
}

// ---------------- MIDI out (DIN + USB) ----------------
inline void sendBytes(const uint8_t *b, int n) { Serial1.write(b, n); usbMidi.write(b, n); }
inline void sendNote(bool on, uint8_t note) {
  uint8_t ch = voice.channel ? voice.channel - 1 : 0;
  uint8_t b[3] = {(uint8_t)((on ? 0x90 : 0x80) | ch), note, (uint8_t)(on ? 100 : 0)};
  sendBytes(b, 3);
}
inline void blink() { digitalWrite(PIN_MIDI_LED, HIGH); ledUntil = millis() + 30; }

inline void handle(semi::Parser &p, uint8_t byte, bool thruToUsb) {
  semi::Msg m;
  Serial1.write(byte);                                   // MIDI OUT = merge of everything that comes in
  if (thruToUsb) usbMidi.write(byte);
  if (p.feed(byte, m)) { if (voice.message(m)) writeOutputs(); blink(); }
}

// ---------------- settings ----------------
struct Saved { uint32_t magic; uint8_t channel; float code0, perVolt; };
inline void save() { Saved s{0x5E31D1u, voice.channel, voice.cal.code0, voice.cal.perVolt}; EEPROM.put(0, s); EEPROM.commit(); }
inline void load() { Saved s; EEPROM.get(0, s); if (s.magic == 0x5E31D1u && s.channel <= 16 && s.perVolt > 300 && s.perVolt < 500) { voice.channel = s.channel; voice.cal.code0 = s.code0; voice.cal.perVolt = s.perVolt; } }

inline void calibrate() {                                       // see the header : C4 / D4 move 0 V, E4 goes to +5 V, C5 / D5 move 5 V, LEARN saves
  float c0 = voice.cal.code0, c5 = voice.cal.code0 + 5 * voice.cal.perVolt; bool high = false;
  while (digitalRead(PIN_LEARN) == LOW) delay(10);
  for (;;) {
    dac(PIN_CS_A, 0, (uint16_t)((high ? c5 : c0) + 0.5f));
    digitalWrite(PIN_MIDI_LED, (millis() / (high ? 150 : 500)) & 1);
    semi::Msg m; int b = -1;
    if (Serial1.available()) b = Serial1.read(); else if (usbMidi.available()) b = usbMidi.read();
    if (b >= 0 && parseDin.feed((uint8_t)b, m) && (m.status & 0xF0) == 0x90 && m.d2) {
      if (m.d1 == 60) (high ? c5 : c0) -= 1; if (m.d1 == 62) (high ? c5 : c0) += 1;
      if (m.d1 == 64) high = true; if (m.d1 == 72) c5 -= 1; if (m.d1 == 74) c5 += 1;
    }
    if (digitalRead(PIN_LEARN) == LOW) { voice.cal.code0 = c0; voice.cal.perVolt = (c5 - c0) / 5.0f; save(); while (digitalRead(PIN_LEARN) == LOW) delay(10); return; }
  }
}

inline void appSetup() {
  usbMidi.setStringDescriptor("ocTavio SEMI");
  usbMidi.begin();
  Serial1.setTX(PIN_TX); Serial1.setRX(PIN_RX); Serial1.begin(31250);
  SPI.setSCK(PIN_SCK); SPI.setTX(PIN_MOSI); SPI.begin();
  pinMode(PIN_CS_A, OUTPUT); pinMode(PIN_CS_B, OUTPUT); digitalWrite(PIN_CS_A, HIGH); digitalWrite(PIN_CS_B, HIGH);
  pinMode(PIN_GATE, OUTPUT); pinMode(PIN_TRIG, OUTPUT); pinMode(PIN_MIDI_LED, OUTPUT);
  pinMode(PIN_LEARN, INPUT_PULLUP); pinMode(PIN_GATE_SENSE, INPUT);
  analogReadResolution(12);
  EEPROM.begin(256); load();
  if (digitalRead(PIN_LEARN) == LOW) calibrate();
  writeOutputs();
}

inline void appLoop() {
  while (Serial1.available()) handle(parseDin, Serial1.read(), true);
  while (usbMidi.available()) { parseUsb.sysexDone = false; handle(parseUsb, usbMidi.read(), false); }
  // LEARN : short press = learn the next note's channel ; 2 s = omni
  static uint32_t pressedAt = 0;
  if (digitalRead(PIN_LEARN) == LOW) { if (!pressedAt) pressedAt = millis(); if (millis() - pressedAt > 2000 && voice.channel) { voice.channel = 0; voice.learning = false; save(); } }
  else if (pressedAt) { if (millis() - pressedAt < 2000) voice.learning = true; pressedAt = 0; }
  static uint8_t savedCh = voice.channel;
  if (voice.channel != savedCh) { savedCh = voice.channel; save(); }
  // CV IN / GATE IN -> MIDI : only when the gate on the keyboard section is not ours (a cable in GATE IN)
  static uint32_t nextAdc = 0;
  if ((int32_t)(micros() - nextAdc) >= 0) {
    nextAdc = micros() + 1000;
    adcAvg += 0.25f * (analogRead(PIN_CV_SENSE) * 3.3f / 4095.0f - adcAvg);
    bool ext = digitalRead(PIN_GATE_SENSE) == LOW && !voice.gateOn();
    semi::NoteEvent ev[2]; int n = cv2midi.update(adcAvg, ext, ev);
    for (int i = 0; i < n; i++) { sendNote(ev[i].on, ev[i].note); blink(); }
  }
  if (trigUntil && (int32_t)(micros() - trigUntil) >= 0) { digitalWrite(PIN_TRIG, LOW); trigUntil = 0; }
  if (ledUntil && (int32_t)(millis() - ledUntil) >= 0) { digitalWrite(PIN_MIDI_LED, voice.learning ? (millis() / 120) & 1 : LOW); ledUntil = 0; }
  if (voice.learning) digitalWrite(PIN_MIDI_LED, (millis() / 120) & 1);
}

void setup() { appSetup(); }
void loop() { appLoop(); }
