import os
import secrets
import requests
from authlib.integrations.flask_client import OAuth
from authlib.integrations.base_client import OAuthError
from dotenv import load_dotenv
from flask import (Flask, abort, jsonify, redirect, request, send_from_directory,
                   session, url_for)

from ia_en_python import bot, demarrer_quiz, repondre_quiz, signaler_reponse_inutile

_DIR = os.path.dirname(os.path.abspath(__file__))

# Charge .env dans l'environnement. Les variables déjà définies dans le shell
# gagnent, pour qu'un déploiement puisse imposer ses propres valeurs sans
# qu'un .env oublié sur le serveur ne les écrase.
load_dotenv(os.path.join(_DIR, ".env"))

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

# Signe le cookie de session, qui porte l'état du quiz et l'utilisateur connecté.
# Sans clé fixe, chaque redémarrage du serveur invalide les quiz en cours et
# déconnecte tout le monde — acceptable en local, à définir en production.
CHATPY_SECRET_KEY = os.environ.get("CHATPY_SECRET_KEY", "").strip()
app.secret_key = CHATPY_SECRET_KEY or secrets.token_hex(32)

app.config.update(
    # Le cookie porte une identité : le JavaScript n'a aucune raison d'y toucher.
    SESSION_COOKIE_HTTPONLY=True,
    # "Lax" est le seul réglage qui marche ici : "Strict" ferait perdre le cookie
    # au retour de redirection depuis Google, et le flow échouerait sur un
    # mismatching_state.
    SESSION_COOKIE_SAMESITE="Lax",
    # En https uniquement : à 1 en local (http), le navigateur refuserait le
    # cookie et la connexion ne tiendrait jamais.
    SESSION_COOKIE_SECURE=os.environ.get("CHATPY_COOKIE_SECURE") == "1",
)

# ── OAuth Google et GitHub ───────────────────────────────────────────────────
# Flow "authorization code" côté serveur : le client_secret ne quitte jamais le
# serveur, contrairement aux flows qui se déroulent dans le navigateur.
# Les identifiants viennent de .env ; tant qu'ils sont vides, les routes /auth
# du fournisseur concerné répondent 503 au lieu de planter au démarrage — on
# peut donc développer le reste du site sans compte Google Cloud ni OAuth App
# GitHub, et n'en configurer qu'un des deux.
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "").strip()
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "").strip()
GITHUB_CLIENT_ID = os.environ.get("GITHUB_CLIENT_ID", "").strip()
GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET", "").strip()
GOOGLE_CONFIGURE = bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)
GITHUB_CONFIGURE = bool(GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET)
OAUTH_CONFIGURE = GOOGLE_CONFIGURE or GITHUB_CONFIGURE
if OAUTH_CONFIGURE and not CHATPY_SECRET_KEY:
    raise RuntimeError(
        "CHATPY_SECRET_KEY est obligatoire lorsque OAuth est configuré."
    )
oauth = OAuth(app)
if GOOGLE_CONFIGURE:
    oauth.register(
        name="google",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        # Le document de découverte fournit les URLs d'autorisation, de token et
        # les clés de signature : rien à coder en dur, et rien à corriger le jour
        # où Google les change.
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        # Strictement le minimum. Tout scope supplémentaire déclenche une
        # procédure de vérification Google longue et pénible.
        client_kwargs={"scope": "openid email profile"},
    )
if GITHUB_CONFIGURE:
    oauth.register(
        name="github",
        client_id=GITHUB_CLIENT_ID,
        client_secret=GITHUB_CLIENT_SECRET,
        # GitHub ne fait pas d'OpenID Connect et ne publie donc aucun document
        # de découverte : les trois URLs sont écrites en dur, contrairement à
        # Google. Il n'y a pas non plus d'id_token — l'identité se lit ensuite
        # sur l'API REST, d'où api_base_url.
        authorize_url="https://github.com/login/oauth/authorize",
        access_token_url="https://github.com/login/oauth/access_token",
        api_base_url="https://api.github.com/",
        # read:user pour le nom et l'avatar ; user:email parce que l'adresse est
        # privée par défaut et n'apparaît pas sur /user sans ce scope.
        client_kwargs={"scope": "read:user user:email"},
    )


def _oauth_non_configure(fournisseur, variables):
    """503 plutôt qu'une 500 : le fournisseur n'est pas cassé, il est absent."""
    return jsonify({"error": f"OAuth {fournisseur} non configuré : renseigner "
                             f"{variables} dans .env."}), 503


@app.route("/")
def index():
    return send_from_directory(_DIR, "Index.html")


