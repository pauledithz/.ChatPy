"""La base SQLite : une ligne par personne qui se connecte.

Pourquoi une base ici, alors que tout le reste du projet tient dans des JSON :
les comptes sont la seule donnée qu'on ne peut pas se permettre de perdre. Il
n'y a pas de réinitialisation de mot de passe (voir comptes.py), donc une
écriture concurrente qui écrase un compte l'efface définitivement. Un fichier
JSON entièrement réécrit à chaque inscription ne tient que grâce à un verrou
Python, qui ne protège rien entre deux processus — c'est d'ailleurs pourquoi le
Procfile impose `--workers 1`. SQLite, lui, verrouille au niveau du fichier :
l'écriture d'un compte est atomique quel que soit le nombre de processus.

Ce qui est stocké, et ce qui ne l'est pas :

* nom, email, fournisseur, date de création, dernière connexion, nombre de
  connexions ;
* **l'empreinte scrypt du mot de passe, jamais le mot de passe.** C'est un
  aller simple : on peut vérifier qu'un mot de passe correspond à l'empreinte,
  on ne peut pas retrouver le mot de passe à partir d'elle. Stocker les mots de
  passe en clair rendrait le vol de ce fichier catastrophique — les gens
  réutilisent leurs mots de passe ailleurs — alors qu'ici il ne donne rien. Les
  comptes Google et GitHub n'ont pas d'empreinte du tout : leur mot de passe
  reste chez eux, ChatPy ne le voit jamais.

Le schéma vit dans `schema.sql`, pas ici. `chatpy.db` est un fichier généré,
ignoré par git et absent de FICHIERS_PUBLICS — il ne doit jamais être servi.
"""

import contextlib
import csv
import json
import os
import sqlite3
import threading
from datetime import datetime, timezone

import ia_en_python as ia

_DIR = os.path.dirname(os.path.abspath(__file__))

BASE_FILE = os.path.join(_DIR, "chatpy.db")
SCHEMA_FILE = os.path.join(_DIR, "schema.sql")

# Ancien stockage, repris automatiquement à la première ouverture de la base.
COMPTES_JSON = os.path.join(_DIR, "comptes.json")

# Fichier produit par l'export, pour relire la liste dans un tableur. Il
# contient de vraies adresses email : il est dans .gitignore, comme la base.
EXPORT_CSV = os.path.join(_DIR, "export_comptes.csv")


def chemin():
    """Où vit la base. CHATPY_DB permet de la sortir du dossier du dépôt.

    Utile en production : le disque persistant d'un hébergeur n'est en général
    pas celui où le code est déployé, et une base restée dans le dossier du code
    disparaîtrait au déploiement suivant.
    """
    return os.environ.get("CHATPY_DB", "").strip() or BASE_FILE


def maintenant():
    """Horodatage ISO 8601 en UTC, tel qu'il est écrit dans la base."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# Le schéma n'est posé qu'à la première utilisation, jamais à l'import : d'une
# part importer un module ne devrait pas créer de fichier, d'autre part app.py
# importe comptes.py *avant* d'appeler load_dotenv(), et CHATPY_DB serait donc
# encore inconnue. On retient le chemin déjà préparé plutôt qu'un simple
# booléen, pour qu'un changement de base (les tests en changent à chaque test)
# reparte proprement.
_verrou_schema = threading.Lock()
_base_prete = None
# Le thread qui prépare la base est le seul autorisé à la rouvrir pendant la
# reprise : c'est lui qui coupe la récursion, pas le drapeau public.
_en_preparation = threading.local()


def _preparer(fichier):
    """Crée la base et son schéma si besoin, puis reprend l'ancien comptes.json."""
    global _base_prete
    if _base_prete == fichier:
        return
    if getattr(_en_preparation, "fichier", None) == fichier:
        return  # appel réentrant depuis _reprendre_comptes_json()

    with _verrou_schema:
        if _base_prete == fichier:  # posé pendant qu'on attendait le verrou
            return

        _poser_le_schema(fichier)
        _en_preparation.fichier = fichier
        try:
            _reprendre_comptes_json()
        finally:
            _en_preparation.fichier = None
        # Publié seulement maintenant : aucun autre thread ne voit la base
        # « prête » avant que les anciens comptes n'y soient.
        _base_prete = fichier


