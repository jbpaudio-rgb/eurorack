# Octavio MIX — mixeur 4 entrées façon Moog CP3, Eurorack 8 HP (rev 0.3)

## Façade (de haut en bas)
- **MIX** entre les trous du haut
- **LEVEL** : 4 boutons de niveau en carré (1 2 / 3 4), bien espacés
- **MASTER GAIN** : grand bouton gradué 0 à 10 ; gain général, saturation douce quand on le monte (CP3 poussé)
- Jacks en bas : entrées **IN 1**, **IN 2**, **IN 3**, **IN 4** (2 rangées), colonne de droite séparée : **OUT** et **−OUT** (sortie inversée)

## Circuit
- Chaque entrée passe par son potentiomètre (100k B) puis une résistance de 100k vers un sommateur inverseur (U1A, TL074). Bouton au maximum = gain de 1 pour cette entrée.
- **MASTER GAIN** (U1C) : gain réglable de 1 à 11 ; au-delà d'environ ±5,8 V, deux zeners tête-bêche (BZT52C5V1) à travers 4k7 adoucissent le signal (genou progressif), puis écrêtage aux rails (±10,5 V).
  - MASTER GAIN au minimum : propre jusqu'à ±5 V (mélange de CV possible).
  - MASTER GAIN monté : compression puis saturation, sortie plus chaude (8 à 10 V crête).
- **OUT** = sortie de l'étage MASTER GAIN ; **−OUT** = la même chose inversée par U1B. Résistances de 1k en série sur les sorties.
- Couplage **continu** (DC) : il mélange aussi bien l'audio que les tensions de contrôle (enveloppes, LFO, décalages). −OUT sert à inverser une modulation.
- Entrées non branchées = à la masse (contact du jack), donc pas de bruit.

## À vérifier avant de commander
- Empreintes de façade (`octavio_mu`) : jacks et pots 9 mm.
- Carte placée, **pas encore routée**.
