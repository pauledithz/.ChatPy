"""Conversations archivées des utilisateurs connectés.

Pourquoi un fichier séparé de `.chatpy_history.json` : ce dernier est un journal
plat, partagé par tous les visiteurs et par le CLI, sans horodatage ni frontière
entre deux conversations. Il sert à alimenter le contexte du bot, pas à rendre
son historique à quelqu'un. Rien n'y permet de dire quelles lignes appartiennent
à qui, et il est donc impossible d'en reconstituer l'historique d'un compte.

Ici, à l'inverse, tout est cloisonné par utilisateur :

    {"google-42": [ {id, titre, cree, maj, quiz_actif, messages: [...]}, ... ]}

Le fournisseur fait partie de la clé de rangement — Google et GitHub numérotent
leurs comptes chacun de leur côté, et l'utilisateur Google 42 n'a rien à voir
avec le 42 de GitHub.

Les visiteurs non connectés n'apparaissent pas ici : leur conversation reste
dans le localStorage de leur navigateur, comme avant.
"""

import json
import os
import re
import threading
import time

import ia_en_python as ia

_DIR = os.path.dirname(os.path.abspath(__file__))
CONVERSATIONS_FILE = os.path.join(_DIR, "conversations.json")

# Le fichier entier est relu et réécrit à chaque enregistrement — même stratégie
# que le journal des lacunes. C'est simple et sûr tant qu'il reste petit, d'où
# les plafonds ci-dessous. Au-delà, la conversation la plus ancienne saute.
MAX_CONVERSATIONS = 50
MAX_MESSAGES = 300
MAX_LONGUEUR_TEXTE = 20_000
MAX_LONGUEUR_TITRE = 80
MAX_SUGGESTIONS = 6

# Le serveur est multi-thread : sans verrou, deux onglets qui enregistrent en
# même temps liraient la même version et le second écraserait le premier.
_verrou = threading.Lock()

# Un identifiant vient du navigateur ; il finit en clé de dictionnaire et dans
# une URL. On n'accepte donc qu'un alphabet strict, plutôt que d'assainir après
# coup une chaîne quelconque.
_ID_VALIDE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def cle_utilisateur(utilisateur):
    """Clé de rangement d'un compte, à partir de l'entrée de session."""
    return f"{utilisateur['fournisseur']}-{utilisateur['id']}"


def _charger():
    """Tout le fichier. {} s'il n'existe pas, mis de côté s'il est illisible."""
    try:
        with open(CONVERSATIONS_FILE, "r", encoding="utf-8") as f:
            donnees = json.load(f)
    except FileNotFoundError:
        return {}
    except (json.JSONDecodeError, OSError):
        ia._mettre_de_cote(
            CONVERSATIONS_FILE,
            "conversations.json est illisible : les conversations archivées "
            "sont reparties de zéro.",
        )
        return {}
    # Un fichier valide mais de forme inattendue (liste, nombre) est traité
    # comme vide : mieux vaut repartir que planter à chaque requête.
    return donnees if isinstance(donnees, dict) else {}


def _maintenant():
    return int(time.time() * 1000)


# ── Nettoyage de ce qui vient du navigateur ─────────────────────────────────
# Ce corps de requête est écrit sur disque puis resservi plus tard. Rien n'y est
# de confiance : ni les types, ni les tailles, ni la présence des champs.


def _texte(valeur, limite):
    return valeur[:limite] if isinstance(valeur, str) else ""


def _nettoyer_extras(brut):
    """Les suggestions et le libellé attachés à une réponse du bot."""
    if not isinstance(brut, dict):
        return None
    suggestions_brutes = brut.get("suggestions")
    suggestions = []
    if isinstance(suggestions_brutes, list):
        for suggestion in suggestions_brutes[:MAX_SUGGESTIONS]:
            if isinstance(suggestion, str) and suggestion.strip():
                suggestions.append(suggestion[:MAX_LONGUEUR_TITRE * 3])
    extras = {
        "suggestions": suggestions,
        "titre": _texte(brut.get("titre"), 120),
        "question": _texte(brut.get("question"), MAX_LONGUEUR_TEXTE),
    }
    # Des extras entièrement vides n'apportent rien : on ne les stocke pas.
    if not suggestions and not extras["question"]:
        return None
    return extras


def _nettoyer_message(brut):
    """Un message, ou None s'il est inexploitable."""
    if not isinstance(brut, dict):
        return None
    if brut.get("type") not in ("user", "ai"):
        return None
    texte = brut.get("text")
    if not isinstance(texte, str) or not texte.strip():
        return None

    message = {"type": brut["type"], "text": texte[:MAX_LONGUEUR_TEXTE]}
    extras = _nettoyer_extras(brut.get("extras"))
    if extras is not None:
        message["extras"] = extras
    return message


def _titre_par_defaut(messages):
    """Première question posée, tronquée — à défaut, un libellé neutre."""
    for message in messages:
        if message["type"] == "user":
            titre = " ".join(message["text"].split())
            if titre:
                return titre[:MAX_LONGUEUR_TITRE]
    return "Nouvelle conversation"


