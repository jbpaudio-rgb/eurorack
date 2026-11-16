# Octavio AD — enveloppe Attack/Decay contrôlée en tension, Eurorack 6 HP (rev 0.1)

Même style que le VCA : façade alu noire, lettrage blanc, bandes argent, logo ocTavio.

## Façade (de haut en bas)
- **AD** entre les trous du haut
- **ATTACK** (gros bouton, gradué 0–10)
- **DECAY** (gros bouton, gradué 0–10)
- Inverseur **ONE / CYCLE** juste sous DECAY : CYCLE relance l'attaque à la fin du decay → l'AD devient un LFO
- **ATTACK CV / DECAY CV** : petit atténuateur juste au-dessus de chaque entrée CV
- **TRIG** (entrée), **LED** (suit l'enveloppe), **OUT**

## Circuit
- Cœur : OTA **LM13700** monté en « slew » : il charge le condensateur de temps C13 (100 nF C0G) vers une cible de 10 V pendant l'attaque, puis vers 0 V pendant le decay, à un courant égal à IABC.
- **IABC** vient de deux convertisseurs exponentiels à paires PNP (Q1 attack, Q2 decay, BCM857DS). Un seul est actif à la fois (diodes D4/D11 commandées par le latch et son inverse).
- Temps : **≈ 0,8 ms à ≈ 8 s** sur la course de chaque bouton (simulation). La CV atténuée s'ajoute au bouton : +5 V au maximum ≈ ×100 sur le temps (≈ 2 décades), −5 V ≈ ÷100 (limité au plus court).
- U2D : comparateur de trigger (seuil ≈ 1 V, hystérésis). U2A : latch (attaque / decay). U2B : fin d'attaque à ≈ 9,3 V. U2C : tampon ×1,25 → OUT 0 à ≈ 9,6 V.
- U4A : détecteur de fin de decay (< 0,2 V) → via l'inverseur CYCLE, relance le trigger.
- Sortie 1 kΩ, LED 3 mm (R44 2,2 kΩ).

## À vérifier avant de commander
- **Empreintes de façade** (`octavio_mu`) : Thonkiconn, pot 9 mm (4 pots, dont les 2 atténuateurs montés tournés de 180°), inverseur C&K T101 (C668578) → prendre l'empreinte JLC/EasyEDA.
- **LED 3 mm** : elle doit dépasser la façade d'environ 1 mm → entretoise de LED ≈ 10 mm (même hauteur que les jacks).
- **BCM857DS** (paire PNP appairée) : disponibilité chez LCSC à confirmer (sinon BC857BS).
- **LM13700MX** (SOIC-16) : numéro LCSC à choisir dans l'outil BOM de JLC.
- Carte placée, **pas encore routée** (même marche à suivre que le VCA).
