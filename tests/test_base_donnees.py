"""Tests de la base SQLite des comptes (base_donnees.py + schema.sql).

Ce qui est vérifié ici, dans l'ordre d'importance :

1. **Aucun mot de passe en clair n'atteint le disque.** C'est la propriété que
   tout le reste sert à protéger : le test relit les octets bruts du fichier et
   y cherche le mot de passe, plutôt que de faire confiance à la colonne.
2. L'inscription et la connexion écrivent bien ce qu'on attend (nom, email,
   date, compteur de passages), pour les trois moyens de connexion.
3. Les garde-fous du schéma : pas deux comptes locaux à la même adresse, pas de
   compte local sans empreinte.
4. La reprise de l'ancien comptes.json, qui ne doit ni perdre un compte ni
   rejouer deux fois.
5. La base n'est jamais servie par le web.

Chaque test travaille sur une base neuve dans un dossier temporaire : jamais sur
chatpy.db, qui contient de vrais comptes.
"""

import json
import os
import sqlite3
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from werkzeug.security import generate_password_hash

import base_donnees as bdd
import comptes

MOT_DE_PASSE = "phrase-de-passe-42"


class BaseTemporaire(unittest.TestCase):
    """Redirige la base vers un dossier temporaire, le temps d'un test."""

    def setUp(self):
        self._dossier = mock.patch.dict(os.environ, {}, clear=False)
        self._dossier.start()
        os.environ.pop("CHATPY_DB", None)

        import tempfile
        self._temp = tempfile.TemporaryDirectory()
        self.addCleanup(self._temp.cleanup)
        self.addCleanup(self._dossier.stop)

        self.base = os.path.join(self._temp.name, "chatpy-test.db")
        self.json_herite = os.path.join(self._temp.name, "comptes.json")
        for cible, valeur in (("BASE_FILE", self.base),
                              ("COMPTES_JSON", self.json_herite),
                              ("_base_prete", None)):
            correctif = mock.patch.object(bdd, cible, valeur)
            correctif.start()
            self.addCleanup(correctif.stop)

        # Le décompte des tentatives ratées vit en mémoire et survivrait d'un
        # test à l'autre, bloquant les connexions du suivant.
        comptes._tentatives.clear()

    def lignes(self):
        with bdd.connexion() as cnx:
            return [dict(l) for l in cnx.execute("SELECT * FROM utilisateurs")]


class TestSchema(BaseTemporaire):

    def test_la_base_et_sa_table_sont_creees_a_la_premiere_utilisation(self):
        self.assertFalse(os.path.exists(self.base))
        self.assertEqual(self.lignes(), [])
        self.assertTrue(os.path.exists(self.base))

    def test_les_colonnes_attendues_existent(self):
        with bdd.connexion() as cnx:
            colonnes = {l["name"] for l in cnx.execute("PRAGMA table_info(utilisateurs)")}
        self.assertEqual(colonnes, {
            "fournisseur", "id_externe", "nom", "email", "empreinte", "photo",
            "cree", "derniere_connexion", "nb_connexions",
        })

    def test_un_compte_local_sans_empreinte_est_refuse_par_la_base(self):
        """Un compte local sans mot de passe serait un compte à porte ouverte."""
        with self.assertRaises(sqlite3.IntegrityError):
            with bdd.connexion() as cnx:
                cnx.execute(
                    "INSERT INTO utilisateurs (fournisseur, id_externe, nom, email,"
                    " empreinte, cree) VALUES ('local', 'x', 'X', 'x@y.fr', NULL, 'a')"
                )

    def test_chatpy_db_deplace_la_base(self):
        """En production, la base doit pouvoir vivre hors du dossier du code."""
        ailleurs = os.path.join(self._temp.name, "ailleurs.db")
        with mock.patch.dict(os.environ, {"CHATPY_DB": ailleurs}):
            bdd._base_prete = None
            self.assertEqual(bdd.chemin(), ailleurs)
            self.lignes()
        self.assertTrue(os.path.exists(ailleurs))
        self.assertFalse(os.path.exists(self.base))

    @unittest.skipIf(os.name == "nt", "droits POSIX")
    def test_la_base_n_est_lisible_que_par_son_proprietaire(self):
        self.lignes()
        self.assertEqual(os.stat(self.base).st_mode & 0o077, 0)

    def test_rejouer_le_schema_ne_perd_rien(self):
        comptes.creer("paul@example.com", MOT_DE_PASSE, MOT_DE_PASSE, "Paul")
        bdd._base_prete = None  # force un nouveau passage du schema.sql
        self.assertEqual(len(self.lignes()), 1)


