"""Tests pour les fonctionnalités de quiz introduites/refactorées dans ia_en_python.py.

Portée : uniquement le code touché par cette PR (constantes du quiz,
choisir_question_quiz, evaluer_reponse_quiz, _bilan_quiz, demarrer_quiz,
repondre_quiz, mode_quiz, et le retrait de "quiz" de COMMANDES_TERMINAL).
Le reste de chatbot_response() / ChatBot n'est pas modifié par cette PR et
n'est donc pas retesté ici.
"""
import io
import os
import sys
import unittest
from contextlib import redirect_stdout
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ia_en_python as iap


class TestConstantesQuiz(unittest.TestCase):
    def test_quiz_nest_plus_une_commande_terminal(self):
        # Avant cette PR, "quiz" faisait partie de COMMANDES_TERMINAL. Il est
        # désormais géré identiquement par les deux front-ends, donc retiré
        # de cette liste réservée au terminal.
        self.assertNotIn("quiz", iap.COMMANDES_TERMINAL)
        self.assertEqual(iap.COMMANDES_TERMINAL, ("clear", "historique"))

    def test_constantes_de_reglage_du_quiz(self):
        self.assertEqual(iap.QUIZ_NB_QUESTIONS, 10)
        self.assertEqual(iap.QUIZ_MOTS_ARRET, ("fin", "exit", "quitter"))
        self.assertEqual(iap.QUIZ_SEUIL_BONNE, 70)
        self.assertEqual(iap.QUIZ_SEUIL_PRESQUE, 35)


class TestChatbotResponseNeGereplusQuiz(unittest.TestCase):
    def test_quiz_ne_declenche_plus_le_message_reserve_au_terminal(self):
        # Avant la PR, chatbot_response("quiz") renvoyait le message
        # "n'existe que dans la version terminal" car "quiz" était dans
        # COMMANDES_TERMINAL. Le web gère maintenant "quiz" lui-même, donc ce
        # message ne doit plus apparaître ici.
        reponse = iap.chatbot_response("quiz")
        self.assertNotIn("n'existe que dans la version terminal", reponse)


class TestChoisirQuestionQuiz(unittest.TestCase):
    def test_faq_vide_renvoie_none(self):
        with mock.patch.object(iap, "faq", {}):
            self.assertIsNone(iap.choisir_question_quiz())
            self.assertIsNone(iap.choisir_question_quiz("une question"))

    def test_une_seule_question_est_renvoyee_meme_si_deja_posee(self):
        with mock.patch.object(iap, "faq", {"Q1": "A1"}):
            self.assertEqual(iap.choisir_question_quiz(), ("Q1", "A1"))
            self.assertEqual(iap.choisir_question_quiz("Q1"), ("Q1", "A1"))

    def test_exclut_la_derniere_question_si_une_alternative_existe(self):
        with mock.patch.object(iap, "faq", {"Q1": "A1", "Q2": "A2"}):
            for _ in range(20):
                self.assertEqual(iap.choisir_question_quiz("Q1"), ("Q2", "A2"))

    def test_sans_derniere_question_le_tirage_couvre_toute_la_faq(self):
        with mock.patch.object(iap, "faq", {"Q1": "A1", "Q2": "A2"}):
            vus = {iap.choisir_question_quiz()[0] for _ in range(30)}
        self.assertEqual(vus, {"Q1", "Q2"})


class TestEvaluerReponseQuiz(unittest.TestCase):
    def _evaluer(self, similarite):
        # Le score retient max(similarité du texte, précision des mots-clés) :
        # des mots sans rapport gardent la précision à 0 pour que seule
        # la similarité simulée décide du verdict.
        with mock.patch.object(iap, "calcul_similarite", return_value=similarite):
            return iap.evaluer_reponse_quiz("granite", "papillon")

    def test_seuil_bonne_inclusif(self):
        self.assertEqual(self._evaluer(0.70), (70, "bonne"))

    def test_juste_sous_le_seuil_bonne_est_presque(self):
        sim, verdict = self._evaluer(0.699)
        self.assertEqual(verdict, "presque")
        self.assertEqual(sim, 69)

    def test_seuil_presque_inclusif(self):
        self.assertEqual(self._evaluer(0.35), (35, "presque"))

    def test_juste_sous_le_seuil_presque_est_fausse(self):
        sim, verdict = self._evaluer(0.349)
        self.assertEqual(verdict, "fausse")
        self.assertEqual(sim, 34)

    def test_similarite_nulle_est_fausse(self):
        self.assertEqual(self._evaluer(0.0), (0, "fausse"))

    def test_similarite_maximale_est_bonne(self):
        self.assertEqual(self._evaluer(1.0), (100, "bonne"))

    def test_reponses_identiques_apres_normalisation_sont_bonnes(self):
        sim, verdict = iap.evaluer_reponse_quiz("Une Liste", "une liste")
        self.assertEqual(verdict, "bonne")
        self.assertEqual(sim, 100)


