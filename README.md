# 🤖 ChatPy - Chatbot Python Amélioré

## 📖 Utilisation

### **Lancer le chatbot**

```bash
python3 "ia en python.py"
```

Ou en utilisant Python 3.x directement :
```bash
python "ia en python.py"
```

---

## 💬 Commandes disponibles

### **Poser une question**
```
📝 Vous: comment faire une boucle?
```
La réponse affichera :
- ✓ La réponse à votre question
- 💡 Le score de confiance (0-100%)
- 📌 Des questions liées suggérées

### **Voir toutes les questions**
```
📝 Vous: liste
```
Affiche les catégories de questions disponibles.

### **Obtenir de l'aide**
```
📝 Vous: help
```
ou
```
📝 Vous: aide
```

### **Voir l'historique**
```
📝 Vous: historique
```
Affiche toute la conversation depuis le début.

### **Quitter**
```
📝 Vous: au revoir
```
ou `bye`, `quit`, `exit`

---

## 🎯 Exemples d'utilisation

### **Exemple 1 : Question précise**
```
📝 Vous: qu'est-ce qu'une fonction?

✨ Bot: ✓ Une fonction en Python est un bloc de code...
💡 Confiance: 100%

📌 Questions liées:
  1. comment faire une fonction
  2. comment documenter une fonction
```

### **Exemple 2 : Question avec typo**
```
📝 Vous: komment trier une liste

✨ Bot: ✓ Utilisez la méthode sort() ou sorted()...
💡 Confiance: 87%
```

### **Exemple 3 : Question vague**
```
📝 Vous: les trucs en python

✨ Bot: ✓ Une liste est une structure de données...
💡 Confiance: 65%

ℹ️ D'autres réponses possibles :
  • comment afficher tous les éléments d'une liste (62%)
  • qu'est-ce qu'une liste (60%)
```

---

## 📚 Catégories disponibles

Le chatbot peut répondre à des questions dans 7 catégories :

1. **Bases** : Variables, affichage, input, conversions
2. **Fonctions** : Créer et documenter des fonctions
3. **Conditions et Boucles** : if/else, for, while, try/except
4. **Structures de données** : Listes, dictionnaires, tuples
5. **Modules et Fichiers** : Import, lecture/écriture de fichiers
6. **Utile** : sleep, random, version, help
7. **À propos** : Questions sur le chatbot lui-même

---

## 🚀 Fonctionnalités avancées

### **Reconnaissance flexible**
- ✅ Tolère les accents : "déclaré" = "declare"
- ✅ Tolère les typos : "komment" = "comment"
- ✅ Tolère la ponctuation : "comment faire une fonction?" = "comment faire une fonction"
- ✅ Tolère la casse : "COMMENT FAIRE UNE FONCTION" = "comment faire une fonction"

### **Score de confiance**
- **90-100%** : Très précis
- **70-89%** : Assez précis
- **50-69%** : Moins précis (alternatives suggérées)
- **< 50%** : Impossible de répondre

### **Mémoire de conversation**
- Le chatbot se souvient de toutes vos questions
- Accédez à l'historique complet avec `historique`
- Les questions posées ne seront pas re-suggérées

---

## 📝 Ajouter vos propres questions

Pour ajouter une nouvelle question, éditez le fichier et trouvez la section `faq_categories` :

```python
faq_categories = {
    "Bases": {
        "votre question": "Votre réponse avec exemples",
        "autre question": "Autre réponse",
    },
    # ... autres catégories
}
```

Ajoutez votre nouvelle paire question/réponse dans la catégorie appropriée.

---

## 🔗 Créer des relations entre questions

Pour que le chatbot suggère des questions après une réponse, éditez `self.relations` dans la classe `ChatBot` :

```python
self.relations = {
    "votre question": ["question 1 suggérée", "question 2 suggérée"],
    # ...
}
```

---

## ⚙️ Configuration

### Modifier le seuil de confiance minimum
Dans `chatbot_response()`, ligne avec `if sim > 0.5:`, changez `0.5` à votre valeur (0 à 1).

### Changer le nombre de suggestions
Dans la méthode `obtenir_suggestions()`, changez `[:2]` pour plus ou moins de suggestions.

### Afficher/masquer les émojis
Éditez les `print_colored()` et les symboles emoji (👋, 🤖, etc.) dans le code.

---

## 🐛 Dépannage

**Le script ne démarre pas :**
- Vérifiez Python 3.x est installé : `python3 --version`
- Vérifiez l'encodage UTF-8 du fichier

**Les accents ne fonctionnent pas :**
- Vérifiez que le terminal supporte UTF-8
- Sur macOS/Linux, c'est généralement automatique

**Les couleurs n'apparaissent pas :**
- Certains terminaux ne supportent pas les codes ANSI
- Le chatbot fonctionnera quand même, sans couleurs

---

## 📊 Architecture

```
ia en python.py
├── normaliser_texte()      : Nettoie les entrées
├── calcul_similarite()     : Calcule la similarité
├── chatbot_response()      : Logique principale du chatbot
├── print_colored()         : Affichage coloré
└── ChatBot (classe)        : Gestion mémoire + suggestions
    ├── ajouter_message()
    ├── obtenir_contexte()
    ├── obtenir_suggestions()
    ├── traiter_message()
    └── afficher_historique()
```

---

**Bon apprentissage Python ! 🚀**