class TestInscription(BaseTemporaire):

    def test_l_inscription_ecrit_une_ligne_complete(self):
        utilisateur, motif = comptes.creer(
            "Paul@Example.COM", MOT_DE_PASSE, MOT_DE_PASSE, "Paul Z"
        )
        self.assertIsNone(motif)

        lignes = self.lignes()
        self.assertEqual(len(lignes), 1)
        ligne = lignes[0]
        self.assertEqual(ligne["fournisseur"], "local")
        self.assertEqual(ligne["nom"], "Paul Z")
        # Rangée en minuscules, sinon la même personne aurait deux comptes selon
        # la façon dont elle tape son adresse.
        self.assertEqual(ligne["email"], "paul@example.com")
        self.assertEqual(ligne["id_externe"], utilisateur["id"])
        self.assertEqual(ligne["nb_connexions"], 1)
        self.assertTrue(ligne["cree"].startswith("20"))

    def test_le_mot_de_passe_n_est_jamais_ecrit_en_clair(self):
        """La propriété qui compte : relue sur le disque, pas dans la colonne."""
        comptes.creer("paul@example.com", MOT_DE_PASSE, MOT_DE_PASSE, "Paul")

        with open(self.base, "rb") as f:
            octets = f.read()
        self.assertNotIn(MOT_DE_PASSE.encode(), octets)

        empreinte = self.lignes()[0]["empreinte"]
        self.assertTrue(empreinte.startswith("scrypt:"))
        self.assertNotIn(MOT_DE_PASSE, empreinte)

    def test_deux_inscriptions_a_la_meme_adresse_sont_refusees(self):
        comptes.creer("paul@example.com", MOT_DE_PASSE, MOT_DE_PASSE, "Paul")
        utilisateur, motif = comptes.creer(
            "PAUL@example.com", "un-autre-mot-de-passe", "un-autre-mot-de-passe", "Autre"
        )
        self.assertIsNone(utilisateur)
        self.assertEqual(motif, comptes.MESSAGES["compte_existant"]["fr"])
        self.assertEqual(len(self.lignes()), 1)

    def test_une_inscription_refusee_n_ecrit_rien(self):
        _, motif = comptes.creer("pas-une-adresse", MOT_DE_PASSE, MOT_DE_PASSE, "X")
        self.assertTrue(motif)
        self.assertEqual(self.lignes(), [])


class TestConnexion(BaseTemporaire):

    def setUp(self):
        super().setUp()
        self.utilisateur, _ = comptes.creer(
            "paul@example.com", MOT_DE_PASSE, MOT_DE_PASSE, "Paul"
        )

    def test_une_connexion_reussie_avance_le_compteur_et_la_date(self):
        avant = self.lignes()[0]
        utilisateur, motif = comptes.verifier("paul@example.com", MOT_DE_PASSE)
        self.assertIsNone(motif)
        self.assertEqual(utilisateur["id"], self.utilisateur["id"])

        apres = self.lignes()[0]
        self.assertEqual(apres["nb_connexions"], avant["nb_connexions"] + 1)
        self.assertIsNotNone(apres["derniere_connexion"])

    def test_l_adresse_est_reconnue_quelle_que_soit_la_casse(self):
        _, motif = comptes.verifier("  PAUL@Example.com ", MOT_DE_PASSE)
        self.assertIsNone(motif)

    def test_un_mauvais_mot_de_passe_n_avance_rien(self):
        avant = self.lignes()[0]
        utilisateur, motif = comptes.verifier("paul@example.com", "mauvais-mot-de-passe")
        self.assertIsNone(utilisateur)
        self.assertTrue(motif)
        self.assertEqual(self.lignes()[0]["nb_connexions"], avant["nb_connexions"])

    def test_une_adresse_inconnue_ne_cree_aucune_ligne(self):
        utilisateur, motif = comptes.verifier("personne@nulle-part.test", MOT_DE_PASSE)
        self.assertIsNone(utilisateur)
        # Message rigoureusement identique à celui d'un mot de passe faux : le
        # distinguer révélerait quelles adresses sont inscrites.
        self.assertEqual(motif, comptes.MESSAGES["identifiants_incorrects"]["fr"])
        self.assertEqual(len(self.lignes()), 1)

    def test_l_empreinte_ne_sort_jamais_de_la_couche_de_stockage(self):
        self.assertNotIn("empreinte", self.utilisateur)
        for ligne in bdd.lister_utilisateurs():
            self.assertNotIn("empreinte", ligne)


