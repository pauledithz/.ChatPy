"""Tests pour app.py : le routage du quiz dans /api/chat et la clé de session.

Couvre les changements du diff :
- CHATPY_SECRET_KEY (clé fixe vs clé aléatoire par process)
- la bascule quiz / chat normal dans api_chat()
- le fait que les réponses au quiz ne passent jamais par bot.traiter_message()
"""
import importlib
import re

import pytest

import ia_en_python as iep


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


def _extraire_question(message_reponse):
    """Extrait le texte de la question depuis un message '❓ (n/max) <question> ?'."""
    match = re.search(r"❓ \(\d+/\d+\) (.+) \?", message_reponse)
    assert match, f"Aucune question trouvée dans : {message_reponse!r}"
    return match.group(1)


# ── clé de session ───────────────────────────────────────────────────────────

def test_secret_key_utilise_la_variable_environnement(monkeypatch):
    monkeypatch.setenv("CHATPY_SECRET_KEY", "ma-cle-fixe-de-test")
    import app as app_module
    importlib.reload(app_module)

    assert app_module.app.secret_key == "ma-cle-fixe-de-test"


def test_secret_key_aleatoire_si_variable_absente(monkeypatch):
    monkeypatch.delenv("CHATPY_SECRET_KEY", raising=False)
    # app.py charge aussi .env : sans ça, la clé du fichier local reviendrait
    # aussitôt et le test ne mesurerait plus l'absence de configuration.
    monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **k: False)
    import app as app_module

    importlib.reload(app_module)
    premiere_cle = app_module.app.secret_key
    importlib.reload(app_module)
    deuxieme_cle = app_module.app.secret_key

    assert premiere_cle != deuxieme_cle
    assert len(premiere_cle) == 64  # secrets.token_hex(32) -> 64 caractères hexa


# ── /api/chat : bascule quiz / chat normal ──────────────────────────────────

def test_message_normal_hors_quiz_appelle_bot_repondre(app_module, client, monkeypatch):
    """bot.repondre() est l'entrée unique des deux front-ends : elle renvoie les
    suggestions à part du texte, pour que le web en fasse des boutons."""
    appels = []

    def faux_repondre(message):
        appels.append(message)
        return {"response": "réponse du bot", "suggestions": [], "titre_suggestions": ""}

    monkeypatch.setattr(app_module.bot, "repondre", faux_repondre)

    resp = client.post("/api/chat", json={"message": "bonjour"})

    assert resp.status_code == 200
    assert resp.get_json() == {
        "response": "réponse du bot",
        "suggestions": [],
        "titre_suggestions": "",
        "feedback_possible": True,
        "quiz_actif": False,
    }
    assert appels == ["bonjour"]


def test_quiz_demarre_sur_message_quiz(app_module, client, monkeypatch):
    monkeypatch.setattr(iep, "faq", {"Q1": "R1", "Q2": "R2"})
    monkeypatch.setattr(iep.random, "choice", lambda seq: seq[0])

    resp = client.post("/api/chat", json={"message": "quiz"})
    data = resp.get_json()

    assert resp.status_code == 200
    assert "Mode Quiz" in data["response"]
    assert "(1/10)" in data["response"]

    with client.session_transaction() as sess:
        assert sess["quiz"]["question"] == "Q1"
        assert sess["quiz"]["score"] == 0
        assert sess["quiz"]["total"] == 0


def test_quiz_est_insensible_a_la_casse(app_module, client, monkeypatch):
    monkeypatch.setattr(iep, "faq", {"Q1": "R1"})

    resp = client.post("/api/chat", json={"message": "QuIz"})

    assert "Mode Quiz" in resp.get_json()["response"]


