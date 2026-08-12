"""Cohérence du catalogue de traduction (i18n.js) et de son pendant serveur.

Ce fichier existe parce que rien d'autre ne peut échouer quand une traduction
manque. Une clé oubliée dans une langue ne lève aucune erreur : elle retombe
sur le français, et le défaut ne se voit que si quelqu'un consulte la page dans
cette langue-là. Un texte français au milieu d'une page allemande est
exactement le genre de chose qu'on ne remarque jamais soi-même.

Les vérifications portent donc sur trois invariants :

1. chaque clé porte autant de traductions qu'il y a de langues, dans l'ordre ;
2. chaque clé employée dans le HTML ou le JavaScript existe dans le catalogue
   (sinon le texte affiché serait la clé elle-même : « nav.deconnexion ») ;
3. le catalogue serveur (comptes.MESSAGES) couvre les mêmes langues, faute de
   quoi une modale traduite afficherait des refus en français.

i18n.js est lu comme du texte : ce dépôt n'a pas d'exécuteur JavaScript, et un
petit lecteur de littéraux suffit pour un fichier dont la forme est fixe.
"""

import importlib
import os
import re
import unittest

import comptes

_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
I18N_JS = os.path.join(_DIR, "i18n.js")

PAGES = ("Index.html", "chat.html", "compte.html")
SCRIPTS = ("chat.js", "script.js", "compte.js", "nav-compte.js")

# Les familles de clés du catalogue. Sert à distinguer une clé d'un nom de
# fichier ou d'un sélecteur dans les scripts.
PREFIXES = ("nav", "commun", "accueil", "demo", "modale", "oauth", "chat", "compte")


def _lire(nom):
    with open(os.path.join(_DIR, nom), "r", encoding="utf-8") as f:
        return f.read()


def _lire_chaine(source, i):
    """Lit le littéral de chaîne qui commence en `source[i]`.

    Retourne (contenu, index après la chaîne). Gère l'échappement, sans quoi
    « d\\'une minute » couperait la chaîne en deux au milieu.
    """
    delimiteur = source[i]
    i += 1
    morceaux = []
    while i < len(source):
        c = source[i]
        if c == "\\":
            morceaux.append(source[i + 1])
            i += 2
            continue
        if c == delimiteur:
            return "".join(morceaux), i + 1
        morceaux.append(c)
        i += 1
    raise AssertionError("chaîne non terminée dans i18n.js")


def _catalogue():
    """{clé: [traductions]} tel qu'écrit dans i18n.js."""
    source = _lire("i18n.js")
    entrees = {}
    # Les entrées ont toutes la forme  'famille.nom': [ … ]  et sont les seuls
    # tableaux du fichier indexés par une clé pointée.
    for correspondance in re.finditer(r"'([a-z]+\.[a-z0-9_]+)':\s*\[", source):
        cle = correspondance.group(1)
        i = correspondance.end()
        valeurs = []
        while i < len(source):
            c = source[i]
            if c == "]":
                break
            if c in "'\"":
                valeur, i = _lire_chaine(source, i)
                valeurs.append(valeur)
                continue
            i += 1
        entrees[cle] = valeurs
    return entrees


def _langues_js():
    """Le tableau LANGUES de i18n.js, qui fixe l'ordre des traductions."""
    source = _lire("i18n.js")
    bloc = re.search(r"var LANGUES = \[(.*?)\]", source, re.S)
    assert bloc, "LANGUES introuvable dans i18n.js"
    return re.findall(r"'([a-z]{2})'", bloc.group(1))


def _cles_utilisees():
    """Toutes les clés référencées par les pages et les scripts."""
    utilisees = set()

    for page in PAGES:
        contenu = _lire(page)
        for attribut in ("data-i18n", "data-i18n-html", "data-label-connecte-i18n"):
            utilisees.update(re.findall(attribut + r'="([^"]+)"', contenu))
        # data-i18n-attr="placeholder:cle;aria-label:autre"
        for groupe in re.findall(r'data-i18n-attr="([^"]+)"', contenu):
            for paire in groupe.split(";"):
                morceaux = paire.split(":")
                if len(morceaux) == 2:
                    utilisees.add(morceaux[1].strip())

    # Dans les scripts, toute chaîne qui ressemble à une clé : les appels ne
    # passent pas tous par T() — itemMenu() en prend une, setAttribute aussi.
    motif = re.compile(r"['\"](" + "|".join(PREFIXES) + r")\.([a-z0-9_]+)['\"]")
    for script in SCRIPTS:
        for famille, nom in motif.findall(_lire(script)):
            utilisees.add(famille + "." + nom)

    return utilisees


