# Octavio COMPLEX — oscillateur complexe façon Buchla Music Easel, Eurorack 16 HP (rev 0.1)

Inspiré de la partie oscillateurs de la Music Easel (208) : un **oscillateur de modulation** qui module un **oscillateur complexe** en FM ou en AM, et un oscillateur complexe dont on travaille le timbre (repliement du sinus) et la forme d'onde. Circuit conçu par nous (pas une copie du 208), avec nos cœurs de VCO 921.

## Façade
**Gauche : MODULATION OSCILLATOR**
- **FREQUENCY** (gros bouton) : ±3,4 octaves
- **RANGE HI / LO** : LO descend de 6 octaves (≈ 0,4 à 40 Hz, LFO) ; HI ≈ 25 Hz à 2,7 kHz
- **WAVE** (inverseur 3 positions) : dent de scie / carré (centre) / triangle
- **INDEX** : profondeur de modulation ; **MODE FM / AM**
- Jacks : **MOD CV** (1 V/oct), **INDEX CV**, **MOD OUT**

**Droite : COMPLEX OSCILLATOR**
- **PITCH** (gros bouton) : ±3,4 octaves autour de 262 Hz (≈ 25 Hz à 2,7 kHz)
- **WAVE** (inverseur 3 positions) : cible du WAVESHAPE = pointe (spike) / carré (centre) / triangle
- **WAVESHAPE** : fondu continu du sinus (replié) vers la cible ; **TIMBRE** : repliement du sinus
- Jacks : **1V/OCT**, **TIMBRE CV**, **SHAPE CV**, **OUT**

## Circuit
- **Deux cœurs dent de scie façon 921** (comme notre VCO) : convertisseur expo à paire appairée + résistance tempco, intégrateur 10 nF C0G, remise à zéro par JFET ; dent de scie, triangle (redresseur double alternance), carré (comparateur). Réglages V/OCT et HF par cœur.
- **Oscillateur complexe** : sinus par paire différentielle (+ symétrie), **spike** = impulsion étroite négative en fin de rampe (≈ 5 %), comme l'Easel.
- **TIMBRE** : un OTA (LM13700) amplifie le sinus de ×1 à ×4, puis un replieur à deux seuils (2,6 V et 7,8 V, redresseurs de précision TL074) le replie une ou deux fois → sortie ±5 V.
- **WAVESHAPE** : OUT = REPLIÉ + s·(CIBLE − REPLIÉ), s donné par un OTA (même principe que le BLEND du VCO).
- **INDEX** : OTA sur le signal de modulation (±2,5 V au maximum). **FM** : ajouté au convertisseur expo de l'oscillateur complexe (±2,5 octaves). **AM** : OTA de sortie, gain 1 + 0,4 × modulation (pleine profondeur à fond).
- Commandes d'OTA : bouton + CV, courant Iabc = tension / R1 ; une résistance R2 = R1/9 vers −12 V annule la tension de la broche Iabc (zéro propre à 0 V).
- 9 × TL074, 2 × LM13700, 4 paires BC847DS, 2 JFET.

## Calibration (module chaud)
1. Oscillateur complexe : PITCH au centre, régler le trimmer V/OCT du cœur C pour avoir exactement 2 octaves entre 1 V et 3 V sur 1V/OCT ; puis le trimmer HF dans les aigus.
2. Même chose pour l'oscillateur de modulation (MOD CV, RANGE sur HI).
3. Trimmer de symétrie du sinus : TIMBRE et WAVESHAPE à 0, sinus symétrique.

## À vérifier avant de commander
- **Inverseurs 3 positions** SW2 / SW4 : SPDT **ON-OFF-ON** (ex. C&K T103MH9ABE ; le centre « OFF » laisse passer le carré par une résistance de 10 kΩ). SW1 / SW3 : ON-ON (T101MH9ABE). Vérifier disponibilité LCSC.
- **LM13700**, **BC847DS**, **MMBFJ112**, résistances tempco 1k +3300 ppm (×2) : disponibilité LCSC.
- Empreintes de façade (`octavio_mu`) : jacks, pots 9 mm, inverseurs.
- Carte 16 HP placée (beaucoup de composants), **pas encore routée**.
