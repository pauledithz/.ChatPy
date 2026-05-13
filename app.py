import os
import secrets
import json
import base64
from urllib.parse import urlencode
import requests
from flask import Flask, session, redirect, request, jsonify, send_from_directory

app = Flask(__name__, static_folder='.', static_url_path='')
app.secret_key = os.environ.get('FLASK_SECRET', 'devsecret')

CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
REDIRECT_URI = os.environ.get('REDIRECT_URI', 'http://localhost:5000/oauth2callback')

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

@app.route('/')
def index():
    # Serve the landing page
    return send_from_directory('.', 'Index.html')

@app.route('/<path:filename>')
def static_files(filename):
    # Serve static assets (style.css, script.js, images)
    return send_from_directory('.', filename)

@app.route('/auth/google')
def auth_google():
    if not CLIENT_ID:
        return "Google OAuth not configured on server. Set GOOGLE_CLIENT_ID env var.", 500
    state = secrets.token_urlsafe(16)
    session['oauth_state'] = state
    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'scope': 'openid email profile',
        'redirect_uri': REDIRECT_URI,
        'state': state,
        'prompt': 'select_account'
    }
    url = GOOGLE_AUTH_URL + '?' + urlencode(params)
    return redirect(url)

@app.route('/oauth2callback')
def oauth2callback_page():
    # Serve a small page that will exchange the code server-side and postMessage to the opener
    return send_from_directory('.', 'oauth2callback.html')

@app.route('/auth/google/exchange', methods=['POST'])
def exchange_code():
    body = request.get_json() or {}
    code = body.get('code')
    state = body.get('state')
    if not code or state != session.get('oauth_state'):
        return jsonify({'ok': False, 'error': 'invalid_state_or_code'}), 400

    data = {
        'code': code,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'redirect_uri': REDIRECT_URI,
        'grant_type': 'authorization_code'
    }
    token_resp = requests.post(GOOGLE_TOKEN_URL, data=data)
    if token_resp.status_code != 200:
        return jsonify({'ok': False, 'error': 'token_exchange_failed', 'detail': token_resp.text}), 400
    tokens = token_resp.json()
    id_token = tokens.get('id_token')

    userinfo = {}
    if id_token:
        # WARNING: This decodes the JWT payload without verifying signature.
        # In production, verify the id_token using google.oauth2.id_token.verify_oauth2_token
        try:
            parts = id_token.split('.')
            if len(parts) >= 2:
                payload = parts[1]
                # Add padding
                padded = payload + '=' * (-len(payload) % 4)
                decoded = base64.urlsafe_b64decode(padded)
                userinfo = json.loads(decoded.decode('utf-8'))
        except Exception:
            userinfo = {}

    session['user'] = {'email': userinfo.get('email'), 'name': userinfo.get('name'), 'sub': userinfo.get('sub')}
    return jsonify({'ok': True, 'user': session['user']})

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    # dev server
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