def _poser_le_schema(fichier):
    try:
        with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
            schema = f.read()
    except OSError as erreur:
        # Contrairement aux fichiers de données (faq.json et compagnie), le
        # schéma n'est pas une donnée qu'on peut remplacer par un défaut
        # vide : sans lui, aucune connexion n'est possible. Mieux vaut un
        # message clair au démarrage qu'un « no such table » à l'inscription.
        raise RuntimeError(
            f"schema.sql est introuvable ou illisible ({erreur}) : "
            "la base des comptes ne peut pas être créée."
        ) from erreur

    cnx = sqlite3.connect(fichier, timeout=10)
    try:
        # Lecture réservée à son propriétaire : le fichier contient les
        # empreintes de tous les comptes, et rien ne justifie qu'un autre
        # utilisateur de la machine puisse en prendre copie. Fait avant le
        # passage en WAL, car SQLite donne aux fichiers -wal et -shm les
        # droits de la base au moment où il les crée.
        with contextlib.suppress(OSError):  # systèmes sans droits POSIX
            os.chmod(fichier, 0o600)
        # WAL : un lecteur ne bloque plus un écrivain. Le réglage est inscrit
        # dans le fichier, ce PRAGMA ne le repose donc qu'une fois utilement.
        cnx.execute("PRAGMA journal_mode = WAL")
        cnx.executescript(schema)
        cnx.commit()
    finally:
        cnx.close()


class _Session:
    """Un curseur qui rend des dictionnaires plutôt que des lignes sqlite3.

    Le seul intérêt : le reste du module manipule des `dict` ordinaires, ce qui
    laisse les résultats se recopier, se sérialiser et se comparer sans avoir à
    penser au type que renvoie le pilote.
    """

    def __init__(self, curseur):
        self._curseur = curseur

    def execute(self, sql, parametres=()):
        """Exécute et renvoie les lignes, sous forme de dictionnaires.

        Une liste vide après un INSERT ou un UPDATE, qui n'ont rien à rendre.
        """
        self._curseur.execute(sql, parametres)
        return [dict(ligne) for ligne in self._curseur.fetchall()]

    def executemany(self, sql, series):
        self._curseur.executemany(sql, list(series))
        return []


@contextlib.contextmanager
def connexion():
    """Une connexion à la base, validée en sortie et refermée dans tous les cas.

    Une connexion par opération plutôt qu'une partagée : le serveur est
    multi-thread, et un objet sqlite3.Connection n'est pas fait pour circuler
    entre threads. Ouvrir un fichier local coûte quelques dizaines de
    microsecondes, ce qui est sans commune mesure avec un scrypt.
    """
    fichier = chemin()
    _preparer(fichier)
    cnx = sqlite3.connect(fichier, timeout=10)
    cnx.row_factory = sqlite3.Row
    try:
        with cnx:  # valide à la sortie, annule si une exception passe
            yield _Session(cnx.cursor())
    finally:
        cnx.close()


# ── Comptes locaux (email + mot de passe) ────────────────────────────────────


def lire_compte_local(email):
    """Le compte local à cette adresse, empreinte comprise. None s'il n'existe pas.

    C'est la seule fonction qui ressort une empreinte : elle sert à la
    vérification du mot de passe, et à rien d'autre.
    """
    with connexion() as cnx:
        lignes = cnx.execute(
            "SELECT id_externe, nom, email, empreinte FROM utilisateurs "
            "WHERE fournisseur = 'local' AND email = ?",
            (email,),
        )
    if not lignes:
        return None
    ligne = lignes[0]
    return {
        "id": ligne["id_externe"],
        "nom": ligne["nom"],
        "email": ligne["email"],
        "empreinte": ligne["empreinte"],
    }


