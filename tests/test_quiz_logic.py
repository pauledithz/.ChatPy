"""Tests for the quiz-related logic added to ia_en_python.py:

- choisir_question_quiz
- evaluer_reponse_quiz
- _bilan_quiz
- demarrer_quiz / repondre_quiz (web quiz state machine)
- mode_quiz (terminal quiz loop)
- the COMMANDES_TERMINAL / QUIZ_* constants
"""
import pytest

import ia_en_python


# ── Constants ────────────────────────────────────────────────────────────────

def test_commandes_terminal_no_longer_includes_quiz():
    assert ia_en_python.COMMANDES_TERMINAL == ("clear", "historique")
    assert "quiz" not in ia_en_python.COMMANDES_TERMINAL


def test_quiz_constants_values():
    assert ia_en_python.QUIZ_NB_QUESTIONS == 10
    assert ia_en_python.QUIZ_MOTS_ARRET == ("fin", "exit", "quitter")
    assert ia_en_python.QUIZ_SEUIL_BONNE == 70
    assert ia_en_python.QUIZ_SEUIL_PRESQUE == 35


def test_chatbot_response_quiz_no_longer_treated_as_terminal_only(monkeypatch):
    # Previously "quiz" was in COMMANDES_TERMINAL and chatbot_response() would
    # reply with the "n'existe que dans la version terminal" message. Now it
    # falls through to normal matching (and possibly the "don't understand"
    # fallback, which logs to disk) since quiz is handled before
    # chatbot_response() is ever reached in both front-ends.
    monkeypatch.setattr(ia_en_python, "_logger_question_sans_reponse", lambda message: None)
    response = ia_en_python.chatbot_response("quiz")
    assert "n'existe que dans la version terminal" not in response


# ── choisir_question_quiz ────────────────────────────────────────────────────

def test_choisir_question_quiz_returns_none_for_empty_faq(monkeypatch):
    monkeypatch.setattr(ia_en_python, "faq", {})
    assert ia_en_python.choisir_question_quiz() is None


def test_choisir_question_quiz_returns_a_valid_pair(monkeypatch):
    monkeypatch.setattr(ia_en_python, "faq", {"q1": "a1", "q2": "a2"})
    result = ia_en_python.choisir_question_quiz()
    assert result in [("q1", "a1"), ("q2", "a2")]


def test_choisir_question_quiz_avoids_repeating_last_question(monkeypatch):
    monkeypatch.setattr(ia_en_python, "faq", {"q1": "a1", "q2": "a2"})
    for _ in range(30):
        question, _ = ia_en_python.choisir_question_quiz(derniere_question="q1")
        assert question != "q1"


def test_choisir_question_quiz_single_question_can_repeat(monkeypatch):
    monkeypatch.setattr(ia_en_python, "faq", {"q1": "a1"})
    result = ia_en_python.choisir_question_quiz(derniere_question="q1")
    assert result == ("q1", "a1")


# ── evaluer_reponse_quiz ──────────────────────────────────────────────────────

def test_evaluer_reponse_quiz_identical_answer_is_bonne():
    sim, verdict = ia_en_python.evaluer_reponse_quiz(
        "Une variable stocke une valeur", "Une variable stocke une valeur"
    )
    assert sim == 100
    assert verdict == "bonne"


def test_evaluer_reponse_quiz_unrelated_answer_is_fausse():
    sim, verdict = ia_en_python.evaluer_reponse_quiz(
        "banane", "xyz totalement different sujet sans aucun rapport"
    )
    assert verdict == "fausse"
    assert sim < ia_en_python.QUIZ_SEUIL_PRESQUE


@pytest.mark.parametrize(
    "ratio, expected_verdict",
    [
        (1.0, "bonne"),
        (0.70, "bonne"),
        (0.69, "presque"),
        (0.35, "presque"),
        (0.34, "fausse"),
        (0.0, "fausse"),
    ],
)
def test_evaluer_reponse_quiz_threshold_boundaries(monkeypatch, ratio, expected_verdict):
    monkeypatch.setattr(ia_en_python, "calcul_similarite", lambda a, b: ratio)
    sim, verdict = ia_en_python.evaluer_reponse_quiz("peu importe", "peu importe")
    assert sim == int(ratio * 100)
    assert verdict == expected_verdict


# ── _bilan_quiz ───────────────────────────────────────────────────────────────

