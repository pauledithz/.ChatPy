# 🎯 GUIDE RAPIDE - Comment utiliser ChatPy

## 1️⃣ LANCER LE CHATBOT

**Depuis le terminal :**

```bash
cd /chemin/vers/ChatPy-2
python3 "ia_en_python.py"
```

Tu devrais voir :
```
       ____  _           _   ____          │  ChatPy v1.0.0  —  Chatbot FAQ Python
      / ___|| |__   __ _| |_|  _ \ _   _  │
     | |    | '_ \ / _` | __| |_) | | | | │  📚  51 questions · 8 catégories · 8 concepts
     | |___ | | | | (_| | |_|  __/| |_| | │  🐍  Fonctionne 100% hors-ligne
      \____||_| |_|\__,_|\__|_|    \__, |  │
                                   |___/   │  💡  Tapez 'help' pour voir les commandes

📝 Vous:
```

> **Nouveau :** l'historique de tes sessions précédentes est rechargé automatiquement au démarrage.

---

## 2️⃣ ÉTAPES D'UTILISATION

### **Étape 1 : Voir ce que le chatbot peut faire**

```
📝 Vous: liste
```

Tu vas voir toutes les questions disponibles par catégorie.

Tu peux aussi filtrer par catégorie directement :

```
📝 Vous: liste fonctions
```

```
✨ Bot:
📚 Fonctions:
  • qu'est-ce qu'une fonction
  • À quoi sert une fonction
  • comment faire une fonction
  • comment documenter une fonction
```

Le nom de la catégorie n'a pas besoin d'être parfait — `liste structur` trouvera "Structures de données".

---

### **Étape 1b : Chercher par mot-clé**

```
📝 Vous: cherche liste
```

```
✨ Bot:
🔍 Questions contenant 'liste' :

📚 Conditions et Boucles:
  • comment vérifier si un élément est dans une liste

📚 Structures de données:
  • qu'est-ce qu'une liste
  • comment obtenir la longueur d'une liste
  • comment ajouter un élément à une liste
  ...
```

Utile pour trouver rapidement toutes les questions sur un sujet sans parcourir `liste` entièrement.

---

### **Étape 2 : Poser une question**

```
📝 Vous: comment faire une boucle
```

**Réponse attendue :**
```
✨ Bot: ✓ En Python, vous pouvez utiliser 'for' ou 'while'...
💡 Confiance: 95%

📌 Questions liées:
  1. comment faire une condition
  2. comment arrêter un programme
```

---

### **Étape 3 : Essayer avec des typos ou accents**

```
📝 Vous: komment afficher un messaj?
```

Le chatbot comprendra quand même ! 🎉

---

### **Étape 4 : Apprendre un concept en détail**

```
📝 Vous: aide boucle
```

Le chatbot affiche une explication complète sur 3 niveaux :

```
✨ Bot:
📖 Les boucles en Python

Définition : Une boucle répète un bloc de code...

━━ 🟢 Débutant — for et while
for i in range(5):
    print(i)

━━ 🟡 Intermédiaire — enumerate, zip, break, continue
for i, fruit in enumerate(['pomme', 'banane']):
    print(f'{i}: {fruit}')

━━ 🔴 Avancé — Compréhensions et générateurs
carres = [x**2 for x in range(6)]

⚠️  Erreurs courantes :
  • Oublier d'incrémenter le compteur dans un while → boucle infinie
  ...

💡 À retenir : Préférez 'for' quand vous connaissez...
```

**Sujets disponibles :** `variable`, `fonction`, `boucle`, `condition`, `liste`, `dictionnaire`, `exception`, `classe`

---

### **Étape 5 : Tester vos connaissances avec le quiz**

```
📝 Vous: quiz
```

Le chatbot pose une question aléatoire tirée de la FAQ et attend ta réponse.
Il compare ta réponse avec la bonne réponse et te donne un score :

```
🎯 Mode Quiz — répondez de mémoire, tapez 'fin' pour arrêter.

❓ qu'est-ce qu'une liste ?
📝 Votre réponse : c'est une structure qui contient des éléments
✅ Bonne réponse ! (similarité : 74%)
💡 Réponse attendue :
Une liste est une structure de données qui peut contenir plusieurs éléments.
Exemple :
ma_liste = [1, 2, 3, 'hello']

❓ comment faire une fonction ?
📝 Votre réponse : fin

📊 Score final : 1/1 (100%)
```

**Interprétation du score de similarité :**

| Score | Signification |
|-------|--------------|
| ≥ 70 % | ✅ Bonne réponse |
| 35–69 % | ⚠️ Presque — la bonne réponse s'affiche pour apprendre |
| < 35 % | ❌ Pas tout à fait — la bonne réponse s'affiche pour apprendre |

Tape `fin` à n'importe quel moment pour arrêter le quiz et voir ton score total.

---

### **Étape 6 : Voir votre historique**

```
📝 Vous: historique
```

Tu verras toutes les questions et réponses, **y compris celles des sessions précédentes** — l'historique est sauvegardé automatiquement dans le fichier `.chatpy_history.json`.

---

### **Étape 7 : Quitter**

```
📝 Vous: au revoir
```

**ou :** `bye`, `exit`, `quit`

---

## 3️⃣ EXEMPLES COMPLETS

### **Exemple 1 : Débutant**
```
       ____  _           _   ____          │  ChatPy v1.0.0  —  Chatbot FAQ Python
      / ___|| |__   __ _| |_|  _ \ _   _  │
     | |    | '_ \ / _` | __| |_) | | | | │  📚  51 questions · 8 catégories · 8 concepts
     | |___ | | | | (_| | |_|  __/| |_| | │  🐍  Fonctionne 100% hors-ligne
      \____||_| |_|\__,_|\__|_|    \__, |  │
                                   |___/   │  💡  Tapez 'help' pour voir les commandes

📝 Vous: aide

✨ Bot: Commandes disponibles :
  liste      — voir toutes les questions du catalogue
  quiz       — tester vos connaissances Python
  historique — relire la conversation
  au revoir  — quitter

  Ou posez directement une question sur Python.

📝 Vous: liste

✨ Bot: 📚 Bases:
  • comment déclarer une variable
  • comment afficher un message
  • comment lire une entrée utilisateur
  ...

📝 Vous: comment afficher un message

✨ Bot: ✓ Utilisez la fonction print()
Exemple :
print('Bonjour !')
print(f'Hello {nom}')

💡 Confiance: 100%

📝 Vous: au revoir

À bientôt ! Continue à apprendre Python tout les jours ! 🚀
```

---

### **Exemple 2 : Question imprécise**
```
📝 Vous: comment faire un truc avec les listes?

✨ Bot: ✓ Une liste est une structure de données...
💡 Confiance: 68%

ℹ️ D'autres réponses possibles :
  • comment obtenir la longueur d'une liste (71%)
  • comment ajouter un élément à une liste (69%)
```

---

### **Exemple 3 : Session de quiz**
```
📝 Vous: quiz

🎯 Mode Quiz — répondez de mémoire, tapez 'fin' pour arrêter.

❓ comment importer un module ?
📝 Votre réponse : avec import
⚠️  Presque ! (similarité : 42%)
💡 Réponse attendue :
Utilisez le mot-clé 'import'.
Exemple :
import math

from math import sqrt

❓ qu'est-ce qu'une variable ?
📝 Votre réponse : un espace de stockage pour garder une valeur
✅ Bonne réponse ! (similarité : 78%)
💡 Réponse attendue :
Une variable, c'est un espace de stockage nommé...

❓ comment faire une boucle ?
📝 Votre réponse : fin

📊 Score final : 1/2 (50%)
```

---

## 4️⃣ TOUTES LES COMMANDES

| Commande | Résultat |
|----------|----------|
| `liste` | Voir toutes les questions par catégorie |
| `liste <catégorie>` | Questions d'une seule catégorie (ex : `liste fonctions`) |
| `cherche <mot>` | Toutes les questions contenant un mot-clé (ex : `cherche boucle`) |
| `aide <sujet>` | Explication détaillée débutant→avancé (ex : `aide variable`) |
| `quiz` | Lancer une session de quiz interactif |
| `help` ou `aide` ou `?` | Obtenir de l'aide |
| `historique` | Voir toute la conversation (sessions incluses) |
| `au revoir` / `bye` / `exit` / `quit` | Quitter le chatbot |
| `bonjour` / `salut` | Réponse de bienvenue |

---

## 5️⃣ CE QUE LE CHATBOT RECONNAIT

✅ **Le chatbot comprend :**
- Les accents : "déclarer" = "declarer"
- Les typos : "komment" = "comment"
- La ponctuation : "comment ?" = "comment"
- La casse : "COMMENT" = "comment"
- Les variantes : "faire une boucle" = "boucle"

❌ **Le chatbot NE comprend PAS :**
- Les questions sans rapport avec Python
- Les phrases très longues et complexes
- Les questions en d'autres langues

---

## 6️⃣ INTERPRÉTER LE SCORE DE CONFIANCE

```
💡 Confiance: 100% → ✅ Correspondance exacte
💡 Confiance: 75%  → ✅ Assez fiable
💡 Confiance: 60%  → ⚠️ Alternative proposée en plus
💡 Confiance: 40%  → ⚠️ Résultat approximatif
```

---

## 7️⃣ AJOUTER VOS PROPRES QUESTIONS

**Ouvrez `faq.json`** (pas besoin de toucher au code Python !) :

```json
{
  "Bases": {
    "comment déclarer une variable": "Réponse...",
    "ma nouvelle question": "Ma nouvelle réponse avec exemple"
  }
}
```

**Sauvegardez** et relancez le chatbot — la nouvelle question apparaît dans `liste` et dans le `quiz` automatiquement.

---

## 7️⃣b AJOUTER UN CONCEPT DÉTAILLÉ

**Ouvrez `aide_concepts.json`** et ajoutez une nouvelle entrée :

```json
{
  "mon_concept": {
    "titre": "Mon concept en Python",
    "mots_cles": ["mot1", "mot2"],
    "definition": "Définition courte.",
    "niveaux": [
      { "niveau": "🟢 Débutant — ...", "code": "# exemple\nx = 5" },
      { "niveau": "🟡 Intermédiaire — ...", "code": "# exemple\n..." },
      { "niveau": "🔴 Avancé — ...", "code": "# exemple\n..." }
    ],
    "erreurs_courantes": ["erreur fréquente 1"],
    "a_retenir": "Le point le plus important à retenir."
  }
}
```

Ensuite tapez `aide mon_concept` dans le chatbot.

---

## 8️⃣ HISTORIQUE PERSISTANT

Chaque message est automatiquement sauvegardé dans le fichier **`.chatpy_history.json`** dans le dossier du projet.

- Il est rechargé au prochain démarrage — tu ne perds plus ta conversation.
- Pour repartir de zéro : supprime `.chatpy_history.json` (il sera recréé vide).

---

## 🚀 PRÊT À DÉMARRER ?

Ouvre ton terminal et tape :

```bash
cd /chemin/vers/ChatPy-2
python3 "ia_en_python.py"
```

Puis essaie :
```
📝 Vous: liste
📝 Vous: liste fonctions
📝 Vous: cherche boucle
📝 Vous: qu'est-ce qu'une fonction?
📝 Vous: aide boucle
📝 Vous: quiz
📝 Vous: historique
```

**Bon apprentissage ! 🎓**
