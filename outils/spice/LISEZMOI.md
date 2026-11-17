# Simulation SPICE des cartes (ngspice)

`kicad2spice.py` lit une carte KiCad (`.kicad_pcb` pour les liaisons réelles des pastilles, `.kicad_sch` pour les broches de la bibliothèque `octavio_mu`) et écrit une netlist ngspice avec **tous les composants et leurs vraies valeurs**. Modèles : BC847 (NXP), J112, 1N4148, zener 5,1 V, TL07x (3 MHz, 13 V/µs, sortie à 1,5 V des rails), LM13700 (OTA tanh + diodes de linéarisation + darlington).

```
sudo apt install ngspice
bash outils/spice/run.sh  o0 0 "" 0.04        # VCO tel quel, 1V/OCT = 0 V, 40 ms
bash outils/spice/runf.sh c0 0 0.04           # VCO avec la correction proposée (voir plus bas)
bash outils/spice/vcf.sh  vf 0.5 0.35 0       # VCF : FREQUENCY 0.5, EMPHASIS 0.35, MODE LP -> réponse en fréquence
```
`ana.py` donne la fréquence, les niveaux et les harmoniques ; `spice-vco-vcf.png` résume les résultats.

## Résultats (17 nov. 2026)

### VCO (921) – **ne pas commander tel quel**
Tel que dessiné, **le cœur ne démarre pas** : la rampe monte jusqu'au rail (+10 V) et reste bloquée.
1. **Comparateur de reset (U1D) sans hystérésis** : la rampe monte lentement (≈ 1 V/ms à 250 Hz), le TL074 bascule en 20–40 µs au lieu de ~1,5 µs. L'impulsion passe par C11 (220 p) / R15 (22 k), dont la constante de temps est de 4,8 µs : la grille du JFET ne monte qu'à ≈ −3,6 V, le JFET ne conduit pas.
2. **D3 (SYNC) conduit au repos** (R16 à la masse) : la grille reste vers −4 V au lieu de −12 V. Un J112 dont la tension de pincement est près de −5 V (dans la tolérance) serait toujours passant.
3. **Le JFET décharge C10 à travers RV8** (drain sur RAMP) : avec RV8 au milieu (500 Ω), la décharge est trop lente pour une impulsion de quelques µs.
4. **Sortie SINE à ±0,9 V au lieu de ±5 V** : les résistances de 10 k / 12 k de U3A chargent les collecteurs de 47 k de Q3.

**Correction proposée et vérifiée dans SPICE (`runf.sh`)** :
- U1D en monostable : entrée + = RAMP par 10 k, 330 pF + 1 MΩ de RSTQ vers cette entrée (impulsion ≈ 4–5 µs, quelle que soit la vitesse de la rampe) ;
- grille commandée en continu : RSTQ → 1N4148 → 4,7 k (220 pF en parallèle) → GATE, R15 22 k vers −12 V (JFET bien bloqué au repos) ; C11 supprimé ;
- drain du JFET sur HFC (directement aux bornes de C10) ;
- D3 (SYNC) vers l'entrée + de U1D au lieu de la grille ;
- R33 / R35 = 470 k, R34 / R36 = 560 k.

Avec ces changements : oscillation propre, 252 Hz à 0 V (FREQUENCY au milieu, avant calibration), dent de scie à harmoniques en 1/n (rampe parfaitement droite), triangle et pulse ±5 V, sinus ≈ 2 % de distorsion. Suivi avant calibration : ≈ +7 % par octave, dans la plage de RV7. Petit pic de 2–3 V pendant le reset sur TRIANGLE et SINE (quelques µs).

### VCF (ladder) – fonctionne, mais…
- Coupure : ≈ 100 Hz (FREQUENCY 0,25) → 515 Hz (0,5) → 2,6 kHz (0,75) → **≈ 13 kHz au maximum** (et non 20 kHz) : R50 à ajuster si on veut plus haut.
- Gain : −3,5 dB dans la bande passante. Perte de grave avec EMPHASIS : −5 dB à 0,35, −14 dB au maximum (comme sur un Moog). Auto-oscillation vers 0,9.
- **Mode LP imparfait** : la sortie LP = BP + a·(LP − BP) n'est un vrai 24 dB que si le gain de l'OTA vaut exactement a = 1. Dans SPICE, il reste une fuite de passe-bande à ≈ −18 dB au-dessus de la coupure (creux puis remontée, voir le graphique). Le LP est donc moins sombre que prévu. Pistes : un trimmer pour régler a = 1 en position LP, ou une architecture où chaque sortie (LP, BP, HP) a son propre OTA dont le courant tombe à zéro aux extrémités : un zéro est exact, un gain de 1 ne l'est pas.

### Simulateurs
Le simulateur SEMI a été recalé sur ces résultats : rampe droite et sans filtrage, plage du ladder 20 Hz → 13 kHz, courbe d'EMPHASIS et gain de −3,5 dB mesurés. Il garde volontairement le LP « idéal » (24 dB), c'est-à-dire le son visé une fois le mode corrigé.
