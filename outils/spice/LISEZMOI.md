# Simulation SPICE des cartes (ngspice)

`kicad2spice.py` lit une carte KiCad (`.kicad_pcb` pour les liaisons réelles des pastilles, `.kicad_sch` pour les broches de la bibliothèque `octavio_mu`) et écrit une netlist ngspice avec **tous les composants et leurs vraies valeurs**. Modèles : BC847 (NXP), J112, 1N4148, zener 5,1 V, TL07x (3 MHz, 13 V/µs, sortie à 1,5 V des rails), LM13700 (OTA tanh + diodes de linéarisation + darlington).

```
sudo apt install ngspice
bash outils/spice/run.sh  o0 0 "" 0.04        # VCO (carte actuelle), 1V/OCT = 0 V, 40 ms
bash outils/spice/vcf.sh  vf 0.5 0.35 0       # VCF : FREQUENCY 0.5, EMPHASIS 0.35, MODE LP -> réponse en fréquence
```
`ana.py` donne la fréquence, les niveaux et les harmoniques ; `spice-vco-vcf.png` résume les résultats.

## Résultats (17 nov. 2026)

### VCO (921) – corrigé en rev 0.5
La rev 0.4, telle que dessinée, **le cœur ne démarre pas** : la rampe monte jusqu'au rail (+10 V) et reste bloquée.
1. **Comparateur de reset (U1D) sans hystérésis** : la rampe monte lentement (≈ 1 V/ms à 250 Hz), le TL074 bascule en 20–40 µs au lieu de ~1,5 µs. L'impulsion passe par C11 (220 p) / R15 (22 k), dont la constante de temps est de 4,8 µs : la grille du JFET ne monte qu'à ≈ −3,6 V, le JFET ne conduit pas.
2. **D3 (SYNC) conduit au repos** (R16 à la masse) : la grille reste vers −4 V au lieu de −12 V. Un J112 dont la tension de pincement est près de −5 V (dans la tolérance) serait toujours passant.
3. **Le JFET décharge C10 à travers RV8** (drain sur RAMP) : avec RV8 au milieu (500 Ω), la décharge est trop lente pour une impulsion de quelques µs.
4. **Sortie SINE à ±0,9 V au lieu de ±5 V** : les résistances de 10 k / 12 k de U3A chargent les collecteurs de 47 k de Q3.

**Correction appliquée au schéma et à la carte (rev 0.5), vérifiée dans SPICE sur la netlist de la nouvelle carte** (R96, R97, C22, D9, R98 ajoutés) :
- U1D en monostable : entrée + = RAMP par 10 k, 330 pF + 1 MΩ de RSTQ vers cette entrée (impulsion ≈ 4–5 µs, quelle que soit la vitesse de la rampe) ;
- grille commandée en continu : RSTQ → 1N4148 → 4,7 k (220 pF en parallèle) → GATE, R15 22 k vers −12 V (JFET bien bloqué au repos) ; C11 supprimé ;
- drain du JFET sur HFC (directement aux bornes de C10) ;
- D3 (SYNC) vers l'entrée + de U1D au lieu de la grille ;
- R33 / R35 = 470 k, R34 / R36 = 560 k.

Résultat : oscillation propre, 252 Hz à 0 V (FREQUENCY au milieu, avant calibration), dent de scie à harmoniques en 1/n (rampe parfaitement droite), triangle et pulse ±5 V, sinus ≈ 2 % de distorsion. Suivi avant calibration : ≈ +7 % par octave, dans la plage de RV7. Petit pic de 2–3 V pendant le reset sur TRIANGLE et SINE (quelques µs). SYNC : un train d'impulsions à 300 Hz accroche le VCO à 300,1 Hz.

`outils/schpcbcheck.py` vérifie que chaque étiquette du schéma correspond au net de la même pastille sur la carte (0 écart sur le VCO rev 0.5). `outils/pcbedit.py` + `outils/finish.py` ont servi à modifier la carte routée, et `outils/jlcfrompcb.py` à refaire le CPL / BOM.