def creer_compte_local(identifiant, nom, email, empreinte):
    """Inscrit un compte local. Renvoie False si l'adresse est déjà prise.

    Le doublon est détecté par l'index unique de la base et non par une lecture
    préalable : entre un SELECT et un INSERT, deux inscriptions simultanées à la
    même adresse passeraient toutes les deux.
    """
    with connexion() as cnx:
        try:
            cnx.execute(
                "INSERT INTO utilisateurs "
                "(fournisseur, id_externe, nom, email, empreinte, photo, "
                " cree, derniere_connexion, nb_connexions) "
                "VALUES ('local', ?, ?, ?, ?, '', ?, ?, 1)",
                (identifiant, nom, email, empreinte, maintenant(), maintenant()),
            )
        except sqlite3.IntegrityError:
            return False
    return True


# ── Toutes provenances ───────────────────────────────────────────────────────


def noter_connexion(fournisseur, identifiant):
    """Avance la date et le compteur de connexions d'un compte déjà inscrit.

    Un simple UPDATE, sans création : c'est ce qu'il faut pour un compte local,
    dont la ligne existe forcément puisqu'on vient d'y vérifier un mot de passe.
    La recréer ici la recréerait sans empreinte, c'est-à-dire un compte où l'on
    entre sans mot de passe — ce que la contrainte CHECK du schéma refuse.
    """
    with connexion() as cnx:
        cnx.execute(
            "UPDATE utilisateurs SET derniere_connexion = ?, "
            "       nb_connexions = nb_connexions + 1 "
            "WHERE fournisseur = ? AND id_externe = ?",
            (maintenant(), fournisseur, identifiant),
        )


def enregistrer_connexion(utilisateur):
    """Note le passage de quelqu'un venu de Google ou GitHub : crée sa ligne,
    ou met la sienne à jour.

    Chez eux, la première connexion vaut inscription : il n'y a pas d'étape
    d'enregistrement séparée, et rien d'autre à remplir que ce que le
    fournisseur vient de nous dire. Le profil est réécrit à chaque passage, car
    un nom ou une photo changent de leur côté sans nous prévenir.

    L'empreinte reste NULL : leur mot de passe ne nous est jamais montré.
    """
    with connexion() as cnx:
        cnx.execute(
            "INSERT INTO utilisateurs "
            "(fournisseur, id_externe, nom, email, empreinte, photo, "
            " cree, derniere_connexion, nb_connexions) "
            "VALUES (?, ?, ?, ?, NULL, ?, ?, ?, 1) "
            "ON CONFLICT (fournisseur, id_externe) DO UPDATE SET "
            "  nom = excluded.nom,"
            "  email = excluded.email,"
            "  photo = excluded.photo,"
            "  derniere_connexion = excluded.derniere_connexion,"
            # Qualifié par le nom de la table : dans un ON CONFLICT, la
            # colonne nue peut désigner la ligne déjà en base ou celle qu'on
            # tentait d'insérer (« excluded »). Ici c'est bien l'existante.
            "  nb_connexions = utilisateurs.nb_connexions + 1",
            (
                str(utilisateur.get("fournisseur", "")),
                str(utilisateur.get("id", "")),
                str(utilisateur.get("nom", "")),
                # Minuscules comme pour les comptes locaux : sans ça, une même
                # adresse écrite de deux façons compterait pour deux personnes
                # dans n'importe quelle recherche par email.
                str(utilisateur.get("email", "")).strip().lower(),
                str(utilisateur.get("photo", "")),
                maintenant(),
                maintenant(),
            ),
        )


def lister_utilisateurs(avec_empreinte=False):
    """Tous les comptes, du plus récemment vu au plus ancien.

    Sans les empreintes par défaut : elles n'ont qu'un seul usage légitime,
    vérifier un mot de passe, et rien de ce qui affiche ou exporte la liste n'en
    a besoin. `avec_empreinte=True` est réservé à l'export de migration, où les
    omettre reviendrait à déménager des comptes dans lesquels plus personne ne
    pourrait entrer.
    """
    colonnes = ("fournisseur, id_externe, nom, email, photo, cree, "
                "derniere_connexion, nb_connexions")
    if avec_empreinte:
        colonnes += ", empreinte"
    with connexion() as cnx:
        # « IS NULL » d'abord : les comptes jamais reconnectés partent en
        # bas de liste au lieu de se mélanger aux plus récents.
        return cnx.execute(
            f"SELECT {colonnes} FROM utilisateurs "
            "ORDER BY derniere_connexion IS NULL, derniere_connexion DESC, cree DESC"
        )


