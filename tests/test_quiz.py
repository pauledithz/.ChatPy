"""Tests pour la logique de quiz partagée entre le terminal et le web.

Couvre les fonctions ajoutées/modifiées dans ia_en_python.py :
choisir_question_quiz, evaluer_reponse_quiz, _bilan_quiz, demarrer_quiz,
repondre_quiz, mode_quiz, ainsi que la sortie de COMMANDES_TERMINAL.
"""
import builtins

import pytest

import ia_en_python as iep


# ── COMMANDES_TERMINAL ──────────────────────────────────────────────────────

def test_commandes_terminal_ne_contient_plus_quiz():
    assert "quiz" not in iep.COMMANDES_TERMINAL


def test_commandes_terminal_contient_toujours_clear_et_historique():
    assert "clear" in iep.COMMANDES_TERMINAL
    assert "historique" in iep.COMMANDES_TERMINAL


def test_message_quiz_atteint_chatbot_response_comme_une_question_normale(monkeypatch):
    # Depuis que 'quiz' n'est plus dans COMMANDES_TERMINAL, chatbot_response()
    # ne le traite plus comme une commande spéciale : il tombe dans le pipeline
    # de matching normal (les deux front-ends l'interceptent avant cet appel).
    monkeypatch.setattr(iep, "faq", {})
    monkeypatch.setattr(iep, "faq_categories", {})
    monkeypatch.setattr(iep, "norm_vers_original", {})
    response = iep.chatbot_response("quiz")
    assert "n'existe que dans la version terminal" not in response


# ── choisir_question_quiz ───────────────────────────────────────────────────

def test_choisir_question_quiz_faq_vide_retourne_none(monkeypatch):
    monkeypatch.setattr(iep, "faq", {})
    assert iep.choisir_question_quiz() is None


def test_choisir_question_quiz_retourne_une_paire_question_reponse(monkeypatch):
    monkeypatch.setattr(iep, "faq", {"Q1": "R1", "Q2": "R2"})
    resultat = iep.choisir_question_quiz()
    assert resultat in (("Q1", "R1"), ("Q2", "R2"))


def test_choisir_question_quiz_evite_de_reposer_la_derniere_question(monkeypatch):
    monkeypatch.setattr(iep, "faq", {"Q1": "R1", "Q2": "R2"})
    for _ in range(20):
        question, _ = iep.choisir_question_quiz(derniere_question="Q1")
        assert question != "Q1"


def test_choisir_question_quiz_avec_une_seule_question_repose_la_meme(monkeypatch):
    monkeypatch.setattr(iep, "faq", {"Q1": "R1"})
    resultat = iep.choisir_question_quiz(derniere_question="Q1")
    assert resultat == ("Q1", "R1")


# ── evaluer_reponse_quiz ────────────────────────────────────────────────────

def test_evaluer_reponse_quiz_reponse_identique_est_bonne():
    sim, verdict = iep.evaluer_reponse_quiz(
        "Utilisez la fonction print().", "Utilisez la fonction print()."
    )
    assert sim == 100
    assert verdict == "bonne"


def test_evaluer_reponse_quiz_ignore_accents_et_casse():
    sim, verdict = iep.evaluer_reponse_quiz("UNE VARIABLE", "une variable")
    assert sim == 100
    assert verdict == "bonne"


def test_evaluer_reponse_quiz_totalement_hors_sujet_est_fausse():
    sim, verdict = iep.evaluer_reponse_quiz("xyz123", "Utilisez la fonction print() pour afficher un message")
    assert verdict == "fausse"
    assert sim < iep.QUIZ_SEUIL_PRESQUE


@pytest.mark.parametrize(
    "ratio, verdict_attendu",
    [
        (1.0, "bonne"),
        (0.70, "bonne"),
        (0.69, "presque"),
        (0.35, "presque"),
        (0.34, "fausse"),
        (0.0, "fausse"),
    ],
)
def test_evaluer_reponse_quiz_seuils_exacts(monkeypatch, ratio, verdict_attendu):
    monkeypatch.setattr(iep, "calcul_similarite", lambda a, b: ratio)
    sim, verdict = iep.evaluer_reponse_quiz("peu importe", "peu importe")
    assert sim == int(ratio * 100)
    assert verdict == verdict_attendu