def test_reponse_au_quiz_ne_passe_pas_par_bot_traiter_message(app_module, client, monkeypatch):
    monkeypatch.setattr(iep, "faq", {"Q1": "La bonne réponse", "Q2": "Autre chose"})
    monkeypatch.setattr(iep.random, "choice", lambda seq: seq[0])

    appels = []
    monkeypatch.setattr(app_module.bot, "traiter_message", lambda msg: appels.append(msg))

    demarrage = client.post("/api/chat", json={"message": "quiz"}).get_json()
    question = _extraire_question(demarrage["response"])
    assert question == "Q1"

    reponse = client.post("/api/chat", json={"message": "La bonne réponse"}).get_json()

    assert appels == []  # bot.traiter_message() jamais appelé pendant le quiz
    assert "✅ Bonne réponse" in reponse["response"]


def test_quiz_progresse_sur_plusieurs_requetes(app_module, client, monkeypatch):
    monkeypatch.setattr(iep, "faq", {"Q1": "Réponse un", "Q2": "Réponse deux"})
    monkeypatch.setattr(iep.random, "choice", lambda seq: seq[0])

    client.post("/api/chat", json={"message": "quiz"})
    etape2 = client.post("/api/chat", json={"message": "Réponse un"}).get_json()

    assert "(2/10)" in etape2["response"]
    with client.session_transaction() as sess:
        assert sess["quiz"]["question"] == "Q2"
        assert sess["quiz"]["score"] == 1
        assert sess["quiz"]["total"] == 1


def test_fin_termine_le_quiz_et_vide_la_session(app_module, client, monkeypatch):
    monkeypatch.setattr(iep, "faq", {"Q1": "R1"})

    client.post("/api/chat", json={"message": "quiz"})
    reponse = client.post("/api/chat", json={"message": "fin"}).get_json()

    assert "Aucune question répondue." in reponse["response"]
    with client.session_transaction() as sess:
        assert "quiz" not in sess


def test_quiz_de_dix_questions_se_termine_et_vide_la_session(app_module, client, monkeypatch):
    monkeypatch.setattr(iep, "faq", {"Q1": "R1", "Q2": "R2"})
    monkeypatch.setattr(iep.random, "choice", lambda seq: seq[0])

    client.post("/api/chat", json={"message": "quiz"})
    for _ in range(iep.QUIZ_NB_QUESTIONS - 1):
        client.post("/api/chat", json={"message": "peu importe"})
    derniere = client.post("/api/chat", json={"message": "peu importe"}).get_json()

    assert "Score final" in derniere["response"]
    with client.session_transaction() as sess:
        assert "quiz" not in sess


def test_message_apres_quiz_termine_repart_sur_bot_normal(app_module, client, monkeypatch):
    monkeypatch.setattr(iep, "faq", {"Q1": "R1"})
    monkeypatch.setattr(
        app_module.bot, "repondre",
        lambda msg: {"response": "réponse normale", "suggestions": [], "titre_suggestions": ""},
    )

    client.post("/api/chat", json={"message": "quiz"})
    client.post("/api/chat", json={"message": "fin"})
    apres = client.post("/api/chat", json={"message": "bonjour"}).get_json()

    assert apres == {
        "response": "réponse normale",
        "suggestions": [],
        "titre_suggestions": "",
        "feedback_possible": True,
        "quiz_actif": False,
    }


def test_quiz_indisponible_si_faq_vide(app_module, client, monkeypatch):
    monkeypatch.setattr(iep, "faq", {})

    resp = client.post("/api/chat", json={"message": "quiz"})
    data = resp.get_json()

    assert "indisponible" in data["response"]
    with client.session_transaction() as sess:
        assert "quiz" not in sess


# ── validation existante (non modifiée par ce PR, gardée en garde-fou) ──────

def test_message_vide_retourne_erreur_400(client):
    resp = client.post("/api/chat", json={"message": "   "})
    assert resp.status_code == 400


def test_corps_non_json_retourne_erreur_400(client):
    resp = client.post("/api/chat", data="pas du json", content_type="text/plain")
    assert resp.status_code == 400