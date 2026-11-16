# ocTavio Eurorack

Modules Eurorack inspirés du Moog modulaire (façades alu noir, lettrage blanc, bandes argent, logo ocTavio).

| Dossier | Module | État |
|---|---|---|
| VCA | VCA différentiel façon Moog 902, 6 HP (rev 0.7) : CV LEVEL, RESPONSE LIN↔EXP, FIXED CONTROL VOLTAGE, 2 entrées / 2 sorties, 3 entrées CV | schéma + façade prêts ; carte placée, à router |
| AD | Enveloppe Attack/Decay contrôlée en tension, 6 HP (rev 0.1) : ATTACK, DECAY, CV attack et CV decay avec atténuateurs, TRIG, OUT, LED, mode ONE/CYCLE | schéma + façade prêts ; carte placée, à router |
| VCF | Filtre ladder façon Moog 4 pôles, 10 HP (rev 0.3) : bouton LP→BP→HP, FREQUENCY, EMPHASIS, CONTOUR + FREQ CV + EMPH CV avec atténuateurs, IN 1, IN 2, OUT | schéma + façade prêts ; carte placée, à router |
| VCO | Oscillateur façon Moog 921, 12 HP (rev 0.4) : RANGE LO–32’–16’–8’–4’–2’, FREQUENCY ±6 demi-tons, WIDTH, 1V/OCT, SYNC, FM et PWM avec atténuateurs, sorties SINE / TRIANGLE / SAW / PULSE + sortie BLEND (fondu continu des 4 formes) | schéma + façade prêts ; carte placée, à router |
| MIX | Mixeur 4 entrées façon Moog CP3, 8 HP (rev 0.3) : 4 boutons LEVEL, MASTER GAIN (saturation douce), entrées IN 1–4, sorties OUT et −OUT, couplage DC (audio + CV) | schéma + façade prêts ; carte placée, à router |
| ADSR | Enveloppe façon Moog 911, 8 HP (rev 0.1) : ATTACK, DECAY, SUSTAIN, RELEASE (courbes RC), GATE, OUT, −OUT, LED | schéma + façade prêts ; carte placée, à router |
| COMPLEX | Générateur d'onde complexe façon Buchla 259, 30 HP (rev 0.3) : osc. de modulation (FREQ, FINE, AUDIO/LFO, tri/carré/saw, CV, FM), MOD INDEX → AMPL / PITCH / TIMBRE, PHASE LOCK, COMPLEX OSCILLATOR (SINE, SQUARE), HARMONICS (TIMBRE, SYMMETRY, ORDER) → FINAL | schéma + façade prêts ; carte placée, à router |
| STAGES | Séquenceur 8 étapes façon Verbos Multistage, 30 HP (rev 0.1), Raspberry Pi Pico : A, B, TIME, SLIDE par étape, LOOP / ONCE / ENV, CLOCK, START, STROBE, ANALOG, SEL et GATE par étape, CV A, CV B, GATE, END ; programme Arduino | schéma + façade + programme prêts ; carte placée, à router |
| QUADLFO | LFOs : quatre LFO, 12 HP (rev 0.1), Raspberry Pi Pico, version la moins chère (sortie PWM filtrée, sans DAC) : FREQ et WAVE (fondu SINE → SAW → SQUARE) par canal, CLK / FREE, CLOCK (/16 à ×16), RESET, LED par canal | schéma + façade + programme Arduino prêts ; carte placée, à router |
| NOISETOOLS | NOISE TOOLS façon Intellijel, 10 HP (rev 0.1), analogique : PULSE (RATE, CLK / RND), bruit WHITE et PINK, S&H / T&H (entrée = bruit blanc, TRIG = PULSE par défaut), SLEW (entrée = S&H par défaut), 3 LED | schéma + façade prêts ; carte placée, à router |
| ATTINV | ATT / INV : 4 atténuateurs / inverseurs, 8 HP (rev 0.1) : bouton, LED bicolore et inverseur INV (−1 à +1) / ATT (0 à 1) par canal, 8 jacks en bas, entrées vides = +5 V | schéma + façade prêts ; carte placée, à router |
| MULT | Double multiple passif, 4 HP (rev 0.1) : 2 groupes de 4 jacks l'un sous l'autre | façade + carte prêtes (8 jacks, sans alimentation) |

Standards communs : alimentation Eurorack 10 broches (−12 V = bande rouge), jacks Thonkiconn, pots 9 mm, façades PCB aluminium 1,6 mm (vernis noir, sérigraphie blanche, HASL sans plomb), montage JLCPCB.

## Style des façades (commun à tous les modules)
- Titre du module entre les trous du haut : 2,6 mm, gras
- Titres de section (ATTACK, DECAY, CV LEVEL, RESPONSE, FIXED CONTROL VOLTAGE…) : 1,06 mm, gras
- Étiquettes de jacks, d'inverseurs, LIN./EXP. : 0,94 mm, gras
- Chiffres des graduations : 1,0 mm
- Logo ocTavio 16 mm de large en bas, bandes argent sur les côtés, lignes de cadre grises façon Moog