# ── _bilan_quiz ──────────────────────────────────────────────────────────────

def test_bilan_quiz_aucune_question_repondue():
    assert iep._bilan_quiz(0, 0) == "Quiz terminé. Aucune question répondue."


def test_bilan_quiz_score_partiel():
    bilan = iep._bilan_quiz(3, 4)
    assert "3/4" in bilan
    assert "75%" in bilan
    assert "Tapez 'quiz' pour rejouer." in bilan


def test_bilan_quiz_score_parfait():
    bilan = iep._bilan_quiz(5, 5)
    assert "5/5" in bilan
    assert "100%" in bilan


# ── demarrer_quiz (web) ──────────────────────────────────────────────────────

def test_demarrer_quiz_faq_vide(monkeypatch):
    monkeypatch.setattr(iep, "faq", {})
    etat, message = iep.demarrer_quiz()
    assert etat is None
    assert "indisponible" in message


def test_demarrer_quiz_construit_un_etat_valide(monkeypatch):
    monkeypatch.setattr(iep, "faq", {"Q1": "R1", "Q2": "R2"})
    monkeypatch.setattr(iep.random, "choice", lambda seq: seq[0])

    etat, message = iep.demarrer_quiz()

    assert etat == {"question": "Q1", "score": 0, "total": 0, "max": iep.QUIZ_NB_QUESTIONS}
    assert "Mode Quiz" in message
    assert f"(1/{iep.QUIZ_NB_QUESTIONS}) Q1 ?" in message
    assert "fin" in message.lower()


def test_demarrer_quiz_respecte_nb_questions_personnalise(monkeypatch):
    monkeypatch.setattr(iep, "faq", {"Q1": "R1"})
    etat, message = iep.demarrer_quiz(nb_questions=3)
    assert etat["max"] == 3
    assert "3 questions" in message
    assert "(1/3)" in message


# ── repondre_quiz (web) ──────────────────────────────────────────────────────

@pytest.mark.parametrize("mot_arret", ["fin", "EXIT", "  Quitter  "])
def test_repondre_quiz_mot_arret_termine_le_quiz(monkeypatch, mot_arret):
    monkeypatch.setattr(iep, "faq", {"Q1": "R1"})
    etat = {"question": "Q1", "score": 2, "total": 3, "max": 10}

    nouvel_etat, message = iep.repondre_quiz(etat, mot_arret)

    assert nouvel_etat is None
    assert "2/3" in message
    assert "66%" in message


def test_repondre_quiz_question_disparue_de_la_faq(monkeypatch):
    monkeypatch.setattr(iep, "faq", {"Autre question": "Autre réponse"})
    etat = {"question": "Question disparue", "score": 0, "total": 0, "max": 10}

    nouvel_etat, message = iep.repondre_quiz(etat, "une réponse")

    assert nouvel_etat is None
    assert "introuvable" in message


def test_repondre_quiz_bonne_reponse_enchaine_sur_la_suivante(monkeypatch):
    monkeypatch.setattr(iep, "faq", {"Q1": "La réponse un", "Q2": "La réponse deux"})
    monkeypatch.setattr(iep.random, "choice", lambda seq: seq[0])
    etat = {"question": "Q1", "score": 0, "total": 0, "max": 10}

    nouvel_etat, message = iep.repondre_quiz(etat, "La réponse un")

    assert nouvel_etat is not None
    assert nouvel_etat["score"] == 1
    assert nouvel_etat["total"] == 1
    assert nouvel_etat["question"] == "Q2"
    assert "✅ Bonne réponse" in message
    assert "La réponse un" in message  # réponse attendue affichée
    assert "(2/10) Q2 ?" in message


