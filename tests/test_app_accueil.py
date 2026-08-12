"""Tests de la route « / » : l'accueil est réservé aux visiteurs anonymes.

L'accueil est une page de présentation — il explique le chatbot et en montre
une démo animée. Connecté, on peut poser de vraies questions : la présentation
n'a plus d'objet, et le serveur envoie droit au chat.

Ce qui est vérifié ici, c'est surtout ce qui ne doit pas casser autour :
qu'on retrouve l'accueil après s'être déconnecté, et que la redirection ne
reste pas collée dans le cache du navigateur.
"""
import importlib

import pytest


@pytest.fixture
def app_module():
    """Recharge app.py pour repartir d'une app Flask fraîche à chaque test."""
    import app as app_module
    importlib.reload(app_module)
    return app_module


@pytest.fixture
def client(app_module):
    app_module.app.testing = True
    return app_module.app.test_client()


def _connecter(client):
    """Ouvre une session sans passer par un fournisseur OAuth.

    Ce qui est testé ici est la conséquence d'être connecté, pas la façon dont
    on l'est devenu : les trois moyens de connexion posent la même clé.
    """
    with client.session_transaction() as session:
        session["utilisateur"] = {
            "id": "42",
            "nom": "Paul",
            "email": "paul@example.com",
            "photo": "",
            "fournisseur": "local",
        }


def test_accueil_servi_a_un_visiteur_anonyme(client):
    reponse = client.get("/")

    assert reponse.status_code == 200
    assert b"ChatPy" in reponse.data


def test_accueil_redirige_un_visiteur_connecte(app_module, client):
    _connecter(client)

    reponse = client.get("/")

    assert reponse.status_code == 302
    assert reponse.headers["Location"] == app_module.PAGE_APRES_CONNEXION


def test_accueil_revient_apres_deconnexion(client):
    """Le point sensible : la porte se referme, elle ne se condamne pas."""
    _connecter(client)
    assert client.get("/").status_code == 302

    client.post("/auth/logout")

    reponse = client.get("/")
    assert reponse.status_code == 200
    assert b"ChatPy" in reponse.data


@pytest.mark.parametrize("connecte", [False, True])
def test_l_accueil_n_est_jamais_mis_en_cache(client, connecte):
    """Sans ça, un navigateur peut resservir la redirection à quelqu'un qui
    vient de se déconnecter : l'accueil lui resterait fermé sans explication."""
    if connecte:
        _connecter(client)

    reponse = client.get("/")

    assert reponse.headers.get("Cache-Control") == "no-store"


@pytest.mark.parametrize("chemin", ["/chat", "/compte"])
def test_les_autres_pages_restent_ouvertes_aux_connectes(client, chemin):
    """Seul l'accueil est concerné : rien d'autre ne doit s'être fermé au
    passage, et /compte reste ouvert aux deux publics."""
    _connecter(client)

    assert client.get(chemin).status_code == 200


@pytest.mark.parametrize("chemin", ["/chat", "/compte"])
def test_les_autres_pages_restent_ouvertes_aux_anonymes(client, chemin):
    assert client.get(chemin).status_code == 200
