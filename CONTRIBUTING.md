# Contribuer à xtoolav

Merci de t'intéresser au développement de **xtoolav** !  
Nous acceptons les contributions sous forme de correctifs, nouvelles fonctionnalités, traductions ou documentation.

## 🛠 Comment contribuer

1. **Fork** ce dépôt
2. Crée une branche : `git checkout -b feature/nouvel-outil`
3. Commit tes changements : `git commit -m "Ajout: calculateur de fréquence UHF"`
4. Push : `git push origin feature/nouvel-outil`
5. Ouvre une **Pull Request**

## 📝 Règles

- Garde le code propre et commenté
- Respecte le style existant (Python, HTML, CSS)
- Teste localement avant de soumettre
- Mets à jour les traductions (`pybabel extract && pybabel update`)
- Ajoute des tests si possible

## 🌍 Traductions

Les fichiers de traduction se trouvent dans `translations/`.  
Utilise `pybabel` pour mettre à jour :

```bash
pybabel extract -F babel.cfg -o messages.pot .
pybabel update -d translations -l de
pybabel update -d translations -l fr
# ... puis édite les .po
pybabel compile -d translations