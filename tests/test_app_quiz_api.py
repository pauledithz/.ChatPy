"""Tests for the quiz support added to app.py's POST /api/chat endpoint:

- an active quiz (stored in the Flask session) intercepts every message as an
  answer instead of forwarding it to bot.traiter_message()
- 'quiz' starts a new quiz when none is active
- any other message is delegated to bot.traiter_message() as before
- basic request validation (unchanged, but exercised here for regression safety)
"""
import pytest

import app as app_module
import ia_en_python


@pytest.fixture
def client():
    app_module.app.config.update(TESTING=True)
    with app_module.app.test_client() as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def small_faq(monkeypatch):
    # A tiny, controlled FAQ keeps the quiz flow deterministic and avoids
    # depending on the real (and much larger) faq.json content.
    monkeypatch.setattr(ia_en_python, "faq", {"question un": "reponse un", "question deux": "reponse deux"})
    yield


# ── Request validation (pre-existing behaviour, still exercised through the
#    new branching added by this PR) ─────────────────────────────────────────

def test_api_chat_rejects_non_json_body(client):
    resp = client.post("/api/chat", data="not json", content_type="text/plain")
    assert resp.status_code == 400
    assert "JSON invalide" in resp.get_json()["error"]


def test_api_chat_rejects_missing_message_field(client):
    resp = client.post("/api/chat", json={})
    assert resp.status_code == 400


def test_api_chat_rejects_non_string_message(client):
    resp = client.post("/api/chat", json={"message": 123})
    assert resp.status_code == 400
    assert "chaîne de caractères" in resp.get_json()["error"]


def test_api_chat_rejects_empty_message(client):
    resp = client.post("/api/chat", json={"message": "   "})
    assert resp.status_code == 400
    assert "vide" in resp.get_json()["error"]


# ── Delegation to bot.traiter_message() when no quiz is active ──────────────

def test_api_chat_delegates_non_quiz_message_to_bot(client, monkeypatch):
    monkeypatch.setattr(app_module.bot, "traiter_message", lambda message: f"echo:{message}")

    resp = client.post("/api/chat", json={"message": "Bonjour"})

    assert resp.status_code == 200
    assert resp.get_json()["response"] == "echo:Bonjour"


# ── Starting a quiz ───────────────────────────────────────────────────────────

def test_api_chat_starts_quiz_on_quiz_keyword(client):
    resp = client.post("/api/chat", json={"message": "quiz"})

    assert resp.status_code == 200
    body = resp.get_json()["response"]
    assert "Mode Quiz" in body

    with client.session_transaction() as sess:
        assert sess["quiz"]["score"] == 0
        assert sess["quiz"]["total"] == 0


def test_api_chat_quiz_keyword_is_case_insensitive(client):
    resp = client.post("/api/chat", json={"message": "QUIZ"})
    assert "Mode Quiz" in resp.get_json()["response"]


def test_api_chat_quiz_start_does_not_call_bot(client, monkeypatch):
    called = []
    monkeypatch.setattr(app_module.bot, "traiter_message", lambda message: called.append(message))

    client.post("/api/chat", json={"message": "quiz"})

    assert called == []


# ── Answering during an active quiz ──────────────────────────────────────────

def test_api_chat_quiz_answer_is_not_sent_to_bot(client, monkeypatch):
    called = []
    monkeypatch.setattr(app_module.bot, "traiter_message", lambda message: called.append(message))

    client.post("/api/chat", json={"message": "quiz"})
    client.post("/api/chat", json={"message": "ma reponse au quiz"})

    assert called == []


def test_api_chat_quiz_correct_answer_updates_session_score(client, monkeypatch):
    monkeypatch.setattr(ia_en_python, "calcul_similarite", lambda a, b: 1.0)

    client.post("/api/chat", json={"message": "quiz"})
    resp = client.post("/api/chat", json={"message": "peu importe, la similarité est mockée"})

    assert "Bonne réponse" in resp.get_json()["response"]
    with client.session_transaction() as sess:
        assert sess["quiz"]["score"] == 1
        assert sess["quiz"]["total"] == 1


def test_api_chat_quiz_wrong_answer_does_not_update_score(client, monkeypatch):
    monkeypatch.setattr(ia_en_python, "calcul_similarite", lambda a, b: 0.0)

    client.post("/api/chat", json={"message": "quiz"})
    resp = client.post("/api/chat", json={"message": "n'importe quoi"})

    assert "Pas tout à fait" in resp.get_json()["response"]
    with client.session_transaction() as sess:
        assert sess["quiz"]["score"] == 0
        assert sess["quiz"]["total"] == 1


@pytest.mark.parametrize("mot_arret", ["fin", "EXIT", "Quitter"])
def test_api_chat_quiz_stop_word_ends_and_clears_session(client, monkeypatch, mot_arret):
    monkeypatch.setattr(ia_en_python, "calcul_similarite", lambda a, b: 1.0)

    client.post("/api/chat", json={"message": "quiz"})
    client.post("/api/chat", json={"message": "une reponse"})
    resp = client.post("/api/chat", json={"message": mot_arret})

    body = resp.get_json()["response"]
    assert "Score final" in body
    assert "1/1" in body

    with client.session_transaction() as sess:
        assert "quiz" not in sess


def test_api_chat_quiz_stop_word_before_any_answer(client):
    client.post("/api/chat", json={"message": "quiz"})
    resp = client.post("/api/chat", json={"message": "fin"})

    assert "Aucune question répondue" in resp.get_json()["response"]
    with client.session_transaction() as sess:
        assert "quiz" not in sess


def test_api_chat_quiz_completes_and_clears_session_after_max_questions(client, monkeypatch):
    monkeypatch.setattr(ia_en_python, "calcul_similarite", lambda a, b: 1.0)
    monkeypatch.setattr(app_module, "demarrer_quiz", lambda: ia_en_python.demarrer_quiz(nb_questions=2))

    client.post("/api/chat", json={"message": "quiz"})
    resp1 = client.post("/api/chat", json={"message": "reponse"})
    resp2 = client.post("/api/chat", json={"message": "reponse"})

    assert "Bonne réponse" in resp1.get_json()["response"]
    body2 = resp2.get_json()["response"]
    assert "Score final" in body2
    assert "2/2" in body2

    with client.session_transaction() as sess:
        assert "quiz" not in sess


def test_api_chat_quiz_expected_answer_never_leaves_the_server(client):
    # Only the question text and score should travel in the session cookie;
    # the expected answer must stay server-side.
    client.post("/api/chat", json={"message": "quiz"})
    with client.session_transaction() as sess:
        assert set(sess["quiz"].keys()) == {"question", "score", "total", "max"}
        assert "reponse un" not in str(sess["quiz"])
        assert "reponse deux" not in str(sess["quiz"])


# ── Session/secret key wiring ─────────────────────────────────────────────────

def test_app_has_a_secret_key_configured():
    assert app_module.app.secret_key