def test_repondre_quiz_mauvaise_reponse_ne_marque_pas_de_point(monkeypatch):
    monkeypatch.setattr(iep, "faq", {"Q1": "Une réponse bien précise", "Q2": "Autre chose"})
    monkeypatch.setattr(iep.random, "choice", lambda seq: seq[0])
    etat = {"question": "Q1", "score": 0, "total": 0, "max": 10}

    nouvel_etat, message = iep.repondre_quiz(etat, "zzz totalement hors sujet zzz")

    assert nouvel_etat["score"] == 0
    assert nouvel_etat["total"] == 1
    assert "❌ Pas tout à fait" in message


def test_repondre_quiz_derniere_question_termine_le_quiz(monkeypatch):
    monkeypatch.setattr(iep, "faq", {"Q1": "R1"})
    etat = {"question": "Q1", "score": 3, "total": 3, "max": 4}

    nouvel_etat, message = iep.repondre_quiz(etat, "R1")

    assert nouvel_etat is None
    assert "4/4" in message
    assert "100%" in message


def test_repondre_quiz_plus_aucune_question_disponible_termine_le_quiz(monkeypatch):
    # Simule une FAQ qui se viderait pendant la partie : choisir_question_quiz
    # renvoie None même si la question courante existe encore.
    monkeypatch.setattr(iep, "faq", {"Q1": "R1"})
    monkeypatch.setattr(iep, "choisir_question_quiz", lambda derniere_question=None: None)
    etat = {"question": "Q1", "score": 0, "total": 0, "max": 10}

    nouvel_etat, message = iep.repondre_quiz(etat, "R1")

    assert nouvel_etat is None
    assert "1/1" in message
    assert "100%" in message


def test_repondre_quiz_incremente_total_avant_de_verifier_la_fin(monkeypatch):
    monkeypatch.setattr(iep, "faq", {"Q1": "R1"})
    etat = {"question": "Q1", "score": 0, "total": 0, "max": 1}

    nouvel_etat, message = iep.repondre_quiz(etat, "réponse fausse")

    assert nouvel_etat is None
    assert "0/1" in message


# ── mode_quiz (terminal) ─────────────────────────────────────────────────────

def test_mode_quiz_faq_vide_ne_demande_aucune_saisie(monkeypatch, capsys):
    monkeypatch.setattr(iep, "faq", {})

    def input_interdit(*_args, **_kwargs):
        pytest.fail("input() ne doit pas être appelé quand la FAQ est vide")

    monkeypatch.setattr(builtins, "input", input_interdit)

    iep.mode_quiz()

    sortie = capsys.readouterr().out
    assert "indisponible" in sortie


def test_mode_quiz_arret_anticipe_avec_fin(monkeypatch, capsys):
    monkeypatch.setattr(iep, "faq", {"Q1": "La bonne réponse", "Q2": "Autre réponse"})
    monkeypatch.setattr(iep.random, "choice", lambda seq: seq[0])
    reponses = iter(["La bonne réponse", "fin"])
    monkeypatch.setattr(builtins, "input", lambda *_a, **_k: next(reponses))

    iep.mode_quiz(nb_questions_max=5)

    sortie = capsys.readouterr().out
    assert "1/1" in sortie
    assert "100%" in sortie


def test_mode_quiz_parcourt_toutes_les_questions_sans_fin(monkeypatch, capsys):
    monkeypatch.setattr(iep, "faq", {"Q1": "R1", "Q2": "R2"})
    monkeypatch.setattr(iep.random, "choice", lambda seq: seq[0])
    # 3 réponses correctes d'affilée, jamais "fin".
    reponses = iter(["R1", "R2", "R1"])
    monkeypatch.setattr(builtins, "input", lambda *_a, **_k: next(reponses))

    iep.mode_quiz(nb_questions_max=3)

    sortie = capsys.readouterr().out
    assert "3/3" in sortie
    assert "100%" in sortie


def test_mode_quiz_interruption_clavier_avant_toute_reponse(monkeypatch, capsys):
    monkeypatch.setattr(iep, "faq", {"Q1": "R1"})

    def input_interrompu(*_a, **_k):
        raise KeyboardInterrupt

    monkeypatch.setattr(builtins, "input", input_interrompu)

    iep.mode_quiz(nb_questions_max=5)

    sortie = capsys.readouterr().out
    assert "Aucune question répondue." in sortie