import re
import os
import json
import random
import unicodedata
from difflib import get_close_matches, SequenceMatcher

HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".chatpy_history.json")

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

faq_categories = {
    "Bases": {
        "qu'est-ce qu'une variable": "Une variable, c'est un espace de stockage nommé dans lequel on garde une valeur pour pouvoir la réutiliser plus tard dans un programme.",
        "comment déclarer une variable": "En Python, il suffit d'écrire le nom de la variable, un égal, puis la valeur.\nExemple :\nx = 5\nnom = 'Alice'",
        "comment afficher un message": "Utilisez la fonction print().\nExemple :\nprint('Bonjour !')\nprint(f'Hello {nom}')",
        "comment lire une entrée utilisateur": "Utilisez input().\nExemple :\nnom = input('Votre nom ? ')",
        "comment convertir une chaîne en entier": "Utilisez int().\nExemple :\nx = int('5')",
        "comment convertir un entier en chaîne": "Utilisez str().\nExemple :\ns = str(5)",
    },
    "Fonctions": {
        "qu'est-ce qu'une fonction": "Une fonction en Python est un bloc de code réutilisable qui s'exécute lorsqu'on l'appelle avec son nom.\nExemple :\ndef ma_fonction():\n    print('Hello')",
        "À quoi sert une fonction": "Une fonction sert à regrouper un bloc de code qui peut être réutilisé plusieurs fois dans le programme.\nExemple :\ndef ma_fonction():\n    print('Hello')\n\ndef addition(a, b):\n    return a + b",
        "comment faire une fonction": "Utilisez le mot-clé def.\nExemple :\ndef ma_fonction():\n    print('Hello')\n\ndef addition(a, b):\n    return a + b",
        "comment documenter une fonction": "Utilisez une docstring.\nExemple :\ndef f():\n    '''Ceci est une docstring'''\n    pass",
    },
    "Conditions et Boucles": {
        "À quoi sert une condition": "Une condition sert à vérifier si une certaine condition est vraie ou fausse.\nExemple :\nif x > 0:\n    print('positif')\nelif x < 0:\n    print('négatif')\nelse:\n    print('zéro')",
        "comment faire une condition": "Utilisez if, elif, else.\nExemple :\nif x > 0:\n    print('positif')\nelif x < 0:\n    print('négatif')\nelse:\n    print('zéro')",
        "À quoi sert une boucle": "Une boucle sert à répéter un bloc de code un certain nombre de fois ou jusqu'à ce qu'une certaine condition soit vraie.\nExemple :\nfor i in range(5):\n    print(i)\n\ni = 0\nwhile i < 5:\n    print(i)\n    i += 1",
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
        "de quoi tu parles": "Je parle principalement du langage Python et je peux répondre à des questions sur la programmation Python et sur le travail informatique !",
        "qu'est-ce que tu nous apprends": "Je peux t'apprendre les bases de Python, donner des exemples de code et expliquer des concepts de programmation sur le monde informatique.",
        "à quoi tu sers": "Je sers à répondre à tes questions sur Python et à t'aider à apprendre à programmer ainsi que de comprendre le monde informatique.",
        "qui t'a créé": "J'ai été créé par Zoungrana paul-emmanuel pour t'aider à apprendre Python.",
        "comment devenir un expert en Python": "Pour devenir un expert en Python, il faut apprendre les bases, comprendre les concepts de programmation, et pratiquer régulièrement. Il faut aussi suivre des cours, des tutoriels, et des livres. Et enfin, il faut se mettre à jour avec les nouvelles versions de Python et les nouvelles fonctionnalités.",
        "ques-ce-que je peux faire avec Python": "Python est un langage de programmation polyvalent qui peut être utilisé pour de nombreux projets. Voici quelques exemples : \n- Développement web (Django, Flask)\n- Data science (pandas, numpy, matplotlib)\n- Machine learning (scikit-learn, TensorFlow, PyTorch)\n- IA (OpenAI, GPT-3, GPT-4)\n- Automatisation (Selenium, Scrapy)\n- Systèmes d'exploitation (Linux, Windows, MacOS)\n- Base de données (SQLite, MySQL, PostgreSQL)\n- Interface graphique (Tkinter, PyQt, PySide)\n- Réseau (socket, threading, multiprocessing)\n- Sécurité (cryptographie, cybersécurité)\n- Simulation (Pygame, Pysimple2D)",
        "Comment créer une intelligence artificiel": "Concrètement, créer une IA suit en général trois étapes : on rassemble des données (images, textes, chiffres…), on choisit un modèle (souvent un réseau de neurones), puis on l'entraîne en lui faisant comparer ses réponses aux bonnes réponses. À chaque erreur, le modèle se corrige légèrement, et après des milliers de répétitions, il devient capable de généraliser à des cas qu'il n'a jamais vus. Aujourd'hui, on part rarement de zéro : on utilise des modèles déjà entraînés (comme ceux derrière les chatbots) qu'on adapte à un besoin précis. C'est ça, l'essentiel du métier : combiner des données, des modèles et du code pour résoudre un problème concret.",
    },
    "Job et apprentissage python": {
        "comment devenir un développeur Python": "Pour devenir un développeur Python, il faut apprendre les bases, comprendre les concepts de programmation, et pratiquer régulièrement. Il faut aussi suivre des cours, des tutoriels, et des livres. Et enfin, il faut se mettre à jour avec les nouvelles versions de Python et les nouvelles fonctionnalités.",
        "comment trouver un job en Python": "Pour trouver un job en Python, il faut avoir une bonne expérience en programmation, avoir des compétences en Python, et avoir des compétences en mathématiques. Il faut aussi avoir des compétences en ingénierie logicielle, et avoir des compétences dans d'autres langages.",
        "comment devenir ai engineer": "Pour devenir AI engineer, tu dois maîtriser les fondamentaux en programmation (Python surtout), les mathématiques (algèbre linéaire, statistiques, calcul) et les frameworks de machine learning comme TensorFlow ou PyTorch.",
    }
}

