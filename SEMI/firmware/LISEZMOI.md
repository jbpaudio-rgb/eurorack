# SEMI – programme du Pico (KEYBOARD · MIDI)

- `semi_midi/` : le croquis Arduino. Cœur « Raspberry Pi Pico/RP2040 » d'Earle Philhower ; Outils > USB Stack > **Adafruit TinyUSB** (pour l'USB-MIDI). Compilé avec la version 6.4.0 : 90 ko.
- `semi_midi/midicv_core.h` : toute la logique (lecture du MIDI, priorité à la dernière note, legato, pitch bend, LEARN, CV → MIDI), sans dépendance au matériel.
- `test/test_core.cpp` : 24 vérifications sur l'ordinateur : `g++ -std=c++17 test/test_core.cpp -o t && ./t`.

Calibration de la sortie CV (une fois) : allumer en tenant LEARN. La sortie CV donne 0 V : jouer C4 / D4 pour descendre / monter d'un pas jusqu'à lire 0,000 V au voltmètre. E4 passe à +5 V : régler de la même façon avec C5 / D5. LEARN enregistre.
