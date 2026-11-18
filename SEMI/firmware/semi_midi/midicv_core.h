// ocTavio SEMI - MIDI <-> CV core (no hardware here : the .ino feeds it bytes and reads its outputs).
// Tested on the computer by firmware/test/test_core.cpp.
#pragma once
#include <stdint.h>
#include <string.h>

namespace semi {

// ---------------------------------------------------------------- calibration of the pitch DAC (MCP4822 -> TL074, see SEMI/circuits/midi.py)
struct Cal {
  float code0 = 1475.0f;      // DAC code for 0 V (= note 60, C4)
  float perVolt = 413.9f;     // DAC codes per volt (SPICE : 2.416 mV per code)
};

// ---------------------------------------------------------------- MIDI byte parser (running status, realtime bytes ignored)
struct Msg { uint8_t status = 0, d1 = 0, d2 = 0; uint8_t len = 0; };
class Parser {
 public:
  // returns true when a complete channel message is ready in m ; SysEx bytes are passed to sysex()
  bool feed(uint8_t b, Msg &m) {
    if (b >= 0xF8) return false;                                   // realtime : clock, start, stop...
    if (b == 0xF0) { inSysex = true; sxLen = 0; return false; }
    if (b == 0xF7) { inSysex = false; sysexDone = true; return false; }
    if (inSysex) { if (sxLen < sizeof(sx)) sx[sxLen++] = b; return false; }
    if (b & 0x80) {
      if (b >= 0xF0) { status = 0; return false; }                 // other system common : cancels running status
      status = b; n = 0; need = ((b & 0xE0) == 0xC0) ? 1 : 2; return false;
    }
    if (!status) return false;
    data[n++] = b;
    if (n < need) return false;
    m.status = status; m.d1 = data[0]; m.d2 = need > 1 ? data[1] : 0; m.len = need + 1; n = 0;
    return true;
  }
  uint8_t sx[16]; uint8_t sxLen = 0; bool sysexDone = false;
 private:
  uint8_t status = 0, data[2], n = 0, need = 2; bool inSysex = false;
};

// ---------------------------------------------------------------- the voice : last-note priority, legato, pitch bend, velocity, mod wheel
struct Out { uint16_t pitch, vel, mod; bool gate; bool trig; };

class Voice {
 public:
  uint8_t channel = 0;          // 0 = omni, 1..16 = learned channel
  bool learning = false;
  Cal cal;
  int bendRange = 2;            // semitones

  // handles one MIDI channel message ; returns true if it was for us
  bool message(const Msg &m) {
    uint8_t type = m.status & 0xF0, ch = (m.status & 0x0F) + 1;
    if (learning && type == 0x90 && m.d2 > 0) { channel = ch; learning = false; }
    if (channel && ch != channel) return false;
    if (type == 0x90 && m.d2 > 0) { noteOn(m.d1, m.d2); return true; }
    if (type == 0x80 || (type == 0x90 && m.d2 == 0)) { noteOff(m.d1); return true; }
    if (type == 0xB0 && m.d1 == 1) { mod = m.d2; return true; }
    if (type == 0xB0 && (m.d1 == 123 || m.d1 == 120)) { nHeld = 0; gate = false; return true; }   // all notes off
    if (type == 0xE0) { bend = ((int)m.d2 << 7 | m.d1) - 8192; return true; }
    return false;
  }
  void noteOn(uint8_t note, uint8_t v) {
    removeHeld(note);
    if (nHeld < 16) held[nHeld++] = note;
    cur = note; vel = v;
    trigPending = true;                  // TRIG on every new note ; GATE stays high between legato notes
    gate = true;
  }
  void noteOff(uint8_t note) {
    removeHeld(note);
    if (nHeld) cur = held[nHeld - 1]; else gate = false;
  }
  float volts() const { return (cur - 60) / 12.0f + bend / 8192.0f * bendRange / 12.0f; }
  uint16_t pitchCode() const {
    float c = cal.code0 + volts() * cal.perVolt + 0.5f;
    return c < 0 ? 0 : c > 4095 ? 4095 : (uint16_t)c;
  }
  Out out() { Out o{pitchCode(), (uint16_t)(vel * 4095 / 127), (uint16_t)(mod * 4095 / 127), gate, trigPending}; trigPending = false; return o; }
  bool gateOn() const { return gate; }
  uint8_t note() const { return cur; }
 private:
  void removeHeld(uint8_t note) { for (int i = 0; i < nHeld; i++) if (held[i] == note) { memmove(held + i, held + i + 1, nHeld - i - 1); nHeld--; return; } }
  uint8_t held[16]; int nHeld = 0;
  uint8_t cur = 60, vel = 100, mod = 0; int bend = 0;
  bool gate = false, trigPending = false;
};

// ---------------------------------------------------------------- CV IN / GATE IN -> MIDI notes (only when an external gate plays the keyboard)
struct NoteEvent { bool on; uint8_t note; };

class CvToMidi {
 public:
  // adcVolts : voltage on ADC0 (1.65 V + 0.15 x CV) ; extGate : sensed gate high while our own GATE output is low
  // returns the number of events written to ev (0..2)
  int update(float adcVolts, bool extGate, NoteEvent ev[2]) {
    float cv = (adcVolts - 1.65f) / 0.15f;
    float exact = 60.0f + 12.0f * cv;
    int n = 0;
    // hysteresis : keep the current note until the CV is 0.7 semitone away
    if (!playing || exact > last + 0.7f || exact < last - 0.7f) cand = (int)(exact + (exact >= 0 ? 0.5f : -0.5f));
    if (cand < 0) cand = 0;
    if (cand > 127) cand = 127;
    if (extGate && !playing) { ev[n++] = {true, (uint8_t)cand}; last = cand; playing = true; }
    else if (extGate && playing && cand != last) { ev[n++] = {true, (uint8_t)cand}; ev[n++] = {false, (uint8_t)last}; last = cand; }   // legato : new note first
    else if (!extGate && playing) { ev[n++] = {false, (uint8_t)last}; playing = false; }
    return n;
  }
 private:
  bool playing = false; int last = 60, cand = 60;
};

}  // namespace semi
