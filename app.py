import os

from flask import Flask, jsonify, request, send_from_directory

from ia_en_python import bot

_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, static_folder=_DIR, static_url_path="")


@app.route("/")
def index():
    return send_from_directory(_DIR, "Index.html")


@app.route("/chat")
def chat_page():
    return send_from_directory(_DIR, "chat.html")


@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "Message vide."}), 400

    response = bot.traiter_message(message)
    return jsonify({"response": response})


if __name__ == "__main__":
    # Port 5000 est souvent occupé sur macOS par le service AirPlay Receiver.
    app.run(debug=True, port=5001)
