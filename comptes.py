"""Comptes créés sur place, par email et mot de passe.

Troisième moyen de connexion, à côté de Google et GitHub. Contrairement à eux,
il ne dépend d'aucun identifiant à configurer : il fonctionne sur un clone frais.

Ce qu'il ne fait pas, et pourquoi :

* **Aucune vérification d'adresse.** Envoyer un lien de confirmation demanderait
  un serveur SMTP, que ce projet n'a pas. Une adresse saisie ici ne prouve donc
  rien — à la différence de Google et GitHub, dont on refuse justement les
  comptes à l'email non vérifié. Les comptes locaux sont marqués
  `fournisseur: "local"`, ce qui permet de les traiter différemment le jour où
  un privilège dépendra d'une adresse vérifiée.
* **Aucune réinitialisation de mot de passe**, pour la même raison. C'est ce qui
  justifie la confirmation du mot de passe à l'inscription : une faute de frappe
  ne se rattrape pas.

Le fichier `comptes.json` contient des empreintes scrypt, jamais de mot de passe
en clair, et n'est évidemment jamais servi par le web (il n'est pas dans
FICHIERS_PUBLICS) ni committé (il est dans .gitignore).
"""

import json
import os
import re
import secrets
import threading
import time

from werkzeug.security import check_password_hash, generate_password_hash

import ia_en_python as ia

_DIR = os.path.dirname(os.path.abspath(__file__))
COMPTES_FILE = os.path.join(_DIR, "comptes.json")

_verrou = threading.Lock()

MIN_MOT_DE_PASSE = 8
# Borne haute autant que basse : scrypt sur une chaîne de plusieurs mégaoctets
# occuperait le serveur de longues secondes, une seule requête suffirait à le
# mettre à genoux.
MAX_MOT_DE_PASSE = 200
MAX_EMAIL = 254
MAX_NOM = 60

# Volontairement permissif : la seule validation d'adresse qui vaille est
# l'envoi d'un message, et il n'y en a pas ici. On écarte les fautes de frappe
# grossières, pas les adresses exotiques mais valides.
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")

# ── Limitation des tentatives ───────────────────────────────────────────────
# En mémoire, donc remise à zéro au redémarrage et non partagée entre plusieurs
# processus. C'est assez pour ralentir une attaque par dictionnaire depuis un
# navigateur ; ça ne remplacerait pas un vrai limiteur devant le serveur.
TENTATIVES_MAX = 5
BLOCAGE_SECONDES = 300
_tentatives = {}


def _maintenant():
    return time.time()


def _empreinte_factice():
    """Empreinte jetable, comparée quand l'adresse est inconnue.

    Sans elle, une adresse sans compte répondrait instantanément là où une
    adresse existante prendrait le temps d'un scrypt : le simple chronométrage
    dirait qui est inscrit. Calculée à la première demande, pour ne pas ajouter
    ce coût à chaque import du module.
    """
    global _FACTICE
    if _FACTICE is None:
        _FACTICE = generate_password_hash("aucun compte a cette adresse")
    return _FACTICE


_FACTICE = None


def normaliser_email(email):
    """Forme canonique : sans espaces, en minuscules.

    Sans ça, « Paul@X.fr » et « paul@x.fr » créeraient deux comptes distincts,
    et l'un des deux serait impossible à retrouver à la connexion.
    """
    return email.strip().lower() if isinstance(email, str) else ""


def _charger():
    try:
        with open(COMPTES_FILE, "r", encoding="utf-8") as f:
            donnees = json.load(f)
    except FileNotFoundError:
        return {}
    except (json.JSONDecodeError, OSError):
        # Surtout ne pas repartir d'un fichier vide en silence : ce serait
        # effacer tous les comptes. On le met de côté et on le signale.
        ia._mettre_de_cote(
            COMPTES_FILE,
            "comptes.json est illisible : plus aucun compte local ne peut se connecter.",
        )
        return {}
    return donnees if isinstance(donnees, dict) else {}


def _publier(compte):
    """Le compte tel qu'il entre en session — jamais l'empreinte."""
    return {
        "id": compte["id"],
        "nom": compte["nom"],
        "email": compte["email"],
        "photo": "",
        "fournisseur": "local",
    }


# ── Validation ──────────────────────────────────────────────────────────────


