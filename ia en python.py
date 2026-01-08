import re
import os

def chatbot_response(message):
    message = message.lower().strip()
    faq = {
        "qu'est-ce qu'une fonction": "Une fonction en Python est un bloc de code réutilisable qui s'exécute lorsqu'on l'appelle avec son nom.\nExemple :\ndef ma_fonction():\n    print('Hello')",
        "comment faire une boucle": "En Python, vous pouvez utiliser 'for' ou 'while' pour faire des boucles.\nExemple avec for :\nfor i in range(5):\n    print(i)\n\nExemple avec while :\ni = 0\nwhile i < 5:\n    print(i)\n    i += 1",
        "comment déclarer une variable": "En Python, il suffit d'écrire le nom de la variable, un égal, puis la valeur.\nExemple :\nx = 5\nnom = 'Alice'",
        "comment afficher un message": "Utilisez la fonction print().\nExemple :\nprint('Bonjour !')\nprint(f'Hello {nom}')",
        "comment importer un module": "Utilisez le mot-clé 'import'.\nExemple :\nimport math\n\nfrom math import sqrt",
        "qu'est-ce qu'une liste": "Une liste est une structure de données qui peut contenir plusieurs éléments.\nExemple :\nma_liste = [1, 2, 3, 'hello']",
        "comment faire une condition": "Utilisez if, elif, else.\nExemple :\nif x > 0:\n    print('positif')\nelif x < 0:\n    print('négatif')\nelse:\n    print('zéro')",
        "qu'est-ce qu'un dictionnaire": "Un dictionnaire associe des clés à des valeurs.\nExemple :\nmon_dict = {'a': 1, 'b': 2}",
        "comment faire une fonction": "Utilisez le mot-clé def.\nExemple :\ndef ma_fonction():\n    print('Hello')\n\ndef addition(a, b):\n    return a + b",
        "comment lire un fichier": "Utilisez open().\nExemple :\nwith open('fichier.txt', 'r') as f:\n    contenu = f.read()\n    print(contenu)",
        "comment faire une boucle infinie": "Utilisez while True:.\nExemple :\nwhile True:\n    print('boucle infinie')\n    # N'oubliez pas de break pour sortir",
        "comment arrêter un programme": "Utilisez exit() ou break dans une boucle.\nExemple :\nif condition:\n    exit()",
        "qu'est-ce qu'une classe": "Une classe est un modèle pour créer des objets.\nExemple :\nclass MaClasse:\n    def __init__(self):\n        self.valeur = 0",
        "comment installer un module": "Utilisez pip dans le terminal.\nExemple :\npip install nom_du_module",
        "comment convertir une chaîne en entier": "Utilisez int().\nExemple :\nx = int('5')",
        "comment convertir un entier en chaîne": "Utilisez str().\nExemple :\ns = str(5)",
        "comment obtenir la longueur d'une liste": "Utilisez len().\nExemple :\nlongueur = len(ma_liste)",
        "comment trier une liste": "Utilisez la méthode sort() ou la fonction sorted().\nExemple :\nma_liste.sort()\nou\ntriee = sorted(ma_liste)",
        "comment ajouter un élément à une liste": "Utilisez append().\nExemple :\nma_liste.append(4)",
        "comment supprimer un élément d'une liste": "Utilisez remove() ou del.\nExemple :\nma_liste.remove(2)\ndel ma_liste[0]",
        "comment faire une boucle sur un dictionnaire": "Utilisez for clé, valeur in mon_dict.items():\nExemple :\nfor cle, val in mon_dict.items():\n    print(f'{cle}: {val}')",
        "comment vérifier si un élément est dans une liste": "Utilisez in.\nExemple :\nif 3 in ma_liste:\n    print('Présent')",
        "comment faire une exception": "Utilisez try/except.\nExemple :\ntry:\n    # code risqué\n    x = 1 / 0\nexcept ZeroDivisionError as e:\n    print(f'Erreur: {e}')",
        "comment définir une classe": "Utilisez class.\nExemple :\nclass MaClasse:\n    pass",
        "comment hériter d'une classe": "Indiquez la classe parente entre parenthèses.\nExemple :\nclass Fille(Mere):\n    pass",
        "comment documenter une fonction": "Utilisez une docstring.\nExemple :\ndef f():\n    '''Ceci est une docstring'''\n    pass",
        "comment afficher tous les éléments d'une liste": "Utilisez une boucle for.\nExemple :\nfor x in ma_liste:\n    print(x)",
        "comment faire une pause dans un programme": "Utilisez time.sleep().\nExemple :\nimport time\ntime.sleep(2)",
        "comment générer un nombre aléatoire": "Utilisez random.randint().\nExemple :\nimport random\nnombre = random.randint(1, 10)",
        "comment lire une entrée utilisateur": "Utilisez input().\nExemple :\nnom = input('Votre nom ? ')",
        "comment écrire dans un fichier": "Utilisez open() en mode 'w'.\nExemple :\nwith open('f.txt', 'w') as f:\n    f.write('texte')",
        "comment importer une fonction d'un autre fichier": "Utilisez from nom_fichier import nom_fonction\nExemple :\nfrom mon_module import ma_fonction",
        "comment afficher la version de Python": "Utilisez sys.version.\nExemple :\nimport sys\nprint(sys.version)",
        "comment installer plusieurs modules à la fois": "Utilisez pip install module1 module2\nExemple :\npip install requests flask",
        "comment afficher la documentation d'une fonction": "Utilisez help().\nExemple :\nhelp(print)",
        "comment créer un tuple": "Utilisez des parenthèses.\nExemple :\nt = (1, 2, 3)",
        "comment décompresser un tuple": "Utilisez l'affectation multiple.\nExemple :\na, b = (1, 2)",
        "comment faire une liste en compréhension": "Exemple :\ncarres = [x**2 for x in range(5)]\nprint(carres)  # [0, 1, 4, 9, 16]",
        "comment inverser une liste": "Utilisez reverse() ou [::-1].\nExemple :\nma_liste.reverse()\nou\ninverse = ma_liste[::-1]",
        "comment copier une liste": "Utilisez copy() ou list().\nExemple :\nnouvelle = ma_liste.copy()\nou\nnouvelle = list(ma_liste)",
        "de quoi tu parles": "Je parle principalement du langage Python et je peux répondre à des questions sur la programmation Python.",
        "qu'est-ce que tu nous apprends": "Je peux t'apprendre les bases de Python, donner des exemples de code et expliquer des concepts de programmation.",
        "à quoi tu sers": "Je sers à répondre à tes questions sur Python et à t'aider à apprendre à programmer.",
        "qui t'a créé": "J'ai été créé par un humain pour t'aider à apprendre Python."
    }

    # Commandes spéciales
    if message in ["help", "aide", "?"]:
        return "Tapez 'liste' pour voir toutes les questions disponibles.\nTapez 'au revoir' pour quitter.\nOu posez une question sur Python."
    elif message == "liste":
        questions = "\n".join(f"- {q}" for q in faq.keys())
        return f"Voici les questions que je peux répondre :\n{questions}"

    # Recherche flexible par mots-clés
    for question, answer in faq.items():
        mots_cles = question.split()
        if all(re.search(r'\b' + re.escape(mot) + r'\b', message) for mot in mots_cles if len(mot) > 3):
            return answer
        if question in message:
            return answer

    # Réponses conversationnelles
    if any(word in message for word in ["bonjour", "salut", "hello", "hi"]):
        return "Bonjour ! Posez-moi une question sur Python ou tapez 'help' pour l'aide."
    elif any(word in message for word in ["comment", "ça va", "tu vas"]):
        return "Je suis une IA, donc je vais toujours bien ! Comment puis-je vous aider avec Python ?"
    elif any(word in message for word in ["nom", "appelles", "es-tu"]):
        return "Je suis un chatbot Python qui peut répondre à des questions sur le code."
    elif "merci" in message:
        return "De rien ! N'hésitez pas si vous avez d'autres questions sur Python."
    elif any(word in message for word in ["au revoir", "bye", "quit", "exit"]):
        return "Au revoir !"
    else:
        return "Désolé, je ne comprends pas votre question. Essayez de poser une question sur Python ou tapez 'help' pour l'aide."

