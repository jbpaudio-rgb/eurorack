// ocTavio STAGES - 8-stage multistage sequencer (after the Verbos Voltage Multistage)
// Board : Raspberry Pi Pico, Arduino core "Raspberry Pi Pico/RP2040" by Earle Philhower (arduino-pico).
// Arduino IDE : Tools > Board > Raspberry Pi Pico ; upload over USB (hold BOOTSEL the first time).
//
// Per stage : A, B, TIME pots ; SLIDE button (short press = slide on/off, long press = last stage) ;
//             stage LED, slide LED ; SELECT input (jump to the stage) ; GATE output (high while the stage is active).
// Global    : TIME (10 ms .. 10 s), TIME CV with attenuverter, ANALOG (stage address / sustain stage),
//             START (button + input), MODE (LOOP / ONCE / ENV), CLOCK, STROBE ; outputs CV A, CV B, GATE, END.

#include <Arduino.h>
#include <SPI.h>
#include <EEPROM.h>

// ---------------- pins (see the schematic notes) ----------------
const int PIN_CLK = 2, PIN_START = 3, PIN_STROBE = 4;        // conditioned inputs, active LOW
const int PIN_BTN_START = 5, PIN_BTN_MODE = 6;               // buttons to GND, internal pull-ups
const int PIN_MUX_S[4] = {10, 11, 12, 13};
const int PIN_MISO = 16, PIN_CS_DAC = 17, PIN_SCK = 18, PIN_MOSI = 19, PIN_LATCH = 20, PIN_LOAD = 21;
const int PIN_MUX1 = 26, PIN_MUX2 = 27, PIN_ANALOG = 28;     // ADC0, ADC1, ADC2

// ---------------- calibration ----------------
const float DAC_FULL_VOLTS = 2.048f * 4.83f;   // MCP4822 gain 1 x op-amp gain (R 38k3 / 10k + 1)
const float CV_MAX = 8.0f;                     // A / B knob range 0 .. 8 V
const float CVIN_MID = 1.65f, CVIN_GAIN = 0.15f;   // ADC volts = 1.65 - 0.15 x Vin

// ---------------- state ----------------
enum Mode { LOOP = 0, ONCE = 1, ENV = 2 };
float potA[8], potB[8], potT[8], potTime = 0.4f, potTcv = 0.5f, potAnalog = 0.0f, cvTime = 0.0f, cvAnalog = 0.0f;
bool slide[8] = {false};
int endStage = 7;
int mode = LOOP;

int stage = 0, prevStage = 7;
float pos = 0.0f;              // 0..1 inside the current stage
bool running = true;
bool gateHeld = false;          // START gate (input or button) for ENV
uint32_t endPulseUntil = 0;
float prevA = 0, prevB = 0;     // values we glide from

volatile uint32_t clkEdges = 0, startEdges = 0, startFalls = 0, strobeEdges = 0;
uint32_t lastClkUs = 0, clkPeriodUs = 0;
uint16_t selPrev = 0, btnPrev = 0;
uint32_t btnDownMs[8];
bool btnLong[8];
bool startBtnPrev = false, modeBtnPrev = false;
uint32_t saveAt = 0;

// ---------------- helpers ----------------
static inline float clampf(float v, float a, float b) { return v < a ? a : (v > b ? b : v); }

void isrClk() { uint32_t t = micros(); if (lastClkUs) clkPeriodUs = t - lastClkUs; lastClkUs = t; clkEdges++; }
void isrStart() { if (digitalRead(PIN_START) == LOW) startEdges++; else startFalls++; }   // LOW = gate high
void isrStrobe() { strobeEdges++; }

int analogStage() {
  float a = clampf(potAnalog + cvAnalog / 8.0f, 0.0f, 1.0f);
  return (int)lroundf(a * 7.0f);
}

float stageSeconds(int i) {
  float tg = 0.01f * powf(1000.0f, potTime);                     // 10 ms .. 10 s
  float att = potTcv * 2.0f - 1.0f;                              // reversing attenuator
  tg *= powf(2.0f, -att * cvTime);                               // +1 V = twice as fast
  float m = powf(4.0f, potT[i] * 2.0f - 1.0f);                   // stage TIME : x0.25 .. x4
  return clampf(tg * m, 0.001f, 60.0f);
}

void loadSettings() {
  EEPROM.begin(64);
  if (EEPROM.read(0) == 0x5A) {
    uint8_t s = EEPROM.read(1);
    for (int i = 0; i < 8; i++) slide[i] = (s >> i) & 1;
    endStage = EEPROM.read(2) & 7;
    mode = EEPROM.read(3) % 3;
  }
}
void saveSettings() {
  uint8_t s = 0;
  for (int i = 0; i < 8; i++) if (slide[i]) s |= 1 << i;
  EEPROM.write(0, 0x5A); EEPROM.write(1, s); EEPROM.write(2, endStage); EEPROM.write(3, mode);
  EEPROM.commit();
}
void settingsChanged() { saveAt = millis() + 2000; }

