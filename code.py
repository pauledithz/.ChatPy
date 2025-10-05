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
        "qu'est-ce qu'un dictionnaire": "Un dictionnaire est une structure de données qui associe des clés à des valeurs. Exemple : mon_dict = {'a': 1, 'b': 2}",
        "comment faire une fonction": "Utilisez le mot-clé def. Exemple : def ma_fonction(): print('Hello')",
        "comment lire un fichier": "Utilisez open(). Exemple : with open('fichier.txt', 'r') as f: contenu = f.read()",
        "comment faire une boucle infinie": "Utilisez while True:. Exemple : while True: print('boucle infinie')",
        "comment arrêter un programme": "Utilisez exit() ou break dans une boucle.",
        "qu'est-ce qu'une classe": "Une classe est un modèle pour créer des objets. Exemple : class MaClasse: pass",
        "comment installer un module": "Utilisez pip dans le terminal. Exemple : pip install nom_du_module"
    }
    for question, answer in faq.items():
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