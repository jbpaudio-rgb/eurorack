# Octavio SPRING REVERB — réverbe à ressort, Eurorack 10 HP (rev 0.1)

Le module attaque et récupère une vraie cuve à ressorts. La cuve ne tient pas sur le module : elle se fixe dans le boîtier (au fond ou sur le côté), loin du transformateur, et se branche par deux câbles blindés.

## Façade
- **SPRING TANK**
  - **DRIVE** : force avec laquelle on attaque les ressorts (de propre à saturé et « boing »). La LED **PEAK** s'allume quand l'attaque est forte.
  - **TONE** : de **DARK** (retour coupé vers 1,5 kHz) à **BRIGHT**.
- **MIX** : de **DRY** à **WET**, commandé en tension.
- **MIX CV** : atténuateur de l'entrée MIX CV (une tension positive ajoute de la réverbe).
- **Jacks en bas** :

| | | |
|---|---|---|
| **IN** | **SEND** (le signal qui attaque la cuve) | **RETURN** (vide = retour de la cuve) |
| **MIX CV** | **WET** (réverbe seule) | **OUT** |

SEND / RETURN forment une boucle d'effet sur la partie humide : par exemple SEND → filtre → RETURN pour filtrer seulement la réverbe.

## Cuve
- Conseillée : **Accutronics 4FB3C1B** (longue, 3 ressorts, entrée 1 475 Ω, sortie 2 250 Ω, entrée isolée et sortie à la masse). Une Belton équivalente marche aussi.
- Deux câbles blindés : fiche RCA d'un côté, JST PH 2 broches de l'autre (J10 = TANK IN, J11 = TANK OUT, broche 1 = signal, broche 2 = masse).

## Circuit
- Entrée : inverseur 100 kΩ, puis étage DRIVE (gain 0,2 à 4,8).
- Driver : NE5532 en suiveur, 47 Ω vers la bobine d'entrée de la cuve (jusqu'à environ 7 mA).
- Récupération : seconde moitié du NE5532 (bas bruit), gain ×101, puis TONE (passe-bas variable).
- MIX : une paire PNP appairée (BCM857DS) partage environ 200 µA entre les deux OTA d'un LM13700, un pour le signal sec, un pour la réverbe. Le fondu est doux et sans clic.
- 2 × TL074, NE5532, LM13700, 67 composants.

## À vérifier avant de commander
- Choisir la cuve avant de souder : avec une cuve à entrée basse impédance (8 Ω ou 150 Ω), il faudrait un étage de puissance.
- Carte placée, **pas encore routée**.