@app.route("/auth/google")
def auth_google():
    """Envoie l'utilisateur s'authentifier chez Google."""
    if not GOOGLE_CONFIGURE:
        return _oauth_non_configure("Google", "GOOGLE_CLIENT_ID et GOOGLE_CLIENT_SECRET")
    # _external=True : Google exige une URL absolue, et elle doit correspondre au
    # caractère près à l'URI de redirection déclarée dans la console Cloud.
    return oauth.google.authorize_redirect(url_for("auth_google_callback", _external=True))


@app.route("/auth/google/callback")
def auth_google_callback():
    """Retour de Google : échange le code contre un token et ouvre la session."""
    if not GOOGLE_CONFIGURE:
        return _oauth_non_configure("Google", "GOOGLE_CLIENT_ID et GOOGLE_CLIENT_SECRET")

    try:
        token = oauth.google.authorize_access_token()
    except OAuthError:
        # L'utilisateur a refusé, ou le state ne correspond pas. Pas de détail
        # technique dans l'URL : ça finirait dans les logs et l'historique.
        return redirect("/?connexion=echec")

    # Authlib valide et décode l'id_token dès que le scope openid est demandé.
    infos = token.get("userinfo") or oauth.google.userinfo(token=token)

    # Un compte Google dont l'email n'est pas vérifié ne prouve rien : sans ce
    # test, n'importe qui pourrait se déclarer titulaire de l'adresse.
    if not infos.get("email_verified"):
        return redirect("/?connexion=email_non_verifie")

    session["utilisateur"] = {
        # "sub" est l'identifiant Google stable : l'email, lui, peut changer.
        "id": infos["sub"],
        "nom": infos.get("name") or infos.get("email", ""),
        "email": infos.get("email", ""),
        "photo": infos.get("picture", ""),
        # Deux fournisseurs numérotent leurs comptes chacun de leur côté : sans
        # ce champ, rien ne distinguerait l'utilisateur Google 42 du GitHub 42.
        "fournisseur": "google",
    }
    return redirect("/?connexion=ok")


def _api_github(token, chemin):
    """Lit une ressource de l'API GitHub. Renvoie None si l'appel échoue.

    Contrairement à Google, aucune information d'identité n'accompagne le
    token : il faut deux requêtes de plus, et donc deux occasions de plus de
    tomber sur un réseau coupé ou un token révoqué entre-temps.
    """
    try:
        reponse = oauth.github.get(chemin, token=token)
    except requests.RequestException:
        return None
    if not reponse.ok:
        return None
    try:
        return reponse.json()
    except ValueError:
        return None


def _email_verifie_github(emails):
    """Adresse vérifiée du compte, "" s'il n'y en a aucune.

    GitHub n'a pas d'équivalent du `email_verified` de Google sur /user : c'est
    /user/emails qui porte les drapeaux, une adresse par ligne. On prend la
    principale si elle est vérifiée, sinon n'importe quelle autre qui l'est —
    une adresse non vérifiée ne prouve pas qu'on la possède.
    """
    if not isinstance(emails, list):
        return ""
    verifiees = [e for e in emails
                 if isinstance(e, dict) and e.get("verified") and e.get("email")]
    for adresse in verifiees:
        if adresse.get("primary"):
            return adresse["email"]
    return verifiees[0]["email"] if verifiees else ""


@app.route("/auth/github")
def auth_github():
    """Envoie l'utilisateur s'authentifier chez GitHub."""
    if not GITHUB_CONFIGURE:
        return _oauth_non_configure("GitHub", "GITHUB_CLIENT_ID et GITHUB_CLIENT_SECRET")
    # Même contrainte que chez Google : l'URL doit correspondre au caractère près
    # à celle déclarée dans les réglages de l'OAuth App GitHub.
    return oauth.github.authorize_redirect(url_for("auth_github_callback", _external=True))


@app.route("/auth/github/callback")
def auth_github_callback():
    """Retour de GitHub : échange le code, puis lit le profil sur l'API REST."""
    if not GITHUB_CONFIGURE:
        return _oauth_non_configure("GitHub", "GITHUB_CLIENT_ID et GITHUB_CLIENT_SECRET")

    try:
        token = oauth.github.authorize_access_token()
    except OAuthError:
        # L'utilisateur a refusé, ou le state ne correspond pas. Pas de détail
        # technique dans l'URL : ça finirait dans les logs et l'historique.
        return redirect("/?connexion=echec")
    except requests.RequestException:
        return redirect("/?connexion=echec")

    profil = _api_github(token, "user")
    if not profil or not profil.get("id"):
        return redirect("/?connexion=echec")

    email = _email_verifie_github(_api_github(token, "user/emails"))
    if not email:
        return redirect("/?connexion=email_non_verifie")

    session["utilisateur"] = {
        # L'identifiant numérique ne bouge jamais ; le login, lui, se renomme.
        "id": str(profil["id"]),
        "nom": profil.get("name") or profil.get("login") or email,
        "email": email,
        "photo": profil.get("avatar_url", ""),
        "fournisseur": "github",
    }
    return redirect("/?connexion=ok")


