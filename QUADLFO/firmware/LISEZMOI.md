# Programme du module LFOs (Raspberry Pi Pico)

## Installer (une fois)
1. Arduino IDE 2 → Préférences → « URL de gestionnaire de cartes supplémentaires » :
   `https://github.com/earlephilhower/arduino-pico/releases/download/global/package_rp2040_index.json`
2. Gestionnaire de cartes → installer **Raspberry Pi Pico/RP2040** (Earle Philhower).
3. Outils → Carte → **Raspberry Pi Pico**.

## Envoyer le programme
1. Ouvrir `octavio_quadlfo/octavio_quadlfo.ino`.
2. Brancher la Pico en USB (la première fois : tenir **BOOTSEL** en branchant).
3. Téléverser. Le module peut rester dans le rack pendant l'envoi (diode Schottky entre le 5 V du rack et VSYS).

## Utilisation
- **FREQ**, inverseur sur **FREE** : de 0,02 Hz (50 s par cycle) à 25 Hz.
- **FREQ**, inverseur sur **CLK** : le bouton choisit un rapport du CLOCK, en 11 crans : /16, /8, /4, /3, /2, ×1, ×2, ×3, ×4, ×8, ×16. Le LFO reste calé sur l'horloge (même phase à chaque fois). Sans horloge branchée, le canal reste en FREE.
- **WAVE** : passe en douceur de **SINE** (à gauche) à **SAW** (en haut, rampe montante) puis à **SQUARE** (à droite) ; entre deux, mélange des deux formes voisines.
- **RESET** : un front remet toutes les phases au début et recommence le compte des horloges (les divisions repartent ensemble).
- **LED** de chaque canal : suit l'onde. **LED CLOCK** : clignote à chaque impulsion.
- Sorties ±4,9 V.

## Réglages en haut du fichier
- `CLOCKED_WHEN_LOW` : si l'inverseur est à l'envers (CLK en bas), mettre `false`.
- `OUT_OFFSET` / `OUT_GAIN` : le zéro et l'amplitude dépendent un peu du 3,3 V et du +12 V. Mettre une sortie en SQUARE très lente, mesurer les deux paliers et corriger si besoin.
