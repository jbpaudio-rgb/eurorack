# Fabriquer le VCO ocTavio (12 HP) — guide pas à pas

## Ce qu'il y a dans ce dossier
| Dossier / fichier | Pour quoi |
|---|---|
| `1-carte/octavio-vco-gerber.zip` | Gerbers + perçages de la carte (4 couches, routée, plans de masse) |
| `1-carte/octavio-vco-BOM-JLCPCB.csv` | Liste des 140 CMS du dos, pour l'assemblage JLC |
| `1-carte/octavio-vco-CPL-JLCPCB.csv` | Position de chaque CMS (même origine que les Gerbers) |
| `1-carte/octavio-vco.kicad_pcb` | La carte routée, à ouvrir dans KiCad 8 si tu veux la vérifier ou la retoucher (appuie sur **B** pour remplir les plans de masse avant de ressortir des Gerbers) |
| `2-facade/octavio-vco-facade-gerber.zip` | Gerbers + perçages de la façade aluminium |
| `apercu-*.png` | Les fichiers relus et redessinés : ce que l'usine va voir |
| `octavio-vco-ACHATS.csv` | Tout ce qu'il faut acheter en plus (jacks, pots, boutons, câble…) |

## La carte en bref
- 4 couches : dessus, deux couches intérieures (pistes + **plans de masse**), dessous. Les 4 couches ont été nécessaires : en 2 couches, le routeur laissait une trentaine de liaisons impossibles.
- Routée avec Freerouting, puis les 3 dernières liaisons terminées par un petit routeur maison. Vérification indépendante : toutes les liaisons sont faites, écartement ≥ 0,12 mm partout (JLC accepte 0,09 mm en 4 couches).
- 140 CMS au dos (0603), le reste traversant côté façade.

## 1. Vérifier avant de commander (10 minutes)
1. **Commutateur RANGE** : l'empreinte de la carte est générique (12 contacts sur un cercle de 14 mm + commun). Achète d'abord le commutateur (ou télécharge sa fiche), et compare la position des broches. Si elle ne correspond pas, dis-le moi avec la référence exacte : je corrige l'empreinte et je reroute.
2. **Potentiomètres** : Alpha 9 mm vertical, 3 broches au pas de 5 mm devant + 2 pattes de fixation. Prends l'axe **D** de 6 mm pour les boutons Davies D.
3. Ouvre `apercu-carte.png` et `apercu-facade.png` : la façade doit être identique à celle du simulateur.

## 2. Commander la carte chez JLCPCB
1. jlcpcb.com → **Order now** → glisser `octavio-vco-gerber.zip`.
2. Réglages : *Base material* FR-4, *Layers* **4**, *Thickness* 1,6 mm, quantité 5, couleur au choix, *Surface finish* HASL sans plomb. Pour l'ordre des couches, laisse JLC proposer l'empilage standard (F_Cu, In1_Cu, In2_Cu, B_Cu dans cet ordre). Laisse le reste par défaut.
3. Si tu veux que JLC soude les CMS (conseillé : 140 pièces en 0603) : active **PCB Assembly**, choisis **Bottom Side**, puis téléverse `octavio-vco-BOM-JLCPCB.csv` et `octavio-vco-CPL-JLCPCB.csv`.
   - JLC te propose une pièce pour chaque ligne : prends de préférence les pièces « Basic » ; garde bien les résistances **0,1 %** là où la liste le dit (précision du 1 V/oct).
   - À l'écran de placement, vérifie que les CI (points du pin 1) et les diodes sont dans le bon sens ; tourne-les dans l'outil de JLC si besoin.
4. Les pièces traversantes (jacks, pots, commutateur, barrette d'alimentation) ne sont pas dans cette liste : tu les soudes toi-même (étape 5).

## 3. Commander la façade
1. Nouveau devis → glisser `octavio-vco-facade-gerber.zip`.
2. *Base material* **Aluminum**, *Layers* 1, *Thickness* 1,6 mm, *Solder mask* **noir**, *Silkscreen* **blanc**, *Surface finish* **HASL sans plomb** (les deux bandes sur les côtés restent métal argenté).
3. Moins cher : FR-4 noir avec sérigraphie blanche marche aussi (les bandes seront alors étamées).

## 4. Acheter le reste
Voir `octavio-vco-ACHATS.csv` : 9 jacks Thonkiconn, 5 pots 10k B axe D, 1 commutateur rotatif, 6 boutons Davies 1900H (axe D), 1 barrette blindée 2×5, 1 câble 10→16 broches, 2 vis M3.

## 5. Monter
1. **Barrette d'alimentation** (au dos, détrompeur comme dessiné, −12 V côté marqué) : souder en premier.
2. Poser **jacks, pots et commutateur** côté face, **sans souder**.
3. Poser la **façade** par-dessus, visser les écrous des jacks et des pots à la main : tout s'aligne tout seul.
4. Retourner et **souder** toutes les pattes. Serrer les écrous.
5. Mettre les **boutons** (pointeur sur le repère du bas à gauche quand le pot est tout à gauche).

## 6. Premier allumage et réglages
1. Brancher le câble : **bande rouge vers −12 V** (marqué sur la carte). Vérifier qu'il n'y a pas de court-circuit entre +12 V, −12 V et masse à l'ohmmètre **avant** d'allumer.
2. Laisser chauffer 10 minutes, puis les réglages du LISEZMOI du VCO :
   - **RV7 (V/OCT)** : 1 V puis 3 V → exactement 2 octaves d'écart ;
   - **RV8 (HF)** : octaves justes dans l'aigu ;
   - **RV9 (SINE)** : sinus symétrique.