### VCF (ladder) – fonctionne, mais…
- Coupure : ≈ 100 Hz (FREQUENCY 0,25) → 515 Hz (0,5) → 2,6 kHz (0,75) → **≈ 13 kHz au maximum** (et non 20 kHz) : R50 à ajuster si on veut plus haut.
- Gain : −3,5 dB dans la bande passante. Perte de grave avec EMPHASIS : −5 dB à 0,35, −14 dB au maximum (comme sur un Moog). Auto-oscillation vers 0,9.
- **Mode LP imparfait** : la sortie LP = BP + a·(LP − BP) n'est un vrai 24 dB que si le gain de l'OTA vaut exactement a = 1. Dans SPICE, il reste une fuite de passe-bande à ≈ −18 dB au-dessus de la coupure (creux puis remontée, voir le graphique). Le LP est donc moins sombre que prévu. Pistes : un trimmer pour régler a = 1 en position LP, ou une architecture où chaque sortie (LP, BP, HP) a son propre OTA dont le courant tombe à zéro aux extrémités : un zéro est exact, un gain de 1 ne l'est pas.

## Bancs de test de tous les modules analogiques (`bench.py`)
`python3 outils/spice/bench.py all` (ou un module : `VCA`, `AD`…) : chaque carte entière, des sources sur les jacks, des mesures. Les résultats sont dans `bench-<MODULE>.txt`. Les pots marqués A sont simulés en courbe logarithmique.

| Module | Résultat SPICE | Corrigé |
|---|---|---|
| **VCO** | ne démarrait pas (reset), SINE à ±0,9 V | **oui, rev 0.5** (carte routée refaite) |
| **COMPLEX** | **les deux cœurs ne démarraient pas** (même reset que le VCO) ; SINE à ±0,9 V | **oui** : même correction sur les deux cœurs (R193–R198, C47, C48, D19, D20) + R88 / R90 470k, R89 / R91 560k. Les deux oscillateurs tournent (≈ 510 Hz et 840 Hz, boutons au milieu) |
| **S&H / LAG** | **le S&H ne tenait pas** : R17 (1M) entre la grille du JFET et le condensateur de maintien le vidait (≈ 100 V/s) et la grille montait trop lentement pendant l'impulsion | **oui** : R17 = 100k vers l'entrée tamponnée (SHIN_B). Échantillons justes à quelques mV, aucune dérive mesurable en 50 ms |
| **NOISE TOOLS** | même défaut de S&H (R24) | **oui** : R24 = 100k vers SHIN_B |
| **ATT / INV** | l'entrée vide donnait +3,6 V au lieu de +5 V (diviseur 14k / 10k trop faible pour 3 entrées) | **oui** : R1 = 1k4, R2 = 1k → +4,7 V |
| **VCA** | fonctionne : ×1,1 à 5 V, ×1,3 à 10 V (saturation douce), EXP OK, coupure à 0 V. Fuite de CV ≈ 0,9 V trimmer au milieu, **réglable à ≈ 0** avec RV2 (vers 35 % de la course) | réglage seulement |
| **AD** | fonctionne : crête 9,35 V, attaque / decay comme prévu, CYCLE ≈ 120 Hz réglages rapides | — |
| **ADSR** | fonctionne : crête 9,7 V, sustain suit le bouton, relance correcte sur des gates de 20 ms | — |
| **MIX** | fonctionne : gain 1, −OUT inversé, saturation douce au MASTER | — |
| **RING MOD** | fonctionne : vrai produit (bandes 850 / 1150 Hz), fuite de X −23 dB et de Y −44 dB trimmers au milieu (à régler), Y vide = VCA | réglage seulement |
| **SPRING REVERB** | driver : jusqu'à ≈ 6,5 mA dans la cuve. Avec un modèle de cuve estimé (sortie ≈ 0,6 V/A), WET ≈ 17 dB sous le sec à DRIVE maximum | **à vérifier avec la vraie cuve** : si le retour est trop faible, augmenter le gain de U3B |
| bruit (NOISE TOOLS, S&H / LAG) | non simulable : SPICE ne modélise pas l'avalanche base-émetteur | — |
| STAGES, LFOs | numériques (RP2040) : rien à simuler ici | — |

### Simulateurs
Le simulateur SEMI a été recalé sur ces résultats : rampe droite et sans filtrage, plage du ladder 20 Hz → 13 kHz, courbe d'EMPHASIS et gain de −3,5 dB mesurés. Il garde volontairement le LP « idéal » (24 dB), c'est-à-dire le son visé une fois le mode corrigé.
