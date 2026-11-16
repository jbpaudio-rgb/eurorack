# Octavio STAGES — séquenceur 8 étapes façon Verbos Multistage, Eurorack 30 HP (rev 0.1)

Séquenceur / générateur multi-étapes piloté par un **Raspberry Pi Pico (RP2040)** : chaque étape a sa tension A, sa tension B, son temps et son glissé, comme le Voltage Multistage de Verbos, en 8 étapes.

## Façade
- **Gauche** : TIME (gros bouton), TIME CV (atténuateur réversible), ANALOG, boutons START et MODE (LED LOOP / ONCE / ENV) ; jacks CLOCK, START, STROBE, TIME CV, ANALOG, END, CV A, CV B, GATE.
- **8 colonnes** : A, B, TIME, bouton SLIDE + LED ambre, LED d'étape, jack SEL (saut à l'étape), jack GATE.

## Électronique
- **Raspberry Pi Pico** au dos sur 2 barrettes femelles 1×20 de 8,5 mm (soudées à la main ; elle passe au-dessus des composants). USB accessible pour mettre à jour le programme.
- 5 V : AMS1117-5.0 depuis le +12 V → VSYS par une Schottky (USB et rack peuvent être branchés en même temps).
- **27 potentiomètres** lus par deux **74HC4067** (GP26, GP27) ; ANALOG CV sur GP28 ; entrées CV ramenées en 0,15–3,15 V par TL074 + BAT54S.
- **Entrées gate** (CLOCK, START, STROBE, SEL 1-8) : transistor BC847 → logique 3,3 V active à l'état bas ; SEL et boutons SLIDE lus par deux **74HC165**.
- **Sorties** : quatre **74HC595** (LED d'étape, LED slide, gates 1-8, GATE, END, LED de mode) ; gates 0/3,3 V ×3 par TL074 → 0/10 V. **MCP4822** (2 × 12 bits) ×4,83 → CV A / CV B 0–9,9 V.
- Programme Arduino : voir `firmware/LISEZMOI.md`.

## À vérifier avant de commander
- **Raspberry Pi Pico** et barrettes femelles : à commander à part et souder à la main (JLCPCB ne monte pas la Pico).
- **Boutons 6 × 6 mm à tige longue** traversant la façade (hauteur à choisir selon l'écart carte-façade).
- **74HC4067** (SOIC-24 large), **MCP4822**, **AMS1117-5.0** : disponibilité LCSC.
- Empreintes de façade (`octavio_mu`) : jacks, pots 9 mm, LED 3 mm, boutons.
- Carte placée, **pas encore routée** (beaucoup de composants : prévoir 4 couches ou une carte de commandes séparée si le routage 2 couches coince).
