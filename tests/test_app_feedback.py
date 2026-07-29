"""Tests de POST /api/feedback : le pouce vers le bas posé sous une réponse.

Le journal des lacunes ne voit que les échecs complets du matching. Une réponse
trouvée mais mauvaise n'y laisse aucune trace : c'est ce que ce point d'entrée
enregistre, dans un compteur distinct (`pouces_bas`).
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
def journal_temporaire(tmp_path, monkeypatch):
    """Redirige les fichiers runtime vers des fichiers jetables : jamais les vrais."""
    chemin = tmp_path / "questions_sans_reponse.json"
    monkeypatch.setattr(ia_en_python, "QUESTIONS_SANS_REPONSE_FILE", str(chemin))
    monkeypatch.setattr(ia_en_python, "HISTORY_FILE", str(tmp_path / "historique.json"))
    return chemin


def test_pouce_bas_enregistre_la_question(client, journal_temporaire):
    resp = client.post("/api/feedback",
                       json={"question": "comment trier une liste", "utile": False})

    assert resp.status_code == 200
    assert resp.get_json() == {"ok": True}
    assert '"pouces_bas": 1' in journal_temporaire.read_text(encoding="utf-8")


def test_pouce_haut_est_accepte_sans_rien_enregistrer(client, journal_temporaire):
    # Le front envoie les deux votes ; seul le négatif désigne du travail à faire.
    resp = client.post("/api/feedback",
                       json={"question": "comment trier une liste", "utile": True})

    assert resp.status_code == 200
    assert not journal_temporaire.exists()


def test_question_manquante_est_rejetee(client):
    assert client.post("/api/feedback", json={"utile": False}).status_code == 400
    assert client.post("/api/feedback", json={"question": "  ", "utile": False}).status_code == 400
    assert client.post("/api/feedback", data="pas du json",
                       content_type="application/json").status_code == 400


def test_le_chat_annonce_au_front_quand_le_pouce_a_du_sens(client):
    # Une correction de quiz n'est pas un extrait de la FAQ : pas de pouce dessus,
    # y compris sur le message qui clôt le quiz.
    assert client.post("/api/chat", json={"message": "bonjour"}
                       ).get_json()["feedback_possible"] is True

    client.post("/api/chat", json={"message": "quiz"})
    assert client.post("/api/chat", json={"message": "fin"}
                       ).get_json()["feedback_possible"] is False
