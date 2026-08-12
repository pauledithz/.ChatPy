# ChatPy

Petit projet autour de **ChatPy** : un chatbot Python en ligne de commande (FAQ interactive) et une **page d'accueil statique** animée pour présenter le produit.

## Contenu du dépôt

| Fichier | Rôle |
|--------|------|
| `ia_en_python.py` | Chatbot CLI : questions Python, score de confiance, suggestions, quiz |
| `chatpy_landing_animated.html` | Page vitrine (HTML) |
| `style.css`, `script.js` | Styles et démo animée du chat sur la landing |
| `ChatPY_logo.PNG` | Favicon / logo |
| `GUIDE_UTILISATION.md` | Guide pas à pas (complément au README) |
| `.chatpy_history.json` | Historique persistant des conversations (créé automatiquement) |

---

## Page vitrine

La landing est une page **100 % statique** (pas de serveur obligatoire).

1. Ouvrez `chatpy_landing_animated.html` dans votre navigateur (double-clic ou menu *Fichier → Ouvrir*).
2. Ou, depuis le dossier du projet, servez les fichiers en local puis ouvrez l'URL affichée :

```bash
cd /chemin/vers/ChatPy-2
python3 -m http.server 8080
```

Puis : `http://localhost:8080/chatpy_landing_animated.html`

---

## Interface web (Flask)

En plus du CLI, le chatbot est accessible depuis un navigateur via un petit backend Flask (`app.py`).

```bash
cd /chemin/vers/ChatPy-2
python3 -m venv .venv && source .venv/bin/activate   # première fois seulement
pip install -r requirements.txt
python3 app.py
```

Puis ouvrez `http://localhost:5001` (la landing page) ou directement `http://localhost:5001/chat` (interface de chat fonctionnelle, avec de vrais échanges avec le bot — à ne pas confondre avec la démo animée de la landing page).

> Utilisez un environnement virtuel (`.venv`) plutôt qu'un `pip install` global : sur macOS avec Python Homebrew, l'installation globale de paquets est bloquée par défaut (PEP 668). Le port 5001 (et non 5000) est utilisé car macOS occupe souvent le port 5000 avec le service AirPlay Receiver.

Le backend appelle la même logique que le CLI (`bot.traiter_message()` dans `ia_en_python.py`), donc l'historique (`.chatpy_history.json`) est partagé entre le CLI et le web. Le lien "Chat" est visible dans la nav de la landing page et accessible sans connexion : se connecter n'est jamais obligatoire pour discuter avec le bot.

### Créer un compte par email (aucune configuration)

Le formulaire du modal fonctionne : email + mot de passe, avec bascule entre connexion et inscription. Contrairement à Google et GitHub, il ne demande aucun identifiant à configurer — il marche sur un clone frais.

Deux limites assumées, dues à l'absence de serveur d'envoi d'emails : **les adresses ne sont pas vérifiées**, et **il n'y a pas de réinitialisation de mot de passe** — d'où la double saisie à l'inscription.

### Où sont rangés les comptes

Dans une base **SQLite**, `chatpy.db`, créée toute seule au premier démarrage (module `base_donnees.py`, schéma dans `schema.sql`). Une ligne par personne connectée, quel que soit son moyen de connexion : nom, email, fournisseur (`local` / `google` / `github`), date de création, date de dernière connexion et nombre de passages.

**Le mot de passe n'y est jamais écrit en clair** : seule y figure son empreinte scrypt, qui permet de vérifier un mot de passe sans jamais pouvoir le relire. Les comptes Google et GitHub n'ont même pas d'empreinte — leur mot de passe reste chez eux. La base est en `chmod 600`, ignorée par git, et jamais servie par le web.

Pour voir qui s'est inscrit :

```bash
python3 base_donnees.py             # la table des comptes dans le terminal
python3 base_donnees.py --csv       # export_comptes.csv → Numbers, Excel
python3 base_donnees.py --sql       # dump SQL brut de la base (sauvegarde)
```

La première ligne affichée rappelle toujours quel fichier est lu : `Base : chatpy.db`.

Pour ouvrir la base elle-même : l'extension VS Code **SQLite Viewer** (double-clic sur `chatpy.db`), ou en ligne de commande `sqlite3 chatpy.db`, déjà installé sur macOS.

Un ancien `comptes.json` est repris automatiquement au premier lancement, puis renommé `comptes.json.repris` : rien à faire, et rien n'est supprimé. `CHATPY_DB` déplace la base ailleurs (indispensable en production, voir plus bas).

### Connexion Google et GitHub (optionnelle)

