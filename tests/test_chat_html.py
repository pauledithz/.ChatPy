"""Tests sur l'écran d'accueil de chat.html.

L'accueil a changé de forme : c'était un paragraphe citant les commandes entre
balises <code>, c'est aujourd'hui une rangée de puces cliquables (`data-send`)
qui envoient la commande à la place de l'utilisateur. L'intention testée, elle,
n'a pas bougé : le quiz et l'aide doivent tous deux être proposés d'entrée, et
le quiz avant l'aide.

Ces tests lisent le HTML comme du texte — ils vérifient ce que la page offre,
pas comment le navigateur la rend.
"""
import os
import re
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CHAT_HTML = os.path.join(_ROOT, "chat.html")


class TestEcranDAccueilDuChat(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(_CHAT_HTML, "r", encoding="utf-8") as f:
            cls.contenu = f.read()

    def test_propose_le_quiz(self):
        """Sans cette puce, le quiz n'est découvrable qu'en devinant le mot-clé."""
        self.assertIn('data-send="quiz"', self.contenu)
        self.assertIn("Lancer un quiz", self.contenu)

    def test_propose_toujours_laide(self):
        self.assertIn('data-send="help"', self.contenu)

    def test_le_quiz_est_propose_avant_laide(self):
        index_quiz = self.contenu.index('data-send="quiz"')
        index_help = self.contenu.index('data-send="help"')
        self.assertLess(index_quiz, index_help)

    def test_les_puces_envoient_un_message_non_vide(self):
        """Une puce sans data-send exploitable ne fait rien au clic : le bouton
        serait mort sans que rien ne le signale."""
        puces = re.findall(r'class="chat-chip[^"]*"\s+data-send="([^"]*)"', self.contenu)

        self.assertGreaterEqual(len(puces), 2)
        for envoi in puces:
            self.assertTrue(envoi.strip(), "puce avec un data-send vide")

    def test_le_script_chat_js_reste_reference(self):
        self.assertIn('<script src="chat.js">', self.contenu)


if __name__ == "__main__":
    unittest.main()
