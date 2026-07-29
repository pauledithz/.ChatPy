"""Tests unitaires de ChatPy — exécutables sans dépendance externe :

    python3 -m unittest test_chatpy -v

Les tests qui écrivent sur disque redirigent les fichiers runtime
(.chatpy_history.json, questions_sans_reponse.json) vers un dossier temporaire :
la suite ne touche jamais aux vrais fichiers du projet.
"""

import contextlib
import io
import json
import os
import re
import tempfile
import unittest
from unittest.mock import patch

import ia_en_python as chatpy


def _confiance(reponse):
    """Extrait le pourcentage de confiance d'une réponse du bot, ou None."""
    m = re.search(r"Confiance: (\d+)%", reponse)
    return int(m.group(1)) if m else None


class TestNormalisation(unittest.TestCase):
    def test_accents_et_majuscules(self):
        self.assertEqual(chatpy.normaliser_texte("Déclarer une VARIABLE"),
                         "declarer une variable")

    def test_ponctuation_et_espaces(self):
        self.assertEqual(chatpy.normaliser_texte("  qu'est-ce   qu'une liste ?! "),
                         "qu est ce qu une liste")

    def test_contient_mot_entier_seulement(self):
        self.assertTrue(chatpy._contient_mot("bonjour!", ["bonjour"]))
        self.assertFalse(chatpy._contient_mot("bonjour", ["bon"]))

    def test_mots_significatifs_filtre_les_mots_vides(self):
        mots = chatpy._mots_significatifs("comment faire une boucle en python")
        self.assertEqual(mots, {"boucle", "python"})


class TestMatchingFAQ(unittest.TestCase):
    def test_correspondance_exacte(self):
        reponse = chatpy.chatbot_response("qu'est-ce qu'une variable")
        self.assertEqual(_confiance(reponse), 100)
        self.assertIn("espace de stockage", reponse)

    def test_tolere_les_fautes_de_frappe(self):
        reponse = chatpy.chatbot_response("coment declarer une varaible")
        self.assertIsNotNone(_confiance(reponse))
        self.assertIn("nom de la variable", reponse)

    def test_tolere_les_reformulations(self):
        reponse = chatpy.chatbot_response("c'est quoi une liste")
        self.assertIsNotNone(_confiance(reponse))
        self.assertIn("structure de données", reponse)

    def test_question_au_sens_oppose_n_est_pas_sure_d_elle(self):
        # "supprimer une variable" n'est pas dans la FAQ ; la question la plus
        # proche lettre à lettre ("déclarer une variable") dit le contraire.
        # Le bot peut proposer quelque chose, mais jamais avec ≥ 70% de confiance.
        reponse = chatpy.chatbot_response("comment supprimer une variable")
        confiance = _confiance(reponse)
        if confiance is not None:
            self.assertLess(confiance, 70)
            self.assertIn("D'autres réponses possibles", reponse)

    def test_salutation(self):
        self.assertIn("Bonjour", chatpy.chatbot_response("bonjour"))

    def test_fallback_loggue_la_question(self):
        with tempfile.TemporaryDirectory() as tmp:
            journal = os.path.join(tmp, "questions.json")
            with patch.object(chatpy, "QUESTIONS_SANS_REPONSE_FILE", journal):
                reponse = chatpy.chatbot_response("comment dresser un lama sauvage")
            self.assertIn("je ne comprends pas", reponse)
            with open(journal, encoding="utf-8") as f:
                donnees = json.load(f)
            self.assertIn("comment dresser un lama sauvage", donnees)
            self.assertEqual(donnees["comment dresser un lama sauvage"]["occurrences"], 1)

    def test_questions_proches_rattrapent_un_echec(self):
        # Sous le seuil de réponse mais sur le même sujet : à proposer.
        proches = chatpy.questions_proches("comment supprimer une variable")
        self.assertTrue(proches)
        self.assertTrue(all(p in chatpy.faq for p in proches))

    def test_questions_proches_ignorent_le_hors_sujet(self):
        # La ressemblance des seules lettres ferait remonter "décompresser un
        # tuple" : sans mot de sujet commun, on ne propose rien.
        self.assertEqual(chatpy.questions_proches("comment dresser un lama sauvage"), [])

    def test_filtre_du_journal(self):
        self.assertFalse(chatpy._vaut_la_peine_d_etre_logguee("quoi"))
        self.assertFalse(chatpy._vaut_la_peine_d_etre_logguee("x " * 3000))
        self.assertTrue(chatpy._vaut_la_peine_d_etre_logguee("comment installer numpy"))


