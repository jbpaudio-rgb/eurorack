# Octavio VCO — oscillateur façon Moog 921, Eurorack 8 HP (rev 0.1)

## Façade (de haut en bas)
- **VCO** entre les trous du haut
- **FREQUENCY** (gros bouton, gradué −5 … +5 octaves autour du do central ≈ 262 Hz → ≈ 8 Hz à ≈ 8 kHz)
- **FINE** (± ½ octave, ≈ ± 6 demi-tons comme le 921) et **WIDTH** (largeur du carré)
- Entrées : **1V/OCT** et **SYNC** (colonne de gauche), **FM** et **PWM** avec leur petit atténuateur
- Sorties : **SINE**, **TRIANGLE**, **SAW**, **PULSE** (± 5 V), comme les 4 sorties du 921

## Circuit
- **Convertisseur exponentiel** 1 V/oct : U1A additionne 1V/OCT (R5 100k 0,1 %), FREQUENCY, FINE et FM, et attaque la base du transistor de référence d'une paire appairée (Q1, BC847DS) ; U1B fixe le courant de référence (≈ 13 µA à 0 V).
  - Compensation thermique : R9 = résistance 1k à **+3300 ppm/K**, à coller contre Q1 (pâte thermique ou colle). Sans elle, l'accord dérive avec la température.
- **Cœur dent de scie** (comme le 921) : le courant charge C10 (10 nF C0G) dans l'intégrateur U1C ; quand la rampe atteint 5 V, le comparateur U1D envoie une impulsion qui fait conduire le JFET Q2 et vide le condensateur.
- **SYNC** : un front montant sur l'entrée déclenche la même remise à zéro (synchro dure).
- **SAW** (U2A), **TRIANGLE** (redresseur double alternance U2B/U2C), **SINE** (paire différentielle Q3 qui arrondit le triangle, ≈ 1,4 % de distorsion, puis U3A), **PULSE** (comparateur U3B, largeur U3C = WIDTH + PWM, sortie U3D).

## Simulation
- Convertisseur expo (transistors) : rapport d'octave exact à mieux que 0,4 % de −5 à +5 V (≈ 6 cents à +5 octaves).
- Le temps de remise à zéro (≈ 4 µs) fait baisser les aigus de ≈ 3 % à 8 kHz → compensé par **RV8** (en série avec C10).

## Calibration (une fois, module chaud)
1. FREQUENCY et FINE au centre, rien dans 1V/OCT.
2. **RV7 (V/OCT)** : envoyer 1 V puis 3 V depuis un clavier/séquenceur précis, régler pour avoir exactement 2 octaves d'écart ; répéter.
3. **RV8 (HF)** : à 4–5 octaves au-dessus, régler pour que les octaves aiguës restent justes.
4. **RV9 (SINE)** : régler pour un sinus symétrique (haut et bas pareils à l'oscilloscope, ou au son le plus « rond »).

## À vérifier avant de commander
- **R9 tempco** (1k +3300 ppm, ex. KOA LT73V ou Panasonic ERA-S) : disponibilité LCSC.
- **MMBFJ112** (JFET N, SOT-23) : brochage D-S-G à confirmer avec la fiche du fabricant choisi.
- Empreintes de façade (`octavio_mu`) : jacks et pots 9 mm (FM et PWM montés tournés de 180°).
- Carte placée, **pas encore routée**. Au routage : Q1, R9 et C10 près de U1, pistes courtes.
