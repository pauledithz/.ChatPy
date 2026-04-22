# ChatPy

Petit projet autour de **ChatPy** : un chatbot Python en ligne de commande (FAQ interactive) et une **page d’accueil statique** animée pour présenter le produit.

## Contenu du dépôt

| Fichier | Rôle |
|--------|------|
| `ia_en_python.py` | Chatbot CLI : questions Python, score de confiance, suggestions |
| `chatpy_landing_animated.html` | Page vitrine (HTML) |
| `style.css`, `script.js` | Styles et démo animée du chat sur la landing |
| `ChatPY_logo.PNG` | Favicon / logo |
| `GUIDE_UTILISATION.md` | Guide pas à pas (complément au README) |

---

## Page vitrine

La landing est une page **100 % statique** (pas de serveur obligatoire).

1. Ouvrez `chatpy_landing_animated.html` dans votre navigateur (double-clic ou menu *Fichier → Ouvrir*).
2. Ou, depuis le dossier du projet, servez les fichiers en local puis ouvrez l’URL affichée :

```bash
cd /chemin/vers/ChatPy-1
python3 -m http.server 8080
```

Puis : `http://localhost:8080/chatpy_landing_animated.html`

---

## Chatbot en ligne de commande

### Lancer le chatbot

```bash
cd /chemin/vers/ChatPy-1
python3 "ia_en_python.py"
```

Ou : `python "ia_en_python.py"` selon votre installation.

### Commandes utiles

| Saisie | Effet |
|--------|--------|
| *(une question en langage naturel)* | Réponse + score de confiance + questions liées si disponibles |
| `liste` | Affiche les questions disponibles par catégorie |
| `help`, `aide`, `?` | Rappel des commandes |
| `historique` | Conversation depuis le début |
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

**Entrée avec fautes / accents** — le texte est normalisé (accents, ponctuation, casse) et une similarité est calculée ; des typos peuvent quand même matcher une FAQ proche.

---

## Catégories couvertes par la FAQ

1. **Bases** — variables, affichage, `input`, conversions  
2. **Fonctions** — définition, `return`, docstrings  
3. **Conditions et boucles** — `if` / `for` / `while`, `try` / `except`  
4. **Structures de données** — listes, dictionnaires, tuples  
5. **Modules et fichiers** — imports, lecture / écriture de fichiers, `pip`  
6. **Utile** — `sleep`, `random`, version Python, `help`  
7. **À propos** — questions sur le chatbot lui-même  

---

## Fonctionnalités du moteur de réponses

- **Normalisation** : accents, ponctuation, espaces, casse  
- **Score de confiance** :  
  - 90–100 % : très fiable  
  - 70–89 % : assez fiable  
  - 50–69 % : réponse possible + alternatives  
  - moins de 50 % : pas de réponse fiable  
- **Mémoire** : historique des messages ; commande `historique`  

---

## Personnaliser le chatbot

### Ajouter des questions / réponses

Dans `ia_en_python.py`, fonction **`chatbot_response()`**, modifiez le dictionnaire **`faq_categories`** (questions normalisées côté logique via `normaliser_texte` à l’usage, mais les clés de la FAQ sont les formulations de référence) :

```python
def chatbot_response(message):
    ...
    faq_categories = {
        "Bases": {
            "votre question": "Votre réponse avec exemples",
        },
        ...
    }
```

### Questions liées après une réponse

Dans la classe **`ChatBot`**, attribut **`self.relations`** : associez une question source à une liste de suggestions.

---

## Configuration rapide

| Objectif | Où modifier |
|----------|-------------|
| Seuil minimum de similarité | Dans `chatbot_response()`, condition `if sim > 0.5:` (vers la ligne 121) |
| Nombre de suggestions affichées | Dans `obtenir_suggestions()`, tranche `[:2]` (vers la ligne 202) |
| Couleurs / emojis dans le terminal | Appels à `print_colored()` et chaînes affichées dans `ia_en_python.py` |

---

## Dépannage

- **Le script ne démarre pas** : `python3 --version` ; fichier en UTF-8 ; chemin avec espaces : gardez les guillemets autour de `"ia_en_python.py"`.  
- **Accents bizarres** : terminal en UTF-8 (souvent OK sur macOS / Linux).  
- **Pas de couleurs ANSI** : le programme fonctionne quand même, sans couleurs.  

---

## Architecture du script Python

```
ia_en_python.py
├── normaliser_texte()     # entrée utilisateur
├── calcul_similarite()    # SequenceMatcher
├── chatbot_response()     # FAQ + matching + commandes spéciales
├── print_colored()        # sortie terminal
└── class ChatBot
    ├── ajouter_message / obtenir_contexte
    ├── obtenir_suggestions / traiter_message
    └── afficher_historique
```

Bon apprentissage Python.
