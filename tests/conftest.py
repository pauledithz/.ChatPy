import os
import sys

# ia_en_python.py et app.py vivent à la racine du dépôt, pas dans un package.
# pytest ajoute le dossier des tests à sys.path (mode "prepend" sans __init__.py),
# pas la racine : on le fait nous-mêmes pour que `import ia_en_python` fonctionne.
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import pytest  # noqa: E402  (après l'ajout du dépôt à sys.path)

import base_donnees  # noqa: E402


@pytest.fixture(autouse=True)
def base_isolee(tmp_path, monkeypatch):
    """Chaque test travaille sur une base neuve, dans un dossier temporaire.

    Sans ça, le moindre test de connexion inscrirait ses faux profils dans la
    vraie base — c'est arrivé — et un test d'inscription pourrait entrer en
    conflit avec un compte réel. Même principe que les tests qui redirigent
    .chatpy_history.json.

    CHATPY_DB est retirée de l'environnement : elle gagne sur BASE_FILE, et un
    .env qui la définirait renverrait tous les tests sur la base de production.
    """
    monkeypatch.delenv("CHATPY_DB", raising=False)
    monkeypatch.setattr(base_donnees, "BASE_FILE", str(tmp_path / "chatpy-test.db"))
    monkeypatch.setattr(base_donnees, "COMPTES_JSON", str(tmp_path / "comptes.json"))
    # Le schéma est posé une fois par chemin de base : sans cette remise à zéro,
    # la base temporaire du test suivant resterait vide de toute table.
    monkeypatch.setattr(base_donnees, "_base_prete", None)