def print_colored(text, color, bold=False):
    colors = {
        "blue": "\033[94m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "red": "\033[91m",
        "end": "\033[0m"
    }
    if bold:
        color_code = "\033[1;" + colors.get(color, "").lstrip("\033[")  # Add bold
    else:
        color_code = colors.get(color, "")
    print(f"{color_code}{text}{colors['end']}")

if __name__ == "__main__":
    print_colored("Bienvenue sur Chatbot !", "blue", bold=True)
    print("Posez-moi une question sur Python (tapez 'au revoir' pour quitter).")
    print("Tapez 'help' pour l'aide ou 'liste' pour voir les questions disponibles.\n")

    while True:
        try:
            user_input = input("Vous: ").strip()
            if not user_input:
                continue
            response = chatbot_response(user_input)
            os.system('cls' if os.name == 'nt' else 'clear')  # Clear screen
            print_colored("Bienvenue sur Chatbot !", "blue", bold=True)
            print("Posez-moi une question sur Python (tapez 'au revoir' pour quitter).")
            print("Tapez 'help' pour l'aide ou 'liste' pour voir les questions disponibles.\n")
            print(f"Vous: {user_input}")
            print_colored("Bot:", "green")
            print(response)
            print()  # Ligne vide pour séparer
            if any(word in user_input.lower() for word in ["au revoir", "bye", "quit", "exit"]):
                break
        except KeyboardInterrupt:
            print("\nAu revoir !")
            break
        except EOFError:
            break