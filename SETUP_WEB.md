# ChatPy - Interface Web

Interface web moderne pour ton chatbot Python ChatPy.

## 📋 Fichiers inclus

- **app.py** - Serveur Flask (API backend)
- **index.html** - Interface principale
- **style.css** - Styles et design
- **script.js** - Logique frontend

## 🚀 Installation et démarrage

### 1. Installer les dépendances

```bash
pip install flask flask-cors
```

### 2. Lancer le serveur

```bash
python app.py
```

Le serveur démarre sur `http://localhost:5000`

### 3. Ouvrir l'interface

Ouvre `index.html` dans ton navigateur ou accède à `http://localhost:5000`

## ✨ Fonctionnalités

✅ **Chat en temps réel** - Réponses instantanées  
✅ **Catégories** - Questions organisées par sujet  
✅ **Questions rapides** - Raccourcis pour les questions populaires  
✅ **Design responsive** - Fonctionne sur mobile et desktop  
✅ **Historique** - Garder trace de la conversation  
✅ **Interface moderne** - Design sombre avec couleurs Python  

## 🎨 Design

- **Couleur primaire** : Bleu Python (#3776ab)
- **Couleur secondaire** : Jaune Python (#ffd43b)
- **Thème** : Dark mode professionnel

## 📱 Responsive

L'interface s'adapte automatiquement à :
- Ordinateurs de bureau (1920px+)
- Tablettes (768px - 1024px)
- Téléphones (< 768px)

## 🔌 API Endpoints

### POST /api/chat
Envoie un message et reçoit une réponse

**Request:**
```json
{
  "message": "comment déclarer une variable"
}
```

**Response:**
```json
{
  "response": "En Python, il suffit d'écrire..."
}
```

### GET /api/questions
Récupère toutes les questions par catégorie

## 🎯 Améliorations futures

- [ ] Persistance de l'historique en base de données
- [ ] Authentification utilisateur
- [ ] Export de la conversation (PDF, TXT)
- [ ] Dark/Light mode toggle
- [ ] Intégration Discord Bot
- [ ] Système de notation des réponses
- [ ] Analytics et statistiques d'utilisation