def nettoyer_conversation(brut):
    """Valide et normalise une conversation reçue du navigateur.

    Renvoie (conversation, None) ou (None, motif de refus).
    """
    if not isinstance(brut, dict):
        return None, "Le corps doit être un objet JSON."

    identifiant = brut.get("id")
    if not isinstance(identifiant, str) or not _ID_VALIDE.match(identifiant):
        return None, "Identifiant de conversation invalide."

    messages_bruts = brut.get("messages")
    if not isinstance(messages_bruts, list):
        return None, "Le champ 'messages' doit être une liste."

    messages = []
    for message_brut in messages_bruts:
        message = _nettoyer_message(message_brut)
        if message is not None:
            messages.append(message)
    if not messages:
        return None, "Une conversation sans message ne peut pas être enregistrée."
    # Au-delà du plafond, on garde la fin : c'est le contexte le plus récent,
    # et c'est ce que l'utilisateur voit en rouvrant la conversation.
    messages = messages[-MAX_MESSAGES:]

    titre = " ".join(_texte(brut.get("titre"), MAX_LONGUEUR_TITRE).split())
    return {
        "id": identifiant,
        "titre": titre or _titre_par_defaut(messages),
        "cree": brut.get("cree") if isinstance(brut.get("cree"), int) else _maintenant(),
        "maj": _maintenant(),
        "quiz_actif": bool(brut.get("quiz_actif")),
        "messages": messages,
    }, None


# ── Lecture ─────────────────────────────────────────────────────────────────


def _resume(conversation):
    """Ce que la liste latérale affiche — sans le corps des messages.

    Renvoyer les messages complets de cinquante conversations à chaque
    ouverture de la page coûterait des centaines de kilo-octets pour n'afficher
    que des titres.
    """
    return {
        "id": conversation["id"],
        "titre": conversation["titre"],
        "maj": conversation["maj"],
        "nb_messages": len(conversation["messages"]),
    }


def _correspond(conversation, recherche_normalisee):
    if not recherche_normalisee:
        return True
    if recherche_normalisee in ia.normaliser_texte(conversation["titre"]):
        return True
    # La recherche porte aussi sur le contenu : on retrouve plus souvent une
    # conversation par ce qu'on y a dit que par son titre auto-généré.
    return any(
        recherche_normalisee in ia.normaliser_texte(message["text"])
        for message in conversation["messages"]
    )


def lister(cle, recherche=""):
    """Résumés des conversations d'un compte, la plus récente en tête."""
    conversations = _charger().get(cle, [])
    recherche_normalisee = ia.normaliser_texte(recherche) if recherche else ""
    retenues = [c for c in conversations if _correspond(c, recherche_normalisee)]
    retenues.sort(key=lambda c: c.get("maj", 0), reverse=True)
    return [_resume(c) for c in retenues]


def obtenir(cle, identifiant):
    """Une conversation complète, ou None."""
    for conversation in _charger().get(cle, []):
        if conversation.get("id") == identifiant:
            return conversation
    return None


# ── Écriture ────────────────────────────────────────────────────────────────
# Chaque mutation relit le fichier sous verrou juste avant d'écrire : un autre
# onglet a pu enregistrer entre-temps, et son travail ne doit pas disparaître.


def enregistrer(cle, brut):
    """Crée ou remplace une conversation. Renvoie (résumé, None) ou (None, motif)."""
    conversation, motif = nettoyer_conversation(brut)
    if motif:
        return None, motif

    with _verrou:
        donnees = _charger()
        liste = donnees.get(cle, [])
        liste = [c for c in liste if c.get("id") != conversation["id"]]
        liste.append(conversation)
        # Plafond par compte : la plus anciennement modifiée saute.
        liste.sort(key=lambda c: c.get("maj", 0), reverse=True)
        donnees[cle] = liste[:MAX_CONVERSATIONS]
        ia._ecrire_json_atomique(CONVERSATIONS_FILE, donnees)

    return _resume(conversation), None


def renommer(cle, identifiant, titre):
    """Change le titre. Renvoie le résumé, ou None si la conversation n'existe pas."""
    titre = " ".join(_texte(titre, MAX_LONGUEUR_TITRE).split())
    if not titre:
        return None

    with _verrou:
        donnees = _charger()
        for conversation in donnees.get(cle, []):
            if conversation.get("id") == identifiant:
                conversation["titre"] = titre
                # Volontairement sans toucher à « maj » : renommer n'est pas
                # une activité de conversation, et remonter l'entrée en tête de
                # liste pour un simple renommage désorienterait.
                ia._ecrire_json_atomique(CONVERSATIONS_FILE, donnees)
                return _resume(conversation)
    return None


def supprimer(cle, identifiant):
    """Retire une conversation. Renvoie True si elle existait."""
    with _verrou:
        donnees = _charger()
        liste = donnees.get(cle, [])
        restantes = [c for c in liste if c.get("id") != identifiant]
        if len(restantes) == len(liste):
            return False
        donnees[cle] = restantes
        ia._ecrire_json_atomique(CONVERSATIONS_FILE, donnees)
        return True
