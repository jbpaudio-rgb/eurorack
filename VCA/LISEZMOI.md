# Octavio 902 VCA — Eurorack 6 HP (rev 0.7)

VCA différentiel inspiré du Moog 902, adapté au ±12 V Eurorack.

## Contenu
- `octavio-902-vca.kicad_sch` : schéma complet (nets reliés par étiquettes, regroupés par bloc)
- `octavio-902-vca.kicad_pcb` : carte 27 × 106,5 mm, composants **placés, non routés** (le chevelu est là), plans GND haut et bas
- `panel/` : façade en PCB aluminium 1,6 mm (noir, sérigraphie blanche), tous les trous percés
- `octavio_mu.kicad_sym` / `octavio_mu.pretty` : symboles et empreintes de façade (jack, pot, inverseur)
- `octavio-902-vca-BOM-JLCPCB.csv` : BOM au format JLCPCB (Comment, Designator, Footprint, LCSC Part #)

## Façade
- Disposition relevée sur un 902 R.A. Moog d'origine (1 MU) et réduite à l'échelle 0,58 (6 HP = 30 × 128,5 mm) : CONTROL MODE en haut, bouton FIXED CONTROL VOLTAGE gradué 0–6, cadre SIGNAL INPUTS / OUTPUTS avec séparateur central, CONTROL INPUTS en triangle.
- Bandes argent sur les côtés (rappel des rebords pliés en aluminium) : cuivre à nu sans vernis → commander en **HASL sans plomb** pour un rendu argent (ENIG donnerait du doré).
- Trous de fixation Eurorack standard (7,5 mm du bord, 3 mm du haut/bas) : ils remplacent les vis rondes du Moog.

## Bouton RESPONSE (rev 0.4)
Les deux convertisseurs (linéaire U1B et exponentiel U1C/U1D) fonctionnent en permanence. U5A transforme le courant exponentiel en tension (0–1 V), le pot RV4 mélange la tension LIN et la tension EXP, et U5B + Q5 en font le courant de queue. Simulation : gain ×2 à 6 V quelle que soit la position ; à mi-course, −15 dB à 1 V (LIN : −9 dB, EXP : −60 dB).

## Façade rev 0.7
- Titre « VCA » entre les trous du haut.
- **CV LEVEL** (pot 10k, en haut) : atténuateur de la somme des 3 CONTROL INPUTS. U2D additionne CV 1 + CV 2 + CV 3 (sommateur passif 3 × 100k puis gain ×3) ; le pot dose cette somme avant qu'elle s'ajoute au FIXED CONTROL VOLTAGE (qui n'est pas atténué).
- Dessous : le bouton RESPONSE (LIN ↔ EXP), puis FIXED CONTROL VOLTAGE, les jacks signal et les 3 entrées CV.
- Le BOOST est retiré (R20/R21 reviennent à 200 Ω). L'écrêteur doux en sortie (zeners 8,2 V) est conservé.

## Fonctionnement
- 2 entrées signal différentielles (IN 2 est soustraite de IN 1, comme sur le Moog), normalisées à la masse
- 2 sorties : OUT + et OUT − (inversée)
- 3 entrées CV + bouton FIXED CONTROL VOLTAGE (0–6 V), sommés
- Bouton RESPONSE : passe en continu de LIN à EXP (remplace l'inverseur)
- Cœur : paire différentielle appairée (BCM847DS), courant de queue piloté par une source linéaire (U1B + Q5) ou un convertisseur exponentiel (U1C/U1D + BCM847DS)
- Sortie : ampli de différence TL072 (remplace l'étage PNP du 902 d'origine)

Simulation (modèle Ebers-Moll) : gain ×2 (+6 dB) à 6 V de contrôle dans les deux modes ; EXP ≈ 13 dB/V, −80 dB à 0 V ; distorsion ≈ 1,3 % (H3) à 10 Vpp en entrée, 0,05 % à 2 Vpp. Au-delà de 6 V, ça sature doucement.

## Réglage (une fois)
1. Rien branché, bouton à 0 : RV3 (OFFSET) → 0 V en sortie OUT +.
2. LFO lent dans CV 1, rien en entrée : RV2 (CV REJECT) → pas de « pompage » en sortie.

## À vérifier avant de commander
- Empreintes de façade (`octavio_mu`) : positions de broches du Thonkiconn, du pot Alpha 9 mm et de l'inverseur Dailywell dessinées de mémoire → comparer aux fiches techniques.
- Les empreintes standard KiCad (CMS, IDC, 3362P) ont des noms officiels : *Outils → Mettre à jour les empreintes depuis la bibliothèque* pour récupérer les vraies.
- Boîtier : connecteur 10 broches (compatible câbles 16 broches), −12 V = bande rouge. Profondeur estimée ≈ 25 mm.
- Brochage BC847DS : 1 E1, 2 B1, 3 C2, 4 E2, 5 B2, 6 C1 (à confirmer sur la fiche Nexperia).

## Montage complet chez JLCPCB (rev 0.4)
Pièces choisies dans le catalogue JLC (soudure « wave soldering » = montées par JLC) :
- Jacks : QingPu WQP-PJ301M-12 — C9900080080 (même empreinte que le PJ398SM)
- Pot : POT-R09V-100K — C9900018037 (vérifier la tige et l'empreinte)
- Bouton RESPONSE : pot 9 mm B10k (même empreinte que FIXED CONTROL VOLTAGE)
- TL074CDR — C12594 ; BC847DS,115 — C549489 (paire double non appairée en usine → plage du trimmer CV REJECT élargie, R26 = 470k)
- Pour les autres lignes sans numéro LCSC, l'outil BOM de JLC propose une pièce : choisir une « Basic » quand c'est possible.

Commande : PCB 2 couches FR4 + PCBA Economic, assemblage côté **Bottom** pour les CMS ; les pièces traversantes sont soudées à la main par JLC.
Le fichier CPL (placement) se génère dans KiCad après le routage : Fichier → Fabrication → Fichier de position des composants (CSV, mm, les deux faces).
