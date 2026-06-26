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

## Chatbot en ligne de commande

### Lancer le chatbot

```bash
cd /chemin/vers/ChatPy-2
python3 "ia_en_python.py"
```

Ou : `python "ia_en_python.py"` selon votre installation.

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
- **Mode quiz** : questions aléatoires tirées de la FAQ avec score de similarité
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
| Seuil minimum de similarité | Dans `chatbot_response()`, condition `if sim > 0.5:` |
| Nombre de suggestions affichées | Dans `obtenir_suggestions()`, tranche `[:2]` |
| Couleurs / emojis dans le terminal | Appels à `print_colored()` dans `ia_en_python.py` |
| Chemins des fichiers JSON | Constantes `FAQ_FILE`, `AIDE_CONCEPTS_FILE`, `HISTORY_FILE` en haut de `ia_en_python.py` |

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
├── _charger_json()            # lecture robuste des fichiers JSON
├── faq_categories / faq / norm_vers_original  # données chargées au démarrage
├── _formater_concept()        # mise en forme d'un concept pour le terminal
├── _chercher_concept()        # recherche dans aide_concepts.json
├── chatbot_response()         # FAQ + matching + toutes les commandes
├── print_colored()            # sortie terminal colorée / gras
├── mode_quiz()                # session quiz interactif
└── class ChatBot
    ├── _charger_historique() / _sauvegarder_historique()
    ├── ajouter_message / obtenir_contexte
    ├── obtenir_suggestions / traiter_message
    └── afficher_historique
```

Bon apprentissage Python.
