"""Tests de la connexion GitHub (OAuth 2.0) dans app.py.

Même principe que test_app_auth.py : on ne parle jamais à GitHub. Le flow est
coupé à l'échange du code, et les deux appels d'API qui suivent (/user et
/user/emails) sont remplacés par de fausses réponses. Ce qui est vérifié ici,
c'est notre code.

GitHub diffère de Google sur trois points, et ce sont eux qui sont testés :
- pas de document de découverte : les URLs sont écrites en dur ;
- pas d'id_token : l'identité se lit sur l'API REST, donc deux requêtes de plus
  qui peuvent échouer ;
- pas de champ `email_verified` : la vérification se lit sur /user/emails.
"""
import importlib
import os
import sys
from unittest import mock
from urllib.parse import parse_qs, urlparse

import pytest
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app as app_module

# Ce que renvoie GET https://api.github.com/user une fois le code échangé.
PROFIL_GITHUB = {
    "id": 583271,
    "login": "paulo26",
    "name": "Paul Zoungrana",
    "avatar_url": "https://avatars.githubusercontent.com/u/583271?v=4",
    # L'email public est très souvent nul : c'est justement pourquoi on
    # interroge /user/emails plutôt que de se contenter de ce champ.
    "email": None,
}

EMAILS_GITHUB = [
    {"email": "secondaire@example.com", "primary": False, "verified": True},
    {"email": "paul@example.com", "primary": True, "verified": True},
]


def _recharger(identifiants=True):
    """Recharge app.py avec ou sans identifiants GitHub dans l'environnement."""
    env = {
        "CHATPY_SECRET_KEY": "cle-fixe-de-test",
        # Google reste hors-jeu : ce fichier ne teste que GitHub, et le laisser
        # configuré ferait passer OAUTH_CONFIGURE à True pour de mauvaises
        # raisons.
        "GOOGLE_CLIENT_ID": "",
        "GOOGLE_CLIENT_SECRET": "",
        "GITHUB_CLIENT_ID": "Iv1.test-client-id" if identifiants else "",
        "GITHUB_CLIENT_SECRET": "secret-github-de-test" if identifiants else "",
    }
    with mock.patch.dict(os.environ, env), \
            mock.patch("dotenv.load_dotenv", return_value=False):
        importlib.reload(app_module)
    return app_module


@pytest.fixture
def app_configure():
    module = _recharger(identifiants=True)
    module.app.testing = True
    yield module
    # Rendre l'environnement réel aux autres fichiers de tests.
    importlib.reload(app_module)


@pytest.fixture
def app_non_configure():
    module = _recharger(identifiants=False)
    module.app.testing = True
    yield module
    importlib.reload(app_module)


class _FausseReponse:
    """Le minimum de l'interface `requests.Response` utilisé par _api_github."""

    def __init__(self, donnees, ok=True):
        self._donnees = donnees
        self.ok = ok

    def json(self):
        return self._donnees


def _callback(module, profil=PROFIL_GITHUB, emails=EMAILS_GITHUB, erreur=None):
    """Joue le retour de GitHub en court-circuitant l'échange du code et l'API.

    `erreur` remplace, si fourni, ce que lève `authorize_access_token()`.
    """
    reponses = {"user": _FausseReponse(profil), "user/emails": _FausseReponse(emails)}

    def faux_get(chemin, token=None):
        reponse = reponses[chemin]
        if isinstance(reponse, Exception):
            raise reponse
        return reponse

    client = module.app.test_client()
    jeton = mock.patch.object(
        module.oauth.github, "authorize_access_token",
        side_effect=erreur, return_value={"access_token": "gho_test", "token_type": "bearer"})
    with jeton, mock.patch.object(module.oauth.github, "get", side_effect=faux_get):
        return client, client.get("/auth/github/callback")


# ── Sans identifiants : le site doit rester utilisable ───────────────────────

def test_auth_github_repond_503_sans_identifiants(app_non_configure):
    """Un dépôt fraîchement cloné n'a pas de .env : le site ne doit pas planter."""
    reponse = app_non_configure.app.test_client().get("/auth/github")

    assert reponse.status_code == 503
    assert "GITHUB_CLIENT_ID" in reponse.get_json()["error"]


def test_callback_repond_503_sans_identifiants(app_non_configure):
    reponse = app_non_configure.app.test_client().get("/auth/github/callback")

    assert reponse.status_code == 503


def test_github_seul_suffit_a_activer_oauth(app_configure):
    """Les deux fournisseurs sont indépendants : GitHub configuré et Google non,
    /api/moi doit annoncer une connexion possible."""
    assert app_configure.GOOGLE_CONFIGURE is False
    assert app_configure.OAUTH_CONFIGURE is True

    donnees = app_configure.app.test_client().get("/api/moi").get_json()
    assert donnees == {"connecte": False, "oauth_disponible": True}


def test_google_reste_503_quand_seul_github_est_configure(app_configure):
    reponse = app_configure.app.test_client().get("/auth/google")

    assert reponse.status_code == 503


# ── Construction de la redirection vers GitHub ───────────────────────────────

def test_auth_github_redirige_vers_github(app_configure):
    reponse = app_configure.app.test_client().get("/auth/github")

    assert reponse.status_code == 302
    url = urlparse(reponse.headers["Location"])
    assert url.hostname == "github.com"
    assert url.path == "/login/oauth/authorize"


