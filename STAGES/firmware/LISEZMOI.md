# Programme du séquenceur STAGES (Raspberry Pi Pico)

## Installer (une fois)
1. Arduino IDE 2 → Préférences → « URL de gestionnaire de cartes supplémentaires » :
   `https://github.com/earlephilhower/arduino-pico/releases/download/global/package_rp2040_index.json`
2. Gestionnaire de cartes → installer **Raspberry Pi Pico/RP2040** (Earle Philhower).
3. Outils → Carte → **Raspberry Pi Pico**.

## Envoyer le programme
1. Ouvrir `octavio_stages/octavio_stages.ino`.
2. Brancher la Pico en USB (la première fois : tenir **BOOTSEL** en branchant).
3. Téléverser. Le module peut rester alimenté par le rack pendant l'envoi (diode Schottky entre le 5 V du rack et VSYS).

## Utilisation
- **TIME** : durée de base d'une étape, 10 ms à 10 s ; **TIME** de chaque étape : ×0,25 à ×4.
- **TIME CV** + atténuateur réversible : +1 V = deux fois plus vite (bouton à droite), inverse à gauche.
- **SLIDE** (bouton d'étape) : appui court = glissé on/off (LED ambre) ; appui long (> 0,6 s) = cette étape devient la **dernière** (sa LED clignote).
- **A / B** : 0 à 8 V sur CV A et CV B. Avec SLIDE, la tension glisse depuis l'étape précédente pendant toute la durée de l'étape.
- **GATE** : haut pendant la première moitié de chaque étape, ou toute l'étape si la suivante glisse (legato). **GATE 1-8** : haut pendant l'étape. **END** : impulsion de 5 ms à la fin de la séquence.
- **MODE** : **LOOP** (boucle ; START ou le bouton démarre / arrête), **ONCE** (un passage par START), **ENV** (enveloppe : START haut → part de l'étape 1, s'arrête sur l'étape choisie par **ANALOG** tant que START reste haut, puis va jusqu'au bout).
- **CLOCK** : si une horloge arrive, chaque impulsion fait avancer d'une étape (les glissés suivent la période de l'horloge) ; sans horloge pendant 3 s, retour aux temps internes.
- **SELECT 1-8** : un front saute directement à l'étape. **STROBE** : saute à l'étape donnée par **ANALOG** (bouton + CV 0–8 V).
- SLIDE, dernière étape et mode sont mémorisés.

## Calibration
`DAC_FULL_VOLTS` (en haut du fichier) : mettre A1 à fond, mesurer CV A, et ajuster pour lire exactement 8,00 V.
