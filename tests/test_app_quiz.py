"""Tests pour les changements apportés à app.py par cette PR :

- app.secret_key est lu depuis CHATPY_SECRET_KEY, avec repli sur une clé
  aléatoire (secrets.token_hex(32)) si la variable n'est pas définie.
- /api/chat route désormais les messages vers demarrer_quiz()/repondre_quiz()
  quand un quiz est actif ou démarré, en conservant l'état dans la session
  Flask, et ne retombe sur bot.traiter_message() que hors quiz.

Les routes non modifiées par cette PR (`/`, `/chat`, fichiers publics) ne sont
pas retestées ici.
"""
import importlib
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app as app_module
import ia_en_python as iap


class TestSecretKeyConfiguration(unittest.TestCase):
    def tearDown(self):
        # Recharger avec l'environnement réel pour ne pas polluer les autres tests.
        importlib.reload(app_module)

    def test_utilise_la_cle_fournie_par_lenvironnement(self):
        with mock.patch.dict(os.environ, {"CHATPY_SECRET_KEY": "cle-fixe-de-test"}):
            importlib.reload(app_module)
            self.assertEqual(app_module.app.secret_key, "cle-fixe-de-test")

    def test_genere_une_cle_aleatoire_si_absente_de_lenvironnement(self):
        valeur_initiale = os.environ.pop("CHATPY_SECRET_KEY", None)
        try:
            # app.py charge aussi .env : sans neutraliser ce chargement, la clé
            # du fichier local reviendrait et le test ne mesurerait plus
            # l'absence de configuration.
            with mock.patch("dotenv.load_dotenv", return_value=False):
                importlib.reload(app_module)
                cle_1 = app_module.app.secret_key
                importlib.reload(app_module)
                cle_2 = app_module.app.secret_key
        finally:
            if valeur_initiale is not None:
                os.environ["CHATPY_SECRET_KEY"] = valeur_initiale

        self.assertIsInstance(cle_1, str)
        self.assertEqual(len(cle_1), 64)  # secrets.token_hex(32) -> 64 caractères hexadécimaux
        # Deux rechargements sans clé fixe doivent générer deux clés différentes.
        self.assertNotEqual(cle_1, cle_2)


class TestAppImportsQuizHelpers(unittest.TestCase):
    def test_importe_les_memes_fonctions_que_ia_en_python(self):
        self.assertIs(app_module.demarrer_quiz, iap.demarrer_quiz)
        self.assertIs(app_module.repondre_quiz, iap.repondre_quiz)
        self.assertIs(app_module.bot, iap.bot)