@app.route("/auth/logout", methods=["POST"])
def auth_logout():
    """Ferme la session. POST seulement : en GET, un <img> suffirait à
    déconnecter un visiteur à son insu."""
    session.pop("utilisateur", None)
    return jsonify({"ok": True})


@app.route("/api/moi")
def api_moi():
    """Qui est connecté ? Le front en a besoin pour choisir quoi afficher."""
    utilisateur = session.get("utilisateur")
    if not utilisateur:
        response = jsonify({
            "connecte": False,
            "oauth_disponible": OAUTH_CONFIGURE,
        })
    else:
        response = jsonify({
            "connecte": True,
            "oauth_disponible": True,
            **utilisateur,
        })
    response.headers["Cache-Control"] = "no-store"
    return response


@app.route("/chat")
def chat_page():
    return send_from_directory(_DIR, "chat.html")


@app.route("/<path:nom>")
def fichier_public(nom):
    if nom not in FICHIERS_PUBLICS:
        abort(404)
    return send_from_directory(_DIR, nom)


def _lire_message(champ="message"):
    """Extrait et valide un champ texte du corps JSON.

    Retourne (message, None) si valide, (None, réponse d'erreur) sinon.
    """
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None, (jsonify({"error": "Corps de requête JSON invalide."}), 400)

    message = data.get(champ)
    if not isinstance(message, str):
        return None, (jsonify({"error": f"Le champ '{champ}' doit être une chaîne de caractères."}), 400)

    message = message.strip()
    if not message:
        return None, (jsonify({"error": f"Champ '{champ}' vide."}), 400)

    return message, None


@app.route("/api/chat", methods=["POST"])
def api_chat():
    message, erreur = _lire_message()
    if erreur:
        return erreur

    # Un quiz en cours capte tous les messages : ils sont des réponses, pas des
    # questions. On les tient hors de l'historique et du journal des lacunes.
    etat_quiz = session.get("quiz")
    if etat_quiz is not None:
        etat_quiz, response = repondre_quiz(etat_quiz, message)
    elif message.lower() == "quiz":
        etat_quiz, response = demarrer_quiz()
    else:
        # Les suggestions voyagent à part du texte : le front en fait des boutons
        # cliquables plutôt qu'une liste numérotée que l'utilisateur doit recopier.
        resultat = bot.repondre(message)
        resultat["quiz_actif"] = False
        resultat["feedback_possible"] = True
        return jsonify(resultat)

    if etat_quiz is None:
        session.pop("quiz", None)
    else:
        session["quiz"] = etat_quiz
    # Le front a besoin de savoir si un quiz est en cours pour afficher son
    # badge et adapter le placeholder de saisie.
    # Une correction de quiz n'est pas un extrait de la FAQ : ni suggestion de
    # suivi, ni pouce, y compris sur le message qui clôt le quiz.
    return jsonify({"response": response,
                    "suggestions": [],
                    "titre_suggestions": "",
                    "feedback_possible": False,
                    "quiz_actif": etat_quiz is not None})


@app.route("/api/feedback", methods=["POST"])
def api_feedback():
    """Signale qu'une réponse n'a pas aidé, pour repérer les lacunes de la FAQ.

    Seul le pouce vers le bas est enregistré : c'est lui qui désigne du travail
    à faire. Un pouce vers le haut est accepté et ignoré, pour que le front
    n'ait pas à traiter deux cas.
    """
    question, erreur = _lire_message("question")
    if erreur:
        return erreur

    if request.get_json(silent=True).get("utile") is False:
        signaler_reponse_inutile(question)
    return jsonify({"ok": True})


if __name__ == "__main__":
    # Le debugger Werkzeug permet l'exécution de code arbitraire : il ne doit
    # s'activer qu'à la demande explicite, jamais par défaut.
    debug = os.environ.get("CHATPY_DEBUG") == "1"
    # Port 5000 est souvent occupé sur macOS par le service AirPlay Receiver.
    app.run(debug=debug, port=5001)