class TestCommandes(unittest.TestCase):
    def test_help(self):
        self.assertIn("Commandes disponibles", chatpy.chatbot_response("help"))

    def test_liste(self):
        reponse = chatpy.chatbot_response("liste")
        for categorie in chatpy.faq_categories:
            self.assertIn(categorie, reponse)

    def test_cherche(self):
        self.assertIn("trier", chatpy.chatbot_response("cherche trier"))

    def test_aide_sujet_connu(self):
        if not chatpy.aide_concepts:
            self.skipTest("aide_concepts.json non chargé")
        sujet = next(iter(chatpy.aide_concepts))
        self.assertIn("📖", chatpy.chatbot_response(f"aide {sujet}"))

    def test_aide_sujet_trop_court_ne_matche_pas_par_sous_chaine(self):
        # "e" est une sous-chaîne de presque tous les mots-clés : la réponse ne
        # doit pas être le premier concept venu.
        reponse = chatpy.chatbot_response("aide e")
        self.assertIn("introuvable", reponse)

    def test_commande_terminal_expliquee_au_web(self):
        # Les deux moitiés du message comptent : ne marche pas ici (web),
        # marche dans le terminal. Une formulation inversée doit échouer.
        reponse = chatpy.chatbot_response("clear")
        self.assertIn("chat web", reponse)
        self.assertIn("version terminal", reponse)
        self.assertLess(
            reponse.index("chat web"),
            reponse.index("version terminal"),
        )


class TestQuiz(unittest.TestCase):
    def test_reponse_exacte_est_bonne(self):
        question, attendue = next(iter(chatpy.faq.items()))
        sim, verdict = chatpy.evaluer_reponse_quiz(attendue, attendue)
        self.assertEqual(verdict, "bonne")
        self.assertGreaterEqual(sim, chatpy.QUIZ_SEUIL_BONNE)

    def test_les_bons_mots_cles_suffisent(self):
        attendue = "Utilisez append().\nExemple :\nma_liste.append(4)"
        sim, verdict = chatpy.evaluer_reponse_quiz("avec append", attendue)
        self.assertEqual(verdict, "bonne")

    def test_reponse_hors_sujet_est_fausse(self):
        attendue = "Utilisez append().\nExemple :\nma_liste.append(4)"
        sim, verdict = chatpy.evaluer_reponse_quiz("aucune idée du tout", attendue)
        self.assertEqual(verdict, "fausse")

    def test_quiz_web_demarrage_et_bonne_reponse(self):
        etat, message = chatpy.demarrer_quiz()
        self.assertIsNotNone(etat)
        self.assertIn(etat["question"], chatpy.faq)
        self.assertIn("(1/", message)

        etat, message = chatpy.repondre_quiz(etat, chatpy.faq[etat["question"]])
        self.assertIn("✅", message)

    def test_quiz_web_arret_anticipe(self):
        etat, _ = chatpy.demarrer_quiz()
        etat, message = chatpy.repondre_quiz(etat, "fin")
        self.assertIsNone(etat)
        self.assertIn("Quiz terminé", message)

    def test_quiz_web_arret_apres_une_reponse_affiche_le_score(self):
        etat, _ = chatpy.demarrer_quiz()
        etat, _ = chatpy.repondre_quiz(etat, chatpy.faq[etat["question"]])
        etat, message = chatpy.repondre_quiz(etat, "fin")
        self.assertIsNone(etat)
        self.assertIn("Score final : 1/1", message)

    def test_choisir_question_ne_repose_pas_la_meme(self):
        question, _ = chatpy.choisir_question_quiz()
        for _ in range(20):
            suivante, _ = chatpy.choisir_question_quiz(question)
            self.assertNotEqual(suivante, question)