void enterStage(int s) {
  // glide starts from where the outputs are now
  prevA = potA[stage]; prevB = potB[stage];
  prevStage = stage; stage = s; pos = 0.0f;
}

void endOfSequence() {
  endPulseUntil = millis() + 5;
  if (mode == LOOP) enterStage(0);
  else { running = false; pos = 1.0f; }
}

void startEvent(bool rising) {
  if (rising) {
    gateHeld = true;
    if (mode == LOOP) running = !running;
    else { enterStage(0); running = true; }
  } else {
    gateHeld = false;
  }
}

// ---------------- I/O ----------------
uint16_t readInputs() {                 // 74HC165 x2 : byte 0 = SELECT 8..1, byte 1 = buttons 8..1 (active low)
  digitalWrite(PIN_LOAD, LOW); delayMicroseconds(1); digitalWrite(PIN_LOAD, HIGH);
  uint8_t a = SPI.transfer(0), b = SPI.transfer(0);
  return (uint16_t)(~a & 0xFF) | ((uint16_t)(~b & 0xFF) << 8);
}
void writeDac(float va, float vb) {
  uint16_t ca = (uint16_t)clampf(va / DAC_FULL_VOLTS * 4095.0f + 0.5f, 0, 4095);
  uint16_t cb = (uint16_t)clampf(vb / DAC_FULL_VOLTS * 4095.0f + 0.5f, 0, 4095);
  digitalWrite(PIN_CS_DAC, LOW); SPI.transfer16(0x3000 | ca); digitalWrite(PIN_CS_DAC, HIGH);
  digitalWrite(PIN_CS_DAC, LOW); SPI.transfer16(0xB000 | cb); digitalWrite(PIN_CS_DAC, HIGH);
}
void writeOutputs(uint8_t ledStage, uint8_t ledSlide, uint8_t gates, uint8_t misc) {
  // chain MOSI -> U6 (stage LEDs) -> U7 (slide LEDs) -> U8 (gates 1-8) -> U9 (GATE, END, mode LEDs) : last chip first
  SPI.transfer(misc); SPI.transfer(gates); SPI.transfer(ledSlide); SPI.transfer(ledStage);
  digitalWrite(PIN_LATCH, HIGH); delayMicroseconds(1); digitalWrite(PIN_LATCH, LOW);
}

// pots : one mux channel per tick (both muxes at once), 16 ticks per full scan
int muxCh = 0;
void scanPots() {
  float a = analogRead(PIN_MUX1) / 4095.0f, b = analogRead(PIN_MUX2) / 4095.0f;
  const float k = 0.25f;
  if (muxCh < 8) { potA[muxCh] += (a - potA[muxCh]) * k; potT[muxCh] += (b - potT[muxCh]) * k; }
  else {
    int i = muxCh - 8;
    potB[i] += (a - potB[i]) * k;
    if (i == 0) potTime += (b - potTime) * k;
    else if (i == 1) potTcv += (b - potTcv) * k;
    else if (i == 2) potAnalog += (b - potAnalog) * k;
    else if (i == 3) cvTime += ((CVIN_MID - b * 3.3f) / CVIN_GAIN - cvTime) * k;
  }
  cvAnalog += ((CVIN_MID - analogRead(PIN_ANALOG) / 4095.0f * 3.3f) / CVIN_GAIN - cvAnalog) * 0.25f;
  muxCh = (muxCh + 1) & 15;
  for (int i = 0; i < 4; i++) digitalWrite(PIN_MUX_S[i], (muxCh >> i) & 1);   // settles until the next tick
}

// ---------------- setup / loop ----------------
void setup() {
  for (int i = 0; i < 8; i++) { potA[i] = potB[i] = 0.0f; potT[i] = 0.5f; btnDownMs[i] = 0; btnLong[i] = false; }
  pinMode(PIN_CLK, INPUT); pinMode(PIN_START, INPUT); pinMode(PIN_STROBE, INPUT);
  pinMode(PIN_BTN_START, INPUT_PULLUP); pinMode(PIN_BTN_MODE, INPUT_PULLUP);
  for (int i = 0; i < 4; i++) pinMode(PIN_MUX_S[i], OUTPUT);
  pinMode(PIN_CS_DAC, OUTPUT); digitalWrite(PIN_CS_DAC, HIGH);
  pinMode(PIN_LATCH, OUTPUT); digitalWrite(PIN_LATCH, LOW);
  pinMode(PIN_LOAD, OUTPUT); digitalWrite(PIN_LOAD, HIGH);
  analogReadResolution(12);
  SPI.setRX(PIN_MISO); SPI.setSCK(PIN_SCK); SPI.setTX(PIN_MOSI);
  SPI.begin();
  SPI.beginTransaction(SPISettings(8000000, MSBFIRST, SPI_MODE0));
  attachInterrupt(digitalPinToInterrupt(PIN_CLK), isrClk, FALLING);       // LOW = input high
  attachInterrupt(digitalPinToInterrupt(PIN_START), isrStart, CHANGE);
  attachInterrupt(digitalPinToInterrupt(PIN_STROBE), isrStrobe, FALLING);
  loadSettings();
  for (int i = 0; i < 64; i++) { scanPots(); delay(1); }
}

