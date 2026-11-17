# Octavio RING MOD — modulateur en anneau, Eurorack 8 HP (rev 0.1)

Multiplicateur 4 quadrants à MC1496 (la cellule de Gilbert classique des modulateurs en anneau), couplé en continu : il marche en audio comme en CV.

## Façade
- **LEVELS**
  - **X** (SIGNAL) : niveau de l'entrée X.
  - **Y** (CARRIER) : niveau de la porteuse. Bas, la multiplication est propre (cloches, sons métalliques doux). En montant, la porteuse fait commuter le MC1496 et le son devient plus dur, comme un modulateur à diodes.
- **MIX** : fondu de **DRY** (X seul) à **RING** (produit seul). LED bicolore sur la sortie (rouge = +, vert = −).
- **Jacks en bas** : **X IN**, **Y IN**, **RING** (produit seul), **OUT** (après le MIX).
- **Y IN vide = +5 V** : le module devient un ampli / VCA simple pour X, et Y LEVEL règle le gain. Branche une enveloppe dans Y et c'est un VCA.

## Circuit
- MC1496 : paire basse = X (1 kΩ entre 2 et 3 pour la linéarité), paire haute = Y, polarisée à +5,2 V, courant de 1 mA (10 kΩ sur la broche 5).
- Sorties sur 3,9 kΩ, ampli différentiel TL074 (gain 1,5), MIX passif suivi d'un tampon.
- Deux trimmers d'équilibrage :
  - **RV4 CARRIER NULL** : Y branché, X à zéro → tourner pour le minimum à la sortie RING.
  - **RV5 SIGNAL NULL** : X branché, Y à zéro (Y LEVEL au minimum) → tourner pour le minimum.
- 1 × MC1496, 1 × TL074, 47 composants.

## À vérifier avant de commander
- Carte placée, **pas encore routée**.
