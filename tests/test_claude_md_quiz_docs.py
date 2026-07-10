"""Tests de cohérence entre CLAUDE.md et le code pour les points documentés
par cette PR : la variable d'environnement CHATPY_SECRET_KEY, le retrait de
'quiz' de COMMANDES_TERMINAL, et les fonctions du quiz partagées par le CLI
et le web.
"""
import os
import sys
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

import ia_en_python as iap

_CLAUDE_MD = os.path.join(_ROOT, "CLAUDE.md")


class TestDocumentationDuQuizDansClaudeMd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(_CLAUDE_MD, "r", encoding="utf-8") as f:
            cls.contenu = f.read()

    def test_documente_la_variable_denvironnement_de_la_cle_de_session(self):
        self.assertIn("CHATPY_SECRET_KEY", self.contenu)

    def test_ne_decrit_plus_quiz_comme_reserve_au_terminal(self):
        self.assertIn("`clear`, `historique`", self.contenu)
        self.assertNotIn("`clear`, `historique`, `quiz`", self.contenu)

    def test_precise_que_quiz_natteint_jamais_chatbot_response(self):
        self.assertIn("never reaches", self.contenu)
        self.assertIn("chatbot_response()", self.contenu)

    def test_documente_les_fonctions_du_quiz_qui_existent_reellement_dans_le_code(self):
        for nom_fonction in (
            "choisir_question_quiz",
            "evaluer_reponse_quiz",
            "demarrer_quiz",
            "repondre_quiz",
            "mode_quiz",
        ):
            self.assertIn(nom_fonction, self.contenu)
            self.assertTrue(
                hasattr(iap, nom_fonction),
                f"{nom_fonction} est documenté dans CLAUDE.md mais absent de ia_en_python.py",
            )

    def test_documente_les_seuils_de_notation_du_quiz(self):
        self.assertIn("QUIZ_SEUIL_BONNE", self.contenu)
        self.assertIn("QUIZ_SEUIL_PRESQUE", self.contenu)
        self.assertTrue(hasattr(iap, "QUIZ_SEUIL_BONNE"))
        self.assertTrue(hasattr(iap, "QUIZ_SEUIL_PRESQUE"))


if __name__ == "__main__":
    unittest.main()