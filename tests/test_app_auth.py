"""Tests de la connexion Google (OAuth 2.0 / OpenID Connect) dans app.py.

On ne teste jamais contre les serveurs de Google : le flow est coupé au moment
de l'échange du code, et `authorize_access_token()` est remplacé par un faux qui
renvoie le profil qu'on veut. Ce qui est vérifié ici, c'est notre code : la
construction de la redirection, les garde-fous, et ce qui atterrit en session.

Couvre :
- le repli 503 quand .env n'a pas d'identifiants (état par défaut d'un clone) ;
- l'URL d'autorisation : scope minimal, state et nonce présents ;
- le refus d'un compte dont l'email n'est pas vérifié ;
- le contenu exact de la session après connexion, et la déconnexion ;
- le fait que /auth/logout refuse le GET.
"""
import importlib
import os
import sys
from unittest import mock
from urllib.parse import parse_qs, urlparse

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app as app_module

# Profil renvoyé par Google une fois le code échangé. "sub" est l'identifiant
# stable du compte ; l'email, lui, peut changer au fil du temps.
PROFIL_GOOGLE = {
    "sub": "110001112223334445556",
    "name": "Paul Zoungrana",
    "email": "paul@example.com",
    "email_verified": True,
    "picture": "https://lh3.googleusercontent.com/photo.jpg",
}


