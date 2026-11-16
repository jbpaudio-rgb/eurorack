// ocTavio QUAD LFO - four LFOs, free or locked to a clock
// Board : Raspberry Pi Pico, Arduino core "Raspberry Pi Pico/RP2040" by Earle Philhower (arduino-pico).
// Arduino IDE : Tools > Board > Raspberry Pi Pico ; upload over USB (hold BOOTSEL the first time).
//
// Per channel : FREQ knob, WAVE knob (morphs SINE -> SAW -> SQUARE), FREE / CLOCKED toggle,
//               LED that follows the wave, output +/-5 V.
// FREE    : FREQ = 0.02 Hz .. 25 Hz (exponential).
// CLOCKED : FREQ picks a ratio of the CLOCK input : /16 /8 /4 /3 /2 x1 x2 x3 x4 x8 x16, phase locked to the clock.
// RESET   : every phase back to the start (clocked channels restart on the next clock count of 0).
// Outputs : no DAC - hardware PWM 30.5 kHz / 12 bits, two RC poles (159 Hz) and an op-amp (x3.02 - 4.93 V).

#include <Arduino.h>

// ---------------- pins (see the schematic notes) ----------------
const int PIN_SYNC[4] = {0, 1, 2, 3};          // FREE / CLOCKED toggles to GND, internal pull-ups
const int PIN_CLK = 4, PIN_RST = 5;             // conditioned inputs, active LOW
const int PIN_MUX_S[3] = {6, 7, 8};             // 74HC4051 address
const int PIN_LED[4] = {10, 11, 12, 13}, PIN_LED_CLK = 14;
const int PIN_PWM[4] = {16, 17, 18, 19};
const int PIN_MUX = 26;                          // ADC0 : Y0-3 = FREQ 1-4, Y4-7 = WAVE 1-4
const bool CLOCKED_WHEN_LOW = true;             // flip if the toggle reads upside down

// ---------------- calibration ----------------
const float OUT_GAIN = 3.0236f, OUT_OFFSET = 4.93f;   // Vout = 3.0236 x Vpwm - 4.93 (R 20k / 12k4 / 48k7)
const float VPWM_FULL = 3.30f;                         // Pico 3,3 V rail
const float AMP = 4.9f;                                // +/-4.9 V (stays clear of the rails)
const int PWM_RANGE = 4096;
const uint32_t TICK_US = 250;                          // 4 kHz update

// ---------------- state ----------------
const float RATIOS[11] = {1.0f / 16, 1.0f / 8, 1.0f / 4, 1.0f / 3, 1.0f / 2, 1, 2, 3, 4, 8, 16};
float potF[4] = {0.5f, 0.5f, 0.5f, 0.5f}, potW[4] = {0, 0, 0, 0};
int ratioIdx[4] = {5, 5, 5, 5};
float phase[4] = {0, 0, 0, 0};
volatile uint32_t clkCount = 0, lastClkUs = 0, clkPeriodUs = 0;
volatile bool rstFlag = false;
uint32_t clkLedUntil = 0;
int muxCh = 0;
uint32_t nextTick = 0;

static inline float clampf(float v, float a, float b) { return v < a ? a : (v > b ? b : v); }

void isrClk() {
  uint32_t t = micros();
  if (lastClkUs && t - lastClkUs > 2000) clkPeriodUs = t - lastClkUs;   // ignore bounces < 2 ms
  lastClkUs = t; clkCount++;
}
void isrRst() { rstFlag = true; }

void setMux(int ch) { for (int b = 0; b < 3; b++) digitalWrite(PIN_MUX_S[b], (ch >> b) & 1); }

int ratioZone(float v, int cur) {
  float x = v * 10.0f;                           // 11 positions
  int z = (int)lroundf(x);
  if (z != cur && fabsf(x - cur) < 0.6f) return cur;
  return z < 0 ? 0 : (z > 10 ? 10 : z);
}

