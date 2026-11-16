# Octavio ADSR — enveloppe façon Moog 911, Eurorack 8 HP (rev 0.1)

## Façade (de haut en bas)
- **ADSR** entre les trous du haut
- **ATTACK**, **DECAY**, **SUSTAIN**, **RELEASE** : quatre gros boutons l'un par-dessus l'autre, nom au-dessus, gradués 0–10
- Grille 2 × 2 en bas : **ENV** (LED qui suit l'enveloppe) et **GATE** (entrée), puis **OUT** (0 à 10 V) et **−OUT** (0 à −10 V)

## Circuit (comme le 911 : un condensateur chargé à travers des résistances)
- Condensateur de temps C10 (10 µF 50 V X7R, ≈ 6 µF réels sous 10 V), lu par le tampon U1A.
- Trois chemins, chacun = interrupteur CD4066 (U4) + 220 Ω + pot **1 MΩ logarithmique** :
  - **ATTACK** : vers +12 V jusqu'à 10 V (le comparateur de crête U1C arrête l'attaque) → courbe RC qui ralentit en haut, comme le Moog.
  - **DECAY** : vers le niveau **SUSTAIN** (0–10 V, pot 10k tamponné par U2B) tant que le gate est haut.
  - **RELEASE** : vers 0 V quand le gate retombe.
- Logique : comparateur de gate U2C (seuil ≈ 3 V, hystérésis) et son inverse U1B, ramenés en 0–12 V par des BAT54S ; bascule CD4013 (U3) = phase d'attaque, mise à 1 au front montant du gate (léger retard 10 µs), remise à 0 à la crête ou quand le gate retombe.
- Le decay ne s'active que si « pas d'attaque » ET « gate » (deux interrupteurs en série).
- Temps : attaque ≈ 2 ms à ≈ 10 s, decay / release ≈ 3 ms à ≈ 14 s (jusqu'à 90 %). Un nouveau gate pendant le release repart du niveau actuel (pas de saut).
- U2A : inverseur pour −OUT. Sorties 1 kΩ, LED 3 mm (R21 2,2 kΩ).

## À vérifier avant de commander
- **Pots 1 MΩ log (A)** en 9 mm : disponibilité LCSC (sinon B 1 MΩ, les temps seront moins bien répartis).
- **C10** : X7R 10 µF 50 V 1206 ; la valeur réelle baisse avec la tension (c'est prévu dans les temps ci-dessus). Un 10 µF film ou un tantale donnerait des temps ≈ 1,6 × plus longs.
- Empreintes de façade (`octavio_mu`) : jacks, pots 9 mm, LED.
- Carte placée, **pas encore routée**.