def compter():
    """Nombre de comptes enregistrés, par fournisseur."""
    with connexion() as cnx:
        lignes = cnx.execute(
            "SELECT fournisseur, COUNT(*) AS n FROM utilisateurs GROUP BY fournisseur"
        )
    return {ligne["fournisseur"]: ligne["n"] for ligne in lignes}


# ── Reprise de l'ancien comptes.json ─────────────────────────────────────────


def _reprendre_comptes_json():
    """Importe un comptes.json d'avant la base, puis l'écarte du chemin.

    Rejouable sans risque : les comptes déjà présents sont ignorés (INSERT OR
    IGNORE), et le fichier est renommé une fois lu, donc le prochain démarrage
    ne trouve plus rien à reprendre. Il est renommé et non supprimé — c'est la
    seule copie de comptes auxquels personne ne pourra plus se reconnecter si
    l'import s'est mal passé.
    """
    try:
        with open(COMPTES_JSON, "r", encoding="utf-8") as f:
            anciens = json.load(f)
    except FileNotFoundError:
        return 0
    except (json.JSONDecodeError, OSError):
        ia._mettre_de_cote(
            COMPTES_JSON,
            "comptes.json est illisible : ses comptes n'ont pas pu être repris "
            "dans la base.",
        )
        return 0

    if not isinstance(anciens, dict):
        return 0

    reprises = []
    for email, compte in anciens.items():
        if not isinstance(compte, dict) or not compte.get("empreinte"):
            continue
        # « cree » valait des millisecondes depuis 1970 ; la base garde de l'ISO.
        try:
            cree = datetime.fromtimestamp(
                int(compte.get("cree", 0)) / 1000, timezone.utc
            ).isoformat(timespec="seconds")
        except (TypeError, ValueError, OSError, OverflowError):
            cree = maintenant()
        reprises.append((
            str(compte.get("id") or email),
            str(compte.get("nom") or ""),
            str(compte.get("email") or email).strip().lower(),
            str(compte["empreinte"]),
            cree,
        ))

    if reprises:
        with connexion() as cnx:
            # « on conflict do nothing » : un compte déjà repris lors d'un
            # démarrage précédent est laissé tel quel, jamais réécrit.
            cnx.executemany(
                "INSERT INTO utilisateurs "
                "(fournisseur, id_externe, nom, email, empreinte, photo, "
                " cree, derniere_connexion, nb_connexions) "
                "VALUES ('local', ?, ?, ?, ?, '', ?, NULL, 0) "
                "ON CONFLICT DO NOTHING",
                reprises,
            )

    try:
        os.replace(COMPTES_JSON, COMPTES_JSON + ".repris")
    except OSError:
        pass
    print(f"ℹ️  {len(reprises)} compte(s) repris de comptes.json dans la base.")
    return len(reprises)


# ── Export ───────────────────────────────────────────────────────────────────
# Un seul fichier, pour relire la liste des comptes hors du terminal : un CSV
# qui s'ouvre dans Numbers ou Excel. Sans les empreintes — elles n'ont qu'un
# usage, vérifier un mot de passe, et rien de ce qui s'affiche n'en a besoin.

COLONNES_LISIBLES = ("fournisseur", "email", "nom", "cree", "derniere_connexion",
                     "nb_connexions")