// WAVE knob : 0 = SINE, 0.5 = SAW (rising), 1 = SQUARE, crossfaded in between
float shape(float w, float p) {
  float sine = sinf(6.2831853f * p), saw = 2.0f * p - 1.0f, sqr = p < 0.5f ? 1.0f : -1.0f;
  float x = clampf(w * 2.0f, 0.0f, 2.0f);
  if (x < 1.0f) return sine + x * (saw - sine);
  return saw + (x - 1.0f) * (sqr - saw);
}

void writeOut(int ch, float v) {
  float vp = (v * AMP + OUT_OFFSET) / OUT_GAIN;
  int code = (int)lroundf(clampf(vp / VPWM_FULL, 0.0f, 1.0f) * (PWM_RANGE - 1));
  analogWrite(PIN_PWM[ch], code);
}

bool clocked(int ch) { return (digitalRead(PIN_SYNC[ch]) == LOW) == CLOCKED_WHEN_LOW; }

void setup() {
  for (int i = 0; i < 4; i++) pinMode(PIN_SYNC[i], INPUT_PULLUP);
  pinMode(PIN_CLK, INPUT); pinMode(PIN_RST, INPUT);
  for (int b = 0; b < 3; b++) pinMode(PIN_MUX_S[b], OUTPUT);
  analogReadResolution(12);
  analogWriteFreq(30500);
  analogWriteRange(PWM_RANGE);
  for (int i = 0; i < 4; i++) { pinMode(PIN_PWM[i], OUTPUT); pinMode(PIN_LED[i], OUTPUT); }
  pinMode(PIN_LED_CLK, OUTPUT);
  attachInterrupt(digitalPinToInterrupt(PIN_CLK), isrClk, FALLING);   // LOW = clock high
  attachInterrupt(digitalPinToInterrupt(PIN_RST), isrRst, FALLING);
  setMux(0);
  nextTick = micros();
}

void loop() {
  uint32_t now = micros();
  if ((int32_t)(now - nextTick) < 0) return;
  nextTick += TICK_US;
  const float dt = TICK_US * 1e-6f;

  // ---- one pot per tick (8 pots -> every 2 ms), light smoothing
  float raw = analogRead(PIN_MUX) / 4095.0f;
  if (muxCh < 4) potF[muxCh] += 0.25f * (raw - potF[muxCh]);
  else potW[muxCh - 4] += 0.25f * (raw - potW[muxCh - 4]);
  muxCh = (muxCh + 1) & 7; setMux(muxCh);        // settles until the next tick

  // ---- reset
  if (rstFlag) {
    noInterrupts(); rstFlag = false; clkCount = 0; lastClkUs = now; interrupts();
    for (int i = 0; i < 4; i++) phase[i] = 0.0f;
  }

  // ---- clock position : whole clocks (modulo 48 = lcm of 16, 3 ...) + fraction since the last clock
  noInterrupts(); uint32_t n = clkCount, last = lastClkUs, per = clkPeriodUs; interrupts();
  float frac = per ? clampf((float)(now - last) / (float)per, 0.0f, 1.0f) : 0.0f;   // holds if the clock stops
  float clockPos = (float)(n % 48) + frac;
  if (last && now - last < 60000) clkLedUntil = last + 30000;
  digitalWrite(PIN_LED_CLK, (int32_t)(clkLedUntil - now) > 0 ? HIGH : LOW);

  for (int i = 0; i < 4; i++) {
    float p;
    if (clocked(i) && per) {
      ratioIdx[i] = ratioZone(potF[i], ratioIdx[i]);
      float x = clockPos * RATIOS[ratioIdx[i]];
      p = x - floorf(x);
      phase[i] = p;                               // free mode carries on from here when switched back
    } else {
      float hz = 0.02f * powf(2.0f, potF[i] * 10.3f);   // 0.02 .. 25 Hz
      phase[i] += hz * dt;
      if (phase[i] >= 1.0f) phase[i] -= floorf(phase[i]);
      p = phase[i];
    }
    float v = shape(potW[i], p);
    writeOut(i, v);
    float b = 0.5f * (v + 1.0f);
    analogWrite(PIN_LED[i], (int)(b * b * (PWM_RANGE - 1)));
  }
}
