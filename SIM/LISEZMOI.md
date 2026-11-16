# Simulateur ocTavio Eurorack

Page web avec tous les modules (VCO, MIX, VCF, VCA, AD) dans un rack, façades générées depuis les fichiers KiCad, câbles à brancher au doigt et son en temps réel.

- Ouvrir `index.html` (avec `dsp.js` dans le même dossier) depuis un petit serveur web, ou la version publiée.
- Panneau **SIM** (pas un vrai module) : séquence/clavier (CV, GATE), sortie haut-parleurs (AUDIO), oscilloscope (SCOPE).
- Les sons viennent de modèles de comportement réglés sur nos simulations transistor (`source/engine.js`). Ce n'est pas une simulation composant par composant.
- `source/build_data.py` puis `source/build.py` régénèrent la page quand une façade change ; `node source/test.js` rend 4 s du patch en WAV pour vérifier les niveaux.
