# Octavio VCO — oscillateur façon Moog 921, Eurorack 12 HP (rev 0.4)

## Façade (de haut en bas)
- **rev 0.4 : passage en 12 HP** pour donner de l'espace : FREQUENCY et WIDTH en gros boutons gradués, FM / PWM / BLEND en boutons moyens, colonnes plus larges.
- **VCO** entre les trous du haut
- **RANGE** (sélecteur 6 positions comme le 921) : **LO, 32', 16', 8', 4', 2'** = −7, −2, −1, 0, +1, +2 octaves. 8' ≈ do central (≈ 262 Hz), LO ≈ 2 Hz (LFO).
- **FREQUENCY** (± 6 demi-tons à l'intérieur de la plage, comme sur le Moog) et **WIDTH** (largeur du carré)
- Rangée du milieu : **FM** (atténuateur + entrée), **PWM** (atténuateur + entrée), **BLEND** (bouton entouré des 4 formes d'onde dessinées) et sa sortie **OUT** juste en dessous
- Grille du bas : **1V/OCT** et **SYNC** (colonne de gauche), sorties **SINE**, **TRIANGLE**, **SAW**, **PULSE** (± 5 V), comme les 4 sorties du 921

## Circuit
- **RANGE** : échelle de résistances 0,1 % (R1, R2, R6, R48–R51) entre +12 V et −12 V qui donne exactement −7, −2, −1, 0, +1, +2 V ; le commutateur choisit un point, U2D le tamponne et l'envoie au convertisseur par R53 (100k 0,1 %). La justesse des octaves dépend de la précision des rails ±12 V (≈ 1 %), corrigeable avec FREQUENCY.
- **Convertisseur exponentiel** 1 V/oct : U1A additionne 1V/OCT (R5 100k 0,1 %), RANGE, FREQUENCY et FM, et attaque la base du transistor de référence d'une paire appairée (Q1, BC847DS) ; U1B fixe le courant de référence (≈ 13 µA à 0 V).
  - Compensation thermique : R9 = résistance 1k à **+3300 ppm/K**, à coller contre Q1 (pâte thermique ou colle). Sans elle, l'accord dérive avec la température.
- **Cœur dent de scie** (comme le 921) : le courant charge C10 (10 nF C0G) dans l'intégrateur U1C ; quand la rampe atteint 5 V, le comparateur U1D envoie une impulsion qui fait conduire le JFET Q2 et vide le condensateur.
- **SYNC** : un front montant sur l'entrée déclenche la même remise à zéro (synchro dure).
- **SAW** (U2A), **TRIANGLE** (redresseur double alternance U2B/U2C), **SINE** (paire différentielle Q3 qui arrondit le triangle, ≈ 1,4 % de distorsion, puis U3A), **PULSE** (comparateur U3B, largeur U3C = WIDTH + PWM, sortie U3D).

- **BLEND** : fondu continu SINE → TRIANGLE → SAW → PULSE. OUT = S + c1·(T−S) + c2·(SAW−T) + c3·(P−SAW). U4 calcule les trois différences et la somme ; trois OTA (U6, U7 = LM13700) dosent chaque différence ; U5 fabrique c1, c2, c3 à partir du bouton (chacun monte de 0 à 1 sur un tiers de la course, butées par zener) ; U5D remet la sortie dans le bon sens. Le carré peut sonner plus fort que le sinus en fin de course : c'est voulu (comme passer d'une sortie à l'autre).

## Simulation
- Convertisseur expo (transistors) : rapport d'octave exact à mieux que 0,4 % de −5 à +5 V (≈ 6 cents à +5 octaves).
- Le temps de remise à zéro (≈ 4 µs) fait baisser les aigus de ≈ 3 % à 8 kHz → compensé par **RV8** (en série avec C10).

## Calibration (une fois, module chaud)
1. RANGE sur 8', FREQUENCY au centre, rien dans 1V/OCT.
2. **RV7 (V/OCT)** : envoyer 1 V puis 3 V depuis un clavier/séquenceur précis, régler pour avoir exactement 2 octaves d'écart ; répéter.
3. **RV8 (HF)** : à 4–5 octaves au-dessus, régler pour que les octaves aiguës restent justes.
4. **RV9 (SINE)** : régler pour un sinus symétrique (haut et bas pareils à l'oscilloscope, ou au son le plus « rond »).

## À vérifier avant de commander
- **Commutateur RANGE** : rotatif 1 circuit 12 positions avec butée réglable sur 6 (type Alpha SR16 / Lorlin CK1049). L'empreinte `Rotary_1P12T_Alpha_SR16` est une **approximation** : la remplacer par celle du modèle choisi (et ajuster le trou de façade, 9,6 mm prévu).
- **R9 tempco** (1k +3300 ppm, ex. KOA LT73V ou Panasonic ERA-S) : disponibilité LCSC.
- **MMBFJ112** (JFET N, SOT-23) : brochage D-S-G à confirmer avec la fiche du fabricant choisi.
- Empreintes de façade (`octavio_mu`) : jacks et pots 9 mm (FM et PWM montés tournés de 180°).
- **LM13700** (U6, U7) : disponibilité LCSC (sinon NJM13700).
- Carte dense : résistances et condensateurs en **0603**, trimmers en **CMS (Bourns 3314J)**.
- Carte placée, **pas encore routée**. Au routage : Q1, R9 et C10 près de U1, pistes courtes.