class TestConnexionsExterieures(BaseTemporaire):
    """Google et GitHub : la première connexion vaut inscription."""

    GOOGLE = {"id": "110001", "nom": "Paul Z", "email": "Paul@Example.com",
              "photo": "https://exemple.test/p.jpg", "fournisseur": "google"}

    def test_une_premiere_connexion_inscrit_la_personne(self):
        bdd.enregistrer_connexion(self.GOOGLE)
        ligne = self.lignes()[0]
        self.assertEqual(ligne["fournisseur"], "google")
        self.assertEqual(ligne["id_externe"], "110001")
        self.assertEqual(ligne["email"], "paul@example.com")
        self.assertEqual(ligne["nb_connexions"], 1)
        # Leur mot de passe reste chez eux : rien à stocker.
        self.assertIsNone(ligne["empreinte"])

    def test_les_passages_suivants_mettent_le_profil_a_jour(self):
        bdd.enregistrer_connexion(self.GOOGLE)
        bdd.enregistrer_connexion({**self.GOOGLE, "nom": "Paul Zoungrana"})

        lignes = self.lignes()
        self.assertEqual(len(lignes), 1)
        self.assertEqual(lignes[0]["nom"], "Paul Zoungrana")
        self.assertEqual(lignes[0]["nb_connexions"], 2)

    def test_google_42_et_github_42_sont_deux_personnes(self):
        bdd.enregistrer_connexion({**self.GOOGLE, "id": "42"})
        bdd.enregistrer_connexion({**self.GOOGLE, "id": "42", "fournisseur": "github"})
        self.assertEqual(len(self.lignes()), 2)

    def test_une_adresse_deja_prise_en_local_reste_possible_chez_google(self):
        """La contrainte d'unicité ne vaut que pour les comptes locaux."""
        comptes.creer("paul@example.com", MOT_DE_PASSE, MOT_DE_PASSE, "Paul")
        bdd.enregistrer_connexion(self.GOOGLE)
        self.assertEqual(len(self.lignes()), 2)

    def test_noter_connexion_n_invente_pas_de_compte(self):
        bdd.noter_connexion("local", "identifiant-inexistant")
        self.assertEqual(self.lignes(), [])


class TestRepriseDeLAncienJson(BaseTemporaire):
    """L'ancien comptes.json doit entrer dans la base sans perdre personne."""

    ANCIEN = {
        "paul@example.com": {
            "id": "abcdef0123456789",
            "nom": "Paul",
            "email": "paul@example.com",
            "cree": 1786387010923,
        },
    }

    def ecrire_ancien(self, contenu=None):
        donnees = json.loads(json.dumps(contenu if contenu is not None else self.ANCIEN))
        for compte in donnees.values():
            if isinstance(compte, dict) and "empreinte" not in compte:
                compte["empreinte"] = generate_password_hash(MOT_DE_PASSE)
        with open(self.json_herite, "w", encoding="utf-8") as f:
            json.dump(donnees, f)

    def test_le_compte_repris_peut_toujours_se_connecter(self):
        self.ecrire_ancien()
        utilisateur, motif = comptes.verifier("paul@example.com", MOT_DE_PASSE)
        self.assertIsNone(motif)
        self.assertEqual(utilisateur["id"], "abcdef0123456789")

    def test_la_date_de_creation_est_conservee(self):
        self.ecrire_ancien()
        self.assertEqual(self.lignes()[0]["cree"][:4], "2026")

    def test_le_fichier_est_ecarte_pour_ne_pas_etre_rejoue(self):
        self.ecrire_ancien()
        self.lignes()
        self.assertFalse(os.path.exists(self.json_herite))
        self.assertTrue(os.path.exists(self.json_herite + ".repris"))

    def test_une_reprise_rejouee_ne_duplique_pas(self):
        self.ecrire_ancien()
        self.lignes()
        # Rejouée à la main, comme si le fichier n'avait pas pu être renommé.
        os.replace(self.json_herite + ".repris", self.json_herite)
        bdd._reprendre_comptes_json()
        self.assertEqual(len(self.lignes()), 1)

    def test_une_entree_sans_empreinte_est_ignoree_et_non_importee(self):
        self.ecrire_ancien({"x@y.fr": {"id": "1", "nom": "X", "email": "x@y.fr",
                                       "empreinte": ""}})
        self.assertEqual(self.lignes(), [])

    def test_un_json_illisible_est_mis_de_cote_sans_faire_tomber_le_site(self):
        with open(self.json_herite, "w", encoding="utf-8") as f:
            f.write("{ceci n'est pas du json")
        self.assertEqual(self.lignes(), [])
        self.assertTrue(os.path.exists(self.json_herite + ".corrompu"))


