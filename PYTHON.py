print('hello world')

def chatbot_response(message):
    message = message.lower()
    faq = {
        "qu'est-ce qu'une fonction": "Une fonction en Python est un bloc de code réutilisable.",
        "comment faire une boucle": "En Python, vous pouvez utiliser 'for' ou 'while' pour faire des boucles. Exemple : for i in range(5): print(i)",
        "comment déclarer une variable": "En Python, il suffit d'écrire le nom de la variable, un égal, puis la valeur. Exemple : x = 5"
    }
    for question, answer in faq.items():
        if question in message:
            return answer
    return "Je ne comprends pas la question."

if __name__ == "__main__":
    print("Pose-moi une question sur le code Python (tape 'stop' pour quitter).")
    while True:
        user_input = input("Vous: ")
        if user_input.lower() == "stop":
            print("Au revoir !")
            break
        response = chatbot_response(user_input)
        print("Bot:", response)