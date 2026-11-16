# Octavio NOISE TOOLS — bruit, impulsions, S&H et slew, Eurorack 10 HP (rev 0.1)

D'après l'**Intellijel Noise Tools** (module 1U de 22 HP), redessiné en 3U dans le style ocTavio. Tout est analogique et le circuit est le nôtre.

## Façade
**PULSE** (à gauche)
- **RATE** : de 0,5 Hz à 106 Hz, avec une courbe logarithmique pour que la vitesse monte régulièrement sur toute la course
- **CLK / RND** : CLK = horloge régulière ; RND = à chaque coup d'horloge, l'impulsion passe ou non au hasard (une sur deux en moyenne)
- LED ambre et sortie **PULSE** (0 / +10,5 V)

**SLEW** (à droite)
- **RATE** : glissement linéaire, d'environ 1 ms à 1 s pour 10 V
- Entrée **SLEW IN**, branchée par défaut sur la sortie S&H ; sortie **SLEW OUT** ; LED

**S&H / T&H**
- Inverseur **S&H** (échantillonne sur le front montant de TRIG) ou **T&H** (suit l'entrée tant que TRIG est haut, puis garde la dernière valeur)
- **S&H IN** : branchée par défaut sur le bruit blanc ; **TRIG** : branchée par défaut sur PULSE ; sortie **S&H OUT** ; LED

**NOISE** : sorties **WHITE** et **PINK** (environ 10 V crête à crête)

Sans aucun câble, le module donne donc déjà une tension aléatoire en escalier (S&H OUT) et sa version lissée (SLEW OUT).

## Circuit
- **Bruit** : jonction base-émetteur d'un BC847 en avalanche, puis ampli ×1 à ×200 (trimmer RV3 : régler 10 V crête à crête sur WHITE).
- **PINK** : étage inverseur avec 4 branches RC dans la contre-réaction, pente de −3 dB par octave à ±0,3 dB de 20 Hz à 20 kHz.
- **PULSE** : intégrateur + bascule de Schmitt (triangle ±5,5 V, carré ±11 V). Le pot RATE est un 10k logarithmique monté en diviseur sur le carré : la vitesse suit directement la courbe log. **RND** : un CD4013 échantillonne le bruit blanc à chaque front montant, puis un ET à diodes ne laisse passer l'horloge que si le bit vaut 1.
- **S&H / T&H** : comparateur de TRIG (seuil 1,6 V), impulsion de 70 µs pour le S&H, interrupteur JFET MMBFJ112, condensateur de maintien 100 nF C0G, tampon TL074 à entrées JFET (très faible fuite).
- **SLEW** : comparateur + intégrateur (pente constante), pot 1M logarithmique.
- 3 × TL074, 1 × CD4013, 85 composants.

## À vérifier avant de commander
- Le niveau de bruit d'une jonction en avalanche change d'un transistor à l'autre : régler RV3 au montage.
- Pots **A10k** (RATE) et **A1M** (SLEW) en 9 mm vertical, inverseurs SPDT ON-ON.
- Carte 10 HP placée, **pas encore routée** (2 couches devraient suffire).