class TestBilanQuiz(unittest.TestCase):
    def test_aucune_question_repondue(self):
        self.assertEqual(iap._bilan_quiz(0, 0), "Quiz terminé. Aucune question répondue.")

    def test_score_partiel(self):
        message = iap._bilan_quiz(5, 10)
        self.assertIn("5/10", message)
        self.assertIn("50%", message)
        self.assertIn("Tapez 'quiz' pour rejouer.", message)

    def test_score_parfait(self):
        message = iap._bilan_quiz(3, 3)
        self.assertIn("3/3", message)
        self.assertIn("100%", message)

    def test_score_nul_avec_questions_repondues(self):
        message = iap._bilan_quiz(0, 4)
        self.assertIn("0/4", message)
        self.assertIn("0%", message)


class TestDemarrerQuiz(unittest.TestCase):
    def test_faq_vide_renvoie_etat_none_et_message_explicite(self):
        with mock.patch.object(iap, "choisir_question_quiz", return_value=None):
            etat, message = iap.demarrer_quiz()
        self.assertIsNone(etat)
        self.assertIn("indisponible", message)

    def test_ouvre_un_etat_initial_valide(self):
        with mock.patch.object(iap, "choisir_question_quiz", return_value=("Q1", "A1")):
            etat, message = iap.demarrer_quiz(nb_questions=5)
        self.assertEqual(etat, {"question": "Q1", "score": 0, "total": 0, "max": 5})
        self.assertIn("5 questions", message)
        self.assertIn("Tapez 'fin'", message)
        self.assertIn("(1/5) Q1 ?", message)

    def test_utilise_le_nombre_de_questions_par_defaut(self):
        with mock.patch.object(iap, "choisir_question_quiz", return_value=("Q1", "A1")):
            etat, _ = iap.demarrer_quiz()
        self.assertEqual(etat["max"], iap.QUIZ_NB_QUESTIONS)