def _recharger(identifiants=True):
    """Recharge app.py avec ou sans identifiants OAuth dans l'environnement."""
    env = {
        "CHATPY_SECRET_KEY": "cle-fixe-de-test",
        "GOOGLE_CLIENT_ID": "test-client-id.apps.googleusercontent.com" if identifiants else "",
        "GOOGLE_CLIENT_SECRET": "GOCSPX-secret-de-test" if identifiants else "",
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


# ── Sans identifiants : le site doit rester utilisable ───────────────────────

def test_auth_google_repond_503_sans_identifiants(app_non_configure):
    """Un dépôt fraîchement cloné n'a pas de .env : le site ne doit pas planter."""
    reponse = app_non_configure.app.test_client().get("/auth/google")

    assert reponse.status_code == 503
    assert "GOOGLE_CLIENT_ID" in reponse.get_json()["error"]


def test_callback_repond_503_sans_identifiants(app_non_configure):
    reponse = app_non_configure.app.test_client().get("/auth/google/callback")

    assert reponse.status_code == 503


def test_api_moi_signale_oauth_indisponible(app_non_configure):
    donnees = app_non_configure.app.test_client().get("/api/moi").get_json()

    assert donnees == {"connecte": False, "oauth_disponible": False}


# ── Construction de la redirection vers Google ───────────────────────────────

def test_auth_google_redirige_vers_google(app_configure):
    reponse = app_configure.app.test_client().get("/auth/google")

    assert reponse.status_code == 302
    url = urlparse(reponse.headers["Location"])
    assert url.hostname == "accounts.google.com"


def test_redirection_demande_le_scope_minimal(app_configure):
    """Tout scope au-delà d'openid/email/profile déclencherait une procédure de
    vérification Google, pour des données dont le site n'a aucun usage."""
    reponse = app_configure.app.test_client().get("/auth/google")
    params = parse_qs(urlparse(reponse.headers["Location"]).query)

    assert set(params["scope"][0].split()) == {"openid", "email", "profile"}
    assert params["response_type"] == ["code"]


def test_redirection_porte_state_et_nonce(app_configure):
    """state protège du CSRF, nonce du rejeu d'un id_token. Sans eux, le flow
    est vulnérable même si tout le reste est correct."""
    reponse = app_configure.app.test_client().get("/auth/google")
    params = parse_qs(urlparse(reponse.headers["Location"]).query)

    assert params.get("state", [""])[0]
    assert params.get("nonce", [""])[0]


# ── Retour de Google ─────────────────────────────────────────────────────────

def _callback_avec_profil(module, profil):
    """Joue le retour de Google en court-circuitant l'échange du code."""
    client = module.app.test_client()
    with mock.patch.object(module.oauth.google, "authorize_access_token",
                           return_value={"userinfo": profil}):
        return client, client.get("/auth/google/callback")


def test_connexion_reussie_remplit_la_session(app_configure):
    client, reponse = _callback_avec_profil(app_configure, PROFIL_GOOGLE)

    assert reponse.status_code == 302
    assert reponse.headers["Location"] == "/?connexion=ok"

    moi = client.get("/api/moi").get_json()
    assert moi["connecte"] is True
    assert moi["id"] == PROFIL_GOOGLE["sub"]
    assert moi["nom"] == "Paul Zoungrana"
    assert moi["email"] == "paul@example.com"


def test_email_non_verifie_est_refuse(app_configure):
    """Un compte Google non vérifié ne prouve pas la possession de l'adresse :
    sans ce test, n'importe qui pourrait se déclarer titulaire d'un email."""
    profil = {**PROFIL_GOOGLE, "email_verified": False}
    client, reponse = _callback_avec_profil(app_configure, profil)

    assert reponse.headers["Location"] == "/?connexion=email_non_verifie"
    assert client.get("/api/moi").get_json()["connecte"] is False


def test_refus_de_lutilisateur_ne_connecte_personne(app_configure):
    """L'utilisateur clique « Annuler » chez Google : Authlib lève OAuthError."""
    from authlib.integrations.base_client import OAuthError

    client = app_configure.app.test_client()
    with mock.patch.object(app_configure.oauth.google, "authorize_access_token",
                           side_effect=OAuthError("access_denied")):
        reponse = client.get("/auth/google/callback")

    assert reponse.headers["Location"] == "/?connexion=echec"
    assert client.get("/api/moi").get_json()["connecte"] is False


def test_le_secret_google_ne_part_jamais_au_navigateur(app_configure):
    """Le client_secret n'a aucune raison d'apparaître dans une réponse HTTP."""
    client, _ = _callback_avec_profil(app_configure, PROFIL_GOOGLE)

    corps = client.get("/api/moi").get_data(as_text=True)
    assert "GOCSPX-secret-de-test" not in corps


# ── Déconnexion ──────────────────────────────────────────────────────────────

def test_deconnexion_vide_la_session(app_configure):
    client, _ = _callback_avec_profil(app_configure, PROFIL_GOOGLE)
    assert client.get("/api/moi").get_json()["connecte"] is True

    assert client.post("/auth/logout").get_json() == {"ok": True}
    assert client.get("/api/moi").get_json()["connecte"] is False


def test_deconnexion_refuse_le_get(app_configure):
    """En GET, un simple <img src="/auth/logout"> sur un site tiers suffirait à
    déconnecter un visiteur à son insu."""
    client, _ = _callback_avec_profil(app_configure, PROFIL_GOOGLE)

    reponse = client.get("/auth/logout")

    assert reponse.status_code in (404, 405)
    assert client.get("/api/moi").get_json()["connecte"] is True


# ── Cookie de session ────────────────────────────────────────────────────────

def test_cookie_httponly_et_samesite_lax(app_configure):
    """SameSite=Strict ferait perdre le cookie au retour de redirection depuis
    Google, et le flow échouerait sur un mismatching_state."""
    assert app_configure.app.config["SESSION_COOKIE_HTTPONLY"] is True
    assert app_configure.app.config["SESSION_COOKIE_SAMESITE"] == "Lax"


def test_cookie_secure_pilote_par_lenvironnement(app_configure):
    """À 1 en local (http), le navigateur refuserait le cookie : la connexion ne
    tiendrait jamais. Le réglage doit donc rester une décision de déploiement."""
    with mock.patch.dict(os.environ, {"CHATPY_COOKIE_SECURE": "1"}), \
            mock.patch("dotenv.load_dotenv", return_value=False):
        importlib.reload(app_module)
        assert app_module.app.config["SESSION_COOKIE_SECURE"] is True
