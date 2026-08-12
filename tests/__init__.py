"""Filet de sécurité : aucun test n'écrit dans la vraie base de comptes.

Le conftest.py voisin redirige déjà la base vers un dossier temporaire, mais
c'est un mécanisme pytest : `python3 -m unittest` ne le lit pas, et un test de
connexion inscrirait alors ses faux profils Google dans chatpy.db — ce qui est
arrivé. La redirection est donc posée ici, à l'import du paquet de tests, quel
que soit le lanceur. Le conftest la raffine ensuite, base neuve par test.
"""

import atexit
import os
import shutil
import sys
import tempfile

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import base_donnees  # noqa: E402

_BAC_A_SABLE = tempfile.mkdtemp(prefix="chatpy-tests-")
atexit.register(shutil.rmtree, _BAC_A_SABLE, True)

# CHATPY_DB gagnerait sur BASE_FILE : un .env qui la définit enverrait les tests
# écrire dans la base de production. C'est la raison d'être de ce fichier.
os.environ.pop("CHATPY_DB", None)
base_donnees.BASE_FILE = os.path.join(_BAC_A_SABLE, "chatpy.db")
# L'ancien comptes.json de la racine ne doit pas être repris — ni importé dans
# une base de test, ni renommé sous les pieds de l'utilisateur.
base_donnees.COMPTES_JSON = os.path.join(_BAC_A_SABLE, "comptes.json")