Ces deux boutons fonctionnent aussi (Apple et Yahoo restent décoratifs). Chacun demande une paire d'identifiants dans `.env` ; copiez le modèle et remplissez ce dont vous avez besoin :

```bash
cp .env.example .env
python3 -c "import secrets; print(secrets.token_hex(32))"   # CHATPY_SECRET_KEY
```

| Fournisseur | Où créer les identifiants | URL de redirection à déclarer |
|-------------|---------------------------|-------------------------------|
| Google | [console.cloud.google.com](https://console.cloud.google.com) → Google Auth Platform → Clients → Web application | `http://localhost:5001/auth/google/callback` |
| GitHub | [github.com/settings/developers](https://github.com/settings/developers) → OAuth Apps → New OAuth App | `http://localhost:5001/auth/github/callback` |

L'URL de redirection doit être identique au caractère près, sinon le fournisseur refuse avec `redirect_uri_mismatch`. Tant qu'une paire reste vide, la route `/auth/<fournisseur>` correspondante répond 503 et le reste du site fonctionne normalement : on peut n'en configurer qu'un, ou aucun.

La connexion vit dans le cookie de session. Une fois connecté, vos conversations sont archivées côté serveur (`conversations.json`, cloisonné par compte) et vous les retrouvez depuis n'importe quel appareil ; sans compte, elles restent dans votre navigateur. Le journal `.chatpy_history.json`, lui, alimente le contexte du bot et reste commun à tous.

---

## Mise en ligne

`python3 app.py` lance le **serveur de développement** de Werkzeug : il n'est ni conçu ni durci pour être exposé sur Internet. En production, utilisez le `Procfile` fourni :

```bash
gunicorn --workers 1 --threads 8 --timeout 60 --bind 0.0.0.0:$PORT app:app
```

### Un seul worker, ce n'est pas négociable

Les conversations et l'historique du bot reposent sur des fichiers JSON protégés par des `threading.Lock`. Ces verrous fonctionnent entre **fils d'exécution**, pas entre **processus**. Avec `--workers 4`, deux processus peuvent lire, modifier et réécrire `conversations.json` en même temps : le second écrase le premier. Le blocage anti-force-brute, qui vit en mémoire, serait lui aussi compté par worker (5 tentatives × 4 workers = 20).

Les comptes, eux, ne risquent plus rien : ils sont dans SQLite, qui verrouille entre processus. Mais ça n'enlève que la pire conséquence, pas la raison.

`--workers 1 --threads 8` conserve toutes les hypothèses du code tout en servant plusieurs visiteurs à la fois. Pour aller au-delà, il faudrait déplacer ces fichiers JSON dans la base à leur tour.

> `gunicorn` ne tourne pas sous Windows. Y utiliser `waitress` : `waitress-serve --threads=8 --port=5001 app:app`.

### Réglages `.env` en production

| Variable | Valeur | Pourquoi |
|----------|--------|----------|
| `CHATPY_SECRET_KEY` | une clé fixe | Sans elle, une clé aléatoire est tirée à chaque démarrage : tout le monde est déconnecté à chaque redéploiement |
| `CHATPY_COOKIE_SECURE` | `1` | Réserve le cookie de session au HTTPS |
| `CHATPY_DEBUG` | vide | Le debugger Werkzeug permet l'exécution de code arbitraire |
| `CHATPY_PROXIES` | `1` derrière un proxy | Sinon les redirections OAuth pointent vers `127.0.0.1` |

**HTTPS est obligatoire** : depuis l'ajout des comptes par mot de passe, ceux-ci circulent sur le réseau.

`CHATPY_PROXIES` ne doit être renseigné **que** si un reverse proxy réécrit réellement les en-têtes `X-Forwarded-*`. Les activer sans proxy devant laisserait n'importe quel visiteur annoncer `X-Forwarded-Host: site-pirate.fr` et détourner la connexion OAuth vers son domaine. La plupart des hébergeurs (Render, Railway, Fly, Heroku) en ont un : `1`.

### À faire aussi

- **Déclarer les URL de redirection de production** dans la console Google Cloud et les réglages de l'OAuth App GitHub (`https://votre-domaine/auth/google/callback` et `.../auth/github/callback`). Celles de `localhost` ne fonctionneront pas en ligne.
- **Renseigner `CHATPY_DB`** avec un chemin sur le disque persistant de l'hébergeur (`/var/data/chatpy.db` par exemple), **avant la première inscription**. La plupart des hébergeurs reconstruisent le dossier du code à chaque déploiement : une base restée là repartirait vide, avec tous les comptes.
- **Sauvegarder `chatpy.db`.** C'est l'unique copie des comptes, et il n'existe pas de « mot de passe oublié » : le perdre enferme définitivement les utilisateurs dehors. Une copie du fichier serveur arrêté, ou `python3 base_donnees.py --sql > sauvegarde.sql`. `conversations.json` mérite le même soin.

---

## Chatbot en ligne de commande

### Lancer le chatbot

```bash
cd /chemin/vers/ChatPy-2
python3 "ia_en_python.py"
```

Ou : `python "ia_en_python.py"` selon votre installation.

Au démarrage, un écran d'accueil s'affiche avec la mascotte, la version, les stats de la FAQ et un rappel pour `help` :

```
       ____  _           _   ____          │  ChatPy v1.0.0  —  Chatbot FAQ Python
      / ___|| |__   __ _| |_|  _ \ _   _  │
     | |    | '_ \ / _` | __| |_) | | | | │  📚  51 questions · 8 catégories · 8 concepts
     | |___ | | | | (_| | |_|  __/| |_| | │  🐍  Fonctionne 100% hors-ligne
      \____||_| |_|\__,_|\__|_|    \__, |  │
                                   |___/   │  💡  Tapez 'help' pour voir les commandes
```

Les stats (nombre de questions, catégories, concepts) se mettent à jour automatiquement selon le contenu de `faq.json` et `aide_concepts.json`.

### Commandes disponibles

| Saisie | Effet |
|--------|--------|
| *(une question en langage naturel)* | Réponse + score de confiance + questions liées si disponibles |
| `liste` | Affiche toutes les questions par catégorie |
| `liste <catégorie>` | Questions d'une seule catégorie (ex : `liste fonctions`) — accepte les abréviations et les fautes légères |
| `cherche <mot>` | Toutes les questions contenant ce mot-clé (ex : `cherche liste`) |
| `aide <sujet>` | Explication détaillée débutant → avancé (ex : `aide boucle`, `aide classe`) |
| `quiz` | Lance une session de quiz interactif pour tester vos connaissances |
| `help`, `aide`, `?` | Rappel des commandes |
| `historique` | Conversation depuis le début (sessions incluses) |
| `au revoir`, `bye`, `quit`, `exit` | Quitter |

### Exemples

**Question précise**

```
📝 Vous: qu'est-ce qu'une fonction?

✨ Bot: ✓ Une fonction en Python est un bloc de code...
💡 Confiance: 100%

📌 Questions liées:
  1. comment faire une fonction
  2. comment documenter une fonction
```

**Mode quiz**

```
📝 Vous: quiz

🎯 Mode Quiz — répondez de mémoire, tapez 'fin' pour arrêter.

❓ qu'est-ce qu'une liste ?
📝 Votre réponse : c'est une structure qui contient plusieurs éléments
✅ Bonne réponse ! (similarité : 74%)
💡 Réponse attendue : Une liste est une structure de données...

📊 Score final : 1/1 (100%)
```

**Entrée avec fautes / accents** — le texte est normalisé (accents, ponctuation, casse) avant comparaison ; les typos peuvent quand même correspondre à une FAQ proche.

---

## Catégories couvertes par la FAQ

1. **Bases** — variables, affichage, `input`, conversions
2. **Fonctions** — définition, `return`, docstrings
3. **Conditions et boucles** — `if` / `for` / `while`, `try` / `except`
4. **Structures de données** — listes, dictionnaires, tuples
5. **Modules et fichiers** — imports, lecture / écriture de fichiers, `pip`
6. **Utile** — `sleep`, `random`, version Python, `help`
7. **À propos** — questions sur le chatbot lui-même
8. **Job et apprentissage Python** — devenir développeur, trouver un emploi, AI engineer

---

## Fonctionnalités du moteur de réponses

- **Normalisation** : accents, ponctuation, espaces, casse
- **Score de confiance** :
  - 90–100 % : très fiable
  - 70–89 % : assez fiable
  - 50–69 % : réponse possible + alternatives proposées
  - moins de 50 % : pas de réponse fiable
- **Mémoire persistante** : l'historique est sauvegardé dans `.chatpy_history.json` et rechargé à chaque démarrage
- **Mode quiz** : questions aléatoires tirées de la FAQ ; citer les bons mots-clés suffit (répondre « append » à « comment ajouter un élément à une liste » compte juste)
- **Aide détaillée** : 8 concepts Python expliqués sur 3 niveaux (débutant → avancé), chargés depuis `aide_concepts.json`

---

## Personnaliser le chatbot

### Ajouter des questions / réponses FAQ

Ouvrez **`faq.json`** et ajoutez votre question dans la bonne catégorie :

```json
{
  "Bases": {
    "ma nouvelle question": "Ma nouvelle réponse avec exemples",
    ...
  }
}
```

Sauvegardez et relancez — la nouvelle question apparaît dans `liste` et dans le `quiz` automatiquement.

### Ajouter un concept détaillé (`aide`)

Ouvrez **`aide_concepts.json`** et ajoutez une entrée en suivant le modèle existant :

```json
{
  "mon_concept": {
    "titre": "Mon concept en Python",
    "mots_cles": ["mot1", "mot2"],
    "definition": "Définition courte.",
    "niveaux": [
      { "niveau": "🟢 Débutant — ...", "code": "# exemple\n..." },
      { "niveau": "🟡 Intermédiaire — ...", "code": "# exemple\n..." },
      { "niveau": "🔴 Avancé — ...", "code": "# exemple\n..." }
    ],
    "erreurs_courantes": ["erreur 1", "erreur 2"],
    "a_retenir": "Résumé clé."
  }
}
```

### Questions liées après une réponse

Dans la classe **`ChatBot`**, attribut **`self.relations`** : associez une question source à une liste de suggestions.

---

## Configuration rapide

| Objectif | Où modifier |
|----------|-------------|
| Ajouter / modifier des questions FAQ | `faq.json` |
| Ajouter un concept détaillé | `aide_concepts.json` |
| Seuil minimum de correspondance | Constante `SEUIL_CORRESPONDANCE` en haut de `ia_en_python.py` |
| Poids vocabulaire / orthographe dans le score | Constante `POIDS_MOTS` en haut de `ia_en_python.py` |
| Mots ignorés par le matching | Ensemble `MOTS_VIDES` en haut de `ia_en_python.py` |
| Nombre de suggestions affichées | Dans `obtenir_suggestions()`, tranche `[:2]` |
| Couleurs / emojis dans le terminal | Appels à `print_colored()` dans `ia_en_python.py` |
| Chemins des fichiers JSON | Constantes `FAQ_FILE`, `AIDE_CONCEPTS_FILE`, `HISTORY_FILE` en haut de `ia_en_python.py` |

---

## Tests

La suite de tests n'utilise que la bibliothèque standard (`unittest`) et ne touche jamais aux vrais fichiers du projet :

```bash
python3 -m unittest test_chatpy -v
python3 -m unittest tests.test_base_donnees -v   # comptes et base SQLite
python3 -m unittest discover -v                  # tout
```

Lancez-la après toute modification de `ia_en_python.py`.

Les tests qui écrivent redirigent la base et les fichiers d'exécution vers un dossier temporaire : `chatpy.db` et vos vrais comptes ne sont jamais touchés.

---

## Dépannage

- **Le script ne démarre pas** : `python3 --version` ; fichier en UTF-8 ; chemin avec espaces : gardez les guillemets autour de `"ia_en_python.py"`.
- **Accents bizarres** : terminal en UTF-8 (souvent OK sur macOS / Linux).
- **Pas de couleurs ANSI** : le programme fonctionne quand même, sans couleurs.
- **Historique corrompu** : supprimez `.chatpy_history.json` — il sera recréé vide au prochain lancement.

---

## Architecture du script Python

```
Fichiers de données (modifiables sans toucher au code Python) :
├── faq.json              → toutes les questions/réponses du chatbot
├── aide_concepts.json    → 8 concepts expliqués sur 3 niveaux
└── .chatpy_history.json  → historique persistant (créé automatiquement)

ia_en_python.py :
├── _DIR / HISTORY_FILE / FAQ_FILE / AIDE_CONCEPTS_FILE  # chemins
├── normaliser_texte()         # nettoyage de l'entrée
├── calcul_similarite()        # SequenceMatcher (0 à 1)
├── _score_correspondance()    # score hybride lettres + vocabulaire (0 à 1)
├── _charger_json()            # lecture robuste des fichiers JSON
├── faq_categories / faq / norm_vers_original  # données chargées au démarrage
├── _formater_concept()        # mise en forme d'un concept pour le terminal
├── _chercher_concept()        # recherche dans aide_concepts.json
├── chatbot_response()         # FAQ + matching + toutes les commandes
├── print_colored()            # sortie terminal colorée / gras
├── afficher_demarrage()       # écran d'accueil mascotte + stats au lancement
├── mode_quiz()                # session quiz interactif
└── class ChatBot
    ├── _charger_historique() / _sauvegarder_historique()
    ├── ajouter_message / obtenir_suggestions
    ├── traiter_message
    └── afficher_historique

test_chatpy.py  → tests unitaires (python3 -m unittest test_chatpy)
```

Bon apprentissage Python.