def test_bilan_quiz_no_questions_answered():
    assert ia_en_python._bilan_quiz(0, 0) == "Quiz terminé. Aucune question répondue."


def test_bilan_quiz_reports_score_and_percentage():
    message = ia_en_python._bilan_quiz(7, 10)
    assert "7/10" in message
    assert "70%" in message
    assert "Tapez 'quiz' pour rejouer." in message


def test_bilan_quiz_perfect_score():
    message = ia_en_python._bilan_quiz(3, 3)
    assert "3/3" in message
    assert "100%" in message


# ── demarrer_quiz ─────────────────────────────────────────────────────────────

def test_demarrer_quiz_returns_none_state_when_faq_empty(monkeypatch):
    monkeypatch.setattr(ia_en_python, "faq", {})
    etat, message = ia_en_python.demarrer_quiz()
    assert etat is None
    assert "indisponible" in message


def test_demarrer_quiz_builds_initial_state(monkeypatch):
    monkeypatch.setattr(ia_en_python, "faq", {"q1": "a1", "q2": "a2"})
    etat, message = ia_en_python.demarrer_quiz(nb_questions=5)

    assert etat["score"] == 0
    assert etat["total"] == 0
    assert etat["max"] == 5
    assert etat["question"] in {"q1", "q2"}
    assert "5 questions" in message
    assert "(1/5)" in message
    assert etat["question"] in message


def test_demarrer_quiz_does_not_leak_the_expected_answer(monkeypatch):
    monkeypatch.setattr(ia_en_python, "faq", {"q1": "la reponse secrete"})
    etat, message = ia_en_python.demarrer_quiz()
    assert "la reponse secrete" not in message
    assert "la reponse secrete" not in str(etat)


# ── repondre_quiz ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("mot_arret", ["fin", "EXIT", " quitter ", "Fin"])
def test_repondre_quiz_stop_word_ends_quiz(monkeypatch, mot_arret):
    monkeypatch.setattr(ia_en_python, "faq", {"q1": "a1", "q2": "a2"})
    etat = {"question": "q1", "score": 2, "total": 3, "max": 10}

    nouvel_etat, message = ia_en_python.repondre_quiz(etat, mot_arret)

    assert nouvel_etat is None
    assert "2/3" in message


def test_repondre_quiz_missing_question_interrupts_quiz(monkeypatch):
    monkeypatch.setattr(ia_en_python, "faq", {"q2": "a2"})
    etat = {"question": "q1", "score": 0, "total": 0, "max": 10}

    nouvel_etat, message = ia_en_python.repondre_quiz(etat, "n'importe quoi")

    assert nouvel_etat is None
    assert "introuvable" in message


def test_repondre_quiz_correct_answer_advances_and_scores(monkeypatch):
    monkeypatch.setattr(ia_en_python, "faq", {"q1": "reponse1", "q2": "reponse2"})
    monkeypatch.setattr(ia_en_python, "calcul_similarite", lambda a, b: 1.0)
    etat = {"question": "q1", "score": 0, "total": 0, "max": 10}

    nouvel_etat, message = ia_en_python.repondre_quiz(etat, "reponse1")

    assert nouvel_etat is not None
    assert nouvel_etat["score"] == 1
    assert nouvel_etat["total"] == 1
    assert nouvel_etat["question"] == "q2"  # only remaining option
    assert "Bonne réponse" in message
    assert "reponse1" in message  # expected answer revealed after answering
    assert "(2/10)" in message


def test_repondre_quiz_almost_correct_answer_does_not_score(monkeypatch):
    monkeypatch.setattr(ia_en_python, "faq", {"q1": "reponse1", "q2": "reponse2"})
    monkeypatch.setattr(ia_en_python, "calcul_similarite", lambda a, b: 0.5)
    etat = {"question": "q1", "score": 0, "total": 0, "max": 10}

    nouvel_etat, message = ia_en_python.repondre_quiz(etat, "quelque chose")

    assert nouvel_etat["score"] == 0
    assert nouvel_etat["total"] == 1
    assert "Presque" in message


def test_repondre_quiz_wrong_answer_does_not_score(monkeypatch):
    monkeypatch.setattr(ia_en_python, "faq", {"q1": "reponse1", "q2": "reponse2"})
    monkeypatch.setattr(ia_en_python, "calcul_similarite", lambda a, b: 0.0)
    etat = {"question": "q1", "score": 0, "total": 0, "max": 10}

    nouvel_etat, message = ia_en_python.repondre_quiz(etat, "nawak")

    assert nouvel_etat["score"] == 0
    assert nouvel_etat["total"] == 1
    assert "Pas tout à fait" in message