class TestCatalogue(unittest.TestCase):
    def setUp(self):
        self.catalogue = _catalogue()
        self.langues = _langues_js()

    def test_le_catalogue_est_lu(self):
        # Garde-fou du lecteur lui-même : s'il cassait, tous les autres tests
        # passeraient sur un catalogue vide sans rien signaler.
        self.assertGreater(len(self.catalogue), 100)
        self.assertIn("nav.accueil", self.catalogue)
        self.assertEqual(self.catalogue["nav.accueil"][0], "Accueil")

    def test_six_langues_declarees(self):
        self.assertEqual(self.langues, ["fr", "en", "es", "de", "it", "pt"])

    def test_chaque_cle_a_une_traduction_par_langue(self):
        attendu = len(self.langues)
        incompletes = {
            cle: len(valeurs)
            for cle, valeurs in self.catalogue.items()
            if len(valeurs) != attendu
        }
        self.assertEqual(
            incompletes, {},
            "ces clés n'ont pas une traduction par langue "
            f"(il en faut {attendu}, dans l'ordre {self.langues})",
        )

    def test_aucune_traduction_vide(self):
        # Sauf chat.note_langue, dont le français est vide exprès : la note
        # « ChatPy répond en français » n'a rien à dire à un francophone.
        vides = {
            cle: valeurs
            for cle, valeurs in self.catalogue.items()
            if any(v.strip() == "" for v in valeurs) and cle != "chat.note_langue"
        }
        self.assertEqual(vides, {})

    def test_le_francais_de_la_note_de_langue_est_vide(self):
        note = self.catalogue["chat.note_langue"]
        self.assertEqual(note[0], "")
        # Et les cinq autres, elles, doivent bien dire quelque chose.
        self.assertTrue(all(v.strip() for v in note[1:]))

    def test_les_jetons_sont_les_memes_dans_toutes_les_langues(self):
        """{prenom}, {score}… doivent survivre à la traduction.

        Un jeton renommé ou perdu ne casse rien : il s'affiche tel quel, ou la
        valeur disparaît. « Hello {prénom} » à l'écran, et personne ne le voit
        avant un utilisateur.
        """
        for cle, valeurs in self.catalogue.items():
            reference = set(re.findall(r"\{(\w+)\}", valeurs[0]))
            for index, valeur in enumerate(valeurs[1:], start=1):
                if valeur == "":
                    continue
                self.assertEqual(
                    set(re.findall(r"\{(\w+)\}", valeur)), reference,
                    f"{cle} : les jetons de « {self.langues[index]} » "
                    "diffèrent de ceux du français",
                )

    def test_toutes_les_cles_utilisees_existent(self):
        manquantes = sorted(_cles_utilisees() - set(self.catalogue))
        self.assertEqual(
            manquantes, [],
            "ces clés sont employées dans une page ou un script mais absentes "
            "du catalogue : elles s'afficheraient telles quelles",
        )

    def test_le_html_garde_son_texte_francais(self):
        """Le français reste écrit dans le HTML : c'est le rendu sans JavaScript.

        Un data-i18n sur un élément vide passerait tous les autres tests et
        n'afficherait rien du tout si le script ne s'exécute pas.
        """
        for page in PAGES:
            contenu = _lire(page)
            for balise in re.findall(r"<(\w+)[^>]*\sdata-i18n=\"[^\"]+\"[^>]*>(.*?)</\1>",
                                     contenu, re.S):
                self.assertTrue(
                    balise[1].strip(),
                    f"{page} : un élément porte data-i18n mais n'a aucun texte de repli",
                )


