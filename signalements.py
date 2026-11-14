"""Stockage des signalements envoyés depuis le site."""

import json
import os
import threading
import time
import uuid

_DIR = os.path.dirname(os.path.abspath(__file__))
FICHIER = os.path.join(_DIR, "signalements.json")
_verrou = threading.Lock()


def enregistrer(signalement):
    """Ajoute un signalement et renvoie son identifiant."""
    with _verrou:
        try:
            with open(FICHIER, "r", encoding="utf-8") as fichier:
                donnees = json.load(fichier)
            if not isinstance(donnees, list):
                raise ValueError("Le journal des signalements doit être une liste JSON.")
        except FileNotFoundError:
            donnees = []

        entree = {
            "id": uuid.uuid4().hex,
            "date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            **signalement,
        }
        donnees.append(entree)
        temporaire = FICHIER + ".tmp"
        with open(temporaire, "w", encoding="utf-8") as fichier:
            json.dump(donnees, fichier, ensure_ascii=False, indent=2)
            fichier.write("\n")
        os.replace(temporaire, FICHIER)
        return entree["id"]
