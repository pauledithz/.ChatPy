import os
from flask import Flask, request, jsonify

try:
    import openai
except Exception:
    openai = None

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
app = Flask(__name__, static_folder=BASE, static_url_path='')


@app.route('/api/chat', methods=['POST'])
def api_chat():
    data = request.get_json(force=True)
    message = (data or {}).get('message', '')
    if not message:
        return jsonify({'error': 'Pas de message fourni'}), 400

    api_key = os.getenv('OPENAI_API_KEY')
    if api_key and openai:
        try:
            openai.api_key = api_key
            resp = openai.ChatCompletion.create(
                model='gpt-3.5-turbo',
                messages=[{'role': 'user', 'content': message}],
                max_tokens=500,
            )
            reply = resp.choices[0].message.content.strip()
            return jsonify({'reply': reply})
        except Exception as e:
            return jsonify({'error': 'Erreur OpenAI: ' + str(e)}), 500

    # fallback: réponse simulée si pas de clé
    reply = f"(Mode démo) Je reçois : {message}"
    return jsonify({'reply': reply})


if __name__ == '__main__':
    # Serve static files from project root. Open http://127.0.0.1:5000/invite.html
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
