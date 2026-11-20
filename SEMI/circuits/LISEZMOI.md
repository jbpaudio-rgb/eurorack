# SEMI – circuits nouveaux, vérifiés dans SPICE

Les sections du SEMI qui ne viennent pas d'un module ocTavio Eurorack déjà fait. Chaque fichier `.py` contient le circuit complet (valeurs, liaisons, explications en tête), et chaque `test_*.py` le vérifie dans ngspice. Les résultats sont dans `resultats-*.txt` et `spice-svf-lfo.png`.

```
cd SEMI/circuits
python3 test_svf.py     # filtre à variable d'état
python3 test_lfo.py     # LFO
python3 test_midi.py    # MIDI, sorties CV, lecture CV IN / GATE IN, haut-parleur
```

## STATE VARIABLE 12 dB, façon Oberheim SEM (`svf.py`)
LM13700 (2 OTA intégrateurs), 2 × TL074, BCM857DS (convertisseur exponentiel PNP, les deux IABC reliés sur la même puce).
- **FREQUENCY** : 20 Hz → 20 kHz (10,0 octaves). **ENV** 0,8 oct/V et **MOD** 0,5 oct/V au maximum (mesurés : 0,80 et 0,50).
- **MODE** : un seul slider entre LP et HP, comme sur le SEM. LP en bas (−52 dB à 10 kHz), NOTCH au milieu (−41 dB au centre), HP en haut (−56 dB à 30 Hz). L'inverseur **BP** prend le passe-bande à la place.
- Pentes de 12 dB/octave mesurées. **RESONANCE** : de Q 0,5 à +22 dB de bosse, puis auto-oscillation stable à ±5,7 V. La limite vient des zeners D1 / D2 dans la boucle d'amortissement, et R23 / R24 garantissent le démarrage.
- Sature doucement quand la coupure est sur le signal : 0,6 % de distorsion à ±5 V, 1 % à ±10 V.

## LFO 1 et 2, analogiques (`lfo.py`)
Un LM13700 pour les deux (un OTA par LFO), 3 × TL074, 2 × BCM857DS.
- **RATE** : 0,022 → 50 Hz (11,2 octaves). **RATE CV** : 0,99 oct/V.
- **WAVE** : RAMPE ↑ → TRIANGLE → RAMPE ↓ **à vitesse constante** (±4 %). La symétrie passe par les deux moitiés du slider (diodes D3 / D4), donc la période ne dépend que de leur somme. Rampes à 92 / 8 %.
- Le carré n'est plus au bout du slider (il aurait demandé un VCA par LFO) : il a sa propre sortie **SQ** (±5,2 V). **TRIG** : 10 V pendant 5,6 ms au début de chaque montée. **OUT** ±4,9 V, LED.
- Trimmer **RV3** par LFO : annule l'offset du LM13700. Réglage : WAVE au milieu, tourner jusqu'à un triangle symétrique.

## KEYBOARD · MIDI et haut-parleur (`midi.py`, programme dans `../firmware`)
MIDI IN, MIDI OUT et USB sont à l'arrière, sur une petite carte avec le Pico, le H11L1, les DAC et leurs ampli-ops. Une nappe vers la façade transporte CV, GATE, TRIG, VEL, MOD, la lecture de CV IN / GATE IN, LEARN et la LED.
Raspberry Pi Pico, 2 × MCP4822 (DAC 12 bits), H11L1 (entrée MIDI), 2 × TL074, LM386.
- **MIDI IN** (prise DIN 5 broches) : 0 erreur sur 3 octets, venant d'un émetteur 5 V ou 3,3 V (6 à 9,5 mA dans la LED). **MIDI OUT** : 6,7 mA dans un récepteur standard.
- **USB-C** : USB-MIDI, reconnu sans pilote. Tout ce qui entre (MIDI IN ou USB) ressort sur MIDI OUT et USB.
- **CV** : −3,6 à +6,3 V. Note 60 (C4) = 0 V, donc les notes 17 à 127 sont jouables. 2,4 mV par pas, calibré en 2 points par le programme. **GATE** 5 V, **TRIG** 10 V (2 ms), **VEL** et **MOD** (molette) 0 à 10 V. Pitch bend ±2 demi-tons, priorité à la dernière note, legato.
- **CV → MIDI** : quand un séquenceur Eurorack joue CV IN / GATE IN, ses notes partent sur MIDI OUT et USB. Lecture de −10 à +10 V, entrées protégées jusqu'à ±15 V, seuil de gate 1,3 V.
- **LEARN** : appuyer, puis jouer une note, et son canal devient celui du SEMI. Appui de 2 s = omni.
- **Haut-parleur** 40 mm 8 Ω 1 W (au-dessus du MULT) : 200 mW pour une sortie à ±5 V, 0,8 W au maximum. Il est coupé quand un casque est branché, et par l'inverseur SPEAKER.

## Sorties MAIN OUT L / R à l'arrière (`sortie-ligne.cir`)

Par canal : diviseur 22k / 10k (+ 220 pF), suiveur TL072, 100 Ω, 10 µF, 100k vers la masse. 10 Vpp Eurorack donne 3,1 Vpp en ligne, plat de 20 Hz à 20 kHz à 0,2 dB près dans 10 kΩ. Un seul TL072 pour L et R. Le VOLUME de la façade passe à un slider double 60 mm (A10k ×2), IN L et IN R sont normalisées sur la sortie de la reverb par le contact de leur jack.

## Ce qu'il reste à faire
- Les schémas KiCad et les cartes des rangées (ces circuits seront dessinés avec le reste de leur rangée).
- Sur le prototype : régler RV3 des LFO, et calibrer le CV du MIDI (LEARN maintenu à l'allumage, voir `../firmware/semi_midi/semi_midi.ino`).
