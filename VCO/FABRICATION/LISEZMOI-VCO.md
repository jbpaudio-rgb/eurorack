# Octavio VCO — oscillateur façon Moog 921, Eurorack 12 HP (rev 0.5)

> **rev 0.5 (17 nov. 2026)** : remise à zéro corrigée après simulation SPICE de la carte complète (la rev 0.4 ne démarrait pas). Carte vérifiée dans SPICE : oscille, suit le 1 V/oct, SYNC fonctionne – voir `outils/spice/LISEZMOI.md`.

## Façade (de haut en bas)
- **rev 0.4 : passage en 12 HP** pour donner de l'espace : FREQUENCY et WIDTH en gros boutons gradués, FM / PWM / BLEND en boutons moyens, colonnes plus larges.
- **VCO** entre les trous du haut
- **RANGE** (sélecteur 6 positions comme le 921) : **LO, 32', 16', 8', 4', 2'** = −7, −2, −1, 0, +1, +2 octaves. 8' ≈ do central (≈ 262 Hz), LO ≈ 2 Hz (LFO).
- **FREQUENCY** (± 6 demi-tons à l'intérieur de la plage, comme sur le Moog) et **WIDTH** (largeur du carré)
- Rangée du milieu : **FM** (atténuateur + entrée), **PWM** (atténuateur + entrée), **BLEND** (bouton entouré des 4 formes d'onde dessinées) et sa sortie **OUT** juste en dessous
- Grille du bas : **1V/OCT** et **SYNC** (colonne de gauche), sorties **SINE**, **TRIANGLE**, **SAW**, **PULSE** (± 5 V), comme les 4 sorties du 921

## Circuit
- **RANGE** (mini commutateur SR16 1 circuit 8 positions, butée sur 6) : échelle de résistances 0,1 % (R1, R2, R6, R48–R51) entre +12 V et −12 V qui donne exactement −7, −2, −1, 0, +1, +2 V ; le commutateur choisit un point, U2D le tamponne et l'envoie au convertisseur par R53 (100k 0,1 %). La justesse des octaves dépend de la précision des rails ±12 V (≈ 1 %), corrigeable avec FREQUENCY.
- **Convertisseur exponentiel** 1 V/oct : U1A additionne 1V/OCT (R5 100k 0,1 %), RANGE, FREQUENCY et FM, et attaque la base du transistor de référence d'une paire appairée (Q1, BC847DS) ; U1B fixe le courant de référence (≈ 13 µA à 0 V).
  - Compensation thermique : R9 = résistance 1k à **+3300 ppm/K**, à coller contre Q1 (pâte thermique ou colle). Sans elle, l'accord dérive avec la température.
- **Cœur dent de scie** (comme le 921) : le courant charge C10 (10 nF C0G) dans l'intégrateur U1C. Quand la rampe atteint 5 V, le comparateur U1D bascule. Il est monté en **monostable** : la rampe arrive par R96 (10k), et C22 (330 pF) + R97 (1M) le maintiennent haut ≈ 4–5 µs, quelle que soit la vitesse de la rampe. Pendant ce temps, D9 + R98 (4,7k, C11 en parallèle) tirent la grille du JFET Q2 vers le haut. Q2, branché directement aux bornes de C10 (HFC ↔ INTN), vide le condensateur. Au repos, R15 tient la grille à −12 V : le JFET est bien bloqué, quelle que soit sa tension de pincement.
- **SYNC** : un front montant sur l'entrée passe par C12 et D3 vers l'entrée + de U1D et déclenche la même remise à zéro (synchro dure).
- **SAW** (U2A), **TRIANGLE** (redresseur double alternance U2B/U2C), **SINE** (paire différentielle Q3 qui arrondit le triangle, puis U3A en ampli différentiel à haute impédance : R33 / R35 470k, R34 / R36 560k, pour ne pas charger les collecteurs de 47k ; ≈ 2 % de distorsion dans SPICE), **PULSE** (comparateur U3B, largeur U3C = WIDTH + PWM, sortie U3D).

- **BLEND** : fondu continu SINE → TRIANGLE → SAW → PULSE. OUT = S + c1·(T−S) + c2·(SAW−T) + c3·(P−SAW). U4 calcule les trois différences et la somme ; trois OTA (U6, U7 = LM13700) dosent chaque différence ; U5 fabrique c1, c2, c3 à partir du bouton (chacun monte de 0 à 1 sur un tiers de la course, butées par zener) ; U5D remet la sortie dans le bon sens. Le carré peut sonner plus fort que le sinus en fin de course : c'est voulu (comme passer d'une sortie à l'autre).

## Simulation
- **SPICE de la carte entière** (`outils/spice/run.sh`, netlist tirée du `.kicad_pcb`) : 252 Hz à 0 V avant calibration, dent de scie parfaite (harmoniques en 1/n), TRIANGLE et PULSE ±5 V, SINE ≈ 2 % de distorsion, SYNC qui accroche. Petit pic de 2–3 V pendant les ≈ 4 µs du reset sur TRIANGLE et SINE.
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
- Carte **routée** (4 couches) : la rev 0.5 a ajouté R96, R97, R98, C22 et D9 au dos, routés à part (écartement minimal 0,12 mm, JLC accepte 0,09 mm en 4 couches).
