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

    def test_une_reformulation_donne_les_memes_suggestions(self):
        """Le défaut d'origine : les suggestions étaient cherchées à partir du
        message tapé, donc la formulation exacte du dictionnaire `relations`
        était exigée. « c'est quoi une liste » ne proposait rien."""
        canonique = self._repondre("qu'est-ce qu'une liste")
        reformule = self._repondre("c'est quoi une liste")

        self.assertTrue(reformule["suggestions"])
        self.assertEqual(reformule["suggestions"], canonique["suggestions"])

    def test_une_faute_de_frappe_donne_les_memes_suggestions(self):
        canonique = self._repondre("comment trier une liste")
        avec_faute = self._repondre("coment trier une list")

        self.assertTrue(avec_faute["suggestions"])
        self.assertEqual(avec_faute["suggestions"], canonique["suggestions"])

    def test_toute_question_de_la_faq_a_des_suggestions(self):
        """Le dictionnaire `relations` n'en couvre que cinq ; le repli sur les
        voisines de catégorie doit couvrir les cinquante autres."""
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(chatpy, "HISTORY_FILE", os.path.join(tmp, "h.json")):
                bot = chatpy.ChatBot()
        sans = [q for q in chatpy.faq if not bot.obtenir_suggestions(q)]
        self.assertEqual(sans, [])

    def test_une_suggestion_est_toujours_une_vraie_question_de_la_faq(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(chatpy, "HISTORY_FILE", os.path.join(tmp, "h.json")):
                bot = chatpy.ChatBot()
        for question in chatpy.faq:
            for suggestion in bot.obtenir_suggestions(question):
                self.assertIn(suggestion, chatpy.faq)
                # Reproposer la question à laquelle on vient de répondre serait
                # la plus visible des absurdités.
                self.assertNotEqual(suggestion, question)

    def test_les_relations_ecrites_a_la_main_priment(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(chatpy, "HISTORY_FILE", os.path.join(tmp, "h.json")):
                bot = chatpy.ChatBot()
        for source, attendues in bot.relations.items():
            self.assertEqual(bot.obtenir_suggestions(source), attendues[:2], source)

    def test_toutes_les_cles_de_relations_existent_dans_la_faq(self):
        """Une clé mal orthographiée ne déclencherait jamais, sans rien dire :
        le repli sur la catégorie masquerait la panne."""
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(chatpy, "HISTORY_FILE", os.path.join(tmp, "h.json")):
                bot = chatpy.ChatBot()
        connues = {chatpy.normaliser_texte(q) for q in chatpy.faq}
        for source, liees in bot.relations.items():
            self.assertIn(chatpy.normaliser_texte(source), connues, source)
            for q in liees:
                self.assertIn(q, chatpy.faq, q)

    def test_trace_designe_la_question_retenue(self):
        trace = {}
        chatpy.chatbot_response("c'est quoi une liste", trace=trace)
        self.assertEqual(trace["question"], "qu'est-ce qu'une liste")

    def test_trace_reste_vide_hors_reponse_de_la_faq(self):
        """Ni une commande, ni une salutation, ni un échec ne retiennent une
        question — et ne doivent donc proposer aucune suite."""
        for message in ["help", "liste", "bonjour", "comment dresser un lama sauvage"]:
            trace = {}
            with patch.object(chatpy, "_logger_question_sans_reponse"):
                chatpy.chatbot_response(message, trace=trace)
            self.assertEqual(trace, {}, message)

    def test_traiter_message_remet_les_suggestions_en_texte(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(chatpy, "HISTORY_FILE", os.path.join(tmp, "h.json")):
                texte = chatpy.ChatBot().traiter_message("qu'est-ce qu'une fonction")
        self.assertIn(f"📌 {chatpy.TITRE_QUESTIONS_LIEES}:", texte)
        self.assertIn("1. ", texte)


class TestSensibilite(unittest.TestCase):
    """Le seuil de réponse réglable par visiteur (carte « Chatbot » de /compte)."""

    FAQ = {"comment ajouter un élément à une liste": "Avec append()."}

    def setUp(self):
        # FAQ réduite à une entrée : les scores restent lisibles et le test ne
        # dépend pas du contenu réel de faq.json, qui bouge à chaque ajout.
        self._patchs = [
            patch.object(chatpy, "faq", self.FAQ),
            patch.object(chatpy, "norm_vers_original",
                         {chatpy.normaliser_texte(q): q for q in self.FAQ}),
        ]
        for p in self._patchs:
            p.start()
            self.addCleanup(p.stop)

    def test_noms_connus_donnent_des_seuils_ordonnes(self):
        strict = chatpy.seuil_de_sensibilite("stricte")
        normal = chatpy.seuil_de_sensibilite("normale")
        large = chatpy.seuil_de_sensibilite("large")
        self.assertGreater(strict, normal)
        self.assertGreater(normal, large)
        self.assertEqual(normal, chatpy.SEUIL_CORRESPONDANCE)

    def test_toutes_les_sensibilites_laissent_vivre_les_propositions(self):
        """Un seuil sous SEUIL_PROPOSITION refermerait la bande « vouliez-vous
        dire ? » : un échec ne proposerait alors plus rien du tout."""
        for nom, seuil in chatpy.SENSIBILITES.items():
            self.assertGreater(seuil, chatpy.SEUIL_PROPOSITION, nom)

    def test_nom_inconnu_retombe_sur_la_normale(self):
        for valeur in ["", "TRÈS large", None, "normale2"]:
            self.assertEqual(chatpy.seuil_de_sensibilite(valeur),
                             chatpy.SEUIL_CORRESPONDANCE)

    def _confiance(self, message):
        scores = chatpy._scanner_faq(chatpy.normaliser_texte(message))
        return scores[0][1] if scores else 0

    def test_stricte_refuse_ce_que_la_normale_accepte(self):
        """Une question de confiance moyenne : répondue en normale, écartée en
        stricte. C'est tout l'effet visible du réglage."""
        message = "element liste"
        confiance = self._confiance(message)
        # Le test n'a de sens que dans la bande entre les deux seuils.
        self.assertTrue(chatpy.SEUIL_CORRESPONDANCE * 100 <= confiance
                        < chatpy.SENSIBILITES["stricte"] * 100,
                        f"confiance {confiance}% hors de la bande testée")

        with patch.object(chatpy, "_logger_question_sans_reponse"):
            normale = chatpy.chatbot_response(message)
            stricte = chatpy.chatbot_response(
                message, chatpy.seuil_de_sensibilite("stricte"))
        self.assertIn("Confiance:", normale)
        self.assertEqual(stricte, chatpy.REPONSE_INCOMPRISE)

    def test_stricte_ne_pollue_pas_le_journal_des_lacunes(self):
        """Une question que la FAQ traite bien n'est pas une lacune, même quand
        le réglage du visiteur l'a fait passer pour un échec."""
        with patch.object(chatpy, "_logger_question_sans_reponse") as logger:
            chatpy.chatbot_response("element liste",
                                    chatpy.seuil_de_sensibilite("stricte"))
        logger.assert_not_called()

    def test_un_vrai_echec_reste_journalise_en_stricte(self):
        with patch.object(chatpy, "_logger_question_sans_reponse") as logger:
            chatpy.chatbot_response("comment dresser un lama sauvage",
                                    chatpy.seuil_de_sensibilite("stricte"))
        logger.assert_called_once()

    def test_la_bande_des_propositions_suit_le_seuil_applique(self):
        """Écartée en stricte, la question doit reparaître en « vouliez-vous
        dire ? » : sans ça, le réglage ferait disparaître la réponse ET son
        rattrapage."""
        message = "element liste"
        self.assertEqual(chatpy.questions_proches(message), [])
        proches = chatpy.questions_proches(
            message, seuil=chatpy.seuil_de_sensibilite("stricte"))
        self.assertEqual(proches, list(self.FAQ))

    def test_repondre_transmet_la_sensibilite(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(chatpy, "HISTORY_FILE", os.path.join(tmp, "h.json")), \
                 patch.object(chatpy, "QUESTIONS_SANS_REPONSE_FILE", os.path.join(tmp, "j.json")):
                bot = chatpy.ChatBot()
                normale = bot.repondre("element liste")
                stricte = bot.repondre("element liste",
                                       sensibilite="stricte")
        self.assertIn("Confiance:", normale["response"])
        self.assertEqual(stricte["response"], chatpy.REPONSE_INCOMPRISE)
        self.assertEqual(stricte["titre_suggestions"], chatpy.TITRE_QUESTIONS_PROCHES)


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