faq = {}
for _cat, _questions in faq_categories.items():
    faq.update(_questions)

norm_vers_original = {normaliser_texte(q): q for q in faq}


def chatbot_response(message):
    message = message.lower().strip()

    # Commandes spéciales
    if message in ["help", "aide", "?"]:
        return ("Commandes disponibles :\n"
                "  liste              — toutes les questions par catégorie\n"
                "  liste <catégorie>  — questions d'une seule catégorie (ex: liste fonctions)\n"
                "  cherche <mot>      — questions contenant un mot-clé (ex: cherche liste)\n"
                "  quiz               — tester vos connaissances Python\n"
                "  historique         — relire la conversation\n"
                "  au revoir          — quitter\n\n"
                "Ou posez directement une question sur Python.")

    # liste <catégorie> — afficher uniquement une catégorie
    if message.startswith("liste "):
        nom_cat = message[6:].strip()
        nom_cat_norm = normaliser_texte(nom_cat)

        # Correspondance par inclusion (ex: "fonctions" → "Fonctions")
        cats_trouvees = [c for c in faq_categories if nom_cat_norm in normaliser_texte(c)]

        # Fallback : fuzzy matching sur les noms de catégories
        if not cats_trouvees:
            noms_norm = {normaliser_texte(c): c for c in faq_categories}
            matches = get_close_matches(nom_cat_norm, noms_norm.keys(), n=2, cutoff=0.4)
            cats_trouvees = [noms_norm[m] for m in matches]

        if cats_trouvees:
            result = ""
            for cat in cats_trouvees:
                result += f"📚 {cat}:\n"
                for q in faq_categories[cat]:
                    result += f"  • {q}\n"
                result += "\n"
            return result.strip()
        else:
            dispo = ", ".join(faq_categories.keys())
            return f"❌ Catégorie '{nom_cat}' introuvable.\nCatégories disponibles : {dispo}"

    # cherche <mot> — rechercher un mot-clé dans toutes les questions
    if message.startswith("cherche "):
        mot_cle = message[8:].strip()
        mot_cle_norm = normaliser_texte(mot_cle)

        resultats = []
        for cat, questions in faq_categories.items():
            for q in questions:
                if mot_cle_norm in normaliser_texte(q):
                    resultats.append((cat, q))

        if resultats:
            result = f"🔍 Questions contenant '{mot_cle}' :\n"
            cat_actuelle = None
            for cat, q in resultats:
                if cat != cat_actuelle:
                    result += f"\n📚 {cat}:\n"
                    cat_actuelle = cat
                result += f"  • {q}\n"
            return result
        else:
            return f"❌ Aucune question ne contient '{mot_cle}'.\nEssayez un mot plus général ou tapez 'liste' pour tout voir."

    if message == "liste":
        result = "Voici les questions que je peux répondre :\n\n"
        for category, questions in faq_categories.items():
            result += f"\n📚 {category}:\n"
            for q in questions.keys():
                result += f"  • {q}\n"
        return result

    message_normalise = normaliser_texte(message)

    # 1. Recherche exacte normalisée
    if message_normalise in norm_vers_original:
        original_q = norm_vers_original[message_normalise]
        return f"✓ {faq[original_q]}\n\n💡 Confiance: 100%"

    # 2. Fuzzy matching — CORRECTIF 2 : lookup direct via norm_vers_original
    matches = get_close_matches(message_normalise, norm_vers_original.keys(), n=3, cutoff=0.6)
    if matches:
        original_q = norm_vers_original[matches[0]]
        confiance = int(calcul_similarite(message_normalise, matches[0]) * 100)
        return f"✓ {faq[original_q]}\n\n💡 Confiance: {confiance}%"

    # 3. Recherche par similarité
    meilleures_correspondances = []
    for norm_q, original_q in norm_vers_original.items():
        sim = calcul_similarite(message_normalise, norm_q)
        if sim > 0.5:
            meilleures_correspondances.append((original_q, faq[original_q], int(sim * 100)))

    if meilleures_correspondances:
        meilleures_correspondances.sort(key=lambda x: x[2], reverse=True)
        _, best_answer, confiance = meilleures_correspondances[0]
        response = f"✓ {best_answer}\n\n💡 Confiance: {confiance}%"
        if confiance < 70 and len(meilleures_correspondances) > 1:
            response += f"\n\nℹ️ D'autres réponses possibles :\n"
            for q, _, conf in meilleures_correspondances[1:3]:
                response += f"  • {q} ({conf}%)\n"
        return response

    # Réponses conversationnelles
    if any(word in message for word in ["bonjour", "salut", "hello", "hi"]):
        return "👋 Bonjour ! Posez-moi une question sur Python ou tapez 'help' pour l'aide."
    elif any(word in message for word in ["ça va", "tu vas bien"]):
        return "🤖 Je suis une Intelligence Artificielle, donc je vais toujours bien ! Comment puis-je vous aider avec Python aujourd'hui ?"
    elif any(word in message for word in ["nom", "appelles", "qui es-tu"]):
        return "📖 Je suis un chatbot Python qui peut répondre à des questions sur le code."
    elif "merci" in message:
        return "😊 De rien ! N'hésitez pas si vous avez d'autres questions sur Python."
    elif any(word in message for word in ["au revoir", "bye", "quit", "exit"]):
        return "👋 Au revoir ! Continue à apprendre Python le plus possible !"
    else:
        return "❌ Désolé, je ne comprends pas votre question. Essayez de poser une question sur Python ou tapez 'help' pour l'aide."


