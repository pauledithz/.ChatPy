from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import unicodedata
from difflib import get_close_matches, SequenceMatcher

app = Flask(__name__)
CORS(app)

def normaliser_texte(texte):
    """Supprime accents, ponctuation et normalise le texte"""
    texte = unicodedata.normalize('NFKD', texte)
    texte = texte.encode('ASCII', 'ignore').decode('ASCII')
    texte = re.sub(r'[^\w\s]', ' ', texte)
    texte = re.sub(r'\s+', ' ', texte).strip()
    return texte.lower()

def calcul_similarite(texte1, texte2):
    """Calcule la similarité entre deux textes (0 à 1)"""
    return SequenceMatcher(None, texte1, texte2).ratio()

# FAQ organisée par catégories
faq_categories = {
    "Bases": {
        "comment déclarer une variable": "En Python, il suffit d'écrire le nom de la variable, un égal, puis la valeur.\nExemple :\nx = 5\nnom = 'Alice'",
        "comment afficher un message": "Utilisez la fonction print().\nExemple :\nprint('Bonjour !')\nprint(f'Hello {nom}')",
        "comment lire une entrée utilisateur": "Utilisez input().\nExemple :\nnom = input('Votre nom ? ')",
        "comment convertir une chaîne en entier": "Utilisez int().\nExemple :\nx = int('5')",
        "comment convertir un entier en chaîne": "Utilisez str().\nExemple :\ns = str(5)",
    },
    "Fonctions": {
        "qu'est-ce qu'une fonction": "Une fonction en Python est un bloc de code réutilisable qui s'exécute lorsqu'on l'appelle avec son nom.\nExemple :\ndef ma_fonction():\n    print('Hello')",
        "comment faire une fonction": "Utilisez le mot-clé def.\nExemple :\ndef ma_fonction():\n    print('Hello')\n\ndef addition(a, b):\n    return a + b",
        "comment documenter une fonction": "Utilisez une docstring.\nExemple :\ndef f():\n    '''Ceci est une docstring'''\n    pass",
    },
    "Conditions et Boucles": {
        "comment faire une condition": "Utilisez if, elif, else.\nExemple :\nif x > 0:\n    print('positif')\nelif x < 0:\n    print('négatif')\nelse:\n    print('zéro')",
        "comment faire une boucle": "En Python, vous pouvez utiliser 'for' ou 'while' pour faire des boucles.\nExemple avec for :\nfor i in range(5):\n    print(i)\n\nExemple avec while :\ni = 0\nwhile i < 5:\n    print(i)\n    i += 1",
        "comment faire une boucle infinie": "Utilisez while True:.\nExemple :\nwhile True:\n    print('boucle infinie')\n    # N'oubliez pas de break pour sortir",
        "comment faire une exception": "Utilisez try/except.\nExemple :\ntry:\n    # code risqué\n    x = 1 / 0\nexcept ZeroDivisionError as e:\n    print(f'Erreur: {e}')",
        "comment vérifier si un élément est dans une liste": "Utilisez in.\nExemple :\nif 3 in ma_liste:\n    print('Présent')",
    },
    "Structures de données": {
        "qu'est-ce qu'une liste": "Une liste est une structure de données qui peut contenir plusieurs éléments.\nExemple :\nma_liste = [1, 2, 3, 'hello']",
        "comment obtenir la longueur d'une liste": "Utilisez len().\nExemple :\nlongueur = len(ma_liste)",
        "comment ajouter un élément à une liste": "Utilisez append().\nExemple :\nma_liste.append(4)",
        "comment supprimer un élément d'une liste": "Utilisez remove() ou del.\nExemple :\nma_liste.remove(2)\ndel ma_liste[0]",
        "comment trier une liste": "Utilisez la méthode sort() ou la fonction sorted().\nExemple :\nma_liste.sort()\nou\ntriee = sorted(ma_liste)",
        "comment afficher tous les éléments d'une liste": "Utilisez une boucle for.\nExemple :\nfor x in ma_liste:\n    print(x)",
        "comment inverser une liste": "Utilisez reverse() ou [::-1].\nExemple :\nma_liste.reverse()\nou\ninverse = ma_liste[::-1]",
        "comment copier une liste": "Utilisez copy() ou list().\nExemple :\nnouvelle = ma_liste.copy()\nou\nnouvelle = list(ma_liste)",
        "comment faire une liste en compréhension": "Exemple :\ncarres = [x**2 for x in range(5)]\nprint(carres)  # [0, 1, 4, 9, 16]",
        "qu'est-ce qu'un dictionnaire": "Un dictionnaire associe des clés à des valeurs.\nExemple :\nmon_dict = {'a': 1, 'b': 2}",
        "comment faire une boucle sur un dictionnaire": "Utilisez for clé, valeur in mon_dict.items():\nExemple :\nfor cle, val in mon_dict.items():\n    print(f'{cle}: {val}')",
        "comment créer un tuple": "Utilisez des parenthèses.\nExemple :\nt = (1, 2, 3)",
        "comment décompresser un tuple": "Utilisez l'affectation multiple.\nExemple :\na, b = (1, 2)",
    },
    "Modules et Fichiers": {
        "comment importer un module": "Utilisez le mot-clé 'import'.\nExemple :\nimport math\n\nfrom math import sqrt",
        "comment lire un fichier": "Utilisez open().\nExemple :\nwith open('fichier.txt', 'r') as f:\n    contenu = f.read()\n    print(contenu)",
        "comment écrire dans un fichier": "Utilisez open() en mode 'w'.\nExemple :\nwith open('f.txt', 'w') as f:\n    f.write('texte')",
        "comment importer une fonction d'un autre fichier": "Utilisez from nom_fichier import nom_fonction\nExemple :\nfrom mon_module import ma_fonction",
        "comment installer un module": "Utilisez pip dans le terminal.\nExemple :\npip install nom_du_module",
        "comment installer plusieurs modules à la fois": "Utilisez pip install module1 module2\nExemple :\npip install requests flask",
    },
    "Utile": {
        "comment faire une pause dans un programme": "Utilisez time.sleep().\nExemple :\nimport time\ntime.sleep(2)",
        "comment générer un nombre aléatoire": "Utilisez random.randint().\nExemple :\nimport random\nnombre = random.randint(1, 10)",
        "comment afficher la version de Python": "Utilisez sys.version.\nExemple :\nimport sys\nprint(sys.version)",
        "comment afficher la documentation d'une fonction": "Utilisez help().\nExemple :\nhelp(print)",
        "comment arrêter un programme": "Utilisez exit() ou break dans une boucle.\nExemple :\nif condition:\n    exit()",
    },
    "À propos": {
        "de quoi tu parles": "Je parle principalement du langage Python et je peux répondre à des questions sur la programmation Python.",
        "qu'est-ce que tu nous apprends": "Je peux t'apprendre les bases de Python, donner des exemples de code et expliquer des concepts de programmation.",
        "à quoi tu sers": "Je sers à répondre à tes questions sur Python et à t'aider à apprendre à programmer.",
        "qui t'a créé": "J'ai été créé par pauledithz pour t'aider à apprendre Python.",
    }
}

