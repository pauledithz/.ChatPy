"""Tests pour le changement apporté à chat.html : le message d'accueil du
chat mentionne désormais la commande 'quiz' en plus de 'help'.
"""
import os
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CHAT_HTML = os.path.join(_ROOT, "chat.html")


class TestMessageDeBienvenueDuChat(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(_CHAT_HTML, "r", encoding="utf-8") as f:
            cls.contenu = f.read()

    def test_mentionne_la_commande_quiz(self):
        self.assertIn("<code>quiz</code>", self.contenu)
        self.assertIn("tester vos connaissances", self.contenu)

    def test_mentionne_toujours_la_commande_help(self):
        self.assertIn("<code>help</code>", self.contenu)
        self.assertIn("découvrir ce que je sais faire", self.contenu)

    def test_quiz_est_mentionne_avant_help_dans_le_message(self):
        index_quiz = self.contenu.index("<code>quiz</code>")
        index_help = self.contenu.index("<code>help</code>")
        self.assertLess(index_quiz, index_help)

    def test_le_script_chat_js_reste_reference(self):
        self.assertIn('<script src="chat.js">', self.contenu)


if __name__ == "__main__":
    unittest.main()