def valider(email, mot_de_passe, confirmation=None, nom=None):
    """Renvoie (None, motif) si quelque chose cloche, (valeurs, None) sinon."""
    email = normaliser_email(email)
    if not email or len(email) > MAX_EMAIL or not _EMAIL.match(email):
        return None, "Cette adresse email n'est pas valide."

    if not isinstance(mot_de_passe, str):
        return None, "Mot de passe manquant."
    if len(mot_de_passe) < MIN_MOT_DE_PASSE:
        return None, f"Le mot de passe doit faire au moins {MIN_MOT_DE_PASSE} caractères."
    if len(mot_de_passe) > MAX_MOT_DE_PASSE:
        return None, f"Le mot de passe ne peut pas dépasser {MAX_MOT_DE_PASSE} caractères."
    if mot_de_passe.strip().lower() == email:
        return None, "Le mot de passe ne peut pas être votre adresse email."

    if confirmation is not None and mot_de_passe != confirmation:
        return None, "Les deux mots de passe ne correspondent pas."

    nom = " ".join(nom.split())[:MAX_NOM] if isinstance(nom, str) else ""
    # À défaut de nom, la partie avant l'arobase : afficher l'adresse complète
    # dans la barre de navigation l'exposerait à quiconque regarde l'écran.
    return {"email": email, "mot_de_passe": mot_de_passe, "nom": nom or email.split("@")[0]}, None


# ── Inscription et connexion ────────────────────────────────────────────────


def creer(email, mot_de_passe, confirmation=None, nom=None):
    """Crée un compte. Renvoie (utilisateur, None) ou (None, motif)."""
    valeurs, motif = valider(email, mot_de_passe, confirmation, nom)
    if motif:
        return None, motif

    with _verrou:
        comptes = _charger()
        if valeurs["email"] in comptes:
            # Cet aveu permet d'apprendre qu'une adresse est inscrite. Le taire
            # obligerait à confirmer par email pour lever l'ambiguïté, ce qu'on
            # ne sait pas faire ici — et un message vague ferait tourner en rond
            # quelqu'un qui a simplement oublié qu'il avait déjà un compte.
            return None, "Un compte existe déjà avec cette adresse."

        compte = {
            # Identifiant tiré au sort, indépendant de l'adresse : il sert de clé
            # de rangement pour l'historique (« local-<id> »), et changer
            # d'adresse un jour ne doit pas dissocier quelqu'un de ses données.
            "id": secrets.token_hex(16),
            "nom": valeurs["nom"],
            "email": valeurs["email"],
            "empreinte": generate_password_hash(valeurs["mot_de_passe"]),
            "cree": int(_maintenant() * 1000),
        }
        comptes[valeurs["email"]] = compte
        ia._ecrire_json_atomique(COMPTES_FILE, comptes)

    return _publier(compte), None


def _blocage_restant(email):
    """Secondes restantes avant de pouvoir réessayer, 0 si la voie est libre."""
    entree = _tentatives.get(email)
    if not entree:
        return 0
    nombre, dernier = entree
    if nombre < TENTATIVES_MAX:
        return 0
    reste = BLOCAGE_SECONDES - (_maintenant() - dernier)
    if reste <= 0:
        _tentatives.pop(email, None)
        return 0
    return int(reste) + 1


def _noter_echec(email):
    nombre, _ = _tentatives.get(email, (0, 0))
    _tentatives[email] = (nombre + 1, _maintenant())


def verifier(email, mot_de_passe):
    """Authentifie. Renvoie (utilisateur, None) ou (None, motif)."""
    email = normaliser_email(email)
    if not email or not isinstance(mot_de_passe, str):
        return None, "Adresse email ou mot de passe incorrect."
    # Tronqué et non refusé : un mot de passe trop long est forcément faux, mais
    # le hacher entier serait précisément le déni de service qu'on veut éviter.
    mot_de_passe = mot_de_passe[:MAX_MOT_DE_PASSE]

    with _verrou:
        reste = _blocage_restant(email)
        if reste:
            minutes = max(1, round(reste / 60))
            return None, f"Trop de tentatives. Réessayez dans {minutes} minute(s)."

        compte = _charger().get(email)
        # Même sur une adresse inconnue, on paie le prix d'une vérification :
        # voir _empreinte_factice().
        empreinte = compte["empreinte"] if compte else _empreinte_factice()
        valide = check_password_hash(empreinte, mot_de_passe) and compte is not None

        if not valide:
            _noter_echec(email)
            # Message unique pour « adresse inconnue » et « mot de passe faux » :
            # les distinguer révélerait quelles adresses sont inscrites.
            return None, "Adresse email ou mot de passe incorrect."

        _tentatives.pop(email, None)

    return _publier(compte), None
