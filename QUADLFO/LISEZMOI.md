# Octavio QUAD LFO — quatre LFO libres ou synchronisés, Eurorack 12 HP (rev 0.1)

Quatre LFO sur une **Raspberry Pi Pico (RP2040)**, en version la moins chère possible : pas de convertisseur DAC, les ondes sortent directement de la Pico en PWM, puis passent dans un filtre RC à deux pôles et un TL074.

## Façade
Par canal (colonnes 1 à 4) :
- **FREQ** : vitesse en mode FREE, rapport du CLOCK en mode CLK
- **WAVE** : fondu continu **SINE** (gauche) → **SAW** (haut) → **SQUARE** (droite)
- **LED** rouge qui suit l'onde
- Inverseur **CLK / FREE**
- Sortie **OUT** ±5 V

En bas : entrée **CLOCK**, LED d'horloge, entrée **RESET**.

## Circuit
- **Pico** au dos sur barrettes femelles 8,5 mm, alimentée en 5 V par un AMS1117-5.0 depuis le +12 V (diode Schottky vers VSYS : on peut brancher l'USB module en place).
- **8 potentiomètres** (4 FREQ, 4 WAVE) lus par un seul **74HC4051** sur l'entrée analogique GP26.
- **Inverseurs** directement sur la Pico (pull-up internes). Entrées **CLOCK** et **RESET** par transistor BC847 (seuil ≈ 1,3 V, supporte ±12 V).
- **Sorties** : PWM 30,5 kHz 12 bits → 10k/100n → 10k/100n (deux pôles à 159 Hz, ondulation ≈ −45 dB) → TL074 ×3,02 − 4,93 V → 1 kΩ → jack. Les fronts du carré sont arrondis d'environ 1 ms, sans effet pour un LFO.
- Programme Arduino dans `firmware/` (voir son LISEZMOI).

## Coût
Pièces pour un module, hors circuit imprimé et façade : environ **15 à 20 $** (la Pico ≈ 4 $, les 8 potentiomètres et 6 jacks font l'essentiel). Pas de DAC (économie d'environ 6 $ par rapport à deux MCP4822), multiplexeur 8 voies plutôt que 16, inverseurs Dailywell bon marché.

## À vérifier avant de commander
- Inverseurs SPDT **ON-ON** (Dailywell 2MS1 ou C&K T101) : CLK quand le levier est en haut ; sinon changer `CLOCKED_WHEN_LOW` dans le programme.
- Carte 12 HP placée (88 composants, CMS au dos), **pas encore routée**. 2 couches devraient suffire.
