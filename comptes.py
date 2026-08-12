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

Les comptes sont rangés dans la base SQLite (`chatpy.db`, voir base_donnees.py),
qui a remplacé l'ancien `comptes.json` — repris automatiquement au premier
démarrage. Ce module ne décide plus *où* écrire, seulement *quoi* : validation,
empreinte du mot de passe, limitation des tentatives.

Ce qui y est enregistré est une empreinte scrypt, jamais un mot de passe en
clair : on peut vérifier qu'un mot de passe correspond, jamais le relire. La
base n'est ni servie par le web (absente de FICHIERS_PUBLICS) ni committée
(elle est dans .gitignore).
"""

import re
import secrets
import threading
import time

from werkzeug.security import check_password_hash, generate_password_hash

import base_donnees as bdd

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

# ── Motifs de refus, traduits ───────────────────────────────────────────────
# Ces phrases s'affichent dans la modale de connexion, dont la langue est un
# réglage du navigateur (localStorage) que le serveur ne peut pas connaître
# seul : le front la joint à la requête, et les routes la passent ici.
#
# Un catalogue côté serveur double celui de i18n.js, ce qui n'est pas gratuit —
# mais l'alternative, renvoyer un code d'erreur que le front traduirait, rendrait
# ces réponses illisibles pour tout autre appelant de l'API (curl, un test, un
# script) et ferait dépendre le sens d'un message de la version du front.
#
# LANGUES doit rester en phase avec le tableau du même nom dans i18n.js.
LANGUES = ("fr", "en", "es", "de", "it", "pt")
LANGUE_DEFAUT = "fr"

MESSAGES = {
    "email_invalide": {
        "fr": "Cette adresse email n'est pas valide.",
        "en": "This email address is not valid.",
        "es": "Esta dirección de correo no es válida.",
        "de": "Diese E-Mail-Adresse ist ungültig.",
        "it": "Questo indirizzo email non è valido.",
        "pt": "Este endereço de e-mail não é válido.",
    },
    "mot_de_passe_manquant": {
        "fr": "Mot de passe manquant.",
        "en": "Password missing.",
        "es": "Falta la contraseña.",
        "de": "Passwort fehlt.",
        "it": "Password mancante.",
        "pt": "Senha ausente.",
    },
    "mot_de_passe_court": {
        "fr": "Le mot de passe doit faire au moins {n} caractères.",
        "en": "The password must be at least {n} characters long.",
        "es": "La contraseña debe tener al menos {n} caracteres.",
        "de": "Das Passwort muss mindestens {n} Zeichen lang sein.",
        "it": "La password deve contenere almeno {n} caratteri.",
        "pt": "A senha deve ter pelo menos {n} caracteres.",
    },
    "mot_de_passe_long": {
        "fr": "Le mot de passe ne peut pas dépasser {n} caractères.",
        "en": "The password cannot exceed {n} characters.",
        "es": "La contraseña no puede superar los {n} caracteres.",
        "de": "Das Passwort darf {n} Zeichen nicht überschreiten.",
        "it": "La password non può superare i {n} caratteri.",
        "pt": "A senha não pode passar de {n} caracteres.",
    },
    "mot_de_passe_email": {
        "fr": "Le mot de passe ne peut pas être votre adresse email.",
        "en": "The password cannot be your email address.",
        "es": "La contraseña no puede ser tu dirección de correo.",
        "de": "Das Passwort darf nicht Ihre E-Mail-Adresse sein.",
        "it": "La password non può essere il tuo indirizzo email.",
        "pt": "A senha não pode ser o seu endereço de e-mail.",
    },
    "confirmation_differente": {
        "fr": "Les deux mots de passe ne correspondent pas.",
        "en": "The two passwords do not match.",
        "es": "Las dos contraseñas no coinciden.",
        "de": "Die beiden Passwörter stimmen nicht überein.",
        "it": "Le due password non corrispondono.",
        "pt": "As duas senhas não coincidem.",
    },
    "compte_existant": {
        "fr": "Un compte existe déjà avec cette adresse.",
        "en": "An account already exists with this address.",
        "es": "Ya existe una cuenta con esta dirección.",
        "de": "Mit dieser Adresse besteht bereits ein Konto.",
        "it": "Esiste già un account con questo indirizzo.",
        "pt": "Já existe uma conta com este endereço.",
    },
    "trop_de_tentatives": {
        "fr": "Trop de tentatives. Réessayez dans {minutes} minute(s).",
        "en": "Too many attempts. Try again in {minutes} minute(s).",
        "es": "Demasiados intentos. Inténtalo de nuevo en {minutes} minuto(s).",
        "de": "Zu viele Versuche. Versuchen Sie es in {minutes} Minute(n) erneut.",
        "it": "Troppi tentativi. Riprova tra {minutes} minuto/i.",
        "pt": "Tentativas demais. Tente novamente em {minutes} minuto(s).",
    },
    # Un seul code pour « adresse inconnue » et « mot de passe faux » : les
    # distinguer révélerait quelles adresses sont inscrites. Ce message doit
    # rester rigoureusement identique dans les deux cas, dans chaque langue.
    "identifiants_incorrects": {
        "fr": "Adresse email ou mot de passe incorrect.",
        "en": "Incorrect email address or password.",
        "es": "Dirección de correo o contraseña incorrecta.",
        "de": "E-Mail-Adresse oder Passwort ist falsch.",
        "it": "Indirizzo email o password non corretti.",
        "pt": "Endereço de e-mail ou senha incorretos.",
    },
}


def normaliser_langue(langue):
    """Le code de langue s'il est connu, « fr » sinon.

    Tout arrive du réseau ici : une langue absente, inconnue ou d'un autre type
    qu'une chaîne ne justifie pas de refuser une inscription par ailleurs
    valable — c'est un confort d'affichage, pas une autorisation.
    """
    return langue if isinstance(langue, str) and langue in LANGUES else LANGUE_DEFAUT


def _msg(code, langue, **params):
    traductions = MESSAGES[code]
    # Repli sur le français plutôt que sur du vide : une phrase dans la mauvaise
    # langue reste actionnable, une phrase absente non.
    texte = traductions.get(normaliser_langue(langue)) or traductions[LANGUE_DEFAUT]
    return texte.format(**params) if params else texte

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


def valider(email, mot_de_passe, confirmation=None, nom=None, langue=LANGUE_DEFAUT):
    """Renvoie (None, motif) si quelque chose cloche, (valeurs, None) sinon.

    `langue` ne change que la rédaction du motif : les règles, elles, sont les
    mêmes pour tout le monde.
    """
    email = normaliser_email(email)
    if not email or len(email) > MAX_EMAIL or not _EMAIL.match(email):
        return None, _msg("email_invalide", langue)

    if not isinstance(mot_de_passe, str):
        return None, _msg("mot_de_passe_manquant", langue)
    if len(mot_de_passe) < MIN_MOT_DE_PASSE:
        return None, _msg("mot_de_passe_court", langue, n=MIN_MOT_DE_PASSE)
    if len(mot_de_passe) > MAX_MOT_DE_PASSE:
        return None, _msg("mot_de_passe_long", langue, n=MAX_MOT_DE_PASSE)
    if mot_de_passe.strip().lower() == email:
        return None, _msg("mot_de_passe_email", langue)

    if confirmation is not None and mot_de_passe != confirmation:
        return None, _msg("confirmation_differente", langue)

    nom = " ".join(nom.split())[:MAX_NOM] if isinstance(nom, str) else ""
    # À défaut de nom, la partie avant l'arobase : afficher l'adresse complète
    # dans la barre de navigation l'exposerait à quiconque regarde l'écran.
    return {"email": email, "mot_de_passe": mot_de_passe, "nom": nom or email.split("@")[0]}, None


# ── Inscription et connexion ────────────────────────────────────────────────


def creer(email, mot_de_passe, confirmation=None, nom=None, langue=LANGUE_DEFAUT):
    """Crée un compte. Renvoie (utilisateur, None) ou (None, motif)."""
    valeurs, motif = valider(email, mot_de_passe, confirmation, nom, langue)
    if motif:
        return None, motif

    compte = {
        # Identifiant tiré au sort, indépendant de l'adresse : il sert de clé
        # de rangement pour l'historique (« local-<id> »), et changer
        # d'adresse un jour ne doit pas dissocier quelqu'un de ses données.
        "id": secrets.token_hex(16),
        "nom": valeurs["nom"],
        "email": valeurs["email"],
    }
    # L'empreinte est calculée hors de toute transaction : scrypt prend quelques
    # dizaines de millisecondes, et les passer à tenir la base verrouillée
    # bloquerait toutes les autres connexions pendant ce temps.
    empreinte = generate_password_hash(valeurs["mot_de_passe"])

    if not bdd.creer_compte_local(compte["id"], compte["nom"], compte["email"], empreinte):
        # Cet aveu permet d'apprendre qu'une adresse est inscrite. Le taire
        # obligerait à confirmer par email pour lever l'ambiguïté, ce qu'on
        # ne sait pas faire ici — et un message vague ferait tourner en rond
        # quelqu'un qui a simplement oublié qu'il avait déjà un compte.
        return None, _msg("compte_existant", langue)

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


def verifier(email, mot_de_passe, langue=LANGUE_DEFAUT):
    """Authentifie. Renvoie (utilisateur, None) ou (None, motif)."""
    email = normaliser_email(email)
    if not email or not isinstance(mot_de_passe, str):
        return None, _msg("identifiants_incorrects", langue)
    # Tronqué et non refusé : un mot de passe trop long est forcément faux, mais
    # le hacher entier serait précisément le déni de service qu'on veut éviter.
    mot_de_passe = mot_de_passe[:MAX_MOT_DE_PASSE]

    with _verrou:
        reste = _blocage_restant(email)
        if reste:
            minutes = max(1, round(reste / 60))
            return None, _msg("trop_de_tentatives", langue, minutes=minutes)

        compte = bdd.lire_compte_local(email)
        # Même sur une adresse inconnue, on paie le prix d'une vérification :
        # voir _empreinte_factice().
        empreinte = compte["empreinte"] if compte else _empreinte_factice()
        valide = check_password_hash(empreinte, mot_de_passe) and compte is not None

        if not valide:
            _noter_echec(email)
            # Message unique pour « adresse inconnue » et « mot de passe faux » :
            # les distinguer révélerait quelles adresses sont inscrites.
            return None, _msg("identifiants_incorrects", langue)

        _tentatives.pop(email, None)

    # Date et compteur de connexions, comme pour Google et GitHub. Hors du
    # verrou : cette écriture ne touche pas au décompte des tentatives.
    bdd.noter_connexion("local", compte["id"])
    return _publier(compte), None
