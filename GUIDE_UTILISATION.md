# 🎯 GUIDE RAPIDE - Comment utiliser ChatPy

## 1️⃣ LANCER LE CHATBOT

**Depuis le terminal :**

```bash
cd ~/.mobisystems
python3 "ia en python.py"
```

**Ou d'une autre façon :**

```bash
python3 ~/.mobisystems/ia\ en\ python.py
```

Tu devrais voir :
```
🤖 Bienvenue sur ChatPy!
Posez-moi une question sur Python (tapez 'au revoir' pour quitter).
Tapez 'help' pour l'aide ou 'liste' pour voir les questions disponibles.
Tapez 'historique' pour voir toute la conversation.

📝 Vous: 
```

---

## 2️⃣ ÉTAPES D'UTILISATION

### **Étape 1 : Voir ce que le chatbot peut faire**

```
📝 Vous: liste
```

Tu vas voir toutes les questions disponibles par catégorie.

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

### **Étape 4 : Voir votre historique**

```
📝 Vous: historique
```

Tu verras toutes les questions et réponses précédentes.

---

### **Étape 5 : Quitter**

```
📝 Vous: au revoir
```

**ou :** `bye`, `exit`, `quit`

---

## 3️⃣ EXEMPLES COMPLETS

### **Exemple 1 : Débutant**
```
🤖 Bienvenue sur ChatPy!
📝 Vous: aide

✨ Bot: Tapez 'liste' pour voir toutes les questions...

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

À bientôt ! Continue à apprendre Python 🚀
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

## 4️⃣ TOUCHES SPÉCIALES

| Commande | Résultat |
|----------|----------|
| `liste` | Voir toutes les questions |
| `help` ou `aide` | Obtenir de l'aide |
| `historique` | Voir toute la conversation |
| `au revoir` / `bye` / `exit` | Quitter le chatbot |
| `bonjour` / `salut` | Réponse personnalisée |

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
💡 Confiance: 95%  → ✅ Très fiable
💡 Confiance: 75%  → ✅ Assez fiable
💡 Confiance: 60%  → ⚠️ Alternative proposée
💡 Confiance: 40%  → ⚠️ Résultat approximatif
```

---

## 7️⃣ AJOUTER VOS PROPRES QUESTIONS

**Ouvrez le fichier** `ia en python.py` et trouvez :

```python
faq_categories = {
    "Bases": {
        "comment déclarer une variable": "Réponse...",
```

**Ajoutez votre question :**

```python
faq_categories = {
    "Bases": {
        "comment déclarer une variable": "Réponse...",
        "ma nouvelle question": "Ma nouvelle réponse",  # 👈 Ajoutez ici
```

**Sauvegardez** et relancez le chatbot.

---

## 🚀 PRÊT À DÉMARRER ?

Ouvre ton terminal et tape :

```bash
python3 ~/.mobisystems/ia\ en\ python.py
```

Puis essaie :
```
📝 Vous: liste
📝 Vous: qu'est-ce qu'une fonction?
📝 Vous: historique
```

**Bon apprentissage ! 🎓**
