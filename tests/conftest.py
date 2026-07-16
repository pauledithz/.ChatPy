import os
import sys

# ia_en_python.py et app.py vivent à la racine du dépôt, pas dans un package.
# pytest ajoute le dossier des tests à sys.path (mode "prepend" sans __init__.py),
# pas la racine : on le fait nous-mêmes pour que `import ia_en_python` fonctionne.
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
