# Octavio VCF — filtre ladder façon Moog, LP / BP / HP, Eurorack 8 HP (rev 0.1)

## Façade (de haut en bas)
- **VCF** entre les trous du haut
- **FREQUENCY** (gros bouton 0–10) : coupure ≈ 20 Hz → ≈ 20 kHz
- **EMPHASIS** (gros bouton 0–10) : résonance, auto-oscillation vers le haut de la course
- Inverseur **BP / LP / HP** (centre = LP 24 dB, gauche = BP, droite = HP)
- Trois colonnes **FM**, **FREQ CV**, **EMPH CV** : petit atténuateur au-dessus de chaque entrée
- **IN** et **OUT**

## Circuit
- **Ladder à transistors 4 pôles** comme le 904A / Minimoog : Q1 paire d'entrée, Q2–Q4 étages, Q5 charge du haut (paires BC847DS), C11–C14 100 nF C0G, chaîne de polarisation R1–R6 découplée par C15–C19.
- **Coupure** : convertisseur exponentiel (Q6 + U3C), somme FREQUENCY + FREQ CV + FM (U3A/U3B). Atténuateur FREQ CV à fond ≈ 1 V/oct (sans compensation thermique).
- **Modes** : U1 lit la tension de chaque étage (amplis différentiels ×10 à haute impédance, 2,2 MΩ) : y0 (entrée), y1, y2, y4. U2 fait les mélanges :
  - LP 24 dB = y4 (le son Moog)
  - BP 12 dB = 2·y1 − 2·y2
  - HP 12 dB = y0 − 2·y1 + y2 (phase inversée)
  - La résonance agit dans les trois modes.
- **EMPHASIS** : OTA LM13700 dans la boucle de contre-réaction (de y4 vers la base droite de Q1), courant IABC = bouton + EMPH CV (U3D). k max ≈ 5 → auto-oscillation.
- Comme sur le Moog, monter l'emphasis fait baisser le grave en LP (≈ −13 dB).
- Sortie couplée en alternatif (C20 2,2 µF), 1 kΩ.

Simulation transistor (modèle Ebers-Moll + petits signaux) : gain unité dans les trois modes, pics de résonance à la coupure (≈ +7 dB à 3,5, ≈ +13 dB à 4,4 en LP), voir `simulation-modes.png`. Le plancher du HP vers 10 Hz est d'environ −45 dB (dépend de la précision des résistances du mélangeur, 1 %).

## À vérifier avant de commander
- **Placement** : regrouper Q1–Q5 et C11–C14 serrés et symétriques au routage (le placement actuel est automatique).
- Empreintes de façade (`octavio_mu`) : jacks, pots 9 mm (3 atténuateurs montés tournés de 180°), **inverseur ON-OFF-ON** (3 positions) à choisir chez JLC et prendre son empreinte.
- LM13700MX : numéro LCSC à choisir dans l'outil BOM de JLC. Résistances de 22 MΩ et 2,2 MΩ en 0805 : vérifier la disponibilité (sinon 20 MΩ / 2 MΩ).
- Carte placée, **pas encore routée**.
- Premier prototype : prévoir d'ajuster R57 (plage d'emphasis) et R50 (plage de fréquence) à l'oreille.