class TestParLeSite(BaseTemporaire):
    """Le trajet complet : la modale d'inscription du site jusqu'à la base."""

    def setUp(self):
        super().setUp()
        import app as app_module
        app_module.app.testing = True
        self.client = app_module.app.test_client()

    def test_une_inscription_depuis_le_site_atterrit_dans_la_base(self):
        reponse = self.client.post("/auth/inscription", json={
            "email": "nouvelle@example.com",
            "mot_de_passe": MOT_DE_PASSE,
            "confirmation": MOT_DE_PASSE,
            "nom": "Nouvelle",
        })
        self.assertEqual(reponse.status_code, 200)

        lignes = self.lignes()
        self.assertEqual(len(lignes), 1)
        self.assertEqual(lignes[0]["email"], "nouvelle@example.com")
        self.assertEqual(lignes[0]["nom"], "Nouvelle")

    def test_une_connexion_depuis_le_site_avance_le_compteur(self):
        self.client.post("/auth/inscription", json={
            "email": "nouvelle@example.com", "mot_de_passe": MOT_DE_PASSE,
            "confirmation": MOT_DE_PASSE, "nom": "Nouvelle",
        })
        self.client.post("/auth/logout")
        reponse = self.client.post("/auth/connexion", json={
            "email": "nouvelle@example.com", "mot_de_passe": MOT_DE_PASSE,
        })
        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(self.lignes()[0]["nb_connexions"], 2)

    def test_une_panne_de_base_ne_bloque_pas_une_connexion_google(self):
        """La ligne en base est une trace ; le cookie de session, lui, suffit."""
        import app as app_module
        with mock.patch.object(bdd, "enregistrer_connexion",
                               side_effect=sqlite3.OperationalError("disque plein")):
            app_module._memoriser({"fournisseur": "google", "id": "1"})


class TestExports(BaseTemporaire):
    """L'export CSV : relire la liste des comptes hors du terminal."""

    def setUp(self):
        super().setUp()
        comptes.creer("paul@example.com", MOT_DE_PASSE, MOT_DE_PASSE, "Paul O'Neil")
        bdd.enregistrer_connexion({"id": "42", "nom": "Ada", "email": "Ada@Exemple.FR",
                                   "photo": "https://x.test/p.jpg",
                                   "fournisseur": "google"})
        self.csv = os.path.join(self._temp.name, "export.csv")

    # ── CSV ─────────────────────────────────────────────────────────────────

    def test_le_csv_liste_les_comptes(self):
        import csv
        destination, nombre = bdd.exporter_csv(self.csv)
        self.assertEqual((destination, nombre), (self.csv, 2))

        with open(self.csv, encoding="utf-8-sig", newline="") as f:
            lignes = list(csv.DictReader(f))
        self.assertEqual(len(lignes), 2)
        self.assertEqual({l["email"] for l in lignes},
                         {"paul@example.com", "ada@exemple.fr"})
        self.assertIn("Paul O'Neil", {l["nom"] for l in lignes})

    def test_le_csv_ne_contient_aucune_empreinte(self):
        bdd.exporter_csv(self.csv)
        with open(self.csv, encoding="utf-8-sig") as f:
            contenu = f.read()
        self.assertNotIn("scrypt", contenu)
        self.assertNotIn(MOT_DE_PASSE, contenu)

    def test_le_csv_commence_par_le_marqueur_que_reclame_excel(self):
        bdd.exporter_csv(self.csv)
        with open(self.csv, "rb") as f:
            self.assertTrue(f.read(3) == b"\xef\xbb\xbf")

    def test_l_export_n_est_lisible_que_par_son_proprietaire(self):
        if os.name == "nt":
            self.skipTest("droits POSIX")
        bdd.exporter_csv(self.csv)
        self.assertEqual(os.stat(self.csv).st_mode & 0o077, 0)


class TestBaseNonServie(unittest.TestCase):
    """La base ne doit jamais être téléchargeable : elle contient les comptes."""

    def test_absente_de_la_liste_blanche(self):
        import app as app_module
        self.assertNotIn("chatpy.db", app_module.FICHIERS_PUBLICS)
        self.assertNotIn("schema.sql", app_module.FICHIERS_PUBLICS)

        app_module.app.testing = True
        client = app_module.app.test_client()
        for chemin in ("/chatpy.db", "/schema.sql", "/comptes.json",
                       "/export_comptes.csv"):
            self.assertEqual(client.get(chemin).status_code, 404, chemin)


if __name__ == "__main__":
    unittest.main()
