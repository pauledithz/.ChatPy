"""Tests pour la page chat.html : elle doit annoncer la commande 'quiz'.

Il n'y a pas de framework de test JS dans ce dépôt (pas de package.json), donc
on vérifie le contenu statique du gabarit, cohérent avec les autres tests
Python du projet.
"""
import os

CHAT_HTML_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "chat.html")


def _lire_chat_html():
    with open(CHAT_HTML_PATH, "r", encoding="utf-8") as f:
        return f.read()


def test_message_bienvenue_mentionne_la_commande_quiz():
    contenu = _lire_chat_html()
    assert "<code>quiz</code>" in contenu
    assert "tester vos connaissances" in contenu


def test_message_bienvenue_mentionne_toujours_la_commande_help():
    contenu = _lire_chat_html()
    assert "<code>help</code>" in contenu


def test_quiz_est_mentionne_avant_help_dans_le_message_de_bienvenue():
    contenu = _lire_chat_html()
    index_quiz = contenu.index("<code>quiz</code>")
    index_help = contenu.index("<code>help</code>")
    assert index_quiz < index_help