# ocTavio SEMI – grand semi-modulaire (prototype)

Grand panneau semi-modulaire dans l'esprit des gros semi-modulaires des années 70 et 2000 (3 VCO, deux filtres, réverbe à ressort), construit avec les circuits des modules ocTavio Eurorack. **Sliders de 60 mm** à la place des potards, **jacks 3,5 mm** (Thonkiconn) aux **niveaux Eurorack** pour patcher avec le rack.

État : **façade + simulateur jouable** (étape de validation avant les cartes).

- `index.html` : le simulateur (un seul fichier). Ouvrir depuis un petit serveur web (`python3 -m http.server`) pour le son en AudioWorklet ; ouvert directement, il passe en mode compatible.
- `apercu-facade.png` : la façade. `apercu-normalisations.png` : le câblage interne en pointillé.
- `source/def.js` : **la définition unique** (sections, sliders, inverseurs, jacks, normalisations). Le panneau et le son sont générés depuis ce fichier.
- `source/engine.js` : le son (mêmes modèles que `SIM/source/engine.js` pour les circuits déjà faits).
- `python3 source/build.py` régénère `index.html` ; `node source/test.js '{"svf.reso":0.9}' '[["lfo1.out","vcf.mod"]]' test.wav` rend 4 s et affiche les niveaux de chaque sortie.

## Dimensions

| | |
|---|---|
| Panneau | **461 × 387 mm** (3 rangées de 122 mm + bande logo de 17 mm, bandes argent de 8 mm) |
| Sliders | 62 sliders, course **60 mm**, pas de 15 mm, capuchon 9 × 12,4 mm (ex. Bourns PTA6043, série PTA 60 mm, à confirmer chez JLCPCB) |
| Jacks | 81 Thonkiconn 3,5 mm à contact de coupure (normalisations) |
| Inverseurs | 7 (RANGE ×3, SYNC, KBD, TIME ×2), mêmes Dailywell 2MS1 que les modules |

Si 60 mm ne plaît pas : passer à 45 mm (PTA4543) = changer `TRAVEL` et `SP` dans `source/app.js`, le panneau perd environ 15 mm par rangée.

## Sections

**Rangée 1 – SOURCES**
- **OSCILLATOR 1, 2, 3** (cœur 921 du VCO) : COARSE ±3 oct, FINE ±6 demi-tons, WIDTH, FM, PWM, RANGE AUDIO/LO. OSC 2 : SYNC (sur OSC 1). OSC 3 : STABILITY (dérive lente façon années 70) et KBD ON/OFF. Sorties SINE, TRI, SAW, PULSE.
- **RING MOD** (MC1496 du module RING MOD) : X LEVEL, Y LEVEL.
- **NOISE · S&H · LAG** (module S&H / LAG + bruit rose de NOISE TOOLS) : COLOR blanc → rose, CLOCK, RISE, FALL.

**Rangée 2 – FILTERS & AMPLIFIER**
- **AUDIO MIXER** : 5 sliders (OSC 1, OSC 2, OSC 3, NOISE, RING), alimente les deux filtres en parallèle.
- **LADDER FILTER 24 dB** (module VCF) : FREQUENCY, EMPHASIS, MODE LP → BP → HP, KBD, ENV, MOD.
- **STATE VARIABLE 12 dB** (nouveau) : FREQUENCY, RESONANCE, MODE LP → BP → HP → NOTCH, ENV, MOD.
- **AMPLIFIER** (902 du module VCA) : niveau LADDER, niveau STATE VAR., ENV, INITIAL (bourdon), RESP. LIN ↔ EXP.
- **SPRING REVERB** (module SPRING REVERB) : DRIVE, TONE, MIX.
- **OUTPUT** : VOLUME, sorties MAIN (niveau Eurorack) et PHONES.

**Rangée 3 – CONTROL**
- **KEYBOARD** : GLIDE ; sorties CV, GATE, TRIG ; entrées CV IN et GATE IN (un séquenceur Eurorack prend la place du clavier).
- **ENVELOPE 1 et 2** (911 du module ADSR) : ATTACK, DECAY, SUSTAIN, RELEASE, TIME FAST/SLOW (condensateur ×25, jusqu'à ~2 min), LED, sorties OUT et −OUT.
- **LFO 1 et 2** : RATE (0,02 à 50 Hz), WAVE en fondu continu RAMPE ↑ → TRI → RAMPE ↓ → CARRÉ, entrée RATE CV (1 V/oct), sorties OUT et TRIG, LED.
- **ATTENUVERTERS** : 2 sliders −1 à +1, entrée vide = +5 V (offset).
- **MULTIPLE** : 1 entrée, 3 sorties.

## Normalisations (câblage interne, coupé dès qu'un câble entre dans la prise)

| Entrée | Reçoit |
|---|---|
| 1V/OCT des 3 OSC, LADDER KBD | KEYBOARD CV (OSC 3 : seulement si KBD = ON) |
| FM des 3 OSC | LFO 1 |
| PWM des 3 OSC, STATE VAR. MOD | LFO 2 |
| OSC 2 SYNC | OSC 1 PULSE (si SYNC = ON) |
| RING X / Y | OSC 1 SAW / OSC 2 SAW |
| S&H IN / CLOCK / LAG IN | NOISE / CLOCK interne / S&H |
| MIXER 1 à 5 | OSC 1 SAW, OSC 2 PULSE, OSC 3 SAW, NOISE, RING |
| LADDER IN, STATE VAR. IN | MIX |
| LADDER ENV, STATE VAR. ENV | ENVELOPE 1 |
| LADDER MOD | S&H |
| AMPLIFIER LADDER / ST. VAR. / CV | LADDER OUT / STATE VAR. OUT / ENVELOPE 2 |
| REVERB IN → OUTPUT IN | AMPLIFIER OUT → REVERB OUT |
| GATE des 2 enveloppes | KEYBOARD GATE |
| ATTENUVERTERS IN 1 et 2 | +5 V |

## Prochaines étapes

1. Valider la disposition et la course des sliders dans le simulateur.
2. Schéma du filtre à variable d'état (seul circuit audio nouveau) et des 2 LFO.
3. Découper la fabrication par rangée : une carte + une façade par rangée (461 × 122 mm), reliées par nappes, alimentation ±12 V commune. Commencer par la rangée SOURCES (3 VCO).
