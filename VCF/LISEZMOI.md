# Octavio VCF — filtre ladder façon Moog, LP / BP / HP, Eurorack 8 HP (rev 0.2)

## Façade (de haut en bas)
- **VCF** entre les trous du haut
- Bouton **LP → BP → HP** (en haut) : passe en continu du LP 24 dB au BP puis au HP
- **FREQUENCY** (gros bouton 0–10) : coupure ≈ 20 Hz → ≈ 20 kHz
- **EMPHASIS** (gros bouton 0–10) : résonance, auto-oscillation vers le haut de la course
- Trois colonnes **CONTOUR**, **FREQ CV**, **EMPH CV** : petit atténuateur au-dessus de chaque entrée. CONTOUR = entrée d'enveloppe façon « Amount of Contour » du Minimoog (≈ 0,6 oct/V à fond : une enveloppe de 10 V balaie ≈ 6 octaves)
- **IN 1**, **IN 2** (mélangées à l'entrée du ladder) et **OUT**

## Circuit
- **Ladder à transistors 4 pôles** comme le 904A / Minimoog : Q1 paire d'entrée, Q2–Q4 étages, Q5 charge du haut (paires BC847DS), C11–C14 100 nF C0G, chaîne de polarisation R1–R6 découplée par C15–C19.
- **Coupure** : convertisseur exponentiel (Q6 + U3C), somme FREQUENCY + FREQ CV + FM (U3A/U3B). Atténuateur FREQ CV à fond ≈ 1 V/oct (sans compensation thermique).
- **Modes** : U1 lit la tension de chaque étage (amplis différentiels ×10 à haute impédance, 2,2 MΩ) : y0 (entrée), y1, y2, y4.
  - LP 24 dB = y4 (le son Moog), BP 12 dB = 2·y1 − 2·y2, HP 12 dB = y0 − 2·y1 + y2
  - U2 calcule BP, LP − BP et HP − BP ; la sortie vaut BP + a·(LP − BP) + c·(HP − BP).
  - a et c sont deux gains d'OTA (U5, LM13700) commandés par le bouton de mode via U6 : a descend de 1 à 0 sur la première moitié de la course, c monte de 0 à 1 sur la seconde → LP → BP → HP sans saut (voir `simulation-mode-knob.png`).
  - La résonance agit dans tous les modes.
- **EMPHASIS** : OTA LM13700 dans la boucle de contre-réaction (de y4 vers la base droite de Q1), courant IABC = bouton + EMPH CV (U3D). k max ≈ 5 → auto-oscillation.
- Comme sur le Moog, monter l'emphasis fait baisser le grave en LP (≈ −13 dB).
- Sortie couplée en alternatif (C20 2,2 µF), 1 kΩ. Phase inversée par rapport à l'entrée (inaudible).

Simulation transistor (modèle Ebers-Moll + petits signaux) : gain unité dans les trois modes, pics de résonance à la coupure (≈ +7 dB à 3,5, ≈ +13 dB à 4,4 en LP), voir `simulation-modes.png`. Le plancher du HP vers 10 Hz est d'environ −45 dB (dépend de la précision des résistances du mélangeur, 1 %).

## À vérifier avant de commander
- **Placement** : regrouper Q1–Q5 et C11–C14 serrés et symétriques au routage (le placement actuel est automatique).
- Empreintes de façade (`octavio_mu`) : jacks et pots 9 mm (3 atténuateurs montés tournés de 180°).
- LM13700MX (×2 : U4 emphasis, U5 mode) : numéro LCSC à choisir dans l'outil BOM de JLC. Résistances de 22 MΩ et 2,2 MΩ en 0805 : vérifier la disponibilité (sinon 20 MΩ / 2 MΩ).
- Carte placée, **pas encore routée**.
- Premier prototype : prévoir d'ajuster R57 (plage d'emphasis) et R50 (plage de fréquence) à l'oreille.