class TestSuggestions(unittest.TestCase):
    """repondre() sort les suggestions du texte pour que le web en fasse des boutons."""

    def _repondre(self, message):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(chatpy, "HISTORY_FILE", os.path.join(tmp, "h.json")), \
                 patch.object(chatpy, "QUESTIONS_SANS_REPONSE_FILE", os.path.join(tmp, "j.json")):
                return chatpy.ChatBot().repondre(message)

    def test_reponse_trouvee_propose_les_questions_liees(self):
        resultat = self._repondre("qu'est-ce qu'une fonction")
        self.assertIn("Confiance:", resultat["response"])
        self.assertTrue(resultat["suggestions"])
        self.assertEqual(resultat["titre_suggestions"], chatpy.TITRE_QUESTIONS_LIEES)
        # Le texte reste propre : les suggestions ne doivent pas y être recopiées.
        for sug in resultat["suggestions"]:
            self.assertNotIn(sug, resultat["response"])

    def test_echec_propose_les_questions_proches(self):
        resultat = self._repondre("comment supprimer une variable en python")
        if resultat["response"] == chatpy.REPONSE_INCOMPRISE:
            self.assertEqual(resultat["titre_suggestions"], chatpy.TITRE_QUESTIONS_PROCHES)
            self.assertTrue(resultat["suggestions"])

    def test_sans_suggestion_le_titre_reste_vide(self):
        resultat = self._repondre("comment dresser un lama sauvage")
        self.assertEqual(resultat["response"], chatpy.REPONSE_INCOMPRISE)
        self.assertEqual(resultat["suggestions"], [])
        self.assertEqual(resultat["titre_suggestions"], "")

    def test_traiter_message_remet_les_suggestions_en_texte(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(chatpy, "HISTORY_FILE", os.path.join(tmp, "h.json")):
                texte = chatpy.ChatBot().traiter_message("qu'est-ce qu'une fonction")
        self.assertIn(f"📌 {chatpy.TITRE_QUESTIONS_LIEES}:", texte)
        self.assertIn("1. ", texte)


class TestJournalDesLacunes(unittest.TestCase):
    def test_pouce_bas_compte_a_part_des_questions_sans_reponse(self):
        with tempfile.TemporaryDirectory() as tmp:
            journal = os.path.join(tmp, "questions.json")
            with patch.object(chatpy, "QUESTIONS_SANS_REPONSE_FILE", journal):
                # Une question qui a bien reçu une réponse, mais jugée inutile.
                chatpy.signaler_reponse_inutile("comment trier une liste")
                chatpy.signaler_reponse_inutile("comment trier une liste")
            with open(journal, encoding="utf-8") as f:
                entree = json.load(f)["comment trier une liste"]
        self.assertEqual(entree["pouces_bas"], 2)
        # Elle n'a jamais été « sans réponse » : ce compteur-là reste à zéro.
        self.assertEqual(entree["occurrences"], 0)

    def test_pouce_bas_sur_une_entree_ancienne_sans_le_champ(self):
        with tempfile.TemporaryDirectory() as tmp:
            journal = os.path.join(tmp, "questions.json")
            # Format d'avant l'ajout des pouces : pas de clé "pouces_bas".
            with open(journal, "w", encoding="utf-8") as f:
                json.dump({"comment installer numpy": {
                    "texte": "comment installer numpy",
                    "occurrences": 3,
                    "derniere_fois": "2026-01-01"}}, f)
            with patch.object(chatpy, "QUESTIONS_SANS_REPONSE_FILE", journal):
                chatpy.signaler_reponse_inutile("comment installer numpy")
            with open(journal, encoding="utf-8") as f:
                entree = json.load(f)["comment installer numpy"]
        self.assertEqual(entree["pouces_bas"], 1)
        self.assertEqual(entree["occurrences"], 3)

    def test_pouce_bas_filtre_le_bruit(self):
        with tempfile.TemporaryDirectory() as tmp:
            journal = os.path.join(tmp, "questions.json")
            with patch.object(chatpy, "QUESTIONS_SANS_REPONSE_FILE", journal):
                chatpy.signaler_reponse_inutile("help")
            self.assertFalse(os.path.exists(journal))


class TestPersistance(unittest.TestCase):
    def test_ecriture_atomique(self):
        with tempfile.TemporaryDirectory() as tmp:
            chemin = os.path.join(tmp, "donnees.json")
            chatpy._ecrire_json_atomique(chemin, {"clé": "valeur"})
            with open(chemin, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"clé": "valeur"})
            # aucun fichier temporaire orphelin ne doit rester
            self.assertEqual(os.listdir(tmp), ["donnees.json"])

    def test_traiter_message_ecrit_l_historique(self):
        with tempfile.TemporaryDirectory() as tmp:
            historique = os.path.join(tmp, "historique.json")
            with patch.object(chatpy, "HISTORY_FILE", historique):
                bot = chatpy.ChatBot()
                bot.traiter_message("qu'est-ce qu'une variable")
                with open(historique, encoding="utf-8") as f:
                    donnees = json.load(f)
            self.assertEqual(len(donnees), 2)
            self.assertEqual(donnees[0]["role"], "utilisateur")
            self.assertEqual(donnees[1]["role"], "assistant")

    def test_historique_plafonne(self):
        with tempfile.TemporaryDirectory() as tmp:
            historique = os.path.join(tmp, "historique.json")
            with patch.object(chatpy, "HISTORY_FILE", historique):
                bot = chatpy.ChatBot()
                bot.historique = [{"role": "utilisateur", "message": str(i)}
                                  for i in range(chatpy.HISTORIQUE_MAX_MESSAGES + 50)]
                with chatpy._verrou_historique:
                    bot._sauvegarder_historique()
                with open(historique, encoding="utf-8") as f:
                    donnees = json.load(f)
            self.assertEqual(len(donnees), chatpy.HISTORIQUE_MAX_MESSAGES)

    def test_historique_corrompu_mis_de_cote(self):
        with tempfile.TemporaryDirectory() as tmp:
            historique = os.path.join(tmp, "historique.json")
            with open(historique, "w", encoding="utf-8") as f:
                f.write("{pas du json")
            # L'avertissement est destiné à l'utilisateur du CLI : on le capture
            # pour ne pas polluer la sortie de la suite, et on vérifie son contenu.
            sortie = io.StringIO()
            with patch.object(chatpy, "HISTORY_FILE", historique):
                with contextlib.redirect_stdout(sortie):
                    bot = chatpy.ChatBot()
            self.assertEqual(bot.historique, [])
            self.assertTrue(os.path.exists(historique + ".corrompu"))
            self.assertIn("historique.json.corrompu", sortie.getvalue())


if __name__ == "__main__":
    unittest.main()
