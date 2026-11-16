# Octavio MIX — mixeur 4 entrées façon Moog CP3, Eurorack 6 HP (rev 0.1)

## Façade (de haut en bas)
- **MIX** entre les trous du haut
- **LEVEL** : 4 boutons de niveau en colonne (1 à 4), comme sur le CP3
- Jacks en bas : **IN 1**, **IN 2**, **IN 3**, **IN 4**, puis **OUT** et **−OUT** (sortie inversée)

## Circuit
- Chaque entrée passe par son potentiomètre (100k B) puis une résistance de 100k vers un sommateur inverseur (U1A, TL072). Bouton au maximum = gain de 1 pour cette entrée.
- **−OUT** = sortie directe du sommateur (somme inversée), **OUT** = la même chose remise à l'endroit par U1B. Résistances de 1k en série sur les sorties.
- Couplage **continu** (DC) : il mélange aussi bien l'audio que les tensions de contrôle (enveloppes, LFO, décalages). −OUT sert à inverser une modulation.
- Entrées non branchées = à la masse (contact du jack), donc pas de bruit.

## À vérifier avant de commander
- Empreintes de façade (`octavio_mu`) : jacks et pots 9 mm.
- Carte placée, **pas encore routée**.