def test_redirection_demande_le_scope_minimal(app_configure):
    """read:user pour le profil, user:email pour l'adresse — et rien d'autre :
    le scope `user` donnerait au passage l'accès en écriture au profil."""
    reponse = app_configure.app.test_client().get("/auth/github")
    params = parse_qs(urlparse(reponse.headers["Location"]).query)

    assert set(params["scope"][0].split()) == {"read:user", "user:email"}
    assert params["response_type"] == ["code"]


def test_redirection_porte_un_state(app_configure):
    """state protège du CSRF. GitHub n'a pas de nonce : sans id_token, il n'y a
    rien à rejouer."""
    reponse = app_configure.app.test_client().get("/auth/github")
    params = parse_qs(urlparse(reponse.headers["Location"]).query)

    assert params.get("state", [""])[0]


# ── Retour de GitHub ─────────────────────────────────────────────────────────

def test_connexion_reussie_remplit_la_session(app_configure):
    client, reponse = _callback(app_configure)

    assert reponse.status_code == 302
    assert reponse.headers["Location"] == "/?connexion=ok"

    moi = client.get("/api/moi").get_json()
    assert moi["connecte"] is True
    assert moi["id"] == "583271"
    assert moi["nom"] == "Paul Zoungrana"
    assert moi["email"] == "paul@example.com"
    assert moi["photo"] == PROFIL_GITHUB["avatar_url"]
    assert moi["fournisseur"] == "github"


def test_email_principal_verifie_prioritaire(app_configure):
    """L'adresse retenue est la principale, pas la première de la liste."""
    client, _ = _callback(app_configure)

    assert client.get("/api/moi").get_json()["email"] == "paul@example.com"


def test_repli_sur_une_adresse_verifiee_non_principale(app_configure):
    """Si la principale n'est pas vérifiée, une autre adresse vérifiée fait
    l'affaire : ce qui compte est la preuve de possession, pas le rang."""
    emails = [
        {"email": "principale@example.com", "primary": True, "verified": False},
        {"email": "autre@example.com", "primary": False, "verified": True},
    ]
    client, reponse = _callback(app_configure, emails=emails)

    assert reponse.headers["Location"] == "/?connexion=ok"
    assert client.get("/api/moi").get_json()["email"] == "autre@example.com"


def test_aucun_email_verifie_est_refuse(app_configure):
    """Une adresse non vérifiée ne prouve pas qu'on la possède — même exigence
    que le email_verified de Google."""
    emails = [{"email": "paul@example.com", "primary": True, "verified": False}]
    client, reponse = _callback(app_configure, emails=emails)

    assert reponse.headers["Location"] == "/?connexion=email_non_verifie"
    assert client.get("/api/moi").get_json()["connecte"] is False


def test_login_sert_de_nom_quand_le_profil_nen_a_pas(app_configure):
    """`name` est facultatif sur GitHub, contrairement au login."""
    client, _ = _callback(app_configure, profil={**PROFIL_GITHUB, "name": None})

    assert client.get("/api/moi").get_json()["nom"] == "paulo26"


def test_refus_de_lutilisateur_ne_connecte_personne(app_configure):
    """L'utilisateur clique « Cancel » chez GitHub : Authlib lève OAuthError."""
    from authlib.integrations.base_client import OAuthError

    client, reponse = _callback(app_configure, erreur=OAuthError("access_denied"))

    assert reponse.headers["Location"] == "/?connexion=echec"
    assert client.get("/api/moi").get_json()["connecte"] is False


def test_api_github_injoignable_ne_connecte_personne(app_configure):
    """Deux appels d'API séparent le token de l'identité : le réseau peut
    lâcher entre les deux, et personne ne doit être connecté à moitié."""
    client = app_configure.app.test_client()
    with mock.patch.object(app_configure.oauth.github, "authorize_access_token",
                           return_value={"access_token": "gho_test"}), \
            mock.patch.object(app_configure.oauth.github, "get",
                              side_effect=requests.RequestException("réseau coupé")):
        reponse = client.get("/auth/github/callback")

    assert reponse.headers["Location"] == "/?connexion=echec"
    assert client.get("/api/moi").get_json()["connecte"] is False


def test_profil_refuse_par_github_ne_connecte_personne(app_configure):
    """Token révoqué entre l'échange et l'appel : /user répond 401."""
    client = app_configure.app.test_client()
    with mock.patch.object(app_configure.oauth.github, "authorize_access_token",
                           return_value={"access_token": "gho_test"}), \
            mock.patch.object(app_configure.oauth.github, "get",
                              return_value=_FausseReponse({"message": "Bad credentials"}, ok=False)):
        reponse = client.get("/auth/github/callback")

    assert reponse.headers["Location"] == "/?connexion=echec"
    assert client.get("/api/moi").get_json()["connecte"] is False


def test_le_secret_github_ne_part_jamais_au_navigateur(app_configure):
    """Le client_secret n'a aucune raison d'apparaître dans une réponse HTTP."""
    client, _ = _callback(app_configure)

    corps = client.get("/api/moi").get_data(as_text=True)
    assert "secret-github-de-test" not in corps


def test_deconnexion_vide_la_session(app_configure):
    client, _ = _callback(app_configure)
    assert client.get("/api/moi").get_json()["connecte"] is True

    assert client.post("/auth/logout").get_json() == {"ok": True}
    assert client.get("/api/moi").get_json()["connecte"] is False
