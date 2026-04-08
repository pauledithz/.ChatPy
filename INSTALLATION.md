# Prérequis
- Python 3.7+
- pip (gestionnaire de paquets Python)
- Navigateur web moderne (Chrome, Firefox, Safari, Edge)

# Installation

## 1. Installer Flask et Flask-CORS
```bash
pip install flask flask-cors
```

Ou si vous utilisez pip3:
```bash
pip3 install flask flask-cors
```

## 2. Vérifier l'installation
```bash
python -c "import flask; print(flask.__version__)"
```

# Lancer l'application

## Méthode 1: Via terminal
```bash
# Se placer dans le répertoire du projet
cd /chemin/vers/.mobisystems

# Lancer le serveur Flask
python app.py
```

Vous verrez:
```
 * Running on http://127.0.0.1:5000
```

## Méthode 2: Depuis VS Code

1. Ouvrir le terminal intégré (Ctrl + `)
2. Taper: `python app.py`
3. Le serveur démarre

## Accéder à l'interface

1. Ouvrir votre navigateur
2. Aller à: `http://localhost:5000`
3. Ou double-cliquer sur `index.html`

# Troubleshooting

## Port 5000 déjà utilisé
Si le port 5000 est occupé, modifier la dernière ligne d'`app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=8000)  # Changer 5000 en 8000
```
Et mettre à jour l'URL dans `script.js`:
```javascript
const API_URL = 'http://localhost:8000/api';
```

## Module Flask non trouvé
```bash
# Assurez-vous que Flask est installé
pip install flask flask-cors

# Vérifiez votre version de Python
python --version
```

## CORS erreur
Si vous avez une erreur CORS, assurez-vous que Flask-CORS est installé:
```bash
pip install flask-cors
```

# Notes importantes

- Le serveur doit TOUJOURS être en cours d'exécution pour que l'interface fonctionne
- Gardez le terminal ouvert pendant que vous utilisez le chat
- Pour arrêter le serveur: Ctrl + C dans le terminal

# Prochaines étapes

Voir le fichier `SETUP_WEB.md` pour plus d'informations sur:
- Les fonctionnalités de l'interface
- Les endpoints API
- Les améliorations futures