# Créer un dictionnaire plat pour la compatibilité
faq = {}
for cat, questions in faq_categories.items():
    faq.update(questions)

def chatbot_response(message):
    message = message.lower().strip()
    
    # Commandes spéciales
    if message in ["help", "aide", "?"]:
        return "Tapez 'liste' pour voir toutes les questions disponibles.\nOu posez une question sur Python."
    elif message == "liste":
        result = "Voici les questions que je peux répondre :\n\n"
        for category, questions in faq_categories.items():
            result += f"\n📚 {category}:\n"
            for q in questions.keys():
                result += f"  • {q}\n"
        return result

    # Normaliser le message
    message_normalise = normaliser_texte(message)
    
    # 1. Recherche exacte normalisée
    for question, answer in faq.items():
        if normaliser_texte(question) == message_normalise:
            return f"✓ {answer}\n\n💡 Confiance: 100%"
    
    # 2. Fuzzy matching amélioré
    matches = get_close_matches(message_normalise, 
                               [normaliser_texte(q) for q in faq.keys()], 
                               n=3, cutoff=0.6)
    if matches:
        for original_q, norm_q in zip(faq.keys(), [normaliser_texte(q) for q in faq.keys()]):
            if norm_q == matches[0]:
                confiance = int(calcul_similarite(message_normalise, norm_q) * 100)
                return f"✓ {faq[original_q]}\n\n💡 Confiance: {confiance}%"
    
    # 3. Recherche par mots-clés avec calcul de similarité
    meilleures_correspondances = []
    for question, answer in faq.items():
        sim = calcul_similarite(message_normalise, normaliser_texte(question))
        if sim > 0.5:
            meilleures_correspondances.append((question, answer, int(sim * 100)))
    
    if meilleures_correspondances:
        meilleures_correspondances.sort(key=lambda x: x[2], reverse=True)
        best_q, best_answer, confiance = meilleures_correspondances[0]
        response = f"✓ {best_answer}\n\n💡 Confiance: {confiance}%"
        
        if confiance < 70 and len(meilleures_correspondances) > 1:
            response += f"\n\nℹ️ D'autres réponses possibles :\n"
            for q, _, conf in meilleures_correspondances[1:3]:
                response += f"  • {q} ({conf}%)\n"
        return response

    # Réponses conversationnelles
    if any(word in message for word in ["bonjour", "salut", "hello", "hi"]):
        return "👋 Bonjour ! Posez-moi une question sur Python."
    elif any(word in message for word in ["comment", "ça va", "tu vas bien"]):
        return "🤖 Je suis une IA, donc je vais toujours bien ! Comment puis-je vous aider avec Python ?"
    elif any(word in message for word in ["nom", "appelles", "qui es-tu"]):
        return "📖 Je suis ChatPy, un chatbot Python qui peut répondre à des questions sur le code."
    elif "merci" in message:
        return "😊 De rien ! N'hésitez pas si vous avez d'autres questions sur Python."
    else:
        return "❌ Désolé, je ne comprends pas votre question. Essayez de poser une question sur Python ou tapez 'help' pour l'aide."

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message', '')
    
    if not message:
        return jsonify({'error': 'Message vide'}), 400
    
    response = chatbot_response(message)
    return jsonify({'response': response})

@app.route('/api/questions', methods=['GET'])
def get_questions():
    """Retourne toutes les questions disponibles par catégorie"""
    return jsonify(faq_categories)

@app.route('/', methods=['GET'])
def index():
    return "ChatPy API est en ligne !"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
