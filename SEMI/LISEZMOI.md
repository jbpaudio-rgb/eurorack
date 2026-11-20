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
| Panneau | **475 × 387 mm** (3 rangées de 122 mm + bande logo de 17 mm, bandes argent de 8 mm) |
| Sliders | 62 sliders, course **60 mm**, pas de 15 mm, capuchon 9 × 12,4 mm (ex. Bourns PTA6043, série PTA 60 mm, à confirmer chez JLCPCB) |
| Jacks | 85 Thonkiconn 3,5 mm à contact de coupure (normalisations) ; MIDI et USB à l'arrière |
| Inverseurs | 9 (RANGE ×3, SYNC, KBD, BP, TIME ×2, SPEAKER), mêmes Dailywell 2MS1 que les modules ; 1 bouton LEARN |
| Haut-parleur | 40 mm, 8 Ω, 1 W, au-dessus du MULT (ampli LM386) |

Si 60 mm ne plaît pas : passer à 45 mm (PTA4543) = changer `TRAVEL` et `SP` dans `source/app.js`, le panneau perd environ 15 mm par rangée.

## Sections

**Rangée 1 – SOURCES**
- **OSCILLATOR 1, 2, 3** (cœur 921 du VCO) : COARSE ±3 oct, FINE ±6 demi-tons, WIDTH, FM, PWM, RANGE AUDIO/LO. OSC 2 : SYNC (sur OSC 1). OSC 3 : STABILITY (dérive lente façon années 70) et KBD ON/OFF. Sorties SINE, TRI, SAW, PULSE.
- **RING MOD** (MC1496 du module RING MOD) : X LEVEL, Y LEVEL.
- **NOISE · S&H · LAG** (module S&H / LAG + bruit rose de NOISE TOOLS) : COLOR blanc → rose, CLOCK, RISE, FALL.

**Rangée 2 – FILTERS & AMPLIFIER**
- **AUDIO MIXER** : 5 sliders (OSC 1, OSC 2, OSC 3, NOISE, RING), alimente les deux filtres en parallèle.
- **LADDER FILTER 24 dB** (module VCF) : FREQUENCY, EMPHASIS, MODE LP → BP → HP, KBD, ENV, MOD.
- **STATE VARIABLE 12 dB** (nouveau, façon Oberheim SEM) : FREQUENCY, RESONANCE (jusqu'à l'auto-oscillation), MODE LP → NOTCH → HP, inverseur BP, ENV, MOD.
- **AMPLIFIER** (902 du module VCA) : niveau LADDER, niveau STATE VAR., ENV, INITIAL (bourdon), RESP. LIN ↔ EXP.
- **SPRING REVERB** (module SPRING REVERB) : DRIVE, TONE, MIX.
- **OUTPUT** : VOLUME, sorties MAIN (niveau Eurorack) et PHONES.

**Rangée 3 – CONTROL**
- **KEYBOARD · MIDI** : GLIDE ; bouton LEARN (canal MIDI), LED MIDI ; sorties CV, GATE, TRIG, VEL, MOD ; entrées CV IN et GATE IN. Le MIDI (prise ou USB) joue le clavier interne ; un séquenceur Eurorack branché dans CV IN / GATE IN prend sa place, et ses notes ressortent en MIDI.
- **ENVELOPE 1 et 2** (911 du module ADSR) : ATTACK, DECAY, SUSTAIN, RELEASE, TIME FAST/SLOW (condensateur ×25, jusqu'à ~2 min), LED, sorties OUT et −OUT.
- **LFO 1 et 2** (nouveaux, analogiques) : RATE (0,02 à 50 Hz), WAVE RAMPE ↑ → TRI → RAMPE ↓ à vitesse constante, entrée RATE CV (1 V/oct), sorties OUT, SQ et TRIG, LED.
- **ATTENUVERTERS** : 2 sliders −1 à +1, entrée vide = +5 V (offset).
- **SPEAKER · MULT** : haut-parleur intégré (coupé par l'inverseur SPEAKER ou quand un casque est branché) ; multiple 1 entrée, 3 sorties.

## Normalisations (câblage interne, coupé dès qu'un câble entre dans la prise)

Sur la façade, le nom de la source est imprimé en gris sous chaque entrée normalisée (façon ARP 2600).

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

## Panneau arrière (`apercu-arriere.png`)
- **POWER** : embase IEC (C14) avec interrupteur et fusible (T 1 A), reliée à une alimentation fermée à **entrée universelle 100–240 V, 50/60 Hz** (Canada et Europe, sans commutateur ; seul le cordon change). Choix proposé : Mean Well RT-65C (+5 V, +15 V, −15 V, 88–264 VAC), suivie de régulateurs linéaires 7812 / 7912 pour des ±12 V propres. Le +5 V alimente le Pico. Plus simple mais plus bruyant : RT-65B (+5 V, +12 V, −12 V direct). Le 230 V ne va que de l'embase à l'alimentation : fils sertis et gainés, terre de l'embase vissée sur le châssis.
- **MAIN OUT L / R** (jacks 6,35 mm, niveau ligne : 10 Vpp Eurorack → 3,1 Vpp). Sur la façade, la section OUTPUT a **IN L** et **IN R** ; IN R reçoit IN L tant que rien n'y est branché, donc un patch mono sort des deux côtés. Le VOLUME devient un slider double (stéréo). MAIN (façade) = L + R au niveau Eurorack, PHONES en stéréo.
- **MIDI IN**, **MIDI OUT** (prises DIN 5 broches standard) et **USB-C** (USB-MIDI), juste à côté. Ils sont sur une petite carte arrière avec le Pico, l'optocoupleur, les DAC et leurs ampli-ops. Seuls les signaux CV / GATE / TRIG / VEL / MOD, la lecture de CV IN / GATE IN, le bouton LEARN et la LED vont vers la façade par une nappe. L'USB et le SPI restent courts.

## Circuits nouveaux
Le filtre à variable d'état, les LFO, la partie MIDI et le haut-parleur sont décrits et vérifiés dans SPICE dans `circuits/` (voir `circuits/LISEZMOI.md`). Le programme du Pico est dans `firmware/` : il compile pour le Pico, et sa logique passe 24 tests sur l'ordinateur (`firmware/test`).

## Prochaines étapes

1. Valider la disposition et la course des sliders dans le simulateur.
2. ~~Schéma du filtre à variable d'état et des 2 LFO~~ : fait et vérifié dans SPICE (`circuits/`), avec le MIDI et le haut-parleur.
3. Découper la fabrication par rangée : une carte + une façade par rangée (475 × 122 mm), reliées par nappes, alimentation ±12 V commune. Commencer par la rangée SOURCES (3 VCO).
