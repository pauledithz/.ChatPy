import os

from flask import Flask, abort, jsonify, request, send_from_directory

from ia_en_python import bot

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

    response = bot.traiter_message(message)
    return jsonify({"response": response})


if __name__ == "__main__":
    # Le debugger Werkzeug permet l'exécution de code arbitraire : il ne doit
    # s'activer qu'à la demande explicite, jamais par défaut.
    debug = os.environ.get("CHATPY_DEBUG") == "1"
    # Port 5000 est souvent occupé sur macOS par le service AirPlay Receiver.
    app.run(debug=debug, port=5001)