const uint32_t TICK_US = 500;          // 2 kHz engine
uint32_t nextTick = 0, lastClkSeen = 0, edgesSeen = 0, startSeen = 0, fallsSeen = 0, strobeSeen = 0;

void loop() {
  uint32_t now = micros();
  if ((int32_t)(now - nextTick) < 0) return;
  nextTick = now + TICK_US;
  const float dt = TICK_US * 1e-6f;
  uint32_t ms = millis();

  scanPots();

  // ---- buttons and SELECT inputs ----
  uint16_t in = readInputs();
  uint8_t sel = in & 0xFF, btn = in >> 8;
  for (int i = 0; i < 8; i++) {
    bool s = (sel >> i) & 1, sp = (selPrev >> i) & 1;
    if (s && !sp) { enterStage(i); if (mode != LOOP && !running) running = true; }
    bool b = (btn >> i) & 1, bp = (btnPrev >> i) & 1;
    if (b && !bp) { btnDownMs[i] = ms; btnLong[i] = false; }
    if (b && !btnLong[i] && ms - btnDownMs[i] > 600) { btnLong[i] = true; endStage = i; settingsChanged(); }
    if (!b && bp && !btnLong[i]) { slide[i] = !slide[i]; settingsChanged(); }
  }
  selPrev = sel; btnPrev = btn;
  bool sb = digitalRead(PIN_BTN_START) == LOW, mb = digitalRead(PIN_BTN_MODE) == LOW;
  if (sb != startBtnPrev) startEvent(sb);
  if (mb && !modeBtnPrev) { mode = (mode + 1) % 3; settingsChanged(); }
  startBtnPrev = sb; modeBtnPrev = mb;
  while (startSeen != startEdges) { startSeen++; startEvent(true); }
  while (fallsSeen != startFalls) { fallsSeen++; startEvent(false); }
  while (strobeSeen != strobeEdges) { strobeSeen++; enterStage(analogStage()); if (mode != LOOP) running = true; }

  // ---- clock : external if a clock arrived in the last 3 s, otherwise stage TIME ----
  bool extClock = lastClkUs && (now - lastClkUs) < 3000000UL;
  uint32_t newEdges = clkEdges - edgesSeen; edgesSeen = clkEdges;
  int last = endStage;
  bool hold = (mode == ENV) && gateHeld && stage == analogStage() && running;
  if (running) {
    if (extClock) {
      float per = clkPeriodUs > 0 ? clkPeriodUs * 1e-6f : 0.5f;
      pos = clampf(pos + dt / per, 0.0f, 1.0f);
      for (uint32_t e = 0; e < newEdges && running; e++) {
        if (hold) break;
        if (stage == last) endOfSequence(); else enterStage((stage + 1) & 7);
      }
    } else {
      pos += dt / stageSeconds(stage);
      if (pos >= 1.0f) {
        if (hold) pos = 1.0f;
        else if (stage == last) endOfSequence();
        else enterStage((stage + 1) & 7);
      }
    }
  }

  // ---- outputs ----
  float tA = potA[stage] * CV_MAX, tB = potB[stage] * CV_MAX;
  float vA = tA, vB = tB;
  if (slide[stage]) { float p = clampf(pos, 0, 1); vA = prevA * CV_MAX + (tA - prevA * CV_MAX) * p; vB = prevB * CV_MAX + (tB - prevB * CV_MAX) * p; }
  writeDac(vA, vB);

  int nextS = stage == last ? (mode == LOOP ? 0 : stage) : (stage + 1) & 7;
  bool active = running || hold;
  bool gate = active && (pos < 0.5f || slide[nextS] || hold);
  uint8_t gates = active ? (1 << stage) : 0;
  uint8_t ledStage = 1 << stage;
  if (((ms / 250) & 1) && stage != endStage) ledStage |= 1 << endStage;      // the last stage blinks
  uint8_t ledSlide = 0;
  for (int i = 0; i < 8; i++) if (slide[i]) ledSlide |= 1 << i;
  uint8_t misc = (gate ? 0x01 : 0) | (ms < endPulseUntil ? 0x02 : 0) | (0x04 << mode);
  writeOutputs(ledStage, ledSlide, gates, misc);

  if (saveAt && (int32_t)(ms - saveAt) >= 0) { saveAt = 0; saveSettings(); }
}
