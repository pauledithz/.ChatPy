def chatbot_response(message):
    message = message.lower()
    faq = {
        "qu'est-ce qu'une fonction": "Une fonction en Python est un bloc de code réutilisable qui s'exécute lorsqu'on l'appelle avec son nom.",
        "comment faire une boucle": "En Python, vous pouvez utiliser 'for' ou 'while' pour faire des boucles. Exemple : for i in range(5): print(i)",
        "comment déclarer une variable": "En Python, il suffit d'écrire le nom de la variable, un égal, puis la valeur. Exemple : x = 5",
        "comment afficher un message": "Utilisez la fonction print(). Exemple : print('Bonjour !')",
        "comment importer un module": "Utilisez le mot-clé 'import'. Exemple : import math",
        "qu'est-ce qu'une liste": "Une liste est une structure de données qui peut contenir plusieurs éléments. Exemple : ma_liste = [1, 2, 3]",
        "comment faire une condition": "Utilisez if, elif, else. Exemple : if x > 0: print('positif')",
        "qu'est-ce qu'un dictionnaire": "Un dictionnaire associe des clés à des valeurs. Exemple : mon_dict = {'a': 1, 'b': 2}",
        "comment faire une fonction": "Utilisez le mot-clé def. Exemple : def ma_fonction(): print('Hello')",
        "comment lire un fichier": "Utilisez open(). Exemple : with open('fichier.txt', 'r') as f: contenu = f.read()",
        "comment faire une boucle infinie": "Utilisez while True:. Exemple : while True: print('boucle infinie')",
        "comment arrêter un programme": "Utilisez exit() ou break dans une boucle.",
        "qu'est-ce qu'une classe": "Une classe est un modèle pour créer des objets. Exemple : class MaClasse: pass",
        "comment installer un module": "Utilisez pip dans le terminal. Exemple : pip install nom_du_module",
        "comment convertir une chaîne en entier": "Utilisez int(). Exemple : x = int('5')",
        "comment convertir un entier en chaîne": "Utilisez str(). Exemple : s = str(5)",
        "comment obtenir la longueur d'une liste": "Utilisez len(). Exemple : len(ma_liste)",
        "comment trier une liste": "Utilisez la méthode sort() ou la fonction sorted(). Exemple : ma_liste.sort()",
        "comment ajouter un élément à une liste": "Utilisez append(). Exemple : ma_liste.append(4)",
        "comment supprimer un élément d'une liste": "Utilisez remove() ou del. Exemple : ma_liste.remove(2)",
        "comment faire une boucle sur un dictionnaire": "Utilisez for clé, valeur in mon_dict.items():",
        "comment vérifier si un élément est dans une liste": "Utilisez in. Exemple : if 3 in ma_liste:",
        "comment faire une exception": "Utilisez try/except. Exemple : try: ... except Exception as e: ...",
        "comment définir une classe": "Utilisez class. Exemple : class MaClasse: pass",
        "comment hériter d'une classe": "Indiquez la classe parente entre parenthèses. Exemple : class Fille(Mere): pass",
        "comment documenter une fonction": "Utilisez une docstring. Exemple : def f(): '''Ceci est une docstring'''",
        "comment afficher tous les éléments d'une liste": "Utilisez une boucle for. Exemple : for x in ma_liste: print(x)",
        "comment faire une pause dans un programme": "Utilisez time.sleep(). Exemple : import time; time.sleep(2)",
        "comment générer un nombre aléatoire": "Utilisez random.randint(). Exemple : import random; random.randint(1, 10)",
        "comment lire une entrée utilisateur": "Utilisez input(). Exemple : nom = input('Votre nom ? ')",
        "comment écrire dans un fichier": "Utilisez open() en mode 'w'. Exemple : with open('f.txt', 'w') as f: f.write('texte')",
        "comment importer une fonction d'un autre fichier": "Utilisez from nom_fichier import nom_fonction",
        "comment afficher la version de Python": "Utilisez sys.version. Exemple : import sys; print(sys.version)",
        "comment installer plusieurs modules à la fois": "Utilisez pip install module1 module2",
        "comment afficher la documentation d'une fonction": "Utilisez help(). Exemple : help(print)",
        "comment créer un tuple": "Utilisez des parenthèses. Exemple : t = (1, 2, 3)",
        "comment décompresser un tuple": "Utilisez l'affectation multiple. Exemple : a, b = (1, 2)",
        "comment faire une liste en compréhension": "Exemple : [x*2 for x in range(5)]",
        "comment inverser une liste": "Utilisez reverse() ou [::-1]. Exemple : ma_liste[::-1]",
        "comment copier une liste": "Utilisez copy() ou list(). Exemple : nouvelle = ma_liste.copy()",
        "de quoi tu parles": "Je parle principalement du langage Python et je peux répondre à des questions sur la programmation Python.",
        "qu'est-ce que tu nous apprends": "Je peux t'apprendre les bases de Python, donner des exemples de code et expliquer des concepts de programmation.",
        "à quoi tu sers": "Je sers à répondre à tes questions sur Python et à t'aider à apprendre à programmer.",
        "qui t'a créé": "J'ai été créé par un humain pour t'aider à apprendre Python."
    }
    # Recherche flexible par mots-clés
    for question, answer in faq.items():
        mots_cles = question.split()
        if all(mot in message for mot in mots_cles if len(mot) > 3):
            return answer
        if question in message:
            return answer
    if "bonjour" in message:
        return "Bonjour ! Posez-moi une question sur le code Python."
    elif "comment ça va" in message:
        return "Je suis une IA, donc je vais toujours bien !"
    elif "ton nom" in message:
        return "Je suis un chatbot Python qui peut répondre à des questions sur le code."
    elif "au revoir" in message:
        return "Au revoir !"
    else:
        return "Désolé, je ne comprends pas votre question. Essayez de poser une question sur le code Python."

if __name__ == "__main__":
    print("Bienvenue ! Posez-moi une question sur le code Python (tapez 'au revoir' pour quitter).")
    while True:
        user_input = input("Vous: ")
        response = chatbot_response(user_input)
        print("Bot:", response)
        if "au revoir" in user_input.lower():
            break