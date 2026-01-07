# SawerBot — Interface de chat AI (local)

Petite application web pour discuter avec une IA. Le serveur Flask sert les fichiers statiques et fournit l'endpoint `/api/chat`.

Fonctionnalités:
- Frontend: `invite.html`, `js/chat.js`, `style.css`
- Backend: `server/app.py` (proxy vers OpenAI si `OPENAI_API_KEY` est défini)

Installation (Windows PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Exécution (mode demo sans clé OpenAI):

```powershell
python server\app.py
# puis ouvrir http://127.0.0.1:5000/invite.html
```

Exécution avec OpenAI:

```powershell
$env:OPENAI_API_KEY = "votre_cle_api"
python server\app.py
# ouvrir http://127.0.0.1:5000/invite.html
```

Remarques:
- Si vous souhaitez utiliser un autre port, définissez la variable d'environnement `PORT`.
- Le serveur sert les fichiers statiques depuis la racine du projet; ouvrez `invite.html` via le serveur pour éviter les problèmes CORS.
