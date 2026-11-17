# Octavio S&H / LAG — échantillonneur-bloqueur + lag, Eurorack 8 HP (rev 0.1)

> **17 nov. 2026 – SPICE** : R17 déplacée (100k entre la grille du JFET et l'entrée tamponnée, au lieu de 1M vers le condensateur, qui le vidait). Le S&H tient maintenant ses valeurs. Voir `outils/spice/LISEZMOI.md`.

Tout analogique. Sans aucun câble, il sort déjà des tensions aléatoires : le S&H échantillonne son propre bruit au rythme de sa propre horloge.

## Façade
- **SAMPLE & HOLD**
  - **RATE** : vitesse de l'horloge interne (environ 0,5 à 100 Hz), LED **CLOCK** ambre.
  - Inverseur **S&H / T&H** : en haut, le S&H prend une valeur à chaque front montant de TRIG ; en bas, le T&H suit l'entrée tant que TRIG est haut, puis garde la dernière valeur.
- **LAG** : **RISE** (temps de montée) et **FALL** (temps de descente), réglables séparément, d'environ 1 ms à quelques secondes. La LED rouge suit la sortie LAG.
- **Jacks en bas** (2 colonnes de 4, montés de côté comme sur l'ATT / INV) :

| Gauche | Droite |
|---|---|
| **S&H IN** (vide = bruit blanc) | **TRIG** (vide = horloge interne) |
| **NOISE** (bruit blanc, 10 V c-à-c) | **CLOCK** (0 / +11 V) |
| **S&H OUT** | **GATE** (+11 V quand le S&H est positif : porte aléatoire à 50 %) |
| **LAG IN** (vide = S&H OUT) | **LAG OUT** |

## Circuit
- Bruit : jonction base-émetteur d'un BC847 en avalanche, amplifiée (trimmer RV4 = niveau).
- Horloge : intégrateur + bascule de Schmitt (même circuit que le PULSE du NOISE TOOLS).
- S&H : JFET MMBFJ112, condensateur de maintien 100 nF C0G, tampon TL074 (dérive très faible).
- LAG : un comparateur charge le condensateur (2,2 µF) à travers une diode et RISE ou FALL. Il s'arrête exactement sur la tension d'entrée, sans l'erreur de 0,6 V d'un lag à diodes simple.
- 3 × TL074, 71 composants.

## À vérifier avant de commander
- Régler RV4 pour environ 10 V crête à crête sur NOISE (le bruit varie d'un transistor à l'autre).
- Carte placée, **pas encore routée**.