def print_colored(text, color, bold=False):
    codes = {
        "blue":   ("\033[94m",   "\033[1;94m"),
        "green":  ("\033[92m",   "\033[1;92m"),
        "yellow": ("\033[93m",   "\033[1;93m"),
        "red":    ("\033[91m",   "\033[1;91m"),
    }
    normal, gras = codes.get(color, ("\033[0m", "\033[1m"))
    code = gras if bold else normal
    print(f"{code}{text}\033[0m")


def mode_quiz():
    """Lance une session de quiz interactif sur les questions de la FAQ."""
    questions = list(faq.items())
    score = 0
    total = 0

    print_colored("\n🎯 Mode Quiz — répondez de mémoire, tapez 'fin' pour arrêter.\n", "yellow", bold=True)

    while True:
        question, bonne_reponse = random.choice(questions)
        print_colored(f"❓ {question} ?", "blue")

        try:
            reponse = input("📝 Votre réponse : ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if reponse.lower() in ("fin", "exit", "quit"):
            break

        sim = int(calcul_similarite(normaliser_texte(reponse), normaliser_texte(bonne_reponse)) * 100)
        total += 1

        if sim >= 70:
            score += 1
            print_colored(f"✅ Bonne réponse ! (similarité : {sim}%)", "green")
        elif sim >= 35:
            print_colored(f"⚠️  Presque ! (similarité : {sim}%)", "yellow")
        else:
            print_colored(f"❌ Pas tout à fait. (similarité : {sim}%)", "red")

        print(f"💡 Réponse attendue :\n{bonne_reponse}\n")

    if total > 0:
        print_colored(f"\n📊 Score final : {score}/{total} ({int(score/total*100)}%)\n", "blue", bold=True)
    else:
        print("Aucune question répondue.\n")


class ChatBot:
    """Classe pour gérer le chatbot avec mémoire de conversation"""
    def __init__(self):
        self.historique = []
        self.dernieres_categories = []
        self.questions_posees = set()
        self._charger_historique()
        self.relations = {
            "qu'est-ce qu'une fonction": ["comment faire une fonction", "comment documenter une fonction"],
            "comment faire une fonction": ["comment faire une exception", "comment documenter une fonction"],
            "qu'est-ce qu'une liste": ["comment ajouter un élément à une liste", "comment trier une liste"],
            "comment faire une boucle": ["comment faire une condition", "comment arrêter un programme"],
            "comment déclarer une variable": ["comment afficher un message", "comment convertir une chaîne en entier"],
        }

    def _charger_historique(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                    self.historique = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.historique = []

    def _sauvegarder_historique(self):
        try:
            with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.historique, f, ensure_ascii=False, indent=2)
        except IOError:
            pass

    def ajouter_message(self, role, message):
        self.historique.append({"role": role, "message": message})

    def obtenir_contexte(self):
        if len(self.historique) >= 2:
            return self.historique[-2:]
        return []

    def obtenir_suggestions(self, question):
        question_norm = normaliser_texte(question)
        suggestions = []
        for q_source, q_liees in self.relations.items():
            if normaliser_texte(q_source) in question_norm or question_norm in normaliser_texte(q_source):
                suggestions = q_liees
                break
        suggestions = [s for s in suggestions if s not in self.questions_posees]
        return suggestions[:2]

    def traiter_message(self, message):
        self.ajouter_message("utilisateur", message)
        response = chatbot_response(message)
        suggestions = self.obtenir_suggestions(message)
        if suggestions and "Confiance:" in response:
            response += f"\n\n📌 Questions liées:\n"
            for i, sug in enumerate(suggestions, 1):
                response += f"  {i}. {sug}\n"
        self.ajouter_message("assistant", response)
        self.questions_posees.add(normaliser_texte(message))
        self._sauvegarder_historique()
        return response

    def afficher_historique(self):
        print("\n📜 Historique:\n")
        for msg in self.historique:
            if msg["role"] == "utilisateur":
                print_colored(f"Vous: {msg['message']}", "blue")
            else:
                print(f"IA: {msg['message']}\n")


bot = ChatBot()

if __name__ == "__main__":
    print_colored("☕️ Bienvenue sur ChatPy!", "blue", bold=True)
    print("Posez-moi une question sur Python ou sur le travail informatique. (tapez 'au revoir' pour quitter).")
    print("Tapez 'help' pour l'aide | 'liste' pour les questions | 'cherche <mot>' pour filtrer | 'quiz' pour vous tester | 'historique' pour la conversation.\n")

    while True:
        try:
            user_input = input("📝 Vous: ").strip()
            if not user_input:
                continue

            if user_input.lower() == "historique":
                bot.afficher_historique()
                continue

            if user_input.lower() == "quiz":
                mode_quiz()
                continue

            response = bot.traiter_message(user_input)
            print_colored("\n✨ Bot:", "blue")
            print(response)
            print()

            if any(word in user_input.lower() for word in ["au revoir", "bye", "quit", "exit"]):
                print_colored("À bientôt ! Continue à apprendre Python tout les jours ! 🚀", "blue", bold=True)
                break
        except KeyboardInterrupt:
            print("\n\nAu revoir !")
            break
        except EOFError:
            break
