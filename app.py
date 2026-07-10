import os
import secrets

from flask import Flask, abort, jsonify, request, send_from_directory, session

from ia_en_python import bot, demarrer_quiz, repondre_quiz

_DIR = os.path.dirname(os.path.abspath(__file__))

# Liste blanche des fichiers servis au public. Tout le reste du dossier
# (code source, .chatpy_history.json, questions_sans_reponse.json, .env)
# doit rester inaccessible depuis le web.
FICHIERS_PUBLICS = frozenset({
    "style.css",
    "script.js",
    "chat.js",
    "ChatPY_logo.PNG",
    "perso.JPG",
    "Persone professionelle.jpg",
})

app = Flask(__name__, static_folder=None)

# Signe le cookie de session, qui porte l'état du quiz. Sans clé fixe, chaque
# redémarrage du serveur invalide les quiz en cours — acceptable en local,
# à définir en production.
app.secret_key = os.environ.get("CHATPY_SECRET_KEY") or secrets.token_hex(32)


@app.route("/")
def index():
    return send_from_directory(_DIR, "Index.html")


@app.route("/chat")
def chat_page():
    return send_from_directory(_DIR, "chat.html")


@app.route("/<path:nom>")
def fichier_public(nom):
    if nom not in FICHIERS_PUBLICS:
        abort(404)
    return send_from_directory(_DIR, nom)


@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Corps de requête JSON invalide."}), 400

    message = data.get("message")
    if not isinstance(message, str):
        return jsonify({"error": "Le champ 'message' doit être une chaîne de caractères."}), 400

    message = message.strip()
    if not message:
        return jsonify({"error": "Message vide."}), 400

    # Un quiz en cours capte tous les messages : ils sont des réponses, pas des
    # questions. On les tient hors de l'historique et du journal des lacunes.
    etat_quiz = session.get("quiz")
    if etat_quiz is not None:
        etat_quiz, response = repondre_quiz(etat_quiz, message)
    elif message.lower() == "quiz":
        etat_quiz, response = demarrer_quiz()
    else:
        return jsonify({"response": bot.traiter_message(message)})

    if etat_quiz is None:
        session.pop("quiz", None)
    else:
        session["quiz"] = etat_quiz
    return jsonify({"response": response})


if __name__ == "__main__":
    # Le debugger Werkzeug permet l'exécution de code arbitraire : il ne doit
    # s'activer qu'à la demande explicite, jamais par défaut.
    debug = os.environ.get("CHATPY_DEBUG") == "1"
    # Port 5000 est souvent occupé sur macOS par le service AirPlay Receiver.
    app.run(debug=debug, port=5001)