def test_repondre_quiz_ends_when_max_questions_reached(monkeypatch):
    monkeypatch.setattr(ia_en_python, "faq", {"q1": "reponse1", "q2": "reponse2"})
    monkeypatch.setattr(ia_en_python, "calcul_similarite", lambda a, b: 1.0)
    etat = {"question": "q1", "score": 4, "total": 4, "max": 5}

    nouvel_etat, message = ia_en_python.repondre_quiz(etat, "reponse1")

    assert nouvel_etat is None
    assert "5/5" in message
    assert "100%" in message


def test_repondre_quiz_ends_early_if_no_more_questions_available(monkeypatch):
    monkeypatch.setattr(ia_en_python, "faq", {"q1": "reponse1"})
    monkeypatch.setattr(ia_en_python, "calcul_similarite", lambda a, b: 1.0)
    # Simulate the FAQ becoming unusable for a next pick after this answer is scored.
    monkeypatch.setattr(ia_en_python, "choisir_question_quiz", lambda derniere_question=None: None)
    etat = {"question": "q1", "score": 0, "total": 0, "max": 10}

    nouvel_etat, message = ia_en_python.repondre_quiz(etat, "reponse1")

    assert nouvel_etat is None
    assert "1/1" in message
    assert "Bonne réponse" in message


# ── mode_quiz (terminal loop) ─────────────────────────────────────────────────

def test_mode_quiz_empty_faq_prints_error_and_returns(monkeypatch, capsys):
    monkeypatch.setattr(ia_en_python, "faq", {})

    def fail_if_called(*args, **kwargs):
        raise AssertionError("input() should not be called when the FAQ is empty")

    monkeypatch.setattr("builtins.input", fail_if_called)

    ia_en_python.mode_quiz()

    captured = capsys.readouterr()
    assert "indisponible" in captured.out


def test_mode_quiz_scores_correct_answer_and_stops_on_fin(monkeypatch, capsys):
    monkeypatch.setattr(ia_en_python, "faq", {"q1": "a1"})
    monkeypatch.setattr(ia_en_python, "calcul_similarite", lambda a, b: 1.0)

    reponses = iter(["une reponse quelconque", "fin"])
    monkeypatch.setattr("builtins.input", lambda *a, **k: next(reponses))

    ia_en_python.mode_quiz(nb_questions_max=5)

    captured = capsys.readouterr()
    assert "Bonne réponse" in captured.out
    assert "1/1" in captured.out
    assert "100%" in captured.out


def test_mode_quiz_wrong_answers_are_reported_and_not_scored(monkeypatch, capsys):
    monkeypatch.setattr(ia_en_python, "faq", {"q1": "a1"})
    monkeypatch.setattr(ia_en_python, "calcul_similarite", lambda a, b: 0.0)

    reponses = iter(["reponse fausse", "fin"])
    monkeypatch.setattr("builtins.input", lambda *a, **k: next(reponses))

    ia_en_python.mode_quiz(nb_questions_max=5)

    captured = capsys.readouterr()
    assert "Pas tout à fait" in captured.out
    assert "0/1" in captured.out


def test_mode_quiz_stops_immediately_on_eof(monkeypatch, capsys):
    monkeypatch.setattr(ia_en_python, "faq", {"q1": "a1"})

    def raise_eof(*args, **kwargs):
        raise EOFError

    monkeypatch.setattr("builtins.input", raise_eof)

    ia_en_python.mode_quiz(nb_questions_max=5)

    captured = capsys.readouterr()
    assert "Aucune question répondue" in captured.out


def test_mode_quiz_reaches_max_questions_without_stopping(monkeypatch, capsys):
    monkeypatch.setattr(ia_en_python, "faq", {"q1": "a1"})
    monkeypatch.setattr(ia_en_python, "calcul_similarite", lambda a, b: 1.0)

    monkeypatch.setattr("builtins.input", lambda *a, **k: "toujours la meme reponse")

    ia_en_python.mode_quiz(nb_questions_max=3)

    captured = capsys.readouterr()
    assert "3/3" in captured.out
    assert "100%" in captured.out