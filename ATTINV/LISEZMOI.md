# Octavio ATT / INV — quatre atténuateurs / inverseurs, Eurorack 8 HP (rev 0.1)

> **17 nov. 2026 – SPICE** : diviseur +5 V raidi (R1 1k4, R2 1k au lieu de 14k / 10k) : une entrée vide donne +4,7 V au lieu de +3,6 V. Voir `outils/spice/LISEZMOI.md`.

## Façade
- En haut, une rangée par canal (1 à 4) : bouton de niveau, LED bicolore (rouge = sortie positive, vert = négative), inverseur **INV / ATT**.
  - **INV** (levier à gauche) : atténuverteur, de −1 (à gauche) à 0 (au centre) à +1 (à droite).
  - **ATT** (levier à droite) : simple atténuateur, de 0 (à gauche) à +1 (à droite).
- En bas, les 8 jacks serrés à 11 mm : ils sont montés de côté (pattes vers le centre), ce qui permet de les rapprocher sans que la patte d'un jack touche le suivant. **IN 1–4** à gauche, **OUT 1–4** à droite. Avec des câbles à fiche fine (6 à 8 mm), ça passe bien ; des fiches très grosses (plus de 10 mm) seront serrées.
- **IN vide** = +5 V : le canal devient une source de tension réglable (−5 à +5 V en INV, 0 à +5 V en ATT).

## Circuit
- Par canal : IN → inverseur 100 kΩ (−IN) → second inverseur 10 kΩ (+IN, basse impédance). Le pot 10k B va de +IN à −IN (INV) ou à la masse (ATT) ; le curseur passe dans un suiveur, puis 1 kΩ vers OUT.
- +5 V de normalisation : diviseur 14k / 10k sur le +12 V.
- 3 × TL074, 4 inverseurs SPDT ON-ON, 61 composants.

## À vérifier avant de commander
- LED 3 mm bicolore **2 pattes** (rouge/vert tête-bêche).
- Carte placée, **pas encore routée**.