def exporter_csv(destination=None):
    """Écrit la liste des comptes en CSV, lisible dans Numbers ou Excel.

    Sans les empreintes : ce fichier sert à regarder qui s'est inscrit, et
    elles n'ont qu'un usage, vérifier un mot de passe.
    """
    destination = destination or EXPORT_CSV
    utilisateurs = lister_utilisateurs()

    with open(destination, "w", encoding="utf-8-sig", newline="") as f:
        # utf-8-sig : sans ce marqueur en tête, Excel lit un CSV UTF-8 comme du
        # latin-1 et affiche « crÃ©Ã© le ».
        graveur = csv.writer(f)
        graveur.writerow(COLONNES_LISIBLES)
        for u in utilisateurs:
            graveur.writerow([u[c] if u[c] is not None else "" for c in COLONNES_LISIBLES])

    _restreindre(destination)
    return destination, len(utilisateurs)


def _ecrire(destination, contenu):
    with open(destination, "w", encoding="utf-8") as f:
        f.write(contenu)
    _restreindre(destination)


def _restreindre(fichier):
    """Lecture réservée au propriétaire : ces exports listent de vraies adresses."""
    with contextlib.suppress(OSError):
        os.chmod(fichier, 0o600)


# ── Consultation en ligne de commande ────────────────────────────────────────


def _afficher():
    print(f"Base : {os.path.basename(chemin())}\n")
    utilisateurs = lister_utilisateurs()
    if not utilisateurs:
        print("Aucun compte enregistré pour l'instant.")
        return

    entetes = ("FOURNISSEUR", "EMAIL", "NOM", "CRÉÉ LE", "DERNIÈRE CONNEXION", "N")
    lignes = [
        (
            u["fournisseur"],
            u["email"],
            u["nom"],
            (u["cree"] or "")[:10],
            (u["derniere_connexion"] or "—")[:19].replace("T", " "),
            str(u["nb_connexions"]),
        )
        for u in utilisateurs
    ]
    largeurs = [max(len(c) for c in colonne) for colonne in zip(entetes, *lignes)]

    def trace(cellules):
        print("  ".join(c.ljust(l) for c, l in zip(cellules, largeurs)).rstrip())

    trace(entetes)
    trace(tuple("─" * l for l in largeurs))
    for ligne in lignes:
        trace(ligne)

    total = compter()
    print(f"\n{sum(total.values())} compte(s) : " +
          ", ".join(f"{n} {f}" for f, n in sorted(total.items())))


def _exporter_sql():
    """Écrit la base entière en SQL sur la sortie standard (sauvegarde).

    Le dump contient les empreintes : c'est un fichier à traiter comme la base
    elle-même, pas quelque chose à coller dans un ticket.
    """
    cnx = sqlite3.connect(chemin(), timeout=10)
    try:
        for instruction in cnx.iterdump():
            print(instruction)
    finally:
        cnx.close()


AIDE = """\
Usage : python3 base_donnees.py [option] [fichier]

  (sans option)   affiche la table des comptes dans le terminal
  --csv           écrit export_comptes.csv, lisible dans Numbers ou Excel
  --sql           dump SQL brut de la base sur la sortie standard (sauvegarde)
  --aide          ce message

Un chemin peut suivre --csv pour choisir le fichier écrit.
"""


if __name__ == "__main__":
    import sys

    # C'est app.py qui charge .env, et lui seul : lancé à la main, ce script ne
    # verrait donc pas CHATPY_DB et regarderait la mauvaise base sans le dire.
    with contextlib.suppress(ImportError):  # python-dotenv reste facultatif
        from dotenv import load_dotenv
        load_dotenv(os.path.join(_DIR, ".env"))

    arguments = sys.argv[1:]
    option = arguments[0] if arguments else ""
    fichier = arguments[1] if len(arguments) > 1 else None

    if option in ("--aide", "-h", "--help"):
        print(AIDE)
    elif option == "--sql":
        _exporter_sql()
    elif option == "--csv":
        destination, nombre = exporter_csv(fichier)
        print(f"✅ {nombre} compte(s) écrits dans {destination}")
        print("   Ouvrez-le d'un double-clic : il s'affiche dans Numbers ou Excel.")
    elif option:
        print(f"Option inconnue : {option}\n")
        print(AIDE)
        raise SystemExit(2)
    else:
        _afficher()
