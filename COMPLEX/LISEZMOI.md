# Octavio COMPLEX — générateur d'onde complexe façon Buchla 259, Eurorack 30 HP (rev 0.3)

> **17 nov. 2026 – SPICE** : les deux cœurs ne démarraient pas (même défaut de remise à zéro que le VCO rev 0.4). Correction du VCO rev 0.5 appliquée aux deux cœurs (R193–R198, C47, C48, D19, D20) et sortie SINE à haute impédance (R88 / R90 470k, R89 / R91 560k). Voir `outils/spice/LISEZMOI.md`.

Architecture reprise du **Buchla 259** (et de sa version Eurorack 259t), avec **notre propre circuit** : cœurs dent de scie de notre VCO 921, OTA LM13700, replieurs à redresseurs de précision. La rev 0.1 (façon Music Easel, 16 HP) est dans l'historique GitHub.

## Façade (4 zones)
MODULATION OSCILLATOR et COMPLEX OSCILLATOR ont la même largeur (≈ 44 mm), HARMONICS est plus serrée.

**MODULATION OSCILLATOR**
- **FREQUENCY** (≈ 27 Hz à 7 kHz, 8 octaves), **FINE** (± une quinte), **RANGE AUDIO / LFO** (LFO = 7 octaves plus bas)
- **WAVE** : triangle / carré (centre) / dent de scie pour la sortie **SIGNAL** ; sortie **TRI** fixe
- **CV** (atténuverteur) et **FM** (atténuateur) ; jacks **1V/OCT**, **CV**, **FM**

**MODULATION**
- **MOD INDEX** : atténuverteur (− / 0 / +) sur le signal de modulation, + jack **INDEX CV**
- **PHASE LOCK** (atténuateur, sous MOD INDEX) : accroche l'oscillateur principal sur le signal entrant
- Inverseurs **AMPL**, **TIMBRE**, **PITCH** l'un sous l'autre, levier couché (gauche = ON, comme le 259t) : la modulation va vers l'amplitude, la hauteur et/ou le timbre de l'oscillateur principal
- Jacks **INDEX CV** et **PHASE LOCK** en bas de la section

**COMPLEX OSCILLATOR**
- **FREQUENCY**, puis **FINE** seul, puis **CV** (atténuverteur) et **FM** (atténuateur) côte à côte ; jacks **1V/OCT**, **CV**, **FM** ; sorties **SINE** et **SQUARE**

**HARMONICS**
- **TIMBRE** (gros bouton), **TIMBRE CV** (atténuateur) seul dessous, puis **SYMMETRY** et **ORDER** côte à côte ; jacks **SYMMETRY**, **TIMBRE** (CV), **ORDER** et sortie **FINAL** en grille 2 × 2
- **ORDER à gauche (FOLD)** : sortie = replieur ; TIMBRE = quantité de repli, SYMMETRY = décalage continu → repli asymétrique
- **ORDER à droite (SHAPE)** : TIMBRE fond le sinus vers la paire dent de scie / forme en M, SYMMETRY dose entre les deux
- Entre les deux, ORDER fond les deux chemins

## Circuit
- **Cœurs** : convertisseur expo (paire appairée + tempco), intégrateur 10 nF C0G, remise à zéro par JFET ; 0 V = 440 Hz (R 549k). Sinus par paire différentielle (trimmer de symétrie), carré par comparateur.
- **MOD INDEX** : atténuverteur passif (signal et son inverse sur le pot) + OTA commandé par INDEX CV, sommés → MIN. AMPL → commande de l'OTA de sortie (gain 1 ± MIN/5), PITCH → expo principal (200 kΩ, ±2,5 octaves à fond), TIMBRE → commande de timbre.
- **PHASE LOCK** : entrée couplée en alternatif, atténuée, injectée dans la référence de remise à zéro du cœur principal (verrouillage par injection : la rampe se termine sur les crêtes du signal).
- **Replieur** : OTA ×1 à ×4 sur le sinus + décalage SYMMETRY, puis redresseurs de précision à 2,6 V et 7,8 V (un ou deux replis), sortie ±5 V.
- **Forme M** : repli doux du sinus à 2,5 V (le sommet se creuse en M, proche d'un carré arrondi). **Dent de scie** : celle du cœur.
- **Fondus** (même principe que le BLEND du VCO) : X = SAW → M (SYMMETRY), Y = SINE → X (TIMBRE), FINAL = REPLIÉ → Y (ORDER), puis AM.
- 12 × TL074, 3 × LM13700, 4 paires BC847DS, 2 JFET MMBFJ112.

## Calibration (module chaud)
1. Principal : FREQUENCY et FINE au centre, trimmer V/OCT pour 2 octaves exactes entre 1 V et 3 V sur 1V/OCT, puis trimmer HF dans les aigus.
2. Modulation : même chose (RANGE sur AUDIO).
3. Symétrie du sinus : TIMBRE, SYMMETRY au centre, ORDER à gauche → sinus symétrique sur SINE.

## À vérifier avant de commander
- Inverseurs : SW2 SPDT **ON-OFF-ON** (centre = carré), les autres **ON-ON** (C&K T101 / T103) ; AMPL / PITCH / TIMBRE espacés de 12,5 mm.
- **LM13700**, **BC847DS**, **MMBFJ112**, résistances tempco 1k +3300 ppm (×2) : disponibilité LCSC.
- Carte 30 HP placée (≈ 320 composants), **pas encore routée** : prévoir 4 couches ou deux cartes empilées.
