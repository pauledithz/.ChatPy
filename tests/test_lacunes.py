"""Tests de lacunes.py — l'outil qui trie le journal des lacunes.

Le diagnostic est confronté à une FAQ de test, jamais à la vraie : le rangement
d'une question dans « déjà couverte » plutôt que « sujet manquant » dépend
entièrement du contenu de faq.json, qui change à chaque ajout d'entrée.

    python3 -m unittest tests.test_lacunes -v
"""
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ia_en_python as ia  # noqa: E402
import lacunes  # noqa: E402


FAQ_TEST = {
    "comment trier une liste": "Utilisez sorted() ou .sort()",
    "comment installer un module": "Utilisez pip install",
    "qu'est-ce qu'une variable": "Une variable stocke une valeur",
}


class BaseLacunes(unittest.TestCase):
    """Isole la FAQ chargée à l'import et redirige le journal vers un fichier temporaire."""

    def setUp(self):
        self._faq = ia.faq
        self._norm = ia.norm_vers_original
        ia.faq = dict(FAQ_TEST)
        ia.norm_vers_original = {ia.normaliser_texte(q): q for q in FAQ_TEST}

        self._dossier = tempfile.TemporaryDirectory()
        self._journal = os.path.join(self._dossier.name, "questions_sans_reponse.json")
        self._patch_chemin = patch.object(ia, "QUESTIONS_SANS_REPONSE_FILE", self._journal)
        self._patch_chemin.start()

    def tearDown(self):
        self._patch_chemin.stop()
        self._dossier.cleanup()
        ia.faq = self._faq
        ia.norm_vers_original = self._norm

    def ecrire_journal(self, donnees):
        with open(self._journal, "w", encoding="utf-8") as f:
            json.dump(donnees, f, ensure_ascii=False)

    def lire_journal(self):
        with open(self._journal, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def entree(texte, occurrences=1, pouces_bas=0, derniere_fois="2026-01-01"):
        return {"texte": texte, "occurrences": occurrences,
                "pouces_bas": pouces_bas, "derniere_fois": derniere_fois}


class ChargementTests(BaseLacunes):

    def test_journal_absent_vaut_journal_vide(self):
        """Un journal jamais écrit n'est pas une erreur : le bot n'a rien raté."""
        self.assertEqual(lacunes.charger_journal(), {})

    def test_journal_illisible_retourne_none(self):
        with open(self._journal, "w", encoding="utf-8") as f:
            f.write("{ pas du json")
        with redirect_stdout(io.StringIO()):
            self.assertIsNone(lacunes.charger_journal())

    def test_journal_au_mauvais_format_retourne_none(self):
        self.ecrire_journal(["une liste, pas un objet"])
        with redirect_stdout(io.StringIO()):
            self.assertIsNone(lacunes.charger_journal())

    def test_journal_corrompu_nest_pas_deplace(self):
        """Contrairement à _incrementer_journal(), un outil de lecture ne doit
        jamais déplacer le fichier de l'utilisateur sous ses pieds."""
        with open(self._journal, "w", encoding="utf-8") as f:
            f.write("{ pas du json")
        with redirect_stdout(io.StringIO()):
            lacunes.charger_journal()
        self.assertTrue(os.path.exists(self._journal))
        self.assertFalse(os.path.exists(self._journal + ".corrompu"))

    def test_entrees_tolere_les_champs_manquants(self):
        """Les entrées écrites avant l'ajout des pouces n'ont pas le champ."""
        entrees = lacunes._entrees({"vieille": {"texte": "vieille", "occurrences": 3}})
        self.assertEqual(entrees[0]["pouces_bas"], 0)
        self.assertEqual(entrees[0]["derniere_fois"], "?")

    def test_entrees_ignore_les_valeurs_non_dict(self):
        entrees = lacunes._entrees({"cassee": "pas un dict", "bonne": self.entree("bonne")})
        self.assertEqual([e["cle"] for e in entrees], ["bonne"])

    def test_entrees_ignore_les_compteurs_aberrants(self):
        entrees = lacunes._entrees({"x": {"texte": "x", "occurrences": -5, "pouces_bas": "trois"}})
        self.assertEqual(entrees[0]["occurrences"], 0)
        self.assertEqual(entrees[0]["pouces_bas"], 0)


class PoidsTests(BaseLacunes):

    def test_pouce_bas_pese_plus_quun_echec(self):
        """Un pouce bas signale un échec que l'utilisateur n'a pas vu passer :
        il doit remonter plus haut qu'un « je ne comprends pas » assumé."""
        echec = lacunes.poids(self.entree("q", occurrences=1))
        pouce = lacunes.poids(self.entree("q", occurrences=0, pouces_bas=1))
        self.assertGreater(pouce, echec)

    def test_les_deux_compteurs_sadditionnent(self):
        self.assertEqual(
            lacunes.poids(self.entree("q", occurrences=2, pouces_bas=3)),
            2 + 3 * lacunes.POIDS_POUCE_BAS)


class DiagnosticTests(BaseLacunes):

    def diagnostic(self, texte, **kw):
        return lacunes.diagnostiquer(self.entree(texte, **kw))[0]

    def test_question_desormais_couverte_par_la_faq(self):
        """Journalisée avant l'ajout de l'entrée, elle matche maintenant : périmée."""
        self.assertEqual(self.diagnostic("comment trier une liste"), "couverte")

    def test_pouce_bas_sur_une_question_couverte_est_un_faux_positif(self):
        """La FAQ répond *et* l'utilisateur a refusé la réponse : ce n'est pas
        du journal périmé, c'est la mauvaise entrée qui matche."""
        self.assertEqual(
            self.diagnostic("comment trier une liste", occurrences=0, pouces_bas=1),
            "mauvaise_reponse")

    def test_question_proche_dune_entree_existante(self):
        self.assertEqual(self.diagnostic("installer numpy tout de suite"), "a_rapprocher")

    def test_sujet_absent_de_la_faq(self):
        self.assertEqual(self.diagnostic("comment ouvrir une socket reseau"), "manquante")

    def test_ressemblance_sans_mot_commun_nest_pas_a_rapprocher(self):
        """La similarité de caractères seule rapproche n'importe quoi. Sans un
        mot de sujet partagé, la question est absente, pas mal rapprochée."""
        entree = self.entree("comment gerer une pile")
        diagnostic, question, score = lacunes.diagnostiquer(entree)
        self.assertGreaterEqual(score, ia.SEUIL_PROPOSITION * 100,
                                "le cas ne teste rien si le score est déjà sous le seuil")
        self.assertEqual(diagnostic, "manquante")

    def test_faq_vide_rend_tout_manquant(self):
        ia.faq = {}
        ia.norm_vers_original = {}
        self.assertEqual(self.diagnostic("comment trier une liste"), "manquante")


class RegroupementTests(BaseLacunes):

    def test_formulations_voisines_forment_un_seul_sujet(self):
        entrees = [self.entree("comment ouvrir une socket reseau", occurrences=3),
                   self.entree("comment ouvrir une socket", occurrences=2)]
        groupes = lacunes.regrouper(sorted(entrees, key=lacunes.poids, reverse=True))
        self.assertEqual(len(groupes), 1)
        self.assertEqual(groupes[0]["poids"], 5)

    def test_le_representant_est_la_formulation_la_plus_lourde(self):
        entrees = [self.entree("comment ouvrir une socket", occurrences=1),
                   self.entree("comment ouvrir une socket reseau", occurrences=9)]
        groupes = lacunes.regrouper(sorted(entrees, key=lacunes.poids, reverse=True))
        self.assertEqual(groupes[0]["membres"][0]["texte"], "comment ouvrir une socket reseau")

    def test_sujets_distincts_restent_separes(self):
        entrees = [self.entree("comment ouvrir une socket reseau"),
                   self.entree("comment lancer un thread")]
        groupes = lacunes.regrouper(entrees)
        self.assertEqual(len(groupes), 2)

    def test_groupes_tries_par_poids_decroissant(self):
        entrees = sorted([self.entree("comment lancer un thread", occurrences=1),
                          self.entree("comment ouvrir une socket reseau", occurrences=7)],
                         key=lacunes.poids, reverse=True)
        groupes = lacunes.regrouper(entrees)
        self.assertEqual([g["poids"] for g in groupes], [7, 1])


class AnalyseTests(BaseLacunes):

    def test_chaque_entree_atterrit_dans_une_seule_famille(self):
        journal = {
            "comment trier une liste": self.entree("comment trier une liste"),
            "installer numpy": self.entree("installer numpy tout de suite"),
            "socket": self.entree("comment ouvrir une socket reseau"),
        }
        familles = lacunes.analyser(journal)
        total = sum(len(g["membres"]) for f in familles.values() for g in f)
        self.assertEqual(total, 3)
        self.assertEqual(len(familles["couverte"]), 1)
        self.assertEqual(len(familles["a_rapprocher"]), 1)
        self.assertEqual(len(familles["manquante"]), 1)

    def test_toutes_les_sections_sont_presentes_meme_vides(self):
        familles = lacunes.analyser({})
        self.assertEqual(set(familles), {code for code, _, _ in lacunes.SECTIONS})

    def test_un_groupe_ne_melange_jamais_deux_diagnostics(self):
        """Deux formulations proches, mais l'une couverte et l'autre non :
        les diagnostiquer avant de regrouper évite un conseil contradictoire."""
        journal = {
            "a": self.entree("comment trier une liste"),
            "b": self.entree("comment trier une liste de sockets reseau"),
        }
        familles = lacunes.analyser(journal)
        for famille in familles.values():
            for groupe in famille:
                diagnostics = {lacunes.diagnostiquer(m)[0] for m in groupe["membres"]}
                self.assertEqual(len(diagnostics), 1)


class NettoyageTests(BaseLacunes):

    def test_supprime_uniquement_les_entrees_couvertes(self):
        journal = {
            "comment trier une liste": self.entree("comment trier une liste"),
            "socket": self.entree("comment ouvrir une socket reseau"),
        }
        self.ecrire_journal(journal)
        with redirect_stdout(io.StringIO()):
            retirees = lacunes.nettoyer(lacunes.analyser(journal))
        self.assertEqual(retirees, 1)
        self.assertEqual(list(self.lire_journal()), ["socket"])

    def test_une_entree_avec_pouce_bas_nest_jamais_supprimee(self):
        """Elle est diagnostiquée « mauvaise réponse » : la lacune est réelle,
        supprimer la ligne effacerait le seul signal qui la révèle."""
        journal = {"trier": self.entree("comment trier une liste", occurrences=0, pouces_bas=2)}
        self.ecrire_journal(journal)
        with redirect_stdout(io.StringIO()):
            lacunes.nettoyer(lacunes.analyser(journal))
        self.assertEqual(list(self.lire_journal()), ["trier"])

    def test_les_compteurs_bouges_entre_temps_survivent(self):
        """Le serveur Flask peut incrémenter le journal pendant l'analyse :
        la relecture juste avant l'écriture doit préserver son travail."""
        journal = {
            "comment trier une liste": self.entree("comment trier une liste"),
            "socket": self.entree("comment ouvrir une socket reseau", occurrences=1),
        }
        self.ecrire_journal(journal)
        familles = lacunes.analyser(journal)

        entre_temps = dict(journal)
        entre_temps["socket"] = self.entree("comment ouvrir une socket reseau", occurrences=42)
        entre_temps["neuve"] = self.entree("question posee entre temps")
        self.ecrire_journal(entre_temps)

        with redirect_stdout(io.StringIO()):
            lacunes.nettoyer(familles)

        final = self.lire_journal()
        self.assertNotIn("comment trier une liste", final)
        self.assertEqual(final["socket"]["occurrences"], 42)
        self.assertIn("neuve", final)

    def test_rien_a_nettoyer_ne_touche_pas_au_fichier(self):
        journal = {"socket": self.entree("comment ouvrir une socket reseau")}
        self.ecrire_journal(journal)
        avant = os.path.getmtime(self._journal)
        with redirect_stdout(io.StringIO()):
            self.assertEqual(lacunes.nettoyer(lacunes.analyser(journal)), 0)
        self.assertEqual(os.path.getmtime(self._journal), avant)


class RapportTests(BaseLacunes):

    def rendu(self, journal, **kw):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            lacunes.rapport(lacunes.analyser(journal), **kw)
        return buffer.getvalue()

    def test_journal_vide_affiche_un_message_et_pas_de_section(self):
        sortie = self.rendu({})
        self.assertIn("le journal est vide", sortie)
        for _, titre, _ in lacunes.SECTIONS:
            self.assertNotIn(titre, sortie)

    def test_les_sections_vides_sont_omises(self):
        sortie = self.rendu({"socket": self.entree("comment ouvrir une socket reseau")})
        self.assertIn("SUJET MANQUANT", sortie)
        self.assertNotIn("DÉJÀ COUVERTE", sortie)

    def test_affiche_la_faq_la_plus_proche_et_son_score(self):
        sortie = self.rendu({"numpy": self.entree("installer numpy tout de suite")})
        self.assertIn("comment installer un module", sortie)
        self.assertRegex(sortie, r"\(\d+%\)")

    def test_les_formulations_secondaires_sont_listees(self):
        journal = {
            "a": self.entree("comment ouvrir une socket reseau", occurrences=5),
            "b": self.entree("comment ouvrir une socket", occurrences=1),
        }
        sortie = self.rendu(journal)
        self.assertIn("1 autre(s) formulation(s)", sortie)
        self.assertIn("comment ouvrir une socket »", sortie)

    def test_limite_par_section_et_option_tout(self):
        # Des sujets franchement distincts : des variantes d'une même phrase se
        # regrouperaient en un seul sujet et la limite ne serait jamais atteinte.
        sujets = ["comment ouvrir une socket reseau", "comment lancer un thread",
                  "comment chiffrer un mot de passe", "comment envoyer un mail",
                  "comment parser du xml", "comment dessiner un graphique",
                  "comment mesurer le temps", "comment compiler du cython",
                  "comment deployer sur heroku", "comment signer un certificat",
                  "comment jouer un son", "comment scraper une page web",
                  "comment interroger une base mongo"]
        self.assertGreater(len(sujets), lacunes.LIMITE_PAR_SECTION)
        journal = {f"q{i}": self.entree(sujet) for i, sujet in enumerate(sujets)}
        tronque = self.rendu(journal)
        self.assertIn("relancez avec --tout", tronque)
        self.assertNotIn("relancez avec --tout", self.rendu(journal, tout=True))

    def test_retourne_le_nombre_dentrees_supprimables(self):
        journal = {
            "trier": self.entree("comment trier une liste"),
            "socket": self.entree("comment ouvrir une socket reseau"),
        }
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            supprimables = lacunes.rapport(lacunes.analyser(journal))
        self.assertEqual(supprimables, 1)
        self.assertIn("--nettoyer", buffer.getvalue())


class MainTests(BaseLacunes):

    def lancer(self, argv):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = lacunes.main(argv)
        return code, buffer.getvalue()

    def test_sans_option_le_journal_nest_pas_modifie(self):
        journal = {"trier": self.entree("comment trier une liste")}
        self.ecrire_journal(journal)
        code, _ = self.lancer([])
        self.assertEqual(code, 0)
        self.assertIn("trier", self.lire_journal())

    def test_option_nettoyer_ecrit(self):
        self.ecrire_journal({"trier": self.entree("comment trier une liste")})
        code, _ = self.lancer(["--nettoyer"])
        self.assertEqual(code, 0)
        self.assertEqual(self.lire_journal(), {})

    def test_option_inconnue_echoue_avec_laide(self):
        code, sortie = self.lancer(["--supprime-tout"])
        self.assertEqual(code, 1)
        self.assertIn("Option inconnue", sortie)
        self.assertIn("--nettoyer", sortie)

    def test_aide_reussit(self):
        code, sortie = self.lancer(["--aide"])
        self.assertEqual(code, 0)
        self.assertIn("--tout", sortie)

    def test_journal_illisible_termine_en_erreur(self):
        with open(self._journal, "w", encoding="utf-8") as f:
            f.write("{ pas du json")
        code, _ = self.lancer([])
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
