import os
import sys

# The project's modules (ia_en_python.py, app.py) live at the repo root and
# are not packaged, so the root needs to be importable from the tests.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))