class TestCatalogueServeur(unittest.TestCase):
    """comptes.MESSAGES doit suivre le même jeu de langues que i18n.js."""

    def test_memes_langues_que_le_front(self):
        self.assertEqual(list(comptes.LANGUES), _langues_js())

    def test_chaque_message_couvre_toutes_les_langues(self):
        for code, traductions in comptes.MESSAGES.items():
            self.assertEqual(
                sorted(traductions), sorted(comptes.LANGUES),
                f"le message « {code} » ne couvre pas toutes les langues",
            )
            for langue, texte in traductions.items():
                self.assertTrue(texte.strip(), f"{code}/{langue} est vide")

    def test_les_jetons_sont_preserves(self):
        for code, traductions in comptes.MESSAGES.items():
            reference = set(re.findall(r"\{(\w+)\}", traductions["fr"]))
            for langue, texte in traductions.items():
                self.assertEqual(
                    set(re.findall(r"\{(\w+)\}", texte)), reference,
                    f"{code}/{langue} : jetons différents du français",
                )

    def test_langue_inconnue_retombe_sur_le_francais(self):
        for valeur in ("klingon", "", None, 42, ["en"]):
            self.assertEqual(comptes.normaliser_langue(valeur), "fr")
        self.assertEqual(comptes.normaliser_langue("de"), "de")

    def test_les_refus_sont_traduits(self):
        _, motif = comptes.valider("pas-une-adresse", "motdepasse12", langue="en")
        self.assertEqual(motif, "This email address is not valid.")
        _, motif = comptes.valider("a@b.fr", "court", langue="de")
        self.assertIn("8", motif)
        self.assertIn("Passwort", motif)

    def test_identifiants_incorrects_indistinguables_dans_chaque_langue(self):
        """La garantie anti-énumération doit survivre à la traduction.

        Adresse inconnue et mot de passe faux partagent un seul code : si une
        langue les rédigeait différemment, elle rendrait lisible ce que le
        français cache.
        """
        for langue in comptes.LANGUES:
            # Une adresse différente par langue : six essais sur la même
            # déclencheraient le blocage après cinq (TENTATIVES_MAX), et c'est
            # alors ce refus-là qu'on comparerait.
            _, inconnue = comptes.verifier(f"personne-{langue}@nulle-part.test", "x" * 12, langue)
            _, vide = comptes.verifier("", "", langue)
            self.assertEqual(inconnue, vide)
            self.assertEqual(inconnue, comptes.MESSAGES["identifiants_incorrects"][langue])

    def tearDown(self):
        # Le compteur d'échecs vit en mémoire du processus : le laisser garni
        # ferait échouer un test suivant qui s'authentifierait pour de bon.
        comptes._tentatives.clear()


class TestFichierServi(unittest.TestCase):
    """i18n.js doit figurer dans FICHIERS_PUBLICS.

    Flask ne sert aucun dossier statique ici : chaque fichier est nommé un par
    un, parce que la racine du projet contient aussi le code source et les
    journaux de conversation. Un fichier oublié dans cette liste répond 404 —
    et pour celui-ci, le symptôme serait des libellés « nav.deconnexion » sur
    les trois pages, sans erreur ailleurs.
    """

    def setUp(self):
        import app as app_module
        importlib.reload(app_module)
        self.app_module = app_module
        app_module.app.testing = True
        self.client = app_module.app.test_client()

    def test_i18n_js_est_declare_public(self):
        self.assertIn("i18n.js", self.app_module.FICHIERS_PUBLICS)

    def test_i18n_js_est_servi(self):
        reponse = self.client.get("/i18n.js")
        self.assertEqual(reponse.status_code, 200)
        self.assertIn(b"ChatPyI18n", reponse.data)

    def test_les_pages_chargent_i18n_avant_le_contenu(self):
        """Sans defer et dans le <head> : sinon la page s'affiche en français
        puis se réécrit sous les yeux du visiteur."""
        for page in PAGES:
            contenu = _lire(page)
            self.assertIn('<script src="i18n.js"></script>', contenu, page)
            tete = contenu.split("</head>")[0]
            self.assertIn('src="i18n.js"', tete, f"{page} : i18n.js doit être dans le <head>")
            # preferences.js publie le réglage que i18n.js consulte au démarrage.
            self.assertLess(
                tete.index('src="preferences.js"'), tete.index('src="i18n.js"'),
                f"{page} : preferences.js doit précéder i18n.js",
            )

    def test_le_fichier_des_comptes_reste_prive(self):
        # Garde-fou : la liste s'allonge à chaque nouveau fichier de façade, et
        # c'est le moment où l'on relâche l'attention sur ce qu'elle protège.
        self.assertNotIn("comptes.json", self.app_module.FICHIERS_PUBLICS)
        self.assertEqual(self.client.get("/comptes.json").status_code, 404)


if __name__ == "__main__":
    unittest.main()