class TestRepondreQuiz(unittest.TestCase):
    def setUp(self):
        self.etat = {"question": "Q1", "score": 0, "total": 0, "max": 3}

    def test_mot_darret_termine_le_quiz_sans_evaluer_la_reponse(self):
        for mot in ("fin", "EXIT", " quitter "):
            etat = {"question": "Q1", "score": 2, "total": 4, "max": 10}
            with mock.patch.object(iap, "evaluer_reponse_quiz") as evaluer_mock:
                nouvel_etat, message = iap.repondre_quiz(etat, mot)
            evaluer_mock.assert_not_called()
            self.assertIsNone(nouvel_etat)
            self.assertEqual(message, iap._bilan_quiz(2, 4))

    def test_question_disparue_de_la_faq_interrompt_le_quiz(self):
        with mock.patch.object(iap, "faq", {}):
            nouvel_etat, message = iap.repondre_quiz(self.etat, "une reponse")
        self.assertIsNone(nouvel_etat)
        self.assertIn("interrompu", message)

    def test_bonne_reponse_incremente_le_score_et_enchaine(self):
        with mock.patch.object(iap, "faq", {"Q1": "La reponse", "Q2": "Autre reponse"}), \
             mock.patch.object(iap, "evaluer_reponse_quiz", return_value=(95, "bonne")), \
             mock.patch.object(iap, "choisir_question_quiz", return_value=("Q2", "Autre reponse")):
            nouvel_etat, message = iap.repondre_quiz(self.etat, "la reponse")

        self.assertEqual(nouvel_etat, {"question": "Q2", "score": 1, "total": 1, "max": 3})
        self.assertIn("✅ Bonne réponse ! (similarité : 95%)", message)
        self.assertIn("💡 Réponse attendue :\nLa reponse", message)
        self.assertIn("❓ (2/3) Q2 ?", message)

    def test_reponse_presque_juste_nincremente_pas_le_score(self):
        with mock.patch.object(iap, "faq", {"Q1": "La reponse", "Q2": "Autre reponse"}), \
             mock.patch.object(iap, "evaluer_reponse_quiz", return_value=(50, "presque")), \
             mock.patch.object(iap, "choisir_question_quiz", return_value=("Q2", "Autre reponse")):
            nouvel_etat, message = iap.repondre_quiz(self.etat, "presque bon")

        self.assertEqual(nouvel_etat["score"], 0)
        self.assertEqual(nouvel_etat["total"], 1)
        self.assertIn("⚠️ Presque ! (similarité : 50%)", message)

    def test_mauvaise_reponse_nincremente_pas_le_score(self):
        with mock.patch.object(iap, "faq", {"Q1": "La reponse", "Q2": "Autre reponse"}), \
             mock.patch.object(iap, "evaluer_reponse_quiz", return_value=(5, "fausse")), \
             mock.patch.object(iap, "choisir_question_quiz", return_value=("Q2", "Autre reponse")):
            nouvel_etat, message = iap.repondre_quiz(self.etat, "n'importe quoi")

        self.assertEqual(nouvel_etat["score"], 0)
        self.assertIn("❌ Pas tout à fait. (similarité : 5%)", message)

    def test_derniere_question_du_quiz_renvoie_le_bilan_final(self):
        etat = {"question": "Q1", "score": 1, "total": 2, "max": 3}
        with mock.patch.object(iap, "faq", {"Q1": "La reponse"}), \
             mock.patch.object(iap, "evaluer_reponse_quiz", return_value=(90, "bonne")):
            nouvel_etat, message = iap.repondre_quiz(etat, "la reponse")

        self.assertIsNone(nouvel_etat)
        self.assertIn(iap._bilan_quiz(2, 3), message)
        self.assertNotIn("❓ (", message)

    def test_plus_aucune_question_disponible_termine_le_quiz_avant_le_max(self):
        with mock.patch.object(iap, "faq", {"Q1": "La reponse"}), \
             mock.patch.object(iap, "evaluer_reponse_quiz", return_value=(90, "bonne")), \
             mock.patch.object(iap, "choisir_question_quiz", return_value=None):
            nouvel_etat, message = iap.repondre_quiz(self.etat, "la reponse")

        self.assertIsNone(nouvel_etat)
        self.assertIn(iap._bilan_quiz(1, 1), message)


class TestModeQuiz(unittest.TestCase):
    def test_affiche_un_message_si_la_faq_est_vide(self):
        with mock.patch.object(iap, "choisir_question_quiz", return_value=None), \
             mock.patch("builtins.input") as input_mock:
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                iap.mode_quiz()
        input_mock.assert_not_called()
        self.assertIn("indisponible", buffer.getvalue())

    def test_arret_immediat_sur_mot_darret(self):
        with mock.patch.object(iap, "choisir_question_quiz", return_value=("Q1", "A1")), \
             mock.patch("builtins.input", return_value="fin"):
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                iap.mode_quiz(nb_questions_max=5)
        self.assertIn("Aucune question répondue", buffer.getvalue())

    def test_calcule_le_score_sur_plusieurs_questions(self):
        tirages = [("Q1", "A1"), ("Q2", "A2")]
        with mock.patch.object(iap, "choisir_question_quiz", side_effect=tirages), \
             mock.patch.object(iap, "evaluer_reponse_quiz", return_value=(90, "bonne")), \
             mock.patch("builtins.input", side_effect=["bonne reponse", "fin"]):
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                iap.mode_quiz(nb_questions_max=5)
        self.assertIn("Score final : 1/1 (100%)", buffer.getvalue())

    def test_sarrete_naturellement_quand_plus_de_question_disponible(self):
        with mock.patch.object(iap, "choisir_question_quiz", side_effect=[("Q1", "A1"), None]), \
             mock.patch.object(iap, "evaluer_reponse_quiz", return_value=(10, "fausse")), \
             mock.patch("builtins.input", return_value="mauvaise reponse"):
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                iap.mode_quiz(nb_questions_max=5)
        self.assertIn("Score final : 0/1 (0%)", buffer.getvalue())


if __name__ == "__main__":
    unittest.main()