class TestApiChatQuizRouting(unittest.TestCase):
    def setUp(self):
        self.client = app_module.app.test_client()

    def test_message_quiz_demarre_une_session_et_ne_touche_pas_au_bot(self):
        etat_initial = {"question": "Q1", "score": 0, "total": 0, "max": 10}
        with mock.patch.object(app_module, "demarrer_quiz", return_value=(etat_initial, "🎯 Mode Quiz")) as demarrer_mock, \
             mock.patch.object(app_module, "repondre_quiz") as repondre_mock, \
             mock.patch.object(app_module.bot, "repondre") as bot_mock:
            with self.client as client:
                resp = client.post("/api/chat", json={"message": "quiz"})
                self.assertEqual(resp.status_code, 200)
                # Une correction de quiz n'est pas un extrait de la FAQ : ni
                # suggestion de suivi, ni pouce possible.
                self.assertEqual(resp.get_json(), {
                    "response": "🎯 Mode Quiz",
                    "suggestions": [],
                    "titre_suggestions": "",
                    "feedback_possible": False,
                    "quiz_actif": True,
                })
                with client.session_transaction() as sess:
                    self.assertEqual(sess["quiz"], etat_initial)

        demarrer_mock.assert_called_once_with()
        repondre_mock.assert_not_called()
        bot_mock.assert_not_called()

    def test_message_quiz_insensible_a_la_casse_et_aux_espaces(self):
        etat_initial = {"question": "Q1", "score": 0, "total": 0, "max": 10}
        with mock.patch.object(app_module, "demarrer_quiz", return_value=(etat_initial, "message")) as demarrer_mock:
            with self.client as client:
                resp = client.post("/api/chat", json={"message": "  QUIZ  "})
                self.assertEqual(resp.status_code, 200)
        demarrer_mock.assert_called_once_with()

    def test_reponse_pendant_un_quiz_en_cours_utilise_repondre_quiz(self):
        etat_courant = {"question": "Q1", "score": 0, "total": 0, "max": 10}
        etat_suivant = {"question": "Q2", "score": 1, "total": 1, "max": 10}
        with self.client as client:
            with client.session_transaction() as sess:
                sess["quiz"] = etat_courant

            with mock.patch.object(app_module, "repondre_quiz", return_value=(etat_suivant, "suite du quiz")) as repondre_mock, \
                 mock.patch.object(app_module, "demarrer_quiz") as demarrer_mock, \
                 mock.patch.object(app_module.bot, "repondre") as bot_mock:
                resp = client.post("/api/chat", json={"message": "une liste"})

            self.assertEqual(resp.get_json(), {
                "response": "suite du quiz",
                "suggestions": [],
                "titre_suggestions": "",
                "feedback_possible": False,
                "quiz_actif": True,
            })
            repondre_mock.assert_called_once_with(etat_courant, "une liste")
            demarrer_mock.assert_not_called()
            bot_mock.assert_not_called()

            with client.session_transaction() as sess:
                self.assertEqual(sess["quiz"], etat_suivant)

    def test_fin_de_quiz_efface_letat_de_la_session(self):
        etat_courant = {"question": "Q1", "score": 2, "total": 4, "max": 10}
        with self.client as client:
            with client.session_transaction() as sess:
                sess["quiz"] = etat_courant

            with mock.patch.object(app_module, "repondre_quiz", return_value=(None, "bilan final")):
                resp = client.post("/api/chat", json={"message": "fin"})

            # Le message qui clôt le quiz annonce déjà quiz_actif=False, d'où
            # feedback_possible : sans lui le front ne saurait pas que ce
            # message-là n'est pas une réponse de la FAQ.
            self.assertEqual(resp.get_json(), {
                "response": "bilan final",
                "suggestions": [],
                "titre_suggestions": "",
                "feedback_possible": False,
                "quiz_actif": False,
            })
            with client.session_transaction() as sess:
                self.assertNotIn("quiz", sess)

    def test_message_normal_sans_quiz_actif_utilise_le_bot(self):
        # bot.repondre() — et non traiter_message() — est l'entrée partagée par
        # les deux front-ends : elle garde les suggestions à part du texte pour
        # que le web en fasse des boutons cliquables.
        reponse_bot = {"response": "réponse du bot",
                       "suggestions": ["une autre question"],
                       "titre_suggestions": "Questions liées"}
        with mock.patch.object(app_module.bot, "repondre", return_value=reponse_bot) as bot_mock, \
             mock.patch.object(app_module, "demarrer_quiz") as demarrer_mock, \
             mock.patch.object(app_module, "repondre_quiz") as repondre_mock:
            with self.client as client:
                resp = client.post("/api/chat", json={"message": "qu'est-ce qu'une fonction"})
                self.assertEqual(resp.get_json(), {
                    "response": "réponse du bot",
                    "suggestions": ["une autre question"],
                    "titre_suggestions": "Questions liées",
                    "feedback_possible": True,
                    "quiz_actif": False,
                })
                with client.session_transaction() as sess:
                    self.assertNotIn("quiz", sess)

        bot_mock.assert_called_once_with("qu'est-ce qu'une fonction", sensibilite="")
        demarrer_mock.assert_not_called()
        repondre_mock.assert_not_called()

    def test_repondre_quiz_qui_garde_letat_conserve_la_session(self):
        etat_courant = {"question": "Q1", "score": 0, "total": 0, "max": 10}
        etat_suivant = {"question": "Q1", "score": 0, "total": 1, "max": 10}
        with self.client as client:
            with client.session_transaction() as sess:
                sess["quiz"] = etat_courant

            with mock.patch.object(app_module, "repondre_quiz", return_value=(etat_suivant, "encore")):
                client.post("/api/chat", json={"message": "mauvaise reponse"})

            with client.session_transaction() as sess:
                self.assertIn("quiz", sess)
                self.assertEqual(sess["quiz"], etat_suivant)


if __name__ == "__main__":
    unittest.main()