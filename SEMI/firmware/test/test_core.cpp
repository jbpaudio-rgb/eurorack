// Host tests of the MIDI <-> CV core :  g++ -std=c++17 -O1 test_core.cpp -o t && ./t
#include <cstdio>
#include <cmath>
#include <initializer_list>
#include "../semi_midi/midicv_core.h"
using namespace semi;
static int fails = 0, checks = 0;
#define CHECK(c, msg) do { checks++; if (!(c)) { fails++; printf("ÉCHEC : %s (ligne %d)\n", msg, __LINE__); } } while (0)

static void feed(Parser &p, Voice &v, std::initializer_list<int> bytes) { Msg m; for (int b : bytes) if (p.feed((uint8_t)b, m)) v.message(m); }

int main() {
  { Parser p; Voice v;
    feed(p, v, {0x90, 60, 100}); Out o = v.out();
    CHECK(o.gate && o.trig, "note on : GATE et TRIG");
    CHECK(o.pitch == 1475, "note 60 = 0 V = code 1475");
    CHECK(o.vel == 100 * 4095 / 127, "VEL = vélocité");
    feed(p, v, {72, 90});                                   // running status : note 72 without a new status byte
    CHECK(v.note() == 72 && v.gateOn(), "running status");
    CHECK(std::abs((int)v.out().pitch - (1475 + 414)) <= 1, "note 72 = +1 V = +414 codes");
    feed(p, v, {72, 0});                                    // note on velocity 0 = note off -> back to 60 (still held)
    CHECK(v.note() == 60 && v.gateOn(), "priorité dernière note : retour à la note encore tenue");
    feed(p, v, {0x80, 60, 0});
    CHECK(!v.gateOn(), "toutes relâchées : GATE bas");
  }
  { Parser p; Voice v;
    feed(p, v, {0x90, 60, 100}); v.out();
    feed(p, v, {0x90, 64, 100}); Out o = v.out();
    CHECK(o.gate && o.trig, "legato : GATE reste haut, nouveau TRIG");
    feed(p, v, {0xF8, 0xFA, 0xFE});                         // realtime bytes in the middle
    feed(p, v, {0xE0, 0x7F, 0x7F});                          // pitch bend up : +2 semitones
    CHECK(std::abs(v.volts() - (4 + 2) / 12.0f) < 0.002f, "pitch bend +2 demi-tons");
    feed(p, v, {0xB0, 1, 127});
    CHECK(v.out().mod == 4095, "molette = MOD 10 V");
    feed(p, v, {0xB0, 123, 0});
    CHECK(!v.gateOn(), "all notes off");
  }
  { Parser p; Voice v; v.learning = true;
    feed(p, v, {0x93, 50, 100});                              // channel 4
    CHECK(v.channel == 4 && !v.learning, "LEARN : canal 4 appris");
    feed(p, v, {0x80 + 3, 50, 0, 0x90, 61, 100});            // note on channel 1 is ignored
    CHECK(!v.gateOn(), "autre canal ignoré");
    feed(p, v, {0x93, 62, 100});
    CHECK(v.gateOn() && v.note() == 62, "canal appris accepté");
  }
  { Parser p; Voice v; Msg m; int n = 0;
    for (int b : {0xF0, 0x7D, 0x01, 0x02, 0xF7, 0x90, 60, 1}) if (p.feed((uint8_t)b, m)) { v.message(m); n++; }
    CHECK(n == 1 && p.sysexDone && p.sxLen == 3, "SysEx mis de côté, la note suivante passe");
  }
  { Voice v; Out o; v.noteOn(0, 1); o = v.out(); CHECK(o.pitch == 0, "note 0 : code limité à 0");
    v.noteOn(127, 1); o = v.out(); CHECK(std::abs((int)o.pitch - 3786) <= 1, "note 127 = +5,58 V, dans la plage du DAC (notes 17 à 127 jouables)"); }
  { CvToMidi c; NoteEvent ev[2]; int n;
    auto adc = [](float cv) { return 1.65f + 0.15f * cv; };
    n = c.update(adc(0.0f), false, ev); CHECK(n == 0, "pas de gate externe : rien");
    n = c.update(adc(0.02f), true, ev); CHECK(n == 1 && ev[0].on && ev[0].note == 60, "gate externe : note 60 (0 V)");
    n = c.update(adc(0.05f), true, ev); CHECK(n == 0, "petite dérive : pas de nouvelle note (hystérésis)");
    n = c.update(adc(7.0f / 12), true, ev); CHECK(n == 2 && ev[0].on && ev[0].note == 67 && !ev[1].on && ev[1].note == 60, "legato : note 67 puis fin de 60");
    n = c.update(adc(7.0f / 12), false, ev); CHECK(n == 1 && !ev[0].on && ev[0].note == 67, "fin du gate : note off");
    n = c.update(adc(-3.0f), true, ev); CHECK(n == 1 && ev[0].note == 24, "-3 V = note 24 (C1)");
    c.update(adc(-3.0f), false, ev);
    n = c.update(adc(6.0f), true, ev); CHECK(n == 1 && ev[0].note == 127, "+6 V = 132 : limité à 127");
  }
  printf("%d vérifications, %d échec(s)\n", checks, fails);
  return fails ? 1 : 0;